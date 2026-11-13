# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_entries import paint_entry, selected_fragment


class EntryPaintTests(unittest.TestCase):
    def test_missing_roles_leave_no_output(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-entry-pure-') as temp:
            target = Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_entry(backend.load_builder(ROOT), model()['recipes']['gtk2'], {}, target)
            self.assertFalse(target.exists())

    def test_palette_and_geometry_qualify_styles_without_mutation(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        original = copy.deepcopy(recipe)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-entry-pure-') as temp:
            first = paint_entry(builder, recipe, palette, Path(temp)/'first')
            second = paint_entry(builder, recipe, palette, Path(temp)/'second')
            self.assertEqual(first['style_id'], second['style_id'])
            changed = dict(palette)
            key = builder.art.ROLES['view'][0]
            changed[key] = '#010203'
            third = paint_entry(builder, recipe, changed, Path(temp)/'third')
            self.assertNotEqual(first['style_id'], third['style_id'])
            self.assertNotEqual(first['assets'], third['assets'])
            self.assertEqual(
                [name for name in first['assets'] if 'focus' in name],
                [name for name in third['assets'] if 'focus' in name],
                'changing only the field text role must not alter the focus outline',
            )
            rc = Path(third['rc']).read_text()
            self.assertIn('text[SELECTED] = "#010203"', rc)
            selected_background = '#%02x%02x%02x' % builder.art._rgb(
                palette[builder.art.ROLES['view-fg'][0]])
            self.assertIn('base[SELECTED] = "' + selected_background + '"', rc)
            view_bg = '#%02x%02x%02x' % builder.art._rgb(
                palette[builder.art.ROLES['view'][0]])
            view_fg = '#%02x%02x%02x' % builder.art._rgb(
                palette[builder.art.ROLES['view-fg'][0]])
            self.assertIn('base[NORMAL] = "' + view_bg + '"', rc)
            self.assertIn('text[NORMAL] = "' + view_fg + '"', rc)
            self.assertIn('GtkEntry::inner-border', rc)
            self.assertIn('border = { 2, 2, 2, 2 }', rc)
            self.assertIn('GtkEntry::state-hint = 1', rc)
            self.assertIn('GtkWidget::cursor-aspect-ratio = 0.0', rc)
            self.assertIn('detail = "entry" state = ACTIVE', rc)
            asset = Image.open(Path(temp)/'third'/third['assets'][0]).convert('RGB')
            self.assertEqual(asset.size, (5, 5))
            dark = builder.art.evaluate(builder.art.pixel_plan('window', 'dark'), palette)
            self.assertEqual(asset.getpixel((0, 0)), builder.art._rgb(dark))
            focus_name = next(name for name in third['assets'] if name.startswith('entry-focus-'))
            focus_asset = Image.open(Path(temp)/'third'/focus_name).convert('RGBA')
            expected_focus = builder.art._rgb(palette[builder.art.ROLES['focus'][0]])
            self.assertEqual(focus_asset.getpixel((0, 0))[:3], expected_focus)
            self.assertEqual(focus_asset.getpixel((2, 2))[3], 0)
            changed_focus = dict(palette)
            focus_role = builder.art.ROLES['focus'][0]
            changed_focus[focus_role] = '#010203'
            focused = paint_entry(builder, recipe, changed_focus, Path(temp)/'focus-changed')
            self.assertNotEqual(first['style_id'], focused['style_id'])
            self.assertNotEqual(first['assets'], focused['assets'])
            recipe['geometry']['control_padding_px'] += 1
            fourth = paint_entry(builder, recipe, palette, Path(temp)/'fourth')
            self.assertNotEqual(first['style_id'], fourth['style_id'])
        recipe['geometry']['control_padding_px'] -= 1
        self.assertEqual(recipe, original)

    def test_forced_press_is_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError, 'unsupported forced state'):
            selected_fragment(model()['recipes']['gtk2'], 'pressed', None, None)


if __name__ == '__main__':
    unittest.main()
