"""Response hardening: strip fingerprinting headers and add security ones.

Runs last so it sees the final response. Anything that would tell an attacker
which framework or version is serving the request is removed; defensive headers
are added.
"""

REMOVE_HEADERS = (
    'Server',
    'X-Powered-By',
    'X-AspNet-Version',
    'X-Runtime',
)

# Conservative CSP for the API/Admin. The Admin needs inline styles/scripts and
# the Swagger UI needs its bundled assets, so 'unsafe-inline' is kept for those
# document responses only; JSON responses carry the strict default.
CSP_API = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'self'"
)
CSP_DOCUMENT = (
    "default-src 'self'; "
    "img-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self' 'unsafe-inline'; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'self'"
)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        for header in REMOVE_HEADERS:
            if header in response:
                del response[header]

        content_type = response.get('Content-Type', '')
        is_document = 'text/html' in content_type

        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'same-origin')
        response.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.setdefault('X-Frame-Options', 'DENY')
        response.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        response.setdefault('Content-Security-Policy', CSP_DOCUMENT if is_document else CSP_API)

        return response
