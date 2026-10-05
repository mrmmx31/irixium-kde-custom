# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 3 tests. These do not claim to run the native Kvantum plugin."""
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
import menu_art as M
import tab_art as TB
import entry_art as E

def canonical(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(c) for c in e]]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def effective(c,s):
    d=effective(c,c[s]['inherits']) if c.has_option(s,'inherits') else {}
    d.update({k:v for k,v in c[s].items() if k!='inherits'});return d
ENTRY_PREFIXES=('ic-input-','ic-inset-','ic-option-','ic-spin-','ic-optionmark-','ic-spinmark-')
CHANGED_SECTIONS={'Tab','TabFrame','TabBarFrame','Menu','MenuItem','MenuBar','MenuBarItem','LineEdit','ComboBox','IndicatorSpinBox','GenericFrame','CheckBox','RadioButton'}
# Later block 4 has its own full baseline in test_selection.py.
SELECTION_PREFIXES=('ic-checkmark-','menu-ic-checkmark-','item-ic-checkmark-','ic-radiomark-','menu-ic-radiomark-')

class Entries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/'tests/data/entries-baseline.json').read_text())
        cls.xml=ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot()
        cls.nodes={e.get('id'):e for e in cls.xml if e.get('id')}
        cls.atlas=B.build()
        cls.c=configparser.ConfigParser(interpolation=None);cls.c.optionxform=str
        cls.c.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
    def test_all_approved_svg_resources_and_coordinates_are_identical(self):
        expected=self.base['svg']
        for name,h in expected.items():self.assertEqual(digest(canonical(self.nodes[name])),h,name)
        self.assertEqual(len(expected),2132)
    def test_only_new_entry_prefixes_added(self):
        added=set(self.nodes)-set(self.base['svg'])
        self.assertTrue(added)
        self.assertTrue(all(x.startswith(ENTRY_PREFIXES+SELECTION_PREFIXES+M.PREFIXES+TB.PREFIXES) for x in added))
    def test_other_effective_sections_unchanged(self):
        for section,old in self.base['effective_sections'].items():
            if section in CHANGED_SECTIONS or section=='%General':continue
            self.assertEqual(effective(self.c,section),old,section)
    def test_only_three_deliberate_global_options_changed(self):
        old=self.base['effective_sections']['%General'];new=effective(self.c,'%General')
        changed={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
        self.assertEqual(changed,{'comment','active_tab_overlap','combo_as_lineedit','combo_focus_rect','square_combo_button','menu_separator_height','spread_menuitems'})
        self.assertFalse(self.c.getboolean('%General','combo_as_lineedit'))
    def test_palette_scrollbar_and_buttons_not_changed(self):
        for s in ('GeneralColors','Scrollbar','ScrollbarSlider','ScrollbarGroove','PanelButtonCommand','PanelButtonTool','ToolbarButton'):
            self.assertEqual(effective(self.c,s),self.base['effective_sections'][s],s)
    def test_input_has_three_pixel_inset(self):
        im,n=E.surface('input','normal');self.assertEqual(n,3)
        self.assertEqual([im[y][12] for y in range(4)],['#919191','#606060','#2f2f2f','#b6b6aa'])
        self.assertEqual([im[-1-y][12] for y in range(3)],['#ececec','#c1c1c1','#2f2f2f'])
    def test_focus_keeps_content_and_bounds(self):
        a,n=E.surface('input','normal');b,_=E.surface('input','focused')
        self.assertNotEqual(a,b)
        self.assertEqual([r[n:-n] for r in a[n:-n]],[r[n:-n] for r in b[n:-n]])
        self.assertEqual(len(a),len(b));self.assertEqual(len(a[0]),len(b[0]))
    def test_option_and_spin_have_no_hover_animation(self):
        for k in ('option','spin'):self.assertEqual(E.surface(k,'normal'),E.surface(k,'focused'))
    def test_option_press_changes_bevel_not_interior(self):
        a,_=E.surface('option','normal');b,_=E.surface('option','pressed')
        self.assertNotEqual(a,b);self.assertEqual(a[12][12],b[12][12]);self.assertEqual(b[-2][12],'#e1e1e1')
    def test_spin_press_changes_bevel(self):
        a,_=E.surface('spin','normal');b,_=E.surface('spin','pressed')
        self.assertNotEqual(a,b);self.assertEqual(b[-1][12],'#e1e1e1')
    def test_option_marker_is_horizontal_relief(self):
        im=E.option_marker('normal');points=[(x,y) for y,row in enumerate(im) for x,c in enumerate(row) if c]
        self.assertEqual((max(x for x,y in points)-min(x for x,y in points)+1,max(y for x,y in points)-min(y for x,y in points)+1),(10,4))
    def test_option_marker_press_changes_only_colors(self):
        a=E.option_marker('normal');b=E.option_marker('pressed')
        self.assertNotEqual(a,b);self.assertEqual([[c is None for c in r] for r in a],[[c is None for c in r] for r in b])
    def test_all_requested_slices_and_directions_exist(self):
        for kind in ('input','inset','option','spin'):
            for state in E.STATES:
                for part in ('',)+B.PARTS:
                    self.assertIn('ic-'+kind+'-'+state+('-'+part if part else ''),self.nodes)
        for state in E.STATES:
            for direction in ('up','down','left','right'):self.assertIn('ic-spinmark-'+direction+'-'+state,self.nodes)
            self.assertIn('ic-optionmark-down-'+state,self.nodes)
    def test_combo_and_editable_use_separate_resources(self):
        self.assertEqual(effective(self.c,'LineEdit')['frame.element'],'ic-input')
        self.assertEqual(effective(self.c,'ComboBox')['frame.element'],'ic-option')
        self.assertEqual(effective(self.c,'ComboBox')['indicator.element'],'ic-optionmark')
    def test_input_and_spin_metrics_not_reduced(self):
        for s in ('LineEdit','IndicatorSpinBox'):
            old=self.base['effective_sections'][s];new=effective(self.c,s)
            for k in ('frame.top','frame.bottom','frame.left','frame.right','min_height'):
                self.assertEqual(old[k],new[k],s+':'+k)
        self.assertEqual(self.c['%General']['spin_button_width'],'16')
    def test_toolbar_entry_inherits_same_field(self):
        self.assertEqual(effective(self.c,'ToolbarLineEdit'),effective(self.c,'LineEdit'))
    def test_generic_panel_does_not_paint_contents(self):
        im,n=E.surface('inset','normal')
        self.assertTrue(all(c is None for row in im[n:-n] for c in row[n:-n]))
        self.assertFalse(self.c.getboolean('GenericFrame','interior'))
    def test_invalid_arguments(self):
        for kind,state,w,h in [('other','normal',24,24),('input','other',24,24),('input','normal',4,4)]:
            with self.assertRaises(ValueError):E.surface(kind,state,w,h)
    def test_no_fake_readonly_svg_state_claim(self):
        self.assertFalse(any('readonly' in x for x in self.nodes))
        self.assertIn('somente leitura',(ROOT/'docs/CAMPOS.md').read_text())
    def test_roadmap_retains_all_seven_blocks(self):
        text=(ROOT/'PLANO-IRIXCLASSIC.md').read_text()
        for i in range(1,8):self.assertIn('| '+str(i)+'. ',text)
        self.assertIn('0.3.0-rc1',text)

class EntryRendering(unittest.TestCase):
    def test_every_new_element_matches_integer_source_map(self):
        try:
            import cairosvg
            from PIL import Image
        except ImportError:self.skipTest('CairoSVG/Pillow unavailable; not a Qt test.')
        atlas=B.build();ns='{http://www.w3.org/2000/svg}'
        nodes={e.get('id'):e for e in ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot() if e.get('id')}
        tested=0
        for name,img in atlas.items.items():
            if not name.startswith(ENTRY_PREFIXES):continue
            h,w=len(img),len(img[0]);root=ET.Element(ns+'svg',{'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}'})
            node=ET.fromstring(ET.tostring(nodes[name]));node.attrib.pop('transform',None);root.append(node)
            result=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(root)))).convert('RGBA')
            def rgba(c):return (0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,)
            expected=[rgba(c) for row in img for c in row]
            self.assertEqual(list(result.getdata()),expected,name);tested+=1
        self.assertEqual(tested,385)

if __name__=='__main__':unittest.main()
