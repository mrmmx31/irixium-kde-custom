# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Scale scene in an explicitly private Xvfb test."""
import os
assert os.environ.get('T04_PRIVATE_SCALE') == '1'
import copy,json,sys,time,subprocess,itertools
from PIL import Image
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_backend import ROOT,backend,model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from sample_contract import SAMPLES
import gi
gi.require_version('Gtk','2.0')
gi.require_version('Gdk','2.0')
from gi.repository import Gtk, Gdk, GObject
Gtk.init([])
output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
data=model();data['selected_family']='gtk2';r=data['recipes']['gtk2'];r.update(visible_controls=(1<<8)|(1<<9),selected_control=8,edit_state=0)
r['geometry']['scale_slider_width_px']=9;r['geometry']['scale_slider_length_px']=33
r['sizes']=[[0,0] for _ in range(16)];r['sizes'][8]=[260,44];r['sizes'][9]=[44,260]
r['positions']=[[16,16] for _ in range(16)];r['positions'][9]=[300,16]
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
 assert all(k in receipt['translated_controls'] for k in ('scale_h','scale_v'))
 Gtk.rc_parse(receipt['rc'])
 for origin in ('separate','coupled'):
  for state, selected in itertools.product((0,) if gestures_only else (0,2,3), (8,9)):
   candidate=copy.deepcopy(data);candidate['recipes']['gtk2']['edit_state']=state;candidate['recipes']['gtk2']['selected_control']=selected
   host=None
   if origin=='coupled':
    host=Gtk.Window();socket=Gtk.Socket();host.add(socket);host.show_all();drain()
   writer=Writer()
   session=NativeSession(backend,Gtk,Gdk,ROOT,receipt['rc'],candidate,'a'*64,writer,embed_window=socket.get_id() if host else None)
   scene=session.scene
   drain()
   metrics=scene.metrics()
   assert [m['id'] for m in metrics]==['scale_h','scale_v']
   assert all(m['origin']==origin and m['sensitive']==(state!=2 or m['index']!=selected) for m in metrics)
   assert all(m['font_description'] and not m['font_not_applicable'] for m in metrics)
   for prop,expected in (('slider-width',9),('slider-length',33)):
    spec=scene.widgets[selected].find_style_property(prop);value=GObject.Value();value.init(spec.value_type)
    scene.widgets[selected].style_get_property(prop,value)
    assert value.get_value()==expected,(origin,state,selected,prop,value.get_value())
   assert all(scene.widgets[index].get_draw_value() is True for index in (8,9))
   assert metrics[0]['allocation'][2:]==[260,44] and metrics[1]['allocation'][2:]==[44,260]
   image=folder/(origin+'-'+str(state)+'-'+str(selected)+'.png')
   subprocess.run(['import','-window','root',str(image)],check=True,timeout=10)
   screen=Image.open(image).convert('RGB')
   colors=json.loads((folder/'GTK2-NATIVE-COLORS.json').read_text())['colors']
   art=backend.load_builder(ROOT).art
   variant=2 if state==2 else 1 if state==3 else 0
   ox,oy=(host if host else scene.window).get_position()
   background=screen.getpixel((min(screen.width-1,ox+500),min(screen.height-1,oy+500)))
   role_counts=[]
   for index in (8,9):
    allocation=scene.widgets[index].get_allocation()
    roi=screen.crop((ox+allocation.x,oy+allocation.y,
                     ox+allocation.x+allocation.width,oy+allocation.y+allocation.height))
    expected=art._rgb(colors[art.ROLES['button'][variant if index==selected else 0]])
    count=sum(1 for pixel in roi.getdata() if pixel==expected)
    # BreezeLight can make the normal scale face pixel-identical to its host.
    assert expected==background or count>0,(name,origin,state,index,count,expected,background)
    role_counts.append(count)
   if gestures_only:
    for index,x,y in ((8,45,38),(9,322,45)):
     before=scene.widgets[index].get_value()
     subprocess.run(['xdotool','mousemove',str(ox+x),str(oy+y),'keydown','ctrl','click','1','keyup','ctrl'],check=True,timeout=5);drain()
     assert any(e['action']=='select' and e['index']==index for e in writer.events),writer.events
     assert scene.widgets[index].get_value()==before,(index,before,scene.widgets[index].get_value())
     subprocess.run(['xdotool','mousemove',str(ox+x),str(oy+y),'keydown','ctrl','mousedown','1','mousemove',str(ox+x+36),str(oy+y+24),'mouseup','1','keyup','ctrl'],check=True,timeout=5);drain()
     assert any(e['action']=='move' and e['index']==index and e['x']==(52 if index==8 else 336) and e['y']==40 for e in writer.events),writer.events
     assert scene.widgets[index].get_value()==before and scene.gestures.active is None
   if state==0:
    scene.widgets[8].set_value(37);scene.widgets[9].set_value(73);drain()
    assert all(any(e['action']=='native' and e['index']==i and e.get('state',{}).get('value')==v for e in writer.events) for i,v in ((8,37),(9,73))),writer.events
    changed=copy.deepcopy(candidate);changed['recipes']['gtk2']['sizes'][8]=[310,48];changed['recipes']['gtk2']['sizes'][9]=[48,310]
    session.replace(changed,'b'*64);drain()
    assert session.scene.widgets[8].get_value()==37 and session.scene.widgets[9].get_value()==73
    assert session.scene.metrics()[0]['allocation'][2:]==[310,48]
    assert session.scene.metrics()[1]['allocation'][2:]==[48,310]
   rows.append({'scheme':name,'state':state,'selected':selected,
                'role_pixel_counts':role_counts,'metrics':metrics})
   session.close()
   if host:host.destroy()
   drain()
assert data==original
scope = ('GTK2 horizontal/vertical scales in DomainOS normal state: four scenes '
         '(two selected controls × coupled/separate origins); Ctrl selection, '
         'dragging, value preservation and four transactional rebuilds.' if gestures_only else
         'Native horizontal/vertical GTK2 scales: four palettes, three variants, '
         'two origins; paired transactional rebuilds retain values and resized '
         'allocations. Not controller flow, full state pixels or historical approval.')
result={'status':'passed','rows':rows,'scope':scope,'model_unchanged':True,'gestures_tested':gestures_only}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_scenes':len(rows),'model_unchanged':True,'gestures_tested':gestures_only}))
