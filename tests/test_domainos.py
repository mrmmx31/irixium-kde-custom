# SPDX-License-Identifier: GPL-3.0-or-later
"""Protect independent artwork, attribution and the confirmed release label."""
import configparser
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
APPLET = ROOT / 'plasma/applets/org.irixclassic.domainos.panel'
STYLE = ROOT / 'plasma/IrixClassicDomainOS'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DomainOSProvenanceTest(unittest.TestCase):
    def test_classic_source_inventory_is_preserved(self):
        baseline = json.loads((STYLE / 'CLASSIC-BASELINE.json').read_text())
        classic = ROOT / 'plasma/IrixClassic'
        current = {str(p.relative_to(classic)): digest(p)
                   for p in classic.rglob('*') if p.is_file()}
        self.assertEqual(current, baseline)

    def test_original_drawings_and_palette_match_provenance(self):
        images = APPLET / 'contents/images'
        origin = json.loads((images / 'ORIGEM.json').read_text())
        for name, expected in origin['project_files'].items():
            with self.subTest(name=name):
                self.assertEqual(digest(images / name), expected)
        self.assertTrue(all(not r['distributed'] for r in origin['references']))
        self.assertFalse(any((images / r['name']).exists()
                             for r in origin['references']))
        fonts = APPLET / 'contents/fonts'
        font_origin = json.loads((fonts / 'ORIGEM.json').read_text())
        self.assertEqual(digest(fonts / font_origin['file']), font_origin['sha256'])
        self.assertEqual(digest(fonts / font_origin['license_file']),
                         font_origin['license_sha256'])

    def test_sgi_iconbox_bitmaps_are_existing_repository_assets(self):
        origin = json.loads((APPLET / 'ICONBOX-ORIGEM.json').read_text())
        for name, record in origin['copies_unchanged'].items():
            with self.subTest(name=name):
                image = APPLET / 'contents/images/iconbox' / name
                source = ROOT / record['source']
                self.assertEqual(digest(image), record['sha256'])
                self.assertEqual(image.read_bytes(), source.read_bytes())

    def test_institutional_seal_uses_body_blue_and_stacked_label(self):
        images = APPLET / 'contents/images'
        palette = json.loads((images / 'palette.json').read_text())
        root = ET.parse(images / 'gnu-linux.svg').getroot()
        fills = {node.get('fill') for node in root.iter() if node.get('fill')}
        self.assertTrue(fills)
        self.assertLessEqual(fills, set(palette['colors'].values()))
        self.assertEqual(fills, set(palette['institutional_emblem']['colors'].values()))
        labels = [node.get('data-label') for node in root.iter()
                  if node.get('data-label')]
        self.assertEqual(labels, ['GNU/', 'LINUX'])
        self.assertEqual(palette['institutional_emblem']['lettering']['lines'], labels)
        self.assertEqual(palette['institutional_emblem']['colors']['lettering'],
                         palette['colors']['metal_dark'])
        self.assertFalse(any(node.get('width')=='101' and node.get('height')=='22'
                             for node in root.iter()))
        self.assertFalse(root.findall('.//{http://www.w3.org/2000/svg}text'))

    def test_confirmed_sr104_color_scheme_and_origin_match(self):
        scheme = ROOT / 'colors/DomainOS-SR10.4.colors'
        origin = json.loads(scheme.with_suffix('.ORIGEM.json').read_text())
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(scheme)
        self.assertEqual(cfg['General']['Name'], 'DomainOS SR10.4')
        self.assertEqual(origin['name'], 'DomainOS SR10.4')
        self.assertEqual(digest(scheme), origin['file_sha256'])
        self.assertFalse(origin['fonts_changed'])
        self.assertFalse((ROOT / 'colors/DomainOS-SR14.1.colors').exists())
        self.assertFalse((ROOT / 'colors/DomainOS-SR14.4.colors').exists())


if __name__ == '__main__':
    unittest.main()
