import hashlib
import ipaddress

from django.conf import settings
from user_agents import parse


class RequestContext:
    @staticmethod
    def _is_trusted_proxy(value):
        if not value:
            return False
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            return False
        for item in settings.TRUSTED_PROXY_IPS:
            try:
                network = ipaddress.ip_network(item, strict=False)
            except ValueError:
                continue
            if address in network:
                return True
        return False

    @classmethod
    def ip(cls, request):
        if request is None:
            return None
        remote = request.META.get('REMOTE_ADDR')
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if settings.TRUST_PROXY_HEADERS and forwarded and cls._is_trusted_proxy(remote):
            values = [item.strip() for item in forwarded.split(',') if item.strip()]
            if values:
                try:
                    return str(ipaddress.ip_address(values[0]))
                except ValueError:
                    pass
        try:
            return str(ipaddress.ip_address(remote)) if remote else None
        except ValueError:
            return None

    @staticmethod
    def user_agent(request):
        if request is None:
            return ''
        return request.META.get('HTTP_USER_AGENT', '')[:2000]

    @classmethod
    def device(cls, request):
        value = parse(cls.user_agent(request))
        return f'{value.device.family} · {value.os.family} · {value.browser.family}'[:255]

    @classmethod
    def fingerprint(cls, request):
        raw = f'{cls.user_agent(request)}|{cls.device(request)}'
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()
