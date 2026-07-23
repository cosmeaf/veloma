import hashlib
import time

from django.core.cache import cache
from django.http import JsonResponse

from config.authentication.models import AuthenticationActivity
from config.common.models import SecuritySettings
from .ip_intel import IPIntelligenceService
from .request import RequestContext
from .services import SecurityService


class SecurityContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _rate_limit(request, security_settings):
        if not security_settings.api_rate_limit_enabled:
            return None
        is_auth = request.path.startswith('/api/auth/')
        limit = security_settings.auth_rate_limit_requests if is_auth else security_settings.api_rate_limit_requests
        seconds = security_settings.auth_rate_limit_window_seconds if is_auth else security_settings.api_rate_limit_window_seconds
        try:
            window = int(time.time()) // seconds
            raw_key = f'{request.client_ip}:{request.path}:{window}'
            key = 'veloma:rate:' + hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
            cache.add(key, 0, timeout=seconds + 5)
            requests_count = cache.incr(key)
            if requests_count > limit:
                SecurityService.record_activity(
                    event_type='rate_limit',
                    status=AuthenticationActivity.STATUS_BLOCKED,
                    request=request,
                    reason='api_rate_limit_exceeded',
                    metadata={'count': requests_count, 'limit': limit, 'window_seconds': seconds},
                )
                return JsonResponse(
                    {
                        'success': False,
                        'message': 'Too many requests.',
                        'retry_after': seconds,
                    },
                    status=429,
                )
        except Exception:
            # A cache outage must not take the API offline. Authentication-level
            # brute-force controls still remain active in the database.
            return None
        return None

    def __call__(self, request):
        request.client_ip = RequestContext.ip(request)
        request.client_user_agent = RequestContext.user_agent(request)
        request.client_device = RequestContext.device(request)
        request.ip_intel = {}

        if request.path.startswith('/api/'):
            security_settings = SecuritySettings.load()
            response = self._rate_limit(request, security_settings)
            if response:
                return response

            try:
                request.ip_intel = IPIntelligenceService.lookup(request.client_ip)
            except Exception:
                request.ip_intel = {}

            country_code = SecurityService.country_code(request)
            allowed_countries = {
                item.strip().upper()
                for item in security_settings.allowed_country_codes.split(',')
                if item.strip()
            }
            if security_settings.block_unknown_countries and allowed_countries:
                if not country_code or country_code not in allowed_countries:
                    SecurityService.record_activity(
                        event_type='country_access',
                        status=AuthenticationActivity.STATUS_BLOCKED,
                        request=request,
                        reason='country_not_allowed',
                        country_code=country_code,
                    )
                    return JsonResponse(
                        {'success': False, 'message': 'Access is not allowed from this country.'},
                        status=403,
                    )

            block = SecurityService.active_block(
                user=request.user,
                ip_address=request.client_ip,
                country_code=country_code,
                user_agent=request.client_user_agent,
            )
            if block:
                SecurityService.record_activity(
                    event_type='access_block',
                    status=AuthenticationActivity.STATUS_BLOCKED,
                    request=request,
                    reason=block.reason,
                    country_code=country_code,
                    metadata={'block_id': str(block.id), 'block_type': block.block_type},
                )
                return JsonResponse(
                    {'success': False, 'message': 'Access temporarily blocked.'},
                    status=403,
                )
        return self.get_response(request)
