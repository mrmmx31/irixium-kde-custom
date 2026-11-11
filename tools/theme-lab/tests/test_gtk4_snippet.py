# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import re
import json
import tempfile
from pathlib import Path
import unittest
import backend
from gtk4_generation import generate_snapshot
from test_backend import ROOT, model


class SnippetTests(unittest.TestCase):
    def setUp(self):
        self.data=model();self.data['selected_family']='gtk4'
        self.data['recipes']['gtk4']['visible_controls']=1
        self.kde=ROOT/'colors/DomainOS-SR10.4.colors'

    def snippet(self, state='normal'):
        return backend.snippet(ROOT,self.data,'gtk4','push',state,self.kde)

    def test_selected_state_has_symbolic_roles_and_matching_generated_assets(self):
        before=copy.deepcopy(self.data)
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-snippet-') as directory:
            receipt=generate_snapshot(ROOT,Path(directory)/'snapshot',self.data,'a'*64,self.kde)
            generated=Path(receipt['css']).read_text()
            for state,pseudo in (('normal',''),('pressed',':active'),('disabled',':disabled'),('backdrop',':backdrop')):
                fragment=self.snippet(state)
                self.assertEqual(fragment['language'],'css')
                self.assertEqual(fragment['source_kind'],'translated_native_fragment')
                source=fragment['source']
                self.assertIn('@import url("push.css");',source)
                self.assertIn(receipt['style_class']+pseudo+' {',source)
                self.assertNotRegex(source,r'#[0-9a-fA-F]{6}\b')
                names=re.findall(r'url\("([^"/]+\.png)"\)',source)
                self.assertEqual(len(names),8)
                for name in names:
                    self.assertTrue((Path(receipt['css']).parent/name).is_file())
                    self.assertIn(name,generated)
                self.assertIn('border-width: 2px',source)
                self.assertIn('font-size: 13px',source)
                self.assertFalse(fragment['recipe_applied'])
        self.assertEqual(before,self.data)

    def test_custom_roles_and_zero_shadow_are_honored(self):
        recipe=self.data['recipes']['gtk4']
        recipe['palette']['face_role']='Colors:Window/BackgroundNormal'
        recipe['geometry']['shadow_px']=0
        source=self.snippet('backdrop')['source']
        self.assertIn('@theme_unfocused_bg_color_breeze',source)
        self.assertIn('background-image: none;',source)
        self.assertNotRegex(source,r'url\("[^"\n]*\.png"\)')

    def test_other_controls_remain_explicitly_pending(self):
        result=backend.snippet(ROOT,self.data,'gtk4','check',None,self.kde)
        self.assertEqual(result['status'],'not_implemented')
        self.assertEqual(result['language'],'json')
        with self.assertRaises(backend.Unavailable):
            backend.snippet(ROOT,self.data,'gtk4','push','focus',self.kde)

    def test_scrollbar_contract_and_generated_snippet_preserve_missing_steppers(self):
        import copy
        from gtk4_scrollbar_contract import contract
        original=copy.deepcopy(self.data)
        for control in ('scroll_h','scroll_v'):
            capability=contract(control,self.data['recipes']['gtk4'])
            self.assertEqual(capability['native_widget'],'GtkScrollbar')
            self.assertFalse(capability['native_stepper_properties_available'])
            self.assertFalse(capability['geometry_applied'])
            self.assertFalse(capability['palette_roles_applied'])
            self.assertEqual(capability['status'],'capability_contract_only')
            result=backend.snippet(ROOT,self.data,'gtk4',control,None,self.kde)
            self.assertEqual(result['status'],'ok')
            self.assertEqual(result['source_kind'],'translated_native_fragment')
            self.assertIn('@import url("scrollbar.css");',result['source'])
            self.assertIn('GtkAdjustment',result['source'])
            self.assertNotIn('arrow',result['source'].lower())
        self.assertEqual(self.data,original)

    def test_toggle_fragment_matches_qualified_assets_and_native_checked_rules(self):
        self.data['recipes']['gtk4']['visible_controls']=2
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-toggle-snippet-') as d:
            receipt=generate_snapshot(ROOT,Path(d)/'snapshot',self.data,'a'*64,self.kde,allow_toggle=True)
            for state in ('normal','pressed','disabled','backdrop','hover'):
                result=backend.snippet(ROOT,self.data,'gtk4','toggle',state,self.kde)
                self.assertEqual(result['language'],'css')
                source=result['source'];self.assertIn('@import url("toggle.css");',source)
                self.assertNotRegex(source,r'#[0-9a-fA-F]{6}\b')
                self.assertIn(':checked',source);self.assertIn(':not(:checked)',source)
                names=re.findall(r'url\("([^"/]+\.png)"\)',source)
                self.assertEqual(len(names),16)
                for name in names:self.assertTrue((Path(receipt['css']).parent/name).is_file())
            with self.assertRaises(backend.Unavailable):
                backend.snippet(ROOT,self.data,'gtk4','toggle','focus',self.kde)


if __name__=='__main__':unittest.main()
