from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from config.authentication.models import (
    AccountLifecycle,
    OTPChallenge,
    PasswordResetGrant,
    UserSession,
)
from config.authentication.services import AccountLifecycleService
from config.common.models import AuthenticationSettings, EmailTemplate, SecuritySettings


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class AuthenticationCoreTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_veloma', verbosity=0)
        EmailTemplate.objects.update(delivery_mode='sync')
        security = SecuritySettings.load()
        security.api_rate_limit_enabled = False
        security.save()

    @patch('config.authentication.services.OTPService._code', return_value='123456')
    def test_register_uses_native_user_and_verifies_otp(self, _mock_code):
        # The client portal ships with public registration disabled; this test
        # covers the endpoint itself, so it opts back in explicitly.
        auth_settings = AuthenticationSettings.load()
        auth_settings.registration_enabled = True
        auth_settings.save()

        response = self.client.post('/api/auth/register/', {
            'first_name': 'Alex',
            'last_name': 'Silva',
            'email': 'ALEX@EXAMPLE.COM',
            'password': 'StrongPassword@123',
            'password2': 'StrongPassword@123',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='alex@example.com')
        self.assertEqual(user.email, 'alex@example.com')
        self.assertFalse(user.is_active)
        self.assertTrue(user.groups.filter(name='USER').exists())
        challenge = OTPChallenge.objects.get(pk=response.data['data']['challenge_id'])
        self.assertTrue(challenge.matches('123456'))
        self.assertNotEqual(challenge.code_hash, '123456')

        verified = self.client.post('/api/auth/otp/verify/', {
            'challenge_id': str(challenge.id),
            'code': '123456',
        }, format='json')
        self.assertEqual(verified.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_admin_account_cannot_login_to_frontend_api(self):
        User.objects.create_superuser(
            username='admin-test@example.com',
            email='admin-test@example.com',
            password='StrongPassword@123',
        )
        response = self.client.post('/api/auth/login/', {
            'email': 'admin-test@example.com',
            'password': 'StrongPassword@123',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Django administrators', str(response.data))

    def _active_user(self, email='user@example.com'):
        user = User.objects.create_user(
            username=email,
            email=email,
            password='StrongPassword@123',
            first_name='Core',
            last_name='User',
            is_active=True,
        )
        user.groups.add(Group.objects.get(name='USER'))
        return user

    def test_login_creates_revocable_session(self):
        user = self._active_user()
        response = self.client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'StrongPassword@123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.data['data']
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        session = UserSession.objects.get(pk=data['session_id'])
        self.assertEqual(session.user, user)
        self.assertEqual(session.status, UserSession.STATUS_ACTIVE)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, 200)
        logout = self.client.post('/api/auth/logout/', {'refresh': data['refresh']}, format='json')
        self.assertEqual(logout.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.status, UserSession.STATUS_REVOKED)

    @patch('config.authentication.services.OTPService._code', return_value='654321')
    def test_password_reset_grant_is_one_time(self, _mock_code):
        user = self._active_user('reset@example.com')
        recovery = self.client.post('/api/auth/password/recovery/', {'email': user.email}, format='json')
        self.assertEqual(recovery.status_code, 200)
        challenge_id = recovery.data['data']['challenge_id']

        verified = self.client.post('/api/auth/otp/verify/', {
            'challenge_id': challenge_id,
            'code': '654321',
        }, format='json')
        self.assertEqual(verified.status_code, 200)
        grant = verified.data['data']
        payload = {
            'uid': grant['uid'],
            'reset_token': grant['reset_token'],
            'password': 'NewStrongPassword@123',
            'password2': 'NewStrongPassword@123',
        }
        reset = self.client.post('/api/auth/password/reset/', payload, format='json')
        self.assertEqual(reset.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewStrongPassword@123'))

        reused = self.client.post('/api/auth/password/reset/', payload, format='json')
        self.assertEqual(reused.status_code, 400)

    def test_archived_account_cannot_authenticate(self):
        user = self._active_user('archived@example.com')
        admin = User.objects.create_superuser(
            username='lifecycle-admin@example.com',
            email='lifecycle-admin@example.com',
            password='StrongPassword@123',
        )
        AccountLifecycleService.archive(user=user, performed_by=admin, reason='Cliente encerrado')
        response = self.client.post('/api/auth/login/', {
            'email': user.email,
            'password': 'StrongPassword@123',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            user.veloma_auth_activities.filter(event_type='login', reason='account_archived').exists()
        )

    def test_failed_login_creates_automatic_blocks(self):
        user = self._active_user('blocked@example.com')
        settings = SecuritySettings.load()
        settings.login_max_attempts = 2
        settings.save()
        for _ in range(2):
            self.client.post('/api/auth/login/', {
                'email': user.email,
                'password': 'wrong-password',
            }, format='json', REMOTE_ADDR='198.51.100.10')
        self.assertTrue(user.veloma_access_blocks.filter(active=True, automatic=True).exists())


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class AccountLifecycleTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_veloma', verbosity=0)
        EmailTemplate.objects.update(delivery_mode='sync')
        security = SecuritySettings.load()
        security.api_rate_limit_enabled = False
        security.save()

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='lifecycle@example.com',
            email='lifecycle@example.com',
            password='StrongPassword@123',
        )
        self.user = User.objects.create_user(
            username='client@example.com',
            email='client@example.com',
            password='StrongPassword@123',
            is_active=True,
        )
        self.user.groups.add(Group.objects.get(name='USER'))

    def _login(self):
        response = self.client.post('/api/auth/login/', {
            'email': self.user.email,
            'password': 'StrongPassword@123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        return response.data['data']

    def test_deactivate_revokes_sessions_and_blocks_login(self):
        tokens = self._login()
        OTPChallenge.objects.create(
            user=self.user,
            purpose=OTPChallenge.PURPOSE_PASSWORD_RESET,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        AccountLifecycleService.deactivate(
            user=self.user,
            performed_by=self.admin,
            reason='Contrato suspenso',
        )

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        lifecycle = AccountLifecycle.objects.get(user=self.user)
        self.assertEqual(lifecycle.state, AccountLifecycle.STATE_DEACTIVATED)
        self.assertEqual(lifecycle.deactivated_by, self.admin)
        self.assertEqual(lifecycle.deactivation_reason, 'Contrato suspenso')

        self.assertFalse(
            UserSession.objects.filter(user=self.user, status=UserSession.STATUS_ACTIVE).exists()
        )
        self.assertFalse(
            OTPChallenge.objects.filter(user=self.user, blocked_at__isnull=True).exists()
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        self.client.credentials()

        refused = self.client.post('/api/auth/login/', {
            'email': self.user.email,
            'password': 'StrongPassword@123',
        }, format='json')
        self.assertEqual(refused.status_code, 400)

    def test_archive_is_logical_and_preserves_history(self):
        self._login()
        activity_count = self.user.veloma_auth_activities.count()

        AccountLifecycleService.archive(
            user=self.user,
            performed_by=self.admin,
            reason='Cliente encerrado',
        )

        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        lifecycle = AccountLifecycle.objects.get(user=self.user)
        self.assertEqual(lifecycle.state, AccountLifecycle.STATE_ARCHIVED)
        self.assertEqual(lifecycle.archived_by, self.admin)
        self.assertGreater(self.user.veloma_auth_activities.count(), activity_count)
        self.assertTrue(
            self.user.veloma_security_events.filter(event_type='account_archived').exists()
        )
        self.assertTrue(
            UserSession.objects.filter(user=self.user, status=UserSession.STATUS_REVOKED).exists()
        )

    def test_reactivate_restores_access(self):
        AccountLifecycleService.deactivate(user=self.user, performed_by=self.admin, reason='Pausa')
        AccountLifecycleService.reactivate(user=self.user, performed_by=self.admin)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        lifecycle = AccountLifecycle.objects.get(user=self.user)
        self.assertEqual(lifecycle.state, AccountLifecycle.STATE_ACTIVE)
        self.assertIsNotNone(lifecycle.last_reactivated_at)
        self._login()

    def test_restore_leaves_the_account_deactivated(self):
        AccountLifecycleService.archive(user=self.user, performed_by=self.admin, reason='Encerrado')
        AccountLifecycleService.restore(user=self.user, performed_by=self.admin)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        lifecycle = AccountLifecycle.objects.get(user=self.user)
        self.assertEqual(lifecycle.state, AccountLifecycle.STATE_DEACTIVATED)

        AccountLifecycleService.reactivate(user=self.user, performed_by=self.admin)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_archived_account_requires_restore_before_reactivation(self):
        AccountLifecycleService.archive(user=self.user, performed_by=self.admin)
        with self.assertRaises(ValueError):
            AccountLifecycleService.reactivate(user=self.user, performed_by=self.admin)
        with self.assertRaises(ValueError):
            AccountLifecycleService.deactivate(user=self.user, performed_by=self.admin)

    def test_administrator_cannot_change_own_lifecycle(self):
        with self.assertRaises(ValueError):
            AccountLifecycleService.deactivate(user=self.admin, performed_by=self.admin)
        with self.assertRaises(ValueError):
            AccountLifecycleService.archive(user=self.admin, performed_by=self.admin)

    def test_pending_password_reset_grant_is_revoked(self):
        challenge = OTPChallenge.objects.create(
            user=self.user,
            purpose=OTPChallenge.PURPOSE_PASSWORD_RESET,
            expires_at=timezone.now() + timedelta(minutes=5),
            used_at=timezone.now(),
        )
        grant = PasswordResetGrant.objects.create(
            user=self.user,
            otp_challenge=challenge,
            token_hash='a' * 64,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        AccountLifecycleService.deactivate(user=self.user, performed_by=self.admin)

        grant.refresh_from_db()
        self.assertEqual(grant.status, 'revoked')
