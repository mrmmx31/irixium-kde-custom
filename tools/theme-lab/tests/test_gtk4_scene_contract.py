# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import unittest
from test_backend import model
from gtk4_scene_contract import push_records
from gtk4_canvas import canvas_css
from test_backend import backend, ROOT


class PushContractTests(unittest.TestCase):
    def test_mixed_scene_returns_only_supported_push_records(self):
        records = push_records(model())
        self.assertEqual([record['id'] for record in records], ['push'])

    def test_layout_and_state_are_not_mutated(self):
        project = model()
        recipe = project['recipes']['gtk4']
        recipe.update(visible_controls=1, edit_state=1, selected_control=0)
        before = copy.deepcopy(project)
        record = push_records(project)[0]
        self.assertEqual(record['forced_state'], 1)
        self.assertEqual(project, before)

    def test_invalid_geometry_and_hidden_scene(self):
        project = model()
        recipe = project['recipes']['gtk4']
        recipe.update(visible_controls=0)
        self.assertEqual(push_records(project), [])
        recipe['geometry']['shadow_px'] = -1
        with self.assertRaises(ValueError):
            push_records(project)

    def test_canvas_requires_all_effective_window_roles(self):
        art = backend.load_builder(ROOT).art
        with self.assertRaisesRegex(ValueError, 'effective KDE role'):
            canvas_css(art, {})
        palette = {key: '#748596' for role in ('window', 'window-fg') for key in art.ROLES[role]}
        name, css = canvas_css(art, palette)
        self.assertIn(name + ':disabled', css)
        self.assertIn(name + ':backdrop', css)


if __name__ == '__main__':
    unittest.main()
