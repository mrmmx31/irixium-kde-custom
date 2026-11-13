#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Two-process GTK2 recovery probe; run only inside disposable X11 namespace."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
assert os.environ.get('T04_PRIVATE_SAMPLE_RESTART') == '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtk2_session import NativeSession
from gtk2_generation import generate_scrollbar_snapshot
from preview_gtk2 import ProjectWatcher
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_backend import ROOT, backend, model


def parent(output):
    output.mkdir(parents=True, exist_ok=True)
    data = model(); data['selected_family'] = 'gtk2'
    r = data['recipes']['gtk2']
    r.update(visible_controls=(1 << 4) | (1 << 6) | (1 << 7), selected_control=4, edit_state=0)
    r['sizes'] = [[0, 0] for _ in range(16)]
    r['positions'] = [[16, 16] for _ in range(16)]
    for index, y, size in ((4, 16, [300, 44]), (6, 80, [300, 44]), (7, 145, [460, 160])):
        r['sizes'][index] = size; r['positions'][index] = [16, y]
    generation = output / 'generation'
    generation.mkdir(mode=0o700)
    receipt = generate_scrollbar_snapshot(backend, ROOT, generation, data,
                                          ROOT / 'colors/DomainOS-SR10.4.colors')
    (output / 'model.json').write_text(json.dumps(data))
    journals = output / 'journals'; journals.mkdir(mode=0o700)
    reports = []
    for phase in ('write', 'read'):
        for origin in ('coupled', 'separate'):
            command = [sys.executable, '-B', __file__, str(output), '--child', phase, origin]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            (output / (phase + '-' + origin + '.log')).write_text(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
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
        end = time.monotonic() + .20
        while time.monotonic() < end:
            while Gtk.events_pending(): Gtk.main_iteration()
            time.sleep(.001)
    host = None
    if origin == 'coupled':
        host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
    data = json.loads((output / 'model.json').read_text())
    rc = output / 'generation/gtk2/snapshot.gtkrc'
    # Receipt records the exact generated path.
    receipt = json.loads((output / 'generation/GTK2-SCROLLBAR-PROPOSAL.json').read_text())
    rc = Path(receipt['rc'])
    class Writer:
        def emit(self, *args, **kwargs): pass
    session = NativeSession(backend, Gtk, Gdk, ROOT, rc, data, 'a' * 64, Writer(),
        embed_window=socket.get_id() if host else None, sample_directory=output / 'journals')
    drain()
    scene = session.scene
    target = host if host else scene.window
    title = 'T04 sample restart ' + origin
    target.set_title(title); drain()
    subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '^' + title + '$',
                    'windowfocus'], check=True, timeout=5)
    drain()
    def key(value):
        subprocess.run(['xdotool', 'key', '--clearmodifiers', value], check=True, timeout=5)
        drain()
    values = {4: ('ação — ' + origin, 4, 4, None),
              7: ('São Paulo\nsegunda linha — ' + origin, 9, 2, None),
              6: ('-', 1, 1, 42.0)}
    extras = {4: ('outra entrada', 5, 5, None), 7: ('outro parágrafo', 5, 5, None),
              6: ('63', 2, 2, 42.0)}
    if phase == 'write':
        for index, state in values.items():
            editor = scene.text_editors[index]
            editor.restore(state); editor.history.push(editor.read())
            editor.restore(extras[index]); editor.history.push(editor.read())
            editor.step(-1)
        drain(); session.checkpoint()
        for index, state in values.items():
            assert scene.text_editors[index].read() == state, (index, scene.text_editors[index].read(), state)
        # Failure before rebuild/close retains the actual native fields/window.
        watcher = ProjectWatcher(session, output / 'model.json', 'a' * 64)
        with patch.object(session.samples.journal, 'save', side_effect=OSError('falha artificial')):
            assert watcher.delete_event() is True
            assert 'não salv' in scene.window.get_title()
            previous = session.scene
            try: session.replace(copy.deepcopy(data), 'b' * 64)
            except OSError: pass
            else: raise AssertionError('Rebuild ignored failed checkpoint')
            assert session.scene is previous
            for index, state in values.items(): assert scene.text_editors[index].read() == state, (index, scene.text_editors[index].read(), state)
        assert watcher.delete_event() is False
        saved = session.samples.journal.path.read_bytes()
        session.replace(copy.deepcopy(data), 'c' * 64)
        scene = session.scene; drain()
        for index, state in values.items(): assert scene.text_editors[index].read() == state, (index, scene.text_editors[index].read(), state)
        assert session.samples.journal.path.read_bytes() == saved
    else:
        # Assert selection/partial value immediately after native realization.
        for index, state in values.items():
            assert scene.text_editors[index].read() == state, (index, scene.text_editors[index].read(), state)
        for index in (4, 7, 6):
            editor = scene.text_editors[index]
            editor.widget.grab_focus(); drain()
            key('ctrl+y')
            assert editor.read()[0] == extras[index][0], (index, editor.read())
            key('ctrl+z')
            assert editor.read()[0] == values[index][0], (index, editor.read())
            key('ctrl+shift+z')
            assert editor.read()[0] == extras[index][0]
            key('ctrl+z')
            assert editor.read()[0] == values[index][0]
            # Restore exact selection in the live current state for subsequent checkpoint.
            editor.restore(values[index]); editor.history.remember_selection(editor.read())
        session.checkpoint()
    session.close()
    if host: host.destroy()
    print(json.dumps({'status': 'passed', 'phase': phase, 'origin': origin,
                      'pid': os.getpid(), 'controls': ['entry', 'text', 'spin'],
                      'native_keyboard_redo_undo': phase == 'read',
                      'failed_checkpoint_blocks_close_and_rebuild': phase == 'write'}))


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    if '--child' in sys.argv: child(output, sys.argv[-2], sys.argv[-1])
    else: parent(output)
