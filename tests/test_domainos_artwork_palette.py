# SPDX-License-Identifier: GPL-3.0-or-later
"""Preserve approved SVG pixels while allowing KDE palette color changes."""
import importlib.util
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

from PyQt6.QtCore import QByteArray, QCoreApplication, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtQml import QJSEngine
from PyQt6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
APPLET = ROOT / 'plasma/applets/org.irixclassic.domainos.panel'
IMAGES = APPLET / 'contents/images'
ARTWORK = APPLET / 'contents/ui/Artwork.js'
SVG_DATA_PREFIX = 'data:image/svg+xml;charset=utf-8,'


def render(xml):
    renderer = QSvgRenderer(QByteArray(xml.encode('utf-8')))
    image = QImage(renderer.defaultSize(), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


class DomainOSArtworkPaletteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.engine = QJSEngine()
        source = ARTWORK.read_text(encoding='utf-8')
        self.assertTrue(source.startswith('.pragma library\n'))
        evaluated = self.engine.evaluate(source.split('\n', 1)[1])
        self.assertFalse(evaluated.isError(), evaluated.toString())

    def urls(self, color_map):
        function = self.engine.globalObject().property('urls')
        result = function.call([self.engine.toScriptValue(color_map)])
        self.assertFalse(result.isError(), result.toString())
        return result.toVariant()

    def xmls(self, color_map):
        urls = self.urls(color_map)
        self.assertTrue(all(url.startswith(SVG_DATA_PREFIX)
                            for url in urls.values()))
        return {name: unquote(url[len(SVG_DATA_PREFIX):])
                for name, url in urls.items()}

    def test_bundle_is_current_and_default_palette_preserves_original_xml(self):
        spec = importlib.util.spec_from_file_location(
            'domainos_palette_generator',
            ROOT / 'plasma/tools/gerar-domainos-paleta.py')
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        self.assertEqual(ARTWORK.read_text(encoding='utf-8'),
                         generator.generated_source())
        original = {path.name: path.read_text(encoding='utf-8')
                    for path in IMAGES.glob('*.svg')}
        self.assertEqual(self.xmls({}), original)
        colors = {color for xml in original.values()
                  for color in re.findall(r'#[0-9a-fA-F]{6}\b', xml)}
        # Case differences in the input map must not rewrite the approved XML.
        unchanged = {color.upper(): color.upper() for color in colors}
        self.assertEqual(self.xmls(unchanged), original)

    def test_color_collisions_are_replaced_once_case_insensitively(self):
        colors = {'#3E536E': '#c4d5ed', '#C4D5ED': '#123456'}
        original = (IMAGES / 'applications.svg').read_text(encoding='utf-8')
        actual = self.xmls(colors)['applications.svg']
        expected = re.sub(r'#[0-9a-fA-F]{6}\b',
                          lambda match: colors.get(match.group().upper(),
                                                   match.group()), original)
        self.assertEqual(actual, expected)
        self.assertIn('fill="#c4d5ed"', actual)
        self.assertIn('fill="#123456"', actual)

    def test_semantic_recolor_keeps_native_alpha_and_every_artwork_pixel(self):
        originals = {path.name: path.read_text(encoding='utf-8')
                     for path in IMAGES.glob('*.svg')}
        tokens = sorted({color.lower() for xml in originals.values()
                         for color in re.findall(r'#[0-9a-fA-F]{6}\b', xml)})
        # Every role gets a distinct opaque color to expose accidental merging.
        color_map = {color: '#%02x%02x%02x' % (30+index*11, 220-index*10,
                                             50+index*9)
                     for index, color in enumerate(tokens)}
        transformed = self.xmls(color_map)
        for name, original in originals.items():
            with self.subTest(asset=name):
                before, after = render(original), render(transformed[name])
                self.assertEqual(before.size(), after.size())
                for y in range(before.height()):
                    for x in range(before.width()):
                        old, new = before.pixelColor(x, y), after.pixelColor(x, y)
                        self.assertEqual(old.alpha(), new.alpha(), (name, x, y))
                        if old.alpha() == 255:
                            self.assertEqual(new.name(), color_map[old.name()],
                                             (name, x, y))


if __name__ == '__main__':
    unittest.main()
