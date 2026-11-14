"""Simuladores offline de GitHub, SerpApi e SMTP usados por todos os testes."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitor import correio, serpapi  # noqa: E402
from monitor.github import GitHub  # noqa: E402
from monitor.principal import Monitor  # noqa: E402

AGORA = datetime(2027, 1, 10, 15, 0, tzinfo=timezone.utc)

CAMPOS_PADRAO = {
    "Origem": "GRU,CGH",
    "Destino": "LIS",
    "Tipo de viagem": "Ida e volta",
    "Data de ida": "15/03/2027",
    "Data de volta": "29/03/2027",
    "Adultos": "2",
    "Idade de cada criança": "_No response_",
    "Bebês no colo": "- [ ] Os bebês viajam no colo",
    "Classe": "Econômica",
    "Escalas": "Qualquer",
    "Bagagens de mão": "0",
    "Preço-alvo (R$)": "_No response_",
    "Frequência de verificação": "3 h",
    "Monitorar até": "_No response_",
    "E-mail para avisos": "_No response_",
}


def corpo(**mudancas) -> str:
    """Corpo de issue no formato gerado pelo Issue Form. Use o rótulo como chave."""
    campos = {**CAMPOS_PADRAO, **mudancas}
    return "\n\n".join(f"### {rotulo}\n\n{valor}" for rotulo, valor in campos.items())


def resposta_serpapi(preco=4000, nivel="typical", faixa=(3500, 5200), outros=()):
    return {
        "search_metadata": {"google_flights_url": "https://www.google.com/travel/flights?tfs=abc"},
        "best_flights": [
            {
                "flights": [
                    {"airline": "TAP", "departure_airport": {"id": "GRU", "time": "2027-03-15 18:00"},
                     "arrival_airport": {"id": "MAD", "time": "2027-03-16 08:00"}},
                    {"airline": "Iberia", "departure_airport": {"id": "MAD", "time": "2027-03-16 10:00"},
                     "arrival_airport": {"id": "LIS", "time": "2027-03-16 10:20"}},
                ],
                "layovers": [{"id": "MAD", "name": "Madrid", "duration": 120}],
                "total_duration": 755,
                "price": preco,
            }
        ],
        "other_flights": [{"flights": [{"airline": "LATAM"}], "total_duration": 600, "price": p} for p in outros],
        "price_insights": {"lowest_price": preco, "price_level": nivel, "typical_price_range": list(faixa)},
    }


SEM_VOOS = {"error": "Google Flights hasn't returned any results for this query."}


class Resposta:
    def __init__(self, dados, status=200):
        self._dados, self.status_code = dados, status

    def json(self):
        return self._dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class Internet:
    """Sessão HTTP falsa: responde pela API do GitHub e pela SerpApi."""

    def __init__(self):
        self.issues: dict[int, dict] = {}
        self.comentarios: list[tuple[int, str]] = []
        self.consultas: list[dict] = []
        self.serpapi = resposta_serpapi()   # dict, ou função(params) -> dict
        self.falhar_comentario_em: set[int] = set()

    def criar_issue(self, numero, corpo_, titulo="[Passagem] Teste"):
        self.issues[numero] = {"number": numero, "title": titulo, "body": corpo_, "state": "open"}

    def comentarios_de(self, numero):
        return [texto for n, texto in self.comentarios if n == numero]

    def get(self, url, params=None, headers=None, timeout=None):
        if url == serpapi.URL:
            self.consultas.append(params)
            dados = self.serpapi(params) if callable(self.serpapi) else self.serpapi
            return Resposta(dados)
        assert url.endswith("/repos/dono/repo/issues"), url
        assert headers["Authorization"] == "Bearer token-falso"
        abertas = [i for i in self.issues.values() if i["state"] == "open"]
        inicio = (params["page"] - 1) * params["per_page"]
        return Resposta(abertas[inicio:inicio + params["per_page"]])

    def post(self, url, json=None, headers=None, timeout=None):
        numero = int(url.split("/issues/")[1].split("/")[0])
        if numero in self.falhar_comentario_em:
            return Resposta({}, status=500)
        self.comentarios.append((numero, json["body"]))
        return Resposta({}, status=201)

    def patch(self, url, json=None, headers=None, timeout=None):
        self.issues[int(url.rsplit("/", 1)[1])].update(json)
        return Resposta({})


class CaixaDeSaida:
    """Substitui smtplib.SMTP / SMTP_SSL e guarda as mensagens enviadas."""

    def __init__(self):
        self.mensagens = []
        self.conexoes = []
        self.falhar = False

    def fabrica(self, ssl_direto):
        caixa = self

        class Servidor:
            def __init__(self, host, porta, **kwargs):
                caixa.conexoes.append({"host": host, "porta": porta, "ssl": ssl_direto, "tls": False})

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def starttls(self, context=None):
                caixa.conexoes[-1]["tls"] = True

            def login(self, usuario, senha):
                if caixa.falhar:
                    raise RuntimeError("login recusado")
                caixa.conexoes[-1]["login"] = (usuario, senha)

            def send_message(self, mensagem):
                caixa.mensagens.append(mensagem)

        return Servidor

    def para(self, destino):
        return [m for m in self.mensagens if m["To"] == destino]


def html_de(mensagem) -> str:
    return mensagem.get_body(preferencelist=("html",)).get_content()


@pytest.fixture
def internet():
    return Internet()


@pytest.fixture
def caixa(monkeypatch):
    caixa = CaixaDeSaida()
    monkeypatch.setattr(correio.smtplib, "SMTP", caixa.fabrica(ssl_direto=False))
    monkeypatch.setattr(correio.smtplib, "SMTP_SSL", caixa.fabrica(ssl_direto=True))
    return caixa


@pytest.fixture
def monitor(internet, caixa, tmp_path):
    smtp = correio.ConfigSMTP(usuario="eu@gmail.com", senha="senha-de-app")
    return Monitor(
        gh=GitHub("dono/repo", "token-falso", sessao=internet),
        consultar=lambda params: serpapi.consultar(params, "chave-falsa", sessao=internet, espera=0),
        enviar_email=lambda destino, assunto, html, texto: correio.enviar(smtp, destino, assunto, html, texto),
        email_padrao="eu@gmail.com",
        caminho=tmp_path / "data" / "historico.json",
    )
