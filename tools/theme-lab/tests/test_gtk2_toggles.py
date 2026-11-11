# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtk2_toggles import paint_toggle
from test_backend import backend, model, ROOT


class ToggleTests(unittest.TestCase):
    def test_indicatorless_toggle_is_flat_across_native_states(self):
        recipe = model()['recipes']['gtk2']
        before = copy.deepcopy(recipe)
        builder = backend.load_builder(ROOT)
        palette = {name: '#789abc' for role in ('window', 'window-fg')
                   for name in builder.art.ROLES[role]}
        with tempfile.TemporaryDirectory(dir=Path.home() / 'tempia', prefix='i167-toggle-pure-') as folder:
            receipt = paint_toggle(builder, recipe, palette, folder)
            rc = Path(receipt['rc']).read_text()
            self.assertIn('  xthickness = 4', rc)
            self.assertIn('  ythickness = 0', rc)
            for state in ('PRELIGHT', 'INSENSITIVE'):
                self.assertIn('function = BOX detail = "button" state = ' + state +
                              ' shadow = OUT', rc)
                self.assertIn('function = BOX detail = "button" state = ' + state +
                              ' shadow = IN', rc)
            self.assertEqual(len(receipt['assets']), 6)
            self.assertEqual(receipt['translated_control'], 'toggle')
            self.assertIn('inconsistent', receipt['unsupported'])
            for normal, selected in (('toggle-normal.png', 'toggle-normal-selected.png'),
                                     ('toggle-disabled.png', 'toggle-disabled-selected.png'),
                                     ('toggle-backdrop.png', 'toggle-backdrop-selected.png')):
                self.assertEqual((Path(folder) / normal).read_bytes(),
                                 (Path(folder) / selected).read_bytes())
        self.assertEqual(recipe, before)

    def test_missing_state_roles_do_not_create_output(self):
        recipe = model()['recipes']['gtk2']; builder = backend.load_builder(ROOT)
        with tempfile.TemporaryDirectory(dir=Path.home() / 'tempia', prefix='i167-toggle-pure-') as folder:
            target = Path(folder) / 'absent'
            with self.assertRaisesRegex(ValueError, 'effective role'):
                paint_toggle(builder, recipe, {}, target)
            self.assertFalse(target.exists())


if __name__ == '__main__': unittest.main()
