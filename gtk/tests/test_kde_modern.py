#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify Modern resource integrity, reproducibility and GTK2 RC ownership."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'gtk/tools'),str(ROOT/'tools')]
import build_kde_modern as modern
from gtk2_modern_palette import FALLBACK, prepare_modern
from theme_transaction import Failure


class ModernThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent=ROOT/'.gtk-kde-modern-validation';parent.mkdir(exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(prefix='unit-',dir=parent)
        cls.base=Path(cls.temp.name)
        cls.before={str(p.relative_to(modern.SOURCE)):p.read_bytes()for p in modern.SOURCE.rglob('*')if p.is_file()}
        cls.output=cls.base/'Irixium-KDE';cls.receipt=modern.build(cls.output)
        cls.masks=json.loads((cls.output/'common/adaptive/MANIFEST.json').read_text())

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_original_35_files_and_licenses_are_preserved(self):
        self.assertEqual(len(self.before),35)
        self.assertEqual(self.before,{str(p.relative_to(modern.SOURCE)):p.read_bytes()for p in modern.SOURCE.rglob('*')if p.is_file()})
        self.assertEqual((self.output/'LICENSE').read_bytes(),self.before['LICENSE'])
        self.assertEqual((self.output/'README.upstream.md').read_bytes(),self.before['README.md'])

    def test_all_28_artworks_keep_native_pixels_and_transparency(self):
        self.assertEqual(len(self.masks['assets']),28)
        for name,item in self.masks['assets'].items():
            path=modern.SOURCE/'gtk-3.0/assets'/(name+'.png')
            source=modern.native_icon(path)if name.startswith(('checkbox_','option_'))else Image.open(path).convert('RGBA')
            decoded=[[None]*source.width for _ in range(source.height)]
            for layer in item['layers']:
                palette=dict(zip(('error','success','warning'),layer['colors']))
                payload=self.output/'common/adaptive'/layer['file']
                self.assertIn('CC-BY-NC-SA-4.0',payload.read_text())
                for rect in ET.parse(payload).getroot().findall('{http://www.w3.org/2000/svg}rect'):
                    color=palette[rect.attrib['class']].split(':')[0]
                    x,y,w,h=(int(rect.attrib[k])for k in('x','y','width','height'))
                    for yy in range(y,y+h):
                        for xx in range(x,x+w):
                            self.assertIsNone(decoded[yy][xx]);decoded[yy][xx]=tuple(bytes.fromhex(color[1:]))+(round(float(rect.attrib.get('fill-opacity','1'))*255),)
            for y in range(source.height):
                for x in range(source.width):
                    with self.subTest(asset=name,x=x,y=y):
                        value=source.getpixel((x,y))
                        self.assertEqual(decoded[y][x],value if value[3]else None)

    def test_metrics_and_source_css_bevel_offsets_are_retained(self):
        for selector,properties in modern.classic.rules(modern.SOURCE/'gtk-3.0/gtk.css'):
            for leaf in selector.split(','):
                leaf=leaf.strip().replace('*link','link')
                result=modern.transformed(leaf,properties,0,self.masks,'3')
                for prop,value in properties.items():
                    if prop not in modern.COLOR_PROPERTIES:
                        self.assertEqual(result[prop],value,(leaf,prop))
                for prop in('box-shadow','border','border-bottom','border-top','border-left','border-right'):
                    if prop in properties:
                        # Geometry/keywords survive; only symbolic color
                        # expressions differ and may contain extra numbers.
                        for dimension in __import__('re').findall(r'-?\d+px',properties[prop]):
                            self.assertIn(dimension,result[prop])

    def test_reload_alias_has_identical_css_and_masks_and_is_reproducible(self):
        alias=self.base/'Irixium-KDE-Reload';modern.build(alias,theme_name='Irixium-KDE-Reload')
        for relative in self.receipt['files']:
            if relative=='index.theme':continue
            self.assertEqual((self.output/relative).read_bytes(),(alias/relative).read_bytes())
        old={p.relative_to(self.output):p.read_bytes()for p in self.output.rglob('*')if p.is_file()}
        modern.build(self.output)
        self.assertEqual(old,{p.relative_to(self.output):p.read_bytes()for p in self.output.rglob('*')if p.is_file()})

    def test_gtk2_preparation_is_pure_content_addressed_and_has_no_engine_assets(self):
        colors=''.join('@define-color '+k+' '+v+';\n'for k,v in FALLBACK.items()).encode()
        destination=self.base/'not-created-runtime'
        first=prepare_modern(modern.SOURCE,colors,destination)
        second=prepare_modern(modern.SOURCE,colors,destination)
        self.assertEqual(first.files,second.files);self.assertFalse(destination.exists())
        self.assertEqual(first.manifest['asset_count'],0)
        self.assertEqual(set(first.files),{first.gtkrc,first.directory/'manifest.json'})
        rc=first.files[first.gtkrc].decode()
        self.assertNotIn('engine "',rc);self.assertNotIn('file =',rc)
        self.assertIn('base[NORMAL] = "#c1c1c1"',rc)
        self.assertIn('style "irixium-kde-button"',rc)
        self.assertIn('style "irixium-kde-tooltip"',rc)
        self.assertGreater(rc.index('widget "*GtkMenuBar*"'),rc.index('widget "*GtkMenuItem*"'))
        for version in('3','4'):
            self.assertEqual((self.output/('gtk-'+version+'.0')/'gtk-dark.css').read_text(),'@import url("gtk.css");\n')

    def test_missing_export_roles_and_foreign_rc_are_refused(self):
        with self.assertRaises(Failure):prepare_modern(modern.SOURCE,b'@define-color theme_bg_color_breeze #000000;\n',self.base/'missing')
        with self.assertRaises(Failure):modern.gtk2_rc('style "irixium-default" { engine "pixmap" {} }')
        with self.assertRaises(ValueError):modern.build(self.base/'invalid-name',theme_name='other')


if __name__=='__main__':unittest.main()
