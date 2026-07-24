from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from config.common.models import DocumentSettings, EmailTemplate, SecuritySettings
from config.common.storage import StorageService

from . import selectors
from .models import (
    Client,
    ClientFolder,
    ClientInvitation,
    ClientMember,
    Document,
    DocumentVersion,
    LifecycleStatus,
    Protocol,
    ProtocolComment,
    ProtocolRequirement,
)
from .services import (
    ClientLifecycleService,
    ClientService,
    CommentService,
    DocumentService,
    FolderService,
    InvitationService,
    ProtocolService,
    RequirementService,
)

PASSWORD = 'StrongPassword@123'


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class ClientPortalTestCase(APITestCase):
    """Shared fixtures: one client, one staff manager, one staff and one member."""

    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_veloma', verbosity=0)
        EmailTemplate.objects.update(delivery_mode='sync')
        security = SecuritySettings.load()
        security.api_rate_limit_enabled = False
        security.save()
        documents = DocumentSettings.load()
        documents.require_antivirus = False
        documents.antivirus_host = ''
        documents.save()

    def setUp(self):
        self.manager = self._user('manager@veloma.local', 'STAFF_MANAGER')
        self.staff = self._user('staff@veloma.local', 'STAFF')
        self.client_record = ClientService.create(
            data={
                'legal_name': 'Cliente Teste Lda',
                'nif': '501234567',
                'entity_type': 'quotas',
                'assigned_staff': self.staff,
            },
            performed_by=self.manager,
        )

    def _user(self, email, group=None, is_active=True):
        user = User.objects.create_user(
            username=email,
            email=email,
            password=PASSWORD,
            first_name=email.split('@')[0].title(),
            last_name='Teste',
            is_active=is_active,
        )
        if group:
            user.groups.add(Group.objects.get_or_create(name=group)[0])
        return user

    def _authenticate(self, user):
        response = self.client.post('/api/auth/login/', {
            'email': user.email,
            'password': PASSWORD,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        token = response.data['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token

    def _member(self, email='cliente@example.com', role=ClientMember.ROLE_OWNER, client=None):
        user = self._user(email, 'USER')
        member = ClientMember.objects.create(
            client=client or self.client_record,
            user=user,
            role=role,
            status=LifecycleStatus.ACTIVE,
        )
        return user, member

    def _protocol(self, status=Protocol.STATUS_WAITING_DOCUMENTS):
        protocol = ProtocolService.create(
            client=self.client_record,
            data={'title': 'Documentos mensais', 'category': 'monthly_accounting'},
            created_by=self.staff,
        )
        if status != Protocol.STATUS_DRAFT:
            protocol = ProtocolService.transition(
                protocol=protocol, status=Protocol.STATUS_WAITING_DOCUMENTS, performed_by=self.staff,
            )
        return protocol

    @staticmethod
    def _upload(name='fatura.pdf', content=b'%PDF-1.4 conteudo de teste'):
        return SimpleUploadedFile(name, content, content_type='application/pdf')


class InvitationTests(ClientPortalTestCase):
    def test_public_registration_is_disabled(self):
        response = self.client.post('/api/auth/register/', {
            'first_name': 'Publico',
            'last_name': 'Teste',
            'email': 'publico@example.com',
            'password': PASSWORD,
            'password2': PASSWORD,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='publico@example.com').exists())

    def test_staff_creates_invitation_and_client_accepts(self):
        invitation, token = InvitationService.create(
            client=self.client_record,
            email='novo@example.com',
            role=ClientMember.ROLE_OWNER,
            invited_by=self.staff,
        )
        self.assertEqual(invitation.status, ClientInvitation.STATUS_PENDING)
        self.assertNotEqual(invitation.token_hash, token)

        validate = self.client.post('/api/client-portal/invitations/validate/', {'token': token}, format='json')
        self.assertEqual(validate.status_code, 200)
        self.assertEqual(validate.data['data']['email'], 'novo@example.com')

        accept = self.client.post('/api/client-portal/invitations/accept/', {
            'token': token,
            'first_name': 'Novo',
            'last_name': 'Cliente',
            'password': PASSWORD,
            'password2': PASSWORD,
            'accept_terms': True,
            'accept_privacy_policy': True,
        }, format='json')
        self.assertEqual(accept.status_code, 201, accept.data)

        user = User.objects.get(username='novo@example.com')
        self.assertEqual(user.email, 'novo@example.com')
        self.assertTrue(user.groups.filter(name='USER').exists())
        self.assertTrue(ClientMember.objects.filter(user=user, client=self.client_record).exists())
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ClientInvitation.STATUS_ACCEPTED)

    def test_accept_records_terms_acceptance_proof(self):
        from .legal import PRIVACY_VERSION, TERMS_VERSION
        from .models import TermsAcceptance

        _invitation, token = InvitationService.create(
            client=self.client_record,
            email='prova@example.com',
            role=ClientMember.ROLE_OWNER,
            invited_by=self.staff,
        )
        accept = self.client.post('/api/client-portal/invitations/accept/', {
            'token': token,
            'first_name': 'Prova',
            'last_name': 'Legal',
            'password': PASSWORD,
            'password2': PASSWORD,
            'accept_terms': True,
            'accept_privacy_policy': True,
        }, format='json')
        self.assertEqual(accept.status_code, 201, accept.data)

        user = User.objects.get(username='prova@example.com')
        record = TermsAcceptance.objects.get(user=user)
        self.assertEqual(record.context, TermsAcceptance.CONTEXT_INVITATION)
        self.assertEqual(record.terms_version, TERMS_VERSION)
        self.assertEqual(record.privacy_version, PRIVACY_VERSION)
        self.assertEqual(record.client_id, self.client_record.id)
        self.assertEqual(record.email_snapshot, 'prova@example.com')
        # A sealed PDF proof is stored and its key recorded.
        self.assertTrue(record.pdf_storage_key)
        self.assertTrue(StorageService.exists(record.pdf_storage_key))

    def test_invitation_cannot_be_accepted_twice(self):
        _invitation, token = InvitationService.create(
            client=self.client_record, email='dupla@example.com', role=ClientMember.ROLE_EMPLOYEE,
            invited_by=self.staff,
        )
        payload = {
            'token': token,
            'first_name': 'Dupla',
            'last_name': 'Teste',
            'password': PASSWORD,
            'password2': PASSWORD,
            'accept_terms': True,
            'accept_privacy_policy': True,
        }
        first = self.client.post('/api/client-portal/invitations/accept/', payload, format='json')
        self.assertEqual(first.status_code, 201)
        second = self.client.post('/api/client-portal/invitations/accept/', payload, format='json')
        self.assertEqual(second.status_code, 400)

    def test_invalid_and_expired_tokens_are_refused(self):
        response = self.client.post(
            '/api/client-portal/invitations/validate/', {'token': 'x' * 40}, format='json',
        )
        self.assertEqual(response.status_code, 400)

        invitation, token = InvitationService.create(
            client=self.client_record, email='expirado@example.com', role=ClientMember.ROLE_VIEWER,
            invited_by=self.staff,
        )
        ClientInvitation.objects.filter(pk=invitation.pk).update(expires_at=timezone.now() - timedelta(hours=1))
        expired = self.client.post('/api/client-portal/invitations/validate/', {'token': token}, format='json')
        self.assertEqual(expired.status_code, 400)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ClientInvitation.STATUS_EXPIRED)

    def test_revoked_invitation_cannot_be_used(self):
        invitation, token = InvitationService.create(
            client=self.client_record, email='revogado@example.com', role=ClientMember.ROLE_VIEWER,
            invited_by=self.staff,
        )
        InvitationService.revoke(invitation=invitation, performed_by=self.manager)
        response = self.client.post('/api/client-portal/invitations/validate/', {'token': token}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_resend_rotates_the_token(self):
        invitation, first_token = InvitationService.create(
            client=self.client_record, email='reenvio@example.com', role=ClientMember.ROLE_VIEWER,
            invited_by=self.staff,
        )
        invitation, second_token = InvitationService.resend(invitation=invitation, performed_by=self.staff)
        self.assertNotEqual(first_token, second_token)
        self.assertEqual(invitation.resend_count, 1)
        old = self.client.post('/api/client-portal/invitations/validate/', {'token': first_token}, format='json')
        self.assertEqual(old.status_code, 400)

    def test_portal_user_cannot_invite(self):
        user, _member = self._member()
        self._authenticate(user)
        response = self.client.post('/api/client-portal/invitations/', {
            'client': str(self.client_record.id),
            'email': 'outro@example.com',
            'role': ClientMember.ROLE_VIEWER,
        }, format='json')
        self.assertEqual(response.status_code, 403)


class ClientAccessTests(ClientPortalTestCase):
    def test_user_only_sees_own_clients(self):
        user, _member = self._member()
        other = ClientService.create(
            data={'legal_name': 'Outro Cliente Lda', 'nif': '502345678'}, performed_by=self.manager,
        )
        self._authenticate(user)
        response = self.client.get('/api/client-portal/clients/')
        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.data['data']['clients']}
        self.assertIn(str(self.client_record.id), ids)
        self.assertNotIn(str(other.id), ids)

        detail = self.client.get(f'/api/client-portal/clients/{other.id}/')
        self.assertEqual(detail.status_code, 404)

    def test_deactivated_client_blocks_uploads_and_new_protocols(self):
        user, _member = self._member()
        ClientLifecycleService.deactivate(
            client=self.client_record, performed_by=self.manager, reason='Contrato suspenso',
        )
        self.client_record.refresh_from_db()
        with self.assertRaises(ValueError):
            ProtocolService.create(
                client=self.client_record, data={'title': 'Novo'}, created_by=self.staff,
            )
        with self.assertRaises(ValueError):
            DocumentService.upload(
                client=self.client_record, upload=self._upload(), uploaded_by=user,
            )

    def test_archive_client_preserves_history_and_deactivates_members(self):
        user, member = self._member()
        protocol = self._protocol()
        ClientLifecycleService.archive(
            client=self.client_record, performed_by=self.manager, reason='Cliente encerrado',
        )
        self.client_record.refresh_from_db()
        member.refresh_from_db()

        self.assertEqual(self.client_record.status, LifecycleStatus.ARCHIVED)
        self.assertEqual(member.status, LifecycleStatus.DEACTIVATED)
        self.assertTrue(Protocol.objects.filter(pk=protocol.pk).exists())
        self.assertTrue(Client.objects.filter(pk=self.client_record.pk).exists())

    def test_restore_returns_client_as_deactivated(self):
        ClientLifecycleService.archive(client=self.client_record, performed_by=self.manager)
        ClientLifecycleService.restore(client=self.client_record, performed_by=self.manager)
        self.client_record.refresh_from_db()
        self.assertEqual(self.client_record.status, LifecycleStatus.DEACTIVATED)
        ClientLifecycleService.reactivate(client=self.client_record, performed_by=self.manager)
        self.client_record.refresh_from_db()
        self.assertEqual(self.client_record.status, LifecycleStatus.ACTIVE)

    def test_duplicate_active_membership_is_rejected(self):
        user, _member = self._member()
        with self.assertRaises(Exception):
            ClientMember.objects.create(
                client=self.client_record, user=user, role=ClientMember.ROLE_VIEWER,
                status=LifecycleStatus.ACTIVE,
            )


class ProtocolTests(ClientPortalTestCase):
    def test_open_request_opens_protocol_with_sla(self):
        from datetime import timedelta

        from .models import ProtocolSubject

        subject = ProtocolSubject.objects.create(name='Teste SLA', category='tax', sla_hours=48)
        before = timezone.now()
        protocol = ProtocolService.open_request(
            client=self.client_record, subject=subject, created_by=self.manager,
        )
        self.assertTrue(protocol.number.startswith(f'VEL-{timezone.now().year}-'))
        self.assertEqual(protocol.subject_id, subject.id)
        self.assertEqual(protocol.sla_hours, 48)
        self.assertEqual(protocol.status, Protocol.STATUS_WAITING_DOCUMENTS)
        self.assertEqual(protocol.title, 'Teste SLA')
        # Response deadline is now + SLA hours.
        self.assertGreaterEqual(protocol.response_due_at, before + timedelta(hours=47, minutes=59))
        self.assertLessEqual(protocol.response_due_at, timezone.now() + timedelta(hours=48))

    def test_protocol_number_is_sequential_and_public(self):
        first = self._protocol()
        second = self._protocol()
        year = timezone.now().year
        self.assertTrue(first.number.startswith(f'VEL-{year}-'))
        self.assertNotEqual(first.number, second.number)
        self.assertEqual(int(second.number.split('-')[-1]), int(first.number.split('-')[-1]) + 1)

    def test_valid_and_invalid_transitions(self):
        protocol = self._protocol()
        protocol = ProtocolService.transition(
            protocol=protocol, status=Protocol.STATUS_DOCUMENTS_RECEIVED, performed_by=self.staff,
        )
        self.assertEqual(protocol.status, Protocol.STATUS_DOCUMENTS_RECEIVED)
        with self.assertRaises(ValueError):
            ProtocolService.transition(
                protocol=protocol, status=Protocol.STATUS_COMPLETED, performed_by=self.staff,
            )

    def test_only_manager_can_reopen_a_completed_protocol(self):
        protocol = self._protocol()
        for status in (
            Protocol.STATUS_DOCUMENTS_RECEIVED,
            Protocol.STATUS_UNDER_REVIEW,
            Protocol.STATUS_COMPLETED,
        ):
            protocol = ProtocolService.transition(protocol=protocol, status=status, performed_by=self.staff)

        with self.assertRaises(ValueError):
            ProtocolService.transition(
                protocol=protocol, status=Protocol.STATUS_UNDER_REVIEW,
                performed_by=self.staff, is_manager=False,
            )
        protocol = ProtocolService.transition(
            protocol=protocol, status=Protocol.STATUS_UNDER_REVIEW,
            performed_by=self.manager, is_manager=True,
        )
        self.assertEqual(protocol.status, Protocol.STATUS_UNDER_REVIEW)
        self.assertIsNone(protocol.completed_at)

    def test_user_does_not_see_internal_notes(self):
        user, _member = self._member()
        protocol = self._protocol()
        CommentService.create(
            protocol=protocol, author=self.staff, message='Nota interna sensível',
            visibility=ProtocolComment.VISIBILITY_INTERNAL,
        )
        CommentService.create(
            protocol=protocol, author=self.staff, message='Mensagem pública',
            visibility=ProtocolComment.VISIBILITY_PUBLIC,
        )
        self._authenticate(user)
        response = self.client.get(f'/api/client-portal/protocols/{protocol.id}/comments/')
        self.assertEqual(response.status_code, 200)
        messages = [item['message'] for item in response.data['data']['comments']]
        self.assertIn('Mensagem pública', messages)
        self.assertNotIn('Nota interna sensível', messages)
        self.assertNotIn('internal', {item['visibility'] for item in response.data['data']['comments']})

    def test_user_cannot_create_internal_note(self):
        user, _member = self._member()
        protocol = self._protocol()
        self._authenticate(user)
        response = self.client.post(f'/api/client-portal/protocols/{protocol.id}/comments/', {
            'message': 'tentativa',
            'visibility': ProtocolComment.VISIBILITY_INTERNAL,
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_see_other_clients_protocols(self):
        user, _member = self._member()
        other_client = ClientService.create(
            data={'legal_name': 'Terceiro Lda', 'nif': '503456789'}, performed_by=self.manager,
        )
        other_protocol = ProtocolService.create(
            client=other_client, data={'title': 'Privado'}, created_by=self.staff,
        )
        self._authenticate(user)
        response = self.client.get(f'/api/client-portal/protocols/{other_protocol.id}/')
        self.assertEqual(response.status_code, 404)

    def test_client_timeline_hides_internal_events(self):
        user, _member = self._member()
        protocol = self._protocol()
        CommentService.create(
            protocol=protocol, author=self.staff, message='Nota', visibility=ProtocolComment.VISIBILITY_INTERNAL,
        )
        self._authenticate(user)
        response = self.client.get(f'/api/client-portal/protocols/{protocol.id}/timeline/')
        self.assertEqual(response.status_code, 200)
        types = {item['event_type'] for item in response.data['data']['timeline']}
        self.assertNotIn('internal_note_added', types)


class DocumentTests(ClientPortalTestCase):
    def test_delete_hard_removes_document_and_versions(self):
        from .models import DocumentVersion

        user, _member = self._member()
        document, version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), uploaded_by=user,
        )
        doc_id, version_id = document.id, version.id

        DocumentService.delete(document=document, performed_by=self.manager)

        self.assertFalse(Document.objects.filter(pk=doc_id).exists())
        self.assertFalse(DocumentVersion.objects.filter(pk=version_id).exists())

    def test_folder_delete_cascades_documents(self):
        from .models import Document as Doc
        from .services import FolderService

        user, _member = self._member()
        folder = FolderService.create(client=self.client_record, name='Temp', created_by=self.manager)
        DocumentService.upload(
            client=self.client_record, upload=self._upload(), folder=folder, uploaded_by=user,
        )
        FolderService.delete(folder=folder, performed_by=self.manager)
        self.assertFalse(ClientFolder.objects.filter(pk=folder.id).exists())
        self.assertEqual(Doc.objects.filter(client=self.client_record).count(), 0)

    def test_client_upload_without_protocol_auto_creates_one(self):
        user, _member = self._member()
        zip_file = SimpleUploadedFile('docs.zip', b'PK\x03\x04 conteudo', content_type='application/zip')
        document, _version = DocumentService.upload(
            client=self.client_record, upload=zip_file, uploaded_by=user, is_staff=False,
        )
        document.refresh_from_db()
        self.assertIsNotNone(document.protocol_id)
        self.assertTrue(document.protocol.number.startswith('VEL-'))
        # A second client upload reuses the same open request (no sprawl).
        zip2 = SimpleUploadedFile('docs2.zip', b'PK\x03\x04 outro', content_type='application/zip')
        document2, _v2 = DocumentService.upload(
            client=self.client_record, upload=zip2, uploaded_by=user, is_staff=False,
        )
        document2.refresh_from_db()
        self.assertEqual(document2.protocol_id, document.protocol_id)

    def test_upload_creates_document_and_version(self):
        user, _member = self._member()
        protocol = self._protocol()
        document, version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), protocol=protocol, uploaded_by=user,
        )
        self.assertEqual(version.version_number, 1)
        self.assertEqual(len(version.checksum_sha256), 64)
        self.assertTrue(version.storage_key.startswith(f'clients/{self.client_record.id}/'))
        document.refresh_from_db()
        version.refresh_from_db()
        self.assertEqual(document.current_version_id, version.id)
        self.assertEqual(document.status, Document.STATUS_AVAILABLE)
        self.assertEqual(version.scan_status, DocumentVersion.SCAN_SKIPPED)

    def test_invalid_extension_and_oversized_file_are_refused(self):
        user, _member = self._member()
        with self.assertRaises(ValueError):
            DocumentService.upload(
                client=self.client_record,
                upload=SimpleUploadedFile('script.exe', b'MZ binario', content_type='application/octet-stream'),
                uploaded_by=user,
            )
        settings = DocumentSettings.load()
        settings.max_file_size_mb = 1
        settings.save()
        big = SimpleUploadedFile('grande.pdf', b'%PDF-' + b'0' * (2 * 1024 * 1024), content_type='application/pdf')
        with self.assertRaises(ValueError):
            DocumentService.upload(client=self.client_record, upload=big, uploaded_by=user)

    def test_mime_detection_records_the_real_type(self):
        user, _member = self._member()
        fake = SimpleUploadedFile('falso.pdf', b'PK\x03\x04zip real', content_type='application/pdf')
        _document, version = DocumentService.upload(
            client=self.client_record, upload=fake, uploaded_by=user,
        )
        self.assertEqual(version.detected_mime_type, 'application/zip')
        self.assertEqual(version.content_type, 'application/pdf')

    def test_new_version_never_replaces_the_previous_one(self):
        user, _member = self._member()
        document, first = DocumentService.upload(
            client=self.client_record, upload=self._upload(), uploaded_by=user,
        )
        second = DocumentService.new_version(
            document=document,
            upload=self._upload(content=b'%PDF-1.4 nova versao'),
            uploaded_by=user,
            change_reason='Correção',
        )
        self.assertEqual(second.version_number, 2)
        self.assertNotEqual(first.storage_key, second.storage_key)
        self.assertEqual(document.versions.count(), 2)
        document.refresh_from_db()
        self.assertEqual(document.current_version_id, second.id)

    def test_infected_document_is_not_downloadable(self):
        user, _member = self._member()
        document, version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), uploaded_by=user,
        )
        version.scan_status = DocumentVersion.SCAN_INFECTED
        version.save(update_fields=('scan_status',))
        document.status = Document.STATUS_INFECTED
        document.save(update_fields=('status',))
        with self.assertRaises(ValueError):
            DocumentService.build_download(document=document, user=user)

    def test_download_requires_authorisation_and_creates_audit(self):
        user, _member = self._member()
        document, _version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), uploaded_by=user,
        )
        self._authenticate(user)
        response = self.client.post(f'/api/client-portal/documents/{document.id}/download/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn('url', response.data['data'])
        self.assertEqual(document.downloads.count(), 1)

        intruder = self._user('intruso@example.com', 'USER')
        self.client.credentials()
        self._authenticate(intruder)
        denied = self.client.post(f'/api/client-portal/documents/{document.id}/download/')
        self.assertEqual(denied.status_code, 404)

    def test_download_file_streams_the_content_and_creates_audit(self):
        user, _member = self._member()
        document, _version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), uploaded_by=user,
        )
        self._authenticate(user)
        response = self.client.get(f'/api/client-portal/documents/{document.id}/file/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.get('Content-Disposition', ''))
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 conteudo de teste')
        self.assertEqual(document.downloads.count(), 1)

        intruder = self._user('intruso-file@example.com', 'USER')
        self.client.credentials()
        self._authenticate(intruder)
        denied = self.client.get(f'/api/client-portal/documents/{document.id}/file/')
        self.assertEqual(denied.status_code, 404)

    def test_staff_only_documents_are_invisible_to_the_client(self):
        user, _member = self._member()
        document, _version = DocumentService.upload(
            client=self.client_record,
            upload=self._upload(name='interno.pdf'),
            uploaded_by=self.staff,
            visibility=Document.VISIBILITY_STAFF_ONLY,
        )
        self._authenticate(user)
        response = self.client.get('/api/client-portal/documents/')
        ids = {item['id'] for item in response.data['data']['documents']}
        self.assertNotIn(str(document.id), ids)
        detail = self.client.get(f'/api/client-portal/documents/{document.id}/')
        self.assertEqual(detail.status_code, 404)

    def test_upload_fulfils_a_requirement(self):
        user, _member = self._member()
        protocol = self._protocol()
        requirement = RequirementService.create(
            protocol=protocol, data={'title': 'Extrato bancário'}, created_by=self.staff,
        )
        document, _version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), protocol=protocol,
            requirement=requirement, uploaded_by=user,
        )
        requirement.refresh_from_db()
        self.assertEqual(requirement.status, ProtocolRequirement.STATUS_UPLOADED)
        self.assertEqual(requirement.fulfilled_by_document_id, document.id)


class ApiFlowTests(ClientPortalTestCase):
    def test_staff_end_to_end_flow_through_the_api(self):
        self._authenticate(self.staff)

        created = self.client.post('/api/client-portal/protocols/', {
            'client': str(self.client_record.id),
            'title': 'IVA 3.º trimestre',
            'category': 'vat',
        }, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        protocol_id = created.data['data']['protocol']['id']

        requirement = self.client.post(f'/api/client-portal/protocols/{protocol_id}/requirements/', {
            'title': 'Faturas de compra',
        }, format='json')
        self.assertEqual(requirement.status_code, 201)

        transition = self.client.post(f'/api/client-portal/protocols/{protocol_id}/transition/', {
            'status': Protocol.STATUS_WAITING_DOCUMENTS,
        }, format='json')
        self.assertEqual(transition.status_code, 200, transition.data)

        upload = self.client.post('/api/client-portal/documents/upload/', {
            'protocol': protocol_id,
            'file': self._upload(),
        }, format='multipart')
        self.assertEqual(upload.status_code, 201, upload.data)

        timeline = self.client.get(f'/api/client-portal/protocols/{protocol_id}/timeline/')
        self.assertEqual(timeline.status_code, 200)
        types = {item['event_type'] for item in timeline.data['data']['timeline']}
        self.assertIn('protocol_created', types)
        self.assertIn('document_requested', types)
        self.assertIn('document_uploaded', types)

        dashboard = self.client.get('/api/client-portal/dashboard/')
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn('staff', dashboard.data['data'])

    def test_api_has_no_physical_delete(self):
        self._authenticate(self.manager)
        protocol = self._protocol()
        document, _version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), protocol=protocol, uploaded_by=self.staff,
        )
        for url in (
            f'/api/client-portal/protocols/{protocol.id}/',
            f'/api/client-portal/documents/{document.id}/',
            f'/api/client-portal/clients/{self.client_record.id}/',
        ):
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 405, url)

    def test_django_admin_account_cannot_use_the_portal(self):
        admin = User.objects.create_superuser(
            username='portal-admin@example.com',
            email='portal-admin@example.com',
            password=PASSWORD,
        )
        response = self.client.post('/api/auth/login/', {
            'email': admin.email,
            'password': PASSWORD,
        }, format='json')
        self.assertEqual(response.status_code, 400)


class AccountLifecycleIntegrationTests(ClientPortalTestCase):
    def test_archiving_an_account_archives_memberships_and_keeps_documents(self):
        from .services import PortalAccountLifecycleService

        user, member = self._member()
        protocol = self._protocol()
        document, _version = DocumentService.upload(
            client=self.client_record, upload=self._upload(), protocol=protocol, uploaded_by=user,
        )
        InvitationService.create(
            client=self.client_record, email=user.email.replace('cliente', 'convite'),
            role=ClientMember.ROLE_VIEWER, invited_by=self.staff,
        )

        PortalAccountLifecycleService.archive(
            user=user, performed_by=self.manager, reason='Saída do colaborador',
        )

        user.refresh_from_db()
        member.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(member.status, LifecycleStatus.ARCHIVED)
        self.assertTrue(Document.objects.filter(pk=document.pk).exists())
        self.assertTrue(Protocol.objects.filter(pk=protocol.pk).exists())
        self.assertEqual(document.uploader_email_snapshot, user.email)

        refused = self.client.post('/api/auth/login/', {
            'email': user.email,
            'password': PASSWORD,
        }, format='json')
        self.assertEqual(refused.status_code, 400)


class UploadPolicyTests(ClientPortalTestCase):
    """Clients deliver one ZIP package; staff may upload the full type list."""

    def test_client_can_only_upload_zip(self):
        user, _member = self._member()
        with self.assertRaises(ValueError) as caught:
            DocumentService.upload(
                client=self.client_record,
                upload=self._upload(name='fatura.pdf'),
                uploaded_by=user,
                is_staff=False,
            )
        self.assertIn('.zip', str(caught.exception))

        document, _version = DocumentService.upload(
            client=self.client_record,
            upload=SimpleUploadedFile('documentos.zip', b'PK\x03\x04pacote', content_type='application/zip'),
            uploaded_by=user,
            is_staff=False,
        )
        self.assertEqual(document.category, 'zip')

    def test_staff_may_upload_other_types(self):
        document, _version = DocumentService.upload(
            client=self.client_record,
            upload=self._upload(name='mapa.pdf'),
            uploaded_by=self.staff,
            is_staff=True,
        )
        self.assertEqual(document.category, 'pdf')

    def test_zip_rule_is_enforced_through_the_api(self):
        user, _member = self._member()
        protocol = self._protocol()
        self._authenticate(user)

        refused = self.client.post('/api/client-portal/documents/upload/', {
            'protocol': str(protocol.id),
            'file': self._upload(name='fatura.pdf'),
        }, format='multipart')
        self.assertEqual(refused.status_code, 400)
        self.assertIn('.zip', str(refused.data))

        accepted = self.client.post('/api/client-portal/documents/upload/', {
            'protocol': str(protocol.id),
            'file': SimpleUploadedFile('julho.zip', b'PK\x03\x04pacote', content_type='application/zip'),
        }, format='multipart')
        self.assertEqual(accepted.status_code, 201, accepted.data)

    def test_protocol_uploads_have_no_physical_folder(self):
        # Organisation by protocol is dynamic: the document links to the protocol
        # but no physical folder is auto-created.
        user, _member = self._member()
        protocol = self._protocol()
        document, _version = DocumentService.upload(
            client=self.client_record,
            upload=SimpleUploadedFile('julho.zip', b'PK\x03\x04pacote', content_type='application/zip'),
            protocol=protocol,
            uploaded_by=user,
            is_staff=False,
        )
        self.assertIsNone(document.folder)
        self.assertEqual(document.protocol_id, protocol.id)


class FolderVisibilityTests(ClientPortalTestCase):
    """The filing plan belongs to the office; internal folders never reach clients."""

    def test_staff_folders_are_visible_to_the_client(self):
        user, _member = self._member()
        folder = FolderService.create(
            client=self.client_record, name='Fiscal 2026', created_by=self.staff,
        )
        self._authenticate(user)
        response = self.client.get(f'/api/client-portal/folders/?client={self.client_record.id}')
        self.assertEqual(response.status_code, 200)
        names = {item['name'] for item in response.data['data']['folders']}
        self.assertIn(folder.name, names)

    def test_internal_folders_and_their_documents_are_hidden(self):
        user, _member = self._member()
        internal = FolderService.create(
            client=self.client_record,
            name='Papéis de trabalho',
            visibility=ClientFolder.VISIBILITY_STAFF_ONLY,
            created_by=self.staff,
        )
        document, _version = DocumentService.upload(
            client=self.client_record,
            upload=self._upload(name='rascunho.pdf'),
            folder=internal,
            uploaded_by=self.staff,
        )

        self._authenticate(user)
        folders = self.client.get(f'/api/client-portal/folders/?client={self.client_record.id}')
        self.assertNotIn(internal.name, {item['name'] for item in folders.data['data']['folders']})
        detail = self.client.get(f'/api/client-portal/folders/{internal.id}/')
        self.assertEqual(detail.status_code, 404)
        documents = self.client.get('/api/client-portal/documents/')
        self.assertNotIn(str(document.id), {item['id'] for item in documents.data['data']['documents']})

    def test_subfolder_inherits_internal_visibility(self):
        internal = FolderService.create(
            client=self.client_record,
            name='Interno',
            visibility=ClientFolder.VISIBILITY_STAFF_ONLY,
            created_by=self.staff,
        )
        child = FolderService.create(
            client=self.client_record, name='Notas', parent=internal, created_by=self.staff,
        )
        self.assertEqual(child.visibility, ClientFolder.VISIBILITY_STAFF_ONLY)

    def test_client_cannot_create_folders(self):
        user, _member = self._member()
        self._authenticate(user)
        response = self.client.post('/api/client-portal/folders/', {
            'client': str(self.client_record.id),
            'name': 'Pasta do cliente',
        }, format='json')
        self.assertEqual(response.status_code, 403)
