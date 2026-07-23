import hashlib
import ipaddress

import requests
from django.core.cache import cache

from config.common.crypto import CredentialCipher
from config.common.models import SecuritySettings


class IPIntelligenceService:
    @staticmethod
    def lookup(ip_address):
        settings = SecuritySettings.load()
        if not settings.ip_intelligence_enabled or not settings.ip_intelligence_url or not ip_address:
            return {}
        try:
            address = ipaddress.ip_address(ip_address)
            if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
                return {}
        except ValueError:
            return {}
        cache_key = 'veloma:ipintel:' + hashlib.sha256(ip_address.encode('utf-8')).hexdigest()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        url = settings.ip_intelligence_url.format(ip=ip_address)
        token = CredentialCipher.decrypt(settings.encrypted_ip_intelligence_token) if settings.encrypted_ip_intelligence_token else ''
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        response = requests.get(url, headers=headers, timeout=settings.ip_intelligence_timeout_seconds)
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, timeout=86400)
        return data
