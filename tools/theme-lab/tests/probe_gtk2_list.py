# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone list foundation; only run in a private display/namespace."""
import os
assert os.environ.get('T04_PRIVATE_LIST')=='1'
import configparser,copy,json,subprocess,sys,time
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT,backend,model
from gtk2_lists import paint_list
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
rows=[]
for name,source in sources.items():
 palette,_=backend.native_roles(ROOT,source,builder.art,backend.sha(source.read_bytes()))
 result=paint_list(builder,recipe,palette,out/name);Gtk.rc_parse(result['rc'])
 for origin in ('coupled','separate'):
  for variant,index in [('normal',0),('backdrop',1),('disabled',2)]:
   host=Gtk.Window();host.set_title('T04 private list')
   if origin=='coupled':
    socket=Gtk.Socket();host.add(socket);host.show_all();drain();window=Gtk.Plug.new(socket.get_id())
   else:window=host
   fixed=Gtk.Fixed();window.add(fixed)
   prefix={'normal':'themeLabList','backdrop':'themeLabBackdropList','disabled':'themeLabInsensitiveList'}[variant]
   scroll=Gtk.ScrolledWindow();scroll.set_name(prefix+'Enclosure_'+result['style_id']);scroll.set_shadow_type(Gtk.ShadowType.IN)
   scroll.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
   store=Gtk.ListStore(str)
   for text in ('Ação normal','Selecionado — ç','Outro item'):store.append([text])
   tree=Gtk.TreeView(model=store);tree.set_name(prefix+'View_'+result['style_id']);tree.set_headers_visible(False)
   renderer=Gtk.CellRendererText();column=Gtk.TreeViewColumn('Item',renderer,text=0);tree.append_column(column)
   tree.get_selection().select_path(Gtk.TreePath.new_from_string('1'))
   scroll.add(tree);fixed.put(scroll,16,16);tree.show_all();scroll.show_all();drain()
   minimum=Gtk.Requisition();scroll.size_request(minimum);scroll.set_size_request(320,180);scroll.set_sensitive(index!=2);tree.set_sensitive(index!=2)
   window.set_default_size(400,260);window.show_all();host.show_all();drain()
   assert scroll.get_allocation().width==320 and scroll.get_allocation().height==180
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
   if variant=='normal':
    tree.grab_focus();drain()
    subprocess.run(['xdotool','search','--name','^T04 private list$','windowfocus'],check=True,timeout=5)
    subprocess.run(['xdotool','key','--clearmodifiers','Down'],check=True,timeout=5);drain()
    selected_model,it=tree.get_selection().get_selected();assert selected_model.get_value(it,0)=='Outro item'
    for i in range(40):store.append(['Linha extensa '+str(i)+' — '+'abcdef '*30])
    drain();assert scroll.get_vadjustment().get_upper()>scroll.get_vadjustment().get_page_size()
    assert scroll.get_hadjustment().get_upper()>scroll.get_hadjustment().get_page_size()
    scroll.get_vadjustment().set_value(40);drain();assert scroll.get_vadjustment().get_value()>0
   subprocess.run(['import','-window','root',str(out/name/(origin+'-'+variant+'.png'))],check=True,timeout=10)
   rows.append({'scheme':name,'origin':origin,'variant':variant,'allocation':[320,180],'natural_request':[minimum.width,minimum.height],'view_rgb':expected,'selection_rgb':expected_selection})
   window.destroy()
   if window!=host:host.destroy()
   drain()
assert recipe==before
(out/'RESULTADO.json').write_text(json.dumps({'status':'passed','rows':rows,'native_controls':len(rows),'scope':'Standalone GtkTreeView/GtkScrolledWindow: native allocation, selection keyboard and two-axis scrolling, effective KDE style roles. Not integrated scene/controller or full pixel/historical proof.'},ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_controls':len(rows)}))
