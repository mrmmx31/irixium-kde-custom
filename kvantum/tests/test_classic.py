# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import configparser
import hashlib
import importlib.util
import json
import sys
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_classic as B

class Classic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.atlas=B.build();cls.path=ROOT/'IrixClassic/IrixClassic.svg'
        cls.svg=ET.fromstring(cls.path.read_bytes());cls.ids={e.get('id'):e for e in cls.svg.iter() if e.get('id')}
        cls.conf=configparser.ConfigParser(interpolation=None);cls.conf.optionxform=str
        cls.conf.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
    def test_svg_regeneration_is_deterministic(self):
        expected=ET.tostring(self.atlas.root,encoding='utf-8',xml_declaration=True)
        self.assertEqual(self.path.read_bytes(),expected)
    def test_all_ids_unique(self):
        count=sum(e.get('id') is not None for e in self.svg.iter());self.assertEqual(count,len(self.ids))
    def test_no_embedded_fonts_external_urls_gradients_scripts_or_bitmaps(self):
        allowed={'svg','g','rect','title','desc'}
        self.assertTrue(all(e.tag.rsplit('}',1)[-1] in allowed for e in self.svg.iter()))
    def test_all_drawing_coordinates_and_sizes_integer(self):
        for e in self.svg.iter():
            if e.tag.endswith('}rect'):
                for k in ('x','y','width','height'):self.assertEqual(float(e.get(k)),int(e.get(k)))
                self.assertGreater(int(e.get('width')),0);self.assertGreater(int(e.get('height')),0)
    def test_svg_rectangles_reproduce_generator_maps(self):
        for name,img in self.atlas.items.items():
            actual=B.blank(len(img[0]),len(img),None)
            for node in self.ids[name]:
                if node.get('fill-opacity')=='0': continue
                B.rect(actual,int(node.get('x')),int(node.get('y')),int(node.get('width')),int(node.get('height')),node.get('fill'))
            self.assertEqual(actual,img,name)
    def test_manifest_all_entries(self):
        doc=json.loads((ROOT/'IrixClassic/MANIFEST.json').read_text())
        for name,expected in doc['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/'IrixClassic'/name).read_bytes()).hexdigest(),expected)
    def test_config_section_inheritance_exists_and_is_acyclic(self):
        for section in self.conf.sections():
            seen=set();current=section
            while self.conf.has_option(current,'inherits'):
                self.assertNotIn(current,seen);seen.add(current)
                current=self.conf[current]['inherits'];self.assertIn(current,self.conf)
    def test_all_explicit_frame_prefixes_have_all_slices(self):
        for section in self.conf.sections():
            if 'frame.element' in self.conf[section]:
                prefix=self.conf[section]['frame.element']
                for state in (('normal','focused','toggled') if prefix=='ic-notebook' else ('normal',) if prefix in ('ic-notebookpage','ic-notebookbase') else B.STATES):
                    for part in B.PARTS:self.assertIn(prefix+'-'+state+'-'+part,self.ids)
    def test_explicit_interiors_have_states_or_check_substates(self):
        for section in self.conf.sections():
            if 'interior.element' in self.conf[section]:
                prefix=self.conf[section]['interior.element']
                if prefix in ('ic-checkmark','ic-radiomark'):
                    subs=['','-checked'] + (['-tristate'] if prefix=='ic-checkmark' else [])
                    for sub in subs:
                        for state in ('normal','focused'):
                            self.assertIn(prefix+sub+'-'+state,self.ids)
                    continue
                subs=['-checked','-unchecked','-tristate'] if prefix in ('ic-check','ic-radio') else ['']
                for sub in subs:
                    for state in (('normal','focused','toggled') if prefix=='ic-notebook' else ('normal',) if prefix in ('ic-notebookpage','ic-notebookbase') else B.STATES):self.assertIn(prefix+sub+'-'+state,self.ids)
    def test_button_hover_equals_rest_but_press_differs(self):
        a,_=B.surface('button','normal');b,_=B.surface('button','focused');c,_=B.surface('button','pressed')
        self.assertEqual(a,b);self.assertNotEqual(a,c)
        self.assertEqual(a[10][10],c[10][10])
    def test_menu_navigation_is_not_erased(self):
        self.assertNotEqual(B.surface('menuitem','normal'),B.surface('menuitem','focused'))
    def test_checkbox_states_distinct(self):
        states=[B.check('check',x,'normal') for x in ('checked','unchecked','tristate')]
        self.assertTrue(states[0]!=states[1] and states[1]!=states[2] and states[0]!=states[2])
    def test_disabled_check_has_no_black_mark(self):
        self.assertFalse(any('#000000' in row for row in B.check('check','checked','disabled')))
    def test_scrollbar_controls_complete(self):
        for state in B.STATES:
            for direction in ('up','down','left','right'):
                self.assertIn('ic-scrollarrow-'+direction+'-'+state,self.ids)
    def test_accessible_focus_and_default_are_present(self):
        for p in B.PARTS:
            self.assertIn('ic-focus-normal-'+p,self.ids);self.assertIn('ic-button-default-'+p,self.ids)
    def test_compact_tab_overlap_without_frame_expansion(self):
        self.assertEqual(self.conf['%General']['active_tab_overlap'],'4')
        self.assertEqual(self.conf['Tab']['frame.expansion'],'0')
    def test_declared_engine_metrics_within_documented_limits(self):
        g=self.conf['%General']
        self.assertEqual(int(g['scroll_width']),18);self.assertEqual(int(g['check_size']),15)
        self.assertGreaterEqual(int(g['spin_button_width']),16)
        self.assertEqual(g['animate_states'],'false')

if __name__=='__main__':unittest.main()
