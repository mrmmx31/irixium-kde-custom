# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'visual_compare.py'
spec = importlib.util.spec_from_file_location('theme_lab_visual_compare', SOURCE)
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)


@unittest.skipUnless(shutil.which('convert') and shutil.which('identify') and
                     shutil.which('montage') and shutil.which('compare'),
                     'ImageMagick commands are required')
class VisualCompareTests(unittest.TestCase):
    def setUp(self):
        visual.ALLOWED_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix='theme-lab-visual-compare-', dir=visual.ALLOWED_ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def image(self, name, size, color):
        path = self.root / name
        subprocess.run(['convert', '-size', size, f'xc:{color}', str(path)], check=True)
        return path

    def output(self, name):
        path = self.root / name
        path.mkdir(mode=0o700)
        return path

    def test_identical_dimensions_compute_exact_absolute_error(self):
        left = self.image('left.png', '4x3', 'blue')
        right = self.image('right.png', '4x3', 'red')
        output = self.output('different')
        receipt = visual.compare(left, right, output)
        self.assertEqual(receipt['pixel_diff']['status'], 'computed')
        self.assertEqual(receipt['pixel_diff']['changed_pixels'], 12)
        self.assertEqual(receipt['pixel_diff']['total_pixels'], 12)
        self.assertEqual(receipt['pixel_diff']['changed_ratio'], 1.0)
        self.assertFalse(receipt['scale']['rescaled'])
        self.assertEqual(receipt['alignment'], {
            'status': 'unverified',
            'basis': 'canvas_dimensions_only',
            'manual_review_required': True,
        })
        self.assertEqual(json.loads((output / 'receipt.json').read_text()), receipt)
        for path in output.iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_identical_content_is_valid_and_reports_zero(self):
        left = self.image('same-a.png', '5x2', 'blue')
        right = self.root / 'same-b.png'
        shutil.copyfile(left, right)
        receipt = visual.compare(left, right, self.output('same'))
        self.assertEqual(receipt['inputs']['left']['sha256'], receipt['inputs']['right']['sha256'])
        self.assertEqual(receipt['pixel_diff']['changed_pixels'], 0)

    def test_different_dimensions_fail_closed_without_pixel_metric(self):
        left = self.image('small.png', '4x3', 'blue')
        right = self.image('wide.png', '5x3', 'blue')
        output = self.output('dimensions')
        receipt = visual.compare(left, right, output, gap_px=7)
        self.assertEqual(receipt['pixel_diff'], {
            'status': 'not_comparable', 'reason': 'dimensions_differ', 'rescaled': False})
        self.assertFalse((output / 'difference-absolute.png').exists())
        self.assertTrue((output / 'side-by-side-1x1.png').is_file())

    def test_rejects_links_non_png_reuse_and_output_outside_private_root(self):
        left = self.image('source.png', '2x2', 'blue')
        right = self.image('other.png', '2x2', 'red')
        link = self.root / 'linked.png'; link.symlink_to(left)
        with self.assertRaisesRegex(ValueError, 'não link'):
            visual.compare(link, right, self.output('link-output'))
        text = self.root / 'not-image.png'; text.write_text('not a PNG')
        with self.assertRaises(subprocess.CalledProcessError):
            visual.compare(text, right, self.output('text-output'))
        used = self.output('used'); (used / 'prior').write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'vazio'):
            visual.compare(left, right, used)
        with self.assertRaisesRegex(ValueError, 'domainos-theme-work'):
            visual.compare(left, right, Path('/tmp/theme-lab-forbidden-output'))


if __name__ == '__main__':
    unittest.main()
