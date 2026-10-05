#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
set -eu
bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$bundle_dir/irixium_install.py" install "$@"
