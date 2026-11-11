#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise real Motif text events, Unicode and crash recovery on private Xvfb."""
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
results = {}
with tempfile.TemporaryDirectory(prefix='work-board-editing-') as name:
    p = Path(name)
    seed = json.loads((ROOT / 'docs/review/work-board-checklist.json').read_text())
    seed['items'] = seed['items'][:2]
    for i, item in enumerate(seed['items']):
        item['title'] = ['First item', 'Second item'][i]
    (p / 'seed.json').write_text(json.dumps(seed))
    cli = [str(ROOT / 'tools/work-board/build/work-board'), '--state', str(p/'state.json'),
           '--seed', str(p/'seed.json')]
    subprocess.run(cli + ['--command', 'sync'], check=True)
    note = ('Texto artificial: raciocínio, operações, coração e referências.\n'
            'Outro parágrafo com informação importante; não pode desaparecer.\n\n') * 18
    user = json.loads((p/'state.json').read_text())['items'][0]['user']
    (p/'input.json').write_text(json.dumps({**user, 'note': note}))
    subprocess.run(cli + ['--command', 'user', '--id', 'T01', '--revision', '0',
                           '--input', str(p/'input.json')], check=True)
    server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0', '1920x1080x24',
                               '-nolisten', 'tcp'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    board = None
    log = (p/'native.log').open('w')
    try:
        assert select.select([server.stdout], [], [], 5)[0], 'Xvfb failed'
        number = server.stdout.readline().decode().strip()
        assert number.isdigit(), 'Xvfb gave no display'
        env = {**os.environ, 'DISPLAY': ':' + number}

        def start():
            child = subprocess.Popen(cli, env=env, stdout=log, stderr=subprocess.STDOUT)
            time.sleep(.5)
            assert child.poll() is None, (p/'native.log').read_text()
            return child

        def x(*args):
            subprocess.run(['xdotool', *map(str, args)], env=env, check=True,
                           timeout=4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(.06)

        def click(px, py):
            x('mousemove', px, py, 'click', 1)

        def read_text():
            click(900, 450)
            x('key', 'ctrl+a')
            x('key', 'ctrl+c')
            time.sleep(.25)
            saved = json.loads((p/'state.json.drafts.json').read_text())
            selected = saved['selected']
            if selected in saved['drafts']:
                value = saved['drafts'][selected]['user']['note']
            else:
                value = next(item['user']['note'] for item in
                             json.loads((p/'state.json').read_text())['items']
                             if item['id'] == selected)
            if value:
                copied = subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'],
                                                  env=env, timeout=3).decode()
                assert copied == value, (repr(copied[-150:]), repr(value[-150:]))
            x('key', 'ctrl+End')
            return value

        def clipboard(value):
            subprocess.run(['xclip', '-selection', 'clipboard', '-i'], input=value.encode(),
                           env=env, check=True, timeout=3, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

        def journal():
            time.sleep(.3)
            return json.loads((p/'state.json.drafts.json').read_text())

        board = start()
        assert read_text() == note
        x('type', '!')
        x('key', 'ctrl+z')
        assert read_text() == note
        x('key', 'ctrl+y')
        assert read_text() == note + '!'
        x('key', 'ctrl+z')
        x('key', 'ctrl+shift+z')
        assert read_text() == note + '!'
        results['unicode_multiline_undo_redo_shortcuts'] = True

        x('type', '12')
        x('key', 'ctrl+z')
        x('key', 'ctrl+z')
        assert read_text() == note + '!'
        x('key', 'ctrl+y')
        x('key', 'ctrl+y')
        assert read_text() == note + '!12'
        results['multi_step_history'] = True

        x('key', 'ctrl+a')
        x('key', 'ctrl+x')
        assert read_text() == ''
        assert subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'],
                                       env=env, timeout=3).decode() == note + '!12'
        x('key', 'ctrl+z')
        assert read_text() == note + '!12'
        replacement = 'Nova proposta — ação não autorizada.\nSegunda linha com ç e ã.'
        clipboard(replacement)
        x('key', 'ctrl+a')
        x('key', 'ctrl+v')
        actual = read_text()
        assert actual == replacement, repr(actual[-150:])
        x('key', 'ctrl+z')
        assert read_text() == note + '!12'
        results['copy_cut_paste_select_all_and_reversible_replacement'] = True

        click(218, 27)  # Reload: remains local draft.
        assert read_text() == note + '!12'
        click(160, 140)
        click(900, 450)
        x('type', 'Second item stays separate')
        click(160, 73)
        click(900, 450)
        x('key', 'ctrl+z')
        assert read_text() == note + '!1'
        x('key', 'ctrl+y')
        assert read_text() == note + '!12'
        results['history_survives_reload_and_item_switch'] = True

        click(330, 27)  # Save keeps undo history.
        click(900, 450)
        x('key', 'ctrl+End')
        x('type', ' preserved draft')
        current = note + '!12 preserved draft'
        assert read_text() == current
        click(455, 27)  # Return to saved, explicitly reversible.
        assert read_text() == note + '!12'
        x('key', 'ctrl+z')
        assert read_text() == current
        results['save_retains_history_and_return_to_saved_is_reversible'] = True

        # Native context menu, no default Motif virtual keyboard assumptions.
        x('mousemove', 900, 450, 'click', 3)
        x('mousemove', 940, 463, 'click', 1)  # Undo first row.
        actual = read_text()
        assert actual == current[:-1], repr(actual[-100:])
        x('key', 'ctrl+y')
        assert read_text() == current
        results['context_menu_undo'] = True

        click(410, 901)
        x('type', 'Title draft')
        x('key', 'ctrl+z')
        x('key', 'ctrl+y')
        j = journal()
        assert j['title'] == 'Title draft'
        assert j['drafts']['T01']['user']['note'] == current
        assert j['drafts']['T02']['user']['note'] == 'Second item stays separate'
        assert all(not item['user']['authorized'] for item in
                   json.loads((p/'state.json').read_text())['items'])
        assert (p/'state.json.drafts.json').stat().st_mode & 0o777 == 0o600
        results['private_autosave_is_separate_from_answers_and_authorizations'] = True
        other = subprocess.run(cli, env=env, capture_output=True, timeout=3)
        assert other.returncode != 0
        results['second_editor_cannot_overwrite_journal'] = True

        board.kill()
        board.wait(timeout=3)
        board = start()
        assert read_text() == current
        x('key', 'ctrl+z')
        assert read_text() == current[:-1]
        x('key', 'ctrl+y')
        assert read_text() == current
        click(160, 140)
        assert read_text() == 'Second item stays separate'
        assert journal()['title'] == 'Title draft'
        results['crash_restores_multiple_drafts_title_and_undo_redo'] = True

        # Failure to write a checkpoint must not permit discarding the draft.
        sidecar = p/'state.json.drafts.json'
        sidecar.rename(p/'journal-before-failure.json')
        sidecar.symlink_to(p/'journal-before-failure.json')
        click(455, 27)
        assert read_text() == 'Second item stays separate'
        assert sidecar.is_symlink()
        results['failed_checkpoint_prevents_destructive_action'] = True
        if options.evidence:
            options.evidence.mkdir(parents=True, exist_ok=True)
            (options.evidence/'editing-result.json').write_text(json.dumps(results, indent=2)+'\n')
            (options.evidence/'editing.log').write_text((p/'native.log').read_text())
        print(json.dumps(results, indent=2))
    finally:
        for child in (board, server):
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
        log.close()
