# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from gtk4_layout_transaction import LayoutTransaction, layout_modifier


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.records = {0: {'x': 32, 'y': 40}}
        self.positions, self.events = [], []
        self.transaction = LayoutTransaction(
            self.records, lambda index, x, y: self.positions.append((index, x, y)),
            lambda action, index, fields: self.events.append((action, index, fields)))

    def test_ctrl_only_and_shift_ctrl_preserve_other_shortcuts(self):
        for mask in (0, 1, 8, 4 | 8, 4 | (1 << 26)):
            self.assertFalse(layout_modifier(mask))
        self.assertTrue(layout_modifier(4))
        self.assertTrue(layout_modifier(5))

    def test_delta_is_stable_and_commit_follows_event(self):
        t = self.transaction
        t.begin(0, 100, 200, 9, 2)
        t.update(110, 220, 9, 2)
        t.update(120, 230, 9, 2)
        self.assertEqual(self.positions[-1], (0, 52, 70))
        self.assertEqual(self.records[0], {'x': 32, 'y': 40})
        self.assertTrue(t.finish())
        self.assertEqual(self.records[0], {'x': 52, 'y': 70})
        self.assertEqual([e[0] for e in self.events], ['select', 'move'])
        self.assertEqual(self.events[-1][2]['coordinate_space'], 'gtk_logical_px')

    def test_failed_write_restores_original_without_commit(self):
        t = self.transaction
        t.begin(0, 100, 200, 9, 1)
        t.update(120, 230, 9, 1)
        def fail(*args):
            raise OSError('disk full')
        t.emit = fail
        with self.assertRaises(OSError):
            t.finish()
        self.assertEqual(self.positions[-1], (0, 32, 40))
        self.assertEqual(self.records[0], {'x': 32, 'y': 40})
        self.assertIsNone(t.active)

    def test_click_does_not_emit_move_and_cancel_is_idempotent(self):
        t = self.transaction
        t.begin(0, 100, 200, 9, 1)
        self.assertFalse(t.finish())
        t.cancel(); t.cancel()
        self.assertEqual([e[0] for e in self.events], ['select'])

    def test_changed_surface_scale_or_invalid_coordinate_roll_back(self):
        for x, y, surface, scale in ((120, 230, 10, 1),
                                     (120, 230, 9, 2), (float('nan'), 230, 9, 1)):
            t = self.transaction
            t.begin(0, 100, 200, 9, 1)
            t.update(110, 210, 9, 1)
            with self.assertRaises(ValueError):
                t.update(x, y, surface, scale)
            self.assertEqual(self.positions[-1], (0, 32, 40))
            self.assertIsNone(t.active)

    def test_limits_and_cancel_before_second_gesture(self):
        t = self.transaction
        t.begin(0, 100, 200, 9, 1)
        t.update(-1000, 10000, 9, 1)
        self.assertEqual(self.positions[-1], (0, 0, 2048))
        t.begin(0, 100, 200, 9, 1)
        self.assertEqual(self.positions[-1], (0, 32, 40))
        t.cancel()


if __name__ == '__main__':
    unittest.main()
