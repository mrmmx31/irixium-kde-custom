# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_contract import scene
from native_scene_gtk2 import ScrollbarScene, scene_records
from gtk2_session import NativeSession


class SceneContractTests(unittest.TestCase):
    def test_radio_group_and_frame_records_are_supported(self):
        data=self.model();data['recipes']['gtk2']['visible_controls']|=8
        before=copy.deepcopy(data)
        self.assertEqual([r['index'] for r in scene_records(data)],[3,10,11])
        self.assertEqual(data,before)
        data['recipes']['gtk2']['visible_controls']|=1 << 15
        self.assertEqual([r['index'] for r in scene_records(data)],[3,10,11,15])

    def model(self):
        return {'recipes': {'gtk2': {'visible_controls': (1 << 10) | (1 << 11)},
                            'gtk3': {'visible_controls': 1}}}

    def test_independent_family_visibility_and_ids(self):
        model = self.model()
        before = copy.deepcopy(model)
        self.assertEqual([r['index'] for r in scene(model, 'gtk2')], [10, 11])
        self.assertEqual([r['index'] for r in scene(model, 'gtk3')], [0])
        self.assertEqual(model, before)

    def test_missing_frame_identity_is_not_silently_substituted(self):
        model = self.model()
        model['recipes']['gtk2']['visible_controls'] |= 1 << 15
        before = copy.deepcopy(model)
        with self.assertRaisesRegex(ValueError, 'estilo moldura'):
            ScrollbarScene(None, model)
        self.assertEqual(model, before)

    def test_anchor_records_supported_without_mutation(self):
        model = self.model()
        model['recipes']['gtk2']['length_anchor'] = [0]*10+[1,1]+[0]*4
        before=copy.deepcopy(model)
        self.assertEqual([r['length_anchor'] for r in scene_records(model)],[1,1])
        self.assertEqual(model,before)

    def test_forced_press_still_pending(self):
        for key, value in [('edit_state', 1)]:
            model = self.model()
            model['recipes']['gtk2'].update({key: value, 'selected_control': 10})
            before = copy.deepcopy(model)
            with self.assertRaises(ValueError): ScrollbarScene(None, model)
            self.assertEqual(model, before)

    def test_button_pressure_requires_explicit_bridge_scope(self):
        model = self.model()
        model['recipes']['gtk2'].update(visible_controls=1, selected_control=0, edit_state=1)
        with self.assertRaises(ValueError):
            scene_records(model)
        self.assertEqual(scene_records(model, allow_button_pressed=True)[0]['id'], 'push')
        model['recipes']['gtk2'].update(visible_controls=1 << 12, selected_control=12)
        with self.assertRaises(ValueError):
            scene_records(model)
        self.assertEqual(scene_records(model, allow_button_pressed=True)[0]['id'], 'arrow')
        model['recipes']['gtk2'].update(visible_controls=2, selected_control=1)
        with self.assertRaises(ValueError):
            scene_records(model, allow_button_pressed=True)

    def test_normal_scene_does_not_load_optional_bridge(self):
        with patch('gtk2_press_bridge.Gtk2PressBridge') as bridge:
            self.assertIsNone(NativeSession.pressure_bridge(Path('/unused'), self.model()))
            bridge.assert_not_called()

    def test_unsupported_pressure_rejected_before_loading_bridge(self):
        model = self.model()
        model['recipes']['gtk2'].update(selected_control=10, edit_state=1)
        with patch('gtk2_press_bridge.Gtk2PressBridge') as bridge:
            with self.assertRaises(ValueError):
                NativeSession.pressure_bridge(Path('/unused'), model)
            bridge.assert_not_called()

    def test_missing_bridge_rejected_during_preflight(self):
        model = self.model()
        model['recipes']['gtk2'].update(visible_controls=1, selected_control=0, edit_state=1)
        with self.assertRaisesRegex(ValueError, 'ponte de pressão ausente'):
            NativeSession.pressure_bridge(Path('/unused'), model)


if __name__ == '__main__': unittest.main()
