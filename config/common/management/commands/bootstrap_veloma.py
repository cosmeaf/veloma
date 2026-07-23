import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from config.common.models import (
    AuthenticationSettings,
    DocumentSettings,
    EmailSettings,
    EmailTemplate,
    EmailVendor,
    SecuritySettings,
)


TEMPLATES = {
    'register': ('Registo recebido', 'emails/register.html', 'emails/register.txt'),
    'register_otp': ('Confirme o seu registo', 'emails/register_otp.html', 'emails/register_otp.txt'),
    'login_otp': ('Confirme o seu acesso', 'emails/login_otp.html', 'emails/login_otp.txt'),
    'password_recovery': ('Recuperação de palavra-passe', 'emails/password_recovery.html', 'emails/password_recovery.txt'),
    'password_reset': ('Defina a sua nova palavra-passe', 'emails/password_reset.html', 'emails/password_reset.txt'),
    'password_changed': ('Palavra-passe alterada', 'emails/password_changed.html', 'emails/password_changed.txt'),
    'email_changed': ('Endereço de e-mail alterado', 'emails/email_changed.html', 'emails/email_changed.txt'),
    'account_activated': ('Conta ativada', 'emails/account_activated.html', 'emails/account_activated.txt'),
    'account_deactivated': ('Conta desativada', 'emails/account_deactivated.html', 'emails/account_deactivated.txt'),
    'account_blocked': ('Conta bloqueada', 'emails/account_blocked.html', 'emails/account_blocked.txt'),
    'account_unblocked': ('Conta desbloqueada', 'emails/account_unblocked.html', 'emails/account_unblocked.txt'),
    'login_success': ('Novo acesso realizado', 'emails/login_success.html', 'emails/login_success.txt'),
    'login_failed': ('Tentativa de acesso falhada', 'emails/login_failed.html', 'emails/login_failed.txt'),
    'login_attempt_limit': ('Limite de tentativas atingido', 'emails/login_attempt_limit.html', 'emails/login_attempt_limit.txt'),
    'brute_force_detected': ('Tentativas abusivas detetadas', 'emails/brute_force_detected.html', 'emails/brute_force_detected.txt'),
    'suspicious_login': ('Acesso suspeito detetado', 'emails/suspicious_login.html', 'emails/suspicious_login.txt'),
    'new_ip_access': ('Acesso por novo endereço IP', 'emails/new_ip_access.html', 'emails/new_ip_access.txt'),
    'blocked_ip_access': ('Acesso bloqueado por IP', 'emails/blocked_ip_access.html', 'emails/blocked_ip_access.txt'),
    'new_country_access': ('Acesso por novo país', 'emails/new_country_access.html', 'emails/new_country_access.txt'),
    'blocked_country_access': ('Acesso bloqueado por país', 'emails/blocked_country_access.html', 'emails/blocked_country_access.txt'),
    'new_device': ('Novo dispositivo detetado', 'emails/new_device.html', 'emails/new_device.txt'),
    'unknown_device': ('Dispositivo desconhecido', 'emails/unknown_device.html', 'emails/unknown_device.txt'),
    'blocked_user_agent': ('Acesso bloqueado por user-agent', 'emails/blocked_user_agent.html', 'emails/blocked_user_agent.txt'),
    'session_created': ('Nova sessão criada', 'emails/session_created.html', 'emails/session_created.txt'),
    'session_expired': ('Sessão expirada', 'emails/session_expired.html', 'emails/session_expired.txt'),
    'session_revoked': ('Sessão revogada', 'emails/session_revoked.html', 'emails/session_revoked.txt'),
    'multiple_sessions': ('Múltiplas sessões detetadas', 'emails/multiple_sessions.html', 'emails/multiple_sessions.txt'),
    'all_sessions_revoked': ('Todas as sessões foram revogadas', 'emails/all_sessions_revoked.html', 'emails/all_sessions_revoked.txt'),
    'token_expired': ('Token expirado', 'emails/token_expired.html', 'emails/token_expired.txt'),
    'token_revoked': ('Token revogado', 'emails/token_revoked.html', 'emails/token_revoked.txt'),
    'security_alert': ('Alerta de segurança', 'emails/security_alert.html', 'emails/security_alert.txt'),
    'rate_limit_reached': ('Limite de pedidos atingido', 'emails/rate_limit_reached.html', 'emails/rate_limit_reached.txt'),
    'admin_password_reset': ('Recuperação de acesso ao Admin', 'emails/admin_password_reset.html', 'emails/admin_password_reset.txt'),
    # Client portal
    'client_invitation': ('Convite de acesso à Veloma', 'emails/client_invitation.html', 'emails/client_invitation.txt'),
    'client_invitation_reminder': ('O seu convite está a expirar', 'emails/client_invitation_reminder.html', 'emails/client_invitation_reminder.txt'),
    'client_invitation_accepted': ('Conta criada com sucesso', 'emails/client_invitation_accepted.html', 'emails/client_invitation_accepted.txt'),
    'client_account_deactivated': ('Acesso suspenso', 'emails/client_account_deactivated.html', 'emails/client_account_deactivated.txt'),
    'client_account_archived': ('Conta encerrada', 'emails/client_account_archived.html', 'emails/client_account_archived.txt'),
    'client_account_restored': ('Acesso reativado', 'emails/client_account_restored.html', 'emails/client_account_restored.txt'),
    'protocol_created': ('Novo protocolo {{ protocol.number }}', 'emails/protocol_created.html', 'emails/protocol_created.txt'),
    'protocol_status_changed': ('Protocolo {{ protocol.number }} atualizado', 'emails/protocol_status_changed.html', 'emails/protocol_status_changed.txt'),
    'documents_requested': ('Documentos solicitados no protocolo {{ protocol.number }}', 'emails/documents_requested.html', 'emails/documents_requested.txt'),
    'document_uploaded': ('Documento recebido', 'emails/document_uploaded.html', 'emails/document_uploaded.txt'),
    'document_available': ('Documento disponível', 'emails/document_available.html', 'emails/document_available.txt'),
    'document_rejected': ('Documento rejeitado', 'emails/document_rejected.html', 'emails/document_rejected.txt'),
    'staff_public_comment': ('Nova mensagem no protocolo {{ protocol.number }}', 'emails/staff_public_comment.html', 'emails/staff_public_comment.txt'),
    'client_public_comment': ('Nova mensagem do cliente', 'emails/client_public_comment.html', 'emails/client_public_comment.txt'),
    'client_action_required': ('Ação necessária no protocolo {{ protocol.number }}', 'emails/client_action_required.html', 'emails/client_action_required.txt'),
    'protocol_completed': ('Protocolo {{ protocol.number }} concluído', 'emails/protocol_completed.html', 'emails/protocol_completed.txt'),
    'protocol_reopened': ('Protocolo {{ protocol.number }} reaberto', 'emails/protocol_reopened.html', 'emails/protocol_reopened.txt'),
}


class Command(BaseCommand):
    help = 'Creates native groups, default configuration, templates and the optional development administrator.'

    def handle(self, *args, **options):
        for name in ('STAFF_MANAGER', 'STAFF', 'USER'):
            Group.objects.get_or_create(name=name)

        auth_settings, auth_created = AuthenticationSettings.objects.get_or_create(pk=1)
        if auth_created:
            # The client portal only creates accounts through invitations.
            auth_settings.registration_enabled = False
            auth_settings.save(update_fields=('registration_enabled',))
        SecuritySettings.load()
        EmailSettings.load()
        DocumentSettings.load()

        # Seed a console vendor ONLY on a truly fresh install (no vendors at all).
        # Once any vendor exists — e.g. a real SMTP configured in the Admin — a
        # redeploy must never create, reactivate or re-default a vendor. This is
        # what previously stole the default away from the office's SMTP.
        if not EmailVendor.objects.exists():
            EmailVendor.objects.create(
                name='Development console',
                vendor_type=EmailVendor.TYPE_CONSOLE,
                from_email='no-reply@veloma.local',
                active=True,
                is_default=True,
                priority=1,
                use_tls=False,
                use_ssl=False,
            )

        for purpose, (subject, html, text) in TEMPLATES.items():
            EmailTemplate.objects.get_or_create(
                purpose=purpose,
                defaults={
                    'subject': subject,
                    'html_template': html,
                    'text_template': text,
                    'delivery_mode': EmailTemplate.MODE_AUTO,
                },
            )

        username = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip().lower()
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', username).strip().lower()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
        if username and password and not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Development administrator created: {username}'))

        self.stdout.write(self.style.SUCCESS('Veloma core configuration created.'))
