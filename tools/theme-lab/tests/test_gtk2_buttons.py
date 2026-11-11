# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from gtk2_buttons import (PUSH_IMAGE_BORDER_PX, VUE_PUSH_FRAME, geometry,
                          paint_button, geometry_lines, push_geometry_lines,
                          push_frame_pixels, role_source, focus_role)
from test_backend import model, ROOT

class ButtonTests(unittest.TestCase):
    def test_geometry_is_proposed_and_invalid_input_is_rejected(self):
        recipe = model()['recipes']['gtk2']
        self.assertEqual(geometry(recipe), (2, 4, 13))
        self.assertIn('  GtkButton::inner-border = { 4, 4, 4, 4 }', push_geometry_lines(recipe))
        self.assertIn('  GtkButton::focus-line-pattern = ""', push_geometry_lines(recipe))
        self.assertIn('  GtkButton::focus-line-width = 2', push_geometry_lines(recipe))
        self.assertIn('  GtkButton::focus-padding = 2', push_geometry_lines(recipe))
        self.assertIn('  GtkButton::interior-focus = 0', push_geometry_lines(recipe))
        self.assertIn('  xthickness = 2', push_geometry_lines(recipe))
        self.assertIn('  ythickness = 0', push_geometry_lines(recipe))
        self.assertIn('  ythickness = 2', geometry_lines(recipe))
        self.assertEqual(PUSH_IMAGE_BORDER_PX, 6)
        self.assertEqual(len(VUE_PUSH_FRAME), 13)
        self.assertTrue(all(len(row) == 13 for row in VUE_PUSH_FRAME))
        normal_frame = push_frame_pixels('normal')
        pressed_frame = push_frame_pixels('pressed')
        self.assertEqual(normal_frame[0], ['dark'] * 13)
        self.assertEqual(pressed_frame[0], ['face'] * 13)
        for y in range(1, 13): self.assertEqual(pressed_frame[y], normal_frame[y])
        for key, value in [('shadow_px', True), ('control_padding_px', -1), ('font_px', 49)]:
            bad = copy.deepcopy(recipe); bad['geometry'][key] = value
            with self.assertRaises(ValueError): geometry(bad)

    def test_missing_state_role_rejected_before_output(self):
        recipe = model()['recipes']['gtk2']; builder = backend.load_builder(ROOT)
        with tempfile.TemporaryDirectory(dir=Path.home() / 'tempia', prefix='i167-button-pure-') as folder:
            target = Path(folder) / 'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_button(builder, recipe, {}, target)
            self.assertFalse(target.exists())

    def test_enabled_face_uses_dynamic_header_roles_and_disabled_uses_button_roles(self):
        recipe = model()['recipes']['gtk2']; builder = backend.load_builder(ROOT)
        colors = dict(builder.art.DEFAULT)
        colors.update({
            'theme_header_background_breeze': '#123456',
            'theme_header_background_backdrop_breeze': '#234567',
            'theme_header_foreground_breeze': '#345678',
            'theme_header_foreground_backdrop_breeze': '#456789',
            'theme_button_background_insensitive_breeze': '#56789a',
            'theme_button_background_backdrop_insensitive_breeze': '#6789ab',
            'theme_button_foreground_insensitive_breeze': '#789abc',
            'theme_button_foreground_backdrop_insensitive_breeze': '#89abcd',
            'theme_button_decoration_focus_breeze': '#a1b2c3',
            'theme_button_decoration_focus_backdrop_breeze': '#b2c3d4',
        })
        with tempfile.TemporaryDirectory(dir=Path.home() / 'tempia', prefix='i167-button-role-') as folder:
            output = Path(folder)
            for header in ('#123456', '#68a0c8'):
                colors['theme_header_background_breeze'] = header
                result = paint_button(builder, recipe, colors, output)
                expected_pressed = builder.art.tone(header, 0.15, '#000000')
                expected_pressed_rgb = builder.art._rgb(expected_pressed)
                rc = Path(result['rc']).read_text(encoding='utf-8')
                self.assertIn('bg[NORMAL] = "' + header + '"', rc)
                self.assertIn('bg[ACTIVE] = "' + expected_pressed + '"', rc)
                self.assertIn('border = { 6, 6, 6, 6 }', rc)
                normal = Image.open(output / 'push-normal.png').convert('RGB')
                pressed = Image.open(output / 'push-pressed.png').convert('RGB')
                face_rgb = builder.art._rgb(header)
                dark_rgb = builder.art._rgb(builder.art.tone(header, .502, '#000000'))
                light_rgb = builder.art._rgb(builder.art.tone(header, .55, '#ffffff'))
                self.assertEqual(normal.size, (13, 13))
                self.assertEqual(normal.getpixel((6, 6)), face_rgb)
                self.assertEqual(pressed.getpixel((6, 6)), expected_pressed_rgb)
                self.assertEqual(normal.getpixel((6, 0)), dark_rgb)
                self.assertEqual(pressed.getpixel((6, 0)), face_rgb)
                self.assertEqual(normal.getpixel((0, 6)), dark_rgb)
                self.assertEqual(pressed.getpixel((0, 6)), dark_rgb)
                self.assertEqual(normal.getpixel((6, 12)), light_rgb)
                self.assertEqual(pressed.getpixel((6, 12)), light_rgb)
                changed = [(x,y) for y in range(13) for x in range(13)
                           if normal.getpixel((x,y)) != pressed.getpixel((x,y))]
                self.assertEqual(set(changed), {(x, 0) for x in range(13)} | {(6, 6)})
                self.assertEqual(result['press_policy'],
                    'R216 SR10.4 mask: 6px nine-slice bevel, 64x24 center face shaded 15% dynamically from KDE HeaderBackground while the measured 76px top edge flattens; side and bottom relief stay unchanged')
            colors['theme_header_background_breeze'] = '#123456'
            result = paint_button(builder, recipe, colors, output)
            rc = Path(result['rc']).read_text(encoding='utf-8')
            self.assertIn('bg[NORMAL] = "#123456"', rc)
            self.assertIn('fg[NORMAL] = "#a1b2c3"', rc)
            self.assertIn('bg[INSENSITIVE] = "#56789a"', rc)
            self.assertIn('bg[NORMAL] = "#234567"', rc)
            self.assertIn('fg[NORMAL] = "#b2c3d4"', rc)
            self.assertIn('fg[INSENSITIVE] = "#89abcd"', rc)
            self.assertIn('widget "*themeLabPush.GtkLabel" style : highest "theme-lab-gtk2-push-label"', rc)
            self.assertIn('widget "*themeLabBackdropPush.GtkLabel" style : highest "theme-lab-gtk2-push-backdrop-label"', rc)
            self.assertIn('style "theme-lab-gtk2-push-label"', rc)
            self.assertIn('fg[NORMAL] = "#345678"', rc)
            self.assertIn('style "theme-lab-gtk2-push-backdrop-label"', rc)
            self.assertIn('fg[NORMAL] = "#456789"', rc)
            self.assertEqual(result['focus_policy'], 'Solid 2px outer GTK2 focus outline, 2px padding, dynamic KDE DecorationFocus; preview label retains its matching text role')
            normal = Image.open(output / 'push-normal.png').convert('RGB')
            disabled = Image.open(output / 'push-disabled.png').convert('RGB')
            self.assertEqual(normal.getpixel((2, 2)), (18, 52, 86))
            self.assertEqual(disabled.getpixel((2, 2)), (86, 120, 154))
            self.assertEqual(role_source('normal'), ('header', 'header-fg', 0))
            self.assertEqual(role_source('backdrop'), ('header', 'header-fg', 1))
            self.assertEqual(role_source('disabled'), ('button', 'button-fg', 2))
            self.assertEqual(focus_role(), ('focus', 0))
            self.assertEqual(focus_role(backdrop=True), ('focus', 1))

if __name__ == '__main__': unittest.main()
