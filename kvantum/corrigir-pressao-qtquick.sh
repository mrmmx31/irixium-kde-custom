#!/bin/sh
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 -B "$base/tools/qtquick_scrollbar_fix.py" "$@"
