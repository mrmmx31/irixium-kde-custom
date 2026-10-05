#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# Debian may provide PyQt6 in /usr/bin/python3 while a venv is active.
# KVANTUM_PYTHON overrides the executable, without installing dependencies.
if [ -n "${KVANTUM_PYTHON:-}" ]; then
    exec "$KVANTUM_PYTHON" "$base/tools/preview_scrollbars.py" "$@"
fi
if [ -x /usr/bin/python3 ]; then
    exec /usr/bin/python3 "$base/tools/preview_scrollbars.py" "$@"
fi
exec python3 "$base/tools/preview_scrollbars.py" "$@"
