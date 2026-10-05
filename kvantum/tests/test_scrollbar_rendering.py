# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional independent SVG rasterization; CairoSVG is NOT Qt/Kvantum."""
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

AVAILABLE=bool(importlib.util.find_spec('cairosvg') and importlib.util.find_spec('PIL'))

@unittest.skipUnless(AVAILABLE, 'Optional CairoSVG/Pillow renderer not installed; not a Qt runtime test.')
class Rasterization(unittest.TestCase):
    def test_scrollbar_svg_rendered_pixels_match_the_maps(self):
        import cairosvg
        from PIL import Image,ImageColor
        atlas=B.build()
        svg=ET.parse(ROOT/'IrixClassic/IrixClassic.svg').getroot()
        ids={e.get('id'):e for e in svg if e.get('id')}
        tested=0
        for name,pixels in atlas.items.items():
            if not name.startswith(('ic-scrollarrow-','ic-scroll-')):continue
            h,w=len(pixels),len(pixels[0])
            doc=ET.Element('{'+B.NS+'}svg',{'version':'1.1','width':str(w),'height':str(h),
                                          'viewBox':f'0 0 {w} {h}','shape-rendering':'crispEdges'})
            node=copy.deepcopy(ids[name]);node.attrib.pop('transform',None);doc.append(node)
            image=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=ET.tostring(doc)))).convert('RGBA')
            expected=[ImageColor.getrgb(c)+(255,) if c else (0,0,0,0) for row in pixels for c in row]
            self.assertEqual(list(image.getdata()),expected,name);tested+=1
        self.assertEqual(tested,115)
