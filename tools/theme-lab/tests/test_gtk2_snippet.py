# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import model, ROOT
import backend
from gtk2_rc_fragments import image_rules


class SnippetTests(unittest.TestCase):
    def test_checkbox_fragment_uses_check_overlay_without_static_palette(self):
        data=model();data['selected_family']='gtk2'
        before=copy.deepcopy(data)
        for state in ('normal','hover','pressed','disabled','backdrop'):
            result=backend.snippet(ROOT,data,control='check',recipe_state=state)
            self.assertEqual(result['status'],'ok')
            source=result['source']
            self.assertIn('function = CHECK detail = "checkbutton"',source)
            self.assertIn('shadow = IN',source);self.assertIn('shadow = OUT',source)
            self.assertIn('overlay_stretch = FALSE',source)
            self.assertNotIn('function = OPTION',source)
            self.assertNotRegex(source,r'#[0-9a-fA-F]{6}\b')
        self.assertEqual(data,before)

    def test_radio_fragment_uses_native_option_and_both_selection_states(self):
        data=model(); data['selected_family']='gtk2'
        before=copy.deepcopy(data)
        for state in ('normal','hover','pressed','disabled','backdrop'):
            with self.subTest(state=state):
                result=backend.snippet(ROOT,data,control='radio',recipe_state=state)
                self.assertEqual(result['status'],'ok')
                source=result['source']
                self.assertIn('function = OPTION detail = "radiobutton"',source)
                self.assertIn('shadow = IN',source)
                self.assertIn('shadow = OUT',source)
                self.assertIn('overlay_stretch = FALSE',source)
                self.assertNotIn('function = CHECK',source)
                self.assertNotRegex(source,r'#[0-9a-fA-F]{6}\b')
        self.assertEqual(data,before)

    def test_toggle_fragment_keeps_selection_independent_of_pointer_state(self):
        data = model(); data['selected_family'] = 'gtk2'
        before = copy.deepcopy(data)
        for state, variant, native in [('normal','normal','NORMAL'),
                                      ('hover','normal','PRELIGHT'),
                                      ('pressed','normal','ACTIVE'),
                                      ('disabled','disabled','INSENSITIVE'),
                                      ('backdrop','backdrop','NORMAL')]:
            with self.subTest(state=state):
                result = backend.snippet(ROOT, data, control='toggle', recipe_state=state)
                self.assertEqual(result['status'], 'ok')
                source = result['source']
                self.assertIn('shadow = IN', source)
                self.assertIn('shadow = OUT', source)
                self.assertIn('state = ' + native, source)
                self.assertIn('toggle-' + variant + '-selected.png', source)
                self.assertIn('toggle-' + variant + '.png', source)
                self.assertNotRegex(source, r'#[0-9a-fA-F]{6}\b')
        self.assertEqual(data, before)

    def test_push_fragment_uses_same_native_geometry_and_state_image(self):
        data = model(); data['selected_family'] = 'gtk2'
        for state, image in [('normal','normal'),('hover','normal'),('pressed','pressed'),
                             ('disabled','disabled'),('backdrop','backdrop')]:
            result = backend.snippet(ROOT, data, control='push', recipe_state=state)
            self.assertEqual(result['status'], 'ok')
            self.assertIn('push-' + image + '.png', result['source'])
            self.assertIn('inner-border = { 4, 4, 4, 4 }', result['source'])
            self.assertNotRegex(result['source'], r'#[0-9a-fA-F]{6}\b')

    def test_orientation_piece_state_and_native_geometry_are_scoped(self):
        data = model(); data['selected_family'] = 'gtk2'
        recipe = data['recipes']['gtk2']
        before = copy.deepcopy(data)
        count = 0
        for control in ('scroll_h', 'scroll_v'):
            for piece, name in ((0, 'STEPPER'), (2, 'BOX'), (3, 'SLIDER')):
                recipe['selected_scroll_part'] = piece
                for state in ('normal', 'pressed', 'disabled', 'backdrop'):
                    if piece == 2 and state == 'pressed': continue
                    result = backend.snippet(ROOT, data, control=control, recipe_state=state)
                    source = result['source']
                    self.assertEqual(result['source_kind'], 'translated_native_fragment')
                    self.assertFalse(result['recipe_applied'])
                    self.assertIn('function = ' + name, source)
                    self.assertNotRegex(source, r'#[0-9a-fA-F]{6}\b')
                    if piece == 0:
                        self.assertIn('LEFT' if control == 'scroll_h' else 'UP', source)
                        self.assertNotIn('UP' if control == 'scroll_h' else 'LEFT', source)
                    else:
                        self.assertIn('HORIZONTAL' if control == 'scroll_h' else 'VERTICAL', source)
                    count += 1
        self.assertEqual(count, 22)
        recipe.pop('selected_scroll_part')
        self.assertEqual(data, before)

    def test_unsupported_controls_and_states_remain_explicit(self):
        data = model(); data['selected_family'] = 'gtk2'
        self.assertEqual(backend.snippet(ROOT, data, family='gtk5', control='entry')['status'], 'not_implemented')
        for piece, state in ((1, 'normal'), (4, 'normal'), (2, 'pressed'), (0, 'hover')):
            data['recipes']['gtk2']['selected_scroll_part'] = piece
            with self.assertRaises(ValueError): backend.snippet(ROOT, data, control='scroll_h', recipe_state=state)

    def test_all_catalog_controls_emit_a_gtk2_fragment(self):
        data = model(); data['selected_family'] = 'gtk2'
        source = ROOT / 'colors/DomainOS-SR10.4.colors'
        for control in backend.CONTROLS:
            with self.subTest(control=control):
                result = backend.snippet(ROOT, data, family='gtk2', control=control,
                                         kdeglobals=source)
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(result['source_kind'], 'translated_native_fragment')
                self.assertTrue(result['source'].strip())
                self.assertNotRegex(result['source'], r'#[0-9a-fA-F]{6}\b')

    def test_pressed_trough_uses_native_normal_image(self):
        files = {('trough', 'normal'): ('trough-normal.png', 2),
                 ('trough', 'pressed'): ('trough-pressed.png', 2)}
        source = '\n'.join(image_rules(files, 'ACTIVE', 'pressed', ('VERTICAL',), ('trough',)))
        self.assertIn('trough-normal.png', source)
        self.assertNotIn('trough-pressed.png', source)


if __name__ == '__main__': unittest.main()
