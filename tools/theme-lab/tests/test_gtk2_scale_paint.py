# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_scales import paint_scale, selected_fragment


class ScalePaintTests(unittest.TestCase):
    def test_missing_roles_leave_no_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-scale-pure-') as temp:
            target = Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_scale(backend.load_builder(ROOT), model()['recipes']['gtk2'], {}, target)
            self.assertFalse(target.exists())

    def test_palette_and_geometry_qualify_styles_without_mutation(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        original = copy.deepcopy(recipe)
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-scale-pure-') as temp:
            first = paint_scale(builder, recipe, palette, Path(temp)/'first')
            second = paint_scale(builder, recipe, palette, Path(temp)/'second')
            self.assertEqual(first['style_id'], second['style_id'])
            changed = dict(palette)
            key = builder.art.ROLES['button-fg'][0]
            changed[key] = '#010203'
            third = paint_scale(builder, recipe, changed, Path(temp)/'third')
            self.assertNotEqual(first['style_id'], third['style_id'])
            self.assertEqual(first['assets'], third['assets'])
            rc = Path(third['rc']).read_text()
            self.assertIn('fg[SELECTED] = "#010203"', rc)
            self.assertIn('GtkRange::slider-width', rc)
            self.assertIn('GtkRange::slider-width = 8', rc)
            self.assertIn('GtkScale::slider-length = 27', rc)
            recipe['geometry']['control_padding_px'] += 1
            fourth = paint_scale(builder, recipe, palette, Path(temp)/'fourth')
            self.assertNotEqual(first['style_id'], fourth['style_id'])
            recipe['geometry']['scale_slider_length_px'] = 31
            fifth = paint_scale(builder, recipe, palette, Path(temp)/'fifth')
            self.assertNotEqual(first['style_id'], fifth['style_id'])
        recipe['geometry']['control_padding_px'] -= 1
        recipe['geometry'].pop('scale_slider_length_px')
        self.assertEqual(recipe, original)

    def test_invalid_dimension_leaves_no_output(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        for key in ('scale_slider_width_px', 'scale_slider_length_px'):
            for invalid in (True, 0, 129, '11'):
                recipe = model()['recipes']['gtk2']
                recipe['geometry'][key] = invalid
                with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-scale-pure-') as temp:
                    target = Path(temp)/'absent'
                    with self.assertRaisesRegex(ValueError, key):
                        paint_scale(builder, recipe, palette, target)
                    self.assertFalse(target.exists())

    def test_forced_press_is_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError, 'unsupported forced state'):
            selected_fragment(model()['recipes']['gtk2'], 'pressed', None, None)


if __name__ == '__main__':
    unittest.main()
