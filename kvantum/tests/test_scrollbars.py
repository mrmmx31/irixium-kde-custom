# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import configparser
import hashlib
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import scrollbar_art as S
import build_classic as B


def canonical(e):
    return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(ch) for ch in e]]

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class Scrollbars(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.atlas=B.build()
        cls.baseline=json.loads((ROOT/'tests/data/scrollbar-baseline.json').read_text())
        cls.conf=configparser.ConfigParser(interpolation=None);cls.conf.optionxform=str
        cls.conf.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
        cls.xml=ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot()
    def effective(self,section):
        d=self.effective(self.conf[section]['inherits']) if 'inherits' in self.conf[section] else {}
        d.update({k:v for k,v in self.conf[section].items() if k!='inherits'})
        return d
    def test_other_svg_elements_unchanged(self):
        protected={e.get('id'):canonical(e) for e in self.xml if e.get('id')
                   and not e.get('id').startswith(('ic-scrollarrow-','ic-scroll-','ic-command-','ic-palettebutton-','ic-toolbarbutton-'))}
        self.assertEqual(len(protected),self.baseline['protected_svg_count'])
        self.assertEqual(digest(protected),self.baseline['protected_svg_sha256'])
    def test_other_effective_configurations_unchanged(self):
        for section,expected in self.baseline['effective_sections'].items():
            if section in ('PanelButtonCommand','PanelButtonTool'): continue  # Block 2 has its own baseline.
            actual=self.effective(section)
            if section=='%General': actual.pop('comment')
            self.assertEqual(actual,expected,section)
    def test_width_and_hitbox_metric_remains_18(self):
        self.assertEqual(self.conf['%General']['scroll_width'],'18')
        self.assertEqual(self.conf['Scrollbar']['indicator.size'],'18')
    def test_minimum_slider_extent_preserved(self):
        self.assertEqual(self.conf['%General']['scroll_min_extent'],'34')
    def test_arrows_remain_visible(self):
        self.assertEqual(self.conf['%General']['scroll_arrows'],'true')
        self.assertEqual(self.conf['%General']['transient_scrollbar'],'false')
    def test_arrow_cells_opaque_and_same_size_all_states(self):
        for state in B.STATES:
            for direction in ('up','down','left','right'):
                image=S.arrow(state,direction)
                self.assertEqual((len(image[0]),len(image)),(18,18))
                self.assertNotIn(None,[c for row in image for c in row])
    def test_up_arrow_matches_independent_reference_mask(self):
        image=S.arrow('normal','up')
        mask=[[S.DARK if image[y+4][x+5]==S.DARK else S.FACE for x in range(8)] for y in range(9)]
        self.assertEqual(mask,self.baseline['reference']['glyph_up'])
    def test_up_arrow_has_8_by_9_visible_bounds(self):
        image=S.arrow('normal','up')
        points=[(x,y) for y in range(2,16) for x in range(2,16) if image[y][x]==S.DARK]
        self.assertEqual((max(x for x,y in points)-min(x for x,y in points)+1,
                          max(y for x,y in points)-min(y for x,y in points)+1),(8,9))
    def test_horizontal_assets_follow_qvantum_transpose(self):
        for state in B.STATES:
            self.assertEqual(S.arrow(state,'left'),S.transpose(S.arrow(state,'up')))
            self.assertEqual(S.arrow(state,'right'),S.transpose(S.arrow(state,'down')))
    def test_down_glyph_is_mirrored_without_displacement(self):
        up=S.arrow('normal','up');down=S.arrow('normal','down')
        up_points={(x,y) for y in range(2,16) for x in range(2,16) if up[y][x]==S.DARK}
        down_points={(x,y) for y in range(2,16) for x in range(2,16) if down[y][x]==S.DARK}
        self.assertEqual({(17-x,17-y) for x,y in up_points},down_points)
    def test_hover_not_an_additional_highlight(self):
        for direction in ('up','down','left','right'):
            self.assertEqual(S.arrow('normal',direction),S.arrow('focused',direction))
        self.assertEqual(S.thumb('normal'),S.thumb('focused'))
        self.assertEqual(S.grip('normal'),S.grip('focused'))
    def test_press_changes_bevel_and_adds_lip_without_moving_dark_mask(self):
        a=S.arrow('normal','up');b=S.arrow('pressed','up')
        self.assertNotEqual(a,b)
        mask=lambda im:{(x,y) for y in range(2,16) for x in range(2,16) if im[y][x]==S.DARK}
        self.assertEqual(mask(a),mask(b))
        self.assertNotEqual([r[2:16] for r in a[2:16]],[r[2:16] for r in b[2:16]])
        self.assertEqual(S.grip('normal'),S.grip('pressed'))
    def test_disabled_arrow_is_distinct_and_has_no_black(self):
        a=S.arrow('disabled','up')
        self.assertNotEqual(a,S.arrow('normal','up'))
        self.assertNotIn(S.INK,[c for r in a for c in r])
    def test_three_grip_pairs_have_pitch_four(self):
        image=S.grip('normal')
        light_rows=[i for i,row in enumerate(image) if all(c==S.LIGHT for c in row)]
        self.assertEqual(light_rows,[0,4,8])
    def test_grip_pairs_are_light_then_black(self):
        image=S.grip('normal')
        for y in (0,4,8):
            self.assertEqual(image[y],[S.LIGHT]*18)
            self.assertEqual(image[y+1],[S.LIGHT]+[S.INK]*17)
    def test_grip_gaps_are_transparent(self):
        for y in (2,3,6,7): self.assertEqual(S.grip('normal')[y],[None]*18)
    def test_grip_full_width_contract(self):
        self.assertEqual(self.conf['ScrollbarSlider']['frame.left'],'0')
        self.assertEqual(self.conf['ScrollbarSlider']['frame.right'],'0')
        self.assertEqual(self.conf['ScrollbarSlider']['indicator.size'],'10')
        self.assertEqual(self.conf['%General']['center_scrollbar_indicator'],'false')
        self.assertEqual(len(self.atlas.items['ic-scroll-grip-normal'][0]),18)
    def test_thumb_side_profile_matches_reference(self):
        self.assertEqual([S.thumb('normal')[5]],self.baseline['reference']['thumb_profile'])
    def test_thumb_caps_match_reference(self):
        self.assertEqual(S.thumb('normal')[:2],self.baseline['reference']['thumb_top'])
        self.assertEqual(S.thumb('normal')[-3:],self.baseline['reference']['thumb_bottom'])
    def test_grip_composited_on_sides_matches_reference(self):
        row=S.thumb('normal')[5]; image=[row[:] for _ in range(10)]
        for y,r in enumerate(S.grip('normal')):
            for x,c in enumerate(r):
                if c is not None: image[y][x]=c
        self.assertEqual(image,self.baseline['reference']['grip_composited'])
    def test_frame_slices_have_expected_dimensions(self):
        d=self.atlas.items
        for state in B.STATES:
            self.assertEqual((len(d['ic-scroll-thumb-'+state][0]),len(d['ic-scroll-thumb-'+state])),(18,27))
            self.assertEqual(len(d['ic-scroll-thumb-'+state+'-top']),2)
            self.assertEqual(len(d['ic-scroll-thumb-'+state+'-bottom']),3)
    def test_grip_at_minimum_length_does_not_touch_caps(self):
        for height in (34,35,50,81,210):
            start=(height-S.GRIP_HEIGHT)//2
            self.assertGreaterEqual(start,2)
            self.assertLessEqual(start+S.GRIP_HEIGHT,height-3)
    def test_legacy_slider_resources_still_present(self):
        for name in ('ic-groove-normal','ic-thumb-normal','ic-slidercursor-normal','ic-slidergrip-normal'):
            self.assertIn(name,self.atlas.items)
    def test_standard_svg_names_requested_by_engine_exist(self):
        for state in ('normal','focused','pressed','disabled'):
            for prefix in ('ic-scroll-grip','ic-scroll-thumb','ic-scroll-groove'):
                self.assertIn(prefix+'-'+state,self.atlas.items)
    def test_no_qml_window_decoration_dependency(self):
        text=(ROOT/'tools/scrollbar_art.py').read_text()
        self.assertNotIn('org.kde.kwin',text)
    def test_roadmap_covers_all_seven_blocks(self):
        text=(ROOT/'PLANO-IRIXCLASSIC.md').read_text()
        for block in range(1,8): self.assertIn('| '+str(block)+'. ',text)
        self.assertIn('aceitação em Qt/KDE pendente',text)
    def test_historical_limits_are_documented(self):
        text=(ROOT/'docs/ROLAGEM.md').read_text()
        for term in ('Escape','0,7','Sem intervalo','18','impressão'):
            self.assertIn(term.lower(),text.lower())
    def test_bad_direction_is_rejected(self):
        with self.assertRaises(ValueError): S.arrow('normal','diagonal')
    def test_too_short_thumb_rejected(self):
        with self.assertRaises(ValueError): S.thumb('normal',4)

if __name__=='__main__': unittest.main()
