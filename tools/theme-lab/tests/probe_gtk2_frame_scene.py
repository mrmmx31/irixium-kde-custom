# SPDX-License-Identifier: GPL-3.0-or-later
"""Native frame foundation; requires an explicitly private X display."""
import os
assert os.environ.get('T04_PRIVATE_FRAME')=='1'
import configparser,copy,json,subprocess,sys,time,io
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT,backend,model
from gtk2_frames import snapshots
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
import gi
gi.require_version('Gtk','2.0');gi.require_version('Gdk','2.0')
from gi.repository import Gtk,Gdk
Gtk.init([])
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
builder=backend.load_builder(ROOT);recipe=model()['recipes']['gtk2'];before=copy.deepcopy(recipe)
sources={'DomainOS':ROOT/'colors/DomainOS-SR10.4.colors','BreezeLight':Path('/usr/share/color-schemes/BreezeLight.colors'),'BreezeDark':Path('/usr/share/color-schemes/BreezeDark.colors')}
yellow=configparser.ConfigParser(interpolation=None);yellow.optionxform=str;yellow.read(sources['DomainOS'])
for section in ('Colors:Window','Colors:Button','Colors:View'):
 yellow[section]['BackgroundNormal']='236,216,112';yellow[section]['ForegroundNormal']='32,28,12'
with (out/'Yellow.colors').open('w') as f:yellow.write(f)
sources['Yellow']=out/'Yellow.colors'
def drain():
 end=time.monotonic()+.1
 while time.monotonic()<end:
  while Gtk.events_pending():Gtk.main_iteration()
  time.sleep(.001)
gestures_only='--gestures-only' in sys.argv
if gestures_only:sources={'DomainOS':sources['DomainOS']}
class Writer:
 def __init__(self):self.events=[]
 def emit(self,action,index,project_hash,**fields):self.events.append(dict(action=action,index=index,**fields))
rows=[]
for name,source in sources.items():
 palette,_=backend.native_roles(ROOT,source,builder.art,backend.sha(source.read_bytes()))
 data=model();data['selected_family']='gtk2';r=data['recipes']['gtk2'];r.update(visible_controls=1<<15,selected_control=15)
 r['sizes']=[[0,0] for _ in range(16)];r['positions']=[[16,16] for _ in range(16)];r['sizes'][15]=[240,120]
 result=generate_scrollbar_snapshot(backend,ROOT,out/name,data,source);(out/name).chmod(0o700)
 for origin in ('coupled','separate'):
  for variant,index in ([('normal',0)] if gestures_only else [('normal',0),('backdrop',1),('disabled',2)]):
   host=None
   if origin=='coupled':
    host=Gtk.Window();socket=Gtk.Socket();host.add(socket);host.show_all();drain()
   candidate=copy.deepcopy(data);candidate['recipes']['gtk2']['edit_state']={'normal':0,'backdrop':3,'disabled':2}[variant]
   writer=Writer()
   session=NativeSession(backend,Gtk,Gdk,ROOT,result['rc'],candidate,'a'*64,writer,embed_window=socket.get_id() if host else None)
   scene=session.scene;window=scene.window
   if host is None:host=window
   drain();control=scene.frame_controls[15];frame=control.frame;label=control.label
   natural=Gtk.Requisition();frame.size_request(natural)
   assert scene.metrics()[0]['allocation'][2:]==[240,120]
   capture=out/name/(origin+'-'+variant+'.png');subprocess.run(['import','-window','root',str(capture)],check=True,timeout=10)
   screen=Image.open(capture).convert('RGB');ox,oy=host.get_position()
   face=builder.art._rgb(palette[builder.art.ROLES['window'][index]])
   assert screen.getpixel((ox+24,oy+40))==face,(name,origin,variant)
   reference=Image.open(io.BytesIO(snapshots(builder,recipe,palette)[variant][1])).convert('RGB')
   shadow=recipe['geometry']['shadow_px']
   for offset in range(shadow):
    assert screen.getpixel((ox+80,oy+16+offset))==reference.getpixel((shadow,offset)),(name,variant,'top',offset)
    assert screen.getpixel((ox+80,oy+16+119-offset))==reference.getpixel((shadow,2*shadow-offset)),(name,variant,'bottom',offset)
   assert label.get_pango_context().get_font_description().to_string()
   rows.append({'scheme':name,'origin':origin,'variant':variant,'allocation':[240,120],'natural_request':[natural.width,natural.height],'face_rgb':face,'bevel_layers_verified':shadow,'sensitive':frame.get_sensitive()})
   if gestures_only:
    writer.events.clear()
    subprocess.run(['xdotool','mousemove',str(ox+80),str(oy+40),'keydown','ctrl','click','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='select' and e['index']==15 for e in writer.events),writer.events
    subprocess.run(['xdotool','mousemove',str(ox+80),str(oy+40),'keydown','ctrl','mousedown','1','mousemove',str(ox+116),str(oy+64),'mouseup','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='move' and e['index']==15 and e['x']==52 and e['y']==40 for e in writer.events),writer.events
    assert not any(e['action']=='native' for e in writer.events) and scene.gestures.active is None
   if variant=='normal' and not gestures_only:
    changed=copy.deepcopy(candidate);changed['recipes']['gtk2']['sizes'][15]=[300,140]
    changed['recipes']['gtk2']['geometry']['control_padding_px']=7
    changed['recipes']['gtk2']['geometry']['font_px']=17
    folder=out/name/(origin+'-rebuild');folder.mkdir(exist_ok=True);folder.chmod(0o700)
    repaint=generate_scrollbar_snapshot(backend,ROOT,folder,changed,source)
    assert repaint['frame_style_id']!=result['frame_style_id']
    session.replace(changed,'b'*64,repaint['rc']);drain()
    updated=session.scene.frame_controls[15]
    assert session.scene.metrics()[0]['allocation'][2:]==[300,140]
    font=updated.label.get_pango_context().get_font_description()
    assert font.get_size_is_absolute() and font.get_size()==17*1024,font.to_string()
    assert updated.alignment.get_padding()==(7,7,7,7)
   session.close()
   if origin=='coupled':host.destroy()
   drain()
assert recipe==before
(out/'RESULTADO.json').write_text(json.dumps({'status':'passed','rows':rows,'native_controls':len(rows),'scope':'Native GtkFrame/label in two origins/four palettes/three variants. Face and top/bottom bevel layers match symbolic window-role raster. Integrated generation/scene/session, eight font/padding/size rebuilds. No controller or historical certification.'},ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_controls':len(rows)}))
