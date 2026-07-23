"""Password recovery for Django Admin accounts.

Admin accounts are refused by the JWT API on purpose, so they cannot use the
portal recovery flow. This wires Django's native password-reset views into the
Admin, but sends the email through the project's configurable EmailService
instead of Django's EMAIL_BACKEND, so the same SMTP vendor is used everywhere.
"""

import logging

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path, reverse_lazy

logger = logging.getLogger(__name__)


class AdminPasswordResetForm(PasswordResetForm):
    """Restricts recovery to staff accounts and sends via EmailService."""

    def get_users(self, email):
        for user in super().get_users(email):
            # Only administrators recover through /admin/.
            if user.is_staff or user.is_superuser:
                yield user

    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        from config.common.email_service import EmailService

        # `context['user']` is not JSON-serialisable for the async path; pass the
        # primitives the templates need.
        payload = {
            'admin_name': context['user'].get_full_name() or context['user'].get_username(),
            'email': to_email,
            'reset_url': f"{settings.FRONTEND_ADMIN_URL}/admin/reset/{context['uid']}/{context['token']}/",
            'event_time': context.get('event_time'),
        }
        try:
            EmailService.send_by_purpose(
                purpose='admin_password_reset',
                recipients=[to_email],
                context=payload,
                mode='sync',
            )
        except Exception:
            logger.exception('Admin password reset email failed for %s', to_email)
            raise


class AdminPasswordResetView(PasswordResetView):
    form_class = AdminPasswordResetForm
    template_name = 'admin/password_reset_form.html'
    success_url = reverse_lazy('admin_password_reset_done')
    # send_mail on the form handles delivery; these are unused but required.
    email_template_name = 'admin/password_reset_email.txt'
    subject_template_name = 'admin/password_reset_subject.txt'


class AdminPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'admin/password_reset_done.html'


class AdminPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'admin/password_reset_confirm.html'
    success_url = reverse_lazy('admin_password_reset_complete')


class AdminPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'admin/password_reset_complete.html'


admin_recovery_urlpatterns = [
    path('password-reset/', AdminPasswordResetView.as_view(), name='admin_password_reset'),
    path('password-reset/done/', AdminPasswordResetDoneView.as_view(), name='admin_password_reset_done'),
    path('reset/<uidb64>/<token>/', AdminPasswordResetConfirmView.as_view(), name='admin_password_reset_confirm'),
    path('reset/done/', AdminPasswordResetCompleteView.as_view(), name='admin_password_reset_complete'),
]
