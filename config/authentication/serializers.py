import logging
import uuid

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from config.common.email_service import EmailService
from config.common.models import AuthenticationSettings, SecuritySettings
from config.security.request import RequestContext
from config.security.services import SecurityService
from .models import AccountLifecycle, AuthenticationActivity, OTPChallenge, UserSession
from .services import (
    FirstAccessService,
    OTPService,
    PasswordResetService,
    SessionService,
    UserPresenter,
    UserService,
)

logger = logging.getLogger(__name__)


def email_context(user, request=None, **extra):
    return {
        'user': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        },
        'ip_address': RequestContext.ip(request),
        'user_agent': RequestContext.user_agent(request),
        'device': RequestContext.device(request),
        'country_code': SecurityService.country_code(request),
        'event_time': timezone.now(),
        **extra,
    }


def send_optional_email(*, purpose, user, request=None, **extra):
    try:
        return EmailService.send_by_purpose(
            purpose=purpose,
            recipients=[user.email],
            context=email_context(user, request=request, **extra),
        )
    except Exception:
        logger.exception('Optional authentication email failed. purpose=%s user_id=%s', purpose, user.pk)
        return None


def send_session_security_alerts(*, user, request, token_data):
    settings = SecuritySettings.load()
    flags = token_data.get('security', {})
    if flags.get('new_device') and settings.notify_new_device:
        send_optional_email(purpose='new_device', user=user, request=request)
    if flags.get('new_ip') and settings.notify_new_ip:
        send_optional_email(purpose='new_ip_access', user=user, request=request)
    if flags.get('new_country') and settings.notify_new_country:
        send_optional_email(purpose='new_country_access', user=user, request=request)


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(username__iexact=value).exists() or User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email is already registered.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        validate_password(attrs['password'])
        return attrs

    def save(self):
        request = self.context.get('request')
        try:
            user = UserService.register(
                first_name=self.validated_data['first_name'],
                last_name=self.validated_data['last_name'],
                email=self.validated_data['email'],
                password=self.validated_data['password'],
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        auth_settings = AuthenticationSettings.load()
        response = {'user': UserPresenter.build(user), 'requires_otp': False}
        if auth_settings.email_verification_required:
            challenge, code = OTPService.create(
                user=user,
                purpose=OTPChallenge.PURPOSE_REGISTER,
                request=request,
            )
            try:
                EmailService.send_by_purpose(
                    purpose='register_otp',
                    recipients=[user.email],
                    context=email_context(user, request=request, otp=code, challenge_id=str(challenge.id)),
                )
            except Exception as exc:
                logger.exception('Unable to send registration OTP. user_id=%s', user.pk)
                raise serializers.ValidationError('Registration was created, but the OTP email could not be sent.') from exc
            response.update({
                'requires_otp': True,
                'challenge_id': str(challenge.id),
                'expires_at': challenge.expires_at,
            })
        else:
            send_optional_email(purpose='register', user=user, request=request)

        SecurityService.record_activity(
            event_type='register',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=user,
        )
        return response


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        request = self.context.get('request')
        email = attrs['email'].strip().lower()
        ip_address = RequestContext.ip(request)
        pre_user = User.objects.filter(username__iexact=email).first()
        block = SecurityService.active_block(
            user=pre_user,
            ip_address=ip_address,
            country_code=SecurityService.country_code(request),
            user_agent=RequestContext.user_agent(request),
        )
        if block:
            SecurityService.record_activity(
                event_type='login',
                status=AuthenticationActivity.STATUS_BLOCKED,
                request=request,
                user=pre_user,
                email=email,
                reason=block.reason,
            )
            raise serializers.ValidationError('Access is temporarily blocked.')

        # Archived accounts are already inactive, so they never authenticate. The
        # explicit check only records the real reason without leaking it.
        if pre_user and AccountLifecycle.objects.filter(user=pre_user, archived_at__isnull=False).exists():
            SecurityService.record_activity(
                event_type='login',
                status=AuthenticationActivity.STATUS_BLOCKED,
                request=request,
                user=pre_user,
                email=email,
                reason='account_archived',
            )
            raise serializers.ValidationError('Invalid credentials.')

        user = authenticate(request=request, username=email, password=attrs['password'])
        if not user:
            SecurityService.record_activity(
                event_type='login',
                status=AuthenticationActivity.STATUS_FAILED,
                request=request,
                user=pre_user,
                email=email,
                reason='invalid_credentials',
            )
            blocks = SecurityService.enforce_failed_login_blocks(
                user=pre_user,
                email=email,
                ip_address=ip_address,
            )
            if blocks and pre_user:
                send_optional_email(purpose='account_blocked', user=pre_user, request=request)
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('User is inactive or email verification is pending.')

        auth_settings = AuthenticationSettings.load()
        if auth_settings.deny_django_admin_api_login and (user.is_staff or user.is_superuser):
            SecurityService.record_activity(
                event_type='login',
                status=AuthenticationActivity.STATUS_BLOCKED,
                request=request,
                user=user,
                reason='django_admin_frontend_login_denied',
            )
            raise serializers.ValidationError('Esta conta não tem acesso a esta área.')
        attrs['user'] = user
        return attrs

    def save(self):
        request = self.context.get('request')
        user = self.validated_data['user']
        auth_settings = AuthenticationSettings.load()
        if auth_settings.login_otp_enabled:
            challenge, code = OTPService.create(
                user=user,
                purpose=OTPChallenge.PURPOSE_LOGIN,
                request=request,
            )
            try:
                EmailService.send_by_purpose(
                    purpose='login_otp',
                    recipients=[user.email],
                    context=email_context(user, request=request, otp=code, challenge_id=str(challenge.id)),
                )
            except Exception as exc:
                logger.exception('Unable to send login OTP. user_id=%s', user.pk)
                raise serializers.ValidationError('The login OTP could not be sent.') from exc
            return {
                'requires_otp': True,
                'challenge_id': str(challenge.id),
                'expires_at': challenge.expires_at,
            }

        tokens = SessionService.create_tokens(user=user, request=request)
        user.last_login = timezone.now()
        user.save(update_fields=('last_login',))
        SecurityService.record_activity(
            event_type='login',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=user,
            metadata={'session_id': tokens['session_id']},
        )
        send_session_security_alerts(user=user, request=request, token_data=tokens)
        return {'requires_otp': False, **tokens, 'user': UserPresenter.build(user)}


class OTPVerifySerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField()
    code = serializers.CharField(min_length=6, max_length=8, trim_whitespace=True)

    def save(self):
        request = self.context.get('request')
        challenge_id = self.validated_data['challenge_id']
        try:
            challenge = OTPService.verify(
                challenge_id=challenge_id,
                code=self.validated_data['code'],
            )
        except ValueError as exc:
            existing = OTPChallenge.objects.select_related('user').filter(pk=challenge_id).first()
            SecurityService.record_activity(
                event_type='otp_verify',
                status=AuthenticationActivity.STATUS_FAILED,
                request=request,
                user=getattr(existing, 'user', None),
                reason=str(exc),
                metadata={'challenge_id': str(challenge_id)},
            )
            raise serializers.ValidationError(str(exc)) from exc

        user = challenge.user
        if challenge.purpose == OTPChallenge.PURPOSE_REGISTER:
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=('is_active',))
            SecurityService.record_activity(
                event_type='register_otp',
                status=AuthenticationActivity.STATUS_SUCCESS,
                request=request,
                user=user,
            )
            send_optional_email(purpose='account_activated', user=user, request=request)
            return {'verified': True, 'purpose': challenge.purpose, 'user': UserPresenter.build(user)}

        if challenge.purpose == OTPChallenge.PURPOSE_LOGIN:
            tokens = SessionService.create_tokens(user=user, request=request)
            user.last_login = timezone.now()
            user.save(update_fields=('last_login',))
            SecurityService.record_activity(
                event_type='login_otp',
                status=AuthenticationActivity.STATUS_SUCCESS,
                request=request,
                user=user,
                metadata={'session_id': tokens['session_id']},
            )
            send_session_security_alerts(user=user, request=request, token_data=tokens)
            return {
                'verified': True,
                'purpose': challenge.purpose,
                **tokens,
                'user': UserPresenter.build(user),
            }

        if challenge.purpose == OTPChallenge.PURPOSE_PASSWORD_RESET:
            grant = PasswordResetService.create_grant(challenge=challenge, request=request)
            SecurityService.record_activity(
                event_type='password_reset_otp',
                status=AuthenticationActivity.STATUS_SUCCESS,
                request=request,
                user=user,
            )
            return {'verified': True, 'purpose': challenge.purpose, **grant}

        raise serializers.ValidationError('Unsupported OTP purpose.')


class OTPResendSerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField()

    def save(self):
        request = self.context.get('request')
        auth_settings = AuthenticationSettings.load()
        challenge = (
            OTPChallenge.objects.select_related('user')
            .filter(pk=self.validated_data['challenge_id'])
            .first()
        )
        if not challenge or challenge.used_at or challenge.blocked_at:
            raise serializers.ValidationError('OTP challenge cannot be resent.')

        elapsed = (timezone.now() - challenge.created_at).total_seconds()
        if elapsed < auth_settings.otp_resend_cooldown_seconds:
            raise serializers.ValidationError({
                'retry_after': int(auth_settings.otp_resend_cooldown_seconds - elapsed),
                'detail': 'Wait before requesting another OTP.',
            })
        if challenge.resend_count >= auth_settings.otp_max_resends:
            raise serializers.ValidationError('OTP resend limit reached.')

        new_challenge, code = OTPService.create(
            user=challenge.user,
            purpose=challenge.purpose,
            request=request,
        )
        new_challenge.resend_count = challenge.resend_count + 1
        new_challenge.save(update_fields=('resend_count',))
        purpose_map = {
            OTPChallenge.PURPOSE_REGISTER: 'register_otp',
            OTPChallenge.PURPOSE_LOGIN: 'login_otp',
            OTPChallenge.PURPOSE_PASSWORD_RESET: 'password_recovery',
        }
        try:
            EmailService.send_by_purpose(
                purpose=purpose_map[challenge.purpose],
                recipients=[challenge.user.email],
                context=email_context(
                    challenge.user,
                    request=request,
                    otp=code,
                    challenge_id=str(new_challenge.id),
                ),
            )
        except Exception as exc:
            logger.exception('Unable to resend OTP. user_id=%s', challenge.user_id)
            raise serializers.ValidationError('The OTP could not be resent.') from exc

        SecurityService.record_activity(
            event_type='otp_resend',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=challenge.user,
            metadata={
                'purpose': challenge.purpose,
                'resend_count': new_challenge.resend_count,
            },
        )
        return {
            'challenge_id': str(new_challenge.id),
            'expires_at': new_challenge.expires_at,
            'resend_count': new_challenge.resend_count,
        }


class RecoverySerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        request = self.context.get('request')
        email = self.validated_data['email'].strip().lower()
        user = User.objects.filter(username__iexact=email, is_active=True).first()
        auth_settings = AuthenticationSettings.load()
        response_challenge_id = str(uuid.uuid4())

        if user:
            challenge, code = OTPService.create(
                user=user,
                purpose=OTPChallenge.PURPOSE_PASSWORD_RESET,
                request=request,
            )
            response_challenge_id = str(challenge.id)
            try:
                EmailService.send_by_purpose(
                    purpose='password_recovery',
                    recipients=[user.email],
                    context=email_context(user, request=request, otp=code, challenge_id=str(challenge.id)),
                )
            except Exception:
                logger.exception('Unable to send password recovery OTP. user_id=%s', user.pk)
            SecurityService.record_activity(
                event_type='password_recovery',
                status=AuthenticationActivity.STATUS_SUCCESS,
                request=request,
                user=user,
            )
        else:
            SecurityService.record_activity(
                event_type='password_recovery',
                status=AuthenticationActivity.STATUS_SUCCESS,
                request=request,
                email=email,
                reason='generic_response',
            )

        return {
            'sent': True,
            'challenge_id': response_challenge_id,
            'expires_in': auth_settings.otp_expiration_minutes * 60,
        }


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=255)
    reset_token = serializers.CharField(min_length=32, trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def save(self):
        request = self.context.get('request')
        try:
            user = PasswordResetService.consume(
                uid=self.validated_data['uid'],
                token=self.validated_data['reset_token'],
                password=self.validated_data['password'],
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        send_optional_email(purpose='password_changed', user=user, request=request)
        SecurityService.record_activity(
            event_type='password_reset',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=user,
        )
        return {'reset': True}


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def save(self):
        request = self.context['request']
        try:
            user = UserService.change_password(
                user=request.user,
                current_password=self.validated_data['current_password'],
                new_password=self.validated_data['password'],
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        send_optional_email(purpose='password_changed', user=user, request=request)
        SecurityService.record_activity(
            event_type='password_change',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=user,
        )
        return {'changed': True, 'sessions_revoked': AuthenticationSettings.load().revoke_sessions_after_password_change}


class FirstAccessSerializer(serializers.Serializer):
    """First sign-in of a seeded account: own e-mail and a personal password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def save(self):
        request = self.context['request']
        try:
            user = FirstAccessService.complete(
                user=request.user,
                email=self.validated_data['email'],
                password=self.validated_data['password'],
                request=request,
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        send_optional_email(purpose='password_changed', user=user, request=request)
        return {'completed': True, 'email': user.email, 'sessions_revoked': True}


class VelomaTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        request = self.context.get('request')
        incoming = RefreshToken(attrs['refresh'])
        session_id = incoming.get('session_id')
        if not session_id:
            raise serializers.ValidationError('Token has no session context.')
        try:
            session = SessionService.validate(session_id, user_id=incoming.get('user_id'))
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        block = SecurityService.active_block(
            user=session.user,
            ip_address=RequestContext.ip(request),
            country_code=SecurityService.country_code(request),
            user_agent=RequestContext.user_agent(request),
        )
        if block:
            raise serializers.ValidationError('Access is blocked.')

        data = super().validate(attrs)
        if 'refresh' in data:
            SessionService.rotate(session, RefreshToken(data['refresh']))
        data['session_id'] = str(session.id)
        SecurityService.record_activity(
            event_type='token_refresh',
            status=AuthenticationActivity.STATUS_SUCCESS,
            request=request,
            user=session.user,
            metadata={'session_id': str(session.id)},
        )
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=False, trim_whitespace=False)

    def validate(self, attrs):
        request = self.context['request']
        raw_refresh = attrs.get('refresh')
        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
            except TokenError as exc:
                raise serializers.ValidationError('Refresh token is invalid or already revoked.') from exc
            if int(token.get('user_id', 0)) != request.user.id:
                raise serializers.ValidationError('Refresh token does not belong to the authenticated user.')
            attrs['token'] = token
        return attrs

    def save(self):
        request = self.context['request']
        session_ids = set()
        access_session_id = request.auth.get('session_id') if request.auth else None
        if access_session_id:
            session_ids.add(str(access_session_id))
        token = self.validated_data.get('token')
        if token and token.get('session_id'):
            session_ids.add(str(token['session_id']))

        revoked = 0
        for session in UserSession.objects.filter(
            pk__in=session_ids,
            user=request.user,
            status=UserSession.STATUS_ACTIVE,
        ):
            SessionService.revoke(session=session, reason='logout')
            revoked += 1
        if token:
            try:
                token.blacklist()
            except TokenError:
                pass
        return {'logged_out': True, 'sessions_revoked': revoked}


class LogoutAllSerializer(serializers.Serializer):
    def save(self):
        request = self.context['request']
        revoked = SessionService.revoke_all(user=request.user, reason='logout_all')
        send_optional_email(purpose='all_sessions_revoked', user=request.user, request=request)
        return {'logged_out': True, 'sessions_revoked': revoked}
