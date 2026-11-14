"""Leitura e validação do formulário de cadastro (Issue Form) de uma busca."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta

MAX_PASSAGEIROS = 9
FREQUENCIAS = (1, 2, 3, 6, 12, 24)
FREQUENCIA_PADRAO = 3
VAZIOS = {"", "_no response_", "none", "nenhum", "nenhuma"}

# Início do rótulo (sem acentos, minúsculo) -> nome interno do campo.
ROTULOS = (
    ("origem", "origem"),
    ("destino", "destino"),
    ("tipo", "tipo"),
    ("data de ida", "data_ida"),
    ("data de volta", "data_volta"),
    ("adultos", "adultos"),
    ("idade", "criancas"),
    ("bebes", "bebes_colo"),
    ("classe", "classe"),
    ("escalas", "escalas"),
    ("bagagens", "bagagens"),
    ("preco", "preco_alvo"),
    ("frequencia", "frequencia"),
    ("monitorar", "monitorar_ate"),
    ("e-mail", "email"),
    ("email", "email"),
)

NOMES_CLASSE = {1: "Econômica", 2: "Econômica premium", 3: "Executiva", 4: "Primeira classe"}
NOMES_ESCALAS = {0: "Qualquer número de escalas", 1: "Somente voos diretos",
                 2: "No máximo 1 escala", 3: "No máximo 2 escalas"}


@dataclass
class Busca:
    numero: int
    origens: list[str]
    destinos: list[str]
    ida_e_volta: bool
    data_ida: date
    data_volta: date | None
    adultos: int
    criancas: int
    bebes_assento: int
    bebes_colo: int
    classe: int
    escalas: int
    bagagens: int
    preco_alvo: float | None
    frequencia_horas: int
    monitorar_ate: date
    email: str | None

    @property
    def passageiros(self) -> int:
        return self.adultos + self.criancas + self.bebes_assento + self.bebes_colo

    @property
    def com_assento(self) -> int:
        return self.adultos + self.criancas + self.bebes_assento

    def parametros_serpapi(self) -> dict:
        """Parâmetros da engine google_flights da SerpApi para esta busca."""
        params = {
            "engine": "google_flights",
            "departure_id": ",".join(self.origens),
            "arrival_id": ",".join(self.destinos),
            "outbound_date": self.data_ida.isoformat(),
            "type": 1 if self.ida_e_volta else 2,
            "travel_class": self.classe,
            "adults": self.adultos,
            "children": self.criancas,
            "infants_in_seat": self.bebes_assento,
            "infants_on_lap": self.bebes_colo,
            "stops": self.escalas,
            "bags": self.bagagens,
            "currency": "BRL",
            "hl": "pt-BR",
            "gl": "br",
        }
        if self.ida_e_volta and self.data_volta:
            params["return_date"] = self.data_volta.isoformat()
        return params


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.strip().lower()


def ler_secoes(corpo: str) -> dict[str, str]:
    """Divide o corpo da issue ("### Rótulo" + valor) em campos internos."""
    campos: dict[str, str] = {}
    atual = None
    linhas: list[str] = []

    def fechar():
        if atual is None:
            return
        valor = "\n".join(linhas).strip()
        if _normalizar(valor) in VAZIOS:
            valor = ""
        campos.setdefault(atual, valor)

    for linha in (corpo or "").replace("\r\n", "\n").split("\n"):
        if linha.startswith("### "):
            fechar()
            rotulo = _normalizar(linha[4:])
            atual = next((nome for inicio, nome in ROTULOS if rotulo.startswith(inicio)), "")
            atual = atual or None
            linhas = []
        elif atual is not None:
            linhas.append(linha)
    fechar()
    return campos


def _data(texto: str) -> date | None:
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _aeroportos(texto: str, nome: str, erros: list[str]) -> list[str]:
    if not texto:
        erros.append(f"**{nome}**: informe pelo menos um código IATA (ex.: GRU).")
        return []
    codigos = [c.strip().upper() for c in re.split(r"[,;\s]+", texto) if c.strip()]
    invalidos = [c for c in codigos if not re.fullmatch(r"[A-Z]{3}", c)]
    if invalidos:
        erros.append(
            f"**{nome}**: código IATA inválido ({', '.join(invalidos)}). "
            "Use códigos de 3 letras separados por vírgula, ex.: GRU,CGH,VCP."
        )
        return []
    return list(dict.fromkeys(codigos))


def _inteiro(texto: str, nome: str, erros: list[str], padrao: int | None = None) -> int | None:
    if not texto:
        if padrao is None:
            erros.append(f"**{nome}**: campo obrigatório.")
        return padrao
    if not re.fullmatch(r"\d{1,3}", texto.strip()):
        erros.append(f"**{nome}**: informe um número inteiro (recebi \"{texto}\").")
        return None
    return int(texto)


def _idades(texto: str, erros: list[str]) -> list[int]:
    if not texto:
        return []
    limpo = re.sub(r"\banos?\b|\be\b", " ", _normalizar(texto))
    if re.search(r"[^\d,;\s]", limpo):
        erros.append(
            "**Idade de cada criança**: informe só as idades separadas por vírgula, "
            f"ex.: 7, 4, 1 (recebi \"{texto}\")."
        )
        return []
    return [int(i) for i in re.findall(r"\d+", limpo)]


def _preco(texto: str, erros: list[str]) -> float | None:
    if not texto:
        return None
    limpo = re.sub(r"(?i)r\$|\s", "", texto)
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", limpo):
        limpo = limpo.replace(".", "")
    try:
        valor = float(limpo)
    except ValueError:
        valor = 0
    if valor <= 0:
        erros.append(f"**Preço-alvo**: informe um valor em reais, ex.: 3.500,00 (recebi \"{texto}\").")
        return None
    return valor


def _opcao(texto: str, opcoes: tuple[tuple[str, int], ...], nome: str, erros: list[str]) -> int:
    normal = _normalizar(texto)
    if not normal:
        return opcoes[0][1]
    for trecho, valor in opcoes:
        if trecho in normal:
            return valor
    erros.append(f"**{nome}**: opção não reconhecida (\"{texto}\").")
    return opcoes[0][1]


def interpretar(numero: int, corpo: str) -> tuple[Busca | None, list[str]]:
    """Converte o corpo da issue em uma Busca. Devolve (busca, erros)."""
    campos = ler_secoes(corpo)
    erros: list[str] = []
    if not campos:
        return None, [
            "Não encontrei os campos do formulário. Crie a busca pelo formulário "
            "**Monitorar passagem** (New issue) ou restaure os títulos \"### ...\" do texto."
        ]

    def campo(nome: str) -> str:
        return campos.get(nome, "")

    origens = _aeroportos(campo("origem"), "Origem", erros)
    destinos = _aeroportos(campo("destino"), "Destino", erros)
    repetidos = sorted(set(origens) & set(destinos))
    if repetidos:
        erros.append(f"**Origem/Destino**: {', '.join(repetidos)} aparece nos dois campos.")

    ida_e_volta = "somente" not in _normalizar(campo("tipo")) and "so ida" not in _normalizar(campo("tipo"))

    data_ida = _data(campo("data_ida"))
    if not data_ida:
        erros.append("**Data de ida**: use o formato DD/MM/AAAA, ex.: 15/03/2027.")

    data_volta = None
    if ida_e_volta:
        data_volta = _data(campo("data_volta"))
        if not data_volta:
            erros.append(
                "**Data de volta**: obrigatória para ida e volta, no formato DD/MM/AAAA "
                "(ou mude o tipo para \"Somente ida\")."
            )
        elif data_ida and data_volta < data_ida:
            erros.append("**Data de volta**: não pode ser antes da data de ida.")

    informados = _inteiro(campo("adultos"), "Adultos", erros)
    idades = _idades(campo("criancas"), erros)
    bebes_no_colo = "[x]" in campo("bebes_colo").lower()

    adultos = (informados or 0) + sum(1 for i in idades if i >= 12)
    criancas = sum(1 for i in idades if 2 <= i <= 11)
    bebes = sum(1 for i in idades if i < 2)
    bebes_colo = bebes if bebes_no_colo else 0
    bebes_assento = 0 if bebes_no_colo else bebes
    total = adultos + criancas + bebes
    com_assento = adultos + criancas + bebes_assento

    if informados is not None:
        if adultos < 1:
            erros.append("**Adultos**: é preciso pelo menos 1 passageiro com 12 anos ou mais.")
        if total > MAX_PASSAGEIROS:
            erros.append(
                f"**Passageiros**: o máximo é {MAX_PASSAGEIROS} por busca (recebi {total})."
            )
        if bebes_colo > adultos:
            erros.append(
                f"**Bebês no colo**: há {bebes_colo} bebê(s) no colo para {adultos} adulto(s). "
                "Cada bebê no colo precisa de um adulto; desmarque a opção para que viajem com assento."
            )

    bagagens = _inteiro(campo("bagagens"), "Bagagens de mão", erros, padrao=0)
    if bagagens is not None and informados is not None and bagagens > com_assento:
        erros.append(
            f"**Bagagens de mão**: {bagagens} é mais do que os {com_assento} passageiro(s) com assento."
        )

    classe = _opcao(campo("classe"), (("econ", 1), ("premium", 2), ("executiva", 3), ("primeira", 4)),
                    "Classe", erros)
    if "premium" in _normalizar(campo("classe")):
        classe = 2
    escalas = _opcao(campo("escalas"), (("qualquer", 0), ("direto", 1), ("1", 2), ("2", 3)),
                     "Escalas", erros)
    preco_alvo = _preco(campo("preco_alvo"), erros)

    frequencia = FREQUENCIA_PADRAO
    if campo("frequencia"):
        achado = re.search(r"\d+", campo("frequencia"))
        if achado and int(achado.group()) in FREQUENCIAS:
            frequencia = int(achado.group())
        else:
            erros.append("**Frequência de verificação**: escolha 1, 2, 3, 6, 12 ou 24 horas.")

    monitorar_ate = None
    if campo("monitorar_ate"):
        monitorar_ate = _data(campo("monitorar_ate"))
        if not monitorar_ate:
            erros.append("**Monitorar até**: use o formato DD/MM/AAAA ou deixe em branco.")
    if data_ida:
        if monitorar_ate is None and not campo("monitorar_ate"):
            monitorar_ate = data_ida - timedelta(days=1)
        elif monitorar_ate and monitorar_ate > data_ida:
            monitorar_ate = data_ida

    email = campo("email") or None
    if email and not re.fullmatch(r"[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+", email):
        erros.append(f"**E-mail**: endereço inválido (\"{email}\").")

    if erros:
        return None, erros
    return Busca(
        numero=numero, origens=origens, destinos=destinos, ida_e_volta=ida_e_volta,
        data_ida=data_ida, data_volta=data_volta, adultos=adultos, criancas=criancas,
        bebes_assento=bebes_assento, bebes_colo=bebes_colo, classe=classe, escalas=escalas,
        bagagens=bagagens, preco_alvo=preco_alvo, frequencia_horas=frequencia,
        monitorar_ate=monitorar_ate, email=email,
    ), []
