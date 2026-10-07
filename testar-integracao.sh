#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$here"
python3 tools/audit_suite.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest discover -s kvantum/tests -p 'test_*.py'
python3 -m unittest discover -s plasma/tests -p 'test_*.py'
bash decorations/classic/testar.sh
python3 -m unittest discover -s decorations/modern/tests -p 'test_*.py'
python3 -m unittest discover -s icons/tests -p 'test_*.py'
python3 -m unittest discover -s cursors/tests -p 'test_*.py'
bash sons/testar.sh
bash distribuicao/testar.sh
