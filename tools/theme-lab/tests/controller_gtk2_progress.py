# SPDX-License-Identifier: GPL-3.0-or-later
"""Real controller progress scenes and separate-preview persistence (GTK2/3)."""
import json

def run(output,observation,click,wait,move_separate,restart,file_dialog,family="gtk2",control=13):
 def native(width,height,count):
  rows=[r for r in observation().get('native_controls',[]) if r['control']==control]
  return rows if len(rows)==count and all(r['width']==width and r['height']==height and (r['font_kind']==2 and not r['font'] if control==12 else r['font_kind']==1 and r['font']) for r in rows) else None
 wait(lambda:native(220,40,1),30)
 initial=json.loads((output/'home/lab/working.json').read_text())
 assert initial['selected_family']==family
 click('separatePreview');wait(lambda:native(220,40,2),30)
 wait(lambda:json.loads((output/'home/lab/working.json').read_text())['separate_preview'] is True,5)
 assert observation()['separate_preview_checked']
 move_separate()
 path=output/'home/reveal-spin';path.write_text('set-width 300')
 wait(lambda:observation().get('width_text')=='300',5)
 path.write_text('set-height 50');wait(lambda:observation().get('height_text')=='50',5)
 click('apply');rows=wait(lambda:native(300,50,2),30)
 model=json.loads((output/'home/lab/working.json').read_text())
 assert model['recipes'][family]['sizes'][control]==[300,50]
 assert all(model['recipes'][f]==recipe for f,recipe in initial['recipes'].items() if f!=family)
 latest=json.loads((output/'home/lab/generated/latest.json').read_text())
 folder=output/'home'/latest['generation_dir'].removeprefix('/home/domainos-test/')
 receipt=json.loads((folder/'RESULTADO.json').read_text())['families'][family]
 if family=='gtk2':
  kind='frame' if control==15 else 'list' if control==14 else 'arrow' if control==12 else 'scale_h' if control==8 else 'scale_v' if control==9 else 'spin' if control==6 else 'combo' if control==5 else 'text' if control==7 else 'entry' if control==4 else 'progress'
  assert kind in receipt['translated_controls'] and len(receipt[('scale' if control in (8,9) else kind)+'_style_id'])==16
  assert not receipt['recipe_applied']
 else:
  assert receipt['status']=='generated'
 move_separate()
 click('separatePreview');wait(lambda:native(300,50,1),15)
 wait(lambda:json.loads((output/'home/lab/working.json').read_text())['separate_preview'] is False,5)
 click('projectUndo');wait(lambda:native(300,50,2),30)
 assert observation()['separate_preview_checked']
 move_separate();click('projectRedo');wait(lambda:native(300,50,1),15)
 assert not observation()['separate_preview_checked']
 click('separatePreview');wait(lambda:native(300,50,2),30);move_separate()
 path.write_text('set-width 410')
 wait(lambda:json.loads((output/'home/lab/working.json').read_text())['recipes'][family]['sizes'][control][0]==410,10)
 scene=(output/'home/lab/scene.json')
 # Discover the actual scene path from the private controller contract.
 if not scene.exists():scene=output/'home/lab/applied-scene.json'
 scene_before=scene.read_bytes()
 file_dialog('save','/home/domainos-test/separate-project.json')
 saved=json.loads((output/'home/separate-project.json').read_text())
 assert saved['separate_preview'] is True and saved['recipes'][family]['sizes'][control]==[410,50]
 assert native(300,50,2)
 restart();wait(lambda:native(300,50,2),30)
 assert observation()['separate_preview_checked']
 assert scene.read_bytes()==scene_before,'Restart applied pending edits or rewrote scene'
 resumed=json.loads((output/'home/lab/working.json').read_text())
 assert resumed['separate_preview'] is True and resumed['recipes'][family]['sizes'][control]==[410,50]
 assert all(resumed['recipes'][f]==recipe for f,recipe in initial['recipes'].items() if f!=family)
 move_separate();click('separatePreview');wait(lambda:native(300,50,1),15)
 wait(lambda:json.loads((output/'home/lab/working.json').read_text())['separate_preview'] is False,5)
 restart();wait(lambda:native(300,50,1),30)
 assert not observation()['separate_preview_checked']
 file_dialog('load','/home/domainos-test/separate-project.json')
 wait(lambda:native(300,50,2),30)
 assert observation()['separate_preview_checked']
 assert scene.read_bytes()==scene_before
 restored=json.loads((output/'home/lab/working.json').read_text())
 assert restored['separate_preview'] is True and restored['recipes']==saved['recipes']
 return {'status':'passed','scope':f'Native {family} coupled/separate resizing, saved toggle, native Save/Load, project Undo/Redo and process restart with on/off preference; pending410×50 retained while applied300×50 scene bytes preserved.','native':rows,'gtk2_still_partial':True}

