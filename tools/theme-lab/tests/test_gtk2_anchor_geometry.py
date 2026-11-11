# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtk2_anchor_geometry import requested_origin, allocated_origin
from scene_anchor import anchor_origin


class AnchorTests(unittest.TestCase):
    def record(self, control='scroll_h', width=0, height=0):
        return {'id': control, 'x': 400, 'y': 400, 'width': width, 'height': height, 'length_anchor': 1}
    def test_natural_and_explicit_requests_keep_trailing_edge(self):
        r = self.record(); before = copy.deepcopy(r)
        self.assertEqual(requested_origin(r, [48, 15]), (352, 400))
        r['width'] = 20
        self.assertEqual(requested_origin(r, [48, 15]), (380, 400))
        r['width'] = 320
        self.assertEqual(requested_origin(r, [48, 15]), (80, 400))
        self.assertEqual(before['width'], 0)
    def test_vertical_child_offset_uses_real_edge(self):
        r = self.record('scroll_v')
        self.assertEqual(anchor_origin(r, 15, 260, (0, 18)), (400, 122))
        self.assertEqual(requested_origin(r, [15, 48]), (400, 352))
    def test_actual_allocation_replaces_requested_prediction(self):
        r = self.record(width=20, height=15)
        widget = SimpleNamespace(get_allocation=lambda: SimpleNamespace(width=73, height=15))
        self.assertEqual(allocated_origin(r, widget), (327, 400))
    def test_invalid_placement_is_refused_without_mutating_record(self):
        r = self.record(width=500); before = copy.deepcopy(r)
        with self.assertRaisesRegex(ValueError, 'fora do canvas'): requested_origin(r, [48, 15])
        self.assertEqual(r, before)
        with self.assertRaises(ValueError): requested_origin(self.record(), [True, 15])
        with self.assertRaises(ValueError): requested_origin(self.record(), [0, 15])
    def test_unanchored_control_keeps_leading_coordinate(self):
        r = self.record(); r['length_anchor'] = 0
        self.assertEqual(requested_origin(r, [48, 15]), (400, 400))
    def test_only_scrollbars_have_trailing_axis(self):
        with self.assertRaises(ValueError): requested_origin(self.record('push'), [48, 15])


if __name__ == '__main__': unittest.main()
