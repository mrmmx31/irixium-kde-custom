# SPDX-License-Identifier: GPL-3.0-or-later
"""Native progress scene in an explicitly private Xvfb test."""
import os
assert os.environ.get('T04_PRIVATE_PROGRESS') == '1'
import copy,json,sys,time,subprocess
from PIL import Image
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_backend import ROOT,backend,model
from gtk2_generation import generate_scrollbar_snapshot
from native_scene_gtk2 import ScrollbarScene
from gtk2_runtime_state import capture,restore
from sample_contract import SAMPLES
import gi
gi.require_version('Gtk','2.0')
from gi.repository import Gtk
Gtk.init([])
output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
data=model();data['selected_family']='gtk2';r=data['recipes']['gtk2'];r.update(visible_controls=1<<13,selected_control=13,edit_state=0)
r['sizes']=[[0,0] for _ in range(16)];r['sizes'][13]=[220,40]
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
rows=[]
def drain():
 end=time.monotonic()+.15
 while time.monotonic()<end:
  while Gtk.events_pending():Gtk.main_iteration()
  time.sleep(.001)
for name,scheme in sources.items():
 folder=output/name;folder.mkdir(exist_ok=True)
 receipt=generate_scrollbar_snapshot(backend,ROOT,folder,data,scheme)
 assert 'progress' in receipt['translated_controls']
 Gtk.rc_parse(receipt['rc'])
 for origin in ('separate','coupled'):
  for state in (0,2,3):
   candidate=copy.deepcopy(data);candidate['recipes']['gtk2']['edit_state']=state
   host=None
   if origin=='coupled':
    host=Gtk.Window();socket=Gtk.Socket();host.add(socket);host.show_all();drain()
   scene=ScrollbarScene(Gtk,candidate,embed_window=socket.get_id() if host else None,progress_style_id=receipt['progress_style_id'])
   drain();metrics=scene.metrics()[0]
   assert metrics['id']=='progress' and metrics['fraction']==SAMPLES['level']/100.0
   assert all(value>0 for value in metrics['native_request_before_custom_size']),metrics
   assert scene.progress_values[13].get_text()==str(SAMPLES['level'])+'%'
   assert not scene.progress_widgets[13].get_property('show-text')
   assert scene.progress_values[13].get_name().startswith('themeLabProgressValue_' if state==0 else 'themeLabInsensitiveProgressValue_' if state==2 else 'themeLabBackdropProgressValue_')
   value_rect=scene.progress_values[13].get_allocation();bar_rect=scene.progress_widgets[13].get_allocation()
   assert value_rect.y+value_rect.height<=bar_rect.y,(value_rect,bar_rect)
   restore(scene,{'progress':0.375})
   assert capture(scene)['progress']==0.375
   assert scene.progress_values[13].get_text()=='37.5%'
   restore(scene,{'progress':SAMPLES['level']/100.0})
   assert metrics['allocation'][2:]==[220,40],metrics
   assert metrics['origin']==origin and metrics['sensitive']==(state!=2)
   assert metrics['font_description'] and not metrics['font_not_applicable']
   image=folder/(origin+'-'+str(state)+'.png')
   subprocess.run(['import','-window','root',str(image)],check=True,timeout=10)
   screen=Image.open(image).convert('RGB')
   colors=json.loads((folder/'GTK2-NATIVE-COLORS.json').read_text())['colors']
   art=backend.load_builder(ROOT).art
   variant=2 if state==2 else 1 if state==3 else 0
   ox,oy=(host if host else scene.window).get_position()
   expected_fill=art._rgb(colors[art.ROLES['selection'][variant]])
   expected_track=art._rgb(colors[art.ROLES['view'][variant]])
   expected_text=art._rgb(colors[art.ROLES['view-fg'][variant]])
   fill=screen.getpixel((ox+bar_rect.x+8,oy+bar_rect.y+max(3,bar_rect.height//2)));track=screen.getpixel((ox+bar_rect.x+bar_rect.width-6,oy+bar_rect.y+max(3,bar_rect.height//2)))
   text_crop=screen.crop((ox+value_rect.x,oy+value_rect.y,ox+value_rect.x+value_rect.width,oy+value_rect.y+value_rect.height))
   text_matches=sum(1 for pixel in text_crop.getdata() if sum(abs(a-b) for a,b in zip(pixel,expected_text))<36)
   assert fill==expected_fill and track==expected_track,(name,origin,state,fill,expected_fill,track,expected_track)
   assert text_matches>=5,(name,origin,state,expected_text,text_matches)
   rows.append({'scheme':name,'state':state,'fill_rgb':fill,'track_rgb':track,'value_text_rgb':expected_text,'value_text_role_match_pixels':text_matches,'value_above_trough':True,'progressbar_text_inside':False,**metrics})
   scene.window.destroy()
   if host:host.destroy()
   drain()
assert data==original
result={'status':'passed','rows':rows,'scope':'Real GTK2 ProgressBar, 4 palettes, normal/disabled/explicit backdrop, coupled/separate: size, fraction, font and sensitivity. Interior fill/track pixels match effective selection/view roles; not complete pixel/state or historical fidelity approval.','model_unchanged':True}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_scenes':len(rows),'model_unchanged':True}))
