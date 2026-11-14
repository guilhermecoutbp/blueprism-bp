"""Orquestração: percorre as issues de busca e aplica as regras de cada uma."""

from __future__ import annotations

import hashlib
import os
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import correio, historico, mensagens, regras, serpapi
from .formulario import interpretar
from .github import GitHub

FUSO = ZoneInfo("America/Sao_Paulo")
CAMINHO_HISTORICO = Path(__file__).resolve().parent.parent / "data" / "historico.json"
# O cron do GitHub atrasa alguns minutos; sem a folga, uma busca de 3 h rodaria a cada 4 h.
FOLGA = timedelta(minutes=20)


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def _log(numero, texto: str) -> None:
    print(f"[#{numero}] {texto}", flush=True)


class Monitor:
    """Reúne as dependências externas para que os testes possam substituí-las."""

    def __init__(self, gh, consultar, enviar_email, email_padrao: str = "", caminho=CAMINHO_HISTORICO):
        self.gh = gh
        self.consultar = consultar          # função(params) -> JSON da SerpApi
        self.enviar_email = enviar_email    # função(destino, assunto, html, texto)
        self.email_padrao = email_padrao
        self.caminho = Path(caminho)

    def executar(self, agora: datetime | None = None) -> int:
        """Processa todas as buscas abertas. Devolve o número de buscas com erro."""
        agora = agora or datetime.now(timezone.utc)
        dados = historico.carregar(self.caminho)
        buscas = dados["buscas"]
        falhas = 0
        try:
            issues = self.gh.listar_buscas()
            abertas = {str(issue["number"]) for issue in issues}
            for numero in [n for n in buscas if n not in abertas]:
                del buscas[numero]  # issue fechada manualmente: para de monitorar
            for issue in issues:
                try:
                    self._processar(issue, buscas, agora)
                except Exception:  # um erro em uma busca não derruba as outras
                    falhas += 1
                    _log(issue.get("number"), "ERRO inesperado:\n" + traceback.format_exc())
        finally:
            if historico.salvar(self.caminho, dados):
                print("Histórico atualizado.", flush=True)
        return falhas

    def _processar(self, issue: dict, buscas: dict, agora: datetime) -> None:
        numero = issue["number"]
        chave = str(numero)
        corpo = issue.get("body") or ""
        assinatura = _hash(corpo)

        estado = buscas.get(chave)
        if estado is None or estado.get("assinatura") != assinatura:
            # Busca nova ou editada: zera o histórico (mantém só o último erro já comentado).
            erro_anterior = estado.get("erro_cadastro") if estado else None
            estado = historico.novo_estado(assinatura)
            estado["erro_cadastro"] = erro_anterior
            buscas[chave] = estado

        busca, erros = interpretar(numero, corpo)
        hoje = agora.astimezone(FUSO).date()
        if busca and hoje > busca.monitorar_ate and estado["verificacoes"] == 0:
            erros = [
                f"**Datas**: o prazo de monitoramento ({busca.monitorar_ate:%d/%m/%Y}) já passou. "
                "Confira a data de ida e o campo \"Monitorar até\"."
            ]
        if erros:
            texto = mensagens.erro_cadastro(erros)
            if estado.get("erro_cadastro") != _hash(texto):
                self.gh.comentar(numero, texto)
                estado["erro_cadastro"] = _hash(texto)
                _log(numero, "cadastro com erro; comentei na issue.")
            else:
                _log(numero, "cadastro com erro (já comentado).")
            return
        estado["erro_cadastro"] = None
        destino = busca.email or self.email_padrao

        if hoje > busca.monitorar_ate:
            self._encerrar(busca, estado, destino)
            del buscas[chave]
            return

        ultima = estado.get("ultima_verificacao")
        if ultima:
            proxima = datetime.fromisoformat(ultima) + timedelta(hours=busca.frequencia_horas) - FOLGA
            if agora < proxima:
                _log(numero, f"ainda não é hora (a cada {busca.frequencia_horas} h).")
                return

        self._verificar(busca, estado, destino, agora)

    def _verificar(self, busca, estado: dict, destino: str, agora: datetime) -> None:
        numero = busca.numero
        oferta, motivo = None, ""
        try:
            oferta = serpapi.extrair_oferta(self.consultar(busca.parametros_serpapi()))
        except serpapi.SemResultado as erro:
            motivo = str(erro)
        estado["ultima_verificacao"] = agora.isoformat(timespec="seconds")
        estado["verificacoes"] += 1

        if oferta is None:
            _log(numero, f"sem resultado: {motivo}")
            if not estado["sem_resultado_avisado"]:
                self.gh.comentar(numero, mensagens.sem_resultado(motivo))
                estado["sem_resultado_avisado"] = True
            return
        estado["sem_resultado_avisado"] = False

        anteriores = [registro["preco"] for registro in estado["registros"]]
        menor_antes = estado["menor_preco"]
        decisao = regras.avaliar(
            oferta.preco, oferta.nivel, oferta.faixa_tipica, anteriores, busca.preco_alvo,
            estado["ultimo_aviso_preco"], estado["rearmado"],
        )
        historico.registrar_preco(estado, estado["ultima_verificacao"], oferta.preco)
        estado["rearmado"] = decisao.rearmado
        _log(numero, f"preço {oferta.preco:.2f}; motivos: {len(decisao.motivos)}; avisar: {decisao.avisar}")

        if not estado["iniciado"]:
            self.gh.comentar(numero, mensagens.iniciado(busca, oferta, destino))
            estado["iniciado"] = True

        if decisao.avisar:
            # Marca antes de enviar: se o comentário falhar, não repete o e-mail a cada hora.
            estado["ultimo_aviso_preco"] = oferta.preco
            envio = self._email(numero, destino, mensagens.oferta_email(busca, oferta, decisao.motivos, menor_antes))
            self.gh.comentar(
                numero, mensagens.oferta_comentario(busca, oferta, decisao.motivos, menor_antes, envio)
            )

    def _encerrar(self, busca, estado: dict, destino: str) -> None:
        envio = self._email(busca.numero, destino, mensagens.encerramento_email(busca, estado))
        self.gh.comentar(busca.numero, mensagens.encerramento_comentario(busca, estado) + "\n\n" + envio)
        self.gh.fechar(busca.numero)
        _log(busca.numero, "prazo encerrado; issue fechada.")

    def _email(self, numero: int, destino: str, conteudo: tuple[str, str, str]) -> str:
        """Envia o e-mail e devolve a frase que vai no comentário da issue."""
        assunto, html, texto = conteudo
        try:
            self.enviar_email(destino, assunto, html, texto)
        except Exception as erro:
            _log(numero, f"falha ao enviar e-mail: {erro!r}")
            return f"⚠️ Não consegui enviar o e-mail ({erro}). Confira os secrets de SMTP."
        return f"📧 E-mail enviado para {destino}."


def main(env=None) -> int:
    env = os.environ if env is None else env
    repositorio, token = env.get("GITHUB_REPOSITORY"), env.get("GITHUB_TOKEN")
    if not repositorio or not token:
        print("Defina GITHUB_REPOSITORY e GITHUB_TOKEN.")
        return 2

    smtp = correio.ConfigSMTP.do_ambiente(env)
    chave = (env.get("SERPAPI_KEY") or "").strip()
    monitor = Monitor(
        gh=GitHub(repositorio, token),
        consultar=lambda params: serpapi.consultar(params, chave),
        enviar_email=lambda destino, assunto, html, texto: correio.enviar(smtp, destino, assunto, html, texto),
        email_padrao=(env.get("EMAIL_DESTINO") or "").strip() or smtp.usuario,
    )
    falhas = monitor.executar()
    if falhas:
        print(f"{falhas} busca(s) terminaram com erro; veja o log acima.")
        return 1
    return 0
