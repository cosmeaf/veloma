from django.urls import path

from .views import (
    LoginView,
    LogoutAllView,
    LogoutView,
    MeView,
    OTPResendView,
    OTPVerifyView,
    PasswordChangeView,
    PasswordResetView,
    RecoveryView,
    RegisterView,
    SessionListView,
    SessionRevokeView,
    VelomaTokenRefreshView,
)

app_name = 'authentication'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('otp/resend/', OTPResendView.as_view(), name='otp-resend'),
    path('password/recovery/', RecoveryView.as_view(), name='password-recovery'),
    path('password/reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('token/refresh/', VelomaTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout/all/', LogoutAllView.as_view(), name='logout-all'),
    path('me/', MeView.as_view(), name='me'),
    path('sessions/', SessionListView.as_view(), name='sessions'),
    path('sessions/<uuid:session_id>/revoke/', SessionRevokeView.as_view(), name='session-revoke'),
]
