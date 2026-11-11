# SPDX-License-Identifier: GPL-3.0-or-later
"""Native editor remains usable while an actual child exceeds its deadline."""
import json
import os
from pathlib import Path
import subprocess
import time


def run(output, observation, click, wait, environment):
    working = output / 'home/lab/working.json'; scene = output / 'home/lab/scene.json'
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)
    gate = output / 'home/generate-gate'
    (output / 'home/reveal-spin').write_text('width')
    wait(lambda: not (output / 'home/reveal-spin').exists(), 5)

    def key(*args):
        subprocess.run(['xdotool', 'key', '--clearmodifiers', *args], env=environment, check=True, timeout=5)

    def edit(value):
        click('controlWidth*fieldValue'); key('ctrl+a')
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', value],
                       env=environment, check=True, timeout=5)
        wait(lambda: observation().get('width_text') == value, 5)
        wait(lambda: json.loads(working.read_text())['recipes']['gtk3']['sizes'][0][0] == int(value), 10)

    edit('222')
    gate.with_suffix('.arm').touch(mode=0o600)
    started = time.monotonic(); click('apply')
    wait(lambda: gate.with_suffix('.ready').exists(), 15)
    pid = int(gate.with_suffix('.ready').read_text())
    assert pid > 1 and Path(f'/proc/{pid}').stat().st_uid == os.getuid()
    applied = scene.read_bytes()
    assert json.loads(applied)['recipes']['gtk3']['sizes'][0] == [222, 80]
    edit('223')
    key('ctrl+z'); wait(lambda: observation().get('width_text') == '22', 5)
    key('ctrl+y'); wait(lambda: observation().get('width_text') == '223', 5)
    wait(lambda: json.loads(working.read_text())['recipes']['gtk3']['sizes'][0] == [223, 80], 10)
    assert Path(f'/proc/{pid}').exists(), 'Deadline child disappeared before editor input proof'
    pending = json.loads(working.read_text())
    wait(lambda: observation().get('status', '').startswith('Tempo limite excedido'), 40)
    elapsed = time.monotonic() - started
    assert 29 <= elapsed < 40, f'Expected real 30-second deadline, got {elapsed}'
    wait(lambda: not Path(f'/proc/{pid}').exists(), 5)
    current = json.loads(working.read_text()); current.pop('exported_at', None)
    pending.pop('exported_at', None)
    assert current == pending and scene.read_bytes() == applied
    click('apply')
    wait(lambda: observation().get('native_push_allocation') == [223, 80], 90)
    assert json.loads(scene.read_text())['recipes']['gtk3']['sizes'][0] == [223, 80]
    return {'status': 'passed', 'scope': 'Real controller deadline on a stalled test-only pre-exec generation child; actual native typing/Undo/Redo while child lives; proposal/scene preserved on timeout and real GTK3 generation recovers by Apply. No computation/other-toolkit/historical fidelity claim.',
            'deadline_elapsed_seconds': elapsed, 'timed_out_owned_pid': pid,
            'editor_input_undo_redo_while_waiting': True, 'recovered_allocation': [223, 80]}
