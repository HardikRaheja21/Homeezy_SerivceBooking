from app.worker import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="notifications.send_email")
def send_email_task(email_to: str, subject: str, template_name: str, template_data: dict):
    # TODO: Implement actual email sending via SMTP/SendGrid
    logger.info(f"Sending email to {email_to} with subject '{subject}'")
    return {"status": "success", "email_to": email_to}
