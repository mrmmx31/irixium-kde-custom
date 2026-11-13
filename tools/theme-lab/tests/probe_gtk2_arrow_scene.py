# SPDX-License-Identifier: GPL-3.0-or-later
"""Native standalone arrow scene in an explicitly private Xvfb test."""
import os
assert os.environ.get('T04_PRIVATE_ARROW') == '1'
import copy,json,sys,time,subprocess
from PIL import Image
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_backend import ROOT,backend,model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from gtk2_arrows import snapshot_images
from sample_contract import SAMPLES
import gi
gi.require_version('Gtk','2.0')
gi.require_version('Gdk','2.0')
from gi.repository import Gtk, Gdk
Gtk.init([])
output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
data=model();data['selected_family']='gtk2';r=data['recipes']['gtk2'];r.update(visible_controls=1<<12,selected_control=12,edit_state=0)
r['sizes']=[[0,0] for _ in range(16)];r['sizes'][12]=[64,48]
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
 assert 'arrow' in receipt['translated_controls']
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
   assert metrics['id']=='arrow' and isinstance(scene.widgets[12].get_child(),Gtk.Arrow)
   assert scene.widgets[12].get_child().get_property('arrow-type')==Gtk.ArrowType.DOWN
   assert metrics['allocation'][2:]==[64,48],metrics
   assert min(metrics['native_request_before_custom_size'])>=15,metrics
   assert metrics['origin']==origin and metrics['sensitive']==(state!=2)
   assert not metrics['font_description'] and metrics['font_not_applicable']
   image=folder/(origin+'-'+str(state)+'.png')
   subprocess.run(['import','-window','root',str(image)],check=True,timeout=10)
   screen=Image.open(image).convert('RGB')
   colors=json.loads((folder/'GTK2-NATIVE-COLORS.json').read_text())['colors']
   builder=backend.load_builder(ROOT);art=builder.art
   variant=2 if state==2 else 1 if state==3 else 0
   ox,oy=(host if host else scene.window).get_position()
   expected=art._rgb(colors[art.ROLES['button'][variant]])
   pixel=screen.getpixel((ox+24,oy+40))
   assert pixel==expected,(name,origin,state,pixel,expected)
   if gestures_only:
    subprocess.run(['xdotool','mousemove',str(ox+48),str(oy+40),'keydown','ctrl','click','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='select' and e['index']==12 for e in writer.events),writer.events
    assert not any(e['action']=='native' for e in writer.events),writer.events
    subprocess.run(['xdotool','mousemove',str(ox+48),str(oy+40),'keydown','ctrl','mousedown','1','mousemove',str(ox+84),str(oy+64),'mouseup','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='move' and e['index']==12 and e['x']==52 and e['y']==40 for e in writer.events),writer.events
    assert not any(e['action']=='native' for e in writer.events) and scene.gestures.active is None
    subprocess.run(['xdotool','mousemove',str(ox+84),str(oy+64),'click','1'],check=True,timeout=5);drain()
    assert any(e['action']=='native' and e['index']==12 and e.get('state',{}).get('clicked') for e in writer.events),writer.events
   if state==0:
    changed=copy.deepcopy(candidate);changed['recipes']['gtk2']['sizes'][12]=[96,52]
    changed['recipes']['gtk2']['scrollbar_parts']={'arrow_button':{'padding_px':1,'shadow_px':1,'state_relief':{'normal':'flat'}}}
    rebuild=folder/'rebuild';rebuild.mkdir(exist_ok=True);rebuild.chmod(0o700)
    repaint=generate_scrollbar_snapshot(backend,ROOT,rebuild,changed,scheme)
    assert repaint['arrow_style_id']!=receipt['arrow_style_id']
    assert all((Path(repaint['rc']).parent/k).read_bytes()==(Path(receipt['rc']).parent/k).read_bytes() for k in receipt['assets'] if k.startswith(('trough-','thumb-','arrow-')))
    session.replace(changed,'b'*64,repaint['rc']);drain()
    assert session.scene.metrics()[0]['allocation'][2:]==[96,52]
    assert session.scene.widgets[12].get_child().get_property('arrow-type')==Gtk.ArrowType.DOWN
    # Public GTK2 style properties report the new button border.
    assert session.scene.widgets[12].get_style().xthickness==1
   rows.append({'scheme':name,'state':state,'face_rgb':pixel,**metrics})
   session.close()
   if host:host.destroy()
   drain()
assert data==original
result={'status':'passed','rows':rows,'scope':'Native standalone GtkButton/GtkArrow scene:4 palettes/3 variants/2 origins,8 rebuilds change proposed size and button border/padding/relief while preserving direction and unrelated range assets. Gesture mode verifies Ctrl select/move without click then normal click. Not controller flow or historical approval.','model_unchanged':True,'gestures_tested':gestures_only}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_scenes':len(rows),'model_unchanged':True,'gestures_tested':gestures_only}))
