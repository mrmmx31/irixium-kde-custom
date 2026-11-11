#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 trailing-edge native pipeline with real anchored generation and scenes."""
import copy
import json
import os
from pathlib import Path
import sys
import time
import subprocess
assert os.environ.get('T04_PRIVATE_ANCHOR_GEOMETRY') == '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_backend import ROOT, backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from gtk2_anchor_geometry import requested_origin, allocated_origin
import gi
gi.require_version('Gtk', '2.0'); gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk

Gtk.init([])
output = Path(sys.argv[1]).resolve(); output.mkdir(parents=True, exist_ok=True)
data = model(); data['selected_family'] = 'gtk2'
r = data['recipes']['gtk2']
r.update(visible_controls=(1 << 10) | (1 << 11), selected_control=10, edit_state=0)
r['positions'] = [[16, 16] for _ in range(16)]
r['positions'][10] = [400, 100]; r['positions'][11] = [100, 400]
r['sizes'] = [[0, 0] for _ in range(16)]
r['length_anchor'] = [0]*10+[1,1]+[0]*4
folder = output / 'generation'; folder.mkdir(mode=0o700)
receipt = generate_scrollbar_snapshot(backend, ROOT, folder, data,
                                      ROOT / 'colors/DomainOS-SR10.4.colors')
class Writer:
    def emit(self, *args, **kwargs): pass

def drain():
    end = time.monotonic() + .15
    while time.monotonic() < end:
        while Gtk.events_pending(): Gtk.main_iteration()
        time.sleep(.001)

rows = []
for origin in ('coupled', 'separate'):
    host = None
    if origin == 'coupled':
        host = Gtk.Window(); host.set_title('GTK2 anchor lifecycle private'); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
    session = NativeSession(backend, Gtk, Gdk, ROOT, receipt['rc'], data, 'a' * 64, Writer(),
                            embed_window=socket.get_id() if host else None)
    drain()
    for label, sizes in (('natural', ([0, 0], [0, 0])),
                         ('below_native_minimum', ([1, 1], [1, 1])),
                         ('custom', ([320, 15], [15, 260]))):
        candidate = copy.deepcopy(data)
        candidate['recipes']['gtk2']['sizes'][10] = sizes[0]
        candidate['recipes']['gtk2']['sizes'][11] = sizes[1]
        session.replace(candidate, ('b' if label == 'natural' else 'c' if label == 'below_native_minimum' else 'd') * 64)
        drain(); scene = session.scene
        for index, axis in ((10, 0), (11, 1)):
            record = dict(scene.records[index], length_anchor=1)
            scene.records[index] = record
            widget = scene.widgets[index]
            predicted = requested_origin(record, scene.natural[index])
            actual = allocated_origin(record, widget)
            assert predicted == actual, (origin, index, label, predicted, actual, scene.natural[index])
            scene.placement.apply(index); drain()
            allocation = widget.get_allocation()
            edge = (allocation.x + allocation.width) if axis == 0 else (allocation.y + allocation.height)
            assert edge == 400, (origin, index, label, edge)
            assert (allocation.x, allocation.y) == actual
            # Resizing changes the leading edge, while the trailing coordinate stays.
            widget.set_size_request(360 if axis == 0 else 15, 15 if axis == 0 else 300)
            drain()
            resized = allocated_origin(record, widget)
            drain()
            allocation = widget.get_allocation()
            resized_edge = allocation.x + allocation.width if axis == 0 else allocation.y + allocation.height
            assert resized_edge == 400
            rows.append({'origin': origin, 'axis': axis, 'case': label,
                         'native_minimum': scene.natural[index], 'initial_origin': list(actual),
                         'resized_origin': list(resized), 'trailing_edge': resized_edge})
    scene = session.scene
    scene.widgets[10].set_size_request(320, 15); drain()
    def x(*args):
        return subprocess.run(['xdotool', *map(str, args)], check=True, capture_output=True, text=True, timeout=5).stdout
    title = host.get_title() if host else scene.window.get_title()
    windows = x('search', '--onlyvisible', '--pid', os.getpid(), '--name', title).split()
    assert len(windows) == 1, windows
    geometry = dict(line.split('=',1) for line in x('getwindowgeometry','--shell',windows[0]).splitlines() if '=' in line)
    ox, oy = int(geometry['X']), int(geometry['Y'])
    def drag(fail=False):
        widget=scene.widgets[10]; allocation=widget.get_allocation()
        start=(ox+allocation.x+allocation.width//2,oy+allocation.y+7)
        before=dict(scene.records[10]); value=widget.get_adjustment().get_value()
        original=scene.writer.emit
        if fail:
            def failing(action,*args,**fields):
                if action=='move': raise OSError('private anchor commit failure')
                return original(action,*args,**fields)
            scene.writer.emit=failing
        try:
            x('mousemove',*start); x('keydown','ctrl'); x('mousedown',1); drain()
            for dx,dy in ((12,8),(24,16),(36,24)):
                x('mousemove',start[0]+dx,start[1]+dy); drain()
            provisional=dict(before,x=before['x']+36,y=before['y']+24)
            assert 10 in scene.placement.overrides, (origin, start, geometry, scene.gestures.active, getattr(scene,'last_error',None), (allocation.x,allocation.y,allocation.width,allocation.height))
            # Motion may be compressed/hinted by X. Resize must preserve the
            # last delivered position; release must commit its own root coords.
            delivered=scene.gestures.active['position']
            assert delivered != (before['x'],before['y'])
            assert tuple(scene.placement.overrides[10]) == delivered
            widget.set_size_request(300,15); drain()
            a=widget.get_allocation(); assert a.x+a.width==delivered[0],(a.x,a.width,delivered)
            x('mouseup',1); drain()
        finally:
            x('mouseup',1);x('keyup','ctrl');scene.writer.emit=original
        expected=before if fail else provisional
        assert scene.records[10]==expected
        a=widget.get_allocation();assert a.x+a.width==expected['x']
        assert widget.get_adjustment().get_value()==value
        assert scene.gestures.active is None and not scene.placement.overrides
    drag();drag(True)
    saved=dict(scene.records[10])
    try: scene.move_control(10,1,100)
    except ValueError: pass
    else: raise AssertionError('invalid trailing position accepted')
    assert scene.records[10]==saved
    old_placement=scene.placement
    old_placement.changed(scene.widgets[10],scene.widgets[10].get_allocation(),10)
    assert old_placement.pending
    session.close();drain()
    assert old_placement.closed and not old_placement.pending and not old_placement.handlers
    rows.append({'origin':origin,'native_ctrl_drag':True,'resize_during_drag':True,
                 'failed_commit_rolls_back':True,'invalid_move_rejected':True,'pending_idle_cancelled_on_close':True})
    if host: host.destroy()
report = {'status': 'passed', 'native_cases': rows,
          'scene_or_generator_capability_enabled': True,
          'native_gestures_verified': True, 'controller_verified': False,
          'historical_fidelity_claimed': False, 'personal_session_changed': False}
(output / 'RESULTADO.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({'status': 'passed', 'native_cases': len(rows), 'capability_enabled': True, 'native_gestures': 2}))
