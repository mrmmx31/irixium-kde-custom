# SPDX-License-Identifier: GPL-3.0-or-later
"""Native TextView scene in an explicitly private Xvfb test."""
import os
assert os.environ.get('T04_PRIVATE_TEXT') == '1'
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
data=model();data['selected_family']='gtk2';r=data['recipes']['gtk2'];r.update(visible_controls=1<<7,selected_control=7,edit_state=0)
r['sizes']=[[0,0] for _ in range(16)];r['sizes'][7]=[320,120]
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
editing_only='--editing-only' in sys.argv
if editing_only: sources={'DomainOS':sources['DomainOS']}
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
 assert 'text' in receipt['translated_controls']
 Gtk.rc_parse(receipt['rc'])
 for origin in ('separate','coupled'):
  for state in ((0,) if editing_only else (0,2,3)):
   candidate=copy.deepcopy(data);candidate['recipes']['gtk2']['edit_state']=state
   host=None
   if origin=='coupled':
    host=Gtk.Window();socket=Gtk.Socket();host.add(socket);host.show_all();drain()
   session=NativeSession(backend,Gtk,Gdk,ROOT,receipt['rc'],candidate,'a'*64,None,embed_window=socket.get_id() if host else None)
   scene=session.scene
   drain();metrics=scene.metrics()[0]
   assert metrics['id']=='text' and scene.text_editors[7].read()[0]==SAMPLES['text']
   assert metrics['allocation'][2:]==[320,120],metrics
   assert metrics['origin']==origin and metrics['sensitive']==(state!=2)
   assert scene.text_editors[7].widget.get_sensitive()==(state!=2)
   assert scene.text_editors[7].widget.get_wrap_mode()==Gtk.WrapMode.WORD
   assert not scene.widgets[7].get_vscrollbar().get_visible()
   assert not scene.widgets[7].get_hscrollbar().get_visible()
   assert scene.widgets[7].get_hadjustment().get_upper()==scene.widgets[7].get_hadjustment().get_page_size()
   assert metrics['font_description'] and not metrics['font_not_applicable']
   image=folder/(origin+'-'+str(state)+'.png')
   subprocess.run(['import','-window','root',str(image)],check=True,timeout=10)
   screen=Image.open(image).convert('RGB')
   colors=json.loads((folder/'GTK2-NATIVE-COLORS.json').read_text())['colors']
   art=backend.load_builder(ROOT).art
   variant=2 if state==2 else 1 if state==3 else 0
   ox,oy=(host if host else scene.window).get_position()
   expected_track=art._rgb(colors[art.ROLES['view'][variant]])
   track=screen.getpixel((ox+300,oy+80))
   assert track==expected_track,(name,origin,state,track,expected_track)
   if state==0:
    editor=scene.text_editors[7]
    scene.text_editors[7].widget.get_buffer().set_text('Primeira ação — edição\nOutra linha');drain()
    scene.text_editors[7].widget.get_buffer().set_text('Segunda ação — edição\nMais uma linha');drain()
    changed=copy.deepcopy(candidate);changed['recipes']['gtk2']['sizes'][7]=[360,140]
    session.replace(changed,'b'*64);drain()
    assert session.scene.text_editors[7].read()[0]=='Segunda ação — edição\nMais uma linha'
    session.scene.text_editors[7].step(-1);drain()
    assert session.scene.text_editors[7].read()[0]=='Primeira ação — edição\nOutra linha'
    session.scene.text_editors[7].step(1);drain()
    assert session.scene.text_editors[7].read()[0]=='Segunda ação — edição\nMais uma linha'
    assert session.scene.metrics()[0]['allocation'][2:]==[360,140]
    text=session.scene.text_editors[7].widget
    assert text.get_left_margin()==0 and text.get_right_margin()==0
    text.get_buffer().set_text('\n'.join('Linha extensa '+str(i)+' — '+'abcdef '*30 for i in range(30)));drain()
    scroll=session.scene.widgets[7]
    assert scroll.get_vadjustment().get_upper()>scroll.get_vadjustment().get_page_size()
    assert scroll.get_hadjustment().get_upper()==scroll.get_hadjustment().get_page_size()
    scroll.get_vadjustment().set_value(40);drain()
    assert scroll.get_vadjustment().get_value()>0
    assert not scroll.get_hscrollbar().get_visible()
    if editing_only:
     top=host if host else session.scene.window
     top.set_title('T04 private text keyboard');drain()
     text.get_buffer().set_text('Ação Unicode\nLinha ç');drain()
     subprocess.run(['xdotool','search','--name','^T04 private text keyboard$','windowfocus'],check=True,timeout=5)
     text.grab_focus();drain()
     def key(keys):
      subprocess.run(['xdotool','key','--clearmodifiers',keys],check=True,timeout=5);drain()
     expected='Ação Unicode\nLinha ç'
     key('ctrl+a');key('ctrl+c');key('ctrl+x')
     assert session.scene.text_editors[7].read()[0]==''
     key('ctrl+z');assert session.scene.text_editors[7].read()[0]==expected
     key('ctrl+y');assert session.scene.text_editors[7].read()[0]==''
     key('ctrl+v');assert session.scene.text_editors[7].read()[0]==expected
     key('ctrl+z');assert session.scene.text_editors[7].read()[0]==''
     key('ctrl+shift+z');assert session.scene.text_editors[7].read()[0]==expected
   rows.append({'scheme':name,'state':state,'track_rgb':track,**metrics})
   session.close()
   if host:host.destroy()
   drain()
assert data==original
result={'status':'passed','rows':rows,'scope':'Real GTK2 TextView, 4 palettes, normal/disabled/explicit backdrop, coupled/separate: size, Unicode, font and sensitivity; eight transactional rebuilds preserve text/Undo/Redo. Interior pixels match effective view roles; not keyboard/clipboard or complete pixel/state or historical fidelity approval.','model_unchanged':True}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_scenes':len(rows),'model_unchanged':True,'keyboard_clipboard':editing_only}))
