# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 7 regression contract. Rasterization is not native event acceptance."""
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
import range_art as R


def canonical(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(c) for c in e]]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def effective(c,s):
    d=effective(c,c[s]['inherits']) if c.has_option(s,'inherits') else {}
    d.update({k:v for k,v in c[s].items() if k!='inherits'});return d


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/'tests/data/controls-baseline.json').read_text())
        cls.atlas=B.build();cls.xml=ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot()
        cls.nodes={e.get('id'):e for e in cls.xml if e.get('id')}
        cls.c=configparser.ConfigParser(interpolation=None);cls.c.optionxform=str
        cls.c.read(ROOT/'IrixClassic/IrixClassic.kvconfig')

    def test_all_3453_prior_resources_are_byte_canonical_identical(self):
        self.assertEqual(len(self.base['svg']),3453)
        for name,sha in self.base['svg'].items():self.assertEqual(digest(canonical(self.nodes[name])),sha,name)
    def test_additions_have_only_reviewed_names(self):
        added=set(self.nodes)-set(self.base['svg']);self.assertEqual(len(added),1694)
        self.assertTrue(all(x.startswith(R.PREFIXES) for x in added))
    def test_svg_ids_are_unique(self):
        names=[x.get('id') for x in self.xml if x.get('id')]
        self.assertEqual(len(names),len(set(names)))
    def test_regeneration_is_deterministic(self):
        out=io.BytesIO();ET.ElementTree(self.atlas.root).write(out,encoding='utf-8',xml_declaration=True)
        self.assertEqual(out.getvalue(),(ROOT/'IrixClassic/IrixClassic.svg').read_bytes())
    def test_all_effective_configuration_changes_are_explicit(self):
        self.assertEqual(set(self.c.sections()),set(self.base['effective_sections']))
        for section,old in self.base['effective_sections'].items():
            expected=dict(old);expected.update(R.CONFIG_PATCH.get(section,{}))
            if section=='%General':expected['comment']=self.c[section]['comment']
            self.assertEqual(effective(self.c,section),expected,section)
    def test_global_change_is_only_progress_policy_and_version(self):
        old=self.base['effective_sections']['%General'];new=effective(self.c,'%General')
        self.assertEqual({k for k in set(old)|set(new) if old.get(k)!=new.get(k)},{'comment','spread_progressbar'})
        self.assertFalse(self.c.getboolean('%General','spread_progressbar'))
    def test_prior_generators_transactions_and_arrow_patch_untouched(self):
        for rel,sha in self.base['protected_files'].items():self.assertEqual(hashlib.sha256((ROOT.parent/rel).read_bytes()).hexdigest(),sha,rel)
    def test_scrollbar_and_button_configs_unchanged(self):
        for section in ('Scrollbar','ScrollbarGroove','ScrollbarSlider','PanelButtonCommand','PanelButtonTool','ToolbarButton'):
            self.assertEqual(effective(self.c,section),self.base['effective_sections'][section])
    def test_palette_and_font_controls_unchanged(self):
        self.assertEqual(effective(self.c,'GeneralColors'),self.base['effective_sections']['GeneralColors'])
        for section,old in self.base['effective_sections'].items():
            new=effective(self.c,section)
            for key,value in old.items():
                if key.startswith('text.') or 'font' in key:self.assertEqual(new[key],value,(section,key))
    def test_all_frame_shapes_are_valid_nine_slices(self):
        for kind in ('range-track','range-thumb','meter-track','meter-fill','column','hint','section','dock'):
            for state in R.STATES:
                im,n=R.surface(kind,state);self.assertEqual((len(im),len(im[0])),(24,24));self.assertGreater(24,2*n)
    def test_slider_pressure_changes_only_visual_state_not_size(self):
        n=R.surface('range-thumb','normal')[0];p=R.surface('range-thumb','pressed')[0]
        self.assertNotEqual(n,p);self.assertEqual((len(n),len(n[0])),(len(p),len(p[0])))
        self.assertEqual(n[0][12],p[-1][12]);self.assertEqual(n[-1][12],p[0][12])
    def test_slider_metrics_preserved(self):
        for k in ('slider_width','slider_handle_width','slider_handle_length'):
            self.assertEqual(self.c['%General'][k],self.base['effective_sections']['%General'][k])
    def test_slider_ticks_are_explicit_engine_names(self):
        for end in ('','-inactive'):self.assertEqual(self.atlas.items['ic-range-track-tick-normal'+end],[[R.EDGE]*5])
    def test_progress_interior_has_opaque_distinct_fill(self):
        full=R.surface('meter-fill','normal')[0];empty=R.surface('meter-track','normal')[0]
        self.assertEqual(full[12][12],R.FILL);self.assertNotEqual(full[12][12],empty[12][12])
        self.assertTrue(all(c is not None for row in full for c in row))
    def test_progress_unavailable_fill_is_distinct(self):
        self.assertNotEqual(R.surface('meter-fill','normal')[0][12][12],R.surface('meter-fill','disabled')[0][12][12])
    def test_splitter_keeps_7_unit_hit_area_and_5_unit_grip(self):
        self.assertEqual(self.c['%General']['splitter_width'],'7')
        c=effective(self.c,'Splitter');self.assertEqual(7-int(c['frame.left'])-int(c['frame.right']),5)
        self.assertEqual(len(R.divider()[0]),7);self.assertEqual(len(R.grip(w=5)[0]),5)
    def test_splitter_two_orientations_share_same_master(self):
        im=R.divider();horizontal=[list(r) for r in zip(*im)]
        self.assertEqual((len(horizontal[0]),len(horizontal)),(24,7))
    def test_header_separator_is_global_engine_resource(self):
        sep=self.atlas.items['header-separator'];self.assertEqual(len(sep[0]),3)
        self.assertEqual(sep[6],[R.EDGE,R.LIGHT,R.FACE])
    def test_header_pressed_borders_invert(self):
        normal,n=R.surface('column');down,_=R.surface('column','pressed')
        self.assertEqual(n,3);self.assertEqual(normal[0][12],down[-1][12]);self.assertNotEqual(normal,down)
    def test_tree_open_closed_have_distinct_geometry(self):
        self.assertNotEqual(R.triangle('right'),R.triangle('down'))
        self.assertEqual(R.triangle('down'),[list(x) for x in zip(*R.triangle('right'))])
    def test_tree_right_left_are_mirrored(self):
        self.assertEqual(R.triangle('left'),[list(reversed(row)) for row in R.triangle('right')])
    def test_tree_disabled_remains_visible_without_black(self):
        pixels=[c for row in R.triangle('right','disabled') for c in row]
        self.assertIn('#858585',pixels);self.assertNotIn(R.INK,pixels)
    def test_normal_and_disabled_itemview_maps_do_not_paint_background(self):
        for state in ('normal','disabled'):self.assertTrue(all(c is None for row in R.row(state) for c in row))
    def test_three_item_selection_surfaces_are_distinct(self):
        self.assertEqual(len({json.dumps(R.row(s)) for s in ('focused','pressed','toggled')}),3)
        self.assertEqual(R.row('pressed')[5][5],self.c['GeneralColors']['highlight.color'])
    def test_groupbox_center_transparent(self):
        group,n=R.surface('section');self.assertEqual(n,3);self.assertIsNone(group[12][12])
        self.assertTrue(any(c is not None for row in group for c in row))
    def test_tooltip_map_is_opaque(self):
        self.assertTrue(all(c is not None for row in R.surface('hint')[0] for c in row))
    def test_dial_uses_engine_defined_names(self):
        for name in ('dial','dial-handle','dial-notches'):
            self.assertIn(name,self.nodes);self.assertIn(name+'-inactive',self.nodes)
        self.assertIn('dial-focus',self.nodes)
    def test_dial_has_transparent_exterior_and_separate_focus(self):
        body=R.dial();self.assertIsNone(body[0][0]);self.assertEqual(body[16][16],R.FACE)
        focus=R.dial('focus');self.assertIsNone(focus[16][16]);self.assertIn(R.INK,{c for row in focus for c in row})
    def test_mdi_is_separate_from_external_decoration(self):
        self.assertEqual(self.c['TitleBar']['indicator.element'],'ic-mdi-mark')
        self.assertEqual(self.c['TitleBar']['indicator.size'],'12')
        for kind in ('close','minimize','maximize','restore','shade'):
            self.assertIn('ic-mdi-mark-'+kind+'-normal',self.nodes)
    def test_mdi_background_explicit_native_states(self):
        self.assertIn('ic-mdi-title-focused',self.nodes);self.assertIn('ic-mdi-title-normal',self.nodes)
        self.assertNotEqual(self.atlas.items['ic-mdi-title-focused'],self.atlas.items['ic-mdi-title-normal'])
    def test_sizegrip_is_not_empty(self):
        self.assertEqual((len(R.resize_grip()),len(R.resize_grip()[0])),(15,15))
        self.assertTrue(any(c is not None for row in R.resize_grip() for c in row))
    def test_inactive_artwork_preserves_same_map(self):
        for name,im in self.atlas.items.items():
            if name.startswith(R.PREFIXES) and '-inactive' in name:self.assertEqual(im,self.atlas.items[name.replace('-inactive','')],name)
    def test_bad_arguments_rejected(self):
        for fn,args in ((R.blank,(0,1)),(R.surface,('bad',)),(R.surface,('column','bad')), (R.triangle,('bad',)),(R.dial,('bad',)),(R.grip,('normal',2,2)),(R.mdi_symbol,('bad',))):
            with self.assertRaises(ValueError):fn(*args)
    def test_rasterize_all_1694_new_resources(self):
        try:import cairosvg;from PIL import Image
        except ImportError:self.skipTest('CairoSVG/Pillow unavailable; no raster result.')
        count=0;ns='{http://www.w3.org/2000/svg}'
        for name,im in self.atlas.items.items():
            if not name.startswith(R.PREFIXES):continue
            h,w=len(im),len(im[0]);root=ET.Element(ns+'svg',{'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}'})
            g=ET.fromstring(ET.tostring(self.nodes[name]));g.attrib.pop('transform',None);root.append(g)
            raster=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(root)))).convert('RGBA')
            expected=bytes(v for row in im for c in row for v in ((0,0,0,0) if c is None else (*bytes.fromhex(c[1:]),255)))
            self.assertEqual(raster.tobytes(),expected,name);count+=1
        self.assertEqual(count,1694)
    def test_native_gallery_uses_native_actions(self):
        code=(ROOT/'tools/preview_controls.py').read_text()
        for token in ('QStyleFactory.create(\'kvantum\')','QTest.keyClick','QTest.mousePress','QTest.mouseRelease','QSplitter','QDial','QMdiArea','QTreeWidget','QTableWidget'):
            self.assertIn(token,code)
        for token in ('QProxyStyle','setStyleSheet(',"os.environ['QT_QPA_PLATFORM']"):
            self.assertNotIn(token,code)
    def test_quick_gallery_is_manual_without_substitute_mouse_handlers(self):
        code=(ROOT/'tests/qml/PreviewControls.qml').read_text()
        for token in ('Slider','ProgressBar','SplitView','Dial'):self.assertIn(token,code)
        for token in ('Canvas','MouseArea'):self.assertNotIn(token,code)
    def test_coverage_retains_native_and_out_of_scope_limits(self):
        doc=(ROOT/'docs/COBERTURA-IRIXCLASSIC.md').read_text()
        for text in ('Toolbox','thumbwheel','LED','Qt Quick','MDI','aberto','0.7.0-rc1'):self.assertIn(text,doc)
    def test_roadmap_all_blocks_and_integrated_review(self):
        doc=(ROOT/'PLANO-IRIXCLASSIC.md').read_text()
        for i in range(1,8):self.assertIn('| '+str(i)+'. ',doc)
        self.assertIn('revisão integrada',doc);self.assertIn('seta KDE continua sem solução confirmada',doc)
    def test_runtime_limit_no_historical_certification_claim(self):
        doc=(ROOT/'docs/CONTROLES.md').read_text()
        for text in ('não cópias pixel a pixel','State','0–0','decorativas','77','não é possível concluir'):self.assertIn(text,doc)

if __name__=='__main__':unittest.main()
