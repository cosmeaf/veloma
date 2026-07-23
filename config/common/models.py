from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.template.loader import get_template


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def _cache_key(cls):
        return f'veloma:configuration:{cls._meta.label_lower}'

    def save(self, *args, **kwargs):
        self.pk = 1
        result = super().save(*args, **kwargs)
        cache.delete(type(self)._cache_key())
        return result

    def delete(self, *args, **kwargs):
        cache.delete(type(self)._cache_key())
        return super().delete(*args, **kwargs)

    @classmethod
    def load(cls):
        key = cls._cache_key()
        obj = cache.get(key)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(key, obj, timeout=30)
        return obj


class AuthenticationSettings(SingletonModel):
    registration_enabled = models.BooleanField(default=True)
    email_verification_required = models.BooleanField(default=True)
    login_otp_enabled = models.BooleanField(default=False)
    default_frontend_group = models.CharField(max_length=80, default='USER')
    deny_django_admin_api_login = models.BooleanField(default=True)
    otp_length = models.PositiveSmallIntegerField(default=6)
    otp_expiration_minutes = models.PositiveSmallIntegerField(default=5)
    otp_max_attempts = models.PositiveSmallIntegerField(default=5)
    otp_resend_cooldown_seconds = models.PositiveIntegerField(default=60)
    otp_max_resends = models.PositiveSmallIntegerField(default=3)
    password_reset_expiration_minutes = models.PositiveSmallIntegerField(default=10)
    revoke_sessions_after_password_reset = models.BooleanField(default=True)
    revoke_sessions_after_password_change = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Authentication settings'
        verbose_name_plural = 'Authentication settings'

    def __str__(self):
        return 'Authentication settings'

    def clean(self):
        errors = {}
        if not 6 <= self.otp_length <= 8:
            errors['otp_length'] = 'OTP length must be between 6 and 8 digits.'
        for field in (
            'otp_expiration_minutes',
            'otp_max_attempts',
            'otp_resend_cooldown_seconds',
            'otp_max_resends',
            'password_reset_expiration_minutes',
        ):
            if getattr(self, field) < 1:
                errors[field] = 'Value must be at least 1.'
        if errors:
            raise ValidationError(errors)


class SecuritySettings(SingletonModel):
    login_max_attempts = models.PositiveSmallIntegerField(default=5)
    login_window_minutes = models.PositiveSmallIntegerField(default=15)
    automatic_block_minutes = models.PositiveIntegerField(default=30)
    block_user_on_failed_login = models.BooleanField(default=True)
    block_ip_on_failed_login = models.BooleanField(default=True)
    max_active_sessions = models.PositiveSmallIntegerField(default=3)
    session_activity_touch_seconds = models.PositiveIntegerField(default=60)
    api_rate_limit_enabled = models.BooleanField(default=True)
    api_rate_limit_requests = models.PositiveIntegerField(default=120)
    api_rate_limit_window_seconds = models.PositiveIntegerField(default=60)
    auth_rate_limit_requests = models.PositiveIntegerField(default=30)
    auth_rate_limit_window_seconds = models.PositiveIntegerField(default=60)
    ip_intelligence_enabled = models.BooleanField(default=False)
    ip_intelligence_url = models.CharField(max_length=500, blank=True, help_text='Endpoint template. Use {ip} where the client IP must be inserted.')
    encrypted_ip_intelligence_token = models.TextField(blank=True, editable=False)
    ip_intelligence_timeout_seconds = models.PositiveSmallIntegerField(default=3)
    block_unknown_countries = models.BooleanField(default=False)
    allowed_country_codes = models.CharField(max_length=512, blank=True, help_text='Comma-separated ISO country codes.')
    notify_new_device = models.BooleanField(default=True)
    notify_new_ip = models.BooleanField(default=False)
    notify_new_country = models.BooleanField(default=True)
    authentication_record_retention_days = models.PositiveIntegerField(default=30)
    audit_log_retention_days = models.PositiveIntegerField(default=180)
    email_log_retention_days = models.PositiveIntegerField(default=90)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Security settings'
        verbose_name_plural = 'Security settings'

    def __str__(self):
        return 'Security settings'

    def clean(self):
        errors = {}
        numeric_fields = (
            'login_max_attempts',
            'login_window_minutes',
            'automatic_block_minutes',
            'max_active_sessions',
            'session_activity_touch_seconds',
            'api_rate_limit_requests',
            'api_rate_limit_window_seconds',
            'auth_rate_limit_requests',
            'auth_rate_limit_window_seconds',
            'ip_intelligence_timeout_seconds',
            'authentication_record_retention_days',
            'audit_log_retention_days',
            'email_log_retention_days',
        )
        for field in numeric_fields:
            if getattr(self, field) < 1:
                errors[field] = 'Value must be at least 1.'
        codes = [item.strip().upper() for item in self.allowed_country_codes.split(',') if item.strip()]
        invalid = [item for item in codes if len(item) not in {2, 3} or not item.isalpha()]
        if invalid:
            errors['allowed_country_codes'] = f'Invalid country codes: {", ".join(invalid)}.'
        self.allowed_country_codes = ','.join(dict.fromkeys(codes))
        if errors:
            raise ValidationError(errors)


class DocumentSettings(SingletonModel):
    """Upload, storage and antivirus policy for the client portal."""

    allowed_extensions = models.CharField(
        max_length=512,
        default='pdf,xml,csv,xls,xlsx,doc,docx,jpg,jpeg,png,zip',
        help_text='Comma-separated extensions, without dots. Applies to staff uploads.',
    )
    client_allowed_extensions = models.CharField(
        max_length=512,
        default='zip',
        help_text='Extensions clients may upload. Defaults to ZIP only, so each delivery arrives as one package.',
    )
    max_file_size_mb = models.PositiveIntegerField(default=25)
    max_files_per_protocol = models.PositiveIntegerField(default=200)
    allow_zip = models.BooleanField(default=True)
    require_antivirus = models.BooleanField(
        default=False,
        help_text='When enabled, a scanner failure keeps the file in quarantine.',
    )
    antivirus_host = models.CharField(max_length=180, blank=True, default='veloma-clamav')
    antivirus_port = models.PositiveIntegerField(default=3310)
    antivirus_timeout_seconds = models.PositiveSmallIntegerField(default=30)
    signed_url_seconds = models.PositiveIntegerField(default=300)
    quarantine_retention_days = models.PositiveIntegerField(default=30)
    invitation_expiration_days = models.PositiveSmallIntegerField(default=7)
    invitation_reminder_days = models.PositiveSmallIntegerField(default=3)
    invitation_max_resends = models.PositiveSmallIntegerField(default=5)
    overdue_alert_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document settings'
        verbose_name_plural = 'Document settings'

    def __str__(self):
        return 'Document settings'

    @staticmethod
    def _parse_extensions(value):
        return {item.strip().lower().lstrip('.') for item in value.split(',') if item.strip()}

    @property
    def extension_set(self):
        return self._parse_extensions(self.allowed_extensions)

    @property
    def client_extension_set(self):
        return self._parse_extensions(self.client_allowed_extensions)

    def extensions_for(self, *, is_staff):
        """Clients are restricted to their own list; staff use the full one."""
        return self.extension_set if is_staff else self.client_extension_set

    @property
    def max_file_size_bytes(self):
        return self.max_file_size_mb * 1024 * 1024

    def clean(self):
        errors = {}
        for field in (
            'max_file_size_mb',
            'max_files_per_protocol',
            'signed_url_seconds',
            'quarantine_retention_days',
            'invitation_expiration_days',
        ):
            if getattr(self, field) < 1:
                errors[field] = 'Value must be at least 1.'
        for field in ('allowed_extensions', 'client_allowed_extensions'):
            extensions = [
                item.strip().lower().lstrip('.')
                for item in getattr(self, field).split(',')
                if item.strip()
            ]
            invalid = [item for item in extensions if not item.isalnum()]
            if invalid:
                errors[field] = f'Invalid extensions: {", ".join(invalid)}.'
            if not extensions:
                errors[field] = 'At least one extension is required.'
            setattr(self, field, ','.join(dict.fromkeys(extensions)))
        if self.require_antivirus and not self.antivirus_host:
            errors['antivirus_host'] = 'An antivirus host is required when the scan is mandatory.'
        if errors:
            raise ValidationError(errors)


class EmailSettings(SingletonModel):
    default_delivery_mode = models.CharField(
        max_length=10,
        choices=(('sync', 'Sync'), ('async', 'Async'), ('auto', 'Auto')),
        default='auto',
    )
    auto_sync_fallback = models.BooleanField(default=True)
    max_retries = models.PositiveSmallIntegerField(default=3)
    retry_backoff_seconds = models.PositiveIntegerField(default=30)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email settings'
        verbose_name_plural = 'Email settings'

    def __str__(self):
        return 'Email settings'

    def clean(self):
        errors = {}
        if self.max_retries < 0:
            errors['max_retries'] = 'Value cannot be negative.'
        if self.retry_backoff_seconds < 1:
            errors['retry_backoff_seconds'] = 'Value must be at least 1.'
        if errors:
            raise ValidationError(errors)


class EmailVendor(models.Model):
    TYPE_SMTP = 'smtp'
    TYPE_CONSOLE = 'console'
    TYPE_CHOICES = (
        (TYPE_SMTP, 'SMTP'),
        (TYPE_CONSOLE, 'Development console'),
    )

    name = models.CharField(max_length=120, unique=True)
    vendor_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SMTP)
    host = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(default=587)
    username = models.CharField(max_length=255, blank=True)
    encrypted_password = models.TextField(blank=True, editable=False)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    from_email = models.EmailField(blank=True)
    from_name = models.CharField(max_length=120, blank=True)
    reply_to = models.EmailField(blank=True)
    timeout_seconds = models.PositiveSmallIntegerField(default=30)
    priority = models.PositiveSmallIntegerField(default=100)
    active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False)
    is_fallback = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('priority', 'name')
        verbose_name = 'Email vendor'
        verbose_name_plural = 'Email vendors'
        constraints = [
            models.UniqueConstraint(
                fields=('is_default',),
                condition=Q(is_default=True),
                name='single_default_email_vendor',
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}
        if self.use_tls and self.use_ssl:
            errors['use_ssl'] = 'TLS and SSL cannot both be enabled.'
        if self.vendor_type == self.TYPE_SMTP:
            if not self.host:
                errors['host'] = 'SMTP host is required.'
            if not self.from_email:
                errors['from_email'] = 'Sender email is required.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.is_default:
            type(self).objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class EmailTemplate(models.Model):
    MODE_SYNC = 'sync'
    MODE_ASYNC = 'async'
    MODE_AUTO = 'auto'
    MODE_CHOICES = ((MODE_SYNC, 'Sync'), (MODE_ASYNC, 'Async'), (MODE_AUTO, 'Auto'))

    purpose = models.SlugField(max_length=100, unique=True)
    subject = models.CharField(max_length=255)
    html_template = models.CharField(max_length=255)
    text_template = models.CharField(max_length=255)
    delivery_mode = models.CharField(max_length=10, choices=MODE_CHOICES, default=MODE_AUTO)
    vendor = models.ForeignKey(EmailVendor, on_delete=models.SET_NULL, blank=True, null=True, related_name='templates')
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('purpose',)
        verbose_name = 'Email template'
        verbose_name_plural = 'Email templates'

    def __str__(self):
        return self.purpose

    def clean(self):
        errors = {}
        for field_name in ('html_template', 'text_template'):
            value = getattr(self, field_name)
            if not value:
                continue
            try:
                get_template(value)
            except Exception:
                errors[field_name] = f'Template not found: {value}'
        if errors:
            raise ValidationError(errors)


class EmailDeliveryLog(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = ((STATUS_QUEUED, 'Queued'), (STATUS_SENT, 'Sent'), (STATUS_FAILED, 'Failed'))

    purpose = models.CharField(max_length=100, blank=True, db_index=True)
    recipients = models.JSONField(default=list)
    subject = models.CharField(max_length=255)
    vendor = models.ForeignKey(EmailVendor, on_delete=models.SET_NULL, blank=True, null=True)
    delivery_mode = models.CharField(max_length=10)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, db_index=True)
    task_id = models.CharField(max_length=255, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Email delivery log'
        verbose_name_plural = 'Email delivery logs'

    def __str__(self):
        return f'{self.subject} · {self.status}'


class DropboxSettings(SingletonModel):
    """Company Dropbox integration, edited in the Admin (never in settings.py).

    Mirrors two destinations: approved document uploads and the 10-year RGPD
    consent-proof archive. Credentials are Fernet-encrypted like SMTP passwords
    and never rendered back into the form. A Full-Dropbox-scoped app is required
    to write both base paths.
    """

    enabled = models.BooleanField(default=False)
    app_key = models.CharField(max_length=255, blank=True)
    encrypted_app_secret = models.TextField(blank=True, editable=False)
    encrypted_refresh_token = models.TextField(blank=True, editable=False)

    # Dropbox Business (team) apps need a member to act as. When is_team is on and
    # team_member_id is blank, the authenticated team admin is used automatically.
    is_team = models.BooleanField(default=False, help_text='Dropbox Business (team) app.')
    team_member_id = models.CharField(max_length=128, blank=True, help_text='Optional; defaults to the team admin.')

    mirror_uploads = models.BooleanField(default=True)
    uploads_path = models.CharField(max_length=255, default='/Apps/veloma_upload')
    mirror_rgpd = models.BooleanField(default=True)
    rgpd_path = models.CharField(max_length=255, default='/Apps/rgpd')

    timeout_seconds = models.PositiveSmallIntegerField(default=30)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dropbox settings'
        verbose_name_plural = 'Dropbox settings'

    def __str__(self):
        return 'Dropbox settings'

    def app_secret(self):
        from config.common.crypto import CredentialCipher

        return CredentialCipher.decrypt(self.encrypted_app_secret) if self.encrypted_app_secret else ''

    def refresh_token(self):
        from config.common.crypto import CredentialCipher

        return CredentialCipher.decrypt(self.encrypted_refresh_token) if self.encrypted_refresh_token else ''

    def is_configured(self):
        return bool(self.enabled and self.app_key and self.encrypted_app_secret and self.encrypted_refresh_token)
