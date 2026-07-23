#!/usr/bin/env python3
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    '.env',
    '.env.example',
    'manage.py',
    'config/settings.py',
    'config/urls.py',
    'config/admin.py',
    'config/authentication/models.py',
    'config/authentication/serializers.py',
    'config/authentication/tests.py',
    'config/common/email_service.py',
    'config/common/storage.py',
    'app/client_portal/models.py',
    'app/client_portal/services.py',
    'app/client_portal/urls.py',
    'app/client_portal/tests.py',
    'frontend/package.json',
    'frontend/src/proxy.ts',
    'frontend/Dockerfile',
    'docker-compose.yml',
    'Dockerfile',
]

errors = []
for relative in REQUIRED:
    if not (ROOT / relative).exists():
        errors.append(f'Missing: {relative}')

for path in ROOT.rglob('*.py'):
    if '__pycache__' in path.parts:
        continue
    try:
        ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError as exc:
        errors.append(f'Syntax error: {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}')

compose_text = (ROOT / 'docker-compose.yml').read_text(encoding='utf-8')
expected_services = {
    'veloma-api',
    'veloma-postgres',
    'veloma-redis',
    'veloma-celery',
    'veloma-celery-beat',
    'veloma-minio',
    'veloma-minio-init',
    'veloma-clamav',
    'veloma-app',
}
service_block = compose_text.split('services:', 1)[1].split('\nvolumes:', 1)[0]
found_services = set(re.findall(r'^  (veloma-[a-z0-9-]+):\s*$', service_block, flags=re.MULTILINE))
missing_services = expected_services - found_services
if missing_services:
    errors.append(f'Missing Docker services: {sorted(missing_services)}')
if '\nnetworks:' in compose_text:
    errors.append('Custom Docker networks are not allowed for the Coolify Compose resource.')

env_text = (ROOT / '.env').read_text(encoding='utf-8')
required_env = {
    'DJANGO_SECRET_KEY', 'POSTGRES_PASSWORD', 'REDIS_PASSWORD',
    'CREDENTIALS_ENCRYPTION_KEY', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY',
    'DJANGO_SUPERUSER_USERNAME', 'DJANGO_SUPERUSER_PASSWORD',
}
found_env = {
    line.split('=', 1)[0].strip()
    for line in env_text.splitlines()
    if line and not line.startswith('#') and '=' in line
}
missing_env = required_env - found_env
if missing_env:
    errors.append(f'Missing .env keys: {sorted(missing_env)}')

html = {path.stem for path in (ROOT / 'templates/emails').glob('*.html')}
text = {path.stem for path in (ROOT / 'templates/emails').glob('*.txt')}
if html != text:
    errors.append(f'Email template pairs differ. HTML-only={sorted(html-text)} TXT-only={sorted(text-html)}')

if errors:
    print('\n'.join(f'[ERROR] {item}' for item in errors))
    raise SystemExit(1)

print('[OK] Static project validation completed.')
print(f'[OK] Email template pairs: {len(html)}')
print(f"[OK] Docker services: {', '.join(sorted(found_services))}")
print(f'[OK] Environment keys: {len(found_env)}')
