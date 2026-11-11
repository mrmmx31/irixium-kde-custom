# SPDX-License-Identifier: GPL-3.0-or-later
"""Private native session transfer/rollback and independent toggle selection."""
import copy
import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'tools/theme-lab'), str(ROOT / 'tools/theme-lab/tests')]
import backend
from test_backend import model
from gtk4_push_api import PushAPI, bind
from gtk4_toggle_session import ToggleSession


def main():
    guards = backend.private_namespace(ROOT)
    home = Path(os.environ['HOME'])
    gtk = C.CDLL('libgtk-4.so.1'); glib = C.CDLL('libglib-2.0.so.0')
    p, i = C.c_void_p, C.c_int
    bind(gtk, 'gtk_init', None)()
    api = PushAPI(); builder = backend.load_builder(ROOT)
    source = home / '.config/kdeglobals'
    palette, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
    project = model(); recipe = project['recipes']['gtk4']
    recipe['visible_controls'] = 2
    recipe['selected_control'] = 1
    recipe['positions'] = [[16, 16] for _ in range(16)]
    recipe['sizes'] = [[0, 0] for _ in range(16)]
    recipe['positions'][1] = [32, 32]; recipe['sizes'][1] = [180, 50]
    original = copy.deepcopy(project)
    pending = bind(glib, 'g_main_context_pending', i, p)
    iterate = bind(glib, 'g_main_context_iteration', i, p, i)

    def drain():
        end = time.monotonic() + .18
        while time.monotonic() < end:
            while pending(None): iterate(None, 0)
            time.sleep(.003)

    windows = []; sessions = []; events = [[], []]; serial = 0
    def replace(session, value, **kwargs):
        nonlocal serial
        serial += 1
        folder = home / ('scene-' + str(serial))
        if os.environ.get('T04_TOGGLE_SNAPSHOT') == '1':
            from gtk4_generation import generate_snapshot, verify_snapshot
            digest = backend.sha(__import__('json').dumps(value,sort_keys=True).encode())
            generate_snapshot(ROOT, folder, value, digest, source, allow_toggle=True)
            receipt, colors = verify_snapshot(ROOT, folder, value, digest, allow_toggle=True)
            session.replace(value, colors, None, prepared=receipt, **kwargs)
        else:
            session.replace(value, palette, folder, **kwargs)
        drain()

    def selected(session):
        return bool(api.toggle_active(session.scene.widgets[1]))

    def click(n):
        window = windows[n]
        surface = bind(gtk, 'gtk_native_get_surface', p, p)(window)
        wid = bind(gtk, 'gdk_x11_surface_get_xid', C.c_ulong, p)(surface)
        subprocess.run(['xdotool', 'windowraise', str(wid), 'mousemove', '--window',
                        str(wid), '80', '50', 'click', '1'], check=True, timeout=5)
        drain()

    try:
        for n in range(2):
            window = bind(gtk, 'gtk_window_new', p)()
            windows.append(window)
            bind(gtk, 'gtk_window_set_decorated', None, p, i)(window, 0)
            bind(gtk, 'gtk_window_set_default_size', None, p, i, i)(window, 320, 180)
            session = ToggleSession(api, window, builder, lambda index, n=n: events[n].append(index))
            sessions.append(session)
            replace(session, project)
            bind(gtk, 'gtk_window_present', None, p)(window); drain()
        first, second = sessions
        click(0); assert selected(first) and not selected(second) and events == [[1], []]
        old = first.scene
        updated = copy.deepcopy(project); updated['recipes']['gtk4']['sizes'][1] = [210, 60]
        replace(first, updated)
        assert selected(first) and first.scene is not old and events == [[1], []]
        assert old.widgets == {} and old.handlers == []
        accepted = first.scene
        def fail(_candidate): raise RuntimeError('fixture transfer rejection')
        try: replace(first, project, after_transfer=fail)
        except RuntimeError as error: assert str(error) == 'fixture transfer rejection'
        else: raise AssertionError('Transfer rejection was ignored')
        assert first.scene is accepted and selected(first) and events == [[1], []]
        assert first.selection == {1: True}
        unsupported = copy.deepcopy(project); unsupported['recipes']['gtk4']['visible_controls'] = 4
        try: replace(first, unsupported)
        except ValueError as error: assert 'pending' in str(error)
        else: raise AssertionError('Unsupported control accepted')
        assert first.scene is accepted and selected(first)
        # Inspection states preserve selection and produce no native clicks.
        for state in (1, 2, 3, 0):
            inspected = copy.deepcopy(project); inspected['recipes']['gtk4']['edit_state'] = state
            replace(first, inspected)
            assert selected(first) and events == [[1], []]
        hidden = copy.deepcopy(project); hidden['recipes']['gtk4']['visible_controls'] = 0
        replace(first, hidden); assert not first.scene.widgets
        replace(first, project); assert selected(first) and events == [[1], []]
        click(1); assert selected(second) and selected(first) and events == [[1], [1]]
        click(0); assert not selected(first) and selected(second) and events == [[1, 1], [1]]
        replace(first, project); replace(second, project)
        assert not selected(first) and selected(second) and events == [[1, 1], [1]]
        assert project == original
        backend.write_json(home / 'WORKER-RESULTADO.json', {
            'status': 'passed_toggle_session', 'guards': guards,
            'toolkit': 'GTK4', 'fixture_scheme': os.environ['T04_FIXTURE_SCHEME'],
            'verified_snapshots_consumed': os.environ.get('T04_TOGGLE_SNAPSHOT') == '1',
            'physical_clicks': events, 'independent_sessions': True,
            'reload_preserved': True, 'hidden_selection_retained': True,
            'rollback_preserved_live_scene': True, 'unsupported_rejected': True,
            'inspection_did_not_emit_clicks': True, 'project_unchanged': True,
            'source_palette': origin, 'scope': 'Two standalone sessions; not coupled host or controller',
            'public_support_announced': False, 'historical_fidelity_claimed': False})
    finally:
        for session in sessions: session.close()
        for window in windows: api.destroy_window(window)


if __name__ == '__main__': main()
