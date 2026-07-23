import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from config.common.models import DocumentSettings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scan_document_version(self, version_id):
    """Runs the antivirus scan outside the request cycle."""
    from .models import DocumentVersion
    from .services import DocumentService

    version = DocumentVersion.objects.select_related('document').filter(pk=version_id).first()
    if not version:
        return {'skipped': 'version_not_found'}
    try:
        DocumentService.run_scan(version)
    except Exception as exc:
        logger.exception('Antivirus scan failed. version_id=%s', version_id)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    return {'version_id': str(version.id), 'scan_status': version.scan_status}


@shared_task
def expire_invitations():
    """Marks pending invitations past their expiration date."""
    from .models import ClientInvitation

    expired = ClientInvitation.objects.filter(
        status=ClientInvitation.STATUS_PENDING,
        expires_at__lte=timezone.now(),
    ).update(status=ClientInvitation.STATUS_EXPIRED)
    return {'expired': expired}


@shared_task
def send_invitation_reminders():
    """Reminds invitees whose invitation is close to expiring."""
    from .models import ClientInvitation
    from .services import NotificationService

    settings = DocumentSettings.load()
    now = timezone.now()
    window_start = now
    window_end = now + timedelta(days=settings.invitation_reminder_days)
    pending = ClientInvitation.objects.select_related('client').filter(
        status=ClientInvitation.STATUS_PENDING,
        expires_at__gt=window_start,
        expires_at__lte=window_end,
    )
    sent = 0
    for invitation in pending:
        NotificationService.send(
            purpose='client_invitation_reminder',
            recipients=[invitation.email],
            context={
                'client': {'legal_name': invitation.client.legal_name},
                'invitation': {'email': invitation.email, 'expires_at': invitation.expires_at},
                'event_time': now,
            },
        )
        sent += 1
    return {'reminders': sent}


@shared_task
def alert_overdue_protocols():
    """Warns the assigned staff about protocols past their due date."""
    from .models import Protocol
    from .services import NotificationService

    settings = DocumentSettings.load()
    if not settings.overdue_alert_enabled:
        return {'skipped': 'disabled'}
    today = timezone.now().date()
    overdue = Protocol.objects.select_related('client', 'assigned_to').filter(
        due_date__lt=today,
        assigned_to__isnull=False,
    ).exclude(
        status__in=(Protocol.STATUS_COMPLETED, Protocol.STATUS_CANCELLED, Protocol.STATUS_ARCHIVED),
    )
    sent = 0
    for protocol in overdue:
        NotificationService.send(
            purpose='protocol_status_changed',
            recipients=[protocol.assigned_to.email],
            context={
                'client': {'legal_name': protocol.client.legal_name},
                'protocol': {
                    'number': protocol.number,
                    'title': protocol.title,
                    'status': protocol.status,
                    'due_date': protocol.due_date,
                },
                'message': 'Protocolo com prazo ultrapassado.',
                'event_time': timezone.now(),
            },
        )
        sent += 1
    return {'alerts': sent}


@shared_task
def cleanup_quarantined_documents():
    """Removes stored objects of infected versions past the retention window."""
    from .models import Document, DocumentVersion
    from config.common.storage import StorageService

    settings = DocumentSettings.load()
    cutoff = timezone.now() - timedelta(days=settings.quarantine_retention_days)
    versions = DocumentVersion.objects.filter(
        scan_status=DocumentVersion.SCAN_INFECTED,
        created_at__lt=cutoff,
    ).exclude(storage_key='')
    removed = 0
    for version in versions:
        if StorageService.delete(version.storage_key):
            removed += 1
    Document.objects.filter(
        status=Document.STATUS_INFECTED,
        created_at__lt=cutoff,
    ).update(status=Document.STATUS_QUARANTINED)
    return {'objects_removed': removed}


@shared_task
def retry_failed_scans():
    """Reprocesses scans that ended in error, with a bounded scope."""
    from .models import DocumentVersion

    stale = DocumentVersion.objects.filter(
        scan_status=DocumentVersion.SCAN_ERROR,
        created_at__gte=timezone.now() - timedelta(days=2),
    ).order_by('created_at')[:50]
    queued = 0
    for version in stale:
        scan_document_version.delay(str(version.id))
        queued += 1
    return {'queued': queued}
