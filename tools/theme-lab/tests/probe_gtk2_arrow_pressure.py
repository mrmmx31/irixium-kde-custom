#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private foundation: demonstrate pressure versus physical GtkButton/GtkArrow.

No product capability is enabled. Focus is excluded from this pixel comparison.
"""
import configparser
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image, ImageChops

if os.environ.get('T04_PRIVATE_ARROW_PRESSURE') != '1':
    raise SystemExit('Requires the private arrow pressure fixture.')
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/theme-lab'))
from test_backend import backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_press_bridge import Gtk2PressBridge
from gtk2_pressed_state import PressedButtonDemo
import gi
gi.require_version('Gtk','2.0');gi.require_version('Gdk','2.0')
from gi.repository import Gtk, Gdk


def settle():
    deadline=time.monotonic()+.15
    while time.monotonic()<deadline:
        while Gtk.events_pending():Gtk.main_iteration_do(False)
        time.sleep(.002)


def pointer(*args):
    subprocess.run(['xdotool',*map(str,args)],check=True,timeout=5)
    settle()


def capture(button,path):
    # This foundation uses a top-level GtkWindow, never a GtkPlug.
    ox,oy=button.get_toplevel().get_position()
    box=button.get_allocation()
    raw=subprocess.check_output(['import','-window','root','png:-'],timeout=5)
    result=Image.open(io.BytesIO(raw)).convert('RGB').crop((ox+box.x,oy+box.y,ox+box.x+box.width,oy+box.y+box.height))
    result.save(path)
    return result


def main():
    output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,mode=0o700)
    Gtk.init([])
    schemes={'DomainOS':ROOT/'colors/DomainOS-SR10.4.colors',
             'BreezeLight':Path('/usr/share/color-schemes/BreezeLight.colors'),
             'BreezeDark':Path('/usr/share/color-schemes/BreezeDark.colors')}
    yellow=configparser.ConfigParser(interpolation=None);yellow.optionxform=str;yellow.read(schemes['DomainOS'])
    yellow['General']['Name']='Artificial yellow test'
    for section in ('Colors:Window','Colors:Button','Colors:View'):
        yellow[section]['BackgroundNormal']='236,216,112';yellow[section]['ForegroundNormal']='32,28,12'
    yellow['Colors:Selection']['BackgroundNormal']='88,72,24';yellow['Colors:Selection']['ForegroundNormal']='255,248,216'
    schemes['TestYellow']=output/'TestYellow.colors'
    with schemes['TestYellow'].open('w') as f:yellow.write(f)
    bridge=Gtk2PressBridge(ROOT);rows=[]
    for scheme,source in schemes.items():
        folder=output/scheme;data=model();data['selected_family']='gtk2';recipe=data['recipes']['gtk2']
        recipe.update(visible_controls=1<<12,selected_control=12,edit_state=0)
        receipt=generate_scrollbar_snapshot(backend,ROOT,folder,data,source)
        Gtk.rc_parse(str(receipt['rc']))
        for direction in ('up','down','left','right'):
            window=Gtk.Window();window.set_title('T04 private arrow pressure');window.set_default_size(240,140)
            button=Gtk.Button();button.set_name('themeLabArrow_'+receipt['arrow_style_id']);button.set_can_focus(False)
            arrow=Gtk.Arrow(arrow_type=getattr(Gtk.ArrowType,direction.upper()),shadow_type=Gtk.ShadowType.OUT)
            arrow.set_size_request(recipe['geometry']['arrow_px'],recipe['geometry']['arrow_px']);button.add(arrow)
            button.set_size_request(96,64);fixed=Gtk.Fixed();fixed.put(button,32,32);window.add(fixed)
            clicks=[];button.connect('clicked',lambda *_:clicks.append(True));window.show_all();settle()
            pointer('mousemove',700,500)
            normal=capture(button,folder/(direction+'-normal.png'))
            flags=lambda:bridge.flags(bridge.capsule(button.__gpointer__,None))
            assert flags()==0
            demo=PressedButtonDemo(button,bridge.bind(button));settle()
            assert flags()==0 and not clicks
            forced_states=[int(button.get_state()),int(arrow.get_state())]
            forced=capture(button,folder/(direction+'-forced.png'))
            # Crossings must not cancel the visual demonstration or activate.
            pointer('mousemove',80,60);pointer('mousemove',700,500)
            assert [int(button.get_state()),int(arrow.get_state())]==forced_states
            assert not clicks
            demo.close();settle()
            reset=capture(button,folder/(direction+'-reset.png'))
            assert ImageChops.difference(normal,reset).getbbox() is None
            assert flags()==0
            pointer('mousemove',80,60,'mousedown',1)
            actual_states=[int(button.get_state()),int(arrow.get_state())]
            physical=capture(button,folder/(direction+'-physical.png'))
            try:
                assert actual_states==forced_states, (scheme,direction,forced_states,actual_states)
                difference=ImageChops.difference(forced,physical)
                assert difference.getbbox() is None,(scheme,direction,difference.getbbox())
                assert not clicks
            finally:pointer('mouseup',1)
            assert len(clicks)==1
            pointer('mousemove',700,500)
            assert flags()==0
            assert ImageChops.difference(normal,capture(button,folder/(direction+'-released.png'))).getbbox() is None
            rows.append({'scheme':scheme,'direction':direction,'forced_states':forced_states,
                         'physical_states':actual_states,'pixels_equal':True,'reset_equal':True,
                         'artificial_clicks':0,'physical_clicks':1,'native_input_flags_restored':True})
            window.destroy();settle()
    result={'status':'passed_scoped_foundation','rows':rows,'product_capability_enabled':False,
            'focus_comparison_excluded':True,'historical_fidelity_claimed':False}
    (output/'RESULTADO.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Arrow pressure foundation:',len(rows),'scheme/direction cases passed',flush=True)


if __name__=='__main__':main()
