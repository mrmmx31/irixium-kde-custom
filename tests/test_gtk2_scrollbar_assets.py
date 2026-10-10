#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native stepper recipe boundaries; original spin/art metrics stay untouched."""
from pathlib import Path
import hashlib
import io
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from gtk2_scrollbar_assets import adapt_scrollbars  # noqa: E402


class ScrollbarRecipeTests(unittest.TestCase):
    def setUp(self):
        self.theme = ROOT/'gtk/IrixClassic'
        self.original = (self.theme/'gtk-2.0/gtkrc').read_text()

    def prepare(self, text=None, reader=None):
        return adapt_scrollbars(self.original if text is None else text,
                                reader or (lambda name: (self.theme/'common/assets'/name).read_bytes()))

    def test_original_rc_is_recovered_by_removing_only_new_stepper_lines(self):
        result = self.prepare()
        recovered = '\n'.join(line for line in result.text.split('\n')
                              if 'function = STEPPER' not in line)
        self.assertEqual(recovered, self.original)
        self.assertEqual(result.assets, {})
        self.assertEqual(len(result.source_assets), 16)

    def test_specific_rules_cover_native_states_and_orientation(self):
        result = self.prepare()
        rules = re.findall(r'image \{ function = STEPPER  state = (\w+)  detail = "(\w+)"  '
                           r'arrow_direction = (\w+)  file = "../common/assets/([^"/]+)"  '
                           r'stretch = TRUE \}', result.text)
        self.assertEqual(len(rules), 20)
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            actual = {(detail, direction) for found, detail, direction, _ in rules if found == state}
            self.assertEqual(actual, {('hscrollbar', 'LEFT'), ('hscrollbar', 'RIGHT'),
                                      ('vscrollbar', 'UP'), ('vscrollbar', 'DOWN')})
        self.assertTrue(all(name in result.source_assets for _, _, _, name in rules))

    def test_closure_contains_only_original_eighteen_pixel_pngs(self):
        from PIL import Image
        observed = []
        def read(name):
            observed.append(name)
            self.assertRegex(name, r'^stepper-(up|down|left|right)-(normal|pressed|toggled|disabled)\.png$')
            return (self.theme/'common/assets'/name).read_bytes()
        result = self.prepare(reader=read)
        self.assertEqual(len(observed), 16)
        self.assertEqual(len(set(observed)), 16)
        for name, raw in result.source_assets.items():
            self.assertEqual(raw, (self.theme/'common/assets'/name).read_bytes())
            with Image.open(io.BytesIO(raw)) as image:
                self.assertEqual(image.size, (18, 18))
            self.assertEqual(result.manifest['source_assets'][name], hashlib.sha256(raw).hexdigest())

    def test_rejects_unknown_source_duplicate_and_broken_art(self):
        with self.assertRaises(ValueError):
            self.prepare(text=self.original.replace('irixclassic-default', 'foreign-default'))
        with self.assertRaises(ValueError):
            self.prepare(text=self.prepare().text)
        with self.assertRaises(ValueError):
            self.prepare(text=self.original.replace('state = NORMAL  arrow_direction = UP',
                                                    'state = NORMAL  arrow_direction = DOWN'))
        with self.assertRaises((ValueError, OSError)):
            self.prepare(reader=lambda name: b'not a PNG')


if __name__ == '__main__':
    unittest.main()
