from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from config.authentication.models import AccessBlock, AuthenticationActivity, SecurityEvent, UserSession
from config.common.models import SecuritySettings


class SecurityService:
    @staticmethod
    def country_code(request):
        if request is None:
            return ''
        data = getattr(request, 'ip_intel', {}) or {}
        return str(data.get('country_code') or data.get('countryCode') or data.get('country') or '').upper()[:8]

    @staticmethod
    def active_block(*, user=None, ip_address=None, country_code='', user_agent=''):
        now = timezone.now()
        queryset = AccessBlock.objects.filter(active=True, starts_at__lte=now).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        checks = Q()
        if user and getattr(user, 'is_authenticated', False):
            checks |= Q(block_type=AccessBlock.TYPE_USER, user=user)
        if ip_address:
            checks |= Q(block_type=AccessBlock.TYPE_IP, value=ip_address)
        if country_code:
            checks |= Q(block_type=AccessBlock.TYPE_COUNTRY, value__iexact=country_code)
        if user_agent:
            checks |= Q(block_type=AccessBlock.TYPE_USER_AGENT, value__iexact=user_agent)
        return queryset.filter(checks).first() if checks else None

    @staticmethod
    def record_activity(*, event_type, status, request=None, user=None, email='', reason='', metadata=None, country_code=''):
        from .request import RequestContext

        return AuthenticationActivity.objects.create(
            event_type=event_type,
            status=status,
            user=user,
            email=email or getattr(user, 'email', ''),
            ip_address=RequestContext.ip(request) if request else None,
            user_agent=RequestContext.user_agent(request) if request else '',
            country_code=country_code or SecurityService.country_code(request),
            reason=reason,
            metadata=metadata or {},
        )

    @staticmethod
    def create_event(*, event_type, severity, summary, request=None, user=None, metadata=None):
        from .request import RequestContext

        return SecurityEvent.objects.create(
            event_type=event_type,
            severity=severity,
            user=user,
            ip_address=RequestContext.ip(request) if request else None,
            summary=summary,
            metadata=metadata or {},
        )

    @staticmethod
    def failed_logins_for_email(email):
        settings = SecuritySettings.load()
        since = timezone.now() - timedelta(minutes=settings.login_window_minutes)
        return AuthenticationActivity.objects.filter(
            event_type='login',
            status=AuthenticationActivity.STATUS_FAILED,
            created_at__gte=since,
            email__iexact=email,
        ).count()

    @staticmethod
    def failed_logins_for_ip(ip_address):
        if not ip_address:
            return 0
        settings = SecuritySettings.load()
        since = timezone.now() - timedelta(minutes=settings.login_window_minutes)
        return AuthenticationActivity.objects.filter(
            event_type='login',
            status=AuthenticationActivity.STATUS_FAILED,
            created_at__gte=since,
            ip_address=ip_address,
        ).count()

    @staticmethod
    def _existing_automatic_block(*, block_type, user=None, value=''):
        now = timezone.now()
        return AccessBlock.objects.filter(
            block_type=block_type,
            user=user,
            value=value,
            active=True,
            automatic=True,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now)).first()

    @classmethod
    def create_automatic_block(cls, *, block_type, user=None, value='', ip_address=None, reason='Too many failed login attempts'):
        existing = cls._existing_automatic_block(block_type=block_type, user=user, value=value)
        if existing:
            return existing
        settings = SecuritySettings.load()
        expires_at = timezone.now() + timedelta(minutes=settings.automatic_block_minutes)
        block = AccessBlock.objects.create(
            block_type=block_type,
            user=user,
            value=value,
            reason=reason,
            automatic=True,
            expires_at=expires_at,
        )
        cls.create_event(
            event_type='automatic_block',
            severity=SecurityEvent.SEVERITY_WARNING,
            user=user,
            summary=reason,
            metadata={
                'block_id': str(block.id),
                'block_type': block_type,
                'value': value,
                'expires_at': expires_at.isoformat(),
                'source_ip': ip_address,
            },
        )
        return block

    @classmethod
    def enforce_failed_login_blocks(cls, *, user, email, ip_address):
        settings = SecuritySettings.load()
        blocks = []
        if settings.block_user_on_failed_login and user and cls.failed_logins_for_email(email) >= settings.login_max_attempts:
            blocks.append(cls.create_automatic_block(
                block_type=AccessBlock.TYPE_USER,
                user=user,
                ip_address=ip_address,
                reason='User temporarily blocked after repeated failed logins.',
            ))
        if settings.block_ip_on_failed_login and ip_address and cls.failed_logins_for_ip(ip_address) >= settings.login_max_attempts:
            blocks.append(cls.create_automatic_block(
                block_type=AccessBlock.TYPE_IP,
                value=ip_address,
                ip_address=ip_address,
                reason='IP temporarily blocked after repeated failed logins.',
            ))
        return blocks

    @classmethod
    def analyze_session_context(cls, *, user, request):
        from .request import RequestContext

        fingerprint = RequestContext.fingerprint(request)
        ip_address = RequestContext.ip(request)
        country_code = cls.country_code(request)
        previous = UserSession.objects.filter(user=user)
        has_history = previous.exists()
        result = {
            'fingerprint': fingerprint,
            'new_device': has_history and not previous.filter(device_fingerprint=fingerprint).exists(),
            'new_ip': bool(has_history and ip_address and not previous.filter(ip_address=ip_address).exists()),
            'new_country': bool(has_history and country_code and not previous.filter(country_code=country_code).exists()),
        }
        if result['new_device']:
            cls.create_event(
                event_type='new_device',
                severity=SecurityEvent.SEVERITY_WARNING,
                user=user,
                request=request,
                summary='Authentication from a new device.',
                metadata={'device': RequestContext.device(request), 'fingerprint': fingerprint},
            )
        if result['new_ip']:
            cls.create_event(
                event_type='new_ip',
                severity=SecurityEvent.SEVERITY_INFO,
                user=user,
                request=request,
                summary='Authentication from a new IP address.',
                metadata={'ip_address': ip_address},
            )
        if result['new_country']:
            cls.create_event(
                event_type='new_country',
                severity=SecurityEvent.SEVERITY_WARNING,
                user=user,
                request=request,
                summary='Authentication from a new country.',
                metadata={'country_code': country_code},
            )
        return result
