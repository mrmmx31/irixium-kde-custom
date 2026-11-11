#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK3 screen-pixel proof of the lab's independent trough recipe.

KColorScheme supplies every palette/state. Proposed geometry is not a claim
about historical Motif defaults. The worker cannot access the personal home.
"""
import configparser
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HOME = '/home/domainos-test'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def worker():
    thumb_mode = '--thumb' in sys.argv
    fitting_mode = '--fitting' in sys.argv
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk
    from PIL import Image
    backend = module(ROOT/'tools/theme-lab/backend.py', 'trough_backend')
    fixtures = module(ROOT/'tools/theme-lab/tests/test_backend.py', 'trough_fixtures')
    builder = backend.load_builder(ROOT)
    pieces_module = module(ROOT/'tools/theme-lab/native_parts_gtk.py', 'pixel_native_parts')
    pieces_reader = pieces_module.Reader(Gtk)
    assert pieces_reader.available
    art = builder.art
    output = Path(HOME)/'results'
    output.mkdir()
    palette = configparser.ConfigParser(interpolation=None)
    palette.optionxform = str
    palette.read(ROOT/'colors/DomainOS-SR10.4.colors')
    palette['General']['Name'] = 'Artificial yellow fixture'
    for section in ('Colors:Window', 'Colors:Button', 'Colors:View'):
        palette[section]['BackgroundNormal'] = '236,216,112'
        palette[section]['ForegroundNormal'] = '32,28,12'
    directory = Path(HOME)/'.local/share/color-schemes'
    directory.mkdir(parents=True)
    with (directory/'TestYellow.colors').open('w') as stream:
        palette.write(stream)
    assert Gtk.init_check(None)[0]
    settings = Gtk.Settings.get_default()
    settings.set_property('gtk-enable-animations', False)
    xlib = ctypes.CDLL('libX11.so.6')
    xtst = ctypes.CDLL('libXtst.so.6')
    xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    xlib.XOpenDisplay.restype = ctypes.c_void_p
    xlib.XFlush.argtypes = [ctypes.c_void_p]
    xlib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    connection = xlib.XOpenDisplay(os.environ['DISPLAY'].encode())
    assert connection
    records = []

    def settle():
        for _ in range(12):
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            time.sleep(.005)

    def move(x, y):
        xtst.XTestFakeMotionEvent(connection, -1, x, y, 0)
        xlib.XFlush(connection)
        settle()

    try:
        for scheme in ('DomainOS-SR10.4', 'BreezeLight', 'BreezeDark', 'TestYellow'):
            case = output/scheme
            case.mkdir()
            data = fixtures.model()
            data.update(schema_version=2, color_scheme=scheme)
            recipe = data['recipes']['gtk3']
            recipe['scrollbar_parts'] = {'trough': {'thickness_px': 17, 'shadow_px': 1}}
            if thumb_mode:
                recipe['scrollbar_parts']['thumb'] = {'cross_px': 9, 'shadow_px': 1, 'gap_px': 3}
            if fitting_mode:
                recipe['scrollbar_parts']['fitting'] = {'gap_px': 7, 'inset_px': 1}
            origin = backend.generate_gtk3(ROOT, case, data, Path(HOME)/'.config/kdeglobals')
            theme = Path(origin['theme_path'])
            themes = Path(HOME)/'.local/share/themes'
            themes.mkdir(exist_ok=True)
            (themes/origin['theme']).symlink_to(theme, target_is_directory=True)
            colors = json.loads((case/'GTK3-NATIVE-COLORS.json').read_text())['colors']
            settings.set_property('gtk-theme-name', origin['theme'])
            window = Gtk.Window()
            window.set_default_size(440, 280)
            scroll = Gtk.ScrolledWindow()
            scroll.set_overlay_scrolling(False)
            scroll.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
            content = Gtk.DrawingArea()
            content.set_size_request(900, 650)
            scroll.add(content)
            window.add(scroll)
            window.show_all()
            bars = {'horizontal': scroll.get_hscrollbar(), 'vertical': scroll.get_vscrollbar()}
            viewport = scroll.get_child()
            assert isinstance(viewport, Gtk.Viewport)
            checks, native_nodes, native_piece_boxes = {}, {}, {}
            for phase in ('normal', 'hover', 'pressed', 'released', 'backdrop', 'disabled', 'disabled-backdrop'):
                if phase == 'released':
                    # Release at the pressed pointer position before moving
                    # or resetting adjustments. Otherwise the fixture drags
                    # the thumb to the endpoint and samples it as empty track.
                    xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
                    xlib.XFlush(connection)
                    settle()
                disabled = phase.startswith('disabled')
                backdrop = 'backdrop' in phase
                scroll.set_sensitive(not disabled)
                for widget in (*bars.values(), viewport):
                    widget.unset_state_flags(Gtk.StateFlags.BACKDROP)
                    if backdrop:
                        widget.set_state_flags(Gtk.StateFlags.BACKDROP, False)
                for adjustment in (scroll.get_hadjustment(), scroll.get_vadjustment()):
                    adjustment.set_value((adjustment.get_upper()-adjustment.get_page_size())/2)
                move(700, 400)
                if phase in ('hover', 'pressed', 'released'):
                    bar = bars['vertical']
                    if thumb_mode:
                        start, end = bar.get_slider_range()
                        target = (start+end)//2
                    else:
                        target = bar.get_allocated_height()-7
                    px, py = bar.translate_coordinates(window, bar.get_allocated_width()//2, target)
                    wx, wy = window.get_window().get_origin()[1:]
                    move(wx+px, wy+py)
                if phase == 'pressed':
                    xtst.XTestFakeButtonEvent(connection, 1, 1, 0)
                    xlib.XFlush(connection)
                    settle()
                if phase == 'released':
                    xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
                    xlib.XFlush(connection)
                    settle()
                capture = case/(phase+'.png')
                shot = Gdk.pixbuf_get_from_window(window.get_window(), 0, 0,
                                                window.get_allocated_width(), window.get_allocated_height())
                shot.savev(str(capture), 'png', [], [])
                image = Image.open(capture).convert('RGB')
                def compare_frame(widget, family, border, label):
                    width, height = widget.get_allocated_width(), widget.get_allocated_height()
                    px, py = widget.translate_coordinates(window, 0, 0)
                    tokens = art.bevel(art.blank(width, height), thickness=border, down=True)
                    differences = []
                    with backend.recipe_rules(builder, recipe['palette']):
                        for y, row in enumerate(tokens):
                            for x, token in enumerate(row):
                                if token is None:
                                    continue
                                color = art.evaluate(art.pixel_plan(family, token, inactive=backdrop, disabled=disabled), colors)
                                expected = art._rgb(color)
                                actual = image.getpixel((px+x, py+y))
                                differences.append(max(abs(a-b) for a, b in zip(expected, actual)))
                    checks[phase+':'+label+':integer-frame'] = bool(differences) and max(differences) <= 1
                    return width, height
                for orientation, bar in bars.items():
                    nodes = bar.get_style_context().to_string(Gtk.StyleContextPrintFlags.RECURSE)
                    native_nodes[phase+':'+orientation] = nodes
                    if orientation == 'vertical' and phase in ('hover', 'pressed', 'released'):
                        target = 'slider:' if thumb_mode else 'button.down:'
                        down = [line for line in nodes.splitlines() if line.strip().startswith(target)]
                        checks[phase+':native-'+('thumb' if thumb_mode else 'stepper')+'-state'] = len(down)==1 and (
                            ':active' in down[0] if phase=='pressed' else ':hover' in down[0] and ':active' not in down[0])
                    pieces = pieces_reader.measure(bar)
                    native_piece_boxes[phase+':'+orientation] = pieces
                    checks[phase+':'+orientation+':native-margin-boxes'] = bool(pieces) and all(
                        key in pieces for key in ('slider','track','arrow_first','arrow_last'))
                    if pieces and thumb_mode:
                        cursor=pieces['slider']
                        checks[phase+':'+orientation+':measured-margin-contains-painted-cross-9'] = (
                            cursor['height'] if orientation=='horizontal' else cursor['width'])>=9
                    width, height = compare_frame(bar, 'button', 1, orientation)
                    checks[phase+':'+orientation+':cross-17'] = (height if orientation=='horizontal' else width)==17
                    checks[phase+':'+orientation+':native-sensitive'] = bar.is_sensitive()==(not disabled)
                    px, py = bar.translate_coordinates(window, 0, 0)
                    # Empty trough immediately before the final arrow, beyond
                    # the midrange thumb. Sample the real screen, not canvas.
                    x, y = (width-25, height//2) if orientation=='horizontal' else (width//2, height-25)
                    with backend.recipe_rules(builder, recipe['palette']):
                        expected = art._rgb(art.evaluate(art.pixel_plan('button', 'trough', inactive=backdrop, disabled=disabled), colors))
                    checks[phase+':'+orientation+':trough-role'] = max(abs(a-b) for a,b in zip(image.getpixel((px+x,py+y)),expected))<=1
                    if thumb_mode:
                        start, end = bar.get_slider_range()
                        middle = (start + end)//2
                        offset = ((height if orientation=='horizontal' else width) - 9)//2
                        tokens = art.bevel(art.blank(9, 9, 'face'), thickness=1, down=False)
                        differences = []
                        with backend.recipe_rules(builder, recipe['palette']):
                            for transverse in range(9):
                                token = tokens[transverse][4] if orientation=='horizontal' else tokens[4][transverse]
                                expected_thumb = art._rgb(art.evaluate(art.pixel_plan('button', token, inactive=backdrop, disabled=disabled), colors))
                                point = (px+middle, py+offset+transverse) if orientation=='horizontal' else (px+offset+transverse, py+middle)
                                differences.append(max(abs(a-b) for a,b in zip(image.getpixel(point), expected_thumb)))
                        checks[phase+':'+orientation+':thumb-cross-9-relief-1'] = max(differences)<=1
                        for transverse in (offset-1, offset+9):
                            point = (px+middle, py+transverse) if orientation=='horizontal' else (px+transverse, py+middle)
                            checks[phase+':'+orientation+':thumb-margin-'+str(transverse)] = max(abs(a-b) for a,b in zip(image.getpixel(point),expected))<=1
                        if phase=='normal':
                            adjustment = bar.get_adjustment()
                            adjustment.set_value(adjustment.get_lower())
                            settle()
                            lower, _ = bar.get_slider_range()
                            adjustment.set_value(adjustment.get_upper()-adjustment.get_page_size())
                            settle()
                            _, upper = bar.get_slider_range()
                            checks[orientation+':native-gap-3'] = lower==15 and upper==(width if orientation=='horizontal' else height)-15
                            adjustment.set_value((adjustment.get_upper()-adjustment.get_page_size())/2)
                            settle()
                compare_frame(viewport, 'view', 1 if fitting_mode else 2,
                              'independent-viewport' if fitting_mode else 'unchanged-viewport')
                if fitting_mode:
                    vx, vy = viewport.translate_coordinates(window, 0, 0)
                    hx, hy = bars['horizontal'].translate_coordinates(window, 0, 0)
                    bx, by = bars['vertical'].translate_coordinates(window, 0, 0)
                    checks[phase+':horizontal-content-gap-7'] = hy - (vy + viewport.get_allocated_height()) == 7
                    checks[phase+':vertical-content-gap-7'] = bx - (vx + viewport.get_allocated_width()) == 7
                if disabled:
                    before = scroll.get_vadjustment().get_value()
                    bar = bars['vertical']
                    px, py = bar.translate_coordinates(window, bar.get_allocated_width()//2, bar.get_allocated_height()-7)
                    wx, wy = window.get_window().get_origin()[1:]
                    move(wx+px, wy+py)
                    for held in (1, 0):
                        xtst.XTestFakeButtonEvent(connection, 1, held, 0)
                        xlib.XFlush(connection)
                        settle()
                    checks[phase+':disabled-input-blocked'] = scroll.get_vadjustment().get_value()==before
            xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
            xlib.XFlush(connection)
            window.destroy()
            settle()
            record = {'scheme': scheme, 'checks': checks, 'passed': all(checks.values()),
                      'palette_origin': origin['palette'], 'selected_scheme': origin['selected_scheme'],
                      'native_nodes': native_nodes, 'native_piece_boxes': native_piece_boxes}
            (case/'NATIVE.json').write_text(json.dumps(record, indent=2)+'\n')
            records.append(record)
            print(scheme, sum(checks.values()), '/', len(checks), flush=True)
        result = {'cases': records, 'passed': all(record['passed'] for record in records),
                  'scope': 'Real GTK3 screen frames and trough face; 17px trough/1px inset, unchanged 2px GtkViewport; four KColorScheme palettes; explicit GTK backdrop state',
                  'fitting_recipe': {'gap_px': 7, 'inset_px': 1} if fitting_mode else None,
                  'thumb_recipe': {'cross_px': 9, 'shadow_px': 1, 'gap_px': 3} if thumb_mode else None,
                  'historical_fidelity_claimed': False, 'personal_home_exposed': False,
                  'not_verified': ['Internal stepper allocation', 'Historical disabled/backdrop defaults', 'Disabled input in other directions']}
        (output/'RESULTADO.json').write_text(json.dumps(result, indent=2)+'\n')
        return int(not result['passed'])
    finally:
        xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
        xlib.XFlush(connection)
        xlib.XCloseDisplay(connection)


def main(script=None, prefix='.qa-theme-lab-trough-', worker_args=(), deadline=180):
    if '--worker' in sys.argv:
        return worker()
    output = Path(tempfile.mkdtemp(prefix=prefix, dir=ROOT))
    print(output, flush=True)
    for name in ('home', 'home/.config', 'home/.local/share', 'home/.local/state', 'home/.cache', 'etc', 'run/user/1000', 'tmp'):
        (output/name).mkdir(mode=0o700, parents=True, exist_ok=True)
    (output/'etc/passwd').write_text(f'domainos-test:x:1000:1000:Preview:{HOME}:/usr/sbin/nologin\n')
    (output/'etc/group').write_text('domainos-test:x:1000:\n')
    (output/'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\n')
    for path in ('/etc/fonts', '/etc/ld.so.cache', '/etc/alternatives'):
        target = output/'etc'/Path(path).name
        if Path(path).is_dir():
            target.mkdir()
        else:
            target.touch()
    (output/'home/.config/kdeglobals').write_bytes((ROOT/'colors/DomainOS-SR10.4.colors').read_bytes())
    server = process = None
    with (output/'LOG').open('w') as log:
        try:
            server = subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','800x500x24','-nolisten','tcp','-ac'], stdout=subprocess.PIPE, stderr=log, text=True)
            assert select.select([server.stdout], [], [], 10)[0]
            number = int(server.stdout.readline().strip())
            command = ['unshare','--user','--map-root-user','--net','bwrap','--unshare-user','--unshare-ipc','--unshare-uts','--uid','1000','--gid','1000','--clearenv',
                       '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64',
                       '--ro-bind',str(output/'etc'),'/etc','--proc','/proc','--dev','/dev','--bind',str(output/'run'),'/run',
                       '--bind',str(output/'tmp'),'/tmp','--bind',str(output/'home'),HOME,'--ro-bind',str(ROOT),'/fixture/root',
                       '--ro-bind',f'/tmp/.X11-unix/X{number}',f'/tmp/.X11-unix/X{number}']
            for path in ('/etc/fonts','/etc/ld.so.cache','/etc/alternatives'):
                command += ['--ro-bind',path,path]
            environment = {'PATH':'/usr/bin:/bin','HOME':HOME,'LC_ALL':'C.UTF-8','DISPLAY':':'+str(number),
                           'XDG_CONFIG_HOME':HOME+'/.config','XDG_DATA_HOME':HOME+'/.local/share','XDG_STATE_HOME':HOME+'/.local/state',
                           'XDG_CACHE_HOME':HOME+'/.cache','XDG_RUNTIME_DIR':'/run/user/1000','GDK_BACKEND':'x11',
                           'NO_AT_BRIDGE':'1','GIO_USE_VFS':'local','XDG_DATA_DIRS':'/usr/share'}
            for key,value in environment.items():
                command += ['--setenv',key,value]
            command += ['--die-with-parent','--new-session','--chdir',HOME,'dbus-run-session','--','/usr/bin/python3','-B',
                        '/fixture/root/'+str(Path(script).relative_to(ROOT) if script else Path('tools/theme-lab/tests/test_trough_native.py')),'--worker']
            for mode in ('--thumb', '--fitting'):
                if mode in sys.argv:
                    command += [mode]
            command += list(worker_args)
            process = subprocess.Popen(command, stdout=log, stderr=log)
            result = process.wait(timeout=deadline)
            print((output/'LOG').read_text(), flush=True)
            return result
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            if server is not None:
                server.terminate()
                server.wait(timeout=10)


if __name__ == '__main__':
    raise SystemExit(main())
