#!/bin/sh
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 -B -m unittest discover -s "$here/tests" -p 'test_*.py' -v
