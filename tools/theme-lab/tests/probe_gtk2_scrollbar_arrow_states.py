#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture real GTK2 scrollbar stepper states in an explicitly supplied Xephyr."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if os.environ.get('I167_PRIVATE_PROBE') != '1':
    raise SystemExit('Set I167_PRIVATE_PROBE=1 only for an owned Xephyr test.')
out = Path(os.environ['I167_ARROW_OUTPUT']).expanduser().resolve()
tempia = (Path.home() / 'tempia').resolve()
if not out.is_relative_to(tempia):
    raise SystemExit('Evidence must be written under ~/tempia.')
display = os.environ.get('DISPLAY', '')
if display != os.environ.get('I167_NATIVE_DISPLAY') or not display.startswith(':'):
    raise SystemExit('Use the explicitly supplied local Xephyr display.')
out.mkdir(parents=True, exist_ok=True, mode=0o700)
out.chmod(0o700)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
sys.path.insert(0, str(ROOT / 'tools/theme-lab/tests'))
from test_backend import backend, model
from gtk2_recipe import paint_scrollbars
from native_scene_gtk2 import ScrollbarScene
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk
from PIL import Image

scheme_name = os.environ.get('I167_SCHEME', 'DomainOS-SR10.4')
scheme = Path(os.environ.get('I167_SCHEME_PATH', ROOT / 'colors/DomainOS-SR10.4.colors')).resolve()
data = model()
data['selected_family'] = 'gtk2'
data['recipes']['gtk2'].update(
    visible_categories=31, visible_controls=(1 << 10) | (1 << 11),
    selected_control=10, edit_state=0,
    positions=[[16 + (i % 4) * 160, 16 + (i // 4) * 80] for i in range(16)],
    sizes=[[0, 0] for _ in range(16)])
recipe = data['recipes']['gtk2']
recipe['positions'][10], recipe['sizes'][10] = [16, 16], [220, 15]
recipe['positions'][11], recipe['sizes'][11] = [260, 16], [15, 180]
builder = backend.load_builder(ROOT)
colors, palette_origin = backend.native_roles(
    ROOT, scheme, builder.art, backend.sha(scheme.read_bytes()))
palette_origin['selection_scope'] = 'GTK2 isolated probe reads this scheme file; no host/profile scheme change'
with backend.recipe_rules(builder, recipe['palette']):
    generated = paint_scrollbars(builder, recipe, colors, out / 'generated')

os.environ['GTK2_RC_FILES'] = '/dev/null'
os.environ['GTK_MODULES'] = ''
os.environ['NO_AT_BRIDGE'] = '1'
Gtk.init([])
Gtk.rc_parse(str(generated['rc']))

def settle(seconds=.15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(.003)

pointer_before = subprocess.check_output(['xdotool', 'getmouselocation', '--shell'],
                                         text=True, timeout=5)
pointer_before = {line.split('=', 1)[0]: int(line.split('=', 1)[1])
                  for line in pointer_before.splitlines() if line.startswith(('X=', 'Y='))}

def pixel_diff(a, b):
    return sum(x != y for x, y in zip(a.getdata(), b.getdata()))

def inspect_origin(origin):
    host = None
    embed = None
    if origin == 'coupled':
        host = Gtk.Window()
        socket = Gtk.Socket()
        host.add(socket)
        host.set_title('I167 GTK2 socket host')
        host.show_all()
        settle()
        embed = socket.get_id()
    session = ScrollbarScene(Gtk, data, embed_window=embed, Gdk=Gdk)
    window = session.window
    title = 'I167 GTK2 arrow held/release probe ' + origin
    window.set_title(title)
    window.show_all()
    settle()
    if origin == 'coupled':
        # GtkPlug is an embedded child of GtkSocket, so it is not a WM top-level
        # and xdotool's title search cannot find it. GtkPlug.get_id() returns
        # the actual native XID and keeps this capture scoped to the plug.
        xid = str(window.get_id())
    else:
        windows = subprocess.check_output(['xdotool', 'search', '--name', '^' + title + '$'],
                                          text=True, timeout=5).split()
        if len(windows) != 1:
            raise AssertionError(f'{origin}: expected one owned window, got {windows}')
        xid = windows[0]
    rows = []
    try:
        for name, x, y, roi in (
            ('left', 23, 23, (16, 16, 15, 15)),
            ('right', 228, 23, (221, 16, 15, 15)),
            ('up', 267, 23, (260, 16, 15, 15)),
            ('down', 267, 188, (260, 181, 15, 15)),
        ):
            subprocess.run(['xdotool', 'mousemove', '--window', str(xid), str(x), str(y)],
                           check=True, timeout=5)
            settle()
            def capture(state):
                path = out / f'{origin}-{name}-{state}.png'
                # Capture only the owned GTK2 window, never other private Xephyr content.
                subprocess.run(['import', '-window', str(xid), str(path)],
                               check=True, timeout=5)
                with Image.open(path) as image:
                    x0, y0, width, height = roi
                    return image.convert('RGB').crop((x0, y0, x0 + width, y0 + height)).copy()
            baseline = capture('hover')
            subprocess.run(['xdotool', 'mousedown', '1'], check=True, timeout=5)
            try:
                settle(.25)
                held = capture('held')
            finally:
                subprocess.run(['xdotool', 'mouseup', '1'], check=True, timeout=5)
            settle()
            released = capture('released')
            held_delta = pixel_diff(baseline, held)
            release_delta = pixel_diff(baseline, released)
            rows.append({'direction': name, 'roi': list(roi), 'pixels': 225,
                         'held_differences': held_delta,
                         'release_differences': release_delta})
            if held_delta == 0 or release_delta != 0:
                raise AssertionError(f'{origin}/{name}: held={held_delta}, release={release_delta}')
    finally:
        window.destroy()
        if host is not None:
            host.destroy()
        settle()
    return rows

origins = tuple(x for x in os.environ.get('I167_ORIGINS', 'separate,coupled').split(',') if x)
if not origins or any(x not in ('separate', 'coupled') for x in origins):
    raise SystemExit('I167_ORIGINS must contain separate and/or coupled.')
try:
    results = {origin: inspect_origin(origin) for origin in origins}
finally:
    subprocess.run(['xdotool', 'mousemove', str(pointer_before['X']), str(pointer_before['Y'])],
                   check=True, timeout=5)
result = {
    'status': 'passed', 'display': display, 'runtime': f'{Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}',
    'family': 'GTK2', 'scope': 'Real GtkScrollbar stepper press/release for selected origins: ' + ', '.join(origins),
    'scheme': scheme_name, 'palette_origin': palette_origin,
    'recipe_sha256': backend.sha(json.dumps(recipe, sort_keys=True).encode()),
    'rows': results, 'host_changed': False, 'historical_fidelity_claimed': False,
}
(out / 'RESULTADO.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
