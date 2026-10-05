# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 2 and scrollbar pressure regressions, without a native Qt claim."""
from pathlib import Path
import configparser
import hashlib
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
import button_art as A
import scrollbar_art as S

PREFIXES=('ic-command-','ic-palettebutton-','ic-toolbarbutton-',
          'ic-input-','ic-inset-','ic-option-','ic-spin-','ic-optionmark-','ic-spinmark-','ic-checkmark-','menu-ic-checkmark-','item-ic-checkmark-','ic-radiomark-','menu-ic-radiomark-')
def canonical(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[canonical(ch) for ch in e]]
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def effective(c,s):
 d=effective(c,c[s]['inherits']) if c.has_option(s,'inherits') else {}
 d.update({k:v for k,v in c[s].items() if k!='inherits'});return d

class Buttons(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.atlas=B.build(); cls.base=json.loads((ROOT/'tests/data/buttons-baseline.json').read_text())
  cls.conf=configparser.ConfigParser(interpolation=None);cls.conf.optionxform=str
  cls.conf.read(ROOT/'IrixClassic/IrixClassic.kvconfig')
 def test_all_unrelated_svg_elements_and_positions_unchanged(self):
  nodes=ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot()
  data={e.get('id'):canonical(e) for e in nodes if e.get('id') and not e.get('id').startswith(PREFIXES+M.PREFIXES+TB.PREFIXES+RG.PREFIXES)
        and not (e.get('id').startswith('ic-scrollarrow-') and e.get('id').endswith(('-pressed','-toggled')))}
  self.assertEqual(len(data),self.base['protected_svg_count']); self.assertEqual(sha(data),self.base['protected_svg_sha256'])
 def test_non_button_effective_configuration_is_unchanged(self):
  for s,old in self.base['effective_sections'].items():
   if s in ('Tab','TabFrame','TabBarFrame','Menu','MenuItem','MenuBar','MenuBarItem','LineEdit','ComboBox','IndicatorSpinBox','GenericFrame','CheckBox','RadioButton') + RG.CONFIG_SECTIONS: continue  # Block 3: test_entries.py
   new=effective(self.conf,s)
   if s=='%General':
    new.pop('comment')
    new['active_tab_overlap']=old['active_tab_overlap']
    new['spread_progressbar']=old['spread_progressbar']
    for k in ('menu_separator_height','spread_menuitems'):new.pop(k,None)
    for k in ('combo_as_lineedit','combo_focus_rect','square_combo_button'):new[k]=old[k]
   self.assertEqual(old,new,s)
 def test_command_resting_profile_matches_reference_samples(self):
  image,_=A.surface('command','normal',52,31)
  self.assertEqual([image[y][20] for y in range(4)],['#4c4c4c','#e1e1e1','#cccccc','#999999'])
  self.assertEqual([image[y][20] for y in range(27,31)],['#999999','#737373','#4c4c4c','#252525'])
  self.assertEqual(image[15][:4],['#4c4c4c','#e1e1e1','#cccccc','#999999'])
 def test_command_face_matches_legacy_resting_map(self):
  self.assertEqual(A.surface('command','normal')[0],B.surface('button','normal')[0])
 def test_hover_does_not_create_a_new_button_highlight(self):
  for k in ('command','palettebutton','toolbarbutton'):
   self.assertEqual(A.surface(k,'normal'),A.surface(k,'focused'),k)
 def test_press_exposes_lower_and_right_lip(self):
  for k in ('command','palettebutton','toolbarbutton'):
   with self.subTest(k=k):
    n=A.surface(k,'normal')[0];p,fw=A.surface(k,'pressed')
    inner=1 if fw==3 else 0
    self.assertEqual(p[-1-inner][10],A.LIGHT)
    self.assertEqual(p[10][-1-inner],A.LIGHT)
    self.assertNotEqual(n,p)
    self.assertEqual(p[10][10],A.FACE)
 def test_command_outer_outline_does_not_move_on_press(self):
  a,_=A.surface('command','normal');b,_=A.surface('command','pressed')
  self.assertEqual(a[0],b[0]);self.assertEqual(a[-1],b[-1])
 def test_default_overlay_does_not_cover_inner_pressure_bevel(self):
  image,_=A.surface('command','pressed');ring=A.default_ring()
  for y,row in enumerate(ring):
   for x,c in enumerate(row):
    if c is not None:image[y][x]=c
  self.assertEqual(image[-2][10],A.LIGHT)
  self.assertEqual(image[10][-2],A.LIGHT)
  self.assertEqual(image[-1][10],'#000000')
 def test_default_ring_has_only_one_pixel_thickness(self):
  r=A.default_ring()
  self.assertEqual(sum(c is not None for row in r for c in row),4*24-4)
  self.assertTrue(all(c is None for row in r[1:-1] for c in row[1:-1]))
 def test_native_keyboard_focus_primitive_retained(self):
  for p in B.PARTS:self.assertIn('ic-focus-normal-'+p,self.atlas.items)
  self.assertFalse(self.conf.getboolean('PanelButtonCommand','focusFrame'))
 def test_persistent_toggle_distinct_from_momentary_press(self):
  p,_=A.surface('command','pressed');t,_=A.surface('command','toggled')
  self.assertNotEqual(t,p);self.assertEqual(t[10][10],'#919191')
 def test_disabled_shape_has_no_solid_black(self):
  for k in ('command','palettebutton','toolbarbutton'):
   im,_=A.surface(k,'disabled');self.assertNotIn('#000000',[c for row in im for c in row])
 def test_toolbar_rest_is_transparent_only_inside_its_own_control(self):
  im,_=A.surface('toolbarbutton','normal');self.assertTrue(all(c is None for row in im for c in row))
  im,_=A.surface('palettebutton','normal');self.assertTrue(all(c is not None for row in im for c in row))
 def test_every_new_button_state_has_complete_slices(self):
  for k in ('command','palettebutton','toolbarbutton'):
   for st in A.STATES:
    for part in ('',)+B.PARTS:
     self.assertIn('ic-'+k+'-'+st+('-'+part if part else ''),self.atlas.items)
 def test_nested_toolbutton_separators_exist(self):
  for k in ('palettebutton','toolbarbutton'):
   for part in ('','-top','-bottom'):
    self.assertIn('ic-'+k+'-separator'+part,self.atlas.items)
 def test_hitbox_dimensions_and_text_margins_not_reduced(self):
  for section,n in [('PanelButtonCommand',3),('PanelButtonTool',2)]:
   c=effective(self.conf,section)
   for side in ('top','bottom','left','right'):self.assertEqual(c['frame.'+side],str(n))
   self.assertEqual(c['min_height'],'22')
  self.assertEqual(self.conf['PanelButtonCommand']['text.margin.top'],'2')
  self.assertFalse(self.conf.getboolean('%General','button_contents_shift'))
 def test_scrollarrow_dark_mask_stays_in_same_place_on_press(self):
  for direction in ('up','down','left','right'):
   a=S.arrow('normal',direction);b=S.arrow('pressed',direction)
   mask=lambda im:{(x,y) for y in range(2,16) for x in range(2,16) if im[y][x]==S.DARK}
   self.assertEqual(mask(a),mask(b),direction)
 def test_scrollarrow_pressed_impression_has_lower_right_light_lip(self):
  for direction in ('up','down','left','right'):
   a=S.arrow('normal',direction);b=S.arrow('pressed',direction)
   changed={(x,y) for y in range(2,16) for x in range(2,16) if b[y][x]!=a[y][x]}
   self.assertGreater(len(changed),0,direction)
   self.assertTrue(all(b[y][x]==S.LIGHT for x,y in changed))
 def test_arrow_release_map_restores_without_timer_or_global_setting(self):
  self.assertEqual(S.arrow('focused','up'),S.arrow('normal','up'))
  self.assertNotEqual(S.arrow('pressed','up'),S.arrow('normal','up'))
  self.assertFalse(self.conf.getboolean('%General','animate_states'))
 def test_invalid_button_arguments_rejected(self):
  with self.assertRaises(ValueError):A.surface('wrong','normal')
  with self.assertRaises(ValueError):A.surface('command','wrong')
  with self.assertRaises(ValueError):A.surface('command','normal',4,4)
 def test_roadmap_keeps_all_blocks_and_feedback(self):
  text=(ROOT/'PLANO-IRIXCLASSIC.md').read_text()
  for i in range(1,8):self.assertIn('| '+str(i)+'. ',text)
  self.assertIn('0.2.0-rc1',text)
  self.assertIn('bloco 3',text.lower())

if __name__=='__main__':unittest.main()
