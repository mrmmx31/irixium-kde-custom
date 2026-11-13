# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone list foundation; only run in a private display/namespace."""
import os
assert os.environ.get('T04_PRIVATE_LIST')=='1'
import configparser,copy,json,subprocess,sys,time
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT,backend,model
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
yellow['Colors:Selection']['BackgroundNormal']='88,72,24';yellow['Colors:Selection']['ForegroundNormal']='255,248,216'
with (out/'Yellow.colors').open('w') as f:yellow.write(f)
sources['Yellow']=out/'Yellow.colors'
def drain():
 end=time.monotonic()+.08
 while time.monotonic()<end:
  while Gtk.events_pending():Gtk.main_iteration()
  time.sleep(.001)
def rgb(color):return [color.red//257,color.green//257,color.blue//257]
gestures_only='--gestures-only' in sys.argv
if gestures_only:sources={'DomainOS':sources['DomainOS']}
class Writer:
 def __init__(self):self.events=[]
 def emit(self,action,index,project_hash,**fields):self.events.append(dict(action=action,index=index,**fields))
rows=[]
for name,source in sources.items():
 palette,_=backend.native_roles(ROOT,source,builder.art,backend.sha(source.read_bytes()))
 data=model();data['selected_family']='gtk2';data['recipes']['gtk2'].update(visible_controls=1<<14,selected_control=14)
 data['recipes']['gtk2']['sizes']=[[0,0] for _ in range(16)];data['recipes']['gtk2']['positions']=[[16,16] for _ in range(16)]
 data['recipes']['gtk2']['sizes'][14]=[320,180];data['recipes']['gtk2']['positions'][14]=[16,16]
 result=generate_scrollbar_snapshot(backend,ROOT,out/name,data,source);(out/name).chmod(0o700)
 for origin in ('coupled','separate'):
  for variant,index in ([('normal',0)] if gestures_only else [('normal',0),('backdrop',1),('disabled',2)]):
   host=None
   if origin=='coupled':
    host=Gtk.Window();socket=Gtk.Socket();host.add(socket);host.show_all();drain()
   candidate=copy.deepcopy(data);candidate['recipes']['gtk2']['edit_state']={'normal':0,'disabled':2,'backdrop':3}[variant]
   writer=Writer()
   session=NativeSession(backend,Gtk,Gdk,ROOT,result['rc'],candidate,'a'*64,writer,embed_window=socket.get_id() if host else None)
   scene=session.scene;window=scene.window
   if host is None:host=window
   host.set_title('T04 private list');drain()
   listing=scene.list_controls[14];scroll=listing.widget;tree=listing.view;store=listing.store;column=tree.get_column(0);fixed=scene.fixed
   minimum=Gtk.Requisition();scroll.size_request(minimum)
   assert scene.metrics()[0]['allocation'][2:]==[320,180]
   assert tree.get_sensitive()==(index!=2)
   expected=list(builder.art._rgb(palette[builder.art.ROLES['view'][index]]))
   capture=out/name/(origin+'-'+variant+'.png')
   subprocess.run(['import','-window','root',str(capture)],check=True,timeout=10)
   screenshot=Image.open(capture).convert('RGB');ox,oy=host.get_position()
   actual=list(screenshot.getpixel((ox+200,oy+140)))
   assert actual==expected,(name,variant,actual,expected)
   expected_selection=list(builder.art._rgb(palette[builder.art.ROLES['selection'][index]]))
   area=tree.get_background_area(Gtk.TreePath.new_from_string('1'),column)
   origin_xy=tree.translate_coordinates(fixed,0,0)
   tx,ty=origin_xy[-2:];tx+=ox;ty+=oy
   actual_selection=list(screenshot.getpixel((tx+200,ty+area.y+area.height//2)))
   assert actual_selection==(expected if index==2 else expected_selection),(name,variant,actual_selection,expected_selection)
   if gestures_only:
    writer.events.clear();selected=listing.snapshot()['selected']
    subprocess.run(['xdotool','mousemove',str(ox+200),str(oy+34),'keydown','ctrl','click','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='select' and e['index']==14 for e in writer.events),writer.events
    assert listing.snapshot()['selected']==selected and not any(e['action']=='native' for e in writer.events),writer.events
    subprocess.run(['xdotool','mousemove',str(ox+200),str(oy+34),'keydown','ctrl','mousedown','1','mousemove',str(ox+236),str(oy+58),'mouseup','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='move' and e['index']==14 and e['x']==52 and e['y']==40 for e in writer.events),writer.events
    assert listing.snapshot()['selected']==selected and scene.gestures.active is None
    subprocess.run(['xdotool','mousemove',str(ox+236),str(oy+58),'click','1'],check=True,timeout=5);drain()
    assert listing.snapshot()['selected']==['0']
    assert any(e['action']=='native' for e in writer.events),writer.events
   if variant=='normal' and not gestures_only:
    tree.grab_focus();drain()
    subprocess.run(['xdotool','search','--name','^T04 private list$','windowfocus'],check=True,timeout=5)
    subprocess.run(['xdotool','key','--clearmodifiers','Down'],check=True,timeout=5);drain()
    selected_model,it=tree.get_selection().get_selected();assert selected_model.get_value(it,0)=='Outro item'
    for i in range(40):store.append(['Linha extensa '+str(i)+' — '+'abcdef '*30])
    drain();assert scroll.get_vadjustment().get_upper()>scroll.get_vadjustment().get_page_size()
    assert scroll.get_hadjustment().get_upper()>scroll.get_hadjustment().get_page_size()
    scroll.get_vadjustment().set_value(40);drain();assert scroll.get_vadjustment().get_value()>0
   if variant=='normal' and not gestures_only:
    scroll.get_hadjustment().set_value(20);drain()
    saved=listing.snapshot()
    changed=copy.deepcopy(candidate);changed['recipes']['gtk2']['sizes'][14]=[360,200]
    session.replace(changed,'b'*64);drain()
    replacement=session.scene.list_controls[14]
    assert replacement.snapshot()==saved,(replacement.snapshot(),saved)
    assert session.scene.metrics()[0]['allocation'][2:]==[360,200]
   rows.append({'scheme':name,'origin':origin,'variant':variant,'allocation':[320,180],'natural_request':[minimum.width,minimum.height],'view_rgb':expected,'selection_rgb':expected_selection})
   session.close()
   if origin=='coupled':host.destroy()
   drain()
assert recipe==before
(out/'RESULTADO.json').write_text(json.dumps({'status':'passed','rows':rows,'native_controls':len(rows),'scope':'Integrated GtkTreeView/GtkScrolledWindow with eight state-preserving rebuilds: native allocation, selection keyboard and two-axis scrolling, effective KDE style roles. Not integrated scene/controller or full pixel/historical proof.'},ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_controls':len(rows)}))
