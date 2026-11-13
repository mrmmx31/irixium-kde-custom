# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure mapper/encoding gates; native startup and GUI have separate receipts."""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO/'tools'))
import kvantum_classic_palette as classic
import kvantum_modern_palette as modern
from kvantum_palette_config import adapt_config

# Explicit unit fixture, not a claimed native KDE oracle. Public renderers
# receive the actual native Qt palette from the caller's separate getter.
QT = {g: {'Base':'#607f91', 'AlternateBase':'#678799', 'Shadow':'#20282d'}
      for g in ('Active','Inactive','Disabled')}
QT['Disabled'] = {'Base':'#5c798a', 'AlternateBase':'#628192', 'Shadow':'#1f262b'}


def export_fixture(kind):
    """Distinct role/state literals exercise semantic mapping, not a live app."""
    color = {'blue':'#7894a7', 'yellow':'#ffff00', 'dark':'#202326'}[kind]
    output = {name: color for names in classic.ROLE.values() for name in names}
    output.update({name: color for name in modern.REQUIRED})
    output.update(theme_header_background_breeze=color, theme_header_foreground_breeze='#efeeee',
        theme_titlebar_background_breeze=color, theme_titlebar_background_backdrop_breeze='#283c51')
    for role in ('theme_fg_color_breeze','theme_button_foreground_normal_breeze','theme_text_color_breeze','tooltip_text_breeze'):
        output[role]='#efeeee'
    output['theme_base_color_breeze']='#324960'
    output['theme_selected_bg_color_breeze']='#145ad0'
    output['theme_button_background_insensitive_breeze']='#56758b'
    output['tooltip_background_breeze']='#24333c'
    output['error_color_breeze']='#c83640'
    output['warning_color_breeze']='#e3aa12'
    return output


class PaletteConfigTests(unittest.TestCase):
    def test_native_special_fields_and_explicit_disabled_limits(self):
        for theme in ('IrixClassic','Irixium'):
            raw=(REPO/'kvantum'/theme/(theme+'.kvconfig')).read_bytes()
            output, report=adapt_config(raw,native_qt_palette=QT)
            for line in (b'base.color=#607f91', b'inactive.base.color=#607f91',
                         b'alt.base.color=#678799', b'inactive.alt.base.color=#678799', b'shadow.color=#20282d'):
                self.assertIn(line+b'\n',output)
            self.assertIn(b'no_inactiveness=false\n',output)
            self.assertEqual([item['role'] for item in report['backendLimitations']],['Base','AlternateBase','Shadow'])
            self.assertEqual(adapt_config(raw,native_qt_palette=QT),(output,report))

    def test_noncolor_bytes_and_line_endings(self):
        source=b'; literal\r\n[%General]\r\nno_inactiveness=true\r\n[GeneralColors]\r\nbase.color = #abcdef\r\n;keep\r\n[Panel]\r\nwidth=19\r\ntext.normal.color=black\r\n'
        output,report=adapt_config(source,native_qt_palette=QT)
        self.assertTrue(output.startswith(b'; literal\r\n[%General]\r\nno_inactiveness=false\r\n'))
        self.assertIn(b';keep\r\n',output)
        self.assertTrue(output.endswith(b'[Panel]\r\nwidth=19\r\ntext.normal.color=none\r\n'))
        self.assertNotIn(b'\n',output.replace(b'\r\n',b''))
        self.assertEqual(report['insertedFields'],['inactive.base.color','alt.base.color','inactive.alt.base.color','shadow.color'])

    def test_final_line_without_newline(self):
        output,_=adapt_config(b'[GeneralColors]\nbase.color=#010203',native_qt_palette=QT)
        self.assertIn(b'base.color=#607f91\ninactive.base.color=',output)

    def test_unclassified_or_duplicate_fields_rejected(self):
        for source in (b'[Panel]\nother.color=#010203\n', b'[GeneralColors]\nbase.color=#010203\nbase.color=#040506\n', b'[GeneralColors]\n[GeneralColors]\n'):
            with self.assertRaises(ValueError):adapt_config(source,native_qt_palette=QT)

    def test_unencodable_inactive_shadow_rejected(self):
        native=copy.deepcopy(QT);native['Inactive']['Shadow']='#123456'
        with self.assertRaisesRegex(ValueError,'Active/Inactive Shadow'):
            adapt_config(b'[GeneralColors]\n',native_qt_palette=native)

    def test_missing_malformed_native_role_rejected(self):
        for group,role in (('Active','Base'),('Inactive','AlternateBase'),('Disabled','Shadow')):
            native=copy.deepcopy(QT);del native[group][role]
            with self.assertRaisesRegex(ValueError,'native Qt color'):
                adapt_config(b'[GeneralColors]\n',native_qt_palette=native)
        native=copy.deepcopy(QT);native['Active']['Base']='url(secret)'
        with self.assertRaises(ValueError):adapt_config(b'[GeneralColors]\n',native_qt_palette=native)

    def test_distinct_inactive_base_kept(self):
        native=copy.deepcopy(QT);native['Inactive']['Base']='#010203'
        output,_=adapt_config(b'[%General]\nno_inactiveness=true\n[GeneralColors]\n',native_qt_palette=native)
        self.assertIn(b'inactive.base.color=#010203\n',output)
        self.assertIn(b'no_inactiveness=false\n',output)


class SvgPaletteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources={theme: ((REPO/'kvantum'/theme/(theme+'.svg')).read_bytes(),
                            (REPO/'kvantum'/theme/(theme+'.kvconfig')).read_bytes())
                     for theme in ('IrixClassic','Irixium')}
        cls.outputs={theme: {kind: (classic if theme=='IrixClassic' else modern).render(
            *cls.sources[theme],export_fixture(kind),native_qt_palette=QT)
            for kind in ('blue','yellow','dark')} for theme in cls.sources}

    def test_deterministic_distinct_outputs_without_source_writes(self):
        for theme,variants in self.outputs.items():
            self.assertEqual(len({hashlib.sha256(value[0]).hexdigest() for value in variants.values()}),3)
            renderer=classic if theme=='IrixClassic' else modern
            self.assertEqual(renderer.render(*self.sources[theme],export_fixture('blue'),native_qt_palette=QT),variants['blue'])
            self.assertEqual((REPO/'kvantum'/theme/(theme+'.svg')).read_bytes(),self.sources[theme][0])
            self.assertEqual((REPO/'kvantum'/theme/(theme+'.kvconfig')).read_bytes(),self.sources[theme][1])

    def test_classic_only_fill_literals_change(self):
        source=self.sources['IrixClassic'][0]
        output,config,report=self.outputs['IrixClassic']['blue']
        normalize=lambda value:re.sub(rb'fill="#[0-9a-fA-F]{6}"',b'fill="COLOR"',value)
        self.assertEqual(normalize(source),normalize(output))
        self.assertEqual(classic.geometry(source),classic.geometry(output))
        self.assertEqual((report['groups'],report['opaqueRects'],report['transparentBoundsPreserved']),(5191,19934,5191))
        self.assertEqual(report['scrollGlyphRects'],130)

    def test_classic_scroll_glyph_masks_keep_41_pixels_each(self):
        for direction in ('up','down','left','right'):
            for state in ('normal','pressed','disabled'):
                self.assertEqual(len(classic.scroll_mask('ic-scrollarrow-'+direction+'-'+state)),41)

    def test_modern_original_ids_references_geometry_and_aliases(self):
        original={node.get('id'):node for node in ET.fromstring(self.sources['Irixium'][0]).iter() if node.get('id')}
        output,config,report=self.outputs['Irixium']['blue']
        generated={node.get('id'):node for node in ET.fromstring(output).iter() if node.get('id')}
        self.assertEqual(report['originalIdsPreserved'],1697)
        self.assertEqual(report['originalReferencesPreserved'],84)
        for name,node in original.items():
            self.assertIn(name,generated)
            if name not in ('svg8','layer1'):self.assertEqual(modern._geometry(node),modern._geometry(generated[name]),name)
            self.assertEqual(node.get('{http://www.w3.org/1999/xlink}href'),generated[name].get('{http://www.w3.org/1999/xlink}href'),name)
        for alias in report['aliases']:
            for name,node in original.items():
                if name.startswith(alias['sourceFamily']+'-'):
                    target=name.replace(alias['sourceFamily']+'-',alias['family']+'-',1)
                    self.assertEqual(modern._geometry(node),modern._geometry(generated[target]),target)
        self.assertEqual(len(report['configContextChanges']),4)

    def test_missing_native_svg_role_rejected(self):
        for theme in self.sources:
            palette=export_fixture('blue');del palette['theme_bg_color_breeze']
            renderer=classic if theme=='IrixClassic' else modern
            with self.assertRaises(ValueError):renderer.render(*self.sources[theme],palette,native_qt_palette=QT)

    def test_unreviewed_source_revision_rejected(self):
        for theme in self.sources:
            renderer=classic if theme=='IrixClassic' else modern
            svg,config=self.sources[theme]
            with self.assertRaisesRegex(ValueError,'source revision'):
                renderer.render(svg+b'\n',config,export_fixture('blue'),native_qt_palette=QT)
            with self.assertRaisesRegex(ValueError,'source revision'):
                renderer.render(svg,config+b'\n',export_fixture('blue'),native_qt_palette=QT)

if __name__=='__main__':unittest.main()
