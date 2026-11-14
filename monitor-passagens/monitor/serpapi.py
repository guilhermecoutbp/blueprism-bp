"""Consulta de preços na SerpApi (engine google_flights)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

URL = "https://serpapi.com/search.json"


class SemResultado(Exception):
    """A SerpApi respondeu, mas sem voos (ou com uma mensagem de erro)."""


@dataclass
class Oferta:
    preco: float
    companhias: list[str] = field(default_factory=list)
    escalas: int = 0
    conexoes: list[str] = field(default_factory=list)
    duracao_min: int | None = None
    origem: str = ""
    destino: str = ""
    partida: str = ""
    chegada: str = ""
    url: str = ""
    nivel: str | None = None
    faixa_tipica: tuple[float, float] | None = None


def consultar(params: dict, chave: str, sessao=None, tentativas: int = 3, espera: float = 5) -> dict:
    """Faz a consulta e devolve o JSON. Erros de rede são repetidos algumas vezes."""
    if not chave:
        raise RuntimeError("O secret SERPAPI_KEY não está configurado.")
    sessao = sessao or requests
    ultimo_erro: Exception | None = None
    for tentativa in range(tentativas):
        try:
            resposta = sessao.get(URL, params={**params, "api_key": chave}, timeout=90)
            if resposta.status_code >= 500:
                raise requests.HTTPError(f"SerpApi respondeu HTTP {resposta.status_code}")
            try:
                dados = resposta.json()
            except ValueError:
                raise requests.HTTPError(
                    f"SerpApi respondeu HTTP {resposta.status_code} sem JSON válido"
                ) from None
            return dados
        except requests.RequestException as erro:
            # A mensagem do requests pode conter a URL com a chave: não repassar.
            ultimo_erro = RuntimeError(f"Falha de rede ao consultar a SerpApi ({type(erro).__name__}).")
            if tentativa < tentativas - 1:
                time.sleep(espera)
    raise ultimo_erro


def extrair_oferta(dados: dict) -> Oferta:
    """Menor preço entre best_flights e other_flights. Levanta SemResultado se não houver."""
    opcoes = [
        voo
        for grupo in ("best_flights", "other_flights")
        for voo in (dados.get(grupo) or [])
        if isinstance(voo.get("price"), (int, float)) and voo["price"] > 0
    ]
    if not opcoes:
        raise SemResultado(str(dados.get("error") or "nenhum voo com preço foi retornado."))

    melhor = min(opcoes, key=lambda voo: voo["price"])
    trechos = melhor.get("flights") or []
    insights = dados.get("price_insights") or {}
    faixa = insights.get("typical_price_range")
    faixa_tipica = None
    if isinstance(faixa, (list, tuple)) and len(faixa) == 2 and all(
        isinstance(v, (int, float)) for v in faixa
    ):
        faixa_tipica = (float(faixa[0]), float(faixa[1]))

    primeiro = trechos[0] if trechos else {}
    ultimo = trechos[-1] if trechos else {}
    return Oferta(
        preco=float(melhor["price"]),
        companhias=list(dict.fromkeys(t["airline"] for t in trechos if t.get("airline"))),
        escalas=max(len(trechos) - 1, 0),
        conexoes=[c.get("id") or c.get("name") or "?" for c in (melhor.get("layovers") or [])],
        duracao_min=melhor.get("total_duration"),
        origem=(primeiro.get("departure_airport") or {}).get("id", ""),
        destino=(ultimo.get("arrival_airport") or {}).get("id", ""),
        partida=(primeiro.get("departure_airport") or {}).get("time", ""),
        chegada=(ultimo.get("arrival_airport") or {}).get("time", ""),
        url=(dados.get("search_metadata") or {}).get("google_flights_url", ""),
        nivel=insights.get("price_level"),
        faixa_tipica=faixa_tipica,
    )
