# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 4 contract, isolated artwork and full prior-resource preservation."""
from pathlib import Path
import configparser
import hashlib
import io
import json
import sys
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_classic as B
import range_art as RG
import menu_art as M
import tab_art as TB
import selection_art as A

def canonical(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(c) for c in e]]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def effective(c,s):
    r=effective(c,c[s]['inherits']) if c.has_option(s,'inherits') else {}
    r.update({k:v for k,v in c[s].items() if k!='inherits'});return r

class Selection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/'tests/data/selection-baseline.json').read_text())
        cls.atlas=B.build()
        cls.nodes={e.get('id'):e for e in ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot() if e.get('id')}
        cls.c=configparser.ConfigParser(interpolation=None);cls.c.optionxform=str
        cls.c.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
    def test_all_2517_prior_maps_and_coordinates_unchanged(self):
        self.assertEqual(len(self.base['svg']),2517)
        for n,h in self.base['svg'].items():self.assertEqual(digest(canonical(self.nodes[n])),h,n)
    def test_52_added_resources_are_isolated(self):
        added={n for n in set(self.nodes)-set(self.base['svg']) if not n.startswith(M.PREFIXES+TB.PREFIXES+RG.PREFIXES)}
        self.assertEqual(len(added),52)
        self.assertTrue(all(n.startswith(A.PREFIXES) for n in added))
    def test_only_interior_routes_and_version_comment_change(self):
        self.assertEqual(set(self.c.sections()),set(self.base['effective_sections']))
        for s,old in self.base['effective_sections'].items():
            if s in ('Tab','TabFrame','TabBarFrame','Menu','MenuItem','MenuBar','MenuBarItem') + RG.CONFIG_SECTIONS:continue  # Block 5 is checked by test_menus.py.
            new=effective(self.c,s);changed={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
            self.assertEqual(changed,{'interior.element'} if s in ('CheckBox','RadioButton') else {'comment','active_tab_overlap','menu_separator_height','spread_menuitems','spread_progressbar'} if s=='%General' else set(),s)
    def test_size_and_label_metrics_unchanged(self):
        self.assertEqual(self.c['%General']['check_size'],'15')
        for s in ('CheckBox','RadioButton'):
            old=self.base['effective_sections'][s];new=effective(self.c,s)
            for k in ('min_height','text.margin.top','text.margin.bottom','text.margin.left','text.margin.right'):
                self.assertEqual(new[k],old[k])
    def test_contexts_use_actual_engine_suffixes(self):
        for prefix in A.PREFIXES:
            values=('','checked-','tristate-') if 'checkmark' in prefix else ('','checked-')
            for v in values:
                for st in ('normal','focused'):
                    for tail in ('','-inactive'):self.assertIn(prefix+v+st+tail,self.nodes)
    def test_no_unreachable_pressed_or_disabled_assets_advertised(self):
        added={n for n in set(self.nodes)-set(self.base['svg']) if not n.startswith(M.PREFIXES+TB.PREFIXES+RG.PREFIXES)}
        self.assertTrue(all('pressed' not in n and 'disabled' not in n for n in added))
    def test_all_cells_15_square(self):
        for n,im in self.atlas.items.items():
            if n.startswith(A.PREFIXES):self.assertEqual((len(im),len(im[0])),(15,15),n)
    def test_checkbox_red_only_when_selected_or_mixed(self):
        for state in ('off','on','mixed'):
            im=A.indicator('check',state);colors={c for row in im for c in row}
            self.assertEqual(A.RED in colors,state!='off');self.assertNotIn(A.BLUE,colors)
    def test_radio_blue_only_when_selected(self):
        for state in ('off','on'):
            im=A.indicator('radio',state);colors={c for row in im for c in row}
            self.assertEqual(A.BLUE in colors,state=='on');self.assertNotIn(A.RED,colors)
    def test_checkbox_three_states_differ_without_color_only_signal(self):
        mats=[A.indicator('check',s) for s in ('off','on','mixed')]
        self.assertEqual(len({json.dumps(m) for m in mats}),3)
        masks=[{(x,y) for y,r in enumerate(im) for x,c in enumerate(r) if c==A.RED} for im in mats]
        self.assertTrue(masks[1] and masks[2]);self.assertNotEqual(masks[1],masks[2])
    def test_mixed_has_horizontal_bar_not_tick(self):
        im=A.indicator('check','mixed');p={(x,y) for y,r in enumerate(im) for x,c in enumerate(r) if c==A.RED}
        self.assertEqual(p,{(x,y) for y in (6,7) for x in range(4,11)})
    def test_blue_mark_points_right_not_round_dot(self):
        im=A.indicator('radio','on');p={(x,y) for y,r in enumerate(im) for x,c in enumerate(r) if c==A.BLUE}
        self.assertEqual(min(x for x,y in p),5);self.assertEqual(max(x for x,y in p),9)
        self.assertEqual({y for x,y in p if x==9},{7})
    def test_shapes_are_square_and_diamond(self):
        a=A.indicator('check');b=A.indicator('radio')
        self.assertIsNotNone(a[1][1]);self.assertIsNone(b[1][1]);self.assertIsNotNone(b[1][7])
    def test_locate_highlight_changes_face_not_selection(self):
        for kind,values,col in (('check',('off','on','mixed'),A.RED),('radio',('off','on'),A.BLUE)):
            for val in values:
                a=A.indicator(kind,val);b=A.indicator(kind,val,True)
                self.assertNotEqual(a,b)
                mask=lambda im:{(x,y) for y,r in enumerate(im) for x,c in enumerate(r) if c==col}
                self.assertEqual(mask(a),mask(b))
    def test_active_inactive_aliases_equal(self):
        for n,im in self.atlas.items.items():
            if n.startswith(A.PREFIXES) and n.endswith('-inactive'):self.assertEqual(im,self.atlas.items[n[:-9]])
    def test_menu_and_view_maps_have_same_visual_language(self):
        for st in ('normal','focused','checked-normal','checked-focused','tristate-normal','tristate-focused'):
            a=self.atlas.items['ic-checkmark-'+st]
            self.assertEqual(a,self.atlas.items['menu-ic-checkmark-'+st]);self.assertEqual(a,self.atlas.items['item-ic-checkmark-'+st])
    def test_invalid_values_rejected(self):
        for kind,val in (('radio','mixed'),('bad','on'),('check','invalid')):
            with self.assertRaises(ValueError):A.indicator(kind,val)
    def test_roadmap_retains_all_seven_blocks_and_unresolved_arrows(self):
        t=(ROOT/'PLANO-IRIXCLASSIC.md').read_text()
        for i in range(1,8):self.assertIn('| '+str(i)+'. ',t)
        self.assertIn('0.4.0-rc1',t);self.assertIn('diagnosticar-setas.sh',t)
    def test_native_disabled_and_pressed_limit_documented(self):
        t=(ROOT/'docs/SELECAO.md').read_text()
        for text in ('0.7','State_Sunken','tristate','15'):self.assertIn(text,t)
    def test_52_elements_rasterized_with_cairosvg(self):
        try:import cairosvg;from PIL import Image
        except ImportError:self.skipTest('CairoSVG/Pillow absent; not a passing render test')
        for name,m in self.atlas.items.items():
            if not name.startswith(A.PREFIXES):continue
            root=ET.Element('{http://www.w3.org/2000/svg}svg',{'width':'15','height':'15','viewBox':'0 0 15 15'})
            g=ET.fromstring(ET.tostring(self.nodes[name]));g.attrib.pop('transform',None);root.append(g)
            im=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(root)))).convert('RGBA')
            expected=[(0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,) for row in m for c in row]
            self.assertEqual(list(im.getdata()),expected,name)

if __name__=='__main__':unittest.main()
