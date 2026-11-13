#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned private-Xvfb scene probe, no personal display input."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import hashlib
assert os.environ.get('I167_PRIVATE_PROBE') == '1'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', type=Path, required=True)
parser.add_argument('--rc', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--embedded', action='store_true')
parser.add_argument('--ipc', action='store_true')
parser.add_argument('--gestures', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk
from native_scene_gtk2 import ScrollbarScene
from preview_event_writer import EventWriter
Gtk.init([])
Gtk.rc_parse(str(args.rc))
model = json.loads(args.project.read_text())
host = None
if args.embedded:
    host = Gtk.Window()
    host.set_title('I167 GTK2 gesture host ' + str(os.getpid()))
    socket = Gtk.Socket()
    host.add(socket)
    host.show_all()
    while Gtk.events_pending(): Gtk.main_iteration()
    xid = socket.get_id()
else:
    xid = None
writer = EventWriter(args.output / 'events', Path(__file__).resolve().parents[3], family='gtk2') if args.ipc or args.gestures else None
project_hash = hashlib.sha256(args.project.read_bytes()).hexdigest()
native = ScrollbarScene(Gtk, model, xid, writer, project_hash, Gdk if args.gestures else None)
deadline = time.monotonic() + 3
while time.monotonic() < deadline:
    while Gtk.events_pending(): Gtk.main_iteration()
    if all(w.get_allocation().width > 1 and w.get_allocation().height > 1
           for w in native.widgets.values()) and (not args.embedded or native.window.get_embedded()):
        break
    time.sleep(.005)
metrics = native.metrics()
for item in metrics:
    record = native.records[item['index']]
    x, y, width, height = item['allocation']
    assert [x, y] == [record['x'], record['y']], item
    assert [width, height] == [record['width'], record['height']], item
    assert item['origin'] == ('coupled' if args.embedded else 'separate')
assert not args.embedded or native.window.get_embedded()
gestures = None
if args.gestures:
    def drain(seconds=.06):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            while Gtk.events_pending(): Gtk.main_iteration()
            time.sleep(.001)
    def x(*values):
        return subprocess.run(['xdotool', *map(str, values)], check=True, capture_output=True, text=True, timeout=5).stdout
    title = host.get_title() if host else native.window.get_title()
    windows = x('search', '--onlyvisible', '--pid', os.getpid(), '--name', title).split()
    assert len(windows) == 1, windows
    geometry = dict(line.split('=', 1) for line in x('getwindowgeometry', '--shell', windows[0]).splitlines() if '=' in line)
    ox, oy = int(geometry['X']), int(geometry['Y'])
    record = native.records[10]
    sx, sy = ox + record['x'] + 7, oy + record['y'] + 7
    adjustment = native.widgets[10].get_adjustment()
    initial = adjustment.get_value()
    held = ctrl = False
    try:
        x('mousemove', sx, sy)
        x('keydown', 'ctrl'); ctrl = True
        x('mousedown', 1); held = True; drain()
        assert adjustment.get_value() == initial, 'Ctrl selection operated scrollbar'
        for dx, dy in ((12, 8), (24, 16), (36, 24)):
            x('mousemove', sx + dx, sy + dy); drain()
        x('mouseup', 1); held = False; drain()
    finally:
        if held: x('mouseup', 1)
        if ctrl: x('keyup', 'ctrl')
    drain()
    moved = native.widgets[10].get_allocation()
    assert [moved.x, moved.y] == [record['x'] + 36, record['y'] + 24], (moved.x, moved.y, native.records[10], getattr(native, 'last_error', None))
    assert adjustment.get_value() == initial
    assert native.gestures.active is None
    sx, sy = ox + moved.x + 7, oy + moved.y + 7
    held = False
    try:
        x('mousemove', sx, sy)
        x('mousedown', 1); held = True; drain()
        assert adjustment.get_value() == initial - 1, adjustment.get_value()
    finally:
        if held: x('mouseup', 1)
    drain()
    assert native.records[10]['x'] == record['x'] + 36
    # Fail only the commit event after a real preview drag. It must roll back
    # its provisional position, report the failure and release its GTK grab.
    successful = dict(native.records[10])
    original_emit = writer.emit
    def fail_move(action, *values, **fields):
        if action == 'move': raise OSError('artificial move persistence failure')
        return original_emit(action, *values, **fields)
    writer.emit = fail_move
    held = ctrl = False
    try:
        x('mousemove', ox + successful['x'] + 7, oy + successful['y'] + 7)
        x('keydown', 'ctrl'); ctrl = True
        x('mousedown', 1); held = True; drain()
        x('mousemove', ox + successful['x'] + 43, oy + successful['y'] + 31); drain()
        x('mouseup', 1); held = False; drain()
    finally:
        if held: x('mouseup', 1)
        if ctrl: x('keyup', 'ctrl')
        writer.emit = original_emit
    drain()
    failed = native.widgets[10].get_allocation()
    assert [failed.x, failed.y] == [successful['x'], successful['y']]
    assert native.records[10] == successful
    assert native.gestures.active is None
    assert 'artificial move persistence failure' in native.last_error
    value_before = adjustment.get_value()
    held = False
    try:
        x('mousemove', ox + failed.x + 7, oy + failed.y + 7)
        x('mousedown', 1); held = True; drain()
    finally:
        if held: x('mouseup', 1)
    drain()
    assert adjustment.get_value() == value_before - 1
    gestures = {'ctrl_drag_delta': [36, 24], 'ctrl_preserves_native_adjustment': True,
                'plain_click_delta': -1, 'grab_released': True,
                'failed_commit_rolls_back_position_and_releases_grab':True,
                'plain_click_works_after_failure':True}
if args.ipc:
    native.emit_metrics()
    native.select_control(10)
    native.move_control(10, 83, 91)
    while Gtk.events_pending(): Gtk.main_iteration()
    native.widgets[10].get_adjustment().set_value(40)
    while Gtk.events_pending(): Gtk.main_iteration()
    native.emit_metrics()
    assert native.widgets[10].get_allocation().x == 83
args.output.mkdir(parents=True, exist_ok=True)
subprocess.run(['import', '-window', 'root', str(args.output / 'native.png')], check=True, timeout=10)
native.window.destroy()
if host: host.destroy()
print(json.dumps({'status': 'passed', 'metrics': metrics, 'embedded': args.embedded,
                  'gesture_results':gestures,
                  'project_sha256':project_hash, 'ipc_events_emitted':args.ipc,
                  'native_toolkit': 'GTK2', 'scene_scope': 'Scrollbar foundation only',
                  'personal_display_input_sent': False}, indent=2))
