#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
exec python3 -m unittest discover -s kvantum/tests -p 'test_*.py' -v
