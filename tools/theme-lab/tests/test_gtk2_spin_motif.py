#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 spin glyph geometry against the checked-in native Motif sample."""
import hashlib
import sys
from pathlib import Path
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/theme-lab/tests'))
from test_backend import backend, model
from gtk2_spins import paint_spin, spin_arrow_geometry


REFERENCE = ROOT / 'docs/review/theme-lab-motif-reference/01-MOTIF-REFERENCE.png'
REFERENCE_SHA256 = 'f413f7ab6eb2306998d8582b480dba01fa3bf7caf66715dd7136e5e435443527'
ARROW_BOXES = {'up': (929, 647), 'down': (929, 663)}
ROLE_COLORS = {
    (120, 160, 213): None,
    (196, 196, 196): 'face',
    (196, 213, 237): 'light',
    (62, 83, 110): 'dark',
}


class Gtk2SpinMotifTests(unittest.TestCase):
    def test_stepper_masks_match_motif_sample_and_have_no_square_bevel(self):
        self.assertEqual(hashlib.sha256(REFERENCE.read_bytes()).hexdigest(), REFERENCE_SHA256)
        builder = backend.load_builder(ROOT)
        recipe = model()['recipes']['gtk2']
        geometry = spin_arrow_geometry(recipe)
        self.assertEqual(geometry['arrow_px'], 13)
        reference = Image.open(REFERENCE).convert('RGB')
        for direction, (x, y) in ARROW_BOXES.items():
            actual = builder.gtk3_arrow('normal', direction, geometry=geometry)
            crop = reference.crop((x, y, x + 13, y + 13))
            observed = [[ROLE_COLORS[crop.getpixel((px, py))] for px in range(13)]
                        for py in range(13)]
            self.assertEqual(actual, observed, direction)

        # The scroll-bar recipe remains 11px; the spin owns its 13px Motif
        # glyph metric and the stepper panel is a flat View surface.
        self.assertEqual(recipe['geometry']['arrow_px'], 11)
        palette, _ = backend.native_roles(
            ROOT, ROOT / 'colors/DomainOS-SR10.4.colors', builder.art,
            backend.sha((ROOT / 'colors/DomainOS-SR10.4.colors').read_bytes()))
        temp_root = Path.home() / 'tempia'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='i167-spin-motif-', dir=temp_root) as tmp:
            generated = paint_spin(builder, recipe, palette, Path(tmp))
            folder = Path(tmp)
            rc = Path(generated['rc']).read_text(encoding='utf-8')
            self.assertIn('detail = "spinbutton_up" state = NORMAL', rc)
            self.assertIn('detail = "spinbutton_down" state = NORMAL', rc)
            spin_boxes = [line for line in rc.splitlines() if 'detail = "spinbutton_' in line]
            self.assertEqual(len(spin_boxes), 30)
            self.assertTrue(all('border = { 0, 0, 0, 0 }' in line for line in spin_boxes))
            panel = next(folder.glob('spin-panel-normal-*.png'))
            panel_image = Image.open(panel).convert('RGB')
            expected = builder.art._rgb(palette[builder.art.ROLES['view'][0]])
            self.assertEqual(panel_image.size, (1, 1))
            self.assertEqual(panel_image.getpixel((0, 0)), expected)


if __name__ == '__main__':
    unittest.main()
