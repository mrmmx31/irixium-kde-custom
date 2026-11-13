#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 runtime-state capture/restore against actual widgets in private X11."""
import copy
import json
import os
from pathlib import Path
import sys
import time
assert os.environ.get('T04_PRIVATE_RUNTIME_STATE') == '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_backend import ROOT, backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from gtk2_runtime_state import capture, restore, IDS
import gi
gi.require_version('Gtk', '2.0'); gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk

Gtk.init([])
output = Path(sys.argv[1]).resolve(); output.mkdir(parents=True, exist_ok=True)
data = model(); data['selected_family'] = 'gtk2'
r = data['recipes']['gtk2']
r.update(visible_controls=sum(1 << index for index in IDS), selected_control=1, edit_state=0)
r['sizes'] = [[0, 0] for _ in range(16)]
r['positions'] = [[16, 16] for _ in range(16)]
for count, index in enumerate(IDS):
    r['positions'][index] = [16 + (count % 3) * 270, 16 + (count // 3) * 170]
    r['sizes'][index] = [240, 120] if index == 14 else [220, 80]
(output / 'generation').mkdir(mode=0o700)
receipt = generate_scrollbar_snapshot(backend, ROOT, output / 'generation', data,
                                      ROOT / 'colors/DomainOS-SR10.4.colors')
class Writer:
    def emit(self, *args, **kwargs): pass

def drain():
    end = time.monotonic() + .25
    while time.monotonic() < end:
        while Gtk.events_pending(): Gtk.main_iteration()
        time.sleep(.001)

reports = []
for origin in ('coupled', 'separate'):
    host = None
    if origin == 'coupled':
        host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
    session = NativeSession(backend, Gtk, Gdk, ROOT, receipt['rc'], data, 'a' * 64, Writer(),
                            embed_window=socket.get_id() if host else None)
    drain(); scene = session.scene
    snapshot = capture(scene)
    snapshot.update(toggle=True, check=True, radio=1, combo=2, progress=.375)
    for name, value in (('scale_h', 37), ('scale_v', 73), ('scroll_h', 26), ('scroll_v', 61)):
        snapshot[name]['value'] = value
    snapshot['list'] = {'rows': [('linha%03d — ação ' % i) + 'longa ' * 90 for i in range(60)],
                        'selected': ['32'], 'horizontal': 70, 'vertical': 260}
    restore(scene, snapshot); drain()
    measured = capture(scene)
    assert measured == snapshot, (origin, measured, snapshot)
    assert scene.widgets[13].get_text() == '37.5%'
    # Reject native range mismatch before changing even an earlier checkbox.
    invalid = copy.deepcopy(snapshot); invalid['toggle'] = False
    invalid['scroll_h']['page_size'] = 10
    try: restore(scene, invalid)
    except ValueError: pass
    else: raise AssertionError('Native bounds mismatch accepted')
    assert capture(scene) == snapshot
    # A partial scene capture conserves hidden control values by stable ID.
    prior = capture(scene)
    masked = copy.copy(scene); masked.widgets = {1: scene.widgets[1]}
    scene.widgets[1].set_active(False)
    kept = capture(masked, prior)
    assert kept['toggle'] is False
    for key in prior:
        if key != 'toggle': assert kept[key] == prior[key]
    restore(scene, snapshot); drain()
    assert capture(scene) == snapshot
    reports.append({'origin': origin, 'controls': sorted(snapshot),
                    'list_rows': len(snapshot['list']['rows']),
                    'list_scroll': [measured['list']['horizontal'], measured['list']['vertical']],
                    'hidden_state_preserved': True, 'preflight_no_partial_change': True})
    session.close()
    if host: host.destroy()
report = {'status': 'passed', 'native_origins': reports,
          'storage_or_cross_process_restore_verified': False,
          'historical_fidelity_claimed': False, 'personal_session_changed': False}
(output / 'RESULTADO.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report))
