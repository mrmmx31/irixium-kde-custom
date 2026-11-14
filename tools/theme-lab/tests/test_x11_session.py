# SPDX-License-Identifier: GPL-3.0-or-later
import os
from pathlib import Path
import sys
import unittest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))

from x11_session import _peer_text, verify_local_x11


class X11SessionTests(unittest.TestCase):
    def test_abstract_and_pathname_peers_have_the_same_identity(self):
        self.assertEqual(_peer_text(b'\0/tmp/.X11-unix/X1'),
                         ('/tmp/.X11-unix/X1', 'abstract'))
        self.assertEqual(_peer_text('/tmp/.X11-unix/X1'),
                         ('/tmp/.X11-unix/X1', 'pathname'))

    def test_current_local_session_is_actively_authenticated(self):
        if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'):
            self.skipTest('Sessão X11 autenticada não está presente.')
        proof = verify_local_x11()
        self.assertTrue(proof['verified'])
        self.assertTrue(proof['transport'].startswith('unix_'))
        self.assertEqual(proof['peer'],
                         f"/tmp/.X11-unix/X{proof['display_number']}")
        self.assertEqual(Path(proof['xauthority']).stat().st_mode & 0o077, 0)

    def test_remote_display_is_rejected_before_connection(self):
        with self.assertRaisesRegex(ValueError, 'DISPLAY X11 local'):
            verify_local_x11(display='example.invalid:1',
                             authority=os.environ.get('XAUTHORITY', ''))

    def test_relative_authority_is_rejected_before_connection(self):
        with self.assertRaisesRegex(ValueError, 'caminho absoluto'):
            verify_local_x11(display=':1', authority='authority-relative')


if __name__ == '__main__':
    unittest.main()
