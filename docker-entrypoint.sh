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
exec "$@"
