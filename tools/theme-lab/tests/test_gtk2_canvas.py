# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtk2_canvas import canvas_rc


class ArtFixture:
    ROLES = {'window': tuple('bg' + str(i) for i in range(4)),
             'window-fg': tuple('fg' + str(i) for i in range(4))}
    @staticmethod
    def _rgb(value): return tuple(value)


class CanvasTests(unittest.TestCase):
    def test_effective_roles_and_disabled_variant_without_mutation(self):
        palette = {name: [index + 11, index + 21, index + 31]
                   for names in ArtFixture.ROLES.values() for index, name in enumerate(names)}
        before = copy.deepcopy(palette)
        output = canvas_rc(ArtFixture, palette)
        self.assertIn('bg[NORMAL] = "#0b151f"', output)
        self.assertIn('bg[INSENSITIVE] = "#0d1721"', output)
        changed = dict(palette, bg0=[72, 83, 94])
        self.assertIn('bg[NORMAL] = "#48535e"', canvas_rc(ArtFixture, changed))
        self.assertEqual(palette, before)
        self.assertIn('widget "*themeLabCanvasWindow"', output)
        self.assertNotIn('class "*"', output)

    def test_missing_role_has_no_color_fallback(self):
        with self.assertRaisesRegex(ValueError, 'missing effective role'):
            canvas_rc(ArtFixture, {})


if __name__ == '__main__': unittest.main()
