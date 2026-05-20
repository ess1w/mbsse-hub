"""
Thin wrapper around SendGrid.
Swap out the implementation here if you move to another provider (Mailgun, SES, etc.)
"""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import get_settings

settings = get_settings()


async def send_email(to: str, subject: str, html_body: str) -> None:
    """
    Sends an HTML email via SendGrid.
    Raises on failure so the Celery task can catch and mark the reminder failed.
    """
    if settings.environment == "development":
        # In dev, just print instead of sending
        print(f"\n[DEV EMAIL] To: {to}\nSubject: {subject}\n{html_body}\n")
        return

    message = Mail(
        from_email=(settings.email_from, settings.email_from_name),
        to_emails=to,
        subject=subject,
        html_content=html_body,
    )
    sg = SendGridAPIClient(settings.sendgrid_api_key)
    response = sg.send(message)
    if response.status_code not in (200, 202):
        raise RuntimeError(
            f"SendGrid returned {response.status_code}: {response.body}"
        )
