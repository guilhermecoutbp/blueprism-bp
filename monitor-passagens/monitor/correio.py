"""Envio de e-mail por SMTP (Gmail com senha de app por padrão)."""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass
class ConfigSMTP:
    usuario: str
    senha: str
    host: str = "smtp.gmail.com"
    porta: int = 587

    @classmethod
    def do_ambiente(cls, env) -> "ConfigSMTP":
        return cls(
            usuario=(env.get("SMTP_USER") or "").strip(),
            senha=env.get("SMTP_PASSWORD") or "",
            host=(env.get("SMTP_HOST") or "").strip() or "smtp.gmail.com",
            porta=int((env.get("SMTP_PORT") or "").strip() or 587),
        )


def enviar(config: ConfigSMTP, destino: str, assunto: str, html: str, texto: str) -> None:
    if not config.usuario or not config.senha:
        raise RuntimeError("os secrets SMTP_USER e SMTP_PASSWORD não estão configurados")
    if not destino:
        raise RuntimeError("nenhum e-mail de destino definido")

    mensagem = EmailMessage()
    mensagem["From"] = f"Monitor de Passagens <{config.usuario}>"
    mensagem["To"] = destino
    mensagem["Subject"] = assunto
    mensagem.set_content(texto)
    mensagem.add_alternative(html, subtype="html")

    contexto = ssl.create_default_context()
    if config.porta == 465:
        servidor = smtplib.SMTP_SSL(config.host, config.porta, timeout=30, context=contexto)
    else:
        servidor = smtplib.SMTP(config.host, config.porta, timeout=30)
    with servidor:
        if config.porta != 465:
            servidor.starttls(context=contexto)
        servidor.login(config.usuario, config.senha)
        servidor.send_message(mensagem)
