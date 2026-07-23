from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from config.common.models import EmailDeliveryLog, SecuritySettings
from .models import AuthenticationActivity, OTPChallenge, PasswordResetGrant, SecurityEvent, UserSession


@shared_task
def cleanup_expired_authentication_records():
    now = timezone.now()
    settings = SecuritySettings.load()

    expired_sessions = UserSession.objects.filter(
        status=UserSession.STATUS_ACTIVE,
        expires_at__lte=now,
    ).update(status=UserSession.STATUS_EXPIRED)

    auth_cutoff = now - timedelta(days=settings.authentication_record_retention_days)
    audit_cutoff = now - timedelta(days=settings.audit_log_retention_days)
    email_cutoff = now - timedelta(days=settings.email_log_retention_days)

    deleted_grants, _ = PasswordResetGrant.objects.filter(created_at__lt=auth_cutoff).delete()
    deleted_otps, _ = OTPChallenge.objects.filter(created_at__lt=auth_cutoff).delete()
    deleted_sessions, _ = UserSession.objects.filter(
        created_at__lt=auth_cutoff,
    ).exclude(status=UserSession.STATUS_ACTIVE).delete()
    deleted_activities, _ = AuthenticationActivity.objects.filter(created_at__lt=audit_cutoff).delete()
    deleted_events, _ = SecurityEvent.objects.filter(created_at__lt=audit_cutoff).delete()
    deleted_email_logs, _ = EmailDeliveryLog.objects.filter(created_at__lt=email_cutoff).delete()

    # SimpleJWT stores its own token history. Keep the same authentication retention.
    BlacklistedToken.objects.filter(blacklisted_at__lt=auth_cutoff).delete()
    OutstandingToken.objects.filter(expires_at__lt=auth_cutoff).delete()

    return {
        'expired_sessions': expired_sessions,
        'deleted_otps': deleted_otps,
        'deleted_grants': deleted_grants,
        'deleted_sessions': deleted_sessions,
        'deleted_activities': deleted_activities,
        'deleted_security_events': deleted_events,
        'deleted_email_logs': deleted_email_logs,
    }
