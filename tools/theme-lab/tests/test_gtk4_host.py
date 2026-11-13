# SPDX-License-Identifier: GPL-3.0-or-later
import os
import threading
import unittest
from unittest.mock import MagicMock, patch
from gtk4_host import HostBridge, process_identity


class HostGuardsTests(unittest.TestCase):
    def test_attach_retries_until_x11_ownership_is_published(self):
        bridge=HostBridge.__new__(HostBridge)
        bridge.handle,bridge.pid=1,os.getpid()
        bridge.start=process_identity(bridge.pid)
        bridge._attach=MagicMock(side_effect=(0,0,1))
        times=iter((0.0,0.1,0.2))
        progress=MagicMock()
        bridge.attach(0x1234,clock=lambda:next(times),sleeper=lambda _delay:None,
                      progress=progress)
        self.assertEqual(bridge._attach.call_count,3)
        self.assertEqual(progress.call_count,2)

    def test_attach_rejects_invalid_progress_callback(self):
        bridge=HostBridge.__new__(HostBridge)
        bridge.handle,bridge.pid=1,os.getpid()
        bridge.start=process_identity(bridge.pid)
        bridge._attach=MagicMock(return_value=1)
        with self.assertRaisesRegex(ValueError,'must be callable'):
            bridge.attach(0x1234,progress=True)
        bridge._attach.assert_not_called()

    def test_attach_timeout_is_bounded(self):
        bridge=HostBridge.__new__(HostBridge)
        bridge.handle,bridge.pid=1,os.getpid()
        bridge.start=process_identity(bridge.pid)
        bridge._attach=MagicMock(return_value=0)
        times=iter((0.0,1.0))
        with self.assertRaisesRegex(ValueError,'cannot be attached'):
            bridge.attach(0x1234,timeout=0.5,clock=lambda:next(times),
                          sleeper=lambda _delay:None)
        self.assertEqual(bridge._attach.call_count,1)

    def test_live_process_identity_is_stable(self):
        self.assertEqual(process_identity(os.getpid()), process_identity(os.getpid()))

    def test_invalid_pid_is_rejected(self):
        for value in (0, -1, True, '1'):
            with self.assertRaises(ValueError):
                process_identity(value)

    def test_invalid_canvas_refused_before_loading_library(self):
        for value in (0, -1, True, 0x100000000):
            with self.assertRaisesRegex(ValueError, 'canvas XID'):
                HostBridge('/nonexistent-library', value, os.getpid())

    def test_background_thread_refused_before_loading_library(self):
        errors = []
        def attempt():
            try:
                HostBridge('/nonexistent-library', 1, os.getpid())
            except RuntimeError as error:
                errors.append(str(error))
        thread = threading.Thread(target=attempt)
        thread.start(); thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ['GTK4 X11 host requires the main thread'])

    def test_transient_process_observation_error_is_not_terminal(self):
        bridge = HostBridge.__new__(HostBridge)
        bridge.handle, bridge.pid, bridge.start = 1, os.getpid(), 'known'
        with patch('gtk4_host.process_identity', side_effect=OSError('temporary observation failure')):
            with self.assertRaises(OSError):
                bridge.poll()
        self.assertEqual(bridge.handle, 1)


if __name__ == '__main__':
    unittest.main()
