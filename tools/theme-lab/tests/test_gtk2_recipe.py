#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure GTK2 translation contract; native allocations tested separately."""
import copy
import sys
from pathlib import Path
import unittest
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gtk2_recipe import scrollbar_properties, scrollbar_rc, paint_scrollbars
import domainos_motif_art as art


def recipe():
    return {'geometry': {'bar_px': 15, 'shadow_px': 2, 'arrow_px': 11,
                         'thumb_cross_px': 11, 'arrow_thumb_gap_px': 1}}


class GeometryTests(unittest.TestCase):
    def test_native_recipe_and_no_palette_or_input_mutation(self):
        data = recipe(); before = copy.deepcopy(data)
        result = scrollbar_properties(data)
        self.assertEqual(result['slider-width'] + 2 * result['trough-border'], 15)
        self.assertEqual(result['stepper-size'], 15)
        self.assertEqual(result['stepper-spacing'], 0)
        self.assertIs(result['trough-under-steppers'], False)
        source = scrollbar_rc(data)
        self.assertNotIn('bg[', source)
        self.assertNotIn('engine', source)
        self.assertEqual(data, before)

    def test_sparse_piece_overrides_take_precedence(self):
        data = recipe()
        data['scrollbar_parts'] = {'trough': {'thickness_px': 23, 'shadow_px': 3},
                                   'thumb': {'cross_px': 17, 'gap_px': 2},
                                   'arrow': {'glyph_px': 15}}
        result = scrollbar_properties(data)
        self.assertEqual((result['slider-width'], result['stepper-size'], result['trough-border']), (17, 23, 3))

    def test_incompatible_geometry_is_not_clamped(self):
        for key, value in [('bar_px', 16), ('arrow_px', 10), ('thumb_cross_px', 0),
                           ('shadow_px', True), ('arrow_thumb_gap_px', 129)]:
            with self.subTest(key=key):
                data = recipe(); data['geometry'][key] = value
                with self.assertRaises(ValueError): scrollbar_properties(data)


class PieceReliefTests(unittest.TestCase):
    def test_native_stepper_trough_junction_caps_follow_shared_rule_and_palette(self):
        import backend
        from PIL import Image
        root = Path(__file__).resolve().parents[3]
        builder = backend.load_builder(root)
        palette = {name: '#%06x' % (index + 1)
                   for index, name in enumerate(dict.fromkeys(
                       name for names in builder.art.ROLES.values() for name in names))}
        expected = art.gtk2_stepper_trough_junctions()
        with tempfile.TemporaryDirectory(prefix='gtk2-junction-caps-') as directory:
            generated = paint_scrollbars(builder, recipe(), palette, Path(directory))
            rc = Path(generated['rc']).read_text(encoding='utf-8')
            self.assertIn('orientation = HORIZONTAL file = "trough-horizontal-normal.png" border = { 5, 5, 2, 2 }', rc)
            self.assertIn('orientation = VERTICAL file = "trough-vertical-normal.png" border = { 2, 2, 5, 5 }', rc)
            for orientation, names, expected_size in (
                    ('horizontal', ('horizontal_start_rows', 'horizontal_end_rows'), (30,15)),
                    ('vertical', ('vertical_start_rows', 'vertical_end_rows'), (15,30))):
                with Image.open(Path(directory) / f'trough-{orientation}-normal.png') as image:
                    image = image.convert('RGBA')
                    self.assertEqual(image.size, expected_size)
                    profile = expected['normal_cross_axis_profile']
                    if orientation == 'horizontal':
                        actual_profile = [image.getpixel((10, y)) for y in range(image.height)]
                    else:
                        actual_profile = [image.getpixel((x, 10)) for x in range(image.width)]
                    expected_profile = [tuple(
                        int(art.evaluate(art.pixel_plan('button', token), palette)[i:i+2], 16)
                        for i in (1, 3, 5)) + (255,) for token in profile]
                    self.assertEqual(actual_profile, expected_profile, orientation)
                    starts, ends = (expected[name] for name in names)
                    for rows, x0, y0 in ((starts,0,0), (ends,0,0)):
                        for y,row in enumerate(rows):
                            for x,token in enumerate(row):
                                if orientation == 'horizontal':
                                    px = x0 + (x if rows is starts else image.width-5+x)
                                    py = y0 + y
                                else:
                                    px = x0 + x
                                    py = y0 + (y if rows is starts else image.height-5+y)
                                rgb = tuple(int(art.evaluate(art.pixel_plan('button',token),palette)[i:i+2],16)
                                            for i in (1,3,5))
                                self.assertEqual(image.getpixel((px,py)),rgb+(255,))

    def test_explicit_trough_relief_updates_the_cross_axis_profile(self):
        import backend
        from PIL import Image
        root = Path(__file__).resolve().parents[3]
        builder = backend.load_builder(root)
        palette = {name: '#%06x' % (index + 1)
                   for index, name in enumerate(dict.fromkeys(
                       name for names in builder.art.ROLES.values() for name in names))}
        base = art.gtk2_stepper_trough_junctions()['normal_cross_axis_profile']
        variants = {
            'sunken': base,
            'raised': tuple({'dark': 'light', 'light': 'dark'}.get(token, token)
                            for token in base),
            'flat': tuple('face' for _ in base),
        }
        for relief, tokens in variants.items():
            with self.subTest(relief=relief), tempfile.TemporaryDirectory(
                    prefix='gtk2-cross-axis-relief-') as directory:
                data = recipe()
                data['scrollbar_parts'] = {'trough': {'state_relief': {'normal': relief}}}
                paint_scrollbars(builder, data, palette, Path(directory))
                for orientation in ('horizontal', 'vertical'):
                    with Image.open(Path(directory) / f'trough-{orientation}-normal.png') as image:
                        image = image.convert('RGBA')
                        actual = ([image.getpixel((10, y)) for y in range(image.height)]
                                  if orientation == 'horizontal' else
                                  [image.getpixel((x, 10)) for x in range(image.width)])
                    expected = [tuple(
                        int(art.evaluate(art.pixel_plan('button', token), palette)[i:i+2], 16)
                        for i in (1, 3, 5)) + (255,) for token in tokens]
                    self.assertEqual(actual, expected, f'{orientation}/{relief}')

    def test_scrollbar_style_identity_tracks_effective_palette_for_live_reload(self):
        import backend
        root = Path(__file__).resolve().parents[3]
        builder = backend.load_builder(root)
        palette_a = {name: '#607080' for names in builder.art.ROLES.values() for name in names}
        palette_b = {name: '#a0b0c0' for names in builder.art.ROLES.values() for name in names}
        data = recipe()
        with tempfile.TemporaryDirectory(prefix='gtk2-style-identity-') as directory:
            first = paint_scrollbars(builder, data, palette_a, Path(directory) / 'first')
            second = paint_scrollbars(builder, data, palette_b, Path(directory) / 'second')
            self.assertNotEqual(first['scrollbar_style_id'], second['scrollbar_style_id'])
            for receipt in (first, second):
                ident = receipt['scrollbar_style_id']
                content = Path(receipt['rc']).read_text(encoding='utf-8')
                self.assertIn('class "GtkScrollbar" style : highest "theme-lab-gtk2-scroll-paint-' + ident + '"', content)
                self.assertIn('style "theme-lab-gtk2-scroll-geometry-' + ident + '"', content)

    def test_isolated_relief_preserves_geometry_alpha_and_other_assets(self):
        import backend
        from PIL import Image
        root = Path(__file__).resolve().parents[3]
        builder = backend.load_builder(root)
        # Artificial uniform role inputs; no product scheme or profile is used.
        palette = {name: '#607080' for names in builder.art.ROLES.values() for name in names}
        data = recipe()
        with tempfile.TemporaryDirectory(prefix='gtk2-piece-') as directory:
            base, changed = Path(directory) / 'base', Path(directory) / 'changed'
            paint_scrollbars(builder, data, palette, base)
            data['scrollbar_parts'] = {'arrow': {'state_relief': {'normal': 'flat'}}}
            before = copy.deepcopy(data)
            paint_scrollbars(builder, data, palette, changed)
            for direction in ('left', 'right', 'up', 'down'):
                name = 'arrow-' + direction + '-normal.png'
                a, b = Image.open(base / name), Image.open(changed / name)
                self.assertEqual(a.size, b.size)
                self.assertEqual(a.size, (15, 15))
                self.assertEqual(a.getchannel('A').tobytes(), b.getchannel('A').tobytes())
                self.assertNotEqual(a.tobytes(), b.tobytes())
            for path in base.glob('*.png'):
                if path.name.startswith('arrow-') and path.name.endswith('-normal.png'): continue
                self.assertEqual(path.read_bytes(), (changed / path.name).read_bytes(), path.name)
            self.assertEqual(data, before)

    def test_unsupported_state_fails_without_erasing_recipe(self):
        import backend
        builder = backend.load_builder(Path(__file__).resolve().parents[3])
        data = recipe()
        data['scrollbar_parts'] = {'trough': {'state_relief': {'pressed': 'flat'}}}
        before = copy.deepcopy(data)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'unsupported piece'):
                paint_scrollbars(builder, data, {}, directory)
        self.assertEqual(data, before)


if __name__ == '__main__': unittest.main()
