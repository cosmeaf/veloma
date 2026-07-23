from django import forms
from django.contrib import messages
from django.contrib.admin import AdminSite, ModelAdmin, SimpleListFilter, action, register
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.utils import timezone

from config.authentication.models import (
    AccessBlock,
    AccountLifecycle,
    ArchivedAccount,
    AuthenticationActivity,
    OTPChallenge,
    PasswordResetGrant,
    SecurityEvent,
    UserSession,
)
from config.authentication.services import AccountLifecycleService, SessionService
from config.common.crypto import CredentialCipher
from config.common.email_service import EmailService
from config.common.dropbox_service import DropboxService
from config.common.models import (
    AuthenticationSettings,
    DocumentSettings,
    DropboxSettings,
    EmailDeliveryLog,
    EmailSettings,
    EmailTemplate,
    EmailVendor,
    SecuritySettings,
)


class VelomaAdminSite(AdminSite):
    site_header = 'Veloma Administration'
    site_title = 'Veloma Admin'
    index_title = 'Administration and debug'

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        authentication_models = []
        configuration_models = []
        client_portal_models = []

        for app in app_list:
            if app['app_label'] in {'auth', 'veloma_authentication'}:
                authentication_models.extend(app['models'])
            elif app['app_label'] == 'veloma_configuration':
                configuration_models.extend(app['models'])
            elif app['app_label'] == 'veloma_client_portal':
                client_portal_models.extend(app['models'])

        result = []
        if authentication_models:
            result.append({
                'name': 'Authentication',
                'app_label': 'authentication',
                'app_url': '',
                'has_module_perms': True,
                'models': sorted(authentication_models, key=lambda item: item['name']),
            })
        if client_portal_models:
            result.append({
                'name': 'Client portal',
                'app_label': 'client_portal',
                'app_url': '',
                'has_module_perms': True,
                'models': sorted(client_portal_models, key=lambda item: item['name']),
            })
        if configuration_models:
            result.append({
                'name': 'Configuration',
                'app_label': 'configuration',
                'app_url': '',
                'has_module_perms': True,
                'models': sorted(configuration_models, key=lambda item: item['name']),
            })
        return result


veloma_admin_site = VelomaAdminSite(name='veloma_admin')
veloma_admin_site.register(Group, GroupAdmin)


STATE_LABELS = {
    AccountLifecycle.STATE_ACTIVE: 'Active',
    AccountLifecycle.STATE_DEACTIVATED: 'Deactivated',
    AccountLifecycle.STATE_ARCHIVED: 'Archived',
}


def account_state(obj):
    lifecycle = getattr(obj, 'veloma_lifecycle', None)
    if lifecycle is None:
        return STATE_LABELS[AccountLifecycle.STATE_ACTIVE if obj.is_active else AccountLifecycle.STATE_DEACTIVATED]
    return STATE_LABELS[lifecycle.state]


account_state.short_description = 'Account state'


def run_lifecycle_action(modeladmin, request, queryset, operation, **kwargs):
    """Applies a lifecycle operation and reports per-account failures."""
    done = 0
    failures = []
    for user in queryset:
        try:
            operation(user=user, performed_by=request.user, request=request, **kwargs)
            done += 1
        except ValueError as exc:
            failures.append(f'{user.username}: {exc}')
    if done:
        modeladmin.message_user(request, f'{done} account(s) processed.')
    for failure in failures:
        modeladmin.message_user(request, failure, level=messages.WARNING)


class LifecycleStateFilter(SimpleListFilter):
    title = 'Account state'
    parameter_name = 'account_state'

    def lookups(self, request, model_admin):
        return (
            (AccountLifecycle.STATE_ACTIVE, 'Active'),
            (AccountLifecycle.STATE_DEACTIVATED, 'Deactivated'),
        )

    def queryset(self, request, queryset):
        if self.value() == AccountLifecycle.STATE_ACTIVE:
            return queryset.filter(is_active=True)
        if self.value() == AccountLifecycle.STATE_DEACTIVATED:
            return queryset.filter(is_active=False)
        return queryset


@register(User, site=veloma_admin_site)
class VelomaUserAdmin(UserAdmin):
    """Native UserAdmin without physical deletion.

    Archived accounts are hidden here and managed through `ArchivedAccount`.
    """

    list_display = UserAdmin.list_display + (account_state,)
    list_filter = UserAdmin.list_filter + (LifecycleStateFilter,)
    actions = ('deactivate_accounts', 'archive_accounts', 'reactivate_accounts')

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('veloma_lifecycle')
            .filter(veloma_lifecycle__archived_at__isnull=True)
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Physical deletion is forbidden by the application.
        actions.pop('delete_selected', None)
        if not request.user.is_superuser:
            actions.pop('reactivate_accounts', None)
        return actions

    def has_delete_permission(self, request, obj=None):
        return False

    def _protected(self, obj):
        from config.authentication.services import _is_protected_admin
        return bool(obj and _is_protected_admin(obj))

    def has_change_permission(self, request, obj=None):
        # The protected administrator can only be edited by itself.
        if self._protected(obj) and obj != request.user:
            return False
        return super().has_change_permission(request, obj)

    @action(description='Desativar contas selecionadas')
    def deactivate_accounts(self, request, queryset):
        run_lifecycle_action(
            self,
            request,
            queryset,
            AccountLifecycleService.deactivate,
            reason='Deactivated from the Django Admin.',
        )

    @action(description='Excluir e arquivar contas selecionadas')
    def archive_accounts(self, request, queryset):
        run_lifecycle_action(
            self,
            request,
            queryset,
            AccountLifecycleService.archive,
            reason='Archived from the Django Admin.',
        )

    @action(description='Reativar contas selecionadas')
    def reactivate_accounts(self, request, queryset):
        run_lifecycle_action(self, request, queryset, AccountLifecycleService.reactivate)


@register(ArchivedAccount, site=veloma_admin_site)
class ArchivedAccountAdmin(ModelAdmin):
    """Read-only list of logically deleted accounts, with restore."""

    list_display = ('username', 'email', 'first_name', 'last_name', 'archived_at', 'archived_by', 'archive_reason')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-veloma_lifecycle__archived_at',)
    actions = ('restore_accounts',)

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('veloma_lifecycle')
            .filter(veloma_lifecycle__archived_at__isnull=False)
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        if not request.user.is_superuser:
            actions.pop('restore_accounts', None)
        return actions

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @staticmethod
    def archived_at(obj):
        return obj.veloma_lifecycle.archived_at

    @staticmethod
    def archived_by(obj):
        return obj.veloma_lifecycle.archived_by

    @staticmethod
    def archive_reason(obj):
        return obj.veloma_lifecycle.archive_reason

    @action(description='Restaurar contas arquivadas')
    def restore_accounts(self, request, queryset):
        run_lifecycle_action(self, request, queryset, AccountLifecycleService.restore)


class ReadOnlyAuditAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)


@register(OTPChallenge, site=veloma_admin_site)
class OTPChallengeAdmin(ReadOnlyAuditAdmin):
    list_display = ('user', 'purpose', 'status_display', 'attempts', 'max_attempts', 'expires_at', 'created_at')
    list_filter = ('purpose', 'used_at', 'blocked_at', 'created_at')
    search_fields = ('user__email', 'request_ip', 'id')
    date_hierarchy = 'created_at'
    exclude = ('code_hash',)

    @staticmethod
    def status_display(obj):
        return obj.status


@register(PasswordResetGrant, site=veloma_admin_site)
class PasswordResetGrantAdmin(ReadOnlyAuditAdmin):
    list_display = ('user', 'status_display', 'expires_at', 'used_at', 'revoked_at', 'created_at')
    list_filter = ('used_at', 'revoked_at', 'created_at')
    search_fields = ('user__email', 'request_ip', 'id')
    exclude = ('token_hash',)

    @staticmethod
    def status_display(obj):
        return obj.status


@register(UserSession, site=veloma_admin_site)
class UserSessionAdmin(ReadOnlyAuditAdmin):
    list_display = ('user', 'status', 'ip_address', 'device', 'country_code', 'last_activity_at', 'expires_at')
    list_filter = ('status', 'country_code', 'created_at')
    search_fields = ('user__email', 'ip_address', 'device', 'id')
    actions = ('revoke_sessions',)
    exclude = ('refresh_jti', 'device_fingerprint')

    def has_change_permission(self, request, obj=None):
        return True

    @staticmethod
    def revoke_sessions(modeladmin, request, queryset):
        count = 0
        for session in queryset.filter(status=UserSession.STATUS_ACTIVE):
            SessionService.revoke(session=session, reason=f'admin:{request.user.pk}')
            count += 1
        modeladmin.message_user(request, f'{count} session(s) revoked.')

    revoke_sessions.short_description = 'Revoke selected active sessions'


@register(AuthenticationActivity, site=veloma_admin_site)
class AuthenticationActivityAdmin(ReadOnlyAuditAdmin):
    list_display = ('event_type', 'status', 'email', 'ip_address', 'country_code', 'reason', 'created_at')
    list_filter = ('event_type', 'status', 'country_code', 'created_at')
    search_fields = ('email', 'user__email', 'ip_address', 'reason')
    date_hierarchy = 'created_at'


@register(AccessBlock, site=veloma_admin_site)
class AccessBlockAdmin(ModelAdmin):
    list_display = ('block_type', 'target', 'active', 'automatic', 'starts_at', 'expires_at', 'reason')
    list_filter = ('block_type', 'active', 'automatic')
    search_fields = ('user__email', 'value', 'reason')
    readonly_fields = ('id', 'automatic', 'created_at', 'updated_at')
    actions = ('activate_blocks', 'deactivate_blocks')

    @staticmethod
    def target(obj):
        return obj.user.email if obj.user_id else obj.value

    @staticmethod
    def activate_blocks(modeladmin, request, queryset):
        count = queryset.update(active=True)
        modeladmin.message_user(request, f'{count} block(s) activated.')

    @staticmethod
    def deactivate_blocks(modeladmin, request, queryset):
        count = queryset.update(active=False)
        modeladmin.message_user(request, f'{count} block(s) deactivated.')

    activate_blocks.short_description = 'Activate selected blocks'
    deactivate_blocks.short_description = 'Deactivate selected blocks'


@register(SecurityEvent, site=veloma_admin_site)
class SecurityEventAdmin(ReadOnlyAuditAdmin):
    list_display = ('severity', 'event_type', 'summary', 'user', 'ip_address', 'resolved', 'created_at')
    list_filter = ('severity', 'event_type', 'resolved', 'created_at')
    search_fields = ('summary', 'user__email', 'ip_address')
    actions = ('mark_resolved',)

    def has_change_permission(self, request, obj=None):
        return True

    @staticmethod
    def mark_resolved(modeladmin, request, queryset):
        count = queryset.update(resolved=True, resolved_at=timezone.now())
        modeladmin.message_user(request, f'{count} event(s) marked as resolved.')

    mark_resolved.short_description = 'Mark selected events as resolved'


class SingletonAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@register(AuthenticationSettings, site=veloma_admin_site)
class AuthenticationSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Access', {
            'fields': (
                'registration_enabled',
                'email_verification_required',
                'login_otp_enabled',
                'default_frontend_group',
                'deny_django_admin_api_login',
            ),
        }),
        ('OTP', {
            'fields': (
                'otp_length',
                'otp_expiration_minutes',
                'otp_max_attempts',
                'otp_resend_cooldown_seconds',
                'otp_max_resends',
            ),
        }),
        ('Passwords', {
            'fields': (
                'password_reset_expiration_minutes',
                'revoke_sessions_after_password_reset',
                'revoke_sessions_after_password_change',
            ),
        }),
    )
    readonly_fields = ('updated_at',)


class SecuritySettingsAdminForm(forms.ModelForm):
    ip_intelligence_token = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text='Leave empty to keep the current token.',
    )

    class Meta:
        model = SecuritySettings
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        token = self.cleaned_data.get('ip_intelligence_token')
        if token:
            instance.encrypted_ip_intelligence_token = CredentialCipher.encrypt(token)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@register(SecuritySettings, site=veloma_admin_site)
class SecuritySettingsAdmin(SingletonAdmin):
    form = SecuritySettingsAdminForm
    fieldsets = (
        ('Authentication protection', {
            'fields': (
                'login_max_attempts',
                'login_window_minutes',
                'automatic_block_minutes',
                'block_user_on_failed_login',
                'block_ip_on_failed_login',
                'max_active_sessions',
                'session_activity_touch_seconds',
            ),
        }),
        ('API rate limits', {
            'fields': (
                'api_rate_limit_enabled',
                'api_rate_limit_requests',
                'api_rate_limit_window_seconds',
                'auth_rate_limit_requests',
                'auth_rate_limit_window_seconds',
            ),
        }),
        ('IP Intelligence and countries', {
            'fields': (
                'ip_intelligence_enabled',
                'ip_intelligence_url',
                'ip_intelligence_token',
                'ip_intelligence_timeout_seconds',
                'block_unknown_countries',
                'allowed_country_codes',
            ),
        }),
        ('Security notifications', {
            'fields': ('notify_new_device', 'notify_new_ip', 'notify_new_country'),
        }),
        ('Retention', {
            'fields': (
                'authentication_record_retention_days',
                'audit_log_retention_days',
                'email_log_retention_days',
            ),
        }),
    )
    readonly_fields = ('updated_at',)


@register(DocumentSettings, site=veloma_admin_site)
class DocumentSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Uploads', {
            'fields': (
                'allowed_extensions',
                'max_file_size_mb',
                'max_files_per_protocol',
                'allow_zip',
            ),
        }),
        ('Antivirus', {
            'fields': (
                'require_antivirus',
                'antivirus_host',
                'antivirus_port',
                'antivirus_timeout_seconds',
                'quarantine_retention_days',
            ),
        }),
        ('Downloads', {'fields': ('signed_url_seconds',)}),
        ('Invitations', {
            'fields': (
                'invitation_expiration_days',
                'invitation_reminder_days',
                'invitation_max_resends',
            ),
        }),
        ('Protocols', {'fields': ('overdue_alert_enabled',)}),
    )
    readonly_fields = ('updated_at',)


@register(EmailSettings, site=veloma_admin_site)
class EmailSettingsAdmin(SingletonAdmin):
    fields = (
        'default_delivery_mode',
        'auto_sync_fallback',
        'max_retries',
        'retry_backoff_seconds',
        'updated_at',
    )
    readonly_fields = ('updated_at',)


class EmailVendorAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text='Leave empty to keep the current password.',
    )

    class Meta:
        model = EmailVendor
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            instance.encrypted_password = CredentialCipher.encrypt(password)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@register(EmailVendor, site=veloma_admin_site)
class EmailVendorAdmin(ModelAdmin):
    form = EmailVendorAdminForm
    list_display = ('name', 'vendor_type', 'host', 'from_email', 'active', 'is_default', 'is_fallback', 'priority')
    list_filter = ('vendor_type', 'active', 'is_default', 'is_fallback')
    search_fields = ('name', 'host', 'username', 'from_email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('send_test_email',)

    @staticmethod
    def send_test_email(modeladmin, request, queryset):
        if not request.user.email:
            modeladmin.message_user(
                request,
                'The administrator account has no email address.',
                level=messages.ERROR,
            )
            return
        sent = 0
        failed = 0
        for vendor in queryset:
            try:
                EmailService.send(
                    recipients=[request.user.email],
                    subject='Veloma email vendor test: {{ vendor_name }}',
                    html_template='emails/security_alert.html',
                    text_template='emails/security_alert.txt',
                    context={
                        'user': {'first_name': request.user.first_name or request.user.username},
                        'message': f'Test message sent through {vendor.name}.',
                        'vendor_name': vendor.name,
                    },
                    purpose='vendor_test',
                    mode='sync',
                    vendor_id=vendor.pk,
                )
                sent += 1
            except Exception:
                failed += 1
        modeladmin.message_user(request, f'Test completed. Sent: {sent}. Failed: {failed}.')

    send_test_email.short_description = 'Send test email through selected vendors'


class DropboxSettingsAdminForm(forms.ModelForm):
    app_secret = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text='Leave empty to keep the current app secret.',
    )
    refresh_token = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text='Leave empty to keep the current refresh token.',
    )

    class Meta:
        model = DropboxSettings
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        app_secret = self.cleaned_data.get('app_secret')
        if app_secret:
            instance.encrypted_app_secret = CredentialCipher.encrypt(app_secret)
        refresh_token = self.cleaned_data.get('refresh_token')
        if refresh_token:
            instance.encrypted_refresh_token = CredentialCipher.encrypt(refresh_token)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@register(DropboxSettings, site=veloma_admin_site)
class DropboxSettingsAdmin(SingletonAdmin):
    form = DropboxSettingsAdminForm
    fieldsets = (
        ('Credenciais', {
            'description': 'App Dropbox com acesso Full Dropbox (escreve nos dois caminhos). '
            'Os segredos são cifrados e nunca são mostrados de volta.',
            'fields': ('enabled', 'app_key', 'app_secret', 'refresh_token', 'timeout_seconds'),
        }),
        ('Uploads aprovados', {
            'fields': ('mirror_uploads', 'uploads_path'),
        }),
        ('Arquivo RGPD (10 anos)', {
            'fields': ('mirror_rgpd', 'rgpd_path'),
        }),
    )
    readonly_fields = ('updated_at',)
    actions = ('test_connection',)

    @staticmethod
    def test_connection(modeladmin, request, queryset):
        ok, message = DropboxService.check_connection()
        modeladmin.message_user(
            request,
            message,
            level=messages.SUCCESS if ok else messages.ERROR,
        )

    test_connection.short_description = 'Testar ligação ao Dropbox'


@register(EmailTemplate, site=veloma_admin_site)
class EmailTemplateAdmin(ModelAdmin):
    list_display = ('purpose', 'subject', 'delivery_mode', 'vendor', 'active', 'updated_at')
    list_filter = ('delivery_mode', 'active', 'vendor')
    search_fields = ('purpose', 'subject', 'html_template', 'text_template')
    readonly_fields = ('created_at', 'updated_at')


@register(EmailDeliveryLog, site=veloma_admin_site)
class EmailDeliveryLogAdmin(ReadOnlyAuditAdmin):
    list_display = ('purpose', 'subject', 'status', 'vendor', 'delivery_mode', 'attempts', 'created_at', 'sent_at')
    list_filter = ('status', 'delivery_mode', 'vendor', 'created_at')
    search_fields = ('purpose', 'subject', 'recipients', 'error', 'task_id')
