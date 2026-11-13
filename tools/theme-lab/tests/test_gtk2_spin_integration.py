# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import validate_snapshot
from native_scene_gtk2 import ScrollbarScene
from gtk2_spins import paint_spin, spin_geometry


class SpinIntegrationTests(unittest.TestCase):
    def test_missing_roles_do_not_create_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-spin-roles-') as temp:
            target = Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_spin(backend.load_builder(ROOT), model()['recipes']['gtk2'], {}, target)
            self.assertFalse(target.exists())

    def test_invalid_arrow_geometry_is_rejected(self):
        recipe = model()['recipes']['gtk2']
        for value in (0, 129, True, 3.5):
            recipe['geometry']['arrow_px'] = value
            with self.assertRaisesRegex(ValueError, 'arrow_px'):
                spin_geometry(recipe)

    def test_generation_and_binding_guard_without_gui(self):
        data = model()
        data['selected_family'] = 'gtk2'
        data['recipes']['gtk2'].update(visible_controls=1 << 6, selected_control=6)
        original = copy.deepcopy(data)
        snippet = backend.snippet(ROOT, data, kdeglobals=ROOT/'colors/DomainOS-SR10.4.colors')
        self.assertEqual(snippet['source_kind'], 'translated_native_fragment')
        self.assertIn('function = ARROW', snippet['source'])
        with self.assertRaisesRegex(backend.Unavailable, 'origem explícita'):
            backend.snippet(ROOT, data)
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-spin-generation-') as temp:
            folder = Path(temp)
            receipt = generate_scrollbar_snapshot(backend, ROOT, folder, data,
                                                  ROOT/'colors/DomainOS-SR10.4.colors')
            self.assertIn('spin', receipt['translated_controls'])
            self.assertFalse(receipt['recipe_applied'])
            self.assertFalse(receipt['scene_integrated'])
            self.assertEqual(validate_snapshot(backend, ROOT, receipt['rc'], data)['spin_style_id'],
                             receipt['spin_style_id'])
            manifest = folder/'GTK2-SCROLLBAR-PROPOSAL.json'
            receipt['spin_style_id'] = '0123456789abcdef'
            manifest.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'não corresponde aos recursos'):
                validate_snapshot(backend, ROOT, receipt['rc'], data)
        self.assertEqual(data, original)

    def test_missing_style_rejected_before_widget_creation(self):
        data = model()
        data['recipes']['gtk2']['visible_controls'] = 1 << 6
        with self.assertRaisesRegex(ValueError, 'estilo spin'):
            ScrollbarScene(None, data)


if __name__ == '__main__':
    unittest.main()
