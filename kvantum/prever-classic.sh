#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# Prefer distro bindings; virtual-environment Python may not see them.
if [ -x /usr/bin/python3 ]; then
    exec /usr/bin/python3 "$here/tools/preview_classic.py" "$@"
fi
exec python3 "$here/tools/preview_classic.py" "$@"
