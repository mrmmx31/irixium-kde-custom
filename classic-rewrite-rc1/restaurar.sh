#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "${1:-}" = "--recuperar" ]; then
    exec python3 "$base/tools/manage.py" --recuperar
fi
exec python3 "$base/tools/manage.py" --restaurar "$@"
