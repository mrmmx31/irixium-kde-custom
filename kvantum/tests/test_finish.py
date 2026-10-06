# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Finishing baseline and reporting tests. Does not claim native Qt execution."""
from pathlib import Path
import configparser
import hashlib
import inspect
import io
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_classic as B
import finish_art as F
import gallery_report as J


def canonical(e):return [e.tag, sorted(e.attrib.items()), (e.text or '').strip(), [canonical(c) for c in e]]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def effective(c,s):
    v=effective(c,c[s]['inherits']) if c.has_option(s,'inherits') else {}
    v.update({k:x for k,x in c[s].items() if k!='inherits'});return v


class Finishing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/'tests/data/finish-baseline.json').read_text())
        cls.c=configparser.ConfigParser(interpolation=None);cls.c.optionxform=str
        cls.c.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
        cls.atlas=B.build()
        cls.nodes={e.get('id'):e for e in ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot() if e.get('id')}
    def test_5147_previous_resources_and_positions_are_identical(self):
        self.assertEqual(len(self.base['svg']),5147)
        for n,h in self.base['svg'].items():self.assertEqual(digest(canonical(self.nodes[n])),h,n)
    def test_only_44_new_resources(self):
        names=set(self.nodes)-set(self.base['svg']);self.assertEqual(len(names),44)
        self.assertTrue(all(n.startswith(F.PREFIXES) for n in names))
    def test_only_two_actual_routes_and_version_comment_change(self):
        self.assertEqual(set(self.c.sections()),set(self.base['effective_sections']))
        for s,old in self.base['effective_sections'].items():
            expected=dict(old);expected.update(F.CONFIG_PATCH.get(s,{}))
            if s=='%General': expected['comment']=expected['comment'].replace('test candidate 0.7.0-rc1','stable release 0.7.1')
            self.assertEqual(effective(self.c,s),expected,s)
    def test_preserved_generators_and_system_repair(self):
        for p,h in self.base['protected_files'].items():
            self.assertEqual(hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest(),h,p)
    def test_current_whitelist_does_not_change_arbitrary_bad_values(self):
        self.assertEqual(F.prior_effective('Toolbar',{'indicator.element':'bad'}),{'indicator.element':'bad'})
        self.assertEqual(F.prior_effective('Other',{'indicator.element':'ic-finish-toolbar'}),{'indicator.element':'ic-finish-toolbar'})
    def test_toolbar_handle_same_map(self):
        for s in ('','-inactive'):
            self.assertEqual(self.atlas.items['ic-finish-toolbar-handle'+s],self.atlas.items['ic-toolbar-handle'])
    def test_separator_canonical_is_vertical_two_columns(self):
        m=F.toolbar_separator();self.assertEqual((len(m),len(m[0])),(12,10))
        for y,row in enumerate(m):
            self.assertEqual([x for x,c in enumerate(row) if c is not None],[4,5] if 1<=y<=10 else [])
        self.assertEqual(m[5][4:6],['#919191','#ececec'])
    def test_rotated_separator_is_horizontal_two_rows(self):
        m=F.toolbar_separator(); rotated=[list(r) for r in zip(*m)]
        self.assertEqual(sum(any(c is not None for c in r) for r in rotated),2)
    def test_arrow_separator_not_reused(self):
        self.assertNotEqual(self.atlas.items['ic-finish-toolbar-separator'],self.atlas.items['ic-arrow-separator'])
        self.assertEqual((len(self.atlas.items['ic-arrow-separator']),len(self.atlas.items['ic-arrow-separator'][0])),(2,10))
    def test_spin_shape_grows_not_allocation(self):
        for st in F.STATES:
            m=F.spin_marker(st,'up');self.assertEqual((len(m),len(m[0])),(12,12))
            color='#858585' if st=='disabled' else '#4c4c4c'
            pts=[(x,y) for y,r in enumerate(m) for x,c in enumerate(r) if c==color]
            self.assertEqual((max(x for x,y in pts)-min(x for x,y in pts)+1,max(y for x,y in pts)-min(y for x,y in pts)+1),(7,6))
            self.assertEqual(len(pts),24)
    def test_press_does_not_move_spin_dark_mask(self):
        for direction in ('up','down','left','right'):
            normal=F.spin_marker('normal',direction);down=F.spin_marker('pressed',direction)
            mask=lambda im:{(x,y) for y,r in enumerate(im) for x,c in enumerate(r) if c=='#4c4c4c'}
            self.assertEqual(mask(normal),mask(down));self.assertNotEqual(normal,down)
    def test_hover_no_shift_and_disabled_distinct(self):
        self.assertEqual(F.spin_marker('normal','up'),F.spin_marker('focused','up'))
        self.assertNotEqual(F.spin_marker('normal','up'),F.spin_marker('disabled','up'))
    def test_spin_four_directions_and_inactive(self):
        for state in F.STATES:
            for d in ('up','down','left','right'):
                n='ic-finish-spinmark-'+d+'-'+state
                self.assertEqual(self.atlas.items[n],self.atlas.items[n+'-inactive'])
    def test_invalid_marker_rejected(self):
        for args in (('bad','up'),('normal','diagonal'),('normal','up',13)):
            with self.assertRaises(ValueError):F.spin_marker(*args)
    def test_modern_selection_uses_actual_geometry_and_not_classic_palette(self):
        s=(ROOT/'tools/preview_selection.py').read_text()
        self.assertIn("if a.tema=='IrixClassic':",s)
        self.assertIn('subElementRect(se,option,widget)',s)
        self.assertIn("selected rendering differs from unselected",s)
        self.assertNotIn('QImage(15,15',s)
    def test_menus_partial_failure_writes_report(self):
        s=(ROOT/'tools/preview_menus.py').read_text()
        for part in ('GalleryReport(', 'report.enter(', 'report.abort(exc)', 'report.finish(completed)', "--resultado"):
            self.assertIn(part,s)
        self.assertNotIn('setStyleSheet(',s)
    def test_menu_attempt_recorded_before_readiness(self):
        s=(ROOT/'tools/native_gallery_input.py').read_text().split('    def menu_action',1)[1]
        self.assertLess(s.index('self.records.append(row)'),s.index('self._ready(menu)'))
        self.assertNotIn('.trigger(',s);self.assertNotIn('.setActiveAction(',s)
    def test_finishing_joins_integrated_native_tasks_only_on_request(self):
        import review_integrated as R
        self.assertNotIn('native-finishing',{t[0] for t in R.tasks(False)})
        self.assertIn('native-finishing',{t[0] for t in R.tasks(True)})
    def test_missing_native_menu_window_is_recorded_before_error(self):
        from types import SimpleNamespace
        from native_gallery_input import GalleryInput
        app=SimpleNamespace(processEvents=lambda:None)
        menu=SimpleNamespace(isVisible=lambda:False)
        menu.window=lambda:SimpleNamespace(windowHandle=lambda:None)
        action=SimpleNamespace(text=lambda:'Demo',isEnabled=lambda:True)
        engine=GalleryInput(None,None,None,app)
        with self.assertRaises(ValueError):engine.menu_action(menu,action)
        self.assertEqual(len(engine.records),1)
        row=engine.records[0]
        self.assertEqual(row['stage'],'readiness');self.assertIn('error',row)
        self.assertFalse(row['valid_target']);self.assertFalse(row['visible_before'])
    def test_all_44_new_elements_rasterized(self):
        try:import cairosvg;from PIL import Image
        except ImportError:self.skipTest('CairoSVG/Pillow absent; not native acceptance.')
        count=0;ns='{http://www.w3.org/2000/svg}'
        for n,img in self.atlas.items.items():
            if not n.startswith(F.PREFIXES):continue
            h,w=len(img),len(img[0]);root=ET.Element(ns+'svg',width=str(w),height=str(h),viewBox=f'0 0 {w} {h}')
            g=ET.fromstring(ET.tostring(self.nodes[n]));g.attrib.pop('transform',None);root.append(g)
            raster=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(root)))).convert('RGBA')
            expected=[(0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,) for r in img for c in r]
            self.assertEqual(list(raster.getdata()),expected,n);count+=1
        self.assertEqual(count,44)


class IncrementalReports(unittest.TestCase):
    def test_interruption_keeps_partial_results_and_stage(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.json';r=J.GalleryReport({'theme':'Irixium'},p)
            r.enter('initial');r.check('popup visible',True);r.enter('submenu_mouse');r.abort(ValueError('hidden'))
            self.assertEqual(r.finish(False),1);doc=json.loads(p.read_text())
            self.assertEqual(doc['status'],'interrupted');self.assertEqual(len(doc['results']),1)
            self.assertEqual(doc['errors'][0]['stage'],'submenu_mouse');self.assertFalse(doc['completed'])
    def test_each_check_is_checkpointed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json';r=J.GalleryReport({},p);r.check('one',True)
            self.assertEqual(len(json.loads(p.read_text())['results']),1)
    def test_existing_report_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json';p.write_text('keep')
            with self.assertRaises(ValueError):J.GalleryReport({},p)
            self.assertEqual(p.read_text(),'keep')
    def test_empty_results_not_a_pass(self):
        r=J.GalleryReport({});self.assertEqual(r.finish(),1)
    def test_failed_test_not_hidden_by_completion(self):
        r=J.GalleryReport({});r.check('bad',False);self.assertEqual(r.finish(),1)
        self.assertEqual(r.doc['status'],'failed')
    def test_all_pass_requires_completion(self):
        r=J.GalleryReport({});r.check('good',True);self.assertEqual(r.finish(),0)
    def test_trace_preserved_after_error(self):
        r=J.GalleryReport({});r.doc['input_trace'].append({'events':['press']});r.abort(RuntimeError('x'));r.finish()
        self.assertEqual(r.doc['input_trace'][0]['events'],['press'])
    def test_output_not_group_writable(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json';r=J.GalleryReport({},p)
            self.assertEqual(p.stat().st_mode&0o777,0o600)

if __name__=='__main__':unittest.main()
