#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# Prefer distro Qt bindings when the shell's Python points into a virtualenv.
for py in /usr/bin/python3 python3; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import importlib.util as u; raise SystemExit(not any(u.find_spec(x) for x in ("PyQt6","PySide6")))' 2>/dev/null; then
        exec "$py" "$here/tools/preview_buttons.py" "$@"
    fi
done
exec python3 "$here/tools/preview_buttons.py" "$@"
