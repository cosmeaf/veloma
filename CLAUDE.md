# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Veloma Core: a Django 5.2 + DRF backend providing authentication, session-bound JWT, native Django RBAC, security controls, configurable email and audit. There is no business application yet — `app/` is intentionally empty and a `veloma-app` compose service must not be created until the core is approved (`scripts/validate_project.py` fails the build if one appears).

`BEGIN_VELOMA.md` is the master spec (in Portuguese) describing the intended end state, including the future Next.js frontend. `README.md` documents the delivered core.

## Commands

Local stack (Postgres, Redis, MinIO, Celery worker + beat):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

Tests inside the container:

```bash
docker exec -it veloma-api python manage.py test
```

Fast tests on the host without Docker (SQLite + local-memory cache + eager Celery):

```bash
DATABASE_ENGINE=sqlite MINIO_ENABLED=false USE_LOCAL_MEMORY_CACHE=true \
CELERY_TASK_ALWAYS_EAGER=true python manage.py test

# single test
DATABASE_ENGINE=sqlite MINIO_ENABLED=false USE_LOCAL_MEMORY_CACHE=true \
CELERY_TASK_ALWAYS_EAGER=true python manage.py test \
  config.authentication.tests.AuthenticationCoreTests.test_login_creates_revocable_session
```

Static validation (required file set, syntax, compose services, `.env` keys, email template pairing):

```bash
python3 scripts/validate_project.py
python3 -m compileall -q .
```

Seed groups, singleton settings, email vendor/templates and the dev superuser (idempotent; also run by the entrypoint when `RUN_BOOTSTRAP=true`):

```bash
python manage.py bootstrap_veloma
```

`python scripts/generate_secrets.py` prints a fresh set of production secrets. The committed `.env` is development-only.

## Architecture

### Layout

`config/` is both the Django project package and the home of all four apps — there is no top-level apps directory. App labels are deliberately renamed, and code that keys off labels must use them:

| Package | Label | Contents |
| --- | --- | --- |
| `config.authentication` | `veloma_authentication` | register/login/OTP/reset, sessions, JWT, audit models |
| `config.common` | `veloma_configuration` | DB-backed settings singletons, email service, crypto, health |
| `config.security` | `veloma_security` | request context, IP intelligence, blocks, rate limit middleware |
| `config.iam` | `veloma_iam` | DRF permission classes only (no models) |
| `app.client_portal` | `veloma_client_portal` | business module: clients, members, invitations, protocols, folders, documents |

`config.security` and `config.iam` have no migrations; the security/audit models (`AccessBlock`, `SecurityEvent`, `AuthenticationActivity`, …) all live in `config/authentication/models.py` with explicit `db_table` names.

### Identity model — do not change

Native `django.contrib.auth.models.User`, `Group`, `Permission` only. No `CustomUser`, no `AUTH_USER_MODEL`, no profile model. `username` is always the normalized email (`email.strip().lower()`), set in `UserService.register`.

Three separate access tiers:
- **Django Admin** — `is_staff=True`, `/admin/` only. `LoginSerializer` rejects staff/superuser accounts on the JWT API when `AuthenticationSettings.deny_django_admin_api_login` is on.
- **Platform STAFF** — `is_staff=False`, in group `STAFF` (`IsFrontendStaff`).
- **Customer USER** — `is_staff=False`, in group `USER` (`IsFrontendUser`).

Groups `STAFF`/`USER` are created by a `post_migrate` receiver in `config/authentication/signals.py` and by `bootstrap_veloma`.

### Runtime configuration lives in the database

`AuthenticationSettings`, `SecuritySettings`, `EmailSettings` are `SingletonModel` rows (pk=1) loaded via `Cls.load()` with a 30-second cache invalidated on save. Behavior knobs — OTP length/expiry, login attempt thresholds, block duration, max active sessions, rate limits, country allow-list, notification toggles, retention windows — are edited in Django Admin, **not** in `settings.py`. `settings.py` only reads environment variables (infrastructure, JWT lifetimes, proxy trust).

### Session-bound JWT

Every access/refresh token carries a `session_id` claim mapped to a `UserSession` row (keyed by `refresh_jti`).

- `SessionService.create_tokens` enforces `max_active_sessions` by revoking the oldest sessions, runs `SecurityService.analyze_session_context` (new device / new IP / new country detection via SHA-256 UA fingerprint) and returns the security flags.
- `SessionJWTAuthentication` (the default DRF auth class) re-checks active blocks and calls `SessionService.validate` on every request, touching `last_activity_at` at most once per `session_activity_touch_seconds`.
- `VelomaTokenRefreshSerializer` validates the session before delegating to SimpleJWT, then `SessionService.rotate` re-points the row at the new `jti`. Revocation blacklists the outstanding token and flips the session status.

A token whose session was revoked or expired fails authentication even while the JWT signature is still valid.

### Account lifecycle

Accounts are never deleted physically. `AccountLifecycle` (one row per user, `veloma_lifecycle`) records deactivation and logical deletion; the account state is derived from it: `active` → `deactivated` (temporary, still listed) → `archived` (logical delete, hidden from operations).

`AccountLifecycleService` is the only supported entry point — `deactivate`, `archive`, `reactivate`, `restore`. Each runs in one transaction and revokes sessions, blacklists outstanding refresh tokens, blocks pending OTPs, revokes pending reset grants, writes an `AuthenticationActivity` + `SecurityEvent` and sends the configured email. Never flip `user.is_active` or edit the lifecycle row directly from a view, serializer or admin action. `restore` un-archives but leaves the account deactivated: access only comes back through an explicit `reactivate`. An administrator cannot run any of these on their own account.

In the Admin, `VelomaUserAdmin` hides archived users, removes `delete_selected` and denies `has_delete_permission`; archived accounts live in the `ArchivedAccount` proxy ("Archived accounts"). Reactivate/restore are only offered to superusers.

FK policy follows the same intent: throwaway auth data (`OTPChallenge`, `PasswordResetGrant`, `UserSession`) cascades, while historical data (`AuthenticationActivity`, `SecurityEvent`) uses `SET_NULL` so the audit trail survives.

### Client portal module

`app/client_portal/` is the accounting-office business module and the only Django app outside `config/`. It follows the same layering, one file per responsibility: `models` → `services` (mutations, transactional) → `selectors` (queries and visibility) → `serializers` → thin `views`.

Rules that shape the code:

- **Invitation-only accounts.** `bootstrap_veloma` turns `AuthenticationSettings.registration_enabled` off on first install; `InvitationService.accept` is the only path that creates a portal `User` (native user, `username` = email, group `USER`, plus a `ClientMember`). Invitation tokens are opaque, single-use and stored only as an HMAC hash, like password-reset grants.
- **Never trust a client id from the request.** Every queryset goes through `selectors.py`, which scopes by active `ClientMember` rows for portal users, by assignment for `STAFF`, and unrestricted for `STAFF_MANAGER`. Internal comments and `staff_only` documents are filtered in the queryset, not in the UI.
- **Nothing is deleted.** Clients, members, protocols, documents and comments only move to `deactivated`/`archived`. There is no `DELETE` verb in the API and `delete_selected` is stripped from every admin. Historical FKs use `SET_NULL`/`PROTECT` and rows carry name/email snapshots so the trail survives anonymisation.
- **Protocol status is a state machine.** `Protocol.TRANSITIONS` defines the legal moves and `ProtocolService.transition` enforces them; reopening a completed protocol requires `STAFF_MANAGER`. Clients see `CLIENT_STATUS_LABELS`, not the internal status.
- **Uploads.** `DocumentService` validates extension/size/MIME sniffing, computes SHA-256, writes through `StorageService` (never the S3 SDK directly) under `clients/{id}/protocols/{id}/documents/{id}/versions/{id}`, then queues `scan_document_version`. A new upload never overwrites a version. Documents only become downloadable after the scan, and every download creates a `DownloadAudit` plus a short-lived signed URL.
- **Antivirus** is a plain socket ClamAV INSTREAM client (`config/common/antivirus.py`). With `require_antivirus` off, a scanner error still publishes the file; with it on, the file stays quarantined.
- Upload, invitation and antivirus policy lives in the `DocumentSettings` singleton (Admin → Configuration), not in `settings.py`.

### Security middleware

`SecurityContextMiddleware` runs after `AuthenticationMiddleware` and only enforces on `/api/` paths. It attaches `request.client_ip`, `client_user_agent`, `client_device`, `ip_intel`, then applies: per-IP+path sliding-window rate limit (separate budget for `/api/auth/`), country allow-list, then user/IP/country/user-agent `AccessBlock` lookup. Rate limiting fails **open** on cache errors by design — DB-backed brute-force blocking still applies. Client IP resolution (`RequestContext.ip`) only honours `X-Forwarded-For` when `REMOTE_ADDR` is inside `TRUSTED_PROXY_IPS`.

Repeated login failures create automatic, expiring `AccessBlock` rows via `SecurityService.enforce_failed_login_blocks`.

### Email

Nothing about email is hardcoded. `EmailService.send_by_purpose(purpose=...)` looks up an `EmailTemplate` row that supplies subject, HTML/TXT template paths, delivery mode and optional vendor; `bootstrap_veloma` seeds the purpose catalogue. Vendors (`EmailVendor`) are DB rows with priority, default and fallback flags. Delivery modes: `sync`, `async` (Celery `send_email_task` with backoff), `auto` (async, falling back to sync). Every send writes an `EmailDeliveryLog`.

Templates live directly in `templates/emails/` and **must exist as matching `.html` + `.txt` pairs** — `validate_project.py` fails otherwise. Adding a new notification means: add both files, add the purpose to `bootstrap_veloma.TEMPLATES`, then call `send_by_purpose`.

SMTP passwords and the IP-intelligence token are Fernet-encrypted through `CredentialCipher` before storage and never rendered back into admin forms; they require a valid `CREDENTIALS_ENCRYPTION_KEY`.

### Request/response conventions

Views are thin: they validate a serializer and return `api_response(...)`, which emits `{success, message, data}`. `custom_exception_handler` wraps DRF errors as `{success: false, message, errors}`. Serializers orchestrate the flow (activity recording, optional emails via `send_optional_email`, which never lets a mail failure break the request); services own the transactional work (`@transaction.atomic`, `select_for_update`). Put new business logic in `services.py`, not in views.

Secrets are never stored raw: OTP codes use the Django password hasher, reset tokens are HMAC-SHA256 hashed (`hash_token`).

### Background work

`config.celery` autodiscovers tasks. Celery beat runs `cleanup_expired_authentication_records` hourly (`AUTH_CLEANUP_INTERVAL_SECONDS`), expiring sessions and pruning OTPs, grants, activity, security events, email logs and SimpleJWT token history according to the retention fields on `SecuritySettings`.

## Conventions

- Code, comments and log messages are in English; user-facing email templates and the spec docs are Portuguese (`pt-pt`, `Europe/Lisbon`).
- Tests subclass `APITestCase`, call `bootstrap_veloma` in `setUpTestData`, force email templates to `sync`, disable the API rate limit, and use `@override_settings` for eager Celery + locmem cache — follow `config/authentication/tests.py`.
- `docker-compose.yml` must not declare custom networks (Coolify/Traefik attaches its own) and must keep the seven `veloma-*` services; `validate_project.py` enforces both.
