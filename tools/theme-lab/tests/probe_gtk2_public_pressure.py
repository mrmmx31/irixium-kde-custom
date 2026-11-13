#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the real GTK2 preview main in an explicitly owned Xvfb fixture."""
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

if os.environ.get('T04_PRIVATE_PRESSED_PROBE') != '1':
    raise SystemExit('Use the private GTK2 Xvfb fixture.')
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
from test_backend import model
import backend
from gtk2_generation import generate_scrollbar_snapshot
import preview_gtk2
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, GLib

output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, mode=0o700)
data = model()
data['selected_family'] = 'gtk2'
data['recipes']['gtk2'].update(visible_controls=1, selected_control=0, edit_state=1,
                             sizes=[[220, 80]] + [[0, 0] for _ in range(15)])
project = output / 'PROJECT.json'
backend.write_json(project, data)
receipt = generate_scrollbar_snapshot(backend, ROOT, output, data, ROOT/'colors/DomainOS-SR10.4.colors')
Gtk.init([])
rows = []
original = preview_gtk2.NativeSession
for embedded in (False, True):
    host = Gtk.Window() if embedded else None
    if host is not None:
        socket = Gtk.Socket()
        host.add(socket)
        host.show_all()
    sessions = []
    observations = []
    class ObservedSession(original):
        # Inherit the real static preflight; replacing the class with a mock
        # callable would accidentally mock pressure_bridge as well.
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            sessions.append(self)
            def inspect_and_close():
                button = self.scene.widgets[0]
                a = button.get_allocation()
                observations.append({'state': int(button.get_state()), 'size': [a.width, a.height]})
                self.scene.window.destroy()
                return False
            GLib.timeout_add(500, inspect_and_close)
    args = ['--root', str(ROOT), '--project', str(project), '--rc', receipt['rc'],
            '--events-dir', str(output/('coupled' if embedded else 'separate'))]
    if embedded:
        args += ['--embed-window', str(socket.get_id())]
    # Only the coordination guard is substituted: this harness already owns
    # its isolated Xvfb/bwrap. Parser, bridge, snapshot, writer and main are real.
    with patch.object(backend, 'private_namespace', return_value={'owned_fixture': True}), \
         patch.object(preview_gtk2, 'NativeSession', ObservedSession):
        code = preview_gtk2.main(args)
    assert code == 0 and observations == [{'state': 1, 'size': [220, 80]}], (code, observations)
    assert len(sessions) == 1
    assert all(demo.closed for demo in sessions[0].scene.press_demos.values())
    if host is not None:
        host.destroy()
    rows.append({'origin': 'coupled' if embedded else 'separate', 'exit_code': code,
                 'observed': observations, 'bindings_closed': True})
(output/'RESULTADO.json').write_text(json.dumps({'status': 'passed', 'rows': rows,
    'scope': 'Real preview main; owned fixture substitutes only coordination guard; not Motif controller.',
    'historical_fidelity_claimed': False}, indent=2)+'\n')
