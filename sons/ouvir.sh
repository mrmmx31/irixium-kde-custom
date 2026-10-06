#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
base="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec python3 -B "$base/tools/preview_sounds.py" "$@"
