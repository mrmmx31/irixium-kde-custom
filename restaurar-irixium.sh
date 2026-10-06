#!/bin/sh
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$bundle_dir/modern-rewrite-rc1/restaurar.sh" "$@"
