#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$here"
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s kvantum/tests -p 'test_*.py' -v
