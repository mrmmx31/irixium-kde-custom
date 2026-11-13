# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_arrows import paint_arrow, selected_fragment


class ArrowPaintTests(unittest.TestCase):
    def test_missing_roles_leave_no_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-arrow-pure-') as temp:
            target = Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_arrow(backend.load_builder(ROOT), model()['recipes']['gtk2'], {}, target)
            self.assertFalse(target.exists())

    def test_palette_and_geometry_qualify_styles_without_mutation(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        original = copy.deepcopy(recipe)
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-arrow-pure-') as temp:
            first = paint_arrow(builder, recipe, palette, Path(temp)/'first')
            second = paint_arrow(builder, recipe, palette, Path(temp)/'second')
            self.assertEqual(first['style_id'], second['style_id'])
            changed = dict(palette)
            key = builder.art.ROLES['button-fg'][0]
            changed[key] = '#010203'
            third = paint_arrow(builder, recipe, changed, Path(temp)/'third')
            self.assertNotEqual(first['style_id'], third['style_id'])
            self.assertEqual(first['assets'], third['assets'])
            rc = Path(third['rc']).read_text()
            self.assertIn('fg[SELECTED] = "#010203"', rc)
            self.assertIn('GtkButton::inner-border', rc)
            recipe['geometry']['font_px'] += 1
            fourth = paint_arrow(builder, recipe, palette, Path(temp)/'fourth')
            self.assertNotEqual(first['style_id'], fourth['style_id'])
        recipe['geometry']['font_px'] -= 1
        self.assertEqual(recipe, original)

    def test_invalid_dimension_leaves_no_output(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        for invalid in (True, 0, 128, 12, '11'):
            recipe = model()['recipes']['gtk2']
            recipe['geometry']['arrow_px'] = invalid
            with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-arrow-pure-') as temp:
                target = Path(temp)/'absent'
                with self.assertRaisesRegex(ValueError, 'arrow_px'):
                    paint_arrow(builder, recipe, palette, target)
                self.assertFalse(target.exists())

    def test_button_relief_preserves_glyph_and_disabled_priority(self):
        from gtk2_arrows import snapshot_images
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        original = snapshot_images(builder,recipe,palette)
        recipe['scrollbar_parts'] = {'arrow_button':{'state_relief':{'pressed':'flat'}}}
        changed = snapshot_images(builder,recipe,palette)
        self.assertNotEqual(original['normal','pressed','panel'], changed['normal','pressed','panel'])
        for context in ('normal','backdrop','disabled'):
            for interaction in ('idle','pressed','hover'):
                for direction in ('up','down','left','right'):
                    self.assertEqual(original[context,interaction,direction],changed[context,interaction,direction])
        self.assertEqual(original['disabled','pressed','panel'],changed['disabled','pressed','panel'])
        recipe['scrollbar_parts']['arrow_button']['state_relief']['focus']='flat'
        with self.assertRaisesRegex(ValueError,'unsupported button relief'):
            snapshot_images(builder,recipe,palette)

    def test_sparse_button_geometry_and_glyph_relief_are_independent(self):
        from gtk2_arrows import snapshot_images, geometry_lines, validate_geometry
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        original = snapshot_images(builder,recipe,palette)
        recipe['scrollbar_parts']={'arrow_button':{'shadow_px':1,'padding_px':1}}
        lines=geometry_lines(recipe)
        self.assertIn('  xthickness = 1',lines)
        self.assertIn('  GtkButton::inner-border = { 1, 1, 1, 1 }',lines)
        changed=snapshot_images(builder,recipe,palette)
        self.assertNotEqual(original['normal','idle','panel'],changed['normal','idle','panel'])
        self.assertEqual(original['normal','idle','down'],changed['normal','idle','down'])
        recipe['scrollbar_parts']['arrow']={'state_relief':{'normal':'flat'}}
        flat=snapshot_images(builder,recipe,palette)
        self.assertNotEqual(changed['normal','idle','down'],flat['normal','idle','down'])
        self.assertEqual(changed['normal','idle','panel'],flat['normal','idle','panel'])
        recipe['scrollbar_parts']['arrow_button']['padding_px']=2
        with self.assertRaisesRegex(ValueError,'must fit reserved extent'):
            validate_geometry(recipe)

    def test_forced_focus_is_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError, 'unsupported forced state'):
            selected_fragment(model()['recipes']['gtk2'], 'focus', None, None)


if __name__ == '__main__':
    unittest.main()
