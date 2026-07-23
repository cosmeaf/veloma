import logging

from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class StorageService:
    """Single entry point for object storage.

    Views, serializers and tasks must never talk to the S3/MinIO SDK directly.
    Backed by `django.core.files.storage.default_storage`, which is the MinIO
    S3 backend when `MINIO_ENABLED` is on and the local filesystem otherwise.
    """

    @staticmethod
    def _storage():
        return default_storage

    @classmethod
    def upload(cls, *, key, content):
        """Stores a file object and returns the effective key."""
        storage = cls._storage()
        if storage.exists(key):
            storage.delete(key)
        return storage.save(key, content)

    @classmethod
    def exists(cls, key):
        return cls._storage().exists(key)

    @classmethod
    def open(cls, key, mode='rb'):
        return cls._storage().open(key, mode)

    @classmethod
    def size(cls, key):
        try:
            return cls._storage().size(key)
        except (NotImplementedError, OSError):
            return 0

    @classmethod
    def delete(cls, key):
        """Removes an object. Only used for quarantine and temporary files."""
        storage = cls._storage()
        if storage.exists(key):
            storage.delete(key)
            return True
        return False

    @classmethod
    def copy(cls, *, source_key, target_key):
        storage = cls._storage()
        with storage.open(source_key, 'rb') as handle:
            return storage.save(target_key, handle)

    @classmethod
    def download_url(cls, key, *, expires_in=300):
        """Short-lived signed URL. Never store or reuse the returned value."""
        storage = cls._storage()
        try:
            return storage.url(key, expire=expires_in)
        except TypeError:
            # The filesystem backend has no expiring URLs.
            return storage.url(key)

    @classmethod
    def metadata(cls, key):
        storage = cls._storage()
        if not storage.exists(key):
            return {}
        data = {'key': key, 'size': cls.size(key)}
        try:
            data['modified_at'] = storage.get_modified_time(key)
        except (NotImplementedError, OSError):
            pass
        return data

    @staticmethod
    def is_object_storage():
        return bool(getattr(settings, 'MINIO_ENABLED', False))
