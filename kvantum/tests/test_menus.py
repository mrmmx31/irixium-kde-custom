# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 5: complete previous-release preservation and menu-only changes.

These tests do not load Qt or the Kvantum plugin. CairoSVG verifies the shipped
SVG against the generator, not native layout or event delivery.
"""
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
import finish_art as FN
import range_art as RG
import menu_art as M
import tab_art as TB

def canonical(e):
    return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(c) for c in e]]
def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def effective(c,s):
    d=effective(c,c[s]['inherits']) if c.has_option(s,'inherits') else {}
    d.update({k:v for k,v in c[s].items() if k!='inherits'});return FN.prior_effective(s,d)

class Menus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/'tests/data/menus-baseline.json').read_text())
        cls.xml=ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot()
        cls.nodes={e.get('id'):e for e in cls.xml if e.get('id')}
        cls.atlas=B.build()
        cls.c=configparser.ConfigParser(interpolation=None);cls.c.optionxform=str
        cls.c.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
    def test_all_2569_prior_resources_and_coordinates_preserved(self):
        self.assertEqual(len(self.base['svg']),2569)
        for n,h in self.base['svg'].items():self.assertEqual(digest(canonical(self.nodes[n])),h,n)
    def test_only_724_menu_resources_added(self):
        added={n for n in set(self.nodes)-set(self.base['svg']) if not n.startswith(TB.PREFIXES+RG.PREFIXES+FN.PREFIXES)}
        self.assertEqual(len(added),724)
        self.assertTrue(all(n.startswith(M.PREFIXES) for n in added))
    def test_all_ids_unique_and_serialization_reproducible(self):
        self.assertEqual(len(self.nodes),len([e for e in self.xml if e.get('id')]))
        generated={e.get('id'):canonical(e) for e in self.atlas.root if e.get('id')}
        self.assertEqual(generated,{n:canonical(e) for n,e in self.nodes.items()})
    def test_no_non_menu_effective_property_changed(self):
        self.assertEqual(set(self.c.sections()),set(self.base['effective_sections'])-{'DEFAULT'})
        for s,old in self.base['effective_sections'].items():
            if s in ('Tab','TabFrame','TabBarFrame','DEFAULT','%General','Menu','MenuItem','MenuBar','MenuBarItem') + RG.CONFIG_SECTIONS:continue
            self.assertEqual(effective(self.c,s),old,s)
    def test_four_menu_sections_have_only_explicit_changes(self):
        changes={
            'Menu':{'frame.element':'ic-menupanel','interior.element':'ic-menupanel'},
            'MenuItem':{'frame.element':'ic-menurow','interior.element':'ic-menurow',
                        'indicator.element':'ic-menuindicator','text.italic':'true'},
            'MenuBar':{'frame.element':'ic-menustrip','interior.element':'ic-menustrip'},
            'MenuBarItem':{'frame.element':'ic-menutitle','interior.element':'ic-menutitle',
                           'indicator.element':'ic-menuindicator'}}
        for s,updates in changes.items():
            expected=self.base['effective_sections'][s].copy();expected.update(updates)
            self.assertEqual(effective(self.c,s),expected,s)
    def test_only_separator_and_explicit_placement_global_options_added(self):
        a=self.base['effective_sections']['%General'];b=effective(self.c,'%General')
        changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
        self.assertEqual(changed,{'comment','active_tab_overlap','menu_separator_height','spread_menuitems','spread_progressbar'})
        self.assertEqual(b['menu_separator_height'],'6');self.assertEqual(b['spread_menuitems'],'false')
        for k in ('scroll_width','check_size','submenu_delay','submenu_overlap','animate_states'):
            self.assertEqual(a[k],b[k])
    def test_menubar_vertical_profile_matches_independent_reference_sample(self):
        # User-provided Confidence Tests screenshot at x=350, y=412..435.
        measured=['#ececec']*2+['#c1c1c1']*20+['#919191','#606060']
        im=M.surface('menustrip',w=64,h=24)
        self.assertEqual([row[32] for row in im],measured)
    def test_panel_is_opaque_and_not_recolored_by_active_window(self):
        for kind in ('menupanel','menustrip'):
            reference=M.surface(kind)
            for s in M.STATES:
                im=M.surface(kind,s);self.assertEqual(im,reference)
                self.assertTrue(all(c is not None for row in im for c in row))
    def test_unarmed_and_disabled_rows_do_not_draw_panel(self):
        for kind in ('menurow','menutitle'):
            for s in ('normal','disabled'):
                self.assertTrue(all(c is None for row in M.surface(kind,s) for c in row))
    def test_selected_is_toggled_and_not_checkbox_state(self):
        for kind in ('menurow','menutitle'):
            self.assertEqual(M.surface(kind,'focused'),M.surface(kind,'toggled'))
            self.assertEqual(M.surface(kind,'toggled')[10][10],'#dfdfdf')
        self.assertEqual(self.c['CheckBox']['interior.element'],'ic-checkmark')
        self.assertEqual(self.c['RadioButton']['interior.element'],'ic-radiomark')
    def test_press_inverts_bevel_and_returns_to_normal(self):
        for kind in ('menurow','menutitle'):
            p=M.surface(kind,'pressed');h=M.surface(kind,'focused')
            self.assertEqual(p[0][10],'#606060');self.assertEqual(p[-1][10],'#ececec')
            self.assertEqual(h[0][10],'#ececec');self.assertEqual(h[-1][10],'#606060')
            self.assertEqual(p[10][10],'#b3b3b3')
            self.assertTrue(all(c is None for row in M.surface(kind,'normal') for c in row))
    def test_no_geometry_jump_with_state_changes(self):
        for kind in ('menupanel','menustrip','menurow','menutitle'):
            for s in M.STATES:
                im=M.surface(kind,s,111,25);self.assertEqual((len(im[0]),len(im)),(111,25))
    def test_menu_bevel_at_narrow_sizes_remains_within_bounds(self):
        for w in (5,9,24,101):
            for h in (5,9,24,33):
                for s in ('normal','toggled','pressed'):
                    im=M.surface('menurow',s,w,h)
                    self.assertEqual(len(im),h);self.assertTrue(all(len(r)==w for r in im))
    def test_separator_two_rows_and_transparent_clearance(self):
        im=M.separator();self.assertEqual((len(im),len(im[0])),(6,20))
        self.assertEqual(im[2],['#919191']*20);self.assertEqual(im[3],['#ececec']*20)
        for y in (0,1,4,5):self.assertEqual(im[y],[None]*20)
    def test_tearoff_tile_and_hover_states_exist(self):
        for s in ('normal','focused'):
            im=M.tearoff(s);self.assertEqual((len(im),len(im[0])),(8,20))
            self.assertEqual([i for i,c in enumerate(im[3]) if c==M.DARK],
                             [x for start in (0,5,10,15) for x in range(start,start+3)])
            self.assertIn('ic-menuindicator-tearoff-'+s,self.nodes)
    def test_submenu_arrows_have_directions_disabled_and_inactive_resources(self):
        for d in ('left','right','up','down'):
            for s in M.STATES:
                im=M.direction_indicator(d,s);self.assertEqual((len(im),len(im[0])),(12,12))
                n='ic-menuindicator-'+d+'-'+s
                self.assertIn(n,self.nodes);self.assertEqual(self.atlas.items[n],self.atlas.items[n+'-inactive'])
        self.assertNotEqual(M.direction_indicator('right'),M.direction_indicator('right','disabled'))
    def test_submenu_dark_masks_are_mirrored_for_rtl(self):
        mask=lambda m:{(x,y) for y,r in enumerate(m) for x,c in enumerate(r) if c==M.DARK}
        right=mask(M.direction_indicator('right'));left=mask(M.direction_indicator('left'))
        self.assertEqual(left,{(11-x,y) for x,y in right})
        self.assertEqual(len(right),25)
    def test_every_menu_frame_slice_exists(self):
        for kind in ('menupanel','menustrip','menurow','menutitle'):
            for st in M.STATES:
                for tail in ('','-inactive'):
                    for p in ('',)+B.PARTS:
                        self.assertIn('ic-'+kind+'-'+st+tail+('-'+p if p else ''),self.nodes)
    def test_invalid_artwork_inputs_rejected(self):
        for args in [('other','normal'),('menurow','bad'),('menurow','normal',4,20)]:
            with self.assertRaises(ValueError):M.surface(*args)
        with self.assertRaises(ValueError):M.direction_indicator('diagonal')
        with self.assertRaises(ValueError):M.direction_indicator('up',size=11)
        with self.assertRaises(ValueError):M.tearoff('pressed')
    def test_full_plan_preserved_with_tabs_next(self):
        t=(ROOT/'PLANO-IRIXCLASSIC.md').read_text()
        for i in range(1,8):self.assertIn('| '+str(i)+'. ',t)
        self.assertIn('bloco 6 — abas',t);self.assertIn('0.5.0-rc1',t)
    def test_native_gallery_is_real_kvantum_not_proxy(self):
        t=(ROOT/'tools/preview_menus.py').read_text()
        self.assertIn("QStyleFactory.create('kvantum')",t)
        self.assertNotIn('QProxyStyle',t)
        self.assertNotIn('setStyleSheet(',t)
        for s in ('QTest.mouseClick','QTest.keyClick','setNativeMenuBar(False)',
                  'setExclusive(True)','setTearOffEnabled(True)','QtQml'):
            self.assertIn(s,t)
    def test_graphic_and_runtime_limits_are_documented(self):
        t=(ROOT/'docs/MENUS.md').read_text()
        for s in ('toggled','Qt Quick','adapta','0.7','tear-off'):self.assertIn(s,t)
    def test_all_724_new_svg_elements_rasterized_with_cairo(self):
        try:import cairosvg;from PIL import Image
        except ImportError:self.skipTest('CairoSVG/Pillow absent; not a passed render test.')
        count=0;ns='{http://www.w3.org/2000/svg}'
        for n,im in self.atlas.items.items():
            if not n.startswith(M.PREFIXES):continue
            h,w=len(im),len(im[0]);root=ET.Element(ns+'svg',{'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}'})
            g=ET.fromstring(ET.tostring(self.nodes[n]));g.attrib.pop('transform',None);root.append(g)
            raster=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(root)))).convert('RGBA')
            expected=[(0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,) for row in im for c in row]
            self.assertEqual(list(raster.getdata()),expected,n);count+=1
        self.assertEqual(count,724)

if __name__=='__main__':unittest.main()
