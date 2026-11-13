# SPDX-License-Identifier: GPL-3.0-or-later
"""Direction selection for real GTK2 scrollbar press/release samples."""
from pathlib import Path
import copy
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preview_gtk2 import (capture_probe, private_capture_model, sample_piece,
                          stepper_event_position)


class FakePixbuf:
    def __init__(self, width, height, crop=None):
        self.width, self.height, self.crop = width, height, crop

    def new_subpixbuf(self, x, y, width, height):
        return FakePixbuf(width, height, (x, y, width, height))


class FakeRange:
    def __init__(self, slider):
        self.slider = slider

    def get_slider_range(self):
        return self.slider


def request(**changes):
    values = dict(capture_control=10, capture_length=220, capture_thickness=15,
                  capture_value=25, capture_page_size=25,
                  capture_part='whole', capture_direction='auto')
    values.update(changes)
    return SimpleNamespace(**values)


class Gtk2StepperCaptureTests(unittest.TestCase):
    def test_horizontal_stepper_centers_use_native_allocation(self):
        self.assertEqual(stepper_event_position('scroll_h', 220, 15, 'left'),
                         (7, 7, 'left'))
        self.assertEqual(stepper_event_position('scroll_h', 220, 15, 'right'),
                         (212, 7, 'right'))

    def test_vertical_stepper_centers_use_native_allocation(self):
        self.assertEqual(stepper_event_position('scroll_v', 15, 54, 'up'),
                         (7, 7, 'up'))
        self.assertEqual(stepper_event_position('scroll_v', 15, 54, 'down'),
                         (7, 46, 'down'))

    def test_existing_default_direction_is_preserved(self):
        self.assertEqual(stepper_event_position('scroll_h', 220, 15),
                         (212, 7, 'right'))
        self.assertEqual(stepper_event_position('scroll_v', 15, 54),
                         (7, 46, 'down'))

    def test_direction_must_match_scrollbar_orientation(self):
        with self.assertRaisesRegex(ValueError, 'horizontal'):
            stepper_event_position('scroll_h', 220, 15, 'up')
        with self.assertRaisesRegex(ValueError, 'vertical'):
            stepper_event_position('scroll_v', 15, 54, 'left')
        with self.assertRaisesRegex(ValueError, 'GtkScrollbar'):
            stepper_event_position('push', 64, 48, 'left')

    def test_private_probe_keeps_geometry_range_and_piece_explicit(self):
        self.assertEqual(capture_probe(request(capture_length=360,
            capture_thickness=19, capture_value=10, capture_page_size=40,
            capture_part='thumb', capture_direction='right')), {
                'length_px': 360, 'thickness_px': 19,
                'value': 10, 'page_size': 40,
                'part': 'thumb', 'direction': 'right'})

    def test_private_geometry_does_not_mutate_loaded_project(self):
        source = {'recipes': {'gtk2': {
            'visible_controls': 65535, 'visible_categories': 31,
            'selected_control': 0, 'edit_state': 0,
            'positions': [[10, 10] for _ in range(16)],
            'sizes': [[0, 0] for _ in range(16)]}}}
        before = copy.deepcopy(source)
        candidate = private_capture_model(source, 11, capture_probe(request(
            capture_control=11, capture_length=360, capture_thickness=19,
            capture_direction='down')))
        self.assertEqual(source, before)
        self.assertEqual(candidate['recipes']['gtk2']['sizes'][11], [19, 360])
        self.assertEqual(candidate['recipes']['gtk2']['visible_controls'], 1 << 11)

    def test_private_probe_rejects_range_and_orientation_mismatch(self):
        with self.assertRaisesRegex(ValueError, '0–100'):
            capture_probe(request(capture_value=80, capture_page_size=25))
        with self.assertRaisesRegex(ValueError, 'horizontal'):
            capture_probe(request(capture_direction='down'))

    def test_piece_crops_are_derived_from_actual_allocation(self):
        image = FakePixbuf(220, 15)
        arrow, direction = sample_piece(FakeRange((40, 105)), image,
                                        'scroll_h', 'arrow', 'left', 220, 15)
        self.assertEqual((arrow.crop, direction), ((2, 2, 11, 11), 'left'))
        button, direction = sample_piece(FakeRange((40, 105)), image,
                                         'scroll_h', 'arrow_button', 'right', 220, 15)
        self.assertEqual((button.crop, direction), ((205, 0, 15, 15), 'right'))
        trough, _ = sample_piece(FakeRange((40, 105)), image,
                                 'scroll_h', 'trough', 'auto', 220, 15)
        self.assertEqual(trough.crop, (15, 0, 190, 15))
        thumb, _ = sample_piece(FakeRange((40, 105)), image,
                                'scroll_h', 'thumb', 'auto', 220, 15)
        self.assertEqual(thumb.crop, (40, 0, 65, 15))

    def test_fitting_is_reported_as_outside_native_scrollbar(self):
        with self.assertRaisesRegex(ValueError, 'contêiner'):
            sample_piece(FakeRange((20, 30)), FakePixbuf(15, 80),
                         'scroll_v', 'fitting', 'auto', 15, 80)


if __name__ == '__main__':
    unittest.main()
