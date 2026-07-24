from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView

from config.common.responses import api_response
from .models import UserSession
from .serializers import (
    FirstAccessSerializer,
    LoginSerializer,
    PreferencesSerializer,
    TwoFactorSerializer,
    LogoutAllSerializer,
    LogoutSerializer,
    OTPResendSerializer,
    OTPVerifySerializer,
    PasswordChangeSerializer,
    PasswordResetSerializer,
    RecoverySerializer,
    RegisterSerializer,
    VelomaTokenRefreshSerializer,
)
from .services import SessionService, UserPresenter


class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(
            data=serializer.save(),
            message='Registration created.',
            status=status.HTTP_201_CREATED,
        )


class LoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='Authentication processed.')


class OTPVerifyView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OTPVerifySerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='OTP validated.')


class OTPResendView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OTPResendSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='OTP resent.')


class RecoveryView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RecoverySerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(
            data=serializer.save(),
            message='If the account exists, recovery instructions were sent.',
        )


class PasswordResetView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='Password changed successfully.')


class PasswordChangeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='Password changed successfully.')


class FirstAccessView(GenericAPIView):
    """Available to any authenticated user; required before portal access."""

    permission_classes = [IsAuthenticated]
    serializer_class = FirstAccessSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(
            data=serializer.save(),
            message='Credentials updated. Sign in again with the new ones.',
        )


class VelomaTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = VelomaTokenRefreshSerializer


class LogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='Session closed.')


class LogoutAllView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutAllSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='All sessions closed.')


class MeView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return api_response(data={'user': UserPresenter.build(request.user)})


class PreferencesView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PreferencesSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(data=serializer.save(), message='Preferências guardadas.')


class NotificationsView(GenericAPIView):
    """Recent activity relevant to the user, with an unread count.

    Derives from the audit trail already recorded, so there is no separate
    notifications table. "Unread" is anything after `notifications_seen_at`.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .notifications import build_notifications

        record, _ = _lifecycle(request.user)
        items = build_notifications(request.user, limit=20, since=record.notifications_cleared_at)
        seen_at = record.notifications_seen_at
        unread = sum(1 for item in items if seen_at is None or item['created_at'] > seen_at)
        return api_response(data={'notifications': items, 'unread': unread})

    def post(self, request):
        # Mark everything as seen.
        from django.utils import timezone

        record, _ = _lifecycle(request.user)
        record.notifications_seen_at = timezone.now()
        record.save(update_fields=('notifications_seen_at',))
        return api_response(data={'unread': 0}, message='Notificações marcadas como lidas.')

    def delete(self, request):
        # Clear all: hide everything up to now from the feed.
        from django.utils import timezone

        now = timezone.now()
        record, _ = _lifecycle(request.user)
        record.notifications_cleared_at = now
        record.notifications_seen_at = now
        record.save(update_fields=('notifications_cleared_at', 'notifications_seen_at'))
        return api_response(data={'notifications': [], 'unread': 0}, message='Notificações apagadas.')


def _lifecycle(user):
    from .models import AccountLifecycle

    return AccountLifecycle.objects.get_or_create(user=user)


class TwoFactorView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TwoFactorSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        message = 'Verificação em duas etapas ativada.' if data['two_factor_email'] else 'Verificação em duas etapas desativada.'
        return api_response(data=data, message=message)


class AccessHistoryView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from user_agents import parse

        from .models import AuthenticationActivity

        events = (
            AuthenticationActivity.objects.filter(
                user=request.user,
                event_type__in=('login', 'login_otp', 'token_refresh', 'first_access'),
            )
            .order_by('-created_at')[:25]
        )
        data = []
        for event in events:
            agent = parse(event.user_agent or '')
            data.append({
                'id': str(event.id),
                'event_type': event.event_type,
                'status': event.status,
                'ip_address': event.ip_address,
                'country_code': event.country_code,
                'device': f'{agent.device.family} · {agent.os.family} · {agent.browser.family}',
                'reason': event.reason,
                'new_device': bool(event.metadata.get('new_device')),
                'new_ip': bool(event.metadata.get('new_ip')),
                'new_country': bool(event.metadata.get('new_country')),
                'created_at': event.created_at,
            })
        return api_response(data={'history': data})


class SessionListView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user).order_by('-created_at')[:100]
        data = [{
            'id': str(item.id),
            'status': item.status,
            'ip_address': item.ip_address,
            'device': item.device,
            'country_code': item.country_code,
            'created_at': item.created_at,
            'last_activity_at': item.last_activity_at,
            'expires_at': item.expires_at,
            'revoked_at': item.revoked_at,
            'revoke_reason': item.revoke_reason,
        } for item in sessions]
        return api_response(data={'sessions': data})


class SessionRevokeView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = UserSession.objects.filter(pk=session_id, user=request.user).first()
        if not session:
            return api_response(message='Session not found.', success=False, status=404)
        SessionService.revoke(session=session, reason='user_revoked')
        return api_response(data={'revoked': True}, message='Session revoked.')
