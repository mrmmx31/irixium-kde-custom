#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
exec python3 "$base/tools/diagnose_arrows.py" "$@"
