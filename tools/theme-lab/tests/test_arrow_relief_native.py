#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real GTK3 stepper pixels and XTest press/release; isolated disposable HOME.
Proves proposed state translation, never SR10.4 historical defaults.
"""
import configparser
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[3]
HOME='/home/domainos-test'
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def worker(states=('normal','pressed'),hover_backdrop=False):
    import gi
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk,Gdk
    from PIL import Image
    backend=module(ROOT/'tools/theme-lab/backend.py','arrow_backend')
    fixtures=module(ROOT/'tools/theme-lab/tests/test_backend.py','arrow_fixtures')
    builder=backend.load_builder(ROOT);art=builder.art
    reader=module(ROOT/'tools/theme-lab/native_parts_gtk.py','arrow_parts').Reader(Gtk)
    assert reader.available
    output=Path(HOME)/'results';output.mkdir()
    palette=configparser.ConfigParser(interpolation=None);palette.optionxform=str
    palette.read(ROOT/'colors/DomainOS-SR10.4.colors')
    palette['General']['Name']='Artificial yellow fixture'
    for section in ('Colors:Window','Colors:Button','Colors:View'):
        palette[section]['BackgroundNormal']='236,216,112'
        palette[section]['ForegroundNormal']='32,28,12'
    schemes=Path(HOME)/'.local/share/color-schemes';schemes.mkdir(parents=True)
    with (schemes/'TestYellow.colors').open('w') as stream:palette.write(stream)
    assert Gtk.init_check(None)[0]
    settings=Gtk.Settings.get_default();settings.set_property('gtk-enable-animations',False)
    xlib=ctypes.CDLL('libX11.so.6');xtst=ctypes.CDLL('libXtst.so.6')
    xlib.XOpenDisplay.argtypes=[ctypes.c_char_p];xlib.XOpenDisplay.restype=ctypes.c_void_p
    xlib.XFlush.argtypes=[ctypes.c_void_p];xlib.XCloseDisplay.argtypes=[ctypes.c_void_p]
    xtst.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
    connection=xlib.XOpenDisplay(os.environ['DISPLAY'].encode());assert connection
    records=[]
    def settle():
        for _ in range(12):
            while Gtk.events_pending():Gtk.main_iteration_do(False)
            time.sleep(.005)
    def move(x,y):
        xtst.XTestFakeMotionEvent(connection,-1,x,y,0);xlib.XFlush(connection);settle()
    def button(held):
        xtst.XTestFakeButtonEvent(connection,1,held,0);xlib.XFlush(connection);settle()
    try:
        for scheme in ('DomainOS-SR10.4','BreezeLight','BreezeDark','TestYellow'):
            for state in states:
                for relief in ('flat','raised','sunken'):
                    case=output/(scheme+'-'+state+'-'+relief+'-'+str(len(records)));case.mkdir()
                    data=fixtures.model();data.update(schema_version=2,color_scheme=scheme)
                    recipe=data['recipes']['gtk3'];recipe['scrollbar_parts']={'arrow':{'state_relief':{state:relief}}}
                    origin=backend.generate_gtk3(ROOT,case,data,Path(HOME)/'.config/kdeglobals')
                    themes=Path(HOME)/'.local/share/themes';themes.mkdir(exist_ok=True)
                    (themes/origin['theme']).symlink_to(origin['theme_path'],target_is_directory=True)
                    colors=json.loads((case/'GTK3-NATIVE-COLORS.json').read_text())['colors']
                    settings.set_property('gtk-theme-name',origin['theme'])
                    window=Gtk.Window();window.set_default_size(460,300)
                    fixed=Gtk.Fixed();window.add(fixed)
                    h=Gtk.Scrollbar(orientation=Gtk.Orientation.HORIZONTAL,adjustment=Gtk.Adjustment(40,0,100,1,10,20))
                    v=Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL,adjustment=Gtk.Adjustment(40,0,100,1,10,20))
                    h.set_size_request(300,-1);v.set_size_request(-1,220)
                    fixed.put(h,20,20);fixed.put(v,360,20);window.show_all();move(700,400)
                    targets=[(h,'arrow_first','left'),(h,'arrow_last','right'),(v,'arrow_first','up'),(v,'arrow_last','down')]
                    checks={};details={};nodes={}
                    def capture(label,active=None,hover=None,disabled=False,inactive=False):
                        shot=Gdk.pixbuf_get_from_window(window.get_window(),0,0,window.get_allocated_width(),window.get_allocated_height())
                        path=case/(label+'.png');shot.savev(str(path),'png',[],[]);image=Image.open(path).convert('RGB')
                        for bar,piece,direction in targets:
                            name=label+':'+direction;measured=reader.measure(bar);assert measured,(name,'missing measured pieces')
                            box=measured[piece];px,py=bar.translate_coordinates(window,0,0)
                            size=recipe['geometry']['arrow_px']
                            # Margin box includes the arrow/track interval on the inner side.
                            horizontal=bar.get_orientation()==Gtk.Orientation.HORIZONTAL
                            gap=recipe['geometry']['arrow_thumb_gap_px']
                            gx=px+box['x']+(gap if horizontal and piece=='arrow_last' else 0)
                            gy=py+box['y']+(gap if not horizontal and piece=='arrow_last' else 0)
                            is_active=active==direction;is_hover=hover==direction
                            native=bar.get_style_context().to_string(Gtk.StyleContextPrintFlags.RECURSE);nodes[name]=native
                            line=[line for line in native.splitlines() if line.strip().startswith('button.'+('up' if piece=='arrow_first' else 'down')+':')]
                            if is_active:checks[name+':native-active']=len(line)==1 and ':active' in line[0]
                            if disabled:checks[name+':native-disabled']=len(line)==1 and ':disabled' in line[0]
                            if inactive:checks[name+':native-backdrop']=':backdrop' in native
                            mode='disabled' if disabled else 'pressed' if is_active else 'normal'
                            mask=builder.gtk3_arrow(mode,direction,geometry=recipe['geometry'])
                            # Normal override intentionally excludes hover/focus; pressed is native active.
                            applied=((state=='pressed' and is_active) or
                                     (state=='normal' and not disabled and not inactive and not is_active and not is_hover) or
                                     (state=='disabled' and disabled) or
                                     (state=='backdrop' and inactive and not disabled and not is_active and not is_hover) or
                                     (state=='hover' and is_hover and not is_active and not disabled))
                            if applied:
                                mask=builder.gtk3_arrow('normal',direction,geometry=recipe['geometry'])
                                mask=[[('face' if relief=='flat' and token else
                                        {'light':'dark','dark':'light'}.get(token,token) if relief=='sunken' else token)
                                       for token in row] for row in mask]
                            differences=[]
                            with backend.recipe_rules(builder,recipe['palette']):
                                for y,row in enumerate(mask):
                                    for x,token in enumerate(row):
                                        expected=art._rgb(art.evaluate(art.pixel_plan('button',token or 'trough',inactive=inactive,disabled=disabled),colors))
                                        actual=image.getpixel((gx+x,gy+y))
                                        if max(abs(a-b) for a,b in zip(expected,actual))>1:
                                            differences.append({'x':x,'y':y,'token':token,'expected':expected,'actual':actual})
                            checks[name+':pixels']=not differences
                            checks[name+':allocation']= (box['width'],box['height'])==((size+gap,size) if horizontal else (size,size+gap))
                            details[name]={'box':box,'glyph_origin':[gx,gy],'differences':differences[:16],'mismatch_count':len(differences)}
                    capture('normal')
                    if hover_backdrop:
                        for current in (h,v):current.set_state_flags(Gtk.StateFlags.BACKDROP,False)
                        settle();capture('backdrop',inactive=True)
                        for bar,piece,direction in targets:
                            box=reader.measure(bar)[piece];px,py=bar.translate_coordinates(window,box['x']+box['width']//2,box['y']+box['height']//2)
                            wx,wy=window.get_window().get_origin()[1:];move(wx+px,wy+py)
                            capture('hover-backdrop-'+direction,hover=direction,inactive=True)
                            button(1);capture('pressed-backdrop-'+direction,active=direction,hover=direction,inactive=True)
                            button(0);move(700,400)
                            for current in (h,v):current.get_adjustment().set_value(40)
                            settle()
                        for current in (h,v):current.unset_state_flags(Gtk.StateFlags.BACKDROP)
                        settle();capture('restored')
                        window.destroy();settle()
                        record={'scheme':scheme,'state':state,'relief':relief,'checks':checks,'passed':all(checks.values()),'details':details,'native_nodes':nodes,'origin':origin,
                                'input':'Real XTest hover/press with controlled BACKDROP flag'}
                        (case/'NATIVE.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
                        print(case.name,sum(checks.values()),'/',len(checks),flush=True)
                        continue
                    if state in ('disabled','backdrop'):
                        for current in (h,v):current.set_sensitive(False)
                        settle();capture('disabled',disabled=True)
                        for current in (h,v):current.set_state_flags(Gtk.StateFlags.BACKDROP,False)
                        settle();capture('disabled-backdrop',disabled=True,inactive=True)
                        for current in (h,v):current.set_sensitive(True)
                        settle();capture('backdrop',inactive=True)
                        for current in (h,v):current.unset_state_flags(Gtk.StateFlags.BACKDROP)
                        settle();capture('restored')
                        window.destroy();settle()
                        record={'scheme':scheme,'state':state,'relief':relief,'checks':checks,'passed':all(checks.values()),'details':details,'native_nodes':nodes,'origin':origin,
                                'input':'Native sensitivity API; controlled BACKDROP flag (no window-manager focus claim)'}
                        (case/'NATIVE.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
                        print(case.name,sum(checks.values()),'/',len(checks),flush=True)
                        continue
                    for bar,piece,direction in targets:
                        box=reader.measure(bar)[piece];px,py=bar.translate_coordinates(window,box['x']+box['width']//2,box['y']+box['height']//2)
                        wx,wy=window.get_window().get_origin()[1:];move(wx+px,wy+py)
                        capture('hover-'+direction,hover=direction)
                        button(1);capture('pressed-'+direction,active=direction,hover=direction)
                        button(0);capture('released-'+direction,hover=direction)
                        move(700,400)
                        for current in (h,v):current.get_adjustment().set_value(40)
                        settle();capture('restored-'+direction)
                    window.destroy();settle()
                    record={'scheme':scheme,'state':state,'relief':relief,'checks':checks,'passed':all(checks.values()),'details':details,'native_nodes':nodes,'origin':origin}
                    (case/'NATIVE.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
                    print(case.name,sum(checks.values()),'/',len(checks),flush=True)
        result={'passed':all(r['passed'] for r in records),'cases':records,'historical_fidelity_claimed':False,
                'scope':'Real GTK3 scrollbar arrow pixels, four directions, proposed overrides '+str(states)+', transitions/restoration, four KDE schemes; isolated HOME',
                'not_verified':['GUI editor','Standalone GtkButton arrow','Historical disabled/backdrop defaults','Other piece/state translation']}
        (output/'RESULTADO.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
    finally:
        xtst.XTestFakeButtonEvent(connection,1,0,0);xlib.XFlush(connection);xlib.XCloseDisplay(connection)
if __name__=='__main__':
    if '--worker' in sys.argv:raise SystemExit(worker())
    runner=module(ROOT/'tools/theme-lab/tests/test_trough_native.py','arrow_runner')
    raise SystemExit(runner.main(script=Path(__file__),prefix='.qa-theme-lab-arrow-relief-'))
