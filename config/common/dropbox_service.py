import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class DropboxService:
    """Uploads copies of files to the company Dropbox.

    Two independent destinations, each with its own base path:

    - ``uploads`` — mirror of approved (clean-scanned) document versions.
    - ``rgpd`` — legal consent proofs (terms-acceptance PDFs), retained for
      ten years. Never pruned.

    MinIO remains the source of truth; Dropbox is a mirror / long-term archive.
    The service fails **open**: when Dropbox is not configured or the API errors,
    it logs and returns ``None`` so the request/task is never broken. A Celery
    task is responsible for retrying.

    Credentials come from the environment (infrastructure config), never the DB.
    A Full-Dropbox-scoped app is required to write both base paths; alternatively
    use two App-folder apps and point the base paths at each app's root.
    """

    PURPOSE_UPLOADS = 'uploads'
    PURPOSE_RGPD = 'rgpd'

    @staticmethod
    def is_enabled():
        return bool(
            settings.DROPBOX_ENABLED
            and settings.DROPBOX_APP_KEY
            and settings.DROPBOX_APP_SECRET
            and settings.DROPBOX_REFRESH_TOKEN
        )

    @classmethod
    def _base_path(cls, purpose):
        mapping = {
            cls.PURPOSE_UPLOADS: settings.DROPBOX_UPLOADS_PATH,
            cls.PURPOSE_RGPD: settings.DROPBOX_RGPD_PATH,
        }
        base = (mapping.get(purpose) or '').rstrip('/')
        return base

    @classmethod
    def _client(cls):
        # Imported lazily so the dependency is optional at runtime.
        import dropbox

        return dropbox.Dropbox(
            app_key=settings.DROPBOX_APP_KEY,
            app_secret=settings.DROPBOX_APP_SECRET,
            oauth2_refresh_token=settings.DROPBOX_REFRESH_TOKEN,
            timeout=settings.DROPBOX_TIMEOUT_SECONDS,
        )

    @classmethod
    def upload_bytes(cls, *, purpose, relative_path, content):
        """Uploads ``content`` (bytes) to ``<base>/<relative_path>``.

        Returns the full Dropbox path on success, ``None`` on any failure.
        """
        if not cls.is_enabled():
            logger.info('Dropbox disabled; skipping mirror. purpose=%s path=%s', purpose, relative_path)
            return None

        import dropbox

        base = cls._base_path(purpose)
        clean = relative_path.strip('/').replace('//', '/')
        full_path = f'{base}/{clean}' if base else f'/{clean}'
        try:
            client = cls._client()
            client.files_upload(content, full_path, mode=dropbox.files.WriteMode.overwrite, mute=True)
            logger.info('Mirrored to Dropbox. purpose=%s path=%s bytes=%s', purpose, full_path, len(content))
            return full_path
        except Exception:  # noqa: BLE001 — never let a mirror failure surface.
            logger.exception('Dropbox upload failed. purpose=%s path=%s', purpose, full_path)
            return None
