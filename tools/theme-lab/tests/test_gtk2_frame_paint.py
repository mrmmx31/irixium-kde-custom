# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT,backend,model
from gtk2_frames import paint_frame,selected_fragment

class FramePaintTests(unittest.TestCase):
    def setUp(self):
        self.builder=backend.load_builder(ROOT)
        path=ROOT/'colors/DomainOS-SR10.4.colors'
        self.palette,_=backend.native_roles(ROOT,path,self.builder.art,backend.sha(path.read_bytes()))
        self.recipe=model()['recipes']['gtk2']
    def test_missing_roles_and_invalid_geometry_publish_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-list-pure-') as temp:
            out=Path(temp)/'absent'
            with self.assertRaisesRegex(ValueError,'effective role'):paint_frame(self.builder,self.recipe,{},out)
            self.assertFalse(out.exists())
            self.recipe['geometry']['control_padding_px']=True
            with self.assertRaisesRegex(ValueError,'geometry'):paint_frame(self.builder,self.recipe,self.palette,out)
            self.assertFalse(out.exists())
    def test_identity_palette_geometry_and_no_model_mutation(self):
        original=copy.deepcopy(self.recipe)
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-list-pure-') as temp:
            a=paint_frame(self.builder,self.recipe,self.palette,Path(temp)/'a')
            p=dict(self.palette);p[self.builder.art.ROLES['window-fg'][0]]='#010203'
            b=paint_frame(self.builder,self.recipe,p,Path(temp)/'b')
            self.assertNotEqual(a['style_id'],b['style_id']);self.assertEqual(a['assets'],b['assets'])
            self.assertIn('fg[SELECTED] = "#010203"',Path(b['rc']).read_text())
            changed=copy.deepcopy(self.recipe);changed['geometry']['font_px']+=1
            c=paint_frame(self.builder,changed,self.palette,Path(temp)/'c')
            self.assertNotEqual(a['style_id'],c['style_id'])
            rc=Path(a['rc']).read_text()
            self.assertIn('detail = "frame"',rc)
            self.assertNotIn('scrolled_window',rc)
        self.assertEqual(self.recipe,original)
    def test_unsupported_forced_state_is_explicit(self):
        for state in ('pressed','focus'):
            with self.assertRaisesRegex(ValueError,'unsupported'):selected_fragment(self.recipe,state,self.builder,self.palette)

if __name__=='__main__':unittest.main()
