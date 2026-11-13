# SPDX-License-Identifier: GPL-3.0-or-later
"""Native ComboBox scene in an explicitly private Xvfb test."""
import os
assert os.environ.get('T04_PRIVATE_COMBO') == '1'
import copy,json,sys,time,subprocess
from PIL import Image
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_backend import ROOT,backend,model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from gtk2_combos import header_relief_plan
from preview_text_editing import bind
from sample_contract import SAMPLES
import gi
gi.require_version('Gtk','2.0')
gi.require_version('Gdk','2.0')
from gi.repository import Gtk, Gdk
Gtk.init([])
output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
data=model();data['selected_family']='gtk2';r=data['recipes']['gtk2'];r.update(visible_controls=1<<5,selected_control=5,edit_state=0)
r['sizes']=[[0,0] for _ in range(16)];r['sizes'][5]=[260,44]
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
if gestures_only: sources={'DomainOS':sources['DomainOS']}
class Writer:
 def __init__(self): self.events=[]
 def emit(self,action,index,project_hash,**fields): self.events.append({'action':action,'index':index,**fields})
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
 assert 'combo' in receipt['translated_controls']
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
   assert metrics['id']=='combo' and scene.combo_widgets[5].get_active_text()==SAMPLES['combo_a']
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
   expected_track=art._rgb(colors[art.ROLES['button'][variant]])
   track=screen.getpixel((ox+150,oy+35))
   assert track==expected_track,(name,origin,state,track,expected_track)
   combo=scene.combo_widgets[5]
   if gestures_only:
    subprocess.run(['xdotool','mousemove',str(ox+30),str(oy+35),'keydown','ctrl','click','1','keyup','ctrl'],check=True,timeout=5);drain()
    assert any(e['action']=='select' and e['index']==5 for e in writer.events),(writer.events,combo.get_property('popup-shown'))
    assert not combo.get_property('popup-shown')
    assert combo.get_active()==0
   popup_pixels=None
   if state!=2:
    if gestures_only:
     subprocess.run(['xdotool','click','1'],check=True,timeout=5)
    else:
     combo.popup()
    drain()
    assert combo.get_property('popup-shown')
    menus=[w.get_child() for w in Gtk.Window.list_toplevels()
           if isinstance(w.get_child(),Gtk.Menu) and w.get_child().get_attach_widget() is combo]
    assert len(menus)==1
    menu=menus[0]
    assert menu.get_name().endswith('Popup_'+receipt['combo_style_id'])
    menu.select_item(menu.get_children()[0]);drain()
    popup_file=folder/(origin+'-'+str(state)+'-popup.png')
    subprocess.run(['import','-window','root',str(popup_file)],check=True,timeout=10)
    popup=Image.open(popup_file).convert('RGB')
    mx,my=menu.get_toplevel().get_position()
    menu_box=menu.get_allocation();mx+=menu_box.x;my+=menu_box.y
    row=menu.get_children()[-1].get_allocation()
    normal_pixel=popup.getpixel((mx+row.x+row.width-6,my+row.y+row.height//2))
    row0=menu.get_children()[0].get_allocation()
    selected_pixel=popup.getpixel((mx+row0.x+row0.width-6,my+row0.y+row0.height//2))
    # VUE menu popups use the same semantic surface as their menubar/header;
    # selection and window roles would misrepresent the historical screenshot.
    expected_menu=art._rgb(colors[art.ROLES['header'][variant]])
    expected_selection=expected_menu
    shell_plan=header_relief_plan(backend.load_builder(ROOT), 'light',
                                  inactive=variant==1)
    expected_shell_light=art._rgb(art.evaluate(shell_plan,colors))
    shell_pixel=popup.getpixel((mx+menu_box.width//2,my+4))
    assert normal_pixel==expected_menu,(name,origin,state,normal_pixel,expected_menu)
    assert selected_pixel==expected_selection,(name,origin,state,selected_pixel,expected_selection)
    assert shell_pixel==expected_shell_light,(name,origin,state,'popup shell light',shell_pixel,expected_shell_light)
    popup_pixels={'normal':normal_pixel,'highlight':selected_pixel,'shell':shell_pixel}
    if gestures_only:
     last=menu.get_children()[-1].get_allocation()
     subprocess.run(['xdotool','mousemove',str(mx+last.x+last.width//2),str(my+last.y+last.height//2),'click','1'],check=True,timeout=5);drain()
     assert combo.get_active()==2 and not combo.get_property('popup-shown')
     combo.set_active(0)
     subprocess.run(['xdotool','mousemove',str(ox+30),str(oy+35),'click','5'],check=True,timeout=5);drain()
     assert combo.get_active()==1,(origin,combo.get_active())
     # Exercise owned Gdk.Event union copies repeatedly, including endpoints:
     # dropping a copied event must not invalidate its native Gdk.Window.
     for direction, expected in (('4',0),('5',2)):
      subprocess.run(['xdotool','click','--repeat','32','--delay','2',direction],check=True,timeout=5);drain()
      assert combo.get_active()==expected and combo.get_window() is not None
     combo.set_active(1)
     subprocess.run(['xdotool','keydown','ctrl','mousedown','1','mousemove',str(ox+66),str(oy+59),'mouseup','1','keyup','ctrl'],check=True,timeout=5);drain()
     assert any(e['action']=='move' and e['index']==5 and e['x']==52 and e['y']==40 for e in writer.events),writer.events
     assert combo.get_active()==1 and not combo.get_property('popup-shown')
     assert scene.gestures.active is None
     assert scene.widgets[5].get_allocation().x==52
    else:
     combo.popdown();drain()
   if state==0:
    top=host if host else scene.window
    top.set_title('T04 private combo keyboard');drain()
    subprocess.run(['xdotool','search','--name','^T04 private combo keyboard$','windowfocus'],check=True,timeout=5)
    combo.grab_focus();drain()
    subprocess.run(['xdotool','key','--clearmodifiers','End'],check=True,timeout=5);drain()
    assert combo.get_active()==2 and combo.get_active_text()==SAMPLES['combo_c']
    changed=copy.deepcopy(candidate);changed['recipes']['gtk2']['sizes'][5]=[310,48]
    session.replace(changed,'b'*64);drain()
    assert session.scene.combo_widgets[5].get_active()==2
    assert session.scene.metrics()[0]['allocation'][2:]==[310,48]
   rows.append({'scheme':name,'state':state,'track_rgb':track,'popup_pixels':popup_pixels,**metrics})
   session.close()
   if host:host.destroy()
   drain()
assert data==original
result={'status':'passed','rows':rows,'scope':'GTK2 ComboBox coupled/separate: size, sample labels, font, sensitivity, keyboard End and active-item preservation across reconstruction; button and popup surfaces follow effective KDE roles, with VUE popup rows mapped to Header. Gestures mode additionally proves actual Ctrl selection/drag, ordinary popup/item click and native wheel. Not a complete pixel/state matrix or historical fidelity approval.','model_unchanged':True,'gestures_tested':gestures_only}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_scenes':len(rows),'model_unchanged':True}))
