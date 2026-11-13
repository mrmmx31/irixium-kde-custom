#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real public backend CLI -> GTK2 scene in an owned bwrap/Xvfb session.

No guard, generator, process or toolkit is mocked. Only fixture-owned
processes receive input and cleanup; the personal session is not exposed.
"""
import json
import os
import re
import ctypes
import ctypes.util
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HOME = '/home/domainos-test'
TASK_OUTPUT_ROOT = Path.home() / 'tempia'


def output_directory(prefix):
    supplied = os.environ.get('I167_PUBLIC_OUTPUT_ROOT')
    base = Path(supplied).expanduser().resolve() if supplied else TASK_OUTPUT_ROOT
    if not base.is_relative_to(TASK_OUTPUT_ROOT.resolve()):
        raise SystemExit('I167_PUBLIC_OUTPUT_ROOT precisa ficar em ~/tempia.')
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    base.chmod(0o700)
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=base))
    path.chmod(0o700)
    return path


def wait(predicate, process, timeout=45):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        if process.poll() is not None:
            raise AssertionError(f'Owned process exited: {process.returncode}')
        time.sleep(.1)
    raise AssertionError('Timeout in public native GTK2 fixture')


def assert_pointer_hits_preview(environment, window, output):
    pointer = subprocess.check_output(['xdotool', 'getmouselocation', '--shell'],
                                      env=environment, text=True)
    x11_path = ctypes.util.find_library('X11')
    if not x11_path:
        raise AssertionError('Xlib unavailable; cannot verify pointer target safely')
    x11 = ctypes.CDLL(x11_path)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    previous_environment = {key: os.environ.get(key) for key in ('DISPLAY', 'XAUTHORITY')}
    for key in previous_environment:
        os.environ[key] = environment[key]
    display = x11.XOpenDisplay(environment['DISPLAY'].encode())
    if not display:
        for key, value in previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        raise AssertionError('Xlib cannot open the test display for pointer hit-test')
    window_id = ctypes.c_ulong
    int_pointer = ctypes.POINTER(ctypes.c_int)
    window_pointer = ctypes.POINTER(window_id)
    x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    x11.XDefaultRootWindow.restype = window_id
    x11.XQueryPointer.argtypes = [ctypes.c_void_p, window_id, window_pointer,
                                  window_pointer, int_pointer, int_pointer,
                                  int_pointer, int_pointer,
                                  ctypes.POINTER(ctypes.c_uint)]
    x11.XQueryPointer.restype = ctypes.c_int
    root = x11.XDefaultRootWindow(display)
    current = root
    path = []
    root_x = root_y = 0
    for depth in range(32):
        root_return, child_return = window_id(), window_id()
        rx, ry, wx, wy = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
        mask = ctypes.c_uint()
        same = x11.XQueryPointer(display, current, ctypes.byref(root_return),
                                 ctypes.byref(child_return), ctypes.byref(rx), ctypes.byref(ry),
                                 ctypes.byref(wx), ctypes.byref(wy), ctypes.byref(mask))
        if not same:
            break
        if current == root:
            root_x, root_y = rx.value, ry.value
        if not child_return.value:
            break
        path.append(child_return.value)
        current = child_return.value
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay(display)
    for key, value in previous_environment.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    info = subprocess.check_output(['xwininfo', '-id', window, '-tree', '-shape', '-events'],
                                   env=environment, text=True)
    (output / 'pointer-hit-debug.txt').write_text(
        f'preview={window}\nroot_pointer={root_x},{root_y}\n'
        f'XQueryPointer_path={[hex(value) for value in path]}\nxdotool_report:\n{pointer}\n{info}',
        encoding='utf-8')
    allowed = {int(window, 0)}
    allowed.update(int(value, 0) for value in re.findall(r'^\s+(0x[0-9a-fA-F]+)\b', info, re.MULTILINE))
    if not allowed.intersection(path):
        raise AssertionError(
            'XTest aborted before click: XQueryPointer path does not include the GTK2 preview or its child; '
            f'path={[hex(value) for value in path]}, preview=0x{int(window, 0):x}, '
            f'coordinates={root_x},{root_y}')


class _ClientMessageData(ctypes.Union):
    _fields_ = [('b', ctypes.c_char * 20),
                ('s', ctypes.c_short * 10),
                ('l', ctypes.c_long * 5)]


class _ClientMessageEvent(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int),
                ('serial', ctypes.c_ulong),
                ('send_event', ctypes.c_int),
                ('display', ctypes.c_void_p),
                ('window', ctypes.c_ulong),
                ('message_type', ctypes.c_ulong),
                ('format', ctypes.c_int),
                ('data', _ClientMessageData)]


class _XEvent(ctypes.Union):
    _fields_ = [('xclient', _ClientMessageEvent),
                ('pad', ctypes.c_long * 24)]


def send_wm_delete(environment, window):
    """Ask GTK to close through WM_PROTOCOLS; do not destroy its X window."""
    library = ctypes.util.find_library('X11')
    if not library:
        raise AssertionError('libX11 unavailable for a native GTK2 close request')
    x11 = ctypes.CDLL(library)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XGetWMProtocols.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
                                    ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),
                                    ctypes.POINTER(ctypes.c_int)]
    x11.XGetWMProtocols.restype = ctypes.c_int
    x11.XFree.argtypes = [ctypes.c_void_p]
    x11.XFree.restype = ctypes.c_int
    x11.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
                               ctypes.c_int, ctypes.c_long,
                               ctypes.POINTER(_XEvent)]
    x11.XSendEvent.restype = ctypes.c_int
    x11.XFlush.argtypes = [ctypes.c_void_p]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    previous_environment = {key: os.environ.get(key)
                            for key in ('DISPLAY', 'XAUTHORITY')}
    for key in previous_environment:
        value = environment.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    display = x11.XOpenDisplay(environment['DISPLAY'].encode())
    if not display:
        for key, value in previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        raise AssertionError('Cannot open the fixture display for WM_DELETE_WINDOW')
    window_id = int(window, 0)
    protocols = ctypes.POINTER(ctypes.c_ulong)()
    protocol_count = ctypes.c_int()
    try:
        if not x11.XGetWMProtocols(display, window_id,
                                   ctypes.byref(protocols),
                                   ctypes.byref(protocol_count)):
            raise AssertionError('GTK2 preview did not publish WM_PROTOCOLS')
        delete_atom = x11.XInternAtom(display, b'WM_DELETE_WINDOW', 0)
        if delete_atom not in [protocols[i] for i in range(protocol_count.value)]:
            raise AssertionError('GTK2 preview does not accept WM_DELETE_WINDOW')
        event = _XEvent()
        event.xclient.type = 33  # ClientMessage
        event.xclient.display = display
        event.xclient.window = window_id
        event.xclient.message_type = x11.XInternAtom(display, b'WM_PROTOCOLS', 0)
        event.xclient.format = 32
        event.xclient.data.l[0] = delete_atom
        event.xclient.data.l[1] = 0  # CurrentTime
        if not x11.XSendEvent(display, window_id, 0, 0, ctypes.byref(event)):
            raise AssertionError('XSendEvent rejected WM_DELETE_WINDOW')
        x11.XFlush(display)
        x11.XSync(display, 0)
    finally:
        if protocols:
            x11.XFree(protocols)
        x11.XCloseDisplay(display)
        for key, value in previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run(scheme, all_controls=False, directions_filter=None, trace_input=False):
    prefix = '.qa-gtk2-public-all-' if all_controls else '.qa-gtk2-public-'
    output = output_directory(prefix)
    print(output, flush=True)
    for name in ('home/.config', 'home/.local/share', 'home/.local/state',
                 'home/.cache', 'etc', 'run/user/1000', 'tmp'):
        (output / name).mkdir(parents=True, mode=0o700, exist_ok=True)
    (output / 'etc/passwd').write_text(f'domainos-test:x:1000:1000:Preview:{HOME}:/usr/sbin/nologin\n')
    (output / 'etc/group').write_text('domainos-test:x:1000:\n')
    (output / 'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\n')
    (output / 'etc/domainos-preview').touch()
    for source in ('/etc/fonts', '/etc/ld.so.cache', '/etc/alternatives'):
        path = Path(source)
        if path.is_dir(): (output / 'etc' / path.name).mkdir()
        elif path.exists(): (output / 'etc' / path.name).touch()
    shutil.copyfile(ROOT / 'colors/DomainOS-SR10.4.colors', output / 'home/.config/kdeglobals')
    sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
    import backend
    contract = json.loads((ROOT / 'tools/domainos_scrollbar_rules.json').read_text())
    recipe = {'geometry': {key: contract['geometry'][key] for key in backend.GEOMETRY[:7]},
              'palette': dict(backend.DEFAULT_ROLES, **backend.FACTORS)}
    recipe['geometry'].update(control_padding_px=4, font_px=13)
    if all_controls:
        recipe.update(visible_categories=31, visible_controls=(1 << len(backend.CONTROLS)) - 1,
                      selected_control=0)
        recipe['positions'] = [[16 + (index % 4) * 160, 16 + (index // 4) * 80]
                               for index in range(len(backend.CONTROLS))]
    else:
        recipe.update(visible_controls=(1 << 10) | (1 << 11), selected_control=10)
        recipe['positions'] = [[16, 16] for _ in range(16)]
        recipe['positions'][11] = [260, 16]
    recipe['sizes'] = [[0, 0] for _ in range(16)]
    if not all_controls:
        recipe['sizes'][10], recipe['sizes'][11] = [220, 15], [15, 180]
    project = {'schema_version': 2, 'kind': 'theme_lab_project', 'name': 'Public GTK2 fixture',
               'selected_family': 'gtk2', 'color_scheme': scheme,
               'recipes': {family: recipe for family in backend.FAMILIES}}
    backend.write_json(output / 'home/project.json', project)
    cached_output = os.environ.get('I167_PREGENERATED_OUTPUT_ROOT')
    if cached_output:
        source = Path(cached_output).expanduser().resolve(strict=True)
        if not source.is_relative_to(TASK_OUTPUT_ROOT.resolve()) or source.name != 'out':
            raise SystemExit('I167_PREGENERATED_OUTPUT_ROOT deve ser uma pasta out anterior dentro de ~/tempia.')
        target = output / 'home/out'
        shutil.copytree(source, target)
        for revision in (target / 'revisions').iterdir():
            if not revision.is_dir():
                continue
            for stale in (revision / 'gtk2-preview-events', revision / 'gtk2-PREVIEW.json'):
                if stale.is_dir():
                    shutil.rmtree(stale)
                elif stale.exists():
                    stale.unlink()
    supplied_display = os.environ.get('I167_NATIVE_DISPLAY')
    supplied_authority = os.environ.get('I167_NATIVE_XAUTHORITY')
    if supplied_display:
        if not supplied_authority:
            raise SystemExit('I167_NATIVE_XAUTHORITY é obrigatório com Xephyr existente.')
        display_number = supplied_display.lstrip(':').split('.', 1)[0]
        if not display_number.isdigit():
            raise SystemExit('I167_NATIVE_DISPLAY deve ser um display X local, como :74.')
        number = int(display_number)
        authority = Path(supplied_authority).expanduser().resolve(strict=True)
        display = supplied_display
        if not Path(f'/tmp/.X11-unix/X{number}').exists():
            raise SystemExit('O socket do display informado não está ativo.')
    else:
        number = next(n for n in range(180, 10000) if not Path(f'/tmp/.X{n}-lock').exists()
                      and not Path(f'/tmp/.X11-unix/X{n}').exists())
        display = f':{number}'
        authority = output / 'Xauthority'
        authority.touch(mode=0o600)
        subprocess.run(['xauth', '-f', str(authority), 'add', display, '.', secrets.token_hex(16)], check=True)
    environment = dict(os.environ, DISPLAY=display, XAUTHORITY=str(authority))
    server = child = None
    preview_pid = None
    preview_window = None
    with (output / 'namespace.log').open('w') as log:
        try:
            if not supplied_display:
                server = subprocess.Popen(['Xvfb', display, '-screen', '0', '800x600x24',
                                           '-nolisten', 'tcp', '-auth', str(authority)],
                                          stdout=log, stderr=log, start_new_session=True)
                wait(lambda: subprocess.run(['xdpyinfo'], env=environment, stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL).returncode == 0, server, 10)
            elif subprocess.run(['xdpyinfo'], env=environment, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL).returncode != 0:
                raise SystemExit('Não foi possível autenticar no Xephyr existente.')
            command = ['unshare', '--user', '--map-root-user', '--net', 'bwrap', '--unshare-user',
                       '--unshare-ipc', '--unshare-uts', '--uid', '1000', '--gid', '1000', '--clearenv',
                       '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
                       '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
                       '--ro-bind', str(output / 'etc'), '/etc', '--proc', '/proc', '--dev', '/dev',
                       '--bind', str(output / 'run'), '/run', '--bind', str(output / 'tmp'), '/tmp',
                       '--bind', str(output / 'home'), HOME, '--ro-bind', str(ROOT), '/fixture/root',
                       '--ro-bind', f'/tmp/.X11-unix/X{number}', f'/tmp/.X11-unix/X{number}',
                       '--ro-bind', str(authority), HOME + '/.Xauthority']
            for source in ('/etc/fonts', '/etc/ld.so.cache', '/etc/alternatives'):
                if Path(source).exists(): command += ['--ro-bind', source, source]
            values = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8', 'HOME': HOME,
                      'DISPLAY': display, 'XAUTHORITY': HOME + '/.Xauthority',
                      'XDG_CONFIG_HOME': HOME + '/.config', 'XDG_DATA_HOME': HOME + '/.local/share',
                      'XDG_STATE_HOME': HOME + '/.local/state', 'XDG_CACHE_HOME': HOME + '/.cache',
                      'XDG_RUNTIME_DIR': '/run/user/1000', 'GDK_BACKEND': 'x11', 'NO_AT_BRIDGE': '1',
                      'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap', 'PRIVATE_XEPHYR': '1',
                      'IRIX_DOMAINOS_PRIVATE_XEPHYR': '1', 'IRIX_DOMAINOS_SESSION_ROOT': HOME}
            for key, value in values.items(): command += ['--setenv', key, value]
            command += ['--die-with-parent', '--new-session', '--chdir', HOME, 'dbus-run-session', '--',
                        '/usr/bin/python3', '-B', '/fixture/root/tools/theme-lab/backend.py', '--preview',
                        '--root', '/fixture/root', '--project', HOME + '/project.json',
                        '--output', HOME + '/out', '--kdeglobals', HOME + '/.config/kdeglobals', '--family', 'gtk2']
            if trace_input:
                command.append('--gtk2-trace-input')
            child = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
            def launched():
                for path in (output / 'home/out/revisions').glob('*/gtk2-PREVIEW.json'):
                    try:
                        proof = json.loads(path.read_text())
                        if proof['status'] == 'launched': return path, proof
                    except (OSError, json.JSONDecodeError): pass
            path, proof = wait(launched, child)
            preview_pid = proof.get('pid')
            generation = json.loads((path.parent / 'RESULTADO.json').read_text())
            assert set(generation['families']) == {'gtk2'}, generation['families'].keys()
            def events():
                rows = [json.loads(p.read_text()) for p in
                        (path.parent / 'gtk2-preview-events').glob('event-*.json')]
                # Directory iteration order is not event order. Keep input
                # assertions deterministic when several scrollbar steps have
                # already emitted native value events.
                return sorted(rows, key=lambda row: row.get('emitted_at', ''))
            rows = wait(lambda: events() or None, child)
            wait(lambda: any(r['action'] == 'metrics' for r in events()), child)
            # The native gallery title no longer says "receita parcial"; keep
            # this smoke test coupled to the stable application identity while
            # allowing the subtitle to describe the current recipe scope.
            windows = subprocess.check_output(['xdotool', 'search', '--name', '^Theme Lab — GTK2 nativo'], env=environment, text=True).split()
            assert len(windows) == 1, windows
            window = preview_window = windows[0]
            # The existing Xephyr has the Theme Lab window beneath this
            # separately launched preview. Explicitly raise/focus our owned
            # GTK2 client so XTest input reaches its scrollbars, not the lab.
            subprocess.run(['xdotool', 'windowraise', window], env=environment,
                           check=True, timeout=5)
            subprocess.run(['xdotool', 'windowfocus', '--sync', window], env=environment,
                           check=True, timeout=5)
            focused_window = subprocess.check_output(['xdotool', 'getwindowfocus'],
                                                     env=environment, text=True).strip()
            geometry = subprocess.check_output(['xdotool', 'getwindowgeometry', '--shell', window],
                                               env=environment, text=True)
            geometry_values = dict(line.split('=', 1) for line in geometry.splitlines() if '=' in line)
            window_x, window_y = int(geometry_values['X']), int(geometry_values['Y'])
            display_size = subprocess.check_output(['xdotool', 'getdisplaygeometry'],
                                                   env=environment, text=True).split()
            far_x, far_y = int(display_size[0]) - 1, int(display_size[1]) - 1
            def move_pointer(local_x, local_y):
                # Force a motion even when the old pointer is already at the
                # requested coordinate, then use absolute X-server positions.
                subprocess.run(['xdotool', 'mousemove', '--sync', str(far_x), str(far_y)],
                               env=environment, check=True, timeout=5)
                subprocess.run(['xdotool', 'mousemove', '--sync',
                                str(window_x + local_x), str(window_y + local_y)],
                               env=environment, check=True, timeout=5)
            (output / 'window-input-debug.txt').write_text(
                f'window={window}\nfocus={focused_window}\n{geometry}')
            subprocess.run(['import', '-window', window, str(output / 'preview-window-start.png')],
                           env=environment, check=True, timeout=5)
            if all_controls:
                metrics = [row for row in events() if row['action'] == 'metrics']
                assert {row['control_id'] for row in metrics} == set(backend.CONTROLS), metrics
                native_events = []
                for control, x, y in (('push', 22, 23), ('toggle', 182, 23),
                                      ('check', 342, 23), ('radio', 502, 57)):
                    move_pointer(x, y)
                    assert_pointer_hits_preview(environment, window, output)
                    subprocess.run(['xdotool', 'click', '1'], env=environment, check=True)
                    event = wait(lambda control=control: next((row for row in events()
                        if row['action'] == 'native' and row['control_id'] == control), None), child)
                    native_events.append(event)
                assert native_events[0]['state'] == {'clicked': True}, native_events[0]
                assert native_events[1]['state'].get('active') is True, native_events[1]
                assert native_events[2]['state'].get('active') is True, native_events[2]
                assert native_events[3]['state'].get('selected_member') == 1, native_events[3]
                assert set(proof['translated_controls']) == set(backend.CONTROLS), proof
                native = native_events
            else:
                # Compare every real GtkRange stepper in the public preview
                # while held and after release. The baseline is captured with
                # the pointer already over the arrow, so hover does not get
                # mistaken for the pressed relief.
                arrow_pressure = []
                direction_rows = (
                    ('scroll_h', 10, recipe['sizes'][10], ('left', 'right')),
                    ('scroll_v', 11, recipe['sizes'][11], ('up', 'down')),
                )
                for control_id, index, extent, all_directions in direction_rows:
                    directions = (tuple(direction for direction in all_directions
                                         if direction in directions_filter)
                                  if directions_filter is not None else all_directions)
                    if not directions:
                        continue
                    bx, by = recipe['positions'][index]
                    bw, bh = extent
                    targets = {
                        'left': (bx + 7, by + 7, (bx, by, bx + 15, by + 15)),
                        'right': (bx + bw - 8, by + 7,
                                  (bx + bw - 15, by, bx + bw, by + 15)),
                        'up': (bx + 7, by + 7, (bx, by, bx + 15, by + 15)),
                        'down': (bx + 7, by + bh - 8,
                                 (bx, by + bh - 15, bx + 15, by + bh)),
                    }
                    for direction in directions:
                        x, y, roi = targets[direction]
                        # Confirm the warp actually reaches this client before
                        # interpreting any pixels or adjustment events as a click.
                        move_pointer(x, y)
                        assert_pointer_hits_preview(environment, window, output)
                        pointer = subprocess.check_output(['xdotool', 'getmouselocation', '--shell'],
                                                          env=environment, text=True)
                        with (output / 'window-input-debug.txt').open('a') as debug:
                            debug.write(f'pointer-before-{control_id}-{direction}:\n{pointer}')
                        time.sleep(.15)
                        def capture(label):
                            path = output / f'arrow-{control_id}-{direction}-{label}.png'
                            subprocess.run(['import', '-window', window, str(path)],
                                           env=environment, check=True, timeout=5)
                            with Image.open(path) as image:
                                return image.convert('RGB').crop(roi).copy()
                        baseline = capture('hover')
                        subprocess.run(['xdotool', 'mousedown', '1'],
                                       env=environment, check=True, timeout=5)
                        try:
                            # GTK2 may accept the press (including repeating
                            # the step) before ImageMagick observes the next
                            # expose. Poll the actual cell instead of treating
                            # a fixed 200 ms capture as evidence of lost input.
                            held_deadline = time.monotonic() + 1.5
                            held = capture('held')
                            held_differences = sum(a != b for a, b in zip(baseline.getdata(), held.getdata()))
                            while held_differences == 0 and time.monotonic() < held_deadline:
                                time.sleep(.05)
                                held = capture('held')
                                held_differences = sum(a != b for a, b in zip(baseline.getdata(), held.getdata()))
                            held_capture_ms = round((1.5 - max(0.0, held_deadline - time.monotonic())) * 1000)
                        finally:
                            subprocess.run(['xdotool', 'mouseup', '1'],
                                           env=environment, check=True, timeout=5)
                        released = capture('released')
                        release_differences = sum(a != b for a, b in zip(baseline.getdata(), released.getdata()))
                        release_deadline = time.monotonic() + 1.5
                        while release_differences != 0 and time.monotonic() < release_deadline:
                            time.sleep(.05)
                            released = capture('released')
                            release_differences = sum(a != b for a, b in zip(baseline.getdata(), released.getdata()))
                        release_capture_ms = round((1.5 - max(0.0, release_deadline - time.monotonic())) * 1000)
                        assert held_differences > 0, (control_id, direction, 'pressed state did not change')
                        assert release_differences == 0, (control_id, direction, 'release did not restore hover state')
                        arrow_pressure.append({'control_id': control_id, 'direction': direction,
                                               'roi': list(roi), 'pixels': 225,
                                               'held_differences': held_differences,
                                               'release_differences': release_differences,
                                               'held_capture_ms': held_capture_ms,
                                               'release_capture_ms': release_capture_ms})
                native = None
                if directions_filter is None:
                    move_pointer(22, 23)
                    assert_pointer_hits_preview(environment, window, output)
                    prior_scroll_values = [r['state']['value'] for r in events()
                        if r.get('action') == 'native' and r.get('control_id') == 'scroll_h'
                        and 'value' in r.get('state', {})]
                    assert prior_scroll_values, 'no native horizontal value before click'
                    expected_after_click = prior_scroll_values[-1] - 1
                    prior_native_ids = {r['event_id'] for r in events()
                                        if r.get('action') == 'native'}
                    subprocess.run(['xdotool', 'click', '1'], env=environment, check=True)
                    native = wait(lambda: next((r for r in events()
                        if r.get('action') == 'native' and r.get('event_id') not in prior_native_ids), None), child)
                    assert native.get('control_id') == 'scroll_h', native
                    assert native['state']['value'] == expected_after_click, (expected_after_click, native)
            subprocess.run(['import', '-window', window, str(output / 'preview.png')], env=environment, check=True)
            assert proof['guards']['verified'] and proof['recipe_scope'] == 'translated_controls'
            assert {'scroll_h', 'scroll_v'} <= set(proof['translated_controls'])
            assert not proof['recipe_applied']
            assert all(r['project_sha256'] == proof['preview_project_sha256'] for r in events())
            # Send the actual WM_PROTOCOLS/WM_DELETE_WINDOW client message.
            # xdotool windowclose destroys the drawable directly when no WM is
            # running, which can race GTK's final GDK paint and create BadDrawable.
            send_wm_delete(environment, window)
            child.wait(timeout=15)
            final = json.loads(path.read_text())
            assert child.returncode == 0 and final['status'] == 'closed', final
            if all_controls:
                assert set(final['translated_controls']) == set(backend.CONTROLS), final
                pixels = {'scope': 'All-controls public capture; no per-control pixel claim.'}
                click_results = [{'control_id': row['control_id'], 'state': row['state']}
                                 for row in native_events]
            else:
                from verify_gtk2_public_capture import verify
                pixels = (verify(output) if directions_filter is None else
                          {'scope': 'Single-direction input diagnosis; full pixel matrix not repeated.'})
                click_results = ({'value': native['state']['value']} if native is not None else None)
            result = {'status': 'passed', 'scheme': scheme, 'all_controls': all_controls,
                      'guards_real': True, 'native_clicks': click_results,
                      'metric_controls': sorted({r['control_id'] for r in events()
                                                 if r['action'] == 'metrics'}),
                      'arrow_pressure': arrow_pressure if not all_controls else [],
                      'native_events': len(events()), 'normal_close': True,
                      'receipt': final, 'pixels': pixels,
                      'capture': str(output / 'preview.png')}
            (output / 'results.json').write_text(json.dumps(result, indent=2))
            return result
        finally:
            if preview_window:
                subprocess.run(['xdotool', 'windowclose', preview_window], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=5, check=False)
            if isinstance(preview_pid, int) and preview_pid > 1:
                command_line = Path(f'/proc/{preview_pid}/cmdline')
                try:
                    owned = b'/fixture/root/tools/theme-lab/preview_gtk2.py' in command_line.read_bytes()
                except OSError:
                    owned = False
                if owned:
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline and command_line.exists():
                        time.sleep(.05)
                    if command_line.exists():
                        os.kill(preview_pid, signal.SIGTERM)
            for process in (child, server):
                if process is not None and process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try: process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait()


if __name__ == '__main__':
    diagnostic_direction = os.environ.get('I167_PUBLIC_DIAGNOSTIC_DIRECTION')
    if diagnostic_direction:
        if diagnostic_direction not in ('left', 'right', 'up', 'down'):
            raise SystemExit('I167_PUBLIC_DIAGNOSTIC_DIRECTION deve ser left/right/up/down.')
        results = [run('DomainOS-SR10.4', directions_filter=(diagnostic_direction,),
                       trace_input=True)]
    else:
        results = [run(scheme) for scheme in ('DomainOS-SR10.4', 'BreezeDark')]
        results.append(run('DomainOS-SR10.4', all_controls=True))
    print(json.dumps(results), flush=True)
