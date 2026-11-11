# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_spins import paint_spin, selected_fragment


class SpinPaintTests(unittest.TestCase):
    def test_missing_roles_leave_no_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-spin-pure-') as temp:
            target = Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_spin(backend.load_builder(ROOT), model()['recipes']['gtk2'], {}, target)
            self.assertFalse(target.exists())

    def test_palette_and_geometry_qualify_styles_without_mutation(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        original = copy.deepcopy(recipe)
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-spin-pure-') as temp:
            first = paint_spin(builder, recipe, palette, Path(temp)/'first')
            second = paint_spin(builder, recipe, palette, Path(temp)/'second')
            self.assertEqual(first['style_id'], second['style_id'])
            changed = dict(palette)
            key = builder.art.ROLES['selection-fg'][0]
            changed[key] = '#010203'
            third = paint_spin(builder, recipe, changed, Path(temp)/'third')
            self.assertNotEqual(first['style_id'], third['style_id'])
            self.assertEqual(first['assets'], third['assets'])
            rc = Path(third['rc']).read_text()
            self.assertIn('text[SELECTED] = "#010203"', rc)
            self.assertIn('GtkEntry::inner-border', rc)
            recipe['geometry']['control_padding_px'] += 1
            fourth = paint_spin(builder, recipe, palette, Path(temp)/'fourth')
            self.assertNotEqual(first['style_id'], fourth['style_id'])
        recipe['geometry']['control_padding_px'] -= 1
        self.assertEqual(recipe, original)

    def test_forced_press_is_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError, 'unsupported forced state'):
            selected_fragment(model()['recipes']['gtk2'], 'pressed', None, None)


if __name__ == '__main__':
    unittest.main()
