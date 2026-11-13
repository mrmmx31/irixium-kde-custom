#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render Classic steppers in private GTK3 processes with native KDE exports.

Run with --output-dir (a new directory), --gray-colors and --blue-colors.
The two colors.css inputs must be genuine KDE GTK Config exports. This test
copies them into disposable profiles, loads the installed-style theme normally,
and compares native scrollbar pixels to the independent original 18px artwork.
It never selects themes or sends input in an existing desktop session.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
THEMES = ('IrixClassic-KDE', 'IrixClassic-KDE-Reload')
DIRECTIONS = {
    'up': ('vertical', (1, 0, 19, 18), (10, 9)),
    'down': ('vertical', (1, 162, 19, 180), (10, 171)),
    'left': ('horizontal', (0, 1, 18, 19), (9, 10)),
    'right': ('horizontal', (162, 1, 180, 19), (171, 10)),
}


def worker(output: Path, theme: str) -> int:
    import cairo
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkX11', '3.0')
    from gi.repository import Gtk, GdkX11
    from PIL import Image
    sys.path.insert(0, str(ROOT / 'tools'))
    from gtk2_palette import asset_color_plan, exported_palette

    palette = exported_palette((Path(os.environ['XDG_CONFIG_HOME']) / 'gtk-3.0/colors.css').read_bytes())
    spec = importlib.util.spec_from_file_location('classic_builder', ROOT / 'gtk/tools/build_kde_classic.py')
    builder = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'gtk/tools'))
    spec.loader.exec_module(builder)
    role_states = {name: values for values in builder.ROLE_STATES.values() for name in values}

    assert Gtk.init_check(None)[0]
    settings = Gtk.Settings.get_default()
    settings.set_property('gtk-theme-name', theme)
    settings.set_property('gtk-application-prefer-dark-theme', True)
    settings.set_property('gtk-enable-animations', False)
    window = Gtk.Window()
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    window.add(box)
    adjustment = Gtk.Adjustment(value=40, lower=0, upper=200, step_increment=1,
                                page_increment=10, page_size=30)
    bars = {}
    for name, orientation in [('horizontal', Gtk.Orientation.HORIZONTAL),
                              ('vertical', Gtk.Orientation.VERTICAL)]:
        bar = Gtk.Scrollbar(orientation=orientation, adjustment=adjustment)
        bar.set_size_request(180, -1) if name == 'horizontal' else bar.set_size_request(-1, 180)
        bar.set_halign(Gtk.Align.START)
        bars[name] = bar
        box.pack_start(bar, False, False, 0)
    window.show_all()

    def settle(iterations=8):
        for _ in range(iterations):
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            time.sleep(.005)

    xlib = ctypes.CDLL('libX11.so.6')
    xtst = ctypes.CDLL('libXtst.so.6')
    xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    xlib.XOpenDisplay.restype = ctypes.c_void_p
    xlib.XFlush.argtypes = [ctypes.c_void_p]
    xlib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int,
                                         ctypes.c_ulong]
    connection = xlib.XOpenDisplay(os.environ['DISPLAY'].encode())
    assert connection
    checks = {}
    records = []

    def capture(phase, disabled=False, backdrop=False, pressed=None, lower=False, upper=False):
        images = {}
        trees = {}
        for name, bar in bars.items():
            allocation = bar.get_allocation()
            checks[phase + ':' + name + ':allocation'] = [allocation.width, allocation.height] == ([180, 20] if name == 'horizontal' else [20, 180])
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, allocation.width, allocation.height)
            bar.draw(cairo.Context(surface))
            filename = output / (phase + '-' + name + '.png')
            surface.write_to_png(str(filename))
            images[name] = Image.open(filename).convert('RGBA')
            trees[name] = bar.get_style_context().to_string(Gtk.StyleContextPrintFlags.RECURSE)
        for direction, (name, rectangle, _) in DIRECTIONS.items():
            insensitive = disabled or (lower and direction in ('up', 'left')) or (upper and direction in ('down', 'right'))
            state = 2 * int(insensitive) + int(backdrop)
            asset = 'stepper-' + direction + ('-disabled' if insensitive else '-pressed' if pressed == direction else '-normal')
            original = Image.open(ROOT / 'gtk/IrixClassic/common/assets' / (asset + '.png')).convert('RGBA')
            actual = images[name].crop(rectangle)
            converted = []
            for pixel in original.getdata():
                if not pixel[3]:
                    converted.append(pixel)
                    continue
                plan = asset_color_plan(asset, '#%02x%02x%02x' % pixel[:3])
                role = role_states.get(plan['role'], [plan['role']] * 4)[state]
                source = tuple(int(palette[role][i:i+2], 16) for i in (1, 3, 5))
                endpoint = tuple(int(plan['endpoint'][i:i+2], 16) for i in (1, 3, 5))
                converted.append(tuple(round(a * (1-plan['mix']) + b * plan['mix']) for a, b in zip(source, endpoint)) + (pixel[3],))
            expected = Image.new('RGBA', (18, 18))
            expected.putdata(converted)
            difference = [max(abs(a-b) for a,b in zip(old,new)) for old,new in zip(actual.getdata(), expected.getdata())]
            # GTK's floating color rounding can differ by one channel unit;
            # geometry, alpha, glyph shape and every pixel still must match.
            checks[phase + ':' + direction + ':artwork'] = max(difference) <= 1
            node = 'button.' + ('up' if direction in ('up', 'left') else 'down')
            lines = [line.strip() for line in trees[name].splitlines() if line.strip().startswith(node + ':')]
            checks[phase + ':' + direction + ':native-state'] = len(lines) == 1 and ((':disabled' in lines[0]) == insensitive) and ((':backdrop' in lines[0]) == backdrop) and (pressed != direction or ':active' in lines[0])
            actual.save(output / (phase + '-' + direction + '.png'))
            records.append({'phase': phase, 'direction': direction, 'asset': asset,
                            'max_channel_difference': max(difference),
                            'different_pixels': sum(bool(value) for value in difference),
                            'native_node': lines[0] if lines else None})

    try:
        settle()
        for phase, value, disabled, backdrop in [('normal', 40, False, False),
                                                 ('lower', 0, False, False),
                                                 ('upper', 170, False, False),
                                                 ('disabled', 40, True, False),
                                                 ('backdrop', 40, False, True),
                                                 ('disabled-backdrop', 40, True, True)]:
            box.set_sensitive(not disabled)
            adjustment.set_value(value)
            for bar in bars.values():
                bar.unset_state_flags(Gtk.StateFlags.BACKDROP)
                if backdrop:
                    bar.set_state_flags(Gtk.StateFlags.BACKDROP, False)
            settle()
            capture(phase, disabled=disabled, backdrop=backdrop, lower=phase == 'lower', upper=phase == 'upper')
        box.set_sensitive(True)
        for bar in bars.values():
            bar.unset_state_flags(Gtk.StateFlags.BACKDROP)
        for direction, (name, _, center) in DIRECTIONS.items():
            adjustment.set_value(40)
            bar = bars[name]
            origin = window.get_window().get_origin()[1:]
            allocation = bar.get_allocation()
            xtst.XTestFakeMotionEvent(connection, -1, origin[0] + allocation.x + center[0], origin[1] + allocation.y + center[1], 0)
            xtst.XTestFakeButtonEvent(connection, 1, 1, 0)
            xlib.XFlush(connection)
            settle(4)
            capture('pressed-' + direction, pressed=direction)
            xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
            xlib.XFlush(connection)
            settle(4)
        result = {'GTK': [Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()],
                  'theme': settings.get_property('gtk-theme-name'), 'dark_variant': settings.get_property('gtk-application-prefer-dark-theme'),
                  'window_id': GdkX11.X11Window.get_xid(window.get_window()),
                  'checks': checks, 'records': records,
                  'scope': 'Native GTK3 normal theme loading from private HOME/XDG. Real XTest arrow presses on own Xvfb; backdrop painted through native GtkWidget state flags. Real KDE-export snapshot inputs; no exporter/live transport tested here. Pixel rounding tolerance <=1; artwork dimensions and every source pixel compared.'}
        (output / 'NATIVE.json').write_text(json.dumps(result, indent=2) + '\n')
        return int(not all(checks.values()))
    finally:
        xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
        xlib.XFlush(connection)
        xlib.XCloseDisplay(connection)
        window.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--gray-colors', type=Path)
    parser.add_argument('--blue-colors', type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--theme', choices=THEMES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if args.worker:
        return worker(output, args.theme)
    if not args.gray_colors or not args.blue_colors:
        parser.error('Two genuine native KDE color exports are required.')
    output.mkdir(mode=0o700)
    snapshots = {name: source.resolve().read_bytes() for name, source in [('gray', args.gray_colors), ('blue', args.blue_colors)]}
    cases = []
    for color, css in snapshots.items():
        for theme in THEMES:
            case = output / (color + '-' + theme)
            case.mkdir(mode=0o700)
            env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
                   'NO_AT_BRIDGE': '1', 'GDK_BACKEND': 'x11', 'GIO_USE_VFS': 'local',
                   'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/nonexistent-private-gtk3-bus',
                   'DBUS_SYSTEM_BUS_ADDRESS': 'unix:path=/nonexistent-private-gtk3-system',
                   'XDG_DATA_DIRS': '/usr/share', 'XDG_CONFIG_DIRS': '/etc/xdg'}
            for variable, name in [('HOME', 'home'), ('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                                   ('XDG_CACHE_HOME', 'cache'), ('XDG_RUNTIME_DIR', 'run'), ('TMPDIR', 'tmp')]:
                folder = case / name
                folder.mkdir(mode=0o700)
                env[variable] = str(folder)
            (case / 'data/themes').mkdir()
            (case / 'data/themes' / theme).symlink_to(ROOT / 'gtk' / theme, target_is_directory=True)
            config = case / 'config/gtk-3.0'
            config.mkdir()
            (config / 'colors.css').write_bytes(css)
            (config / 'gtk.css').write_text('@import "colors.css";\n')
            server = None
            rc = None
            try:
                with (case / 'Xvfb.log').open('w') as log:
                    server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0', '640x420x24', '-nolisten', 'tcp', '-ac'], env=env, text=True, stdout=subprocess.PIPE, stderr=log)
                if not select.select([server.stdout], [], [], 10)[0]:
                    raise RuntimeError('Private Xvfb did not report its display in 10s.')
                number = server.stdout.readline().strip()
                if not number.isdecimal():
                    raise RuntimeError('Private Xvfb failed before GTK loading.')
                env['DISPLAY'] = ':' + number
                child = subprocess.run(['/usr/bin/python3', '-B', str(Path(__file__).resolve()), '--worker', '--theme', theme, '--output-dir', str(case)], env=env, capture_output=True, text=True, timeout=35)
                (case / 'STDOUT.log').write_text(child.stdout)
                (case / 'STDERR.log').write_text(child.stderr)
                rc = child.returncode
            finally:
                if server and server.poll() is None:
                    server.terminate()
                    server.wait(5)
            native = json.loads((case / 'NATIVE.json').read_text()) if (case / 'NATIVE.json').is_file() else {}
            cases.append({'theme': theme, 'color': color, 'colors_sha256': hashlib.sha256(css).hexdigest(),
                          'rc': rc, 'native': str(case / 'NATIVE.json'), 'checks': native.get('checks', {}),
                          'stderr_empty': not (case / 'STDERR.log').read_text()})
    checks = {case['color'] + ':' + case['theme'] + ':' + key: value for case in cases for key, value in case['checks'].items()}
    for case in cases:
        checks[case['color'] + ':' + case['theme'] + ':exit'] = case['rc'] == 0
        checks[case['color'] + ':' + case['theme'] + ':diagnostics'] = case['stderr_empty']
    receipt = {'cases': cases, 'checks': checks, 'passed': sum(checks.values()), 'total': len(checks),
               'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output / 'RESULTADO.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(str(output / 'RESULTADO.json'), receipt['passed'], '/', receipt['total'])
    return int(not all(checks.values()))


if __name__ == '__main__':
    raise SystemExit(main())
