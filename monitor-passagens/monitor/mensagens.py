"""Textos dos comentários nas issues e dos e-mails (português do Brasil)."""

from __future__ import annotations

from html import escape

from .formato import brl, data_br, duracao, plural
from .formulario import NOMES_CLASSE, NOMES_ESCALAS, Busca
from .serpapi import Oferta

NIVEIS = {"low": "baixo", "typical": "típico", "high": "alto"}
LEMBRETE = (
    "Os preços mudam rápido: confirme o valor final no site antes de comprar. "
    "O total é para todos os passageiros da busca."
)


def rota(busca: Busca) -> str:
    seta = "⇄" if busca.ida_e_volta else "→"
    return f"{', '.join(busca.origens)} {seta} {', '.join(busca.destinos)}"


def datas(busca: Busca) -> str:
    if busca.ida_e_volta:
        return f"{data_br(busca.data_ida)} a {data_br(busca.data_volta)}"
    return f"{data_br(busca.data_ida)} (somente ida)"


def passageiros(busca: Busca) -> str:
    partes = [plural(busca.adultos, "adulto", "adultos")]
    if busca.criancas:
        partes.append(plural(busca.criancas, "criança", "crianças"))
    if busca.bebes_assento:
        partes.append(plural(busca.bebes_assento, "bebê com assento", "bebês com assento"))
    if busca.bebes_colo:
        partes.append(plural(busca.bebes_colo, "bebê no colo", "bebês no colo"))
    return ", ".join(partes)


def escalas(oferta: Oferta) -> str:
    if oferta.escalas == 0:
        return "Voo direto"
    texto = plural(oferta.escalas, "escala", "escalas")
    return f"{texto} ({', '.join(oferta.conexoes)})" if oferta.conexoes else texto


def companhias(oferta: Oferta) -> str:
    return ", ".join(oferta.companhias) or "não informada"


def faixa(oferta: Oferta) -> str:
    if not oferta.faixa_tipica:
        return "não informada pelo Google Flights"
    return f"{brl(oferta.faixa_tipica[0])} a {brl(oferta.faixa_tipica[1])}"


def _resumo_busca(busca: Busca) -> list[str]:
    linhas = [
        f"- **Rota:** {rota(busca)}",
        f"- **Datas:** {datas(busca)}",
        f"- **Passageiros:** {passageiros(busca)}",
        f"- **Classe:** {NOMES_CLASSE[busca.classe]} · {NOMES_ESCALAS[busca.escalas]}"
        + (f" · {plural(busca.bagagens, 'bagagem de mão', 'bagagens de mão')}" if busca.bagagens else ""),
    ]
    if busca.preco_alvo:
        linhas.append(f"- **Preço-alvo:** {brl(busca.preco_alvo)}")
    return linhas


def _detalhes_voo(oferta: Oferta) -> str:
    trecho = f"{oferta.origem} → {oferta.destino} · " if oferta.origem and oferta.destino else ""
    return f"{trecho}{companhias(oferta)} · {escalas(oferta)} · {duracao(oferta.duracao_min)}"


def erro_cadastro(erros: list[str]) -> str:
    itens = "\n".join(f"- {erro}" for erro in erros)
    return (
        "⚠️ **Não consegui iniciar o monitoramento.** Corrija os pontos abaixo editando "
        "esta issue (menu **···** → **Edit**); ao salvar, eu valido de novo automaticamente.\n\n"
        f"{itens}"
    )


def iniciado(busca: Busca, oferta: Oferta, destino: str) -> str:
    linhas = ["✅ **Monitoramento iniciado**", ""]
    linhas += _resumo_busca(busca)
    linhas += [
        f"- **Preço atual:** **{brl(oferta.preco)}** ({_detalhes_voo(oferta)})",
        f"- **Faixa típica:** {faixa(oferta)}",
    ]
    if oferta.nivel in NIVEIS:
        linhas.append(f"- **Nível do preço hoje:** {NIVEIS[oferta.nivel]}")
    linhas += [
        f"- **Verificação:** a cada {busca.frequencia_horas} h, até {data_br(busca.monitorar_ate)}",
        f"- **Avisos por e-mail para:** {destino or 'ninguém (configure SMTP_USER ou EMAIL_DESTINO)'}",
        "",
        "Para parar, feche esta issue. Para mudar a busca, edite a issue (o histórico recomeça).",
    ]
    return "\n".join(linhas)


def sem_resultado(motivo: str) -> str:
    return (
        "🔎 **A SerpApi não retornou resultado para esta busca.**\n\n"
        f"Resposta: _{motivo}_\n\n"
        "Vou continuar tentando na frequência configurada e não repito este aviso enquanto "
        "o problema persistir. Se a rota ou as datas estiverem erradas, edite a issue."
    )


def oferta_comentario(busca: Busca, oferta: Oferta, motivos: list[str], menor_antes, envio: str) -> str:
    linhas = [
        f"🔥 **Oferta encontrada: {brl(oferta.preco)}**",
        "",
        f"- **Voo:** {_detalhes_voo(oferta)}",
        f"- **Datas:** {datas(busca)} · {passageiros(busca)}",
        f"- **Menor preço visto antes:** {brl(menor_antes) if menor_antes else 'primeira verificação'}",
        "",
        "**Por que avisei:**",
    ]
    linhas += [f"- {motivo}" for motivo in motivos]
    linhas.append("")
    if oferta.url:
        linhas.append(f"👉 [Ver no Google Flights]({oferta.url})")
        linhas.append("")
    linhas += [f"_{LEMBRETE}_", "", envio]
    return "\n".join(linhas)


def _sem_negrito(texto: str) -> str:
    return texto.replace("**", "")


def _pagina(titulo: str, miolo: str, numero: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><body style="margin:0;padding:24px;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;color:#111827;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:12px;padding:28px;">
<tr><td>
<p style="margin:0 0 4px;font-size:13px;color:#6b7280;">Monitor de Passagens · busca #{numero}</p>
<h1 style="margin:0 0 16px;font-size:22px;">{escape(titulo)}</h1>
{miolo}
</td></tr></table>
</td></tr></table>
</body></html>"""


def _linha(rotulo: str, valor: str) -> str:
    return (
        '<tr><td style="padding:6px 12px 6px 0;color:#6b7280;font-size:14px;white-space:nowrap;'
        f'vertical-align:top;">{escape(rotulo)}</td>'
        f'<td style="padding:6px 0;font-size:14px;">{escape(valor)}</td></tr>'
    )


def oferta_email(busca: Busca, oferta: Oferta, motivos: list[str], menor_antes) -> tuple[str, str, str]:
    """Devolve (assunto, html, texto) do e-mail de oferta."""
    assunto = f"✈️ {brl(oferta.preco)} · {rota(busca)} · {data_br(busca.data_ida)}"
    antes = brl(menor_antes) if menor_antes else "primeira verificação"
    motivos_limpos = [_sem_negrito(m) for m in motivos]
    itens = "".join(f'<li style="margin-bottom:4px;">{escape(m)}</li>' for m in motivos_limpos)
    botao = ""
    if oferta.url:
        botao = (
            f'<p style="margin:24px 0;"><a href="{escape(oferta.url, quote=True)}" '
            'style="background:#1a73e8;color:#ffffff;text-decoration:none;padding:12px 22px;'
            'border-radius:8px;font-weight:bold;display:inline-block;">Ver no Google Flights</a></p>'
        )
    miolo = f"""<p style="margin:0;font-size:36px;font-weight:bold;color:#15803d;">{escape(brl(oferta.preco))}</p>
<p style="margin:4px 0 16px;font-size:13px;color:#6b7280;">total para {escape(passageiros(busca))}</p>
<table role="presentation" cellpadding="0" cellspacing="0">
{_linha("Rota", rota(busca))}
{_linha("Datas", datas(busca))}
{_linha("Companhias", companhias(oferta))}
{_linha("Escalas", escalas(oferta))}
{_linha("Duração", duracao(oferta.duracao_min))}
{_linha("Classe", NOMES_CLASSE[busca.classe])}
{_linha("Faixa típica", faixa(oferta))}
{_linha("Menor preço visto antes", antes)}
</table>
<h2 style="margin:20px 0 8px;font-size:16px;">Por que você recebeu este aviso</h2>
<ul style="margin:0;padding-left:20px;font-size:14px;">{itens}</ul>
{botao}
<p style="margin:0;padding:12px;background:#fef9c3;border-radius:8px;font-size:13px;">⚠️ {escape(LEMBRETE)}</p>"""
    texto = "\n".join(
        [
            f"Oferta encontrada: {brl(oferta.preco)} (total para {passageiros(busca)})",
            f"Rota: {rota(busca)}",
            f"Datas: {datas(busca)}",
            f"Companhias: {companhias(oferta)}",
            f"Escalas: {escalas(oferta)}",
            f"Duração: {duracao(oferta.duracao_min)}",
            f"Menor preço visto antes: {antes}",
            "",
            "Por que você recebeu este aviso:",
            *[f"- {m}" for m in motivos_limpos],
            "",
            f"Ver no Google Flights: {oferta.url}" if oferta.url else "",
            "",
            LEMBRETE,
        ]
    )
    return assunto, _pagina("Passagem abaixo do mercado", miolo, busca.numero), texto


def _resumo_final(estado: dict) -> list[tuple[str, str]]:
    verificacoes = estado.get("verificacoes", 0)
    menor, maior = estado.get("menor_preco"), estado.get("maior_preco")
    return [
        ("Verificações feitas", str(verificacoes)),
        ("Menor preço visto", brl(menor) if menor else "nenhum preço encontrado"),
        ("Maior preço visto", brl(maior) if maior else "nenhum preço encontrado"),
    ]


def encerramento_comentario(busca: Busca, estado: dict) -> str:
    linhas = [
        "🏁 **Monitoramento encerrado**",
        "",
        f"O prazo desta busca terminou ({data_br(busca.monitorar_ate)}).",
        "",
    ]
    linhas += [f"- **{rotulo}:** {valor}" for rotulo, valor in _resumo_final(estado)]
    linhas += ["", "Estou fechando a issue. Para monitorar outra viagem, crie uma nova busca pelo formulário."]
    return "\n".join(linhas)


def encerramento_email(busca: Busca, estado: dict) -> tuple[str, str, str]:
    assunto = f"🏁 Monitoramento encerrado · {rota(busca)} · {data_br(busca.data_ida)}"
    resumo = _resumo_final(estado)
    miolo = f"""<p style="font-size:14px;">O prazo desta busca terminou em {escape(data_br(busca.monitorar_ate))} e a issue foi fechada.</p>
<table role="presentation" cellpadding="0" cellspacing="0">
{_linha("Rota", rota(busca))}
{_linha("Datas", datas(busca))}
{"".join(_linha(r, v) for r, v in resumo)}
</table>
<p style="font-size:14px;">Para monitorar outra viagem, crie uma nova busca pelo formulário.</p>"""
    texto = "\n".join(
        [f"Monitoramento encerrado: {rota(busca)}, {datas(busca)}", ""]
        + [f"{r}: {v}" for r, v in resumo]
    )
    return assunto, _pagina("Monitoramento encerrado", miolo, busca.numero), texto
