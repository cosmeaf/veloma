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
def delete_document_from_dropbox(self, document_id):
    """Removes every version of a recycled document from the Dropbox mirror."""
    from config.common.dropbox_service import DropboxService
    from .models import Document

    if not DropboxService.is_enabled(DropboxService.PURPOSE_UPLOADS):
        return {'skipped': 'dropbox_disabled'}
    document = Document.objects.select_related('client', 'protocol', 'folder').filter(pk=document_id).first()
    if not document:
        return {'skipped': 'document_not_found'}
    deleted = 0
    try:
        for version in document.versions.all():
            if DropboxService.delete_path(
                purpose=DropboxService.PURPOSE_UPLOADS,
                relative_path=_upload_relative_path(version),
            ):
                deleted += 1
    except Exception as exc:  # noqa: BLE001
        logger.exception('Dropbox delete failed. document_id=%s', document_id)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    return {'document_id': str(document_id), 'deleted': deleted}


@shared_task
def purge_recycled_documents():
    """Permanently removes stored objects of documents past their recycle window."""
    from config.common.storage import StorageService
    from .models import Document

    now = timezone.now()
    documents = Document.objects.filter(
        status=Document.STATUS_DELETED,
        purged_at__isnull=True,
        purge_after__lt=now,
    )
    purged = 0
    for document in documents:
        for version in document.versions.exclude(storage_key=''):
            StorageService.delete(version.storage_key)
        document.purged_at = now
        document.save(update_fields=('purged_at', 'updated_at'))
        purged += 1
    return {'purged': purged}


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
    """Builds the Dropbox mirror path, organised by protocol.

    Each request opens a protocol, so documents live under
    ``<número> - <título>/ficheiro``. Documents without a protocol (legacy or
    folder-based) fall back to ``Sem protocolo/<Cliente>/<Pasta>/ficheiro`` so
    they stay identifiable. Versions after the first get a ``(vN)`` suffix
    before the extension; the first keeps the clean name.
    """
    document = version.document

    name = _clean_segment(version.original_name or str(version.id), 'ficheiro')
    if version.version_number and version.version_number > 1:
        if '.' in name:
            stem, ext = name.split('.', 1)
            name = f'{stem} (v{version.version_number}).{ext}'
        else:
            name = f'{name} (v{version.version_number})'

    protocol = document.protocol
    if protocol:
        head = _clean_segment(f'{protocol.number} - {protocol.title}'.strip(' -'), protocol.number)
        return f'{head}/{name}'

    # No protocol: keep it identifiable by client and its folder/category.
    client_part = _clean_segment(getattr(document.client, 'legal_name', '') or str(document.client_id), 'Cliente')
    if document.folder_id:
        sub = document.folder.name
    else:
        sub = document.category or 'Outros'
    return f'Sem protocolo/{client_part}/{_clean_segment(sub, "Outros")}/{name}'


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
