"""
Email service.

Delivery backend is chosen automatically:
  1. BREVO_API_KEY set  → send via Brevo's HTTPS API (works on Render free tier,
     where outbound SMTP ports are blocked).
  2. else SMTP_HOST set → send via SMTP (paid instance / VPS).
  3. else                → log to stdout (local dev / unconfigured).

Raises on failure so the caller can log the error.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import get_settings

settings = get_settings()

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


async def _send_via_brevo(to: str, subject: str, html_body: str) -> None:
    payload = {
        "sender": {"name": settings.email_from_name, "email": settings.email_from},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html_body,
    }
    headers = {
        "api-key": settings.brevo_api_key,
        "content-type": "application/json",
        "accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(BREVO_ENDPOINT, json=payload, headers=headers)
    if resp.status_code >= 300:
        raise RuntimeError(f"Brevo API error {resp.status_code}: {resp.text}")


async def send_email(to: str, subject: str, html_body: str) -> None:
    """Send an HTML email via the configured backend (Brevo API / SMTP / stdout).

    Configuration (env vars):
        BREVO_API_KEY   — send via Brevo HTTPS API (preferred on Render free tier)
        SMTP_HOST       — mail server hostname (SMTP fallback)
        SMTP_PORT       — port (default 587)
        SMTP_USER       — login username / address
        SMTP_PASSWORD   — login password or app-password
        SMTP_USE_TLS    — true|false (default true)
        EMAIL_FROM      — From: address (must be a verified sender in Brevo)
        EMAIL_FROM_NAME — Friendly sender name
    """
    if settings.brevo_api_key:
        await _send_via_brevo(to, subject, html_body)
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
