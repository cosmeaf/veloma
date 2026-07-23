from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.security.request import RequestContext
from config.security.services import SecurityService
from .services import SessionService


class SessionJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, validated_token = result
        block = SecurityService.active_block(
            user=user,
            ip_address=RequestContext.ip(request),
            country_code=SecurityService.country_code(request),
            user_agent=RequestContext.user_agent(request),
        )
        if block:
            raise AuthenticationFailed('Access is blocked.', code='access_blocked')
        return user, validated_token

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        session_id = validated_token.get('session_id')
        if not session_id:
            raise AuthenticationFailed(
                'Token has no active session context.',
                code='session_missing',
            )
        try:
            SessionService.validate(session_id, user_id=user.id)
        except ValueError as exc:
            raise AuthenticationFailed(str(exc), code='session_invalid') from exc
        return user
