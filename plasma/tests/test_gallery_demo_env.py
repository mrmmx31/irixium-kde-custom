#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The private GTK gallery may use ~/tempia without weakening its guard."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'plasma/tests/galerias-nativas/demo_env.py'
SPEC = importlib.util.spec_from_file_location('domainos_demo_env_test', SOURCE)
DEMO_ENV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEMO_ENV)
TEMP_IA = Path.home() / 'tempia'


def private_environment(base):
    paths = {}
    for key, leaf in {
        'XDG_CONFIG_HOME': 'config', 'XDG_DATA_HOME': 'data',
        'XDG_STATE_HOME': 'state', 'XDG_CACHE_HOME': 'cache',
        'XDG_RUNTIME_DIR': 'run',
    }.items():
        path = base / leaf
        path.mkdir(mode=0o700)
        paths[key] = str(path)
    paths.update({
        'IRIX_DOMAINOS_PRIVATE_XEPHYR': '1',
        'IRIX_DOMAINOS_SESSION_ROOT': str(base),
        'HOME': str(base / 'home'),
        'DISPLAY': ':68',
        'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/private-test-bus',
        'GDK_BACKEND': 'x11',
    })
    (base / 'home').mkdir(mode=0o700)
    return paths


class GalleryPrivateEnvironmentTests(unittest.TestCase):
    def test_secure_session_under_tempia_is_accepted(self):
        TEMP_IA.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='demo-env-', dir=TEMP_IA) as name:
            base = Path(name)
            with patch.dict(os.environ, private_environment(base), clear=True):
                DEMO_ENV.require_private_session()

    def test_permissive_session_under_tempia_is_rejected(self):
        TEMP_IA.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='demo-env-open-', dir=TEMP_IA) as name:
            base = Path(name)
            base.chmod(0o755)
            with patch.dict(os.environ, private_environment(base), clear=True):
                with self.assertRaisesRegex(RuntimeError, 'Explicit disposable session root'):
                    DEMO_ENV.require_private_session()


if __name__ == '__main__':
    unittest.main()
