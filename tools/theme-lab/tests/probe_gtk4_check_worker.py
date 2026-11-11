# SPDX-License-Identifier: GPL-3.0-or-later
"""Guarded GTK4 CheckButton worker: native state, reload and event identity."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'tools/theme-lab'), str(ROOT / 'tools/theme-lab/tests')]
import backend
from test_backend import model
from gtk4_route import command as route_command
from gtk4_embed_fixture import MotifHost
from gtk4_push_api import bind


def main():
    guards = backend.private_namespace(ROOT)
    home = Path(os.environ['HOME'])
    project_path = home / 'check-project.json'
    events = home / 'check-events'
    proposal = model()
    proposal['selected_family'] = 'gtk4'
    recipe = proposal['recipes']['gtk4']
    recipe.update(visible_controls=1 << 2, selected_control=2, edit_state=0,
                  positions=[[32, 32] for _ in range(16)],
                  sizes=[[180, 60] for _ in range(16)])
    backend.write_json(project_path, proposal)
    proposal, digest = backend.project(project_path)
    generation = backend.generate(ROOT, home / 'backend-output', proposal, digest,
                                  home / '.config/kdeglobals', family_scope=['gtk4'])
    receipt = generation['families']['gtk4']
    assert receipt['translated_controls'] == ['check'], receipt
    command = route_command(ROOT, receipt, proposal, events, home / '.config/kdeglobals')
    instance = 'e' * 32
    command += ['--preview-instance', instance]
    project_path = Path(receipt['snapshot']) / 'PROJECT.json'
    proposal, digest = backend.project(project_path)
    host = None
    if os.environ.get('T04_WORKER_ORIGIN') == 'coupled':
        host = MotifHost(ROOT / '.qa-t04-anchor-foundation/gtk4-embed-host', bind)
        command += ['--embed-window', str(host.canvas), '--host-pid', str(host.process.pid),
                    '--host-bridge', str(ROOT / '.qa-t04-anchor-foundation/gtk4-host-build/libtheme-lab-gtk4-host.so')]
    with (home / 'check-worker.log').open('w') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)

        def state():
            if process.poll() is not None:
                raise AssertionError('Owned checkbox worker exited: ' + str(process.returncode))
            path = events / 'WORKER.json'
            return json.loads(path.read_text()) if path.exists() else None

        def rows():
            return [json.loads(path.read_text()) for path in sorted(events.glob('event-*.json'))]

        def wait(predicate, timeout=45):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                state()
                value = predicate()
                if value:
                    return value
                time.sleep(.05)
            raise AssertionError('GTK4 checkbox observation deadline')

        def selected():
            return state()['check_selection'].get('2')

        def native():
            return [record for record in rows() if record['action'] == 'native']

        def pointer(*args):
            subprocess.run(['xdotool', *map(str, args)], check=True, timeout=5)

        try:
            initial = wait(state)
            window = initial['window']
            wait(lambda: any(record['action'] == 'metrics' for record in rows()))
            assert initial['embedded'] == (host is not None)
            assert selected() is False
            pointer('mousemove', '--window', window, 100, 80, 'click', 1)
            wait(lambda: len(native()) == 1 and selected() is True)
            assert native()[0]['state'] == {'clicked': True, 'selected': True, 'active': True}

            changed = copy.deepcopy(proposal)
            changed['recipes']['gtk4']['sizes'][2] = [210, 70]
            gate = home / 'color-gate'
            gate.touch()
            backend.write_json(project_path, changed)
            changed, new_digest = backend.project(project_path)
            wait(lambda: state().get('generation_pid'))
            pointer('mousemove', '--window', window, 100, 80, 'click', 1)
            wait(lambda: len(native()) == 2 and selected() is False)
            assert native()[-1]['project_sha256'] == digest
            gate.unlink()
            wait(lambda: state()['project_sha256'] == new_digest)
            wait(lambda: any(record['action'] == 'metrics' and
                             record['project_sha256'] == new_digest for record in rows()))
            assert selected() is False and state()['window'] == window and len(native()) == 2

            invalid = copy.deepcopy(changed)
            invalid['recipes']['gtk4']['visible_controls'] |= 1 << 3
            backend.write_json(project_path, invalid)
            wait(lambda: state()['error'] is not None)
            assert selected() is False and state()['project_sha256'] == new_digest
            pointer('mousemove', '--window', window, 100, 80, 'click', 1)
            wait(lambda: len(native()) == 3 and selected() is True)

            recovered = copy.deepcopy(changed)
            recovered['recipes']['gtk4']['positions'][2] = [40, 40]
            backend.write_json(project_path, recovered)
            _saved, recovered_digest = backend.project(project_path)
            wait(lambda: state()['project_sha256'] == recovered_digest and state()['error'] is None)
            assert selected() is True

            recorded = rows()
            assert all(record['control_index'] == 2 and record['control_id'] == 'check' and
                       record['preview_instance'] == instance for record in recorded)
            consumed = [{'action': record['action'], 'control': record['control_index'],
                         'state': record.get('state'), 'origin': record.get('origin')}
                        for record in recorded if record['action'] == 'native']
            assert [item['state']['active'] for item in consumed] == [True, False, True]
            process.terminate()
            assert process.wait(timeout=8) == 0
            backend.write_json(home / 'WORKER-RESULTADO.json', {
                'status': 'passed_gtk4_checkbox_worker', 'guards': guards,
                'origin': 'coupled' if host else 'separate',
                'native_clicks': 3, 'selection_survives_generation': True,
                'unsupported_preserves_scene': True, 'recovery_preserves_selection': True,
                'events_identity_verified': True, 'events': recorded,
                'event_directory': str(events), 'closed_exit_code': 0,
                'backend_route_used': True, 'public_controller_connected': False,
                'historical_fidelity_claimed': False})
        finally:
            pointer('mouseup', 1, 'keyup', 'Control_L')
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=8)
            if host:
                host.close()


if __name__ == '__main__':
    main()
