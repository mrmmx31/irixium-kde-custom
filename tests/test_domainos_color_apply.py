#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check the installed KDE color applicator in a disposable user profile.

This checks effective KConfig roles, not preview pixels or QWidget recoloring.
The independent native rendering experiment covers the live panel separately.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
import configparser, json, os, pathlib, subprocess, sys
cases = json.loads(sys.argv[1])
observed = []
for case in cases:
    result = subprocess.run(['plasma-apply-colorscheme', case['id']],
                            text=True, capture_output=True, timeout=15)
    if result.returncode:
        raise RuntimeError(result.stderr + result.stdout)
    current = configparser.ConfigParser(interpolation=None)
    current.read(pathlib.Path(os.environ['XDG_CONFIG_HOME'])/'kdeglobals')
    expected = configparser.ConfigParser(interpolation=None)
    expected.read(case['source'])
    for section in ('Colors:Window', 'Colors:View', 'Colors:Button',
                    'Colors:Selection', 'Colors:Tooltip'):
        for key in ('BackgroundNormal', 'ForegroundNormal'):
            assert current.get(section, key) == expected.get(section, key), (case['id'], section, key)
    # BreezeLight is KDE's default and can omit the explicit entry.
    assert current.get('General', 'ColorScheme', fallback='BreezeLight') == case['id']
    observed.append(case['id'])
print(json.dumps({'applied': observed}))
'''


class NativeColorApplyTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('plasma-apply-colorscheme') and shutil.which('dbus-run-session'),
                         'Installed KDE color applicator and D-Bus session launcher required')
    def test_safe_domainos_identifier_applies_effective_colors(self):
        # HOME and all XDG roots belong to this test. No personal config, theme
        # application, desktop/panel activation or cache refresh is involved.
        with tempfile.TemporaryDirectory(prefix='.domainos-color-apply-', dir=ROOT) as directory:
            base = Path(directory)
            env = dict(os.environ)
            for name, folder in (('HOME', 'home'), ('XDG_CONFIG_HOME', 'config'),
                                 ('XDG_DATA_HOME', 'data'), ('XDG_STATE_HOME', 'state'),
                                 ('XDG_CACHE_HOME', 'cache'), ('XDG_RUNTIME_DIR', 'runtime')):
                path = base/folder
                path.mkdir(mode=0o700)
                env[name] = str(path)
            env.update(QT_QPA_PLATFORM='offscreen', XDG_DATA_DIRS='/usr/local/share:/usr/share',
                       PYTHONDONTWRITEBYTECODE='1')
            for name in ('DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'WAYLAND_DISPLAY',
                         'KDE_COLOR_SCHEME_PATH'):
                env.pop(name, None)
            schemes = base/'data/color-schemes'
            schemes.mkdir()
            cases = []
            for identifier, name in (('DomainOS-SR10-4', 'DomainOS-SR10.4'), ('Irixium', 'Irixium')):
                source = schemes/(identifier+'.colors')
                shutil.copyfile(ROOT/'colors'/(name+'.colors'), source)
                cases.append({'id': identifier, 'source': str(source)})
            for identifier in ('BreezeLight', 'BreezeDark'):
                source = Path('/usr/share/color-schemes')/(identifier+'.colors')
                if source.is_file():
                    cases.append({'id': identifier, 'source': str(source)})
            result = subprocess.run(['dbus-run-session', '--', sys.executable, '-B', '-c',
                                     DRIVER, json.dumps(cases)], env=env,
                                    capture_output=True, text=True, timeout=55)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertEqual(report['applied'], [case['id'] for case in cases])


if __name__ == '__main__':
    unittest.main()
