import logging
from dataclasses import asdict, dataclass
from typing import Iterable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils import timezone

from .crypto import CredentialCipher
from .models import EmailDeliveryLog, EmailSettings, EmailTemplate, EmailVendor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessageData:
    recipients: list[str]
    subject: str
    html_template: str
    text_template: str
    context: dict
    purpose: str = ''
    mode: str = EmailTemplate.MODE_AUTO
    vendor_id: int | None = None

    def payload(self):
        return asdict(self)


class BaseEmailVendor:
    def send(self, *, recipients, subject, html_content, text_content):
        raise NotImplementedError


class SMTPEmailVendor(BaseEmailVendor):
    def __init__(self, vendor: EmailVendor):
        self.vendor = vendor

    def send(self, *, recipients, subject, html_content, text_content):
        password = CredentialCipher.decrypt(self.vendor.encrypted_password)
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=self.vendor.host,
            port=self.vendor.port,
            username=self.vendor.username,
            password=password,
            use_tls=self.vendor.use_tls,
            use_ssl=self.vendor.use_ssl,
            timeout=self.vendor.timeout_seconds,
            fail_silently=False,
        )
        from_email = self.vendor.from_email or settings.DEFAULT_FROM_EMAIL
        if self.vendor.from_name and self.vendor.from_email:
            from_email = f'{self.vendor.from_name} <{self.vendor.from_email}>'
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipients,
            reply_to=[self.vendor.reply_to] if self.vendor.reply_to else None,
            connection=connection,
        )
        if html_content:
            message.attach_alternative(html_content, 'text/html')
        return message.send()


class ConsoleEmailVendor(BaseEmailVendor):
    def __init__(self, vendor: EmailVendor):
        self.vendor = vendor

    def send(self, *, recipients, subject, html_content, text_content):
        connection = get_connection('django.core.mail.backends.console.EmailBackend')
        from_email = self.vendor.from_email or settings.DEFAULT_FROM_EMAIL
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipients,
            connection=connection,
        )
        if html_content:
            message.attach_alternative(html_content, 'text/html')
        return message.send()


class EmailVendorFactory:
    @staticmethod
    def build(vendor: EmailVendor) -> BaseEmailVendor:
        if vendor.vendor_type == EmailVendor.TYPE_SMTP:
            return SMTPEmailVendor(vendor)
        if vendor.vendor_type == EmailVendor.TYPE_CONSOLE:
            return ConsoleEmailVendor(vendor)
        raise ValueError(f'Unsupported email vendor: {vendor.vendor_type}')


class EmailService:
    @staticmethod
    def _resolve_vendor(vendor_id=None):
        queryset = EmailVendor.objects.filter(active=True)
        if vendor_id:
            return queryset.filter(pk=vendor_id).first()
        return queryset.filter(is_default=True).first() or queryset.order_by('priority', 'name').first()

    @staticmethod
    def _render_subject(subject, context):
        return ' '.join(Template(subject).render(Context(context)).splitlines()).strip()

    @staticmethod
    def _render(html_template, text_template, context):
        html_content = render_to_string(html_template, context) if html_template else ''
        text_content = render_to_string(text_template, context) if text_template else ''
        return html_content, text_content

    @classmethod
    def send_by_purpose(cls, *, purpose, recipients, context=None, mode=None):
        template = EmailTemplate.objects.select_related('vendor').filter(purpose=purpose, active=True).first()
        if not template:
            raise RuntimeError(f'No active email template is configured for purpose: {purpose}')
        return cls.send(
            recipients=recipients,
            subject=template.subject,
            html_template=template.html_template,
            text_template=template.text_template,
            context=context or {},
            purpose=purpose,
            mode=mode or template.delivery_mode,
            vendor_id=template.vendor_id,
        )

    @classmethod
    def send(
        cls,
        *,
        recipients: Iterable[str],
        subject,
        html_template,
        text_template,
        context=None,
        purpose='',
        mode='auto',
        vendor_id=None,
    ):
        recipients = list(dict.fromkeys(str(item).strip().lower() for item in recipients if str(item).strip()))
        if not recipients:
            raise ValueError('At least one recipient is required.')
        if not mode:
            mode = EmailSettings.load().default_delivery_mode
        if mode not in {EmailTemplate.MODE_SYNC, EmailTemplate.MODE_ASYNC, EmailTemplate.MODE_AUTO}:
            raise ValueError(f'Invalid email delivery mode: {mode}')
        message = EmailMessageData(
            recipients=recipients,
            subject=subject,
            html_template=html_template,
            text_template=text_template,
            context=context or {},
            purpose=purpose,
            mode=mode,
            vendor_id=vendor_id,
        )
        if mode == EmailTemplate.MODE_SYNC:
            return cls.send_sync(message)
        if mode == EmailTemplate.MODE_ASYNC:
            return cls.send_async(message)
        try:
            return cls.send_async(message)
        except Exception:
            if not EmailSettings.load().auto_sync_fallback:
                raise
            logger.exception('Unable to queue email; controlled sync fallback is being used.')
            return cls.send_sync(message)

    @classmethod
    def send_async(cls, message: EmailMessageData):
        from .tasks import send_email_task

        log = EmailDeliveryLog.objects.create(
            purpose=message.purpose,
            recipients=message.recipients,
            subject=cls._render_subject(message.subject, message.context),
            vendor_id=message.vendor_id,
            delivery_mode=EmailTemplate.MODE_ASYNC,
            status=EmailDeliveryLog.STATUS_QUEUED,
        )
        task = send_email_task.delay(message.payload(), log.pk)
        log.task_id = task.id or ''
        log.save(update_fields=('task_id',))
        return {'queued': True, 'task_id': task.id, 'log_id': log.pk}

    @classmethod
    def send_sync(cls, message: EmailMessageData, log_id=None):
        preferred = cls._resolve_vendor(message.vendor_id)
        fallbacks = list(
            EmailVendor.objects.filter(active=True, is_fallback=True)
            .exclude(pk=getattr(preferred, 'pk', None))
            .order_by('priority', 'name')
        )
        vendors = ([preferred] if preferred else []) + fallbacks
        rendered_subject = cls._render_subject(message.subject, message.context)
        log = EmailDeliveryLog.objects.filter(pk=log_id).first() if log_id else None
        if not log:
            log = EmailDeliveryLog.objects.create(
                purpose=message.purpose,
                recipients=message.recipients,
                subject=rendered_subject,
                vendor=preferred,
                delivery_mode=message.mode,
                status=EmailDeliveryLog.STATUS_QUEUED,
            )
        if not vendors:
            log.status = EmailDeliveryLog.STATUS_FAILED
            log.error = 'No active email vendor is configured.'
            log.attempts += 1
            log.save(update_fields=('status', 'error', 'attempts'))
            raise RuntimeError(log.error)

        html_content, text_content = cls._render(message.html_template, message.text_template, message.context)
        errors = []
        for vendor in vendors:
            try:
                sent = EmailVendorFactory.build(vendor).send(
                    recipients=message.recipients,
                    subject=rendered_subject,
                    html_content=html_content,
                    text_content=text_content,
                )
                log.vendor = vendor
                log.status = EmailDeliveryLog.STATUS_SENT
                log.sent_at = timezone.now()
                log.attempts += 1
                log.error = ''
                log.save(update_fields=('vendor', 'status', 'sent_at', 'attempts', 'error'))
                return {'sent': bool(sent), 'log_id': log.pk, 'vendor': vendor.name}
            except Exception as exc:
                errors.append(f'{vendor.name}: {exc}')
                log.attempts += 1
                logger.exception('Email vendor failed. vendor=%s log_id=%s', vendor.name, log.pk)

        log.vendor = vendors[-1]
        log.status = EmailDeliveryLog.STATUS_FAILED
        log.error = ' | '.join(errors)
        log.save(update_fields=('vendor', 'status', 'attempts', 'error'))
        raise RuntimeError(log.error)
