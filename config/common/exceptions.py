import logging
import uuid

from rest_framework.views import exception_handler

logger = logging.getLogger('config.common.exceptions')


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    view = context.get('view')
    request = context.get('request')
    source = view.__class__.__module__ if view else 'unknown'
    path = getattr(request, 'path', '?')
    method = getattr(request, 'method', '?')
    user = getattr(getattr(request, 'user', None), 'pk', None)

    # An error DRF does not know how to turn into a response is a real fault:
    # log the full traceback with a correlation id so it can be found later.
    if response is None:
        incident = uuid.uuid4().hex[:12]
        logger.error(
            '[%s] Unhandled %s at %s %s (user=%s, source=%s)',
            incident, exc.__class__.__name__, method, path, user, source,
            exc_info=exc,
        )
        return None

    detail = response.data
    if response.status_code >= 500:
        logger.error('%s %s -> %s (user=%s, source=%s): %s', method, path, response.status_code, user, source, detail)
    else:
        # 4xx: the reason (validation message) is logged so the cause is never a mystery.
        logger.warning('%s %s -> %s (user=%s, source=%s): %s', method, path, response.status_code, user, source, detail)

    response.data = {
        'success': False,
        'message': 'Request validation failed.' if response.status_code < 500 else 'Internal server error.',
        'errors': detail,
    }
    return response
