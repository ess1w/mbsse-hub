"""
Email service.

Delivery backend is chosen automatically:
  1. POSTMARK_SERVER_TOKEN set → send via Postmark's HTTPS API (works on Render
     free tier, where outbound SMTP ports are blocked).
  2. else SMTP_HOST set        → send via SMTP (paid instance / VPS).
  3. else                       → log to stdout (local dev / unconfigured).

Raises on failure so the caller can log the error.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import get_settings

settings = get_settings()

POSTMARK_ENDPOINT = "https://api.postmarkapp.com/email"


async def _send_via_postmark(to: str, subject: str, html_body: str) -> None:
    payload = {
        "From": f"{settings.email_from_name} <{settings.email_from}>",
        "To": to,
        "Subject": subject,
        "HtmlBody": html_body,
        "MessageStream": "outbound",
    }
    headers = {
        "X-Postmark-Server-Token": settings.postmark_server_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(POSTMARK_ENDPOINT, json=payload, headers=headers)
    if resp.status_code >= 300:
        raise RuntimeError(f"Postmark API error {resp.status_code}: {resp.text}")


async def send_email(to: str, subject: str, html_body: str) -> None:
    """Send an HTML email via the configured backend (Postmark API / SMTP / stdout).

    Configuration (env vars):
        POSTMARK_SERVER_TOKEN — send via Postmark HTTPS API (preferred on Render free tier)
        SMTP_HOST       — mail server hostname (SMTP fallback)
        SMTP_PORT       — port (default 587)
        SMTP_USER       — login username / address
        SMTP_PASSWORD   — login password or app-password
        SMTP_USE_TLS    — true|false (default true)
        EMAIL_FROM      — From: address (must be a verified sender signature in Postmark)
        EMAIL_FROM_NAME — Friendly sender name
    """
    if settings.postmark_server_token:
        await _send_via_postmark(to, subject, html_body)
        return

    if not settings.smtp_host:
        # Dev / unconfigured fallback — log to stdout
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
