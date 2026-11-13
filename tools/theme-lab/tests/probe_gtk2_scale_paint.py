# SPDX-License-Identifier: GPL-3.0-or-later
"""GtkScale foundation only, on an explicitly isolated X display."""
import os
assert os.environ.get('T04_PRIVATE_SCALE') == '1'
import configparser
import json
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_scales import paint_scale
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

rows = []
for name, source in schemes.items():
    palette, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
    folder = output/name
    with backend.recipe_rules(builder, recipe['palette']):
        generated = paint_scale(builder, recipe, palette, folder)
    Gtk.rc_parse(generated['rc'])
    for coupled in (False, True):
        for variant, index, prefix in (('normal',0,'themeLabScale'),('backdrop',1,'themeLabBackdropScale'),('disabled',2,'themeLabInsensitiveScale')):
            for vertical in (False, True):
                host = Gtk.Window()
                if coupled:
                    socket = Gtk.Socket();host.add(socket);host.show_all();drain()
                    window = Gtk.Plug.new(socket.get_id())
                else:
                    window = host
                fixed = Gtk.Fixed();window.add(fixed)
                scale = Gtk.VScale.new_with_range(0,100,1) if vertical else Gtk.HScale.new_with_range(0,100,1)
                scale.set_name(prefix+'_'+generated['style_id'])
                scale.set_draw_value(True)
                scale.set_value(SAMPLES['scale_v' if vertical else 'scale_h'])
                scale.set_sensitive(index != 2)
                size = [44,260] if vertical else [260,44]
                scale.set_size_request(*size);fixed.put(scale,16,16)
                window.show_all();drain()
                allocation=scale.get_allocation()
                assert [allocation.width,allocation.height]==size
                assert scale.get_sensitive()==(index != 2)
                assert scale.get_draw_value() is True
                spec=scale.find_style_property('slider-width');value=GObject.Value();value.init(spec.value_type)
                scale.style_get_property('slider-width',value)
                assert value.get_value()==8
                spec=scale.find_style_property('slider-length');value=GObject.Value();value.init(spec.value_type)
                scale.style_get_property('slider-length',value)
                assert value.get_value()==27
                x,y=host.get_position()
                png=folder/('%s-%s-%s.png'%('coupled' if coupled else 'separate',variant,'vertical' if vertical else 'horizontal'))
                subprocess.run(['import','-window','root',str(png)],check=True,timeout=10)
                screen=Image.open(png).convert('RGB')
                # The value label moves the trough inside the widget allocation.
                # Confirm the expected KDE face is painted in this control's own ROI.
                expected=builder.art._rgb(palette[builder.art.ROLES['button'][index]])
                left=x+allocation.x;top=y+allocation.y
                roi=screen.crop((left,top,left+allocation.width,top+allocation.height))
                role_pixels=sum(1 for pixel in roi.getdata() if pixel==expected)
                assert role_pixels>0,(name,coupled,variant,vertical,role_pixels,expected)
                native_input=None
                if name=='DomainOS' and index==0:
                    host.set_title('T04 private scale');drain()
                    subprocess.run(['xdotool','search','--name','^T04 private scale$','windowfocus'],check=True,timeout=5)
                    scale.grab_focus();drain();before=scale.get_value()
                    subprocess.run(['xdotool','key','--clearmodifiers','Up' if vertical else 'Right'],check=True,timeout=5);drain()
                    assert scale.get_value()==before+(-1 if vertical else 1),(vertical,before,scale.get_value())
                    subprocess.run(['xdotool','key','--clearmodifiers','End'],check=True,timeout=5);drain()
                    assert scale.get_value()==100
                    subprocess.run(['xdotool','key','--clearmodifiers','Home'],check=True,timeout=5);drain()
                    assert scale.get_value()==0
                    native_input={'step':True,'home_end':True}
                rows.append(dict(scheme=name,coupled=coupled,variant=variant,vertical=vertical,size=size,
                                 role_pixel_count=role_pixels,native_input=native_input,
                                 style_id=generated['style_id'],origin=origin))
                window.destroy()
                if coupled:host.destroy()
                drain()
result={'status':'passed','rows':rows,'scope':'Native GTK2 scale foundation; role face pixel, geometry, sensitivity, keyboard stepping and endpoints. Not scene/controller integration, complete pixel/state proof or historical approval.'}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','native_scenes':len(rows)}))
