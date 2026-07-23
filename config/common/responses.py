from rest_framework.response import Response


def api_response(*, data=None, message='', status=200, success=True):
    payload = {'success': success, 'message': message}
    if data is not None:
        payload['data'] = data
    return Response(payload, status=status)
