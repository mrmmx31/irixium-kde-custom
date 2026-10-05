#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt Quick layout harness with fake KDE objects. No real KWin integration."""
from pathlib import Path
import glob
import os
import shutil
import subprocess
import sys
import tempfile
BUNDLE = Path(__file__).resolve().parent.parent
candidates = [shutil.which('qmltestrunner6'), '/usr/lib/qt6/bin/qmltestrunner']
candidates += glob.glob('/usr/lib/*/qt6/bin/qmltestrunner')
runner = next((x for x in candidates if x and os.path.isfile(x) and os.access(x,os.X_OK)), None)
if runner is None:
    print('Qt 6 qmltestrunner não encontrado. Teste QML NÃO EXECUTADO.',file=sys.stderr)
    raise SystemExit(77)
with tempfile.TemporaryDirectory(prefix='irixium-qml-test-') as tmp:
    root = Path(tmp) / 'qml'
    shutil.copytree(BUNDLE / 'tests/qml',root)
    shutil.copyfile(BUNDLE / 'AuroraeButtonGroup.qml',root / 'AuroraeButtonGroup.qml')
    env = os.environ.copy()
    env['QT_QPA_PLATFORM']='offscreen'
    env['QT_QUICK_BACKEND']='software'
    result = subprocess.run([runner,'-input',str(root),'-import',str(root/'imports')],env=env)
    raise SystemExit(result.returncode)
