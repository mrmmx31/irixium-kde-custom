# SPDX-License-Identifier: GPL-3.0-or-later
"""Independent SVG renderer check; explicitly not Qt/Kvantum."""
import copy
import importlib.util
import io
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_classic as B
@unittest.skipUnless(importlib.util.find_spec('PIL') and importlib.util.find_spec('cairosvg'), 'Pillow/CairoSVG ausentes')
class ButtonRendering(unittest.TestCase):
 def test_new_button_svg_matches_all_278_maps(self):
  from PIL import Image,ImageColor
  import cairosvg
  atlas=B.build();nodes={e.get('id'):e for e in ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot() if e.get('id')}
  count=0
  for name,pixels in atlas.items.items():
   if not name.startswith(('ic-command-','ic-palettebutton-','ic-toolbarbutton-')):continue
   h,w=len(pixels),len(pixels[0]);doc=ET.Element('{'+B.NS+'}svg',{'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}'})
   child=copy.deepcopy(nodes[name]);child.attrib.pop('transform',None);doc.append(child)
   im=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(doc)))).convert('RGBA')
   expected=[ImageColor.getrgb(c)+(255,) if c else (0,0,0,0) for row in pixels for c in row]
   actual=[im.getpixel((x,y)) for y in range(h) for x in range(w)]
   self.assertEqual(actual,expected,name);count+=1
  self.assertEqual(count,278)
