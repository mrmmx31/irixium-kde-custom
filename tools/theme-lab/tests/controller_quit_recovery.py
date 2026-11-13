# SPDX-License-Identifier: GPL-3.0-or-later
"""Native controller signal recovery with a deliberately invalid numeric edit."""
import json
import os
import signal
import subprocess
import time


def seed_journal(output):
    directory=output/'home/lab'
    directory.mkdir(mode=0o700)
    path=directory/'editor-journal.json'
    rows={f'artificial/context/{i}': {'entries':['',f'rascunho ação {i}'], 'position':1}
          for i in range(310)}
    path.write_text(json.dumps({'schema_version':1,'histories':rows},ensure_ascii=False))
    path.chmod(0o600)


def run(output, container, observation, edit, click, environment, wait):
    seed={f'artificial/context/{i}': {'entries':['',f'rascunho ação {i}'], 'position':1}
          for i in range(310)} if (output/'home/lab/editor-journal.json').exists() and 'artificial/context/0' in json.loads((output/'home/lab/editor-journal.json').read_text())['histories'] else {}
    wait(lambda: observation().get('controller_pid'))
    # Allow the asynchronous scheme inventory to populate the required combo.
    wait(lambda: (output / 'home/lab/working.json').exists())
    time.sleep(2)
    pid = observation()['controller_pid']
    assert pid != os.getpid() and pid > 1
    (output / 'home/reveal-spin').write_text('width')
    time.sleep(.4)
    click('controlWidth*fieldValue')
    location = subprocess.check_output(['xdotool', 'getmouselocation', '--shell'],
                                       env=environment, text=True, timeout=5)
    window = next(line.split('=', 1)[1] for line in location.splitlines()
                  if line.startswith('WINDOW='))
    subprocess.run(['xdotool', 'windowfocus', window, 'key', 'ctrl+a',
                    'type', '--clearmodifiers', 'invalid'],
                   env=environment, check=True, timeout=5)
    wait(lambda: observation().get('width_text') == 'invalid', 5)
    os.kill(pid, signal.SIGTERM)
    wait(lambda: 'Dimensões entre' in observation().get('status', ''), 10)
    assert container.poll() is None, 'Invalid edit must refuse close without losing text'
    assert observation()['width_text'] == 'invalid'
    edit('controlWidth', 221)

    def autosaved():
        data = json.loads((output / 'home/lab/working.json').read_text())
        return data['recipes'][data['selected_family']]['sizes'][0][0] == 221

    # This proves the production tick (not merely the independent probe timer)
    # continues to read edits and save after rejecting the first close.
    wait(autosaved, 5)
    os.kill(pid, signal.SIGTERM)
    wait(lambda: container.poll() is not None, 10)
    (output / "signal-exit.json").write_text(json.dumps({"returncode": container.returncode, "saved_width": 221}) + "\n")
    assert container.returncode == 0, f"Controller returned {container.returncode}"
    saved=json.loads((output/'home/lab/editor-journal.json').read_text())['histories']
    assert all(saved.get(key)==value for key,value in seed.items())
    return {'seed_histories_preserved': len(seed), 'status': 'passed', 'invalid_close_refused': True,
            'invalid_text_preserved': True, 'autosave_after_refusal': True,
            'second_signal_closed': True, 'personal_profile_exposed': False,
            'historical_fidelity_claimed': False}
