# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / 'tools/theme-lab'
sys.path.insert(0, str(LAB))

from direct_preview_route import append_host_arguments, environment, guard


class DirectPreviewRouteTests(unittest.TestCase):
    def setUp(self):
        base = Path.home() / 'tempia/domainos-theme-work'
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        base.chmod(0o700)
        self.session = Path(tempfile.mkdtemp(prefix='qt-direct-test-', dir=base))
        self.session.chmod(0o700)
        self.output = self.session / 'generated'
        self.output.mkdir(mode=0o700)

    def tearDown(self):
        shutil.rmtree(self.session)

    def test_detached_guard_redirects_every_write_profile(self):
        proof = guard(ROOT, self.output, 'qt6')
        self.assertEqual(proof['mode'], 'explicit_user_session_detached')
        self.assertEqual(proof['origin'], 'detached')
        self.assertFalse(proof['personal_profile_written'])
        child = environment(proof)
        self.assertEqual(child['QT_QPA_PLATFORM'], 'xcb')
        self.assertEqual(child['IRIX_DOMAINOS_DIRECT_PREVIEW'], '1')
        self.assertEqual(child['IRIX_DOMAINOS_PREVIEW_ORIGIN'], 'detached')
        for key in ('HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME',
                    'XDG_CACHE_HOME', 'XDG_STATE_HOME', 'XDG_RUNTIME_DIR'):
            self.assertTrue(Path(child[key]).is_relative_to(self.session), key)
            self.assertEqual(Path(child[key]).stat().st_mode & 0o777, 0o700)

    def test_rejects_other_temp_roots(self):
        outside = Path.home() / 'tempia' / ('direct-outside-' + uuid.uuid4().hex)
        outside.mkdir(mode=0o700)
        try:
            with self.assertRaisesRegex(ValueError, 'domainos-theme-work'):
                guard(ROOT, outside, 'qt5')
        finally:
            outside.rmdir()

    def test_embed_arguments_are_atomic(self):
        command = append_host_arguments(['demo'], embed_window=0x1234,
            host_pid=os.getpid(), host_bridge=ROOT / 'bridge.so',
            host_session_root=self.session)
        self.assertEqual(command[-8:], ['--embed-window', '4660', '--host-pid',
            str(os.getpid()), '--host-bridge', str(ROOT / 'bridge.so'),
            '--host-session-root', str(self.session)])
        with self.assertRaisesRegex(ValueError, 'juntos'):
            append_host_arguments(['demo'], embed_window=0x1234)

    def test_coupled_and_detached_same_family_have_disjoint_profiles(self):
        detached = guard(ROOT, self.output, 'qt6')
        bridge = ROOT / 'tools/theme-lab/build/libtheme-lab-gtk4-host.so'
        coupled = guard(ROOT, self.output, 'qt6', embed_window=0x1234,
            host_pid=os.getpid(), host_bridge=bridge,
            host_session_root=self.session)
        self.assertEqual(coupled['origin'], 'coupled')
        self.assertEqual(coupled['mode'], 'explicit_user_session_x11_reparent')
        for key in ('home', 'config', 'data', 'cache', 'state', 'runtime'):
            detached_path = Path(detached['profile'][key])
            coupled_path = Path(coupled['profile'][key])
            self.assertNotEqual(detached_path, coupled_path, key)
            self.assertEqual(detached_path.parent.name, 'detached')
            self.assertEqual(coupled_path.parent.name, 'coupled')
        self.assertEqual(environment(coupled)['IRIX_DOMAINOS_PREVIEW_ORIGIN'],
                         'coupled')


if __name__ == '__main__':
    unittest.main()
