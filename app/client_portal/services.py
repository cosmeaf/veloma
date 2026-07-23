import hashlib
import logging
import mimetypes
import re
import secrets
import unicodedata
from datetime import timedelta

from django.conf import settings as django_settings
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from config.authentication.models import AuthenticationActivity, hash_token
from config.authentication.services import AccountLifecycleService, SessionService
from config.common.antivirus import AntivirusService, ScanResult
from config.common.models import DocumentSettings
from config.common.storage import StorageService
from config.security.request import RequestContext
from config.security.services import SecurityService

from .models import (
    Client,
    ClientFolder,
    ClientInvitation,
    ClientMember,
    ClientPortalActivity,
    Document,
    DocumentVersion,
    DownloadAudit,
    LifecycleStatus,
    Protocol,
    ProtocolCounter,
    ProtocolComment,
    ProtocolEvent,
    ProtocolRequirement,
    TermsAcceptance,
)

logger = logging.getLogger('app.client_portal.services')

SAFE_NAME = re.compile(r'[^A-Za-z0-9._-]+')


def user_label(user):
    if user is None:
        return ''
    full_name = f'{user.first_name} {user.last_name}'.strip()
    return full_name or user.get_username()


def safe_filename(name):
    """Normalizes an uploaded file name; never trust the client value."""
    base = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode('ascii')
    base = base.replace('\\', '/').split('/')[-1].strip()
    base = SAFE_NAME.sub('_', base).strip('._-')
    return base[:200] or 'file'


class TermsAcceptanceService:
    """Records the legal proof of consent and generates its PDF.

    Called at first access (invitation acceptance). Captures the digital
    evidence, stores a sealed PDF in object storage and queues its mirror to the
    company's 10-year RGPD archive on Dropbox. A mirror or PDF failure must never
    break account activation, so both are best-effort here.
    """

    @staticmethod
    def record(*, user, client=None, context=TermsAcceptance.CONTEXT_INVITATION, request=None,
               first_name='', last_name=''):
        from .legal import PRIVACY_VERSION, TERMS_VERSION, build_acceptance_pdf

        acceptance = TermsAcceptance.objects.create(
            user=user,
            email_snapshot=(getattr(user, 'email', '') or '').strip().lower(),
            client=client,
            client_name_snapshot=getattr(client, 'legal_name', '') or '',
            context=context,
            terms_version=TERMS_VERSION,
            privacy_version=PRIVACY_VERSION,
            ip_address=RequestContext.ip(request),
            country_code=SecurityService.country_code(request),
            region=TermsAcceptanceService._region(request),
            device=RequestContext.device(request),
            user_agent=RequestContext.user_agent(request),
        )

        try:
            pdf_bytes = build_acceptance_pdf(acceptance=acceptance, first_name=first_name, last_name=last_name)
            key = f'rgpd/acceptances/{acceptance.id}.pdf'
            from django.core.files.base import ContentFile

            StorageService.upload(key=key, content=ContentFile(pdf_bytes))
            acceptance.pdf_storage_key = key
            acceptance.save(update_fields=('pdf_storage_key',))
        except Exception:  # noqa: BLE001 — proof PDF must not block activation.
            logger.exception('Unable to build the acceptance PDF. acceptance_id=%s', acceptance.id)
            return acceptance

        try:
            from .tasks import mirror_terms_acceptance_to_dropbox

            mirror_terms_acceptance_to_dropbox.delay(str(acceptance.id))
        except Exception:  # noqa: BLE001 — queue best-effort; a sync fallback runs below.
            logger.exception('Unable to queue the RGPD Dropbox mirror. acceptance_id=%s', acceptance.id)
            TermsAcceptanceService.mirror_to_archive(acceptance)
        return acceptance

    @staticmethod
    def _region(request):
        data = getattr(request, 'ip_intel', {}) or {}
        for key in ('region_name', 'regionName', 'region', 'city'):
            value = data.get(key)
            if value:
                return str(value)[:128]
        return ''

    @staticmethod
    def mirror_to_archive(acceptance):
        """Uploads the proof PDF to the RGPD Dropbox archive. Idempotent."""
        from config.common.dropbox_service import DropboxService

        if not acceptance.pdf_storage_key:
            return None
        with StorageService.open(acceptance.pdf_storage_key) as handle:
            content = handle.read()
        stamp = acceptance.accepted_at.strftime('%Y/%m') if acceptance.accepted_at else 'undated'
        relative = f'{stamp}/{acceptance.id}.pdf'
        path = DropboxService.upload_bytes(
            purpose=DropboxService.PURPOSE_RGPD,
            relative_path=relative,
            content=content,
        )
        if path:
            acceptance.archived_path = path
            acceptance.archived_at = timezone.now()
            acceptance.save(update_fields=('archived_path', 'archived_at'))
        return path


class PortalAudit:
    """Module-level audit trail. Never records secrets or file contents."""

    @staticmethod
    def record(*, event_type, actor=None, client=None, target='', summary='', metadata=None, request=None):
        return ClientPortalActivity.objects.create(
            event_type=event_type,
            actor=actor,
            actor_name_snapshot=user_label(actor),
            client=client,
            target=str(target)[:255],
            summary=summary[:255],
            metadata=metadata or {},
            ip_address=RequestContext.ip(request) if request else None,
            user_agent=RequestContext.user_agent(request) if request else '',
        )


class ProtocolEventService:
    @staticmethod
    def record(*, protocol, event_type, actor=None, old_value='', new_value='', metadata=None, request=None):
        return ProtocolEvent.objects.create(
            protocol=protocol,
            event_type=event_type,
            actor=actor,
            actor_name_snapshot=user_label(actor),
            actor_email_snapshot=getattr(actor, 'email', '') or '',
            old_value=str(old_value)[:255],
            new_value=str(new_value)[:255],
            metadata=metadata or {},
            ip_address=RequestContext.ip(request) if request else None,
            user_agent=RequestContext.user_agent(request) if request else '',
        )


class NotificationService:
    """Thin wrapper over the existing EmailService; purposes are Admin-driven."""

    @staticmethod
    def send(*, purpose, recipients, context=None):
        from config.common.email_service import EmailService

        recipients = [item for item in recipients if item]
        if not recipients:
            return None
        try:
            return EmailService.send_by_purpose(
                purpose=purpose,
                recipients=recipients,
                context=context or {},
            )
        except Exception:
            logger.exception('Client portal notification failed. purpose=%s', purpose)
            return None


class ClientService:
    @staticmethod
    @transaction.atomic
    def create(*, data, performed_by=None, request=None):
        client = Client(**data)
        client.full_clean()
        client.save()
        FolderService.ensure_base_structure(client=client, created_by=performed_by)
        PortalAudit.record(
            event_type='client_created',
            actor=performed_by,
            client=client,
            target=client.nif,
            summary=f'Client {client.legal_name} created.',
            request=request,
        )
        return client

    @staticmethod
    @transaction.atomic
    def update(*, client, data, performed_by=None, request=None):
        for field, value in data.items():
            setattr(client, field, value)
        client.full_clean()
        client.save()
        PortalAudit.record(
            event_type='client_updated',
            actor=performed_by,
            client=client,
            target=client.nif,
            summary=f'Client {client.legal_name} updated.',
            metadata={'fields': sorted(data.keys())},
            request=request,
        )
        return client


class ClientLifecycleService:
    """Deactivation, logical deletion and reversals for accounting clients."""

    @staticmethod
    def _cancel_pending_invitations(client, performed_by=None):
        return ClientInvitation.objects.filter(
            client=client,
            status=ClientInvitation.STATUS_PENDING,
        ).update(status=ClientInvitation.STATUS_CANCELLED, revoked_at=timezone.now())

    @classmethod
    @transaction.atomic
    def deactivate(cls, *, client, performed_by=None, reason='', request=None):
        """Blocks uploads and new protocols; everything stays readable to staff."""
        if client.is_archived:
            raise ValueError('Archived clients must be restored before being deactivated.')
        client.status = LifecycleStatus.DEACTIVATED
        client.deactivated_at = timezone.now()
        client.deactivated_by = performed_by
        client.deactivation_reason = reason
        client.save(update_fields=('status', 'deactivated_at', 'deactivated_by', 'deactivation_reason', 'updated_at'))

        PortalAudit.record(
            event_type='client_deactivated',
            actor=performed_by,
            client=client,
            target=client.nif,
            summary=reason or 'Client deactivated.',
            request=request,
        )
        for member in client.members.filter(status=LifecycleStatus.ACTIVE).select_related('user'):
            NotificationService.send(
                purpose='client_account_deactivated',
                recipients=[member.user.email],
                context={'user': {'first_name': member.user.first_name}, 'client': {'legal_name': client.legal_name},
                         'message': reason or 'O acesso da empresa foi suspenso temporariamente.'},
            )
        return client

    @classmethod
    @transaction.atomic
    def archive(cls, *, client, performed_by=None, reason='', request=None):
        """Logical deletion: members are deactivated, history is preserved."""
        if client.is_archived:
            return client
        now = timezone.now()
        client.status = LifecycleStatus.ARCHIVED
        client.archived_at = now
        client.archived_by = performed_by
        client.archive_reason = reason
        if not client.deactivated_at:
            client.deactivated_at = now
            client.deactivated_by = performed_by
            client.deactivation_reason = reason or 'Archived client.'
        client.save()

        cancelled = cls._cancel_pending_invitations(client, performed_by)
        members = list(client.members.filter(status=LifecycleStatus.ACTIVE).select_related('user'))
        for member in members:
            ClientMemberService.deactivate(
                member=member,
                performed_by=performed_by,
                reason=reason or 'Client archived.',
                request=request,
            )

        PortalAudit.record(
            event_type='client_archived',
            actor=performed_by,
            client=client,
            target=client.nif,
            summary=reason or 'Client archived.',
            metadata={'members_deactivated': len(members), 'invitations_cancelled': cancelled},
            request=request,
        )
        for member in members:
            NotificationService.send(
                purpose='client_account_archived',
                recipients=[member.user.email],
                context={'user': {'first_name': member.user.first_name}, 'client': {'legal_name': client.legal_name},
                         'message': reason or 'A conta da empresa foi encerrada.'},
            )
        return client

    @classmethod
    @transaction.atomic
    def restore(cls, *, client, performed_by=None, request=None):
        """Leaves the archive as deactivated; access needs an explicit reactivate."""
        if not client.is_archived:
            raise ValueError('This client is not archived.')
        client.status = LifecycleStatus.DEACTIVATED
        client.archived_at = None
        client.archived_by = None
        client.archive_reason = ''
        client.restored_at = timezone.now()
        client.save()
        PortalAudit.record(
            event_type='client_restored',
            actor=performed_by,
            client=client,
            target=client.nif,
            summary='Client restored from the archive.',
            request=request,
        )
        return client

    @classmethod
    @transaction.atomic
    def reactivate(cls, *, client, performed_by=None, request=None):
        if client.is_archived:
            raise ValueError('Restore the archived client before reactivating it.')
        client.status = LifecycleStatus.ACTIVE
        client.deactivated_at = None
        client.deactivated_by = None
        client.deactivation_reason = ''
        client.save(update_fields=('status', 'deactivated_at', 'deactivated_by', 'deactivation_reason', 'updated_at'))
        PortalAudit.record(
            event_type='client_reactivated',
            actor=performed_by,
            client=client,
            target=client.nif,
            summary='Client reactivated.',
            request=request,
        )
        for member in client.members.filter(status=LifecycleStatus.ACTIVE).select_related('user'):
            NotificationService.send(
                purpose='client_account_restored',
                recipients=[member.user.email],
                context={'user': {'first_name': member.user.first_name}, 'client': {'legal_name': client.legal_name},
                         'message': 'O acesso da empresa foi reativado.'},
            )
        return client


class ClientMemberService:
    @staticmethod
    @transaction.atomic
    def deactivate(*, member, performed_by=None, reason='', request=None):
        member.status = LifecycleStatus.DEACTIVATED
        member.deactivated_at = timezone.now()
        member.save(update_fields=('status', 'deactivated_at', 'updated_at'))
        SessionService.revoke_all(user=member.user, reason='client_member_deactivated')
        PortalAudit.record(
            event_type='member_deactivated',
            actor=performed_by,
            client=member.client,
            target=member.user.email,
            summary=reason or 'Member deactivated.',
            request=request,
        )
        return member

    @staticmethod
    @transaction.atomic
    def archive(*, member, performed_by=None, reason='', request=None):
        now = timezone.now()
        member.status = LifecycleStatus.ARCHIVED
        member.archived_at = now
        if not member.deactivated_at:
            member.deactivated_at = now
        member.save(update_fields=('status', 'archived_at', 'deactivated_at', 'updated_at'))
        SessionService.revoke_all(user=member.user, reason='client_member_archived')
        PortalAudit.record(
            event_type='member_archived',
            actor=performed_by,
            client=member.client,
            target=member.user.email,
            summary=reason or 'Member archived.',
            request=request,
        )
        return member

    @staticmethod
    @transaction.atomic
    def restore(*, member, performed_by=None, request=None):
        if member.status != LifecycleStatus.ARCHIVED:
            raise ValueError('This membership is not archived.')
        if ClientMember.objects.filter(
            client=member.client,
            user=member.user,
            status=LifecycleStatus.ACTIVE,
        ).exclude(pk=member.pk).exists():
            raise ValueError('This user already has an active membership with the client.')
        member.status = LifecycleStatus.ACTIVE
        member.archived_at = None
        member.deactivated_at = None
        member.save(update_fields=('status', 'archived_at', 'deactivated_at', 'updated_at'))
        PortalAudit.record(
            event_type='member_restored',
            actor=performed_by,
            client=member.client,
            target=member.user.email,
            summary='Member restored.',
            request=request,
        )
        return member


class InvitationService:
    """Invitations are the only path to a USER account."""

    @staticmethod
    def _settings():
        return DocumentSettings.load()

    @classmethod
    @transaction.atomic
    def create(cls, *, client, email, role, invited_by=None, request=None):
        email = email.strip().lower()
        if client.is_archived:
            raise ValueError('Archived clients cannot invite members.')
        if ClientMember.objects.filter(
            client=client,
            user__username__iexact=email,
            status=LifecycleStatus.ACTIVE,
        ).exists():
            raise ValueError('This email already has an active membership with the client.')
        if User.objects.filter(username__iexact=email, is_staff=True).exists():
            raise ValueError('Este endereço não pode ser convidado.')

        ClientInvitation.objects.filter(
            client=client,
            email__iexact=email,
            status=ClientInvitation.STATUS_PENDING,
        ).update(status=ClientInvitation.STATUS_CANCELLED, revoked_at=timezone.now())

        raw_token = secrets.token_urlsafe(48)
        invitation = ClientInvitation.objects.create(
            client=client,
            email=email,
            role=role,
            token_hash=hash_token(raw_token),
            invited_by=invited_by,
            expires_at=timezone.now() + timedelta(days=cls._settings().invitation_expiration_days),
            last_sent_at=timezone.now(),
        )
        cls._send(invitation, raw_token, purpose='client_invitation')
        PortalAudit.record(
            event_type='invitation_created',
            actor=invited_by,
            client=client,
            target=email,
            summary=f'Invitation sent to {email}.',
            metadata={'invitation_id': str(invitation.id), 'role': role},
            request=request,
        )
        return invitation, raw_token

    @staticmethod
    def _send(invitation, raw_token, *, purpose):
        NotificationService.send(
            purpose=purpose,
            recipients=[invitation.email],
            context={
                'client': {'legal_name': invitation.client.legal_name},
                'invitation': {
                    'email': invitation.email,
                    'role': invitation.role,
                    'expires_at': invitation.expires_at,
                },
                'action_url': f'{django_settings.FRONTEND_URL}/convite/aceitar?token={raw_token}',
                'event_time': timezone.now(),
            },
        )

    @classmethod
    @transaction.atomic
    def resend(cls, *, invitation, performed_by=None, request=None):
        if invitation.status != ClientInvitation.STATUS_PENDING:
            raise ValueError('Only pending invitations can be resent.')
        settings = cls._settings()
        if invitation.resend_count >= settings.invitation_max_resends:
            raise ValueError('Invitation resend limit reached.')

        raw_token = secrets.token_urlsafe(48)
        invitation.token_hash = hash_token(raw_token)
        invitation.expires_at = timezone.now() + timedelta(days=settings.invitation_expiration_days)
        invitation.resend_count += 1
        invitation.last_sent_at = timezone.now()
        invitation.save(update_fields=('token_hash', 'expires_at', 'resend_count', 'last_sent_at', 'updated_at'))
        cls._send(invitation, raw_token, purpose='client_invitation')
        PortalAudit.record(
            event_type='invitation_resent',
            actor=performed_by,
            client=invitation.client,
            target=invitation.email,
            summary=f'Invitation resent to {invitation.email}.',
            metadata={'invitation_id': str(invitation.id), 'resend_count': invitation.resend_count},
            request=request,
        )
        return invitation, raw_token

    @staticmethod
    @transaction.atomic
    def revoke(*, invitation, performed_by=None, request=None):
        if invitation.status != ClientInvitation.STATUS_PENDING:
            raise ValueError('Only pending invitations can be revoked.')
        invitation.status = ClientInvitation.STATUS_REVOKED
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=('status', 'revoked_at', 'updated_at'))
        PortalAudit.record(
            event_type='invitation_revoked',
            actor=performed_by,
            client=invitation.client,
            target=invitation.email,
            summary=f'Invitation to {invitation.email} revoked.',
            metadata={'invitation_id': str(invitation.id)},
            request=request,
        )
        return invitation

    @staticmethod
    def validate_token(token):
        """Returns the usable invitation for an opaque token, or raises."""
        invitation = (
            ClientInvitation.objects.select_related('client')
            .filter(token_hash=hash_token(token or ''))
            .first()
        )
        if not invitation:
            raise ValueError('Invalid invitation.')
        if invitation.status == ClientInvitation.STATUS_ACCEPTED:
            raise ValueError('This invitation has already been used.')
        if invitation.status != ClientInvitation.STATUS_PENDING:
            raise ValueError('This invitation is no longer valid.')
        if invitation.expires_at <= timezone.now():
            ClientInvitation.objects.filter(pk=invitation.pk).update(status=ClientInvitation.STATUS_EXPIRED)
            raise ValueError('This invitation has expired.')
        if invitation.client.is_archived:
            raise ValueError('This invitation is no longer valid.')
        return invitation

    @classmethod
    @transaction.atomic
    def accept(cls, *, token, first_name, last_name, password, phone='', position='', request=None):
        invitation = cls.validate_token(token)
        invitation = (
            ClientInvitation.objects.select_for_update()
            .select_related('client')
            .get(pk=invitation.pk)
        )
        if invitation.status != ClientInvitation.STATUS_PENDING:
            raise ValueError('This invitation is no longer valid.')

        email = invitation.email.strip().lower()
        user = User.objects.filter(username__iexact=email).first()
        if user and (user.is_staff or user.is_superuser):
            raise ValueError('Este endereço não está disponível.')

        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise ValueError(' '.join(exc.messages)) from exc

        created = False
        if user is None:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                password=password,
                is_active=True,
            )
            created = True
        elif not user.is_active:
            raise ValueError('This account is not available. Contact the administration.')

        user.groups.add(Group.objects.get_or_create(name='USER')[0])

        member = ClientMember.objects.filter(client=invitation.client, user=user).order_by('-created_at').first()
        if member and member.status == LifecycleStatus.ACTIVE:
            raise ValueError('This user already has an active membership with the client.')
        member = ClientMember.objects.create(
            client=invitation.client,
            user=user,
            role=invitation.role,
            position=position,
            phone=phone,
            status=LifecycleStatus.ACTIVE,
        )

        invitation.status = ClientInvitation.STATUS_ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.accepted_by = user
        invitation.accepted_ip = RequestContext.ip(request)
        invitation.accepted_user_agent = RequestContext.user_agent(request)
        invitation.save()

        SecurityService.record_activity(
            event_type='invitation_accepted',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=user,
            metadata={'client_id': str(invitation.client_id), 'user_created': created},
        )
        PortalAudit.record(
            event_type='invitation_accepted',
            actor=user,
            client=invitation.client,
            target=email,
            summary=f'{email} joined {invitation.client.legal_name}.',
            metadata={'invitation_id': str(invitation.id), 'member_id': str(member.id)},
            request=request,
        )
        # Legal proof of consent — the serializer already enforces both checkboxes.
        try:
            TermsAcceptanceService.record(
                user=user,
                client=invitation.client,
                context=TermsAcceptance.CONTEXT_INVITATION,
                request=request,
                first_name=user.first_name,
                last_name=user.last_name,
            )
        except Exception:  # noqa: BLE001 — never block account activation on the proof.
            logger.exception('Unable to record the terms acceptance. user=%s', email)
        NotificationService.send(
            purpose='client_invitation_accepted',
            recipients=[email],
            context={
                'user': {'first_name': user.first_name, 'email': user.email},
                'client': {'legal_name': invitation.client.legal_name},
                'event_time': timezone.now(),
            },
        )
        return {'user': user, 'member': member, 'invitation': invitation, 'created': created}


class FolderService:
    BASE_FOLDERS = ('Contratos', 'Fiscal', 'Recursos_Humanos', 'Documentos_Permanentes')
    MONTH_FOLDERS = ('Compras', 'Vendas', 'Bancos', 'Recibos', 'Outros')

    @classmethod
    def ensure_base_structure(cls, *, client, created_by=None):
        created = []
        for name in cls.BASE_FOLDERS:
            folder, was_created = ClientFolder.objects.get_or_create(
                client=client,
                parent=None,
                slug=slugify(name),
                defaults={'name': name, 'folder_type': ClientFolder.TYPE_CATEGORY, 'created_by': created_by},
            )
            if was_created:
                created.append(folder)
        return created

    @classmethod
    @transaction.atomic
    def ensure_competence_folder(cls, *, client, year, month, created_by=None):
        """Creates Year/MM_Month/<categories> on demand."""
        year_folder, _ = ClientFolder.objects.get_or_create(
            client=client,
            parent=None,
            slug=slugify(str(year)),
            defaults={
                'name': str(year),
                'folder_type': ClientFolder.TYPE_YEAR,
                'year': year,
                'created_by': created_by,
            },
        )
        month_names = (
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
        )
        label = f'{month:02d}_{month_names[month - 1]}'
        month_folder, _ = ClientFolder.objects.get_or_create(
            client=client,
            parent=year_folder,
            slug=slugify(label),
            defaults={
                'name': label,
                'folder_type': ClientFolder.TYPE_MONTH,
                'year': year,
                'month': month,
                'created_by': created_by,
            },
        )
        for name in cls.MONTH_FOLDERS:
            ClientFolder.objects.get_or_create(
                client=client,
                parent=month_folder,
                slug=slugify(name),
                defaults={
                    'name': name,
                    'folder_type': ClientFolder.TYPE_CATEGORY,
                    'year': year,
                    'month': month,
                    'created_by': created_by,
                },
            )
        return month_folder

    @classmethod
    @transaction.atomic
    def ensure_protocol_folder(cls, *, protocol, created_by=None):
        """Folder where a protocol's documents land, so the tree stays browsable.

        Competence-based protocols go under Year/Month; the rest under
        `Protocolos/<number>`.
        """
        if protocol.competence_year and protocol.competence_month:
            return cls.ensure_competence_folder(
                client=protocol.client,
                year=protocol.competence_year,
                month=protocol.competence_month,
                created_by=created_by,
            )
        root, _ = ClientFolder.objects.get_or_create(
            client=protocol.client,
            parent=None,
            slug='protocolos',
            defaults={'name': 'Protocolos', 'folder_type': ClientFolder.TYPE_CATEGORY, 'created_by': created_by},
        )
        folder, _ = ClientFolder.objects.get_or_create(
            client=protocol.client,
            parent=root,
            slug=slugify(protocol.number),
            defaults={
                'name': protocol.number,
                'folder_type': ClientFolder.TYPE_PROTOCOL,
                'protocol': protocol,
                'created_by': created_by,
            },
        )
        return folder

    @staticmethod
    @transaction.atomic
    def create(*, client, name, parent=None, protocol=None, folder_type=ClientFolder.TYPE_CATEGORY,
               visibility=ClientFolder.VISIBILITY_CLIENT_AND_STAFF, created_by=None, request=None):
        if parent and parent.client_id != client.id:
            raise ValueError('The parent folder belongs to another client.')
        folder = ClientFolder(
            client=client,
            parent=parent,
            protocol=protocol,
            name=name.strip(),
            slug=slugify(name)[:180],
            folder_type=folder_type,
            visibility=visibility,
            created_by=created_by,
        )
        folder.full_clean()
        folder.save()
        if protocol:
            ProtocolEventService.record(
                protocol=protocol,
                event_type='folder_created',
                actor=created_by,
                new_value=folder.name,
                request=request,
            )
        return folder

    @staticmethod
    @transaction.atomic
    def move(*, folder, parent, performed_by=None):
        if parent is not None:
            if parent.client_id != folder.client_id:
                raise ValueError('The target folder belongs to another client.')
            node = parent
            while node is not None:
                if node.pk == folder.pk:
                    raise ValueError('A folder cannot be moved into itself.')
                node = node.parent
        folder.parent = parent
        folder.full_clean()
        folder.save(update_fields=('parent', 'updated_at'))
        return folder

    @staticmethod
    @transaction.atomic
    def archive(*, folder, performed_by=None):
        folder.archived_at = timezone.now()
        folder.save(update_fields=('archived_at', 'updated_at'))
        return folder


class ProtocolService:
    @staticmethod
    def _next_number(year):
        counter, _ = ProtocolCounter.objects.select_for_update().get_or_create(year=year)
        counter.last_number += 1
        counter.save(update_fields=('last_number',))
        return f'VEL-{year}-{counter.last_number:06d}'

    @classmethod
    @transaction.atomic
    def create(cls, *, client, data, created_by=None, request=None):
        if not client.is_active:
            raise ValueError('Protocols can only be created for active clients.')
        year = timezone.now().year
        protocol = Protocol(client=client, created_by=created_by, number=cls._next_number(year), **data)
        protocol.full_clean(exclude=('number',))
        protocol.save()
        ProtocolEventService.record(
            protocol=protocol,
            event_type='protocol_created',
            actor=created_by,
            new_value=protocol.status,
            request=request,
        )
        PortalAudit.record(
            event_type='protocol_created',
            actor=created_by,
            client=client,
            target=protocol.number,
            summary=protocol.title,
            request=request,
        )
        cls._notify_members(protocol, purpose='protocol_created')
        return protocol

    @staticmethod
    def _notify_members(protocol, *, purpose, extra=None):
        emails = list(
            protocol.client.members.filter(status=LifecycleStatus.ACTIVE).values_list('user__email', flat=True)
        )
        NotificationService.send(
            purpose=purpose,
            recipients=emails,
            context={
                'client': {'legal_name': protocol.client.legal_name},
                'protocol': {
                    'number': protocol.number,
                    'title': protocol.title,
                    'status': protocol.client_status_label,
                    'due_date': protocol.due_date,
                },
                'event_time': timezone.now(),
                **(extra or {}),
            },
        )

    @classmethod
    @transaction.atomic
    def transition(cls, *, protocol, status, performed_by=None, is_manager=False, request=None):
        protocol = Protocol.objects.select_for_update().get(pk=protocol.pk)
        if status == protocol.status:
            return protocol
        if not protocol.can_transition_to(status):
            raise ValueError(f'Invalid transition: {protocol.status} → {status}.')
        reopening = protocol.status == Protocol.STATUS_COMPLETED and status == Protocol.STATUS_UNDER_REVIEW
        if reopening and not is_manager:
            raise ValueError('Only STAFF_MANAGER can reopen a completed protocol.')

        previous = protocol.status
        protocol.status = status
        now = timezone.now()
        if status == Protocol.STATUS_WAITING_DOCUMENTS and not protocol.started_at:
            protocol.started_at = now
        if status == Protocol.STATUS_COMPLETED:
            protocol.completed_at = now
            protocol.closed_at = now
        if status == Protocol.STATUS_CANCELLED:
            protocol.cancelled_at = now
        if status == Protocol.STATUS_ARCHIVED:
            protocol.archived_at = now
        if reopening:
            protocol.completed_at = None
            protocol.closed_at = None
        protocol.save()

        event_type = {
            Protocol.STATUS_COMPLETED: 'protocol_completed',
            Protocol.STATUS_CANCELLED: 'protocol_cancelled',
            Protocol.STATUS_ARCHIVED: 'protocol_archived',
        }.get(status, 'protocol_reopened' if reopening else 'status_changed')
        ProtocolEventService.record(
            protocol=protocol,
            event_type=event_type,
            actor=performed_by,
            old_value=previous,
            new_value=status,
            request=request,
        )
        purpose = {
            Protocol.STATUS_COMPLETED: 'protocol_completed',
            Protocol.STATUS_ACTION_REQUIRED: 'client_action_required',
        }.get(status, 'protocol_reopened' if reopening else 'protocol_status_changed')
        cls._notify_members(protocol, purpose=purpose)
        return protocol

    @staticmethod
    @transaction.atomic
    def assign(*, protocol, staff_user, performed_by=None, request=None):
        previous = user_label(protocol.assigned_to)
        protocol.assigned_to = staff_user
        protocol.save(update_fields=('assigned_to', 'updated_at'))
        ProtocolEventService.record(
            protocol=protocol,
            event_type='staff_assigned',
            actor=performed_by,
            old_value=previous,
            new_value=user_label(staff_user),
            request=request,
        )
        return protocol

    @staticmethod
    @transaction.atomic
    def update(*, protocol, data, performed_by=None, request=None):
        old_due_date = protocol.due_date
        for field, value in data.items():
            setattr(protocol, field, value)
        protocol.full_clean(exclude=('number',))
        protocol.save()
        if 'due_date' in data and old_due_date != protocol.due_date:
            ProtocolEventService.record(
                protocol=protocol,
                event_type='due_date_changed',
                actor=performed_by,
                old_value=old_due_date or '',
                new_value=protocol.due_date or '',
                request=request,
            )
        else:
            ProtocolEventService.record(
                protocol=protocol,
                event_type='protocol_updated',
                actor=performed_by,
                metadata={'fields': sorted(data.keys())},
                request=request,
            )
        return protocol


class RequirementService:
    @staticmethod
    @transaction.atomic
    def create(*, protocol, data, created_by=None, request=None):
        requirement = ProtocolRequirement.objects.create(protocol=protocol, created_by=created_by, **data)
        ProtocolEventService.record(
            protocol=protocol,
            event_type='document_requested',
            actor=created_by,
            new_value=requirement.title,
            request=request,
        )
        ProtocolService._notify_members(protocol, purpose='documents_requested')
        return requirement

    @staticmethod
    @transaction.atomic
    def update_status(*, requirement, status, performed_by=None, document=None, request=None):
        requirement.status = status
        if document is not None:
            requirement.fulfilled_by_document = document
        if status in {ProtocolRequirement.STATUS_ACCEPTED, ProtocolRequirement.STATUS_WAIVED}:
            requirement.completed_at = timezone.now()
        requirement.save()
        return requirement


class DocumentService:
    """Upload, versioning, scanning and controlled download."""

    @staticmethod
    def _settings():
        return DocumentSettings.load()

    @staticmethod
    def storage_key(*, client_id, protocol_id, document_id, version_id):
        protocol_part = str(protocol_id) if protocol_id else 'no-protocol'
        return (
            f'clients/{client_id}/protocols/{protocol_part}'
            f'/documents/{document_id}/versions/{version_id}'
        )

    @classmethod
    def validate_upload(cls, *, upload, client, protocol=None, is_staff=True):
        """Validates one upload.

        Clients are held to `client_allowed_extensions` (ZIP only by default) so
        every delivery arrives as a single package instead of loose files.
        """
        settings = cls._settings()
        allowed = settings.extensions_for(is_staff=is_staff)
        name = safe_filename(getattr(upload, 'name', ''))
        extension = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        if not extension:
            raise ValueError('The file must have an extension.')
        if extension not in allowed:
            expected = ', '.join(f'.{item}' for item in sorted(allowed))
            raise ValueError(f'File type not allowed: .{extension}. Accepted: {expected}.')
        if extension == 'zip' and not settings.allow_zip:
            raise ValueError('ZIP files are not accepted.')
        size = getattr(upload, 'size', 0)
        if size <= 0:
            raise ValueError('Empty file.')
        if size > settings.max_file_size_bytes:
            raise ValueError(f'The file exceeds the {settings.max_file_size_mb} MB limit.')
        if protocol is not None:
            count = Document.objects.filter(protocol=protocol).count()
            if count >= settings.max_files_per_protocol:
                raise ValueError('This protocol reached the maximum number of documents.')
        return name, extension

    @staticmethod
    def _checksum_and_mime(upload):
        digest = hashlib.sha256()
        head = b''
        for chunk in upload.chunks():
            if not head:
                head = chunk[:2048]
            digest.update(chunk)
        upload.seek(0)
        guessed, _ = mimetypes.guess_type(getattr(upload, 'name', '') or '')
        detected = ''
        # Magic-number sniffing for the formats that matter most.
        signatures = (
            (b'%PDF-', 'application/pdf'),
            (b'PK\x03\x04', 'application/zip'),
            (b'\xff\xd8\xff', 'image/jpeg'),
            (b'\x89PNG\r\n\x1a\n', 'image/png'),
            (b'\xd0\xcf\x11\xe0', 'application/vnd.ms-office'),
        )
        for signature, mime in signatures:
            if head.startswith(signature):
                detected = mime
                break
        if not detected and head[:5].lower().startswith(b'<?xml'):
            detected = 'application/xml'
        return digest.hexdigest(), (guessed or ''), detected

    @classmethod
    @transaction.atomic
    def upload(cls, *, client, upload, title='', protocol=None, folder=None, uploaded_by=None,
               requirement=None, visibility=Document.VISIBILITY_CLIENT_AND_STAFF, is_staff=True, request=None):
        if not client.is_active:
            raise ValueError('Uploads are blocked for inactive clients.')
        if protocol is not None and not protocol.is_open:
            raise ValueError('This protocol is closed for new documents.')
        name, extension = cls.validate_upload(
            upload=upload, client=client, protocol=protocol, is_staff=is_staff,
        )
        checksum, content_type, detected = cls._checksum_and_mime(upload)

        # Keep the explorer meaningful: every protocol upload lands in a folder.
        if folder is None and protocol is not None:
            folder = FolderService.ensure_protocol_folder(protocol=protocol, created_by=uploaded_by)

        document = Document.objects.create(
            client=client,
            protocol=protocol,
            folder=folder,
            title=(title or name)[:255],
            original_name=name,
            category=extension,
            status=Document.STATUS_PENDING_SCAN,
            visibility=visibility,
            uploaded_by=uploaded_by,
            uploader_name_snapshot=user_label(uploaded_by),
            uploader_email_snapshot=getattr(uploaded_by, 'email', '') or '',
        )
        version = cls._create_version(
            document=document,
            upload=upload,
            checksum=checksum,
            content_type=content_type,
            detected=detected,
            uploaded_by=uploaded_by,
            change_reason='Initial upload.',
        )
        if requirement is not None:
            RequirementService.update_status(
                requirement=requirement,
                status=ProtocolRequirement.STATUS_UPLOADED,
                performed_by=uploaded_by,
                document=document,
            )
        if protocol is not None:
            ProtocolEventService.record(
                protocol=protocol,
                event_type='document_uploaded',
                actor=uploaded_by,
                new_value=document.title,
                metadata={'document_id': str(document.id), 'version': version.version_number},
                request=request,
            )
        PortalAudit.record(
            event_type='document_uploaded',
            actor=uploaded_by,
            client=client,
            target=document.title,
            summary=f'Upload of {document.title}.',
            metadata={'document_id': str(document.id), 'checksum': checksum},
            request=request,
        )
        cls.schedule_scan(version)
        return document, version

    @classmethod
    @transaction.atomic
    def new_version(cls, *, document, upload, uploaded_by=None, change_reason='', is_staff=True, request=None):
        if not document.client.is_active:
            raise ValueError('Uploads are blocked for inactive clients.')
        name, extension = cls.validate_upload(
            upload=upload, client=document.client, protocol=document.protocol, is_staff=is_staff,
        )
        checksum, content_type, detected = cls._checksum_and_mime(upload)
        version = cls._create_version(
            document=document,
            upload=upload,
            checksum=checksum,
            content_type=content_type,
            detected=detected,
            uploaded_by=uploaded_by,
            change_reason=change_reason or 'New version.',
        )
        document.status = Document.STATUS_PENDING_SCAN
        document.original_name = name
        document.save(update_fields=('status', 'original_name', 'updated_at'))
        if document.protocol_id:
            ProtocolEventService.record(
                protocol=document.protocol,
                event_type='document_replaced',
                actor=uploaded_by,
                new_value=document.title,
                metadata={'document_id': str(document.id), 'version': version.version_number},
                request=request,
            )
        cls.schedule_scan(version)
        return version

    @staticmethod
    def _create_version(*, document, upload, checksum, content_type, detected, uploaded_by, change_reason):
        last = document.versions.order_by('-version_number').first()
        number = (last.version_number + 1) if last else 1
        version = DocumentVersion(
            document=document,
            version_number=number,
            storage_key='',
            original_name=safe_filename(getattr(upload, 'name', '')),
            content_type=content_type,
            detected_mime_type=detected,
            size=getattr(upload, 'size', 0),
            checksum_sha256=checksum,
            uploaded_by=uploaded_by,
            uploader_name_snapshot=user_label(uploaded_by),
            uploader_email_snapshot=getattr(uploaded_by, 'email', '') or '',
            change_reason=change_reason,
        )
        version.storage_key = DocumentService.storage_key(
            client_id=document.client_id,
            protocol_id=document.protocol_id,
            document_id=document.id,
            version_id=version.id,
        )
        upload.seek(0)
        StorageService.upload(key=version.storage_key, content=upload)
        version.save()
        document.current_version = version
        document.save(update_fields=('current_version', 'updated_at'))
        return version

    @staticmethod
    def schedule_scan(version):
        from .tasks import scan_document_version

        try:
            scan_document_version.delay(str(version.id))
        except Exception:
            logger.exception('Unable to queue the antivirus scan. version_id=%s', version.id)
            DocumentService.run_scan(version)

    @staticmethod
    @transaction.atomic
    def run_scan(version):
        """Executes the scan and applies the resulting document status."""
        settings = DocumentSettings.load()
        document = version.document
        if not settings.require_antivirus and not settings.antivirus_host:
            result = ScanResult(ScanResult.SKIPPED, 'Antivirus disabled.')
        else:
            with StorageService.open(version.storage_key) as handle:
                result = AntivirusService.scan_stream(
                    handle,
                    host=settings.antivirus_host,
                    port=settings.antivirus_port,
                    timeout=settings.antivirus_timeout_seconds,
                )

        version.scan_status = {
            ScanResult.CLEAN: DocumentVersion.SCAN_CLEAN,
            ScanResult.INFECTED: DocumentVersion.SCAN_INFECTED,
            ScanResult.ERROR: DocumentVersion.SCAN_ERROR,
            ScanResult.SKIPPED: DocumentVersion.SCAN_SKIPPED,
        }[result.status]
        version.scan_message = result.message
        version.scanned_at = timezone.now()
        version.save(update_fields=('scan_status', 'scan_message', 'scanned_at'))

        if result.status == ScanResult.INFECTED:
            document.status = Document.STATUS_INFECTED
        elif result.status == ScanResult.ERROR and settings.require_antivirus:
            document.status = Document.STATUS_QUARANTINED
        else:
            document.status = Document.STATUS_AVAILABLE
        document.save(update_fields=('status', 'updated_at'))

        if document.protocol_id:
            ProtocolEventService.record(
                protocol=document.protocol,
                event_type='document_uploaded' if document.status == Document.STATUS_AVAILABLE else 'document_rejected',
                actor=None,
                new_value=document.status,
                metadata={'document_id': str(document.id), 'scan_status': version.scan_status},
            )
        # Mirror only approved files to the company Dropbox (never infected/quarantined).
        if document.status == Document.STATUS_AVAILABLE:
            try:
                from .tasks import mirror_document_version_to_dropbox

                transaction.on_commit(lambda: mirror_document_version_to_dropbox.delay(str(version.id)))
            except Exception:  # noqa: BLE001 — mirroring must not affect the scan result.
                logger.exception('Unable to queue the Dropbox mirror. version_id=%s', version.id)
        if document.status == Document.STATUS_AVAILABLE and document.visibility != Document.VISIBILITY_STAFF_ONLY:
            emails = list(
                document.client.members.filter(status=LifecycleStatus.ACTIVE).values_list('user__email', flat=True)
            )
            NotificationService.send(
                purpose='document_available',
                recipients=emails,
                context={
                    'client': {'legal_name': document.client.legal_name},
                    'document': {'title': document.title},
                    'event_time': timezone.now(),
                },
            )
        return version

    @staticmethod
    @transaction.atomic
    def reject(*, document, reason, performed_by=None, request=None):
        document.status = Document.STATUS_REJECTED
        document.rejection_reason = reason[:255]
        document.save(update_fields=('status', 'rejection_reason', 'updated_at'))
        if document.protocol_id:
            ProtocolEventService.record(
                protocol=document.protocol,
                event_type='document_rejected',
                actor=performed_by,
                new_value=reason,
                metadata={'document_id': str(document.id)},
                request=request,
            )
        NotificationService.send(
            purpose='document_rejected',
            recipients=[document.uploader_email_snapshot],
            context={
                'document': {'title': document.title},
                'message': reason,
                'event_time': timezone.now(),
            },
        )
        return document

    @staticmethod
    @transaction.atomic
    def archive(*, document, performed_by=None, request=None):
        document.status = Document.STATUS_ARCHIVED
        document.archived_at = timezone.now()
        document.save(update_fields=('status', 'archived_at', 'updated_at'))
        PortalAudit.record(
            event_type='document_archived',
            actor=performed_by,
            client=document.client,
            target=document.title,
            summary='Document archived.',
            request=request,
        )
        return document

    @staticmethod
    @transaction.atomic
    def move(*, document, folder, performed_by=None):
        if folder is not None and folder.client_id != document.client_id:
            raise ValueError('The target folder belongs to another client.')
        document.folder = folder
        document.save(update_fields=('folder', 'updated_at'))
        return document

    @classmethod
    @transaction.atomic
    def build_download(cls, *, document, user, request=None):
        """Validates permission and scan state, then returns a short-lived URL."""
        version = document.current_version
        if version is None:
            raise ValueError('This document has no stored version.')
        if not document.is_downloadable:
            raise ValueError('This document is not available for download.')
        if version.scan_status == DocumentVersion.SCAN_INFECTED:
            raise ValueError('This document is quarantined.')

        settings = cls._settings()
        url = StorageService.download_url(version.storage_key, expires_in=settings.signed_url_seconds)
        DownloadAudit.objects.create(
            document=document,
            version=version,
            user=user,
            user_name_snapshot=user_label(user),
            client=document.client,
            ip_address=RequestContext.ip(request) if request else None,
            user_agent=RequestContext.user_agent(request) if request else '',
        )
        if document.protocol_id:
            ProtocolEventService.record(
                protocol=document.protocol,
                event_type='document_downloaded',
                actor=user,
                new_value=document.title,
                metadata={'document_id': str(document.id)},
                request=request,
            )
        return {'url': url, 'expires_in': settings.signed_url_seconds, 'version': version.version_number}


class CommentService:
    @staticmethod
    @transaction.atomic
    def create(*, protocol, author, message, visibility=ProtocolComment.VISIBILITY_PUBLIC, request=None):
        comment = ProtocolComment.objects.create(
            protocol=protocol,
            author=author,
            author_name_snapshot=user_label(author),
            author_email_snapshot=getattr(author, 'email', '') or '',
            message=message.strip(),
            visibility=visibility,
        )
        ProtocolEventService.record(
            protocol=protocol,
            event_type='internal_note_added' if visibility == ProtocolComment.VISIBILITY_INTERNAL else 'comment_added',
            actor=author,
            request=request,
        )
        if visibility == ProtocolComment.VISIBILITY_PUBLIC:
            ProtocolService._notify_members(protocol, purpose='staff_public_comment')
        return comment

    @staticmethod
    @transaction.atomic
    def update(*, comment, message):
        comment.message = message.strip()
        comment.is_edited = True
        comment.edited_at = timezone.now()
        comment.save(update_fields=('message', 'is_edited', 'edited_at', 'updated_at'))
        return comment

    @staticmethod
    @transaction.atomic
    def archive(*, comment):
        comment.archived_at = timezone.now()
        comment.save(update_fields=('archived_at', 'updated_at'))
        return comment


class PortalAccountLifecycleService:
    """Bridges the core account lifecycle with the module's own side effects."""

    @staticmethod
    @transaction.atomic
    def deactivate(*, user, performed_by=None, reason='', request=None):
        lifecycle = AccountLifecycleService.deactivate(
            user=user, performed_by=performed_by, reason=reason, request=request,
        )
        for member in ClientMember.objects.filter(user=user, status=LifecycleStatus.ACTIVE):
            ClientMemberService.deactivate(member=member, performed_by=performed_by, reason=reason, request=request)
        return lifecycle

    @staticmethod
    @transaction.atomic
    def archive(*, user, performed_by=None, reason='', request=None):
        lifecycle = AccountLifecycleService.archive(
            user=user, performed_by=performed_by, reason=reason, request=request,
        )
        ClientInvitation.objects.filter(
            email__iexact=user.email,
            status=ClientInvitation.STATUS_PENDING,
        ).update(status=ClientInvitation.STATUS_CANCELLED, revoked_at=timezone.now())
        for member in ClientMember.objects.filter(user=user).exclude(status=LifecycleStatus.ARCHIVED):
            ClientMemberService.archive(member=member, performed_by=performed_by, reason=reason, request=request)
        PortalAudit.record(
            event_type='account_archived',
            actor=performed_by,
            target=user.email,
            summary=reason or 'Account archived.',
            request=request,
        )
        return lifecycle
