# SPDX-License-Identifier: GPL-3.0-or-later
"""Real mixed GTK2 scene: button input, metrics and transactional replacement."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
assert os.environ.get('I167_PRIVATE_PROBE') == '1'
parser = argparse.ArgumentParser()
parser.add_argument('--project', type=Path, required=True)
parser.add_argument('--rc', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--embedded', action='store_true')
parser.add_argument('--toggle', action='store_true')
parser.add_argument('--radio', action='store_true')
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from gtk2_session import NativeSession
from preview_event_writer import EventWriter
import gi
gi.require_version('Gtk', '2.0'); gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk
Gtk.init([])
def drain():
    end = time.monotonic() + .1
    while time.monotonic() < end:
        while Gtk.events_pending(): Gtk.main_iteration()
        time.sleep(.001)
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
model = json.loads(args.project.read_text()); host = None
if args.embedded:
    host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
    xid = socket.get_id()
else: xid = None
writer = EventWriter(args.output / 'events', backend.ROOT, family='gtk2')
session = NativeSession(backend, Gtk, Gdk, backend.ROOT, args.rc, model, digest(model), writer, xid)
drain(); session.scene.emit_metrics()
window = session.scene.window; widget = session.scene.widgets[0]
metrics = session.scene.metrics(); push = next(m for m in metrics if m['index'] == 0)
assert push['allocation'] == [20, 20, 180, 50]
assert push['font_description'] and not push['font_not_applicable']
ox, oy = (host if host is not None else window).get_position()
subprocess.run(['xdotool', 'mousemove', str(ox+80), str(oy+40), 'click', '1'],
               check=True, capture_output=True, timeout=5); drain()
events = [json.loads(p.read_text()) for p in (args.output / 'events').glob('*.json')]
assert any(e['control_index'] == 0 and e['action'] == 'native' and e['state']['clicked'] for e in events)
if args.toggle:
    assert not session.scene.widgets[1].get_active()
    subprocess.run(['xdotool','mousemove',str(ox+80),str(oy+110),'click','1'],check=True,capture_output=True,timeout=5);drain()
    assert session.scene.widgets[1].get_active()
    assert any(json.loads(p.read_text()).get('state',{}).get('active') is True for p in (args.output/'events').glob('*.json'))
session.scene.widgets[10].get_adjustment().set_value(43)
if args.check:
    assert not session.scene.widgets[2].get_active()
    subprocess.run(['xdotool','mousemove',str(ox+340),str(oy+40),'click','1'],check=True,capture_output=True,timeout=5);drain()
    assert session.scene.widgets[2].get_active()
if args.radio:
    group=session.scene.radio_groups[3]
    natural=next(m for m in session.scene.metrics() if m['index']==3)['native_request_before_custom_size']
    assert all(v>0 for v in natural),natural
    assert group.selected()==0
    for _ in range(2):
        subprocess.run(['xdotool','mousemove',str(ox+340),str(oy+95),'click','1'],check=True,capture_output=True,timeout=5);drain()
        assert group.selected()==1 and sum(w.get_active() for w in group.members)==1
    members_before=group.metrics()
    assert all(r['allocation'][2:]==[180,50] for r in members_before),members_before
proposal = copy.deepcopy(model)
proposal['recipes']['gtk2']['positions'][0] = [40, 60]
proposal['recipes']['gtk2']['sizes'][0] = [200, 60]
if args.toggle:
    proposal['recipes']['gtk2']['positions'][1]=[260,60]
    proposal['recipes']['gtk2']['sizes'][1]=[200,60]
if args.radio:
    proposal['recipes']['gtk2']['positions'][3]=[260,90]
    proposal['recipes']['gtk2']['sizes'][3]=[200,120]
if args.check:
    proposal['recipes']['gtk2']['positions'][2]=[260,90]
    proposal['recipes']['gtk2']['sizes'][2]=[200,60]
previous = session.scene
session.replace(proposal, digest(proposal)); drain()
assert session.scene.window is window and not previous.gestures.handlers
assert session.scene.widgets[10].get_adjustment().get_value() == 43
after = next(m for m in session.scene.metrics() if m['index'] == 0)
assert after['allocation'] == [40, 60, 200, 60]
if args.check:
    assert session.scene.widgets[2].get_active()
    check_after=next(m for m in session.scene.metrics() if m['index']==2)
    assert check_after['allocation']==[260,90,200,60]
    assert check_after['font_description'] and all(v>0 for v in check_after['native_request_before_custom_size'])
    subprocess.run(['xdotool','mousemove',str(ox+340),str(oy+110),'click','1'],check=True,capture_output=True,timeout=5);drain()
    assert not session.scene.widgets[2].get_active()
if args.radio:
    group=session.scene.radio_groups[3]
    assert group.selected()==1
    radio_after=next(m for m in session.scene.metrics() if m['index']==3)
    assert radio_after['allocation']==[260,90,200,120]
    assert all(r['allocation'][2:]==[200,60] for r in group.metrics())
    subprocess.run(['xdotool','mousemove',str(ox+340),str(oy+115),'click','1'],check=True,capture_output=True,timeout=5);drain()
    assert group.selected()==0
    subprocess.run(['xdotool','mousemove',str(ox+340),str(oy+180),'keydown','Control_L',
                    'mousedown','1','mousemove',str(ox+380),str(oy+200),'mouseup','1',
                    'keyup','Control_L'],check=True,capture_output=True,timeout=5);drain()
    assert group.selected()==0, 'Layout gesture changed native group selection'
    assert (session.scene.records[3]['x'],session.scene.records[3]['y'])==(300,110)
if args.toggle:
    assert session.scene.widgets[1].get_active()
    toggle=next(m for m in session.scene.metrics() if m['index']==1)
    assert toggle['allocation']==[260,60,200,60] and toggle['font_description']
    subprocess.run(['xdotool','mousemove',str(ox+320),str(oy+90),'click','1'],check=True,capture_output=True,timeout=5);drain()
    assert not session.scene.widgets[1].get_active()
session.scene.emit_metrics()
button = session.scene.widgets[0]; button.set_can_focus(False); drain()
subprocess.run(['import', '-window', 'root', str(args.output / 'preview.png')], check=True)
print(json.dumps({'status':'passed', 'origin':'coupled' if args.embedded else 'separate',
                  'before':push, 'after':after, 'same_window':True, 'bar_value_preserved':43,
                  'native_click':True, 'old_handlers_removed':True,
                  'toggle_native_input':args.toggle,'toggle_selection_preserved_on_replace':args.toggle,
                  'toggle_after':toggle if args.toggle else None,
                  'radio_group_exclusive':args.radio,'radio_selection_preserved_on_replace':args.radio,
                  'radio_after':radio_after if args.radio else None,
                  'check_native_input':args.check,'check_selection_preserved_on_replace':args.check,
                  'check_after':check_after if args.check else None}))
session.close()
if host: host.destroy()
