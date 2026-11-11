#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measured GTK2 trailing-edge foundation; scene capability remains guarded."""
import copy
import json
import os
from pathlib import Path
import sys
import time
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
        host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
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
            widget = scene.widgets[index]
            predicted = requested_origin(record, scene.natural[index])
            actual = allocated_origin(record, widget)
            assert predicted == actual, (origin, index, label, predicted, actual, scene.natural[index])
            scene.fixed.move(widget, *actual); drain()
            allocation = widget.get_allocation()
            edge = (allocation.x + allocation.width) if axis == 0 else (allocation.y + allocation.height)
            assert edge == 400, (origin, index, label, edge)
            assert (allocation.x, allocation.y) == actual
            # Resizing changes the leading edge, while the trailing coordinate stays.
            widget.set_size_request(360 if axis == 0 else 15, 15 if axis == 0 else 300)
            drain()
            resized = allocated_origin(record, widget)
            scene.fixed.move(widget, *resized); drain()
            allocation = widget.get_allocation()
            resized_edge = allocation.x + allocation.width if axis == 0 else allocation.y + allocation.height
            assert resized_edge == 400
            rows.append({'origin': origin, 'axis': axis, 'case': label,
                         'native_minimum': scene.natural[index], 'initial_origin': list(actual),
                         'resized_origin': list(resized), 'trailing_edge': resized_edge})
    session.close()
    if host: host.destroy()
report = {'status': 'passed', 'native_cases': rows,
          'scene_or_generator_capability_enabled': False,
          'gestures_or_controller_verified': False,
          'historical_fidelity_claimed': False, 'personal_session_changed': False}
(output / 'RESULTADO.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({'status': 'passed', 'native_cases': len(rows), 'capability_enabled': False}))
