#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GtkButton border pixels and focus/pointer transitions, private HOME."""
import configparser
import ctypes
import json
import os
from pathlib import Path
import sys
import time
from test_arrow_relief_native import module,ROOT,HOME

def worker():
    import gi
    gi.require_version('Gtk','3.0');gi.require_version('GdkX11','3.0')
    from gi.repository import Gtk,Gdk,GdkX11
    from PIL import Image
    backend=module(ROOT/'tools/theme-lab/backend.py','button_backend')
    fixtures=module(ROOT/'tools/theme-lab/tests/test_backend.py','button_fixtures')
    builder=backend.load_builder(ROOT);art=builder.art
    output=Path(HOME)/'results';output.mkdir()
    palette=configparser.ConfigParser(interpolation=None);palette.optionxform=str
    palette.read(ROOT/'colors/DomainOS-SR10.4.colors')
    for section in ('Colors:Window','Colors:Button','Colors:View'):
        palette[section]['BackgroundNormal']='236,216,112';palette[section]['ForegroundNormal']='32,28,12'
    schemes=Path(HOME)/'.local/share/color-schemes';schemes.mkdir(parents=True)
    with (schemes/'TestYellow.colors').open('w') as stream:palette.write(stream)
    assert Gtk.init_check(None)[0]
    settings=Gtk.Settings.get_default();settings.set_property('gtk-enable-animations',False)
    xlib=ctypes.CDLL('libX11.so.6');xtst=ctypes.CDLL('libXtst.so.6')
    xlib.XOpenDisplay.argtypes=[ctypes.c_char_p];xlib.XOpenDisplay.restype=ctypes.c_void_p
    xlib.XFlush.argtypes=[ctypes.c_void_p];xlib.XCloseDisplay.argtypes=[ctypes.c_void_p]
    xlib.XSetInputFocus.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
    xtst.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
    connection=xlib.XOpenDisplay(os.environ['DISPLAY'].encode());assert connection
    records=[]
    def settle():
        for _ in range(6):
            while Gtk.events_pending():Gtk.main_iteration_do(False)
            time.sleep(.004)
    def move(x,y):
        xtst.XTestFakeMotionEvent(connection,-1,x,y,0);xlib.XFlush(connection);settle()
    def press(held):
        xtst.XTestFakeButtonEvent(connection,1,held,0);xlib.XFlush(connection);settle()
    try:
        for scheme in ('DomainOS-SR10.4','BreezeLight','BreezeDark','TestYellow'):
            for state in backend.PART_STATE_IDS:
                for relief in ('flat','raised','sunken'):
                    case=output/(scheme+'-'+state+'-'+relief+'-'+str(len(records)));case.mkdir()
                    data=fixtures.model();data.update(schema_version=2,color_scheme=scheme)
                    recipe=data['recipes']['gtk3'];recipe['selected_control']=12;recipe['selected_scroll_part']=1
                    recipe['scrollbar_parts']={'arrow_button':{'state_relief':{state:relief}}}
                    origin=backend.generate_gtk3(ROOT,case,data,Path(HOME)/'.config/kdeglobals')
                    themes=Path(HOME)/'.local/share/themes';themes.mkdir(exist_ok=True)
                    (themes/origin['theme']).symlink_to(origin['theme_path'],target_is_directory=True)
                    settings.set_property('gtk-theme-name',origin['theme'])
                    colors=json.loads((case/'GTK3-NATIVE-COLORS.json').read_text())['colors']
                    window=Gtk.Window();window.set_default_size(240,140);fixed=Gtk.Fixed();window.add(fixed)
                    button=Gtk.Button();button.get_style_context().add_class('theme-lab-arrow')
                    other=Gtk.Entry();other.set_size_request(90,25)
                    fixed.put(button,30,30);fixed.put(other,90,70);window.show_all();settle()
                    xlib.XSetInputFocus(connection,window.get_window().get_xid(),1,0);xlib.XFlush(connection);settle()
                    window.set_focus(other);move(700,400)
                    baseline=(button.get_allocated_width(),button.get_allocated_height())
                    checks={};details={}
                    def capture(label,expected_state):
                        flags=button.get_state_flags()
                        disabled=bool(flags & Gtk.StateFlags.INSENSITIVE);inactive=bool(flags & Gtk.StateFlags.BACKDROP)
                        active=bool(flags & Gtk.StateFlags.ACTIVE);hover=bool(flags & Gtk.StateFlags.PRELIGHT);focus=bool(flags & Gtk.StateFlags.FOCUSED)
                        actual_state='disabled' if disabled else 'pressed' if active else 'hover' if hover else 'focus' if focus else 'backdrop' if inactive else 'normal'
                        checks[label+':native-state']=actual_state==expected_state
                        checks[label+':geometry']=(button.get_allocated_width(),button.get_allocated_height())==baseline
                        selected=(actual_state==state)
                        effective=relief if selected else 'sunken' if active else 'raised'
                        tokens=('face',)*4 if effective=='flat' else ('light','dark','dark','light') if effective=='raised' else ('dark','light','light','dark')
                        pixbuf=Gdk.pixbuf_get_from_window(window.get_window(),0,0,window.get_allocated_width(),window.get_allocated_height())
                        path=case/(label+'.png');pixbuf.savev(str(path),'png',[],[]);image=Image.open(path).convert('RGB')
                        x,y=button.translate_coordinates(window,0,0);w,h=baseline
                        points=((x+w//2,y),(x+w-1,y+h//2),(x+w//2,y+h-1),(x,y+h//2))
                        differences=[]
                        with backend.recipe_rules(builder,recipe['palette']):
                            for point,token in zip(points,tokens):
                                expected=art._rgb(art.evaluate(art.pixel_plan('button',token,inactive=inactive,disabled=disabled),colors));actual=image.getpixel(point)
                                if max(abs(a-b) for a,b in zip(expected,actual))>1:differences.append({'point':point,'expected':expected,'actual':actual,'token':token})
                        checks[label+':border-pixels']=not differences
                        details[label]={'state':actual_state,'flags':int(flags),'allocation':baseline,'differences':differences,'nodes':button.get_style_context().to_string(Gtk.StyleContextPrintFlags.RECURSE)}
                    capture('normal','normal')
                    wx,wy=window.get_window().get_origin()[1:];x,y=button.translate_coordinates(window,0,0)
                    move(wx+x+baseline[0]//2,wy+y+baseline[1]//2);capture('hover','hover')
                    press(1);capture('pressed','pressed');press(0);move(700,400)
                    button.grab_focus();settle();capture('focus','focus')
                    window.set_focus(other);button.set_sensitive(False);settle();capture('disabled','disabled')
                    button.set_state_flags(Gtk.StateFlags.BACKDROP,False);settle();capture('disabled-backdrop','disabled')
                    button.set_sensitive(True);settle();capture('backdrop','backdrop')
                    button.grab_focus();settle();capture('focus-backdrop','focus')
                    move(wx+x+baseline[0]//2,wy+y+baseline[1]//2);capture('hover-backdrop','hover')
                    press(1);capture('pressed-backdrop','pressed');press(0);move(700,400)
                    window.set_focus(other);button.unset_state_flags(Gtk.StateFlags.BACKDROP);settle();capture('restored','normal')
                    window.destroy();settle()
                    record={'scheme':scheme,'state':state,'relief':relief,'passed':all(checks.values()),'checks':checks,'details':details,'origin':origin}
                    (case/'NATIVE.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
                    print(case.name,sum(checks.values()),'/',len(checks),flush=True)
        result={'passed':all(r['passed'] for r in records),'cases':records,'historical_fidelity_claimed':False,
                'scope':'Actual GtkButton XTest hover/press, native focus routing, sensitivity and controlled BACKDROP; four KDE palettes; outer edge midpoint pixels and allocation',
                'not_verified':['Entire border corners/interior','Glyph pixels','GUI editor','Historical defaults','WM focus policy']}
        (output/'RESULTADO.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
    finally:
        xtst.XTestFakeButtonEvent(connection,1,0,0);xlib.XFlush(connection);xlib.XCloseDisplay(connection)
if __name__=='__main__':
    if '--worker' in sys.argv:raise SystemExit(worker())
    runner=module(ROOT/'tools/theme-lab/tests/test_trough_native.py','button_runner')
    raise SystemExit(runner.main(script=Path(__file__),prefix='.qa-theme-lab-arrow-button-states-'))
