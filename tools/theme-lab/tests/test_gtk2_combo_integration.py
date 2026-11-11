# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import validate_snapshot
from native_scene_gtk2 import ScrollbarScene
from gtk2_combos import (OPTION_INDICATOR_HEIGHT, OPTION_INDICATOR_WIDTH,
                         HEADER_RELIEF_MIX, header_relief_plan, paint_combo,
                         combo_geometry, snapshot_images)

TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class ComboIntegrationTests(unittest.TestCase):
    def test_missing_roles_do_not_create_output(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-combo-roles-') as temp:
            target = Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_combo(backend.load_builder(ROOT), model()['recipes']['gtk2'], {}, target)
            self.assertFalse(target.exists())

    def test_invalid_arrow_geometry_is_rejected(self):
        recipe = model()['recipes']['gtk2']
        for value in (0, 129, True, 3.5):
            recipe['geometry']['arrow_px'] = value
            with self.assertRaisesRegex(ValueError, 'arrow_px'):
                combo_geometry(recipe)

    def test_option_indicator_matches_motif_outline_and_semantic_roles(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art,
                                          backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        with backend.recipe_rules(builder, recipe['palette']):
            images = snapshot_images(builder, recipe, palette)
        normal = Image.open(BytesIO(images['normal', 'arrow'][1])).convert('RGBA')
        pressed = Image.open(BytesIO(images['pressed', 'arrow'][1])).convert('RGBA')
        self.assertEqual(normal.size, (OPTION_INDICATOR_WIDTH, OPTION_INDICATOR_HEIGHT))
        self.assertEqual(normal.size, (14, 8))
        expected = (
            'LLLLLLLLLLLLLL',
            'LLLLLLLLLLLLLD',
            'LLFFFFFFFFFFDD',
            'LLFFFFFFFFFFDD',
            'LLFFFFFFFFFFDD',
            'LLFFFFFFFFFFDD',
            'LLDDDDDDDDDDDD',
            'LDDDDDDDDDDDDD',
        )
        light = tuple(builder.art._rgb(builder.art.evaluate(
            builder.art.pixel_plan('button', 'light'), palette))) + (255,)
        dark = tuple(builder.art._rgb(builder.art.evaluate(
            builder.art.pixel_plan('button', 'dark'), palette))) + (255,)
        face = tuple(builder.art._rgb(builder.art.evaluate(
            builder.art.pixel_plan('button', 'face'), palette))) + (255,)
        for y, row in enumerate(expected):
            for x, token in enumerate(row):
                color = {'L': light, 'D': dark, 'F': face}[token]
                self.assertEqual(normal.getpixel((x, y)), color, (x, y, token))
        self.assertEqual(normal.getpixel((0, 0)), light)
        self.assertEqual(normal.getpixel((13, 0)), light)
        self.assertEqual(normal.getpixel((0, 7)), light)
        self.assertEqual(normal.getpixel((13, 1)), dark)
        self.assertEqual(normal.getpixel((1, 7)), dark)
        self.assertEqual(normal.getpixel((7, 4)), face)
        self.assertEqual(pressed.getpixel((0, 0)), dark)
        self.assertEqual(pressed.getpixel((13, 0)), dark)
        self.assertEqual(pressed.getpixel((13, 7)), light)
        self.assertEqual(pressed.getpixel((0, 0))[:3], dark[:3])

    def test_popup_surfaces_use_header_role_per_state(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art,
                                          backend.sha(source.read_bytes()))
        recipe = model()['recipes']['gtk2']
        with backend.recipe_rules(builder, recipe['palette']):
            images = snapshot_images(builder, recipe, palette)
        expected = {
            ('normal', 'popup'): ('header', 0, (1, 1)),
            ('normal', 'popup-shell'): ('header', 0, (5, 5)),
            ('normal', 'popup-selected'): ('header', 0, (5, 5)),
            ('normal', 'popup-pressed'): ('header', 0, (5, 5)),
            ('backdrop', 'popup'): ('header', 1, (1, 1)),
            ('backdrop', 'popup-shell'): ('header', 1, (5, 5)),
            ('backdrop', 'popup-selected'): ('header', 1, (5, 5)),
            ('backdrop', 'popup-pressed'): ('header', 1, (5, 5)),
            ('disabled', 'popup'): ('header', 2, (1, 1)),
            ('disabled', 'popup-shell'): ('header', 2, (5, 5)),
            ('disabled', 'popup-selected'): ('header', 2, (5, 5)),
            ('disabled', 'popup-pressed'): ('header', 2, (5, 5)),
        }
        for key, (role, index, size) in expected.items():
            filename, payload = images[key]
            pixel = Image.open(BytesIO(payload)).convert('RGBA')
            self.assertEqual(pixel.size, size, filename)
            role_name = builder.art.ROLES[role][index]
            rgb = builder.art._rgb(palette[role_name])
            center = (size[0]//2, size[1]//2)
            self.assertEqual(pixel.getpixel(center), (*rgb, 255), (key, role_name))

        # The popup's Header relief keeps its own Motif light/shade ratios
        # even though the shared GTK2 recipe overrides primary Button relief.
        relief_keys = (('normal', 'popup-shell'), ('normal', 'popup-selected'),
                       ('normal', 'popup-pressed'), ('backdrop', 'popup-shell'),
                       ('backdrop', 'popup-selected'), ('backdrop', 'popup-pressed'),
                       ('disabled', 'popup-shell'), ('disabled', 'popup-selected'),
                       ('disabled', 'popup-pressed'))
        for key in relief_keys:
            actual = Image.open(BytesIO(images[key][1])).convert('RGBA')
            down = key[1] == 'popup-pressed'
            mask = builder.art.bevel(builder.art.blank(5, 5, 'face'),
                                     thickness=2, down=down)
            role_index = {'normal': 0, 'backdrop': 1, 'disabled': 2}[key[0]]
            effective = dict(palette)
            for names in builder.art.ROLES.values():
                if names[role_index] in palette:
                    effective[names[0]] = palette[names[role_index]]
            for y, row in enumerate(mask):
                for x, token in enumerate(row):
                    if token is None:
                        continue
                    plan = header_relief_plan(builder, token)
                    if token in HEADER_RELIEF_MIX:
                        self.assertEqual(plan['mix'], HEADER_RELIEF_MIX[token])
                    value = builder.art.evaluate(plan, effective)
                    expected_pixel = tuple(int(value[n:n+2], 16)
                                            for n in (1, 3, 5)) + (255,)
                    self.assertEqual(actual.getpixel((x, y)), expected_pixel,
                                     (key, x, y, token))

    def test_popup_rc_owns_menuitem_background_instead_of_theme_engine_default(self):
        builder = backend.load_builder(ROOT)
        source = ROOT/'colors/DomainOS-SR10.4.colors'
        palette, _ = backend.native_roles(ROOT, source, builder.art,
                                          backend.sha(source.read_bytes()))
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-combo-popup-') as temp:
            result = paint_combo(builder, model()['recipes']['gtk2'], palette, Path(temp))
            rc = Path(result['rc']).read_text(encoding='utf-8')
            self.assertIn('function = BOX detail = "menuitem" state = NORMAL', rc)
            self.assertIn('function = BOX detail = "menuitem" state = PRELIGHT', rc)
            self.assertIn('border = { 2, 2, 2, 2 } stretch = TRUE', rc)
            self.assertIn('PopupItem_', rc)
            self.assertIn('PopupWindow_', rc)
            for asset in result['assets']:
                self.assertTrue((Path(temp)/asset).is_file(), asset)

    def test_generation_and_binding_guard_without_gui(self):
        data = model()
        data['selected_family'] = 'gtk2'
        data['recipes']['gtk2'].update(visible_controls=1 << 5, selected_control=5)
        original = copy.deepcopy(data)
        snippet = backend.snippet(ROOT, data, kdeglobals=ROOT/'colors/DomainOS-SR10.4.colors')
        self.assertEqual(snippet['source_kind'], 'translated_native_fragment')
        self.assertIn('function = ARROW', snippet['source'])
        with self.assertRaisesRegex(backend.Unavailable, 'origem explícita'):
            backend.snippet(ROOT, data)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-combo-generation-') as temp:
            folder = Path(temp)
            receipt = generate_scrollbar_snapshot(backend, ROOT, folder, data,
                                                  ROOT/'colors/DomainOS-SR10.4.colors')
            self.assertIn('combo', receipt['translated_controls'])
            self.assertFalse(receipt['recipe_applied'])
            self.assertFalse(receipt['scene_integrated'])
            self.assertEqual(validate_snapshot(backend, ROOT, receipt['rc'], data)['combo_style_id'],
                             receipt['combo_style_id'])
            manifest = folder/'GTK2-SCROLLBAR-PROPOSAL.json'
            receipt['combo_style_id'] = '0123456789abcdef'
            manifest.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'não corresponde aos recursos'):
                validate_snapshot(backend, ROOT, receipt['rc'], data)
        self.assertEqual(data, original)

    def test_missing_style_rejected_before_widget_creation(self):
        data = model()
        data['recipes']['gtk2']['visible_controls'] = 1 << 5
        with self.assertRaisesRegex(ValueError, 'estilo combobox'):
            ScrollbarScene(None, data)


if __name__ == '__main__':
    unittest.main()
