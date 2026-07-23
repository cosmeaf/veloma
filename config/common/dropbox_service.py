import logging

logger = logging.getLogger(__name__)


class DropboxService:
    """Uploads copies of files to the company Dropbox.

    Two independent destinations, each with its own base path and toggle:

    - ``uploads`` — mirror of approved (clean-scanned) document versions.
    - ``rgpd`` — legal consent proofs (terms-acceptance PDFs), retained for
      ten years. Never pruned.

    MinIO remains the source of truth; Dropbox is a mirror / long-term archive.
    Configuration (credentials, paths, toggles) lives in the ``DropboxSettings``
    singleton, edited in the Django Admin — never in settings.py. Secrets are
    Fernet-encrypted, like SMTP passwords.

    The service fails **open**: when Dropbox is not configured or the API errors,
    it logs and returns ``None`` so the request/task is never broken. A Celery
    task is responsible for retrying.
    """

    PURPOSE_UPLOADS = 'uploads'
    PURPOSE_RGPD = 'rgpd'

    @staticmethod
    def _settings():
        from config.common.models import DropboxSettings

        return DropboxSettings.load()

    @classmethod
    def is_enabled(cls, purpose=None):
        settings = cls._settings()
        if not settings.is_configured():
            return False
        if purpose == cls.PURPOSE_UPLOADS:
            return settings.mirror_uploads
        if purpose == cls.PURPOSE_RGPD:
            return settings.mirror_rgpd
        return True

    @staticmethod
    def _base_path(settings, purpose):
        mapping = {
            DropboxService.PURPOSE_UPLOADS: settings.uploads_path,
            DropboxService.PURPOSE_RGPD: settings.rgpd_path,
        }
        return (mapping.get(purpose) or '').rstrip('/')

    @staticmethod
    def _client(settings):
        # Imported lazily so the dependency is optional at runtime.
        import dropbox

        return dropbox.Dropbox(
            app_key=settings.app_key,
            app_secret=settings.app_secret(),
            oauth2_refresh_token=settings.refresh_token(),
            timeout=settings.timeout_seconds,
        )

    @classmethod
    def upload_bytes(cls, *, purpose, relative_path, content):
        """Uploads ``content`` (bytes) to ``<base>/<relative_path>``.

        Returns the full Dropbox path on success, ``None`` on any failure.
        """
        if not cls.is_enabled(purpose):
            logger.info('Dropbox mirror off for purpose=%s; skipping path=%s', purpose, relative_path)
            return None

        import dropbox

        settings = cls._settings()
        base = cls._base_path(settings, purpose)
        clean = relative_path.strip('/').replace('//', '/')
        full_path = f'{base}/{clean}' if base else f'/{clean}'
        try:
            client = cls._client(settings)
            client.files_upload(content, full_path, mode=dropbox.files.WriteMode.overwrite, mute=True)
            logger.info('Mirrored to Dropbox. purpose=%s path=%s bytes=%s', purpose, full_path, len(content))
            return full_path
        except Exception:  # noqa: BLE001 — never let a mirror failure surface.
            logger.exception('Dropbox upload failed. purpose=%s path=%s', purpose, full_path)
            return None

    @classmethod
    def check_connection(cls):
        """Verifies credentials against the Dropbox API. Returns (ok, message)."""
        settings = cls._settings()
        if not settings.is_configured():
            return False, 'Dropbox is not enabled or is missing credentials.'
        try:
            account = cls._client(settings).users_get_current_account()
            return True, f'Connected as {account.name.display_name} ({account.email}).'
        except Exception as exc:  # noqa: BLE001
            logger.exception('Dropbox connection check failed.')
            return False, f'Connection failed: {exc}'
