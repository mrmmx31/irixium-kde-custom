#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native private GTK2 session replacement and preservation proof."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch
assert os.environ.get('I167_PRIVATE_PROBE') == '1'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', type=Path, required=True)
parser.add_argument('--rc', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--embedded', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
import gtk2_session
from preview_event_writer import EventWriter
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk
Gtk.init([])
model = json.loads(args.project.read_text())
def digest(model): return hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()
def drain():
    deadline = time.monotonic() + .08
    while time.monotonic() < deadline:
        while Gtk.events_pending(): Gtk.main_iteration()
        time.sleep(.001)
host = None
if args.embedded:
    host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
    xid = socket.get_id()
else: xid = None
writer = EventWriter(args.output / 'events', backend.ROOT, family='gtk2')
session = gtk2_session.NativeSession(backend, Gtk, Gdk, backend.ROOT, args.rc, model, digest(model), writer, xid)
drain()
window = session.scene.window
session.scene.widgets[10].get_adjustment().set_value(43)
session.scene.widgets[11].get_adjustment().set_value(51)
original = copy.deepcopy(model)
rows = []
for iteration in range(1, 11):
    proposal = copy.deepcopy(model)
    recipe = proposal['recipes']['gtk2']
    recipe['positions'][10] = [41 + iteration, 57 + iteration]
    recipe['sizes'][10] = [240 + 5 * iteration, 15]
    previous = session.scene
    session.replace(proposal, digest(proposal))
    drain()
    assert session.scene.window is window
    assert not previous.gestures.handlers
    assert len(session.scene.gestures.handlers) == 9
    assert Gtk.grab_get_current() is None
    metrics = session.scene.metrics()
    assert metrics[0]['allocation'] == [41 + iteration, 57 + iteration, 240 + 5 * iteration, 15]
    assert [item['value'] for item in metrics] == [43, 51]
    session.scene.emit_metrics()
    rows.append(metrics)
assert model == original
stable = session.scene
stable_metrics = stable.metrics()
bad = copy.deepcopy(model)
bad['recipes']['gtk2']['sizes'][10] = [-1, 15]
try: session.replace(bad, digest(bad))
except ValueError: pass
else: raise AssertionError('Invalid layout accepted')
assert session.scene is stable and stable.metrics() == stable_metrics
old_rc = args.rc.read_bytes()
try:
    args.rc.write_bytes(old_rc + b'\n# artificial tampering\n')
    try: session.replace(model, digest(model))
    except ValueError as error: assert 'RC GTK2 alterado' in str(error)
    else: raise AssertionError('Modified RC accepted')
    assert session.scene is stable and stable.metrics() == stable_metrics
finally: args.rc.write_bytes(old_rc)
factory = gtk2_session.LayoutGestures
calls = []
def fail_once(*values):
    calls.append(True)
    if len(calls) == 1: raise RuntimeError('artificial reparent failure')
    return factory(*values)
with patch.object(gtk2_session, 'LayoutGestures', side_effect=fail_once):
    try: session.replace(model, digest(model))
    except RuntimeError: pass
    else: raise AssertionError('Injected failure did not occur')
drain()
assert session.scene is stable and stable.window.get_child() is stable.fixed
assert stable.metrics() == stable_metrics
assert len(stable.gestures.handlers) == 9
assert Gtk.grab_get_current() is None
session.scene.widgets[10].get_adjustment().set_value(44)
assert session.scene.widgets[10].get_adjustment().get_value() == 44
session.scene.window.set_sensitive(False)
drain()
assert session.scene.window.get_name() == 'themeLabCanvasInsensitiveWindow'
session.replace(model, digest(model))
drain()
assert session.scene.window is window and not window.get_sensitive()
assert window.get_child().get_name() == 'themeLabCanvasInsensitive'
assert session.scene.widgets[10].get_adjustment().get_value() == 44
window.set_sensitive(True)
drain()
assert window.get_child().get_name() == 'themeLabCanvas'
session.close()
if host: host.destroy()
print(json.dumps({'status': 'passed', 'embedded': args.embedded, 'replacements': rows,
                  'same_window_preserved': True, 'adjustments_preserved': True,
                  'invalid_layout_and_tampered_rc_preserve_previous': True,
                  'reparent_failure_restores_previous_and_handlers': True,
                  'native_interaction_after_failure': True, 'model_unchanged': True}, indent=2))
