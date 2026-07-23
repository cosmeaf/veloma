import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='AuthenticationActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(db_index=True, max_length=64)),
                ('status', models.CharField(choices=[('success', 'Success'), ('failed', 'Failed'), ('blocked', 'Blocked')], db_index=True, max_length=16)),
                ('email', models.EmailField(blank=True, db_index=True, max_length=254)),
                ('ip_address', models.GenericIPAddressField(blank=True, db_index=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('country_code', models.CharField(blank=True, db_index=True, max_length=8)),
                ('reason', models.CharField(blank=True, max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='veloma_auth_activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name_plural': 'Authentication activity', 'db_table': 'authentication_activity', 'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='SecurityEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(db_index=True, max_length=64)),
                ('severity', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('critical', 'Critical')], db_index=True, max_length=16)),
                ('ip_address', models.GenericIPAddressField(blank=True, db_index=True, null=True)),
                ('summary', models.CharField(max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('resolved', models.BooleanField(db_index=True, default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='veloma_security_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'authentication_security_event', 'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='OTPChallenge',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('purpose', models.CharField(choices=[('register', 'Register'), ('login', 'Login'), ('password_reset', 'Password reset')], db_index=True, max_length=32)),
                ('code_hash', models.CharField(editable=False, max_length=255)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('max_attempts', models.PositiveSmallIntegerField(default=5)),
                ('resend_count', models.PositiveSmallIntegerField(default=0)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('blocked_at', models.DateTimeField(blank=True, null=True)),
                ('request_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='veloma_otp_challenges', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'authentication_otp_challenge', 'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('refresh_jti', models.CharField(db_index=True, max_length=255, unique=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('revoked', 'Revoked'), ('expired', 'Expired')], db_index=True, default='active', max_length=16)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('device', models.CharField(blank=True, max_length=255)),
                ('device_fingerprint', models.CharField(blank=True, db_index=True, max_length=64)),
                ('country_code', models.CharField(blank=True, max_length=8)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('last_activity_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('revoke_reason', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='veloma_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'authentication_user_session', 'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='AccessBlock',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('block_type', models.CharField(choices=[('user', 'User'), ('ip', 'IP address'), ('country', 'Country'), ('user_agent', 'User agent')], db_index=True, max_length=16)),
                ('value', models.CharField(blank=True, db_index=True, max_length=512)),
                ('reason', models.CharField(max_length=255)),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('automatic', models.BooleanField(default=False)),
                ('starts_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='veloma_access_blocks', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'authentication_access_block', 'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='PasswordResetGrant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token_hash', models.CharField(editable=False, max_length=64, unique=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('request_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('otp_challenge', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='reset_grant', to='veloma_authentication.otpchallenge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='veloma_password_reset_grants', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'authentication_password_reset_grant', 'ordering': ('-created_at',)},
        ),
        migrations.AddIndex(
            model_name='otpchallenge',
            index=models.Index(fields=['user', 'purpose', 'created_at'], name='auth_otp_usr_purp_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['user', 'status', 'created_at'], name='auth_sess_usr_stat_idx'),
        ),
    ]
