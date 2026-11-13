#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Persist real nontext GTK2 controls across processes in disposable X11."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
assert os.environ.get('T04_PRIVATE_RUNTIME_RESTART') == '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_backend import ROOT, backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_runtime_state import capture, restore, IDS
from gtk2_session import NativeSession
from preview_gtk2 import ProjectWatcher


def parent(output):
    output.mkdir(parents=True, exist_ok=True)
    data = model(); data['selected_family'] = 'gtk2'
    r = data['recipes']['gtk2']
    r.update(visible_controls=sum(1 << index for index in IDS), selected_control=1, edit_state=0)
    r['sizes'] = [[0, 0] for _ in range(16)]; r['positions'] = [[16, 16] for _ in range(16)]
    for count, index in enumerate(IDS):
        r['positions'][index] = [16 + count % 3 * 270, 16 + count // 3 * 170]
        r['sizes'][index] = [240, 120] if index == 14 else [220, 80]
    folder = output / 'generation'; folder.mkdir(mode=0o700)
    generate_scrollbar_snapshot(backend, ROOT, folder, data, ROOT / 'colors/DomainOS-SR10.4.colors')
    (output / 'model.json').write_text(json.dumps(data))
    (output / 'journals').mkdir(mode=0o700)
    reports = []
    for phase in ('write', 'read'):
        for origin in ('coupled', 'separate'):
            result = subprocess.run([sys.executable, '-B', __file__, str(output), '--child', phase, origin],
                                    capture_output=True, text=True, timeout=30)
            (output / (phase + '-' + origin + '.log')).write_text(result.stdout + result.stderr)
            if result.returncode: raise RuntimeError(result.stdout + result.stderr)
            reports.append(json.loads(result.stdout.strip().splitlines()[-1]))
    report = {'status': 'passed', 'native_processes': reports,
              'historical_fidelity_claimed': False, 'personal_session_changed': False}
    (output / 'RESULTADO.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report))


def child(output, phase, origin):
    import gi
    gi.require_version('Gtk', '2.0'); gi.require_version('Gdk', '2.0')
    from gi.repository import Gtk, Gdk
    from unittest.mock import patch
    Gtk.init([])
    def drain():
        end = time.monotonic() + .25
        while time.monotonic() < end:
            while Gtk.events_pending(): Gtk.main_iteration()
            time.sleep(.001)
    host = None
    if origin == 'coupled':
        host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
    data = json.loads((output / 'model.json').read_text())
    receipt = json.loads((output / 'generation/GTK2-SCROLLBAR-PROPOSAL.json').read_text())
    class Writer:
        def emit(self, *args, **kwargs): pass
    session = NativeSession(backend, Gtk, Gdk, ROOT, receipt['rc'], data, 'a' * 64, Writer(),
        embed_window=socket.get_id() if host else None, sample_directory=output / 'journals')
    drain(); scene = session.scene
    if phase == 'write':
        expected = capture(scene)
        coupled = origin == 'coupled'
        expected.update(toggle=coupled, check=not coupled, radio=1 if coupled else 0,
                        combo=2 if coupled else 1, progress=.375 if coupled else .625)
        for name, value in (('scale_h', 37 if coupled else 41), ('scale_v', 73 if coupled else 67),
                            ('scroll_h', 26 if coupled else 34), ('scroll_v', 61 if coupled else 57)):
            expected[name]['value'] = value
        expected['list'] = {'rows': [('linha%03d — ação %s ' % (i, origin)) + 'longa ' * 90 for i in range(60)],
                            'selected': ['32' if coupled else '12'],
                            'horizontal': 70 if coupled else 90, 'vertical': 260 if coupled else 200}
        restore(scene, expected); drain(); session.checkpoint()
        assert capture(scene) == expected
        saved = session.samples.runtime_journal.path.read_bytes()
        # Fail the runtime write while the separate textual journal remains valid.
        watcher = ProjectWatcher(session, output / 'model.json', 'a' * 64)
        with patch.object(session.samples.runtime_journal, 'save', side_effect=OSError('falha runtime artificial')):
            assert watcher.delete_event() is True
            assert 'não salv' in scene.window.get_title()
            try: session.replace(copy.deepcopy(data), 'b' * 64)
            except OSError: pass
            else: raise AssertionError('Runtime checkpoint failure ignored')
            assert session.scene is scene and capture(scene) == expected
            assert session.samples.runtime_journal.path.read_bytes() == saved
        assert watcher.delete_event() is False
        # Hidden controls retain their states through checkpoint and reappearance.
        hidden = copy.deepcopy(data)
        hidden['recipes']['gtk2']['visible_controls'] &= ~((1 << 8) | (1 << 14))
        session.replace(hidden, 'c' * 64); drain(); session.checkpoint()
        assert 'scale_h' in session.samples.runtime_states and 'list' in session.samples.runtime_states
        session.replace(copy.deepcopy(data), 'd' * 64); drain(); scene = session.scene
        assert capture(scene) == expected
        session.checkpoint()
        assert session.samples.runtime_journal.path.read_bytes() == saved
        (output / ('expected-' + origin + '.json')).write_text(json.dumps(expected, ensure_ascii=False))
    else:
        expected = json.loads((output / ('expected-' + origin + '.json')).read_text())
        # Stale controller flags must never override completed checkpoints.
        session.samples.seed_runtime(scene, 0 if expected['toggle'] else 1,
                                     0 if expected['check'] else 1, 1 - expected['radio'])
        actual = capture(scene)
        assert actual == expected, (origin, actual, expected)
        assert scene.widgets[13].get_text() == ('37.5%' if origin == 'coupled' else '62.5%')
        session.replace(copy.deepcopy(data), 'e' * 64); drain(); scene = session.scene
        assert capture(scene) == expected
        session.checkpoint()
    session.close()
    if host: host.destroy()
    print(json.dumps({'status': 'passed', 'phase': phase, 'origin': origin, 'pid': os.getpid(),
        'native_controls': sorted(expected), 'list_rows': 60,
        'hidden_rebuild_preserved': phase == 'write', 'runtime_failure_blocks_close_rebuild': phase == 'write',
        'distinct_process_restore_verified': phase == 'read'}))


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    if '--child' in sys.argv: child(output, sys.argv[-2], sys.argv[-1])
    else: parent(output)
