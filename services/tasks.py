# services/tasks.py
from celery import shared_task
from .utils.emails.sendemail import EmailService

@shared_task
def send_email_task(payload: dict):
    svc = EmailService()
    if payload.get("template_code"):
        return svc.send_by_template(
            template_code=payload["template_code"],
            to=payload["to"],
            context=payload.get("context") or {},
            subject=payload.get("subject"),
        )
    else:
        return svc.send_raw(
            subject=payload.get("subject") or "(no subject)",
            to=payload["to"],
            body_text=payload.get("body_text") or "",
            body_html=payload.get("body_html"),
        )
