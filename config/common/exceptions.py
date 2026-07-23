from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    detail = response.data
    response.data = {
        'success': False,
        'message': 'Request validation failed.' if response.status_code < 500 else 'Internal server error.',
        'errors': detail,
    }
    return response
