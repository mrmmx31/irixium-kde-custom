# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Static integration and regression checks; not a Qt/KWin runtime substitute."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
UI=ROOT/'package/contents/ui'

class PreviewContractTests(unittest.TestCase):
    def test_approved_artwork_and_gestures_unchanged(self):
        expected=json.loads((ROOT/'tests/preview-preserved.json').read_text())
        for filename,digest in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256((UI/filename).read_bytes()).hexdigest(),digest)
    def test_adapter_initializes_borders_without_resize_repaint(self):
        code=(UI/'main.qml').read_text()
        self.assertIn('decoration.installTitleItem(face.titleItem)',code)
        self.assertIn('onGridScaleChanged: updateBorders()',code)
        self.assertNotIn('onWidthChanged:',code)
        self.assertNotIn('onHeightChanged:',code)
        self.assertIn('menuOnPress: true',code)
    def test_resize_uses_fixed_frame_textures(self):
        frame=(UI/'Frame.qml').read_text()
        self.assertIn('fillMode: Image.Tile',frame)
        self.assertNotIn('Canvas',frame)
        self.assertNotIn('Timer',frame)
        surface=(UI/'Surface.qml').read_text()
        self.assertNotIn('Artwork.paintDecoration(',surface)
        self.assertNotIn('surface.repaint()',surface)
    def test_adapter_passes_actual_parent_and_identity(self):
        code=(UI/'main.qml').read_text()
        self.assertIn('previewHost: root.parent',code)
        self.assertIn('expectedDecoration: decoration',code)
        self.assertIn('metrics: face.metrics',code)
        self.assertIn('shaded: decoration.client.shaded',code)
        self.assertLess(code.index('    PreviewBackground {'),code.index('    Surface {'))
    def test_fill_uses_palette_and_no_input(self):
        code=(UI/'PreviewBackground.qml').read_text()
        self.assertIn('previewHost.windowColor',code)
        self.assertIn('active: PreviewSupport.needsFill(',code)
        self.assertIn('enabled: false',code)
        self.assertNotIn('MouseArea',code)
        self.assertNotIn('Timer {',code)
    def test_real_decoration_retains_alpha(self):
        code=(UI/'main.qml').read_text()
        self.assertIn('alpha: true',code)
        self.assertNotIn('alpha: false',code)
    def test_manifest_covers_new_components_and_revision(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text())
        self.assertEqual(m['version'],'1.0.0-rc3')
        for rel in ['contents/ui/PreviewBackground.qml','contents/ui/PreviewSupport.js','contents/ui/main.qml']:
            self.assertEqual(m['package'][rel],hashlib.sha256((ROOT/'package'/rel).read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
