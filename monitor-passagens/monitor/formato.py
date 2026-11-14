"""Formatação de valores para exibição em português do Brasil."""

from __future__ import annotations

from datetime import date


def brl(valor: float) -> str:
    """Formata um número como R$ 1.234,56."""
    texto = f"{float(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(dia: date) -> str:
    return dia.strftime("%d/%m/%Y")


def duracao(minutos: int | None) -> str:
    if not minutos:
        return "não informada"
    horas, resto = divmod(int(minutos), 60)
    if horas and resto:
        return f"{horas}h {resto:02d}min"
    if horas:
        return f"{horas}h"
    return f"{resto}min"


def plural(quantidade: int, singular: str, plural_: str) -> str:
    return f"{quantidade} {singular if quantidade == 1 else plural_}"
