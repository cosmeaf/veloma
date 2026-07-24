import hashlib
import hmac
import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def hash_token(value: str) -> str:
    """Hash high-entropy opaque tokens without storing their raw value."""
    return hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        value.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


class OTPChallenge(models.Model):
    PURPOSE_REGISTER = 'register'
    PURPOSE_LOGIN = 'login'
    PURPOSE_PASSWORD_RESET = 'password_reset'
    PURPOSE_CHOICES = (
        (PURPOSE_REGISTER, 'Register'),
        (PURPOSE_LOGIN, 'Login'),
        (PURPOSE_PASSWORD_RESET, 'Password reset'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='veloma_otp_challenges')
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES, db_index=True)
    code_hash = models.CharField(max_length=255, editable=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    resend_count = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(blank=True, null=True)
    blocked_at = models.DateTimeField(blank=True, null=True)
    request_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'authentication_otp_challenge'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('user', 'purpose', 'created_at'), name='auth_otp_usr_purp_idx')]

    def __str__(self):
        return f'{self.user.email} · {self.purpose} · {self.status}'

    @property
    def status(self):
        if self.used_at:
            return 'used'
        if self.blocked_at:
            return 'blocked'
        if self.expires_at <= timezone.now():
            return 'expired'
        return 'pending'

    def set_code(self, code: str) -> None:
        self.code_hash = make_password(code)

    def matches(self, code: str) -> bool:
        return check_password(code, self.code_hash)


class PasswordResetGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='veloma_password_reset_grants')
    otp_challenge = models.OneToOneField(OTPChallenge, on_delete=models.PROTECT, related_name='reset_grant')
    token_hash = models.CharField(max_length=64, editable=False, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    request_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'authentication_password_reset_grant'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.email} · {self.status}'

    @property
    def status(self):
        if self.used_at:
            return 'used'
        if self.revoked_at:
            return 'revoked'
        if self.expires_at <= timezone.now():
            return 'expired'
        return 'active'

    def matches(self, token: str) -> bool:
        return hmac.compare_digest(self.token_hash, hash_token(token))


class UserSession(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_REVOKED = 'revoked'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_REVOKED, 'Revoked'),
        (STATUS_EXPIRED, 'Expired'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='veloma_sessions')
    refresh_jti = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    device = models.CharField(max_length=255, blank=True)
    device_fingerprint = models.CharField(max_length=64, blank=True, db_index=True)
    country_code = models.CharField(max_length=8, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    revoke_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'authentication_user_session'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('user', 'status', 'created_at'), name='auth_sess_usr_stat_idx')]

    def __str__(self):
        return f'{self.user.email} · {self.id} · {self.status}'

    def revoke(self, reason='manual'):
        if self.status != self.STATUS_REVOKED:
            self.status = self.STATUS_REVOKED
            self.revoked_at = timezone.now()
            self.revoke_reason = reason
            self.save(update_fields=('status', 'revoked_at', 'revoke_reason'))


class AuthenticationActivity(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_BLOCKED = 'blocked'
    STATUS_CHOICES = (
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_BLOCKED, 'Blocked'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='veloma_auth_activities')
    email = models.EmailField(blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True, db_index=True)
    user_agent = models.TextField(blank=True)
    country_code = models.CharField(max_length=8, blank=True, db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'authentication_activity'
        ordering = ('-created_at',)
        verbose_name_plural = 'Authentication activity'

    def __str__(self):
        return f'{self.event_type} · {self.status} · {self.email or "anonymous"}'


class AccessBlock(models.Model):
    TYPE_USER = 'user'
    TYPE_IP = 'ip'
    TYPE_COUNTRY = 'country'
    TYPE_USER_AGENT = 'user_agent'
    TYPE_CHOICES = (
        (TYPE_USER, 'User'),
        (TYPE_IP, 'IP address'),
        (TYPE_COUNTRY, 'Country'),
        (TYPE_USER_AGENT, 'User agent'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block_type = models.CharField(max_length=16, choices=TYPE_CHOICES, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='veloma_access_blocks')
    value = models.CharField(max_length=512, blank=True, db_index=True)
    reason = models.CharField(max_length=255)
    active = models.BooleanField(default=True, db_index=True)
    automatic = models.BooleanField(default=False)
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'authentication_access_block'
        ordering = ('-created_at',)

    def __str__(self):
        target = self.user.email if self.user_id else self.value
        return f'{self.block_type} · {target}'

    def clean(self):
        errors = {}
        if self.block_type == self.TYPE_USER and not self.user_id:
            errors['user'] = 'A user is required for a user block.'
        if self.block_type != self.TYPE_USER and not self.value.strip():
            errors['value'] = 'A value is required for this block type.'
        if self.block_type == self.TYPE_COUNTRY and self.value:
            self.value = self.value.strip().upper()
        if self.expires_at and self.expires_at <= self.starts_at:
            errors['expires_at'] = 'Expiration must be later than the start time.'
        if errors:
            raise ValidationError(errors)

    @property
    def is_effective(self):
        now = timezone.now()
        return self.active and self.starts_at <= now and (not self.expires_at or self.expires_at > now)


class AccountLifecycle(models.Model):
    """Lifecycle record for a native Django user.

    It never replaces `User`; it only stores when and why an account was
    deactivated or logically deleted, so accounts are never removed physically.
    """

    STATE_ACTIVE = 'active'
    STATE_DEACTIVATED = 'deactivated'
    STATE_ARCHIVED = 'archived'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='veloma_lifecycle')
    deactivated_at = models.DateTimeField(blank=True, null=True, db_index=True)
    deactivated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_deactivated_accounts',
    )
    deactivation_reason = models.CharField(max_length=255, blank=True)
    archived_at = models.DateTimeField(blank=True, null=True, db_index=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='veloma_archived_accounts',
    )
    archive_reason = models.CharField(max_length=255, blank=True)
    last_reactivated_at = models.DateTimeField(blank=True, null=True)
    # Accounts created in bulk share a temporary password: the holder must set
    # their own e-mail and password before doing any work.
    must_change_credentials = models.BooleanField(default=False, db_index=True)
    # Per-user two-factor by email, on top of the global setting.
    two_factor_email_enabled = models.BooleanField(default=False)
    # UI preferences that follow the user across devices.
    theme = models.CharField(max_length=8, choices=(('light', 'Light'), ('dark', 'Dark')), default='light')
    sound_enabled = models.BooleanField(default=True)
    notifications_seen_at = models.DateTimeField(blank=True, null=True)
    notifications_cleared_at = models.DateTimeField(blank=True, null=True)
    credentials_updated_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'authentication_account_lifecycle'
        ordering = ('-updated_at',)
        verbose_name = 'Account lifecycle'
        verbose_name_plural = 'Account lifecycle'

    def __str__(self):
        return f'{self.user.email} · {self.state}'

    @property
    def state(self):
        if self.archived_at:
            return self.STATE_ARCHIVED
        if self.deactivated_at:
            return self.STATE_DEACTIVATED
        return self.STATE_ACTIVE

    @property
    def is_archived(self):
        return bool(self.archived_at)


class ArchivedAccount(User):
    """Admin-only view over logically deleted accounts."""

    class Meta:
        proxy = True
        verbose_name = 'Archived account'
        verbose_name_plural = 'Archived accounts'


class SecurityEvent(models.Model):
    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_CRITICAL = 'critical'
    SEVERITY_CHOICES = (
        (SEVERITY_INFO, 'Info'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_CRITICAL, 'Critical'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='veloma_security_events')
    ip_address = models.GenericIPAddressField(blank=True, null=True, db_index=True)
    summary = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'authentication_security_event'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.severity} · {self.event_type} · {self.summary}'
