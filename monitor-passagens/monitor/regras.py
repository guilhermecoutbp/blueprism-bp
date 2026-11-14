"""Regra de "abaixo do mercado" e trava anti-spam."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median

from .formato import brl

MIN_HISTORICO = 8          # verificações antes de usar a mediana própria
DESCONTO_MEDIANA = 0.10    # 10% abaixo da mediana
QUEDA_REAVISO = 0.03       # só reavisa se cair mais 3% desde o último aviso
ALTA_REARME = 0.10         # subir mais de 10% acima do último aviso libera novo aviso


@dataclass
class Decisao:
    motivos: list[str] = field(default_factory=list)
    avisar: bool = False
    rearmado: bool = False


def motivos_de_oferta(preco, nivel, faixa_tipica, anteriores, preco_alvo) -> list[str]:
    motivos = []
    if nivel == "low":
        motivos.append("O Google Flights classifica este preço como **baixo** para a rota.")
    if faixa_tipica and preco < faixa_tipica[0]:
        motivos.append(
            f"Está abaixo da faixa típica da rota ({brl(faixa_tipica[0])} a {brl(faixa_tipica[1])})."
        )
    if len(anteriores) >= MIN_HISTORICO:
        mediana = median(anteriores)
        if preco <= mediana * (1 - DESCONTO_MEDIANA):
            queda = (1 - preco / mediana) * 100
            motivos.append(
                f"Está {queda:.0f}% abaixo da mediana do seu histórico "
                f"({brl(mediana)} em {len(anteriores)} verificações)."
            )
    if preco_alvo and preco <= preco_alvo:
        motivos.append(f"Atingiu o seu preço-alvo de {brl(preco_alvo)}.")
    return motivos


def avaliar(preco, nivel, faixa_tipica, anteriores, preco_alvo, ultimo_aviso, rearmado) -> Decisao:
    """Decide se o preço atual merece um aviso.

    `ultimo_aviso` é o preço do último aviso enviado (ou None) e `rearmado` indica
    que o preço já subiu mais de 10% acima dele, liberando um novo aviso.
    """
    motivos = motivos_de_oferta(preco, nivel, faixa_tipica, anteriores, preco_alvo)
    avisar = bool(motivos) and (
        ultimo_aviso is None or rearmado or preco <= ultimo_aviso * (1 - QUEDA_REAVISO)
    )
    if avisar:
        return Decisao(motivos=motivos, avisar=True, rearmado=False)
    # A alta em si não gera aviso: ela só libera o aviso para uma verificação seguinte.
    if ultimo_aviso is not None and preco > ultimo_aviso * (1 + ALTA_REARME):
        rearmado = True
    return Decisao(motivos=motivos, avisar=False, rearmado=rearmado)
