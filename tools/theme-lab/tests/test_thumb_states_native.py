#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native movable slider states; complete thumb pixels and enclosing frames."""
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
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk,Gdk
    from PIL import Image
    backend=module(ROOT/'tools/theme-lab/backend.py','trough_state_backend')
    fixtures=module(ROOT/'tools/theme-lab/tests/test_backend.py','trough_state_fixtures')
    builder=backend.load_builder(ROOT);art=builder.art
    reader=module(ROOT/'tools/theme-lab/native_parts_gtk.py','thumb_parts').Reader(Gtk)
    output=Path(HOME)/'results';output.mkdir()
    palette=configparser.ConfigParser(interpolation=None);palette.optionxform=str
    palette.read(ROOT/'colors/DomainOS-SR10.4.colors')
    for section in ('Colors:Window','Colors:Button','Colors:View'):
        palette[section]['BackgroundNormal']='236,216,112';palette[section]['ForegroundNormal']='32,28,12'
    schemes=Path(HOME)/'.local/share/color-schemes';schemes.mkdir(parents=True)
    with (schemes/'TestYellow.colors').open('w') as stream:palette.write(stream)
    assert Gtk.init_check(None)[0]
    settings=Gtk.Settings.get_default();settings.set_property('gtk-enable-animations',False)
    settings.set_property('gtk-primary-button-warps-slider',False)
    xlib=ctypes.CDLL('libX11.so.6');xtst=ctypes.CDLL('libXtst.so.6')
    xlib.XOpenDisplay.argtypes=[ctypes.c_char_p];xlib.XOpenDisplay.restype=ctypes.c_void_p
    xlib.XFlush.argtypes=[ctypes.c_void_p];xlib.XCloseDisplay.argtypes=[ctypes.c_void_p]
    xtst.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
    connection=xlib.XOpenDisplay(os.environ['DISPLAY'].encode());assert connection
    records=[]
    if '--resume-relative' in sys.argv:
        relative=Path(sys.argv[sys.argv.index('--resume-relative')+1])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Private relative fixture path required')
        previous=ROOT/relative
        for path in sorted(previous.glob('*/NATIVE.json')):
            record=json.loads(path.read_text())
            if not record['passed'] or not record['checks'] or not all(record['checks'].values()):
                raise ValueError('Cannot reuse failing or incomplete case: '+str(path))
            record['proof_source']=str(path.relative_to(ROOT));record['reused']=True
            records.append(record)
    completed={(r['scheme'],r['state'],r['relief']) for r in records}
    if len(completed)!=len(records):raise ValueError('Duplicate prior cases')
    case_index=0
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
            for state in ('normal','pressed','disabled','backdrop','hover'):
                for relief in ('flat','raised','sunken'):
                    index=case_index;case_index+=1
                    if (scheme,state,relief) in completed:continue
                    case=output/(scheme+'-'+state+'-'+relief+'-'+str(index));case.mkdir()
                    data=fixtures.model();data.update(schema_version=2,color_scheme=scheme)
                    recipe=data['recipes']['gtk3'];recipe['scrollbar_parts']={'thumb':{'state_relief':{state:relief}}}
                    origin=backend.generate_gtk3(ROOT,case,data,Path(HOME)/'.config/kdeglobals')
                    themes=Path(HOME)/'.local/share/themes';themes.mkdir(exist_ok=True)
                    (themes/origin['theme']).symlink_to(origin['theme_path'],target_is_directory=True)
                    settings.set_property('gtk-theme-name',origin['theme'])
                    colors=json.loads((case/'GTK3-NATIVE-COLORS.json').read_text())['colors']
                    window=Gtk.Window();window.set_default_size(440,280)
                    scroll=Gtk.ScrolledWindow();scroll.set_overlay_scrolling(False)
                    scroll.set_policy(Gtk.PolicyType.ALWAYS,Gtk.PolicyType.ALWAYS)
                    content=Gtk.DrawingArea();content.set_size_request(900,650);scroll.add(content)
                    window.add(scroll);window.show_all();settle()
                    bars={'horizontal':scroll.get_hscrollbar(),'vertical':scroll.get_vscrollbar()}
                    viewport=scroll.get_child();checks={};details={};pixels=0
                    baseline={name:(bar.get_allocated_width(),bar.get_allocated_height()) for name,bar in bars.items()}
                    for phase in ('normal','hover-h','pressed-h','released-h','hover-v','pressed-v','released-v','backdrop','hover-backdrop','pressed-backdrop','disabled','disabled-backdrop','restored'):
                        # Release before sensitivity changes or moving the pointer;
                        # otherwise a held drag changes the sampled geometry.
                        if not phase.startswith('pressed'):press(0)
                        disabled=phase.startswith('disabled');backdrop='backdrop' in phase
                        scroll.set_sensitive(not disabled)
                        for bar in (*bars.values(),viewport):
                            bar.unset_state_flags(Gtk.StateFlags.BACKDROP)
                            if backdrop:bar.set_state_flags(Gtk.StateFlags.BACKDROP,False)
                        for adjustment in (scroll.get_hadjustment(),scroll.get_vadjustment()):
                            adjustment.set_value((adjustment.get_upper()-adjustment.get_page_size())/2)
                        move(700,400)
                        target_name='horizontal' if phase.endswith('-h') else 'vertical'
                        if phase.startswith(('hover','pressed','released')):
                            bar=bars[target_name];start,end=bar.get_slider_range();target=(start+end)//2
                            x,y=bar.translate_coordinates(window,target if target_name=='horizontal' else bar.get_allocated_width()//2,
                                bar.get_allocated_height()//2 if target_name=='horizontal' else target)
                            wx,wy=window.get_window().get_origin()[1:];move(wx+x,wy+y)
                        if phase.startswith('pressed'):press(1)
                        settle()
                        shot=Gdk.pixbuf_get_from_window(window.get_window(),0,0,440,280)
                        path=case/(phase+'.png');shot.savev(str(path),'png',[],[]);image=Image.open(path).convert('RGB')
                        effective_state='disabled' if disabled else 'backdrop' if backdrop else 'normal'
                        effective='sunken'
                        for name,bar in (*bars.items(),('viewport',viewport)):
                            width,height=bar.get_allocated_width(),bar.get_allocated_height()
                            x,y=bar.translate_coordinates(window,0,0)
                            frame=art.bevel(art.blank(width,height),thickness=2,down=effective=='sunken' if name!='viewport' else True)
                            differences=[]
                            with backend.recipe_rules(builder,recipe['palette']):
                                expected_frame={token:art._rgb(art.evaluate(art.pixel_plan('view' if name=='viewport' else 'button',token,inactive=backdrop,disabled=disabled),colors)) for token in ('face','light','dark')}
                                for py,row in enumerate(frame):
                                    for px,token in enumerate(row):
                                        if token is None:continue
                                        if name!='viewport' and effective=='flat':token='face'
                                        expected=expected_frame[token]
                                        actual=image.getpixel((x+px,y+py));pixels+=1
                                        if max(abs(a-b) for a,b in zip(actual,expected))>1:differences.append({'point':[x+px,y+py],'expected':expected,'actual':actual})
                            checks[phase+':'+name+':frame']=not differences
                            if name!='viewport':
                                checks[phase+':'+name+':allocation']=(width,height)==baseline[name]
                                nodes=bar.get_style_context().to_string(Gtk.StyleContextPrintFlags.RECURSE)
                                contents=[line for line in nodes.splitlines() if line.strip().startswith('contents')]
                                checks[phase+':'+name+':contents-state']=len(contents)==1 and ':active' not in contents[0] and ':hover' not in contents[0]
                                slider=[line for line in nodes.splitlines() if line.strip().startswith('slider')]
                                assert len(slider)==1
                                active=':active' in slider[0];hover=':hover' in slider[0]
                                current='disabled' if disabled else 'pressed' if active else 'hover' if hover else 'backdrop' if backdrop else 'normal'
                                if name==target_name and phase.startswith(('hover','pressed','released')):
                                    checks[phase+':native-slider-interaction']=active if phase.startswith('pressed') else hover and not active
                                pieces=reader.measure(bar);assert pieces and 'slider' in pieces
                                rect=pieces['slider'];sx,sy=x+rect['x'],y+rect['y'];sw,sh=rect['width'],rect['height']
                                chosen=relief if current==state else 'raised'
                                mask=art.bevel(art.blank(sw,sh,'face'),thickness=2,down=chosen=='sunken')
                                if chosen=='flat':mask=[['face' for token in row] for row in mask]
                                changes=[]
                                with backend.recipe_rules(builder,recipe['palette']):
                                    expected={token:art._rgb(art.evaluate(art.pixel_plan('button',token,inactive=backdrop,disabled=disabled),colors)) for token in ('face','light','dark')}
                                for py,row in enumerate(mask):
                                    for px,token in enumerate(row):
                                        pixels+=1;actual=image.getpixel((sx+px,sy+py))
                                        if max(abs(a-b) for a,b in zip(actual,expected[token]))>1:changes.append({'point':[sx+px,sy+py],'expected':expected[token],'actual':actual})
                                checks[phase+':'+name+':thumb-full-pixels']=not changes
                                details[phase+':'+name+':thumb']={'state':current,'rect':rect,'differences':changes[:20],'difference_count':len(changes)}
                            else:nodes=''
                            details[phase+':'+name]={'differences':differences[:20],'difference_count':len(differences),'allocation':[width,height],'nodes':nodes}
                    window.destroy();settle()
                    record={'scheme':scheme,'state':state,'relief':relief,'checks':checks,'details':details,'pixels':pixels,'passed':all(checks.values())}
                    (case/'NATIVE.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
                    print(case.name,sum(checks.values()),'/',len(checks),flush=True)
        result={'passed':all(r['passed'] for r in records),'cases':records,'pixels':sum(r['pixels'] for r in records),
                'scope':'Full slider pixels and unchanged enclosing/viewport borders; both orientations, native pointer hold/release, sensitivity, controlled BACKDROP; four palettes',
                'limits':['WM focus policy','Historical disabled/hover/pressed appearance','GUI editor'],'historical_fidelity_claimed':False}
        (output/'RESULTADO.json').write_text(json.dumps(result,indent=2)+'\n');return int(not result['passed'])
    finally:
        xtst.XTestFakeButtonEvent(connection,1,0,0);xlib.XFlush(connection);xlib.XCloseDisplay(connection)


if __name__=='__main__':
    if '--worker' in sys.argv:raise SystemExit(worker())
    runner=module(ROOT/'tools/theme-lab/tests/test_trough_native.py','trough_state_runner')
    args=[]
    if '--resume' in sys.argv:
        previous=Path(sys.argv[sys.argv.index('--resume')+1]).resolve(strict=True)
        relative=previous.relative_to(ROOT)
        if not relative.parts[0].startswith('.qa-theme-lab-thumb-states-') or relative.parts[-2:]!=('home','results'):
            raise ValueError('Only this test private results directory may be resumed')
        args=['--resume-relative',str(relative)]
    raise SystemExit(runner.main(script=Path(__file__),prefix='.qa-theme-lab-thumb-states-',worker_args=args,deadline=360))
