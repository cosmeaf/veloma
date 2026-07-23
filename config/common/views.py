from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


def health(request):
    checks = {'database': 'ok', 'cache': 'ok'}
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        checks['database'] = 'unavailable'
    try:
        cache.set('veloma:health', 'ok', timeout=5)
        if cache.get('veloma:health') != 'ok':
            raise RuntimeError('Cache read failed.')
    except Exception:
        checks['cache'] = 'unavailable'
    healthy = all(value == 'ok' for value in checks.values())
    return JsonResponse({
        'status': 'ok' if healthy else 'degraded',
        **checks,
        'time': timezone.now().isoformat(),
    }, status=200 if healthy else 503)
