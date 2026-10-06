#!/bin/sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
activate=0
case "${1:-}" in
  ""|--instalar) ;;
  --ativar) activate=1 ;;
  *)
    printf '%s\n' "Uso: $0 [--instalar|--ativar]" >&2
    exit 2
esac

if [ "$activate" -eq 1 ]; then
  exec "$base/../modern-rewrite-rc1/instalar.sh" --ativar
fi
exec "$base/../modern-rewrite-rc1/instalar.sh"
