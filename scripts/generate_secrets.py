#!/usr/bin/env python3
import base64
import os
import secrets

print(f'DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}')
print(f'POSTGRES_PASSWORD={secrets.token_urlsafe(32)}')
print(f'REDIS_PASSWORD={secrets.token_urlsafe(32)}')
print(f'CREDENTIALS_ENCRYPTION_KEY={base64.urlsafe_b64encode(os.urandom(32)).decode()}')
print(f'MINIO_ACCESS_KEY=veloma-{secrets.token_hex(8)}')
print(f'MINIO_SECRET_KEY={secrets.token_urlsafe(32)}')
print(f'DJANGO_SUPERUSER_PASSWORD={secrets.token_urlsafe(24)}')
