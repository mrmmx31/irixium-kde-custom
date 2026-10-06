#!/bin/sh
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$base"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s kvantum/tests -p 'test_*.py' -v
