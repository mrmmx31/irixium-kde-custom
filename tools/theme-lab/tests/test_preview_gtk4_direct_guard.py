# SPDX-License-Identifier: GPL-3.0-or-later
"""The normal desktop route remains confined to the Theme Lab private session."""
from pathlib import Path
import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch

import backend
import preview_gtk4


class DirectGuardTests(unittest.TestCase):
    def test_entrypoint_reports_expected_guard_without_traceback(self):
        argv = [
            '--project', '/owned/scene.json', '--snapshot', '/owned/snapshot',
            '--events-dir', '/owned/events', '--root', '/repo'
        ]
        output = io.StringIO()
        with patch.object(backend, 'private_namespace',
                          side_effect=backend.Unavailable('private launcher required')), \
             contextlib.redirect_stderr(output):
            self.assertEqual(preview_gtk4.entrypoint(argv), 2)
        self.assertEqual(output.getvalue(),
                         'Prévia GTK4 indisponível: private launcher required\n')
        self.assertNotIn('Traceback', output.getvalue())

    def test_embed_uses_explicit_session_guard_before_worker(self):
        argv = [
            '--project', '/owned/scene.json', '--snapshot', '/owned/snapshot',
            '--events-dir', '/owned/events', '--root', '/repo',
            '--embed-window', '4660', '--host-pid', '99',
            '--host-bridge', '/repo/bridge.so',
            '--host-session-root', '/owned'
        ]
        worker = MagicMock()
        worker.return_value.run.return_value = 0
        with patch.dict('os.environ', {}, clear=True), \
             patch.object(backend, 'embedded_user_preview_guard',
                          return_value={'verified': True}) as guard, \
             patch.object(backend, 'private_namespace') as private, \
             patch('gtk4_worker.Worker', worker):
            self.assertEqual(preview_gtk4.main(argv), 0)
        private.assert_not_called()
        guard.assert_called_once()
        call = guard.call_args
        self.assertEqual(call.kwargs['family'], 'gtk4')
        self.assertFalse(call.kwargs['capture_mode'])
        self.assertEqual(call.args[5], 4660)

    def test_bwrap_keeps_original_private_namespace_guard(self):
        argv = [
            '--project', '/owned/scene.json', '--snapshot', '/owned/snapshot',
            '--events-dir', '/owned/events', '--root', '/repo',
            '--host-session-root', '/owned'
        ]
        worker = MagicMock()
        worker.return_value.run.return_value = 0
        with patch.dict('os.environ', {'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap'}, clear=True), \
             patch.object(backend, 'embedded_user_preview_guard') as direct, \
             patch.object(backend, 'private_namespace',
                          return_value={'verified': True}) as private, \
             patch('gtk4_worker.Worker', worker):
            self.assertEqual(preview_gtk4.main(argv), 0)
        direct.assert_not_called()
        private.assert_called_once_with(Path('/repo'))


if __name__ == '__main__':
    unittest.main()
