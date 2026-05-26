"""
SMTP email service.

In development (SMTP_HOST unset) messages are printed to stdout.
In production set the SMTP_* environment variables on your hosting platform.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings

settings = get_settings()


async def send_email(to: str, subject: str, html_body: str) -> None:
    """
    Send an HTML email via SMTP.
    Raises on failure so the caller can log the error.

    Configuration (env vars):
        SMTP_HOST       — mail server hostname (e.g. smtp.gmail.com)
        SMTP_PORT       — port (default 587)
        SMTP_USER       — login username / address
        SMTP_PASSWORD   — login password or app-password
        SMTP_USE_TLS    — true|false (default true)
        EMAIL_FROM      — From: address shown to recipients
        EMAIL_FROM_NAME — Friendly sender name
    """
    if not settings.smtp_host:
        # Dev / no-SMTP fallback — log to stdout
        print(
            f"\n[EMAIL] To: {to}\n"
            f"Subject: {subject}\n"
            f"{html_body}\n"
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()

    if settings.smtp_use_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, [to], msg.as_bytes())
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, [to], msg.as_bytes())
