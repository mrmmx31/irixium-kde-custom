# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone GtkArrow foundation only, on an explicitly isolated X display."""
import os
assert os.environ.get('T04_PRIVATE_ARROW') == '1'
import configparser
import json
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_arrows import paint_arrow, snapshot_images, DIRECTIONS
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk, GLib, GObject
from sample_contract import SAMPLES
Gtk.init([])
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
builder = backend.load_builder(ROOT)
recipe = model()['recipes']['gtk2']
schemes = {'DomainOS': ROOT/'colors/DomainOS-SR10.4.colors',
           'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
           'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors')}
yellow = configparser.ConfigParser(interpolation=None)
yellow.optionxform = str
yellow.read(schemes['DomainOS'])
yellow['General']['Name'] = 'Artificial yellow test'
for section in ('Colors:Window', 'Colors:Button', 'Colors:View'):
    yellow[section]['BackgroundNormal'] = '236,216,112'
    yellow[section]['ForegroundNormal'] = '32,28,12'
yellow['Colors:Selection']['BackgroundNormal'] = '88,72,24'
yellow['Colors:Selection']['ForegroundNormal'] = '255,248,216'
schemes['TestYellow'] = output/'TestYellow.colors'
with schemes['TestYellow'].open('w') as stream:
    yellow.write(stream)

def drain():
    deadline = time.monotonic() + .15
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(.001)

interaction_only='--interaction-only' in sys.argv
if interaction_only:schemes={'DomainOS':schemes['DomainOS']}
rows=[]
def contains_mask(screen, template, cx, cy):
    template=Image.open(template).convert('RGBA')
    points=[(x,y,tuple(template.getpixel((x,y))[:3])) for y in range(template.height) for x in range(template.width) if template.getpixel((x,y))[3]==255]
    for oy in range(cy-template.height//2-8,cy-template.height//2+9):
        for ox in range(cx-template.width//2-8,cx-template.width//2+9):
            if all(screen.getpixel((ox+x,oy+y))==rgb for x,y,rgb in points):return True
    return False
for name,source in schemes.items():
    palette,origin=backend.native_roles(ROOT,source,builder.art,backend.sha(source.read_bytes()))
    folder=output/name
    with backend.recipe_rules(builder,recipe['palette']):
        generated=paint_arrow(builder,recipe,palette,folder)
        images=snapshot_images(builder,recipe,palette)
    Gtk.rc_parse(generated['rc'])
    for coupled in (False,True):
        for variant,index,prefix in (('normal',0,'themeLabArrow'),('backdrop',1,'themeLabBackdropArrow'),('disabled',2,'themeLabInsensitiveArrow')):
            if interaction_only and index==2:continue
            host=Gtk.Window()
            if coupled:
                socket=Gtk.Socket();host.add(socket);host.show_all();drain();window=Gtk.Plug.new(socket.get_id())
            else:window=host
            fixed=Gtk.Fixed();window.add(fixed)
            buttons=[];clicks=[]
            for i,direction in enumerate(DIRECTIONS):
                button=Gtk.Button()
                button.set_name(prefix+'_'+generated['style_id'])
                arrow=Gtk.Arrow(arrow_type=getattr(Gtk.ArrowType,direction.upper()),shadow_type=Gtk.ShadowType.OUT)
                arrow.set_size_request(recipe['geometry']['arrow_px'],recipe['geometry']['arrow_px'])
                button.add(arrow);button.set_size_request(64,48);button.set_sensitive(index!=2)
                button.connect('clicked',lambda _w,d=direction:clicks.append(d))
                fixed.put(button,16+i*80,16);buttons.append(button)
            window.show_all();drain();ox,oy=host.get_position()
            png=folder/('%s-%s.png'%('coupled' if coupled else 'separate',variant))
            subprocess.run(['import','-window','root',str(png)],check=True,timeout=10)
            screen=Image.open(png).convert('RGB')
            for i,(direction,button) in enumerate(zip(DIRECTIONS,buttons)):
                allocation=button.get_allocation()
                assert [allocation.width,allocation.height]==[64,48]
                assert button.get_sensitive()==(index!=2)
                pixel=screen.getpixel((ox+24+i*80,oy+40))
                expected=builder.art._rgb(palette[builder.art.ROLES['button'][index]])
                assert pixel==expected,(name,coupled,variant,direction,pixel,expected)
                assert contains_mask(screen,folder/images[variant,'idle',direction][0],ox+48+i*80,oy+40),(name,coupled,variant,direction)
                rows.append(dict(scheme=name,variant=variant,coupled=coupled,direction=direction,pixel=pixel,mask_matched=True,style_id=generated['style_id']))
            if name=='DomainOS' and index in (0,1):
                host.set_title('T04 private isolated arrows');drain()
                subprocess.run(['xdotool','search','--name','^T04 private isolated arrows$','windowfocus'],check=True,timeout=5)
                for i,direction in enumerate(DIRECTIONS):
                    subprocess.run(['xdotool','mousemove',str(ox+48+i*80),str(oy+40),'mousedown','1'],check=True,timeout=5);drain()
                    pressed=folder/('pressed-%s-%s-%s.png'%('coupled' if coupled else 'separate',variant,direction))
                    subprocess.run(['import','-window','root',str(pressed)],check=True,timeout=10)
                    pic=Image.open(pressed).convert('RGB')
                    assert contains_mask(pic,folder/images[variant,'pressed',direction][0],ox+48+i*80,oy+40),('pressed',coupled,direction)
                    subprocess.run(['xdotool','mouseup','1'],check=True,timeout=5);drain()
                    assert clicks[-1]==direction
                    released=folder/('released-%s-%s-%s.png'%('coupled' if coupled else 'separate',variant,direction))
                    subprocess.run(['import','-window','root',str(released)],check=True,timeout=10)
                    pic=Image.open(released).convert('RGB')
                    assert contains_mask(pic,folder/images[variant,'idle',direction][0],ox+48+i*80,oy+40),('released',variant,coupled,direction)
                buttons[0].grab_focus();drain();before=len(clicks)
                subprocess.run(['xdotool','key','--clearmodifiers','space'],check=True,timeout=5);drain()
                assert len(clicks)==before+1 and clicks[-1]=='up'
            if index==2:
                subprocess.run(['xdotool','mousemove',str(ox+48),str(oy+40),'click','1'],check=True,timeout=5);drain()
                assert not clicks
            window.destroy()
            if coupled:host.destroy()
            drain()
result={'status':'passed','rows':rows,'interaction_only':interaction_only,'scope':'GTK2 standalone arrow button foundation:96 directional controls, four schemes, three variants, two origins. Real mask matching for glyph colors/shape, face pixels, allocation and sensitivity. DomainOS normal/backdrop:four pressed glyphs/released glyphs/clicks and Space activation; insensitive blocks click. Not scene/controller integration or historical approval.'}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_controls':len(rows)}))
