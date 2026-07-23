#!/bin/sh
set -eu
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  python manage.py migrate --noinput
fi
if [ "${RUN_COLLECTSTATIC:-false}" = "true" ]; then
  python manage.py collectstatic --noinput
fi
if [ "${RUN_BOOTSTRAP:-false}" = "true" ]; then
  python manage.py bootstrap_veloma
fi
# Seed the office staff accounts once. Idempotent: existing accounts are skipped,
# so it is safe to leave enabled across deploys.
if [ "${RUN_STAFF_SEED:-false}" = "true" ] && [ -n "${STAFF_INITIAL_PASSWORD:-}" ]; then
  python manage.py create_staff_accounts
fi
exec "$@"
