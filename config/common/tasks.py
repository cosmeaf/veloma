from celery import shared_task

from .email_service import EmailMessageData, EmailService
from .models import EmailSettings


@shared_task(bind=True)
def send_email_task(self, message_data, log_id):
    message = EmailMessageData(**message_data)
    settings = EmailSettings.load()
    try:
        return EmailService.send_sync(message, log_id=log_id)
    except Exception as exc:
        if self.request.retries >= settings.max_retries:
            raise
        countdown = settings.retry_backoff_seconds * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown, max_retries=settings.max_retries)
