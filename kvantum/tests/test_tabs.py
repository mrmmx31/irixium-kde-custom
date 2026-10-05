# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 6: frozen earlier resources, native suffix contracts and SVG rendering.

CairoSVG validation is not native Qt/Kvantum layout or event acceptance.
"""
from pathlib import Path
import configparser, hashlib, io, json, sys, unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_classic as B
import range_art as RG
import tab_art as A

def canonical(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(c) for c in e]]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def effective(c,s):
    d=effective(c,c[s]['inherits']) if c.has_option(s,'inherits') else {}
    d.update({k:v for k,v in c[s].items() if k!='inherits'});return d

class Tabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/'tests/data/tabs-baseline.json').read_text())
        cls.atlas=B.build();cls.xml=ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot()
        cls.nodes={e.get('id'):e for e in cls.xml if e.get('id')}
        cls.c=configparser.ConfigParser(interpolation=None);cls.c.optionxform=str
        cls.c.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
    def test_all_3293_earlier_resources_and_coordinates_unchanged(self):
        self.assertEqual(len(self.base['svg']),3293)
        for n,h in self.base['svg'].items():self.assertEqual(digest(canonical(self.nodes[n])),h,n)
    def test_only_160_new_tab_resources_added(self):
        added={n for n in set(self.nodes)-set(self.base['svg']) if not n.startswith(RG.PREFIXES)}
        self.assertEqual(len(added),160)
        self.assertTrue(all(n.startswith(A.PREFIXES) for n in added))
    def test_approved_artwork_generators_and_optional_system_patch_unchanged(self):
        for name,h in self.base['protected_files'].items():
            self.assertEqual(hashlib.sha256((ROOT.parent/name).read_bytes()).hexdigest(),h,name)
    def test_other_effective_sections_are_unchanged(self):
        self.assertEqual(set(self.c.sections()),set(self.base['effective_sections']))
        for s,old in self.base['effective_sections'].items():
            if s in ('%General','Tab','TabFrame','TabBarFrame') + RG.CONFIG_SECTIONS:continue
            self.assertEqual(effective(self.c,s),old,s)
    def test_only_overlap_and_version_comment_changed_globally(self):
        old=self.base['effective_sections']['%General'];new=effective(self.c,'%General')
        self.assertEqual({k for k in set(old)|set(new) if old.get(k)!=new.get(k)}, {'comment','active_tab_overlap','spread_progressbar'})
        self.assertEqual(new['active_tab_overlap'],'4')
    def test_tab_specific_changes_are_explicit(self):
        updates={'Tab':{'frame.element':'ic-notebook','interior.element':'ic-notebook',
                        'indicator.element':'ic-tabmark','frame.left':'6','frame.right':'6',
                        'text.margin.left':'2','text.margin.right':'2'},
                 'TabFrame':{'frame.element':'ic-notebookpage','interior.element':'ic-notebookpage'},
                 'TabBarFrame':{'interior.element':'ic-notebookbase'}}
        for s,changes in updates.items():
            expected=dict(self.base['effective_sections'][s]);expected.update(changes)
            self.assertEqual(effective(self.c,s),expected,s)
    def test_total_label_insets_and_min_height_preserved(self):
        old=self.base['effective_sections']['Tab'];new=effective(self.c,'Tab')
        for side in ('left','right','top','bottom'):
            self.assertEqual(int(old['frame.'+side])+int(old['text.margin.'+side]),
                             int(new['frame.'+side])+int(new['text.margin.'+side]))
        self.assertEqual(new['min_height'],old['min_height']);self.assertEqual(new['indicator.size'],'12')
    def test_notebook_selected_bottom_joins_page(self):
        self.assertEqual(A.tab('toggled')[-1][14],A.FACE)
        self.assertNotEqual(A.tab('normal')[-1][14],A.FACE)
    def test_document_selected_tab_retains_baseline(self):
        self.assertNotEqual(A.tab('toggled')[-1][14],A.tab('toggled',floating=True)[-1][14])
    def test_three_native_body_states_are_distinct(self):
        self.assertEqual(len({json.dumps(A.tab(s)) for s in A.STATES}),3)
    def test_body_has_no_unreachable_pressed_or_disabled_state(self):
        for prefix in ('ic-notebook-','floating-ic-notebook-'):
            self.assertFalse(any(n.startswith(prefix) and any(s in n for s in ('pressed','disabled')) for n in self.nodes))
    def test_sloped_shoulders_fit_frame_slices(self):
        im=A.tab();left,top,right,bottom=A.TAB_METRICS
        self.assertTrue(all(c is not None for row in im for c in row[left:-right]))
        self.assertIsNone(im[0][0]);self.assertIsNotNone(im[-1][0])
    def test_asymmetric_slices_reconstruct_original_map(self):
        im=A.tab('toggled');w,h=len(im[0]),len(im);l,t,r,b=A.TAB_METRICS
        positions={'':(l,t),'top':(l,0),'bottom':(l,h-b),'left':(0,t),'right':(w-r,t),
                   'topleft':(0,0),'topright':(w-r,0),'bottomleft':(0,h-b),'bottomright':(w-r,h-b)}
        rebuilt=A.blank(w,h)
        for name,mat in A.slices(im,A.TAB_METRICS).items():
            x,y=positions[name]
            for j,row in enumerate(mat):rebuilt[y+j][x:x+len(row)]=row
        self.assertEqual(rebuilt,im)
    def test_all_eight_oriented_junctions_exist_with_correct_dimensions(self):
        js=A.junctions();self.assertEqual(len(js),8)
        for key,im in js.items():
            self.assertEqual((len(im[0]),len(im)),(6,3) if key.startswith(('top-','bottom-')) else (3,6))
            for state in ('normal','normal-inactive'):self.assertIn('ic-notebookpage-'+state+'-'+key,self.nodes)
    def test_active_tab_close_does_not_look_permanently_pressed(self):
        self.assertEqual(A.close('normal'),A.close('toggled'))
        self.assertNotEqual(A.close('toggled'),A.close('toggledPressed'))
    def test_close_uses_exact_camel_case_pseudo_states(self):
        for s in ('normal','focused','pressed','toggled','toggledFocused','toggledPressed','disabled'):
            for tail in ('','-inactive'):self.assertIn('ic-tabmark-close-'+s+tail,self.nodes)
    def test_close_ink_does_not_shift_under_pressure(self):
        def mask(im):return {(x,y) for y,row in enumerate(im) for x,c in enumerate(row) if c=='#000000'}
        self.assertEqual(mask(A.close('normal')),mask(A.close('pressed')))
        self.assertTrue(any(A.LIGHT in r for r in A.close('pressed')))
    def test_disabled_close_is_visible_but_lower_contrast(self):
        self.assertTrue(any('#858585' in row for row in A.close('disabled')))
        self.assertFalse(any('#000000' in row for row in A.close('disabled')))
    def test_inactive_window_maps_equal_active(self):
        for n,mat in self.atlas.items.items():
            if n.startswith(A.PREFIXES) and '-inactive' in n:
                self.assertEqual(mat,self.atlas.items[n.replace('-inactive','')],n)
    def test_invalid_input_is_rejected(self):
        for fn,args in ((A.tab,('pressed',)),(A.tab,('normal',8,8)),(A.page,(4,4)),(A.close,('invalid',)),(A.blank,(0,1))):
            with self.assertRaises(ValueError):fn(*args)
        with self.assertRaises(ValueError):A.slices(A.tab(),(14,2,14,2))
    def test_every_new_element_is_rasterized_against_its_map(self):
        try:import cairosvg;from PIL import Image
        except ImportError:self.skipTest('CairoSVG/Pillow absent, no render result.')
        count=0;ns='{http://www.w3.org/2000/svg}'
        for n,im in self.atlas.items.items():
            if not n.startswith(A.PREFIXES):continue
            h,w=len(im),len(im[0]);root=ET.Element(ns+'svg',{'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}'})
            g=ET.fromstring(ET.tostring(self.nodes[n]));g.attrib.pop('transform',None);root.append(g)
            raster=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(root)))).convert('RGBA')
            expected=[(0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,) for row in im for c in row]
            self.assertEqual(list(raster.getdata()),expected,n);count+=1
        self.assertEqual(count,160)
    def test_native_gallery_is_not_a_fake_style(self):
        t=(ROOT/'tools/preview_tabs.py').read_text()
        for token in ("QStyleFactory.create('kvantum')",'QTest.mouseClick','QTest.keyClick','setDocumentMode','setTabEnabled','QtQml','State_Sunken'):
            self.assertIn(token,t)
        for forbidden in ('QProxyStyle','setStyleSheet(',"os.environ['QT_QPA_PLATFORM']"):self.assertNotIn(forbidden,t)
    def test_qtquick_gallery_keeps_native_controls(self):
        t=(ROOT/'tests/qml/PreviewTabs.qml').read_text()
        self.assertIn('TabBar',t);self.assertIn('StackLayout',t)
        self.assertNotIn('Canvas',t);self.assertNotIn('MouseArea',t)
    def test_roadmap_and_fidelity_limits_documented(self):
        plan=(ROOT/'PLANO-IRIXCLASSIC.md').read_text()
        for i in range(1,8):self.assertIn('| '+str(i)+'. ',plan)
        self.assertIn('0.6.0-rc1',plan);self.assertIn('bloco 7',plan)
        t=(ROOT/'docs/ABAS.md').read_text()
        for word in ('adapta','ViewKit','Qt Quick','toggledPressed','State_Sunken','4 unidades'):self.assertIn(word,t)

if __name__=='__main__':unittest.main()
