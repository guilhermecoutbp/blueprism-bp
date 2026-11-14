"""Acesso mínimo à API do GitHub: listar buscas, comentar e fechar issues."""

from __future__ import annotations

import requests

PREFIXO_TITULO = "[Passagem]"


class GitHub:
    def __init__(self, repositorio: str, token: str, sessao=None, api: str = "https://api.github.com"):
        self.base = f"{api}/repos/{repositorio}"
        self.sessao = sessao or requests.Session()
        self.cabecalhos = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _pedir(self, metodo: str, caminho: str, **kwargs):
        resposta = getattr(self.sessao, metodo)(
            self.base + caminho, headers=self.cabecalhos, timeout=30, **kwargs
        )
        resposta.raise_for_status()
        return resposta.json()

    def listar_buscas(self) -> list[dict]:
        """Issues abertas cujo título começa com [Passagem] (ignora pull requests)."""
        buscas, pagina = [], 1
        while True:
            lote = self._pedir(
                "get", "/issues",
                params={"state": "open", "per_page": 100, "page": pagina, "direction": "asc"},
            )
            buscas += [
                issue for issue in lote
                if "pull_request" not in issue
                and (issue.get("title") or "").strip().startswith(PREFIXO_TITULO)
            ]
            if len(lote) < 100:
                return buscas
            pagina += 1

    def comentar(self, numero: int, texto: str) -> None:
        self._pedir("post", f"/issues/{numero}/comments", json={"body": texto})

    def fechar(self, numero: int) -> None:
        self._pedir("patch", f"/issues/{numero}", json={"state": "closed", "state_reason": "completed"})
