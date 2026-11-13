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
from gtk2_scales import paint_scale, geometry_lines

TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class ScaleIntegrationTests(unittest.TestCase):
    def test_missing_roles_do_not_create_output(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='qa-scale-roles-') as temp:
            target = Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_scale(backend.load_builder(ROOT), model()['recipes']['gtk2'], {}, target)
            self.assertFalse(target.exists())

    def test_invalid_slider_geometry_is_rejected(self):
        recipe = model()['recipes']['gtk2']
        for key in ('scale_slider_width_px', 'scale_slider_length_px'):
            for value in (0, 129, True, 3.5):
                recipe['geometry'][key] = value
                with self.assertRaisesRegex(ValueError, key):
                    geometry_lines(recipe)
                recipe['geometry'].pop(key)

    def test_custom_slider_dimensions_translate_to_gtk2_resources(self):
        recipe = model()['recipes']['gtk2']
        recipe['geometry']['scale_slider_width_px'] = 13
        recipe['geometry']['scale_slider_length_px'] = 33
        lines = geometry_lines(recipe)
        self.assertTrue(any(line.strip() == 'GtkRange::slider-width = 13' for line in lines))
        self.assertTrue(any(line.strip() == 'GtkScale::slider-length = 33' for line in lines))

    def test_generation_and_binding_guard_without_gui(self):
        data = model()
        data['selected_family'] = 'gtk2'
        data['recipes']['gtk2'].update(visible_controls=1 << 8, selected_control=8)
        original = copy.deepcopy(data)
        snippet = backend.snippet(ROOT, data, kdeglobals=ROOT/'colors/DomainOS-SR10.4.colors')
        self.assertEqual(snippet['source_kind'], 'translated_native_fragment')
        self.assertIn('function = SLIDER', snippet['source'])
        with self.assertRaisesRegex(backend.Unavailable, 'origem explícita'):
            backend.snippet(ROOT, data)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='qa-scale-generation-') as temp:
            folder = Path(temp)
            receipt = generate_scrollbar_snapshot(backend, ROOT, folder, data,
                                                  ROOT/'colors/DomainOS-SR10.4.colors')
            self.assertIn('scale_h', receipt['translated_controls'])
            self.assertFalse(receipt['recipe_applied'])
            self.assertFalse(receipt['scene_integrated'])
            self.assertEqual(validate_snapshot(backend, ROOT, receipt['rc'], data)['scale_style_id'],
                             receipt['scale_style_id'])
            manifest = folder/'GTK2-SCROLLBAR-PROPOSAL.json'
            receipt['scale_style_id'] = '0123456789abcdef'
            manifest.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'não corresponde aos recursos'):
                validate_snapshot(backend, ROOT, receipt['rc'], data)
        self.assertEqual(data, original)

    def test_missing_style_rejected_before_widget_creation(self):
        data = model()
        data['recipes']['gtk2']['visible_controls'] = 1 << 8
        with self.assertRaisesRegex(ValueError, 'estilo escala'):
            ScrollbarScene(None, data)


if __name__ == '__main__':
    unittest.main()
