# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt preview teardown must not depend on lastWindowClosed after X11 reparenting."""
from pathlib import Path
import sys
import unittest


GALLERIES = Path(__file__).resolve().parents[3] / 'plasma/tests/galerias-nativas'
sys.path.insert(0, str(GALLERIES))

from qt6_demo import PreviewShutdown


class Recorder:
    def __init__(self, name, events):
        self.name = name
        self.events = events

    def stop(self):
        self.events.append(self.name + '.stop')

    def close(self):
        self.events.append(self.name + '.close')

    def quit(self):
        self.events.append(self.name + '.quit')


class PreviewShutdownTests(unittest.TestCase):
    def test_request_is_ordered_and_idempotent(self):
        events = []
        shutdown = PreviewShutdown(Recorder('app', events), Recorder('window', events))
        shutdown.set_timer(Recorder('timer', events))
        shutdown.set_bridge(Recorder('bridge', events))
        self.assertTrue(shutdown.request())
        self.assertFalse(shutdown.request())
        shutdown.cleanup()
        self.assertEqual(events, [
            'timer.stop', 'bridge.close', 'window.close', 'app.quit'])

    def test_about_to_quit_cleanup_does_not_reenter_quit(self):
        events = []
        shutdown = PreviewShutdown(Recorder('app', events), Recorder('window', events))
        shutdown.set_timer(Recorder('timer', events))
        shutdown.set_bridge(Recorder('bridge', events))
        shutdown.cleanup()
        shutdown.cleanup()
        self.assertEqual(events, ['timer.stop', 'bridge.close'])


if __name__ == '__main__':
    unittest.main()
