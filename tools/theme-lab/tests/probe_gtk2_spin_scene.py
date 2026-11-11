# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Spin scene in an explicitly private Xvfb test."""
import os
assert os.environ.get('T04_PRIVATE_SPIN') == '1'
import copy,json,sys,time,subprocess
from PIL import Image
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_backend import ROOT,backend,model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from preview_text_editing import bind
from sample_contract import SAMPLES
import gi
gi.require_version('Gtk','2.0')
gi.require_version('Gdk','2.0')
from gi.repository import Gtk, Gdk
Gtk.init([])
output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
data=model();data['selected_family']='gtk2';r=data['recipes']['gtk2'];r.update(visible_controls=1<<6,selected_control=6,edit_state=0)
r['sizes']=[[0,0] for _ in range(16)];r['sizes'][6]=[260,44]
r['positions']=[[16,16] for _ in range(16)]
original=copy.deepcopy(data)
sources={'DomainOS':ROOT/'colors/DomainOS-SR10.4.colors','BreezeLight':Path('/usr/share/color-schemes/BreezeLight.colors'),'BreezeDark':Path('/usr/share/color-schemes/BreezeDark.colors')}
import configparser
yellow=configparser.ConfigParser(interpolation=None);yellow.optionxform=str;yellow.read(ROOT/'colors/DomainOS-SR10.4.colors')
yellow['General']['Name']='Artificial yellow test'
for section in ('Colors:Window','Colors:Button','Colors:View'):
 yellow[section]['BackgroundNormal']='236,216,112';yellow[section]['BackgroundAlternate']='216,196,92';yellow[section]['ForegroundNormal']='32,28,12'
yellow['Colors:Selection']['BackgroundNormal']='88,72,24';yellow['Colors:Selection']['ForegroundNormal']='255,248,216'
with (output/'TestYellow.colors').open('w') as stream:yellow.write(stream)
sources['TestYellow']=output/'TestYellow.colors'
gestures_only='--gestures-only' in sys.argv
if gestures_only:sources={'DomainOS':sources['DomainOS']}
class Writer:
 def __init__(self):self.events=[]
 def emit(self,action,index,project_hash,**fields):self.events.append({'action':action,'index':index,**fields})
rows=[]
def drain():
 end=time.monotonic()+.15
 while time.monotonic()<end:
  while Gtk.events_pending():Gtk.main_iteration()
  time.sleep(.001)
for name,scheme in sources.items():
 folder=output/name;folder.mkdir(exist_ok=True)
 receipt=generate_scrollbar_snapshot(backend,ROOT,folder,data,scheme)
 folder.chmod(0o700)
 assert 'spin' in receipt['translated_controls']
 Gtk.rc_parse(receipt['rc'])
 for origin in ('separate','coupled'):
  for state in ((0,) if gestures_only else (0,2,3)):
   candidate=copy.deepcopy(data);candidate['recipes']['gtk2']['edit_state']=state
   host=None
   if origin=='coupled':
    host=Gtk.Window();socket=Gtk.Socket();host.add(socket);host.show_all();drain()
   writer=Writer()
   session=NativeSession(backend,Gtk,Gdk,ROOT,receipt['rc'],candidate,'a'*64,writer,embed_window=socket.get_id() if host else None)
   scene=session.scene
   drain();metrics=scene.metrics()[0]
   assert metrics['id']=='spin' and scene.widgets[6].get_text()==str(SAMPLES['spin'])
   assert metrics['allocation'][2:]==[260,44],metrics
   assert metrics['origin']==origin and metrics['sensitive']==(state!=2)
   assert metrics['font_description'] and not metrics['font_not_applicable']
   image=folder/(origin+'-'+str(state)+'.png')
   subprocess.run(['import','-window','root',str(image)],check=True,timeout=10)
   screen=Image.open(image).convert('RGB')
   colors=json.loads((folder/'GTK2-NATIVE-COLORS.json').read_text())['colors']
   art=backend.load_builder(ROOT).art
   variant=2 if state==2 else 1 if state==3 else 0
   ox,oy=(host if host else scene.window).get_position()
   expected_track=art._rgb(colors[art.ROLES['view'][variant]])
   track=screen.getpixel((ox+150,oy+35))
   assert track==expected_track,(name,origin,state,track,expected_track)
   if gestures_only:
    subprocess.run(['xdotool','mousemove',str(ox+30),str(oy+35),'keydown','ctrl','click','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='select' and e['index']==6 for e in writer.events),writer.events
    assert scene.widgets[6].get_value()==SAMPLES['spin']
    subprocess.run(['xdotool','mousemove',str(ox+268),str(oy+24),'keydown','ctrl','mousedown','1','mousemove',str(ox+304),str(oy+48),'mouseup','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='move' and e['index']==6 and e['x']==52 and e['y']==40 for e in writer.events),writer.events
    assert scene.widgets[6].get_value()==SAMPLES['spin'] and scene.gestures.active is None
   if state==0:
    editor=scene.text_editors[6]
    scene.widgets[6].set_value(37);drain()
    scene.widgets[6].set_text('6');drain()
    prior_numeric_state=editor.read()
    changed=copy.deepcopy(candidate);changed['recipes']['gtk2']['sizes'][6]=[310,48]
    session.replace(changed,'b'*64);drain()
    assert session.scene.text_editors[6].read()==prior_numeric_state,(prior_numeric_state,session.scene.text_editors[6].read())
    session.scene.text_editors[6].step(-1);drain()
    assert session.scene.widgets[6].get_text()=='37'
    session.scene.text_editors[6].step(1);drain()
    assert session.scene.widgets[6].get_text()=='6'
    assert session.scene.metrics()[0]['allocation'][2:]==[310,48]
   rows.append({'scheme':name,'state':state,'track_rgb':track,**metrics})
   session.close()
   if host:host.destroy()
   drain()
assert data==original
result={'status':'passed','rows':rows,'scope':'Real GTK2 Spin, 4 palettes, normal/disabled/explicit backdrop, coupled/separate: size, numeric field, font and sensitivity; eight transactional rebuilds preserve partial numeric text/value/Undo/Redo. Interior pixels match effective view roles; not keyboard/clipboard or complete pixel/state or historical fidelity approval.','model_unchanged':True,'gestures_tested':gestures_only}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_scenes':len(rows),'model_unchanged':True,'gestures_tested':gestures_only}))
