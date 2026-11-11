#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real mouse/keyboard smoke test on our own Xvfb and artificial responses."""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--evidence', type=Path)
options = parser.parse_args()

with tempfile.TemporaryDirectory(prefix='work-board-native-') as name:
    folder = Path(name)
    seed = json.loads((ROOT / 'docs/review/work-board-checklist.json').read_text())
    seed['items'] = seed['items'][:2]
    seed['items'][0]['title'] = 'First item'
    seed['items'][1]['title'] = 'Second item'
    (folder / 'seed.json').write_text(json.dumps(seed))
    cli = [str(ROOT / 'tools/work-board/build/work-board'), '--state', str(folder / 'state.json'),
           '--seed', str(folder / 'seed.json')]
    server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0', '1920x1080x24',
                               '-nolisten', 'tcp'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    board = None
    try:
        if not select.select([server.stdout], [], [], 5)[0]:
            raise RuntimeError('Xvfb did not start')
        env = {**os.environ, 'DISPLAY': ':' + server.stdout.readline().decode().strip()}
        args = cli[:]
        helper = ROOT / 'tools/theme-lab/build/theme-lab-colors'
        config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'kdeglobals'
        if helper.is_file() and config.is_file():
            args += ['--colors-helper', str(helper), '--kde-config', str(config)]
        with (folder / 'ui.log').open('w') as log:
            board = subprocess.Popen(args, env=env, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(.6)

        def x(*arguments):
            subprocess.run(['xdotool', *map(str, arguments)], env=env, check=True,
                           timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def click(px, py):
            x('mousemove', px, py, 'click', 1)
            time.sleep(.15)

        def state():
            return {o['id']: o for o in json.loads((folder / 'state.json').read_text())['items']}

        click(900, 450)
        x('type', 'Partial response')
        click(330, 27)
        assert state()['T01']['user']['note'] == 'Partial response'
        assert state()['T02']['user']['revision'] == 0
        click(900, 450)
        x('key', 'ctrl+End')
        x('type', ' -- draft')
        subprocess.run(cli + ['--command', 'reply', '--id', 'T01', '--revision', '1',
                               '--reply', 'Separate assistant reply'], check=True)
        click(218, 27)
        click(330, 27)
        assert state()['T01']['user']['note'] == 'Partial response -- draft'
        assert state()['T01']['assistant']['reply'] == 'Separate assistant reply'
        assert state()['T01']['user']['revision'] == 2
        assert state()['T01']['assistant']['ack_revision'] == 1
        click(160, 140)
        click(900, 450)
        x('type', 'Draft of second item')
        click(160, 73)
        click(218, 27)
        click(160, 140)
        click(330, 27)
        assert state()['T02']['user']['note'] == 'Draft of second item'
        click(130, 110)
        click(410, 901)
        x('type', 'Inserted instruction')
        click(1140, 901)
        instructions = [o for o in state().values() if o['type'] == 'instruction']
        assert len(instructions) == 1 and instructions[0]['after'] == 'T01'
        assert not instructions[0]['user']['authorized']
        click(900, 450)
        x('type', 'Explicit scope for proposal')
        click(330, 27)
        assert state()[instructions[0]['id']]['user']['note'] == 'Explicit scope for proposal'
        # Use actual popup list selection to show the anchored ordering.
        click(158, 27)
        click(60, 129)
        assert board.poll() is None
        result = dict(partial_save=True, reload_preserves_current_draft=True,
                      reload_preserves_other_draft=True, assistant_reply_preserved=True,
                      newer_response_unread=True, anchored_instruction=True,
                      instruction_starts_unauthorized=True, native_save_reload_responsive=True)
        if options.evidence:
            options.evidence.mkdir(parents=True, exist_ok=True)
            subprocess.run(['import', '-display', env['DISPLAY'], '-window', 'root',
                            str(options.evidence / 'native.png')], check=True, timeout=5)
            (options.evidence / 'native-result.json').write_text(json.dumps(result, indent=2)+'\n')
            (options.evidence / 'native.log').write_text((folder / 'ui.log').read_text())
        print(json.dumps(result, indent=2))
    finally:
        for child in (board, server):
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
