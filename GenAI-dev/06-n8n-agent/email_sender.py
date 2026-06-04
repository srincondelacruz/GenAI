# email_sender.py — envío del informe de noticias por Gmail
# Convierte el Markdown del agente a HTML limpio antes de enviarlo.
# Usa SMTP con App Password (no OAuth) para simplicidad.

import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os


def _md_to_html(text: str) -> str:
    """
    Convierte el Markdown del agente a HTML para el email.
    Pasos en orden:
      1. Elimina imágenes de thumbnail (no se renderizan en email)
      2. Mueve la fecha al lado del título para mejor legibilidad
      3. Convierte links, negritas y cursivas
      4. Convierte saltos de línea a <br>
    """
    # Elimina líneas de thumbnails generadas por SerpAPI
    text = re.sub(r'!\[thumbnail\]\([^)]+\)', '', text)

    # Mueve la fecha junto al título:
    # **[titulo](url)**\n*Fuente: X*\n*Fecha: Y*  →  **[titulo](url)** — Y\n*Fuente: X*
    text = re.sub(
        r'(\*\*\[[^\]]+\]\([^)]+\)\*\*)(\s*\n\s*\*Fuente:[^\*]+\*)?(\s*\n\s*\*Fecha:\s*([^\*]+)\*)',
        lambda m: f"{m.group(1)} — {m.group(4).strip()}{m.group(2) or ''}",
        text
    )

    # Convierte [texto](url) a enlace HTML
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Convierte **texto** a negrita
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Convierte *texto* a cursiva
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Saltos de línea
    text = text.replace('\n', '<br>')

    return text


def send_email(question: str, answer: str) -> None:
    """Envía el informe de noticias al correo configurado en .env."""
    sender = os.getenv("GMAIL_ADDRESS")
    recipient = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Informe de noticias - {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = sender
    msg["To"] = recipient

    html = f"""
    <h2>Resumen de noticias</h2>
    <p><b>Tu pregunta:</b><br>{question}</p>
    <hr>
    <p>{_md_to_html(answer)}</p>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
