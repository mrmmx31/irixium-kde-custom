#!/bin/sh
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in
  --verificar|--ativar|"")
    exec "$bundle_dir/modern-rewrite-rc1/instalar.sh" "$@"
    ;;
  --aplicar-fontes)
    printf '%s\n' '--aplicar-fontes não faz parte da decoração user-local; use o instalador de fontes separado.' >&2
    exit 2
    ;;
  *)
    printf '%s\n' 'Uso: update-irixium.sh [--verificar|--ativar]' >&2
    exit 2
    ;;
esac
