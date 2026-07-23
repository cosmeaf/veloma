from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class CredentialCipher:
    @staticmethod
    def _fernet():
        key = settings.CREDENTIALS_ENCRYPTION_KEY
        if not key:
            raise RuntimeError('CREDENTIALS_ENCRYPTION_KEY is required to store encrypted configuration secrets.')
        try:
            return Fernet(key.encode('utf-8'))
        except (TypeError, ValueError) as exc:
            raise RuntimeError('CREDENTIALS_ENCRYPTION_KEY must be a valid Fernet key.') from exc

    @classmethod
    def encrypt(cls, value: str) -> str:
        if not value:
            return ''
        return cls._fernet().encrypt(value.encode('utf-8')).decode('utf-8')

    @classmethod
    def decrypt(cls, value: str) -> str:
        if not value:
            return ''
        try:
            return cls._fernet().decrypt(value.encode('utf-8')).decode('utf-8')
        except InvalidToken as exc:
            raise RuntimeError('Unable to decrypt the configured credential.') from exc
