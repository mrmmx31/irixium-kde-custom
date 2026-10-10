#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure layout checks; GI is never imported and no native preview is opened."""
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'preview_gtk.py'
spec = importlib.util.spec_from_file_location('theme_lab_preview_scene_test', SOURCE)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def project():
    return {'recipes': {'gtk3': {'visible_categories': 31, 'visible_controls': 65535,
                               'selected_control': 0, 'edit_state': 0,
                               'positions': [[16 + (i % 4)*160, 16 + (i // 4)*80] for i in range(16)]}}}


class SceneTests(unittest.TestCase):
    def test_all_native_control_ids_and_positions_are_preserved(self):
        data = project()
        original = copy.deepcopy(data)
        records = preview.scene(data)
        self.assertEqual([item['id'] for item in records], list(preview.CONTROLS))
        self.assertEqual([item['index'] for item in records], list(range(16)))
        self.assertEqual(records[15]['x'], 496)
        self.assertEqual(records[15]['y'], 256)
        self.assertEqual(data, original)
        self.assertNotIn('gi', sys.modules)

    def test_categories_and_controls_intersect_without_renumbering(self):
        data = project()
        data['recipes']['gtk3'].update(visible_categories=1 << 1,
                                      visible_controls=(1 << 4) | (1 << 6) | (1 << 14))
        records = preview.scene(data)
        self.assertEqual([item['id'] for item in records], ['entry', 'spin'])
        self.assertEqual([item['index'] for item in records], [4, 6])
        data['recipes']['gtk3']['visible_categories'] = 0
        self.assertEqual(preview.scene(data), [])

    def test_forced_state_applies_only_to_selected_visible_control(self):
        data = project()
        data['recipes']['gtk3'].update(selected_control=10, edit_state=2)
        records = preview.scene(data)
        self.assertEqual([item['id'] for item in records if item['forced_state']], ['scroll_h'])
        self.assertEqual(preview.EDIT_STATES[records[10]['forced_state']], 'disabled')
        data['recipes']['gtk3']['visible_controls'] ^= 1 << 10
        self.assertFalse(any(item['selected'] for item in preview.scene(data)))

    def test_old_recipe_receives_layout_defaults(self):
        records = preview.scene({'recipes': {'gtk3': {}}})
        self.assertEqual(len(records), 16)
        self.assertEqual((records[0]['x'], records[0]['y']), (16, 16))

    def test_invalid_masks_states_and_boolean_values_are_rejected(self):
        for key, value in [('visible_categories', 32), ('visible_controls', 65536),
                           ('selected_control', 16), ('edit_state', -1),
                           ('visible_controls', True), ('edit_state', 1.0)]:
            with self.subTest(key=key, value=value):
                data = project()
                data['recipes']['gtk3'][key] = value
                with self.assertRaises(ValueError):
                    preview.scene(data)

    def test_hidden_positions_are_still_validated(self):
        data = project()
        recipe = data['recipes']['gtk3']
        recipe.update(visible_categories=0, visible_controls=0)
        for value in (-1, 2049, True, 1.5):
            with self.subTest(value=value):
                recipe['positions'][15][0] = value
                with self.assertRaises(ValueError):
                    preview.scene(data)
        recipe['positions'][15] = [0, 2048]
        self.assertEqual(preview.scene(data), [])

    def test_positions_require_sixteen_exact_pairs(self):
        for replacement in ([], [[1, 2]]*15, [[1, 2, 3]]*16, 'not positions'):
            data = project()
            data['recipes']['gtk3']['positions'] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                preview.scene(data)

    def test_drag_clamps_coordinates_and_rejects_nonfinite_offsets(self):
        self.assertEqual(preview.drag_position((16, 80), -100, 3000), (0, 2048))
        self.assertEqual(preview.drag_position((16, 80), 12, -30), (28, 50))
        for offset in (float('nan'), float('inf'), True):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                preview.drag_position((16, 80), offset, 0)

    def test_stable_root_coordinates_keep_exact_delta_and_gdk_logical_units(self):
        self.assertEqual(preview.root_coordinates((True, 100.25, -200)), (100.25, -200))
        self.assertEqual(preview.root_coordinates((100.25, -200)), (100.25, -200))
        self.assertEqual(preview.root_drag_position((176, 16), (100, 200), (124, 218)), (200, 34))
        # A scale-2 GDK event already expresses a physical 48px move as 24
        # logical units. The layout conversion must not halve this again.
        self.assertEqual(preview.root_drag_position((176, 16), (50, 100), (74, 118)), (200, 34))
        self.assertEqual(preview.root_drag_position((176, 16), (100, 200), (-1000, 5000)), (0, 2048))
        for value in ((False, 1, 2), (True, float('nan'), 2), (True, 1, float('inf')),
                      (True, 1), (1, 2, 3), ('1', 2), None):
            with self.subTest(value=value):
                self.assertIsNone(preview.root_coordinates(value))
        with self.assertRaises(ValueError):
            preview.root_drag_position((176, 16), (100, 200), None)

    def test_event_root_getter_handles_mouse_touch_and_unavailable_coordinates(self):
        for result in ((True, 120.5, 90.25), (120.5, 90.25)):
            event = SimpleNamespace(get_root_coords=lambda: result)
            self.assertEqual(preview.event_root_position(event), (120.5, 90.25))
        self.assertIsNone(preview.event_root_position(None))
        self.assertIsNone(preview.event_root_position(SimpleNamespace()))
        def unavailable():
            raise RuntimeError('Unusable event')
        self.assertIsNone(preview.event_root_position(SimpleNamespace(get_root_coords=unavailable)))

    def test_drag_callbacks_do_not_feed_widget_motion_back_into_final_position(self):
        pointer = {'coords': (True, 100.0, 200.0), 'mask': 4}
        event = SimpleNamespace(get_root_coords=lambda: pointer['coords'],
                                get_state=lambda: (True, pointer['mask']))
        class Gesture:
            def __init__(self):
                self.handlers, self.states = {}, []
            @classmethod
            def new(cls, _widget):
                return cls()
            def set_button(self, _button):
                pass
            def set_propagation_phase(self, _phase):
                pass
            def group(self, other):
                self.grouped = other
            def get_current_sequence(self):
                return None  # Mouse sequences use NULL in the native API.
            def get_last_event(self, _sequence):
                return event
            def set_state(self, state):
                self.states.append(state)
            def connect(self, signal, handler):
                self.handlers[signal] = handler
        box = SimpleNamespace(scale=1)
        box.get_scale_factor = lambda: box.scale
        native = preview.NativeScene.__new__(preview.NativeScene)
        native.Gtk = SimpleNamespace(GestureMultiPress=Gesture, GestureDrag=Gesture,
                                     PropagationPhase=SimpleNamespace(CAPTURE='capture'),
                                     EventSequenceState=SimpleNamespace(CLAIMED='claimed', DENIED='denied'))
        native.Gdk = SimpleNamespace(ModifierType=SimpleNamespace(CONTROL_MASK=4))
        native.gestures, native.dragging = [], {}
        movements, events = [], []
        native.fixed = SimpleNamespace(move=lambda _box, x, y: movements.append((x, y)))
        native.emit = lambda action, index, **fields: events.append((action, index, fields))
        native.status = SimpleNamespace(set_text=lambda _text: None)
        record = {'index': 1, 'id': 'toggle', 'x': 176, 'y': 16}
        native.control_capture(box, record)
        select, drag = native.gestures
        self.assertIs(select.grouped, drag)
        drag.handlers['drag-begin'](drag, 20, 20)
        pointer['coords'] = (True, 112.0, 209.0)
        drag.handlers['drag-update'](drag, 12, 9)
        pointer['coords'] = (True, 124.0, 218.0)
        # GTK's widget-relative offsets become smaller as the box moves.
        # They must no longer control the proposed layout destination.
        drag.handlers['drag-update'](drag, 12, 9)
        drag.handlers['drag-end'](drag, 0, 0)
        self.assertEqual(movements, [(188, 25), (200, 34), (200, 34)])
        self.assertEqual((record['x'], record['y']), (200, 34))
        self.assertEqual(events, [('move', 1, {'x': 200, 'y': 34,
                                              'coordinate_space': 'gtk_logical_px', 'scale_factor': 1})])
        self.assertFalse(native.dragging)
        # Ordinary native input stays denied by the editor capture.
        pointer['mask'] = 0
        drag.handlers['drag-begin'](drag, 20, 20)
        self.assertEqual(drag.states[-1], 'denied')
        self.assertFalse(native.dragging)
        # Scale changes and cancellation restore the origin and release the
        # reload guard, without publishing a misleading final position.
        pointer['mask'] = 4
        drag.handlers['drag-begin'](drag, 20, 20)
        box.scale = 2
        drag.handlers['drag-update'](drag, 12, 9)
        self.assertEqual(movements[-1], (200, 34))
        self.assertFalse(native.dragging)
        self.assertEqual(len(events), 1)

    def test_other_toolkit_is_not_simulated(self):
        with self.assertRaisesRegex(ValueError, 'GTK3 reais'):
            preview.scene(project(), 'gtk4')

    def test_modifier_out_parameter_is_normalized_without_gtk(self):
        self.assertEqual(preview.modifier_value((True, 4)), 4)
        self.assertEqual(preview.modifier_value((False, 4)), 0)
        self.assertEqual(preview.modifier_value(4), 4)
        self.assertEqual(preview.modifier_value((True,)), 0)

    def test_arrow_factory_is_a_button_with_a_native_click_event(self):
        class Button:
            def __init__(self):
                self.classes, self.handlers = [], {}

            def get_style_context(self):
                return SimpleNamespace(add_class=self.classes.append)

            def connect(self, signal, callback):
                self.handlers[signal] = callback

        native = preview.NativeScene.__new__(preview.NativeScene)
        # A display-only Gtk.Arrow is intentionally unavailable here: only a
        # button can expose the ordinary native click contract under review.
        native.Gtk = SimpleNamespace(Button=Button)
        events = []
        native.changed = lambda index, **fields: events.append((index, fields))
        widget = native.factory('arrow', 12)
        self.assertIsInstance(widget, Button)
        self.assertEqual(widget.classes, ['theme-lab-arrow'])
        widget.handlers['clicked'](widget)
        self.assertEqual(events, [(12, {'clicked': True})])
        self.assertNotIn('gi', sys.modules)


if __name__ == '__main__':
    unittest.main()
