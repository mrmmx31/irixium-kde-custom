#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
exec python3 "$(dirname -- "${BASH_SOURCE[0]}")/tools/preview_controls.py" "$@"
