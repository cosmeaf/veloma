from datetime import timedelta
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=False)

APP_VERSION = '1.0.0'


def env(name, default=None, *, required=False):
    value = os.getenv(name, default)
    if required and (value is None or value == ''):
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


def env_bool(name, default=False):
    return str(env(name, str(default))).strip().lower() in {'1', 'true', 'yes', 'on'}


def env_int(name, default):
    return int(env(name, default))


def env_list(name, default=''):
    value = env(name, default)
    return [item.strip() for item in str(value).split(',') if item.strip()]


SECRET_KEY = env('DJANGO_SECRET_KEY', 'unsafe-local-development-key-change-me')
DEBUG = env_bool('DJANGO_DEBUG', False)
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,veloma-api')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS', 'http://localhost:8000')
CORS_ALLOWED_ORIGINS = env_list('DJANGO_CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'storages',
    'config.authentication.apps.AuthenticationConfig',
    'config.common.apps.CommonConfig',
    'config.iam.apps.IamConfig',
    'config.security.apps.SecurityConfig',
    'app.client_portal.apps.ClientPortalConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.security.middleware.SecurityContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'config.security.headers.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

DATABASE_ENGINE = env('DATABASE_ENGINE', 'postgresql').strip().lower()
if DATABASE_ENGINE in {'sqlite', 'sqlite3'}:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': env('DATABASE_SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB', 'veloma'),
            'USER': env('POSTGRES_USER', 'veloma'),
            'PASSWORD': env('POSTGRES_PASSWORD', 'veloma-local-only'),
            'HOST': env('POSTGRES_HOST', 'localhost'),
            'PORT': env('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': env_int('POSTGRES_CONN_MAX_AGE', 60),
            'CONN_HEALTH_CHECKS': True,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = env('DJANGO_LANGUAGE_CODE', 'pt-pt')
TIME_ZONE = env('DJANGO_TIME_ZONE', 'Europe/Lisbon')
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

MINIO_ENABLED = env_bool('MINIO_ENABLED', False)
STORAGES = {
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    'default': {
        'BACKEND': 'storages.backends.s3.S3Storage' if MINIO_ENABLED else 'django.core.files.storage.FileSystemStorage',
    },
}

if MINIO_ENABLED:
    AWS_ACCESS_KEY_ID = env('MINIO_ACCESS_KEY', required=True)
    AWS_SECRET_ACCESS_KEY = env('MINIO_SECRET_KEY', required=True)
    AWS_STORAGE_BUCKET_NAME = env('MINIO_BUCKET', 'veloma')
    AWS_S3_ENDPOINT_URL = env('MINIO_ENDPOINT', 'http://veloma-minio:9000')
    AWS_S3_REGION_NAME = env('MINIO_REGION', 'us-east-1')
    AWS_S3_ADDRESSING_STYLE = 'path'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = env_bool('MINIO_QUERYSTRING_AUTH', True)
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_USE_SSL = env_bool('MINIO_USE_SSL', False)
    AWS_S3_VERIFY = env_bool('MINIO_VERIFY_SSL', False)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('config.authentication.jwt.SessionJWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'EXCEPTION_HANDLER': 'config.common.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env_int('JWT_ACCESS_MINUTES', 15)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env_int('JWT_REFRESH_DAYS', 7)),
    'ROTATE_REFRESH_TOKENS': env_bool('JWT_ROTATE_REFRESH_TOKENS', True),
    'BLACKLIST_AFTER_ROTATION': env_bool('JWT_BLACKLIST_AFTER_ROTATION', True),
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'LEEWAY': env_int('JWT_LEEWAY_SECONDS', 0),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Veloma Core API',
    'DESCRIPTION': 'Authentication, native Django RBAC, sessions, security, email and audit foundation.',
    'VERSION': APP_VERSION,
    'SERVE_INCLUDE_SCHEMA': False,
}

CELERY_BROKER_URL = env('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_TASK_ALWAYS_EAGER = env_bool('CELERY_TASK_ALWAYS_EAGER', False)
CELERY_TASK_EAGER_PROPAGATES = env_bool('CELERY_TASK_EAGER_PROPAGATES', True)
CELERY_TASK_TIME_LIMIT = env_int('CELERY_TASK_TIME_LIMIT', 300)
CELERY_TASK_SOFT_TIME_LIMIT = env_int('CELERY_TASK_SOFT_TIME_LIMIT', 270)
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-authentication-records': {
        'task': 'config.authentication.tasks.cleanup_expired_authentication_records',
        'schedule': float(env('AUTH_CLEANUP_INTERVAL_SECONDS', '3600')),
    },
    'expire-client-invitations': {
        'task': 'app.client_portal.tasks.expire_invitations',
        'schedule': float(env('INVITATION_EXPIRE_INTERVAL_SECONDS', '3600')),
    },
    'send-invitation-reminders': {
        'task': 'app.client_portal.tasks.send_invitation_reminders',
        'schedule': float(env('INVITATION_REMINDER_INTERVAL_SECONDS', '86400')),
    },
    'alert-overdue-protocols': {
        'task': 'app.client_portal.tasks.alert_overdue_protocols',
        'schedule': float(env('PROTOCOL_OVERDUE_INTERVAL_SECONDS', '86400')),
    },
    'cleanup-quarantined-documents': {
        'task': 'app.client_portal.tasks.cleanup_quarantined_documents',
        'schedule': float(env('QUARANTINE_CLEANUP_INTERVAL_SECONDS', '86400')),
    },
    'retry-failed-document-scans': {
        'task': 'app.client_portal.tasks.retry_failed_scans',
        'schedule': float(env('SCAN_RETRY_INTERVAL_SECONDS', '3600')),
    },
}

CACHE_URL = env('CACHE_URL', 'redis://localhost:6379/2')
if env_bool('USE_LOCAL_MEMORY_CACHE', False):
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': CACHE_URL,
        }
    }

CREDENTIALS_ENCRYPTION_KEY = env(
    'CREDENTIALS_ENCRYPTION_KEY',
    env('EMAIL_CREDENTIALS_ENCRYPTION_KEY', ''),
)
EMAIL_CREDENTIALS_ENCRYPTION_KEY = CREDENTIALS_ENCRYPTION_KEY
FRONTEND_URL = env('FRONTEND_URL', 'https://veloma.app').rstrip('/')
# The default administrator account can never be deactivated, archived or deleted.
PROTECTED_ADMIN_EMAIL = env('PROTECTED_ADMIN_EMAIL', env('DJANGO_SUPERUSER_EMAIL', ''))
# Base URL for the admin password-reset link sent by email.
FRONTEND_ADMIN_URL = env('FRONTEND_ADMIN_URL', 'https://api.veloma.app').rstrip('/')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@veloma.local')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

TRUST_PROXY_HEADERS = env_bool('TRUST_PROXY_HEADERS', True)
TRUSTED_PROXY_IPS = env_list(
    'TRUSTED_PROXY_IPS',
    '127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16',
)

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = env('SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SAMESITE = env('CSRF_COOKIE_SAMESITE', 'Lax')
SESSION_COOKIE_NAME = env('SESSION_COOKIE_NAME', 'veloma_admin_sessionid')
CSRF_COOKIE_NAME = env('CSRF_COOKIE_NAME', 'veloma_csrftoken')
USE_X_FORWARDED_HOST = TRUST_PROXY_HEADERS
if TRUST_PROXY_HEADERS:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    SECURE_HSTS_SECONDS = env_int('DJANGO_HSTS_SECONDS', 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DATA_UPLOAD_MAX_MEMORY_SIZE = env_int('DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)
FILE_UPLOAD_MAX_MEMORY_SIZE = env_int('FILE_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env('DJANGO_LOG_LEVEL', 'INFO'),
    },
}
