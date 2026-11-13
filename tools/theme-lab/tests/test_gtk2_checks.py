# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtk2_checks import check_geometry, paint_check
from test_backend import backend, model, ROOT


class CheckTests(unittest.TestCase):
    def test_invalid_glyph_or_impossible_bevel_rejected_before_output(self):
        recipe = model()['recipes']['gtk2']
        for value in (True, 0, 129, 4):
            bad = copy.deepcopy(recipe); bad['geometry']['check_indicator_px'] = value
            with self.assertRaisesRegex(ValueError, 'check_indicator_px'): check_geometry(bad)
        builder = backend.load_builder(ROOT)
        with tempfile.TemporaryDirectory(dir=Path.home()/'tempia',prefix='i167-check-pure-') as folder:
            output = Path(folder)/'absent'
            with self.assertRaisesRegex(ValueError,'effective role'):
                paint_check(builder,recipe,{},output)
            self.assertFalse(output.exists())

    def test_window_background_and_text_remain_separate_from_indicator(self):
        recipe = model()['recipes']['gtk2']; before = copy.deepcopy(recipe)
        builder = backend.load_builder(ROOT)
        palette = {name: '#789abc' for role in ('button','button-fg','window','window-fg')
                   for name in builder.art.ROLES[role]}
        with tempfile.TemporaryDirectory(dir=Path.home()/'tempia',prefix='i167-check-pure-') as folder:
            receipt = paint_check(builder,recipe,palette,folder)
            rc = Path(receipt['rc']).read_text()
            self.assertIn('indicator-size = 10',rc)
            self.assertIn('indicator-spacing = 3',rc)
            self.assertEqual(len(receipt['assets']),9)
            self.assertEqual(recipe['geometry']['arrow_px'], 11)
            self.assertEqual(check_geometry(recipe)[0], 10)
            self.assertEqual(check_geometry(recipe)[2], 3)
            for state in ('NORMAL','PRELIGHT','ACTIVE','INSENSITIVE'):
                for shadow in ('IN','OUT'):
                    self.assertIn('state = '+state+' shadow = '+shadow+' overlay_file',rc)
            self.assertIn('function = FLAT_BOX detail = "checkbutton"',rc)
            self.assertIn('themeLabCanvasWindow',rc)
        self.assertEqual(recipe,before)


if __name__ == '__main__': unittest.main()
