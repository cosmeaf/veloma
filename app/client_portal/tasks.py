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


@shared_task(bind=True, max_retries=5)
def mirror_document_version_to_dropbox(self, version_id):
    """Copies an approved document version to the company Dropbox uploads area."""
    from config.common.dropbox_service import DropboxService
    from config.common.storage import StorageService
    from .models import Document, DocumentVersion

    if not DropboxService.is_enabled(DropboxService.PURPOSE_UPLOADS):
        return {'skipped': 'dropbox_disabled'}
    version = DocumentVersion.objects.select_related(
        'document', 'document__client', 'document__protocol', 'document__folder'
    ).filter(pk=version_id).first()
    if not version:
        return {'skipped': 'version_not_found'}
    # Only mirror files that passed the scan and are available.
    if version.document.status != Document.STATUS_AVAILABLE:
        return {'skipped': 'not_available'}
    try:
        with StorageService.open(version.storage_key) as handle:
            content = handle.read()
        relative = _upload_relative_path(version)
        path = DropboxService.upload_bytes(
            purpose=DropboxService.PURPOSE_UPLOADS,
            relative_path=relative,
            content=content,
        )
        if not path:
            raise RuntimeError('dropbox_upload_returned_none')
    except Exception as exc:  # noqa: BLE001
        logger.exception('Dropbox mirror failed. version_id=%s', version_id)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    return {'version_id': str(version.id), 'dropbox_path': path}


@shared_task(bind=True, max_retries=5)
def mirror_terms_acceptance_to_dropbox(self, acceptance_id):
    """Copies a consent proof PDF to the RGPD Dropbox archive (10-year retention)."""
    from config.common.dropbox_service import DropboxService
    from .models import TermsAcceptance
    from .services import TermsAcceptanceService

    if not DropboxService.is_enabled(DropboxService.PURPOSE_RGPD):
        return {'skipped': 'dropbox_disabled'}
    acceptance = TermsAcceptance.objects.filter(pk=acceptance_id).first()
    if not acceptance:
        return {'skipped': 'acceptance_not_found'}
    if acceptance.archived_path:
        return {'skipped': 'already_archived'}
    try:
        path = TermsAcceptanceService.mirror_to_archive(acceptance)
        if not path:
            raise RuntimeError('dropbox_upload_returned_none')
    except Exception as exc:  # noqa: BLE001
        logger.exception('RGPD Dropbox mirror failed. acceptance_id=%s', acceptance_id)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    return {'acceptance_id': str(acceptance.id), 'dropbox_path': path}


def _clean_segment(value, fallback='item'):
    """Readable, Dropbox-safe path segment: keeps letters (incl. accents),
    digits, spaces and common punctuation; drops path separators and control
    characters. Not slugified — the archive is meant to be browsed by humans.
    """
    import re
    import unicodedata

    text = str(value or '').replace('\\', '-').replace('/', '-')
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
    text = re.sub(r'\s+', ' ', text).strip().strip('.').strip()
    return text[:150] or fallback


def _upload_relative_path(version):
    """Builds ``Cliente/Protocolo-ou-Pasta/ficheiro`` for the Dropbox mirror.

    With a protocol → ``número - título``; otherwise the folder name; failing
    both, the document category or ``Outros``. Versions after the first get a
    ``(vN)`` suffix before the extension; the first keeps the clean name.
    """
    document = version.document
    client_part = _clean_segment(getattr(document.client, 'legal_name', '') or str(document.client_id), 'Cliente')

    protocol = document.protocol
    if protocol:
        middle = f'{protocol.number} - {protocol.title}'.strip(' -')
    elif document.folder_id:
        middle = document.folder.name
    else:
        middle = document.category or 'Outros'
    middle_part = _clean_segment(middle, 'Outros')

    name = _clean_segment(version.original_name or str(version.id), 'ficheiro')
    if version.version_number and version.version_number > 1:
        if '.' in name:
            stem, ext = name.split('.', 1)
            name = f'{stem} (v{version.version_number}).{ext}'
        else:
            name = f'{name} (v{version.version_number})'

    return f'{client_part}/{middle_part}/{name}'


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
