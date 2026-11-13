# SPDX-License-Identifier: GPL-3.0-or-later
"""Native frame foundation; requires an explicitly private X display."""
import os
assert os.environ.get('T04_PRIVATE_FRAME')=='1'
import configparser,copy,json,subprocess,sys,time,io
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT,backend,model
from gtk2_frames import paint_frame,snapshots
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
rows=[]
for name,source in sources.items():
 palette,_=backend.native_roles(ROOT,source,builder.art,backend.sha(source.read_bytes()))
 result=paint_frame(builder,recipe,palette,out/name);Gtk.rc_parse(result['rc'])
 for origin in ('coupled','separate'):
  for variant,index in [('normal',0),('backdrop',1),('disabled',2)]:
   host=Gtk.Window()
   if origin=='coupled':
    socket=Gtk.Socket();host.add(socket);host.show_all();drain();window=Gtk.Plug.new(socket.get_id())
   else:window=host
   prefix={'normal':'themeLabFrame','backdrop':'themeLabBackdropFrame','disabled':'themeLabInsensitiveFrame'}[variant]
   window.set_name(prefix+'Content_'+result['style_id'])
   fixed=Gtk.Fixed();window.add(fixed)
   frame=Gtk.Frame();frame.set_name(prefix+'_'+result['style_id']);frame.set_shadow_type(Gtk.ShadowType.IN)
   assert frame.get_shadow_type()==Gtk.ShadowType.IN
   align=Gtk.Alignment.new(.5,.5,1,1);padding=recipe['geometry']['control_padding_px'];align.set_padding(padding,padding,padding,padding)
   label=Gtk.Label(label='Conteúdo — ação');label.set_name(prefix+'Content_'+result['style_id']);align.add(label);frame.add(align)
   fixed.put(frame,16,16);frame.show_all();natural=Gtk.Requisition();frame.size_request(natural)
   frame.set_size_request(240,120);frame.set_sensitive(index!=2);window.set_default_size(320,200);window.show_all();host.show_all();drain()
   assert frame.get_allocation().width==240 and frame.get_allocation().height==120
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
   window.destroy()
   if window!=host:host.destroy()
   drain()
assert recipe==before
(out/'RESULTADO.json').write_text(json.dumps({'status':'passed','rows':rows,'native_controls':len(rows),'motif_contract':{'widget':'XmFrame','shadow_type':'XmSHADOW_IN','shadow_thickness_px':2,'source':'tools/theme-lab/src/view.c'},'gtk2_shadow_type':'Gtk.ShadowType.IN','scope':'Native GtkFrame/label in two origins/four palettes/three variants. Face and top/bottom bevel layers match the inward symbolic window-role raster. No controller or SR10.4 VM certification.'},ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_controls':len(rows)}))
