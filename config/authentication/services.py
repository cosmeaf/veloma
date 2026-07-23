import secrets
from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from config.common.models import AuthenticationSettings, SecuritySettings
from config.security.request import RequestContext
from .models import AccountLifecycle, OTPChallenge, PasswordResetGrant, UserSession, hash_token

import logging

logger = logging.getLogger('config.authentication.services')


class UserPresenter:
    @staticmethod
    def build(user):
        roles = list(user.groups.order_by('name').values_list('name', flat=True))
        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'last_login': user.last_login,
            'roles': roles,
            'status': 'active' if user.is_active else 'inactive',
            'is_active': user.is_active,
            'is_admin': bool(user.is_staff or user.is_superuser),
            'is_platform_staff': 'STAFF' in roles and not user.is_staff,
            'must_change_credentials': AccountLifecycle.objects.filter(
                user=user, must_change_credentials=True,
            ).exists(),
            'two_factor_email': AccountLifecycle.objects.filter(
                user=user, two_factor_email_enabled=True,
            ).exists(),
            'preferences': UserPresenter._preferences(user),
        }

    @staticmethod
    def _preferences(user):
        record = AccountLifecycle.objects.filter(user=user).first()
        return {
            'theme': record.theme if record else 'light',
            'sound_enabled': record.sound_enabled if record else True,
        }


class UserService:
    @staticmethod
    @transaction.atomic
    def register(*, first_name, last_name, email, password):
        auth_settings = AuthenticationSettings.load()
        if not auth_settings.registration_enabled:
            raise ValueError('Registration is disabled.')
        email = email.strip().lower()
        is_active = not auth_settings.email_verification_required
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                password=password,
                is_active=is_active,
            )
        except IntegrityError as exc:
            raise ValueError('Email is already registered.') from exc
        group, _ = Group.objects.get_or_create(name=auth_settings.default_frontend_group)
        user.groups.add(group)
        return user

    @staticmethod
    @transaction.atomic
    def change_password(*, user, current_password, new_password):
        if not user.check_password(current_password):
            raise ValueError('Current password is invalid.')
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            raise ValueError(' '.join(exc.messages)) from exc
        user.set_password(new_password)
        user.save(update_fields=('password',))
        if AuthenticationSettings.load().revoke_sessions_after_password_change:
            SessionService.revoke_all(user=user, reason='password_changed')
        return user


class OTPService:
    @staticmethod
    def _code(length):
        maximum = 10 ** length
        return f'{secrets.randbelow(maximum):0{length}d}'

    @classmethod
    @transaction.atomic
    def create(cls, *, user, purpose, request=None):
        auth_settings = AuthenticationSettings.load()
        now = timezone.now()
        OTPChallenge.objects.filter(
            user=user,
            purpose=purpose,
            used_at__isnull=True,
            blocked_at__isnull=True,
            expires_at__gt=now,
        ).update(expires_at=now)
        code = cls._code(auth_settings.otp_length)
        challenge = OTPChallenge(
            user=user,
            purpose=purpose,
            max_attempts=auth_settings.otp_max_attempts,
            expires_at=now + timedelta(minutes=auth_settings.otp_expiration_minutes),
            request_ip=RequestContext.ip(request),
            user_agent=RequestContext.user_agent(request),
        )
        challenge.set_code(code)
        challenge.save()
        return challenge, code

    @staticmethod
    @transaction.atomic
    def verify(*, challenge_id, code, purpose=None):
        challenge = (
            OTPChallenge.objects.select_for_update()
            .select_related('user')
            .filter(pk=challenge_id)
            .first()
        )
        if not challenge:
            raise ValueError('Invalid OTP challenge.')
        if purpose and challenge.purpose != purpose:
            raise ValueError('Invalid OTP purpose.')
        if challenge.used_at:
            raise ValueError('OTP has already been used.')
        if challenge.blocked_at:
            raise ValueError('OTP is blocked.')
        if challenge.expires_at <= timezone.now():
            raise ValueError('OTP has expired.')

        challenge.attempts += 1
        if not challenge.matches(str(code).strip()):
            if challenge.attempts >= challenge.max_attempts:
                challenge.blocked_at = timezone.now()
            challenge.save(update_fields=('attempts', 'blocked_at'))
            raise ValueError('Invalid OTP.')

        challenge.used_at = timezone.now()
        challenge.save(update_fields=('attempts', 'used_at'))
        return challenge


class PasswordResetService:
    @staticmethod
    @transaction.atomic
    def create_grant(*, challenge, request=None):
        if challenge.purpose != OTPChallenge.PURPOSE_PASSWORD_RESET or not challenge.used_at:
            raise ValueError('A verified password reset OTP is required.')
        auth_settings = AuthenticationSettings.load()
        PasswordResetGrant.objects.filter(
            user=challenge.user,
            used_at__isnull=True,
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())
        raw_token = secrets.token_urlsafe(48)
        PasswordResetGrant.objects.create(
            user=challenge.user,
            otp_challenge=challenge,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(minutes=auth_settings.password_reset_expiration_minutes),
            request_ip=RequestContext.ip(request),
            user_agent=RequestContext.user_agent(request),
        )
        return {
            'uid': urlsafe_base64_encode(force_bytes(challenge.user.pk)),
            'reset_token': raw_token,
            'expires_in': auth_settings.password_reset_expiration_minutes * 60,
        }

    @staticmethod
    @transaction.atomic
    def consume(*, uid, token, password):
        try:
            user_id = int(urlsafe_base64_decode(uid).decode('utf-8'))
        except (TypeError, ValueError, UnicodeDecodeError) as exc:
            raise ValueError('Invalid password reset identifier.') from exc

        grant = (
            PasswordResetGrant.objects.select_for_update()
            .select_related('user')
            .filter(token_hash=hash_token(token), user_id=user_id)
            .first()
        )
        if not grant or grant.status != 'active' or not grant.matches(token):
            raise ValueError('Invalid or expired password reset token.')

        user = grant.user
        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            raise ValueError(' '.join(exc.messages)) from exc

        user.set_password(password)
        user.save(update_fields=('password',))
        grant.used_at = timezone.now()
        grant.save(update_fields=('used_at',))
        PasswordResetGrant.objects.filter(
            user=user,
            used_at__isnull=True,
            revoked_at__isnull=True,
        ).exclude(pk=grant.pk).update(revoked_at=timezone.now())
        if AuthenticationSettings.load().revoke_sessions_after_password_reset:
            SessionService.revoke_all(user=user, reason='password_reset')
        return user


class SessionService:
    @staticmethod
    def _datetime_from_timestamp(timestamp):
        return datetime.fromtimestamp(int(timestamp), tz=dt_timezone.utc)

    @classmethod
    @transaction.atomic
    def create_tokens(cls, *, user, request=None):
        from config.security.services import SecurityService

        security_settings = SecuritySettings.load()
        active = list(
            UserSession.objects.select_for_update()
            .filter(user=user, status=UserSession.STATUS_ACTIVE)
            .order_by('created_at')
        )
        max_sessions = max(1, security_settings.max_active_sessions)
        while len(active) >= max_sessions:
            oldest = active.pop(0)
            cls.revoke(session=oldest, reason='session_limit')

        analysis = SecurityService.analyze_session_context(user=user, request=request)
        refresh = RefreshToken.for_user(user)
        session = UserSession.objects.create(
            user=user,
            refresh_jti=str(refresh['jti']),
            ip_address=RequestContext.ip(request),
            user_agent=RequestContext.user_agent(request),
            device=RequestContext.device(request),
            device_fingerprint=analysis['fingerprint'],
            country_code=SecurityService.country_code(request),
            metadata={
                'new_device': analysis['new_device'],
                'new_ip': analysis['new_ip'],
                'new_country': analysis['new_country'],
            },
            expires_at=cls._datetime_from_timestamp(refresh['exp']),
        )
        roles = list(user.groups.values_list('name', flat=True))
        refresh['session_id'] = str(session.id)
        refresh['roles'] = roles
        access = refresh.access_token
        return {
            'access': str(access),
            'refresh': str(refresh),
            'access_expires_at': cls._datetime_from_timestamp(access['exp']),
            'refresh_expires_at': session.expires_at,
            'session_id': str(session.id),
            'security': {
                'new_device': analysis['new_device'],
                'new_ip': analysis['new_ip'],
                'new_country': analysis['new_country'],
            },
        }

    @staticmethod
    def validate(session_id, user_id=None):
        session = UserSession.objects.filter(pk=session_id, status=UserSession.STATUS_ACTIVE).first()
        if not session or session.expires_at <= timezone.now():
            if session and session.status == UserSession.STATUS_ACTIVE:
                session.status = UserSession.STATUS_EXPIRED
                session.save(update_fields=('status',))
            raise ValueError('Session is invalid or expired.')
        if user_id and session.user_id != int(user_id):
            raise ValueError('Session does not belong to the token user.')
        touch_seconds = max(15, SecuritySettings.load().session_activity_touch_seconds)
        if (timezone.now() - session.last_activity_at).total_seconds() >= touch_seconds:
            session.last_activity_at = timezone.now()
            session.save(update_fields=('last_activity_at',))
        return session

    @staticmethod
    @transaction.atomic
    def rotate(session, new_refresh):
        session.refresh_jti = str(new_refresh['jti'])
        session.expires_at = SessionService._datetime_from_timestamp(new_refresh['exp'])
        session.last_activity_at = timezone.now()
        session.save(update_fields=('refresh_jti', 'expires_at', 'last_activity_at'))

    @staticmethod
    def _blacklist_jti(jti):
        outstanding = OutstandingToken.objects.filter(jti=jti).first()
        if outstanding:
            BlacklistedToken.objects.get_or_create(token=outstanding)

    @classmethod
    def revoke(cls, *, session, reason='manual'):
        cls._blacklist_jti(session.refresh_jti)
        session.revoke(reason)

    @classmethod
    def revoke_all(cls, *, user, reason='manual'):
        count = 0
        sessions = UserSession.objects.filter(user=user, status=UserSession.STATUS_ACTIVE)
        for session in sessions:
            cls.revoke(session=session, reason=reason)
            count += 1
        return count


class FirstAccessService:
    """Forces a credential change on the first sign-in of a seeded account.

    The flag is checked by the portal permissions, so an account that has not
    completed this step can authenticate and fix its own credentials but cannot
    reach any business endpoint.
    """

    @staticmethod
    def require(user):
        record, _ = AccountLifecycle.objects.get_or_create(user=user)
        record.must_change_credentials = True
        record.save(update_fields=('must_change_credentials',))
        return record

    @staticmethod
    def is_pending(user):
        if not user or not user.is_authenticated:
            return False
        return AccountLifecycle.objects.filter(user=user, must_change_credentials=True).exists()

    @staticmethod
    @transaction.atomic
    def complete(*, user, email, password, request=None):
        """Applies the new e-mail and password, then revokes every session."""
        from config.security.services import SecurityService
        from .models import AuthenticationActivity

        email = (email or '').strip().lower()
        if not email:
            raise ValueError('An email address is required.')
        if User.objects.filter(username__iexact=email).exclude(pk=user.pk).exists():
            raise ValueError('This email is already in use.')
        if user.check_password(password):
            raise ValueError('Choose a password different from the temporary one.')
        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            raise ValueError(' '.join(exc.messages)) from exc

        previous_email = user.email
        # The project keeps username and email in sync.
        user.username = email
        user.email = email
        user.set_password(password)
        user.save(update_fields=('username', 'email', 'password'))

        record, _ = AccountLifecycle.objects.get_or_create(user=user)
        record.must_change_credentials = False
        record.credentials_updated_at = timezone.now()
        record.save(update_fields=('must_change_credentials', 'credentials_updated_at'))

        revoked = SessionService.revoke_all(user=user, reason='first_access_completed')
        SecurityService.record_activity(
            event_type='first_access',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=user,
            metadata={'email_changed': previous_email != email, 'sessions_revoked': revoked},
        )
        return user


def _is_protected_admin(user):
    """The default administrator can never be deactivated, archived or deleted."""
    from django.conf import settings
    protected = (getattr(settings, 'PROTECTED_ADMIN_EMAIL', '') or '').strip().lower()
    if user is None:
        return False
    if protected and user.email.strip().lower() == protected:
        return True
    return bool(user.is_superuser)


class AccountLifecycleService:
    """Single entry point for deactivation, logical deletion and their reversals.

    Accounts are never removed physically. Views, serializers and the Admin must
    call this service instead of touching `is_active` or the lifecycle record.
    """

    @staticmethod
    def lifecycle_for(user):
        record, _ = AccountLifecycle.objects.get_or_create(user=user)
        return record

    @staticmethod
    def _assert_not_self(user, performed_by):
        if performed_by is not None and performed_by.pk == user.pk:
            raise ValueError('An administrator cannot change the lifecycle of their own account.')

    @staticmethod
    def _cancel_pending_credentials(user):
        """Blocks pending OTPs and revokes pending password reset grants."""
        now = timezone.now()
        OTPChallenge.objects.filter(
            user=user,
            used_at__isnull=True,
            blocked_at__isnull=True,
            expires_at__gt=now,
        ).update(blocked_at=now)
        PasswordResetGrant.objects.filter(
            user=user,
            used_at__isnull=True,
            revoked_at__isnull=True,
        ).update(revoked_at=now)

    @staticmethod
    def _blacklist_outstanding_tokens(user):
        """Blacklists every refresh token, including tokens without a session row."""
        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)

    @classmethod
    def _revoke_access(cls, *, user, reason):
        revoked = SessionService.revoke_all(user=user, reason=reason)
        cls._blacklist_outstanding_tokens(user)
        cls._cancel_pending_credentials(user)
        return revoked

    @staticmethod
    def _audit(*, event_type, user, performed_by, reason, severity, request=None, metadata=None):
        from config.authentication.models import AuthenticationActivity, SecurityEvent
        from config.security.services import SecurityService

        payload = {
            'performed_by': getattr(performed_by, 'pk', None),
            'performed_by_email': getattr(performed_by, 'email', ''),
            **(metadata or {}),
        }
        SecurityService.record_activity(
            event_type=event_type,
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=user,
            reason=reason,
            metadata=payload,
        )
        SecurityService.create_event(
            event_type=event_type,
            severity=severity,
            user=user,
            request=request,
            summary=reason or event_type.replace('_', ' ').capitalize(),
            metadata=payload,
        )

    @staticmethod
    def _notify(*, purpose, user, request, message):
        from config.authentication.serializers import send_optional_email

        send_optional_email(purpose=purpose, user=user, request=request, message=message)

    @classmethod
    @transaction.atomic
    def deactivate(cls, *, user, performed_by=None, reason='', request=None):
        """Temporary, reversible suspension. The account stays visible in the Admin."""
        from config.authentication.models import SecurityEvent

        cls._assert_not_self(user, performed_by)
        if _is_protected_admin(user):
            raise ValueError('The default administrator account is protected and cannot be changed.')
        lifecycle = cls.lifecycle_for(user)
        if lifecycle.is_archived:
            raise ValueError('Archived accounts must be restored before being deactivated.')
        if lifecycle.deactivated_at and not user.is_active:
            return lifecycle

        user.is_active = False
        user.save(update_fields=('is_active',))
        revoked = cls._revoke_access(user=user, reason='account_deactivated')

        lifecycle.deactivated_at = timezone.now()
        lifecycle.deactivated_by = performed_by
        lifecycle.deactivation_reason = reason
        lifecycle.save(update_fields=('deactivated_at', 'deactivated_by', 'deactivation_reason'))

        cls._audit(
            event_type='account_deactivated',
            user=user,
            performed_by=performed_by,
            reason=reason or 'Account deactivated.',
            severity=SecurityEvent.SEVERITY_WARNING,
            request=request,
            metadata={'sessions_revoked': revoked},
        )
        cls._notify(
            purpose='account_deactivated',
            user=user,
            request=request,
            message=reason or 'A sua conta foi desativada.',
        )
        return lifecycle

    @classmethod
    @transaction.atomic
    def archive(cls, *, user, performed_by=None, reason='', request=None):
        """Logical deletion. Nothing is removed; the account is hidden from operations."""
        from config.authentication.models import SecurityEvent

        cls._assert_not_self(user, performed_by)
        if _is_protected_admin(user):
            raise ValueError('The default administrator account is protected and cannot be changed.')
        lifecycle = cls.lifecycle_for(user)
        if lifecycle.is_archived:
            return lifecycle

        user.is_active = False
        user.save(update_fields=('is_active',))
        revoked = cls._revoke_access(user=user, reason='account_archived')

        now = timezone.now()
        lifecycle.archived_at = now
        lifecycle.archived_by = performed_by
        lifecycle.archive_reason = reason
        if not lifecycle.deactivated_at:
            lifecycle.deactivated_at = now
            lifecycle.deactivated_by = performed_by
            lifecycle.deactivation_reason = reason or 'Archived account.'
        lifecycle.save()

        cls._audit(
            event_type='account_archived',
            user=user,
            performed_by=performed_by,
            reason=reason or 'Account archived.',
            severity=SecurityEvent.SEVERITY_WARNING,
            request=request,
            metadata={'sessions_revoked': revoked},
        )
        cls._notify(
            purpose='account_deactivated',
            user=user,
            request=request,
            message=reason or 'A sua conta foi encerrada.',
        )
        return lifecycle

    @classmethod
    @transaction.atomic
    def reactivate(cls, *, user, performed_by=None, request=None):
        """Reverses a deactivation. Archived accounts must be restored first."""
        from config.authentication.models import SecurityEvent

        cls._assert_not_self(user, performed_by)
        lifecycle = cls.lifecycle_for(user)
        if lifecycle.is_archived:
            raise ValueError('Restore the archived account before reactivating it.')

        user.is_active = True
        user.save(update_fields=('is_active',))
        lifecycle.deactivated_at = None
        lifecycle.deactivated_by = None
        lifecycle.deactivation_reason = ''
        lifecycle.last_reactivated_at = timezone.now()
        lifecycle.save(update_fields=(
            'deactivated_at',
            'deactivated_by',
            'deactivation_reason',
            'last_reactivated_at',
        ))

        cls._audit(
            event_type='account_reactivated',
            user=user,
            performed_by=performed_by,
            reason='Account reactivated.',
            severity=SecurityEvent.SEVERITY_INFO,
            request=request,
        )
        cls._notify(
            purpose='account_activated',
            user=user,
            request=request,
            message='A sua conta foi reativada.',
        )
        return lifecycle

    @classmethod
    @transaction.atomic
    def restore(cls, *, user, performed_by=None, request=None):
        """Reverses a logical deletion.

        The account leaves the archive as deactivated: login is only restored by
        an explicit `reactivate`, so restoring never silently grants access back.
        """
        from config.authentication.models import SecurityEvent

        cls._assert_not_self(user, performed_by)
        lifecycle = cls.lifecycle_for(user)
        if not lifecycle.is_archived:
            raise ValueError('This account is not archived.')

        lifecycle.archived_at = None
        lifecycle.archived_by = None
        lifecycle.archive_reason = ''
        if not lifecycle.deactivated_at:
            lifecycle.deactivated_at = timezone.now()
            lifecycle.deactivated_by = performed_by
        if not lifecycle.deactivation_reason:
            lifecycle.deactivation_reason = 'Restored from the archive. Reactivation is required.'
        lifecycle.save()

        cls._audit(
            event_type='account_restored',
            user=user,
            performed_by=performed_by,
            reason='Account restored from the archive.',
            severity=SecurityEvent.SEVERITY_INFO,
            request=request,
        )
        return lifecycle
