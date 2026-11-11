# SPDX-License-Identifier: GPL-3.0-or-later
"""Crash only identified disposable GTK3 children and verify editor recovery."""
import json
import os
from pathlib import Path
import signal
import subprocess


def run(output, observation, click, wait, environment):
    working = output / 'home/lab/working.json'
    scene = output / 'home/lab/scene.json'
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)

    def crash(embedded):
        candidates = []
        for path in Path('/proc').iterdir():
            if not path.name.isdigit(): continue
            try:
                argv = (path / 'cmdline').read_bytes().split(b'\0')
                env = (path / 'environ').read_bytes().split(b'\0')
                if (path.stat().st_uid == os.getuid() and
                        b'/fixture/root/tools/theme-lab/preview_gtk.py' in argv and
                        (b'--embed-window' in argv) == embedded and
                        ('DISPLAY=' + environment['DISPLAY']).encode() in env and
                        b'TL_SPIN_PROBE=/home/domainos-test/probe.json' in env):
                    candidates.append((int(path.name), argv, env))
            except (OSError, PermissionError): pass
        assert len(candidates) == 1, f'Expected one owned GTK3 child, found {len(candidates)}'
        pid, argv, env = candidates[0]
        descriptor = os.pidfd_open(pid)
        try:
            assert (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0') == argv
            assert (Path('/proc') / str(pid) / 'environ').read_bytes().split(b'\0') == env
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
        finally: os.close(descriptor)
        wait(lambda: observation().get('status', '').startswith('Prévia indisponível'), 10)
        return pid

    before = working.read_bytes(); applied = scene.read_bytes()
    coupled_pid = crash(True)
    assert working.read_bytes() == before and scene.read_bytes() == applied
    wait(lambda: not any(x['separate'] == 0 for x in observation().get('native_controls', [])), 5)
    # Actual native text input proves the editor still processes events.
    (output / 'home/reveal-spin').write_text('width')
    wait(lambda: not (output / 'home/reveal-spin').exists(), 5)
    click('controlWidth*fieldValue')
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'], env=environment, check=True, timeout=5)
    subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', '222'], env=environment, check=True, timeout=5)
    wait(lambda: json.loads(working.read_text())['recipes']['gtk3']['sizes'][0] == [222, 80], 10)
    assert scene.read_bytes() == applied
    click('apply')
    wait(lambda: observation().get('native_push_allocation') == [222, 80], 90)
    (output / 'home/reveal-spin').write_text('separate')
    wait(lambda: not (output / 'home/reveal-spin').exists(), 5)
    click('separatePreview')
    wait(lambda: observation().get('native_push_allocation') == [222, 80] and
         any(x['separate'] == 1 for x in observation().get('native_controls', [])), 30)
    before = working.read_bytes(); applied = scene.read_bytes()
    separate_pid = crash(False)
    # The checkbox is a saved user preference, not merely the child's alive
    # state. A crash must stop retrying without silently discarding the choice.
    wait(lambda: observation().get('separate_preview_checked') is True, 5)
    assert working.read_bytes() == before and scene.read_bytes() == applied
    assert observation()['native_push_allocation'] == [222, 80]
    wait(lambda: not any(x['separate'] == 1 for x in observation().get('native_controls', [])), 5)
    click('apply')
    wait(lambda: observation().get('native_push_allocation') == [222, 80] and
         any(x['separate'] == 1 for x in observation().get('native_controls', [])), 90)
    return {'status': 'passed', 'scope': 'Owned native GTK3 coupled and separate child crashes; model/scene preserved; editor native input and explicit Apply recover; dead preview metrics removed. No timeout or historical fidelity claim.',
            'crashed_owned_pids': [coupled_pid, separate_pid], 'editor_recovered': True,
            'separate_preview_preference_preserved': True,
            'separate_preview_recovered_by_apply': True}
