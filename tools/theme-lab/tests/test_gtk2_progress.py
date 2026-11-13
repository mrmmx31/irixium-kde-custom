# SPDX-License-Identifier: GPL-3.0-or-later
import copy,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT,model,backend
from gtk2_progress import geometry_lines,paint_progress,selected_fragment
from native_scene_gtk2 import ScrollbarScene,scene_records

class ProgressTests(unittest.TestCase):
 def test_geometry_and_model_preserved(self):
  data=model();before=copy.deepcopy(data);r=data['recipes']['gtk2'];r['visible_controls']=1<<13
  self.assertEqual([x['id'] for x in scene_records(data)],['progress'])
  self.assertIn('  font_name = "13px"',geometry_lines(r))
  before['recipes']['gtk2']['visible_controls']=1<<13
  self.assertEqual(data,before)
 def test_missing_role_has_no_output(self):
  with tempfile.TemporaryDirectory(dir=Path.home()/'tempia',prefix='qa-progress-pure-') as d:
   target=Path(d)/'absent'
   with self.assertRaisesRegex(ValueError,'effective role'):
    paint_progress(backend.load_builder(ROOT),model()['recipes']['gtk2'],{},target)
   self.assertFalse(target.exists())
 def test_missing_runtime_style_rejected_before_widget_creation(self):
  data=model();data['recipes']['gtk2']['visible_controls']=1<<13
  with self.assertRaisesRegex(ValueError,'identidade do estilo'):
   ScrollbarScene(None,data)
 def test_progress_value_uses_motif_above_trough_layout_and_kde_role(self):
  art=backend.load_builder(ROOT).art
  palette=art.DEFAULT.copy()
  with tempfile.TemporaryDirectory(dir=Path.home()/'tempia',prefix='qa-progress-style-') as d:
   result=paint_progress(backend.load_builder(ROOT),model()['recipes']['gtk2'],palette,Path(d))
   source=Path(result['rc']).read_text(encoding='utf-8')
   self.assertIn('widget "*themeLabProgressValue_'+result['style_id']+'"',source)
   self.assertIn('fg[NORMAL]',source)
   expected=art._rgb(palette[art.ROLES['view-fg'][0]])
   self.assertIn('#%02x%02x%02x'%expected,source)
 def test_forced_press_not_falsely_implemented(self):
  r=model()['recipes']['gtk2']
  with self.assertRaisesRegex(ValueError,'unsupported forced state'):
   selected_fragment(r,'pressed',None,None)

if __name__=='__main__':unittest.main()
