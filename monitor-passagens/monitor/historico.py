"""Estado e histórico de preços de cada busca (data/historico.json)."""

from __future__ import annotations

import json
from pathlib import Path

MAX_REGISTROS = 500
VERSAO = 1


def carregar(caminho) -> dict:
    caminho = Path(caminho)
    if caminho.exists() and caminho.read_text(encoding="utf-8").strip():
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    else:
        dados = {}
    dados.setdefault("versao", VERSAO)
    dados.setdefault("buscas", {})
    return dados


def serializar(dados: dict) -> str:
    return json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def salvar(caminho, dados: dict) -> bool:
    """Grava o arquivo só se o conteúdo mudou. Devolve True se gravou."""
    caminho = Path(caminho)
    novo = serializar(dados)
    if caminho.exists() and caminho.read_text(encoding="utf-8") == novo:
        return False
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(novo, encoding="utf-8")
    return True


def novo_estado(assinatura: str) -> dict:
    return {
        "assinatura": assinatura,
        "erro_cadastro": None,
        "ultima_verificacao": None,
        "verificacoes": 0,
        "iniciado": False,
        "sem_resultado_avisado": False,
        "registros": [],
        "menor_preco": None,
        "maior_preco": None,
        "ultimo_aviso_preco": None,
        "rearmado": False,
    }


def registrar_preco(estado: dict, quando: str, preco: float) -> None:
    estado["registros"].append({"quando": quando, "preco": preco})
    del estado["registros"][:-MAX_REGISTROS]
    if estado["menor_preco"] is None or preco < estado["menor_preco"]:
        estado["menor_preco"] = preco
    if estado["maior_preco"] is None or preco > estado["maior_preco"]:
        estado["maior_preco"] = preco
