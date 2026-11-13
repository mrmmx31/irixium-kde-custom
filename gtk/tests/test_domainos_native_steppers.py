#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render DomainOS SR10.4 Motif steppers using snapshots of real KDE color roles.

Run with --output-dir (a new directory), --gray-colors and --blue-colors.
The colors.css inputs can be raw KDE GTK Config exports or documented,
normalized snapshots from the KDE palette bridge. This test copies those
KDE-derived role snapshots into disposable profiles, loads the theme normally,
and compares native scrollbar pixels to the 11px semantic artwork in a 15px bar.
The range-end color policy is an adaptation: a logically disabled end arrow
keeps its sensitive scrollbar's colors. A wholly insensitive scrollbar keeps
its own disabled palette. Neither comparison establishes historical disabled
Motif colors. Use --boundary to check just this changed scope.
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
import re
import select
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
THEMES = ('DomainOS-SR10-4-KDE', 'DomainOS-SR10-4-KDE-Reload')
DIRECTIONS = {
    'up': ('vertical', (2, 2, 13, 13), (7, 7)),
    'down': ('vertical', (2, 167, 13, 178), (7, 173)),
    'left': ('horizontal', (2, 2, 13, 13), (7, 7)),
    'right': ('horizontal', (167, 2, 178, 13), (173, 7)),
}


def worker(output: Path, theme: str, *, boundary_only=False) -> int:
    import cairo
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkX11', '3.0')
    from gi.repository import Gtk, GdkX11
    from PIL import Image
    sys.path.insert(0, str(ROOT / 'tools'))
    sys.path.insert(0, str(ROOT / 'gtk/tools'))
    from gtk2_palette import exported_palette
    import domainos_motif_art as art
    import build_kde_domainos as builder

    palette = exported_palette((Path(os.environ['XDG_CONFIG_HOME']) / 'gtk-3.0/colors.css').read_bytes())

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
            checks[phase + ':' + name + ':allocation'] = [allocation.width, allocation.height] == ([180, 15] if name == 'horizontal' else [15, 180])
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, allocation.width, allocation.height)
            bar.draw(cairo.Context(surface))
            filename = output / (phase + '-' + name + '.png')
            surface.write_to_png(str(filename))
            images[name] = Image.open(filename).convert('RGBA')
            trees[name] = bar.get_style_context().to_string(Gtk.StyleContextPrintFlags.RECURSE)
        for direction, (name, rectangle, _) in DIRECTIONS.items():
            insensitive = disabled or (lower and direction in ('up', 'left')) or (upper and direction in ('down', 'right'))
            asset = 'stepper-' + direction + ('-disabled' if insensitive else '-pressed' if pressed == direction else '-normal')
            actual = images[name].crop(rectangle)
            # Logical child sensitivity and paint origin are independent:
            # an end-of-range arrow uses its parent's palette without being
            # re-enabled. A wholly insensitive parent still uses disabled roles.
            background = art.evaluate(art.pixel_plan('button', 'trough', inactive=backdrop, disabled=disabled), palette)
            expected = Image.new('RGBA', (11, 11), tuple(int(background[index:index+2], 16) for index in (1, 3, 5))+(255,))
            pixels = builder.gtk3_arrow('disabled' if insensitive else 'pressed' if pressed == direction else 'normal', direction)
            family = 'button'
            for yy, row in enumerate(pixels):
                for xx, token in enumerate(row):
                    if token is None: continue
                    plan = art.pixel_plan(family, token, inactive=backdrop, disabled=disabled)
                    color = art.evaluate(plan, palette)
                    expected.putpixel((xx, yy), tuple(int(color[index:index+2], 16) for index in (1, 3, 5))+(255,))
            difference = [max(abs(a-b) for a,b in zip(old,new)) for old,new in zip(actual.getdata(), expected.getdata())]
            # GTK's floating color rounding can differ by one channel unit;
            # geometry, alpha, glyph shape and every pixel still must match.
            checks[phase + ':' + direction + ':artwork'] = max(difference) <= 1
            node = 'button.' + ('up' if direction in ('up', 'left') else 'down')
            lines = [line.strip() for line in trees[name].splitlines() if line.strip().startswith(node + ':')]
            checks[phase + ':' + direction + ':native-state'] = len(lines) == 1 and ((':disabled' in lines[0]) == insensitive) and ((':backdrop' in lines[0]) == backdrop) and (pressed != direction or ':active' in lines[0])
            actual.save(output / (phase + '-' + direction + '.png'))
            records.append({'phase': phase, 'direction': direction, 'asset': asset,
                            'logical_disabled': insensitive, 'parent_disabled': disabled,
                            'paint_face_role': art.role('button', inactive=backdrop, disabled=disabled),
                            'max_channel_difference': max(difference),
                            'different_pixels': sum(bool(value) for value in difference),
                            'native_node': lines[0] if lines else None})

    def blocked_click(phase, direction):
        bar = bars[DIRECTIONS[direction][0]]
        origin = window.get_window().get_origin()[1:]
        allocation = bar.get_allocation()
        center = DIRECTIONS[direction][2]
        before = adjustment.get_value()
        xtst.XTestFakeMotionEvent(connection, -1, origin[0]+allocation.x+center[0],
                                 origin[1]+allocation.y+center[1], 0)
        xtst.XTestFakeButtonEvent(connection, 1, 1, 0)
        xlib.XFlush(connection)
        settle(4)
        xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
        xlib.XFlush(connection)
        settle(4)
        checks[phase+':'+direction+':blocked-click-no-adjustment'] = adjustment.get_value() == before

    boundary_phases = [('lower', 0, False, False), ('upper', 170, False, False),
                       ('lower-backdrop', 0, False, True), ('upper-backdrop', 170, False, True),
                       ('disabled-lower', 0, True, False), ('disabled-upper-backdrop', 170, True, True)]
    ordinary_phases = [('normal', 40, False, False), ('disabled', 40, True, False),
                       ('backdrop', 40, False, True), ('disabled-backdrop', 40, True, True)]
    try:
        settle()
        for phase, value, disabled, backdrop in boundary_phases + ([] if boundary_only else ordinary_phases):
            box.set_sensitive(not disabled)
            adjustment.set_value(value)
            for bar in bars.values():
                bar.unset_state_flags(Gtk.StateFlags.BACKDROP)
                if backdrop:
                    bar.set_state_flags(Gtk.StateFlags.BACKDROP, False)
            settle()
            lower = phase in ('lower', 'lower-backdrop', 'disabled-lower')
            upper = phase in ('upper', 'upper-backdrop', 'disabled-upper-backdrop')
            capture(phase, disabled=disabled, backdrop=backdrop, lower=lower, upper=upper)
            checks[phase+':parent-sensitive'] = all(bar.is_sensitive() == (not disabled) for bar in bars.values())
            if disabled:
                blocked = DIRECTIONS
            elif lower:
                blocked = ('up', 'left')
            elif upper:
                blocked = ('down', 'right')
            else:
                blocked = ()
            for direction in blocked:
                blocked_click(phase, direction)
        box.set_sensitive(True)
        for bar in bars.values():
            bar.unset_state_flags(Gtk.StateFlags.BACKDROP)
        for direction, (name, _, center) in ([] if boundary_only else DIRECTIONS.items()):
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
                  'worker_pid': os.getpid(),
                  'window_id': GdkX11.X11Window.get_xid(window.get_window()),
                  'checks': checks, 'records': records, 'boundary_only': boundary_only,
                  'palette_policy': 'Range-end arrows retain sensitive-parent colors while remaining logically disabled; a wholly insensitive parent retains insensitive colors. Adaptation, not historical Motif disabled-state proof.',
                  'scope': 'Native GTK3 theme loading from private HOME/XDG. Real XTest arrow presses on own Xvfb; backdrop painted through native GtkWidget state flags. KDE-derived role snapshots, from raw exports or documented normalized bridge snapshots; exporter and live transport are not tested here. Pixel rounding tolerance <=1; artwork dimensions and every semantic pixel compared. VUE source pixels, files and fonts are not embedded.'}
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
    parser.add_argument('--gray-colors', type=Path,
                        help='KDE-derived gray role snapshot: raw export or documented normalized bridge snapshot.')
    parser.add_argument('--blue-colors', type=Path,
                        help='KDE-derived blue role snapshot: raw export or documented normalized bridge snapshot.')
    parser.add_argument('--extra-colors', action='append', default=[], metavar='NAME=PATH',
                        help='Add a named KDE-derived role snapshot; labels must be distinct safe directory names.')
    parser.add_argument('--themes', nargs='+', choices=THEMES, default=THEMES,
                        help='Limit identities checked; the default preserves both existing themes.')
    parser.add_argument('--corner', action='store_true', help='Exercise real TreeView scrollbar corners, hover and bounds.')
    parser.add_argument('--boundary', action='store_true', help='Check only limits, backdrop limits and wholly insensitive limits; preserve disabled input handling.')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--theme', choices=THEMES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if args.worker:
        if args.corner:
            from test_domainos_native_scroll_corner import worker as corner_worker
            return corner_worker(output, args.theme, boundary_only=args.boundary)
        return worker(output, args.theme, boundary_only=args.boundary)
    if not args.gray_colors or not args.blue_colors:
        parser.error('Two KDE-derived role snapshots are required: raw exports or documented normalized bridge snapshots.')
    sources = {'gray': args.gray_colors, 'blue': args.blue_colors}
    for value in args.extra_colors:
        label, separator, filename = value.partition('=')
        if not separator or not filename or not re.fullmatch(r'[a-z][a-z0-9_-]*', label):
            parser.error('--extra-colors must use a safe NAME=PATH, such as dark=/tmp/colors.css.')
        if label in sources:
            parser.error('Duplicate palette label: '+label)
        sources[label] = Path(filename)
    snapshots = {name: source.resolve().read_bytes() for name, source in sources.items()}
    output.mkdir(mode=0o700)
    cases = []
    for color, css in snapshots.items():
        for theme in dict.fromkeys(args.themes):
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
                    server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0', '640x420x24', '-nolisten', 'tcp', '-ac', '-extension', 'MIT-SHM'], env=env, text=True, stdout=subprocess.PIPE, stderr=log)
                if not select.select([server.stdout], [], [], 10)[0]:
                    raise RuntimeError('Private Xvfb did not report its display in 10s.')
                number = server.stdout.readline().strip()
                if not number.isdecimal():
                    raise RuntimeError('Private Xvfb failed before GTK loading.')
                env['DISPLAY'] = ':' + number
                command = ['/usr/bin/python3', '-B', str(Path(__file__).resolve()), '--worker', '--theme', theme, '--output-dir', str(case)]
                if args.corner: command.append('--corner')
                if args.boundary: command.append('--boundary')
                child = subprocess.run(command, env=env, capture_output=True, text=True, timeout=35)
                (case / 'STDOUT.log').write_text(child.stdout)
                (case / 'STDERR.log').write_text(child.stderr)
                rc = child.returncode
            finally:
                if server and server.poll() is None:
                    server.terminate()
                    server.wait(5)
            native = json.loads((case / 'NATIVE.json').read_text()) if (case / 'NATIVE.json').is_file() else {}
            native.setdefault('checks', {})['worker_report_present'] = bool(native.get('records'))
            native['checks']['owned_worker_gone'] = bool(native.get('worker_pid')) and not Path('/proc', str(native['worker_pid'])).exists()
            native['checks']['owned_xvfb_gone'] = server is not None and not Path('/proc', str(server.pid)).exists()
            cases.append({'theme': theme, 'color': color, 'colors_sha256': hashlib.sha256(css).hexdigest(),
                          'colors_source': str(sources[color].resolve()),
                          'rc': rc, 'native': str(case / 'NATIVE.json'), 'checks': native.get('checks', {}),
                          'stderr_empty': not (case / 'STDERR.log').read_text()})
    checks = {case['color'] + ':' + case['theme'] + ':' + key: value for case in cases for key, value in case['checks'].items()}
    for case in cases:
        checks[case['color'] + ':' + case['theme'] + ':exit'] = case['rc'] == 0
        checks[case['color'] + ':' + case['theme'] + ':diagnostics'] = case['stderr_empty']
    receipt = {'cases': cases, 'checks': checks, 'passed': sum(checks.values()), 'total': len(checks),
               'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'mode': 'native-scrolled-corner' if args.corner else 'isolated-scrollbars',
               'boundary_only': args.boundary}
    (output / 'RESULTADO.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(str(output / 'RESULTADO.json'), receipt['passed'], '/', receipt['total'])
    return int(not all(checks.values()))


if __name__ == '__main__':
    raise SystemExit(main())
