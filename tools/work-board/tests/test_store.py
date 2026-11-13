#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Concurrency/persistence contract exercised through the same C model as the UI."""
import copy
import fcntl
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BINARY = ROOT / 'tools/work-board/build/work-board'


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='work-board-test-')
        self.folder = Path(self.temp.name)
        self.state = self.folder / 'respostas.json'
        self.seed = self.folder / 'checklist.json'
        self.definition = json.loads((ROOT / 'docs/review/work-board-checklist.json').read_text())
        self.definition['items'] = self.definition['items'][:2]
        self.seed.write_text(json.dumps(self.definition))
        self.run_cli('sync')

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, command, *args, ok=True):
        result = subprocess.run([str(BINARY), '--state', str(self.state), '--seed', str(self.seed),
                                 '--command', command, *map(str, args)], capture_output=True,
                                text=True, timeout=3)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def items(self):
        return {o['id']: o for o in json.loads(self.state.read_text())['items']}

    def save(self, id='T01', revision=0, **changes):
        user = copy.deepcopy(self.items()[id]['user'])
        user.update(changes)
        file = self.folder / 'input.json'
        file.write_text(json.dumps(user))
        return self.run_cli('user', '--id', id, '--revision', revision, '--input', file)

    def test_initial_authorizations_are_false(self):
        self.assertTrue(all(not o['user']['authorized'] for o in self.items().values()))

    def test_save_one_preserves_other(self):
        other = copy.deepcopy(self.items()['T02'])
        self.save(note='Uma resposta agora. As outras depois.', authorized=True)
        one = self.items()['T01']
        self.assertEqual(other, self.items()['T02'])
        self.assertEqual(one['user']['revision'], 1)
        self.assertTrue(one['user']['responded_at'].endswith('Z'))
        self.assertEqual(one['user']['authorized_definition'], one['definition_sha256'])
        self.assertTrue(list(self.folder.glob('respostas.json.history.*')))

    def test_assistant_read_keeps_text_authorization_and_time(self):
        self.save(note='Não apagar.', authorized=True, level='expert')
        before = self.items()['T01']['user']
        self.run_cli('reply', '--id', 'T01', '--revision', 1, '--reply', 'Explicação direta.')
        after = self.items()['T01']
        self.assertEqual(before, after['user'])
        self.assertEqual(after['assistant']['ack_revision'], 1)
        self.assertTrue(after['assistant']['read_at'])

    def test_stale_ack_does_not_clear_new_response(self):
        self.save(note='Primeira')
        self.save(revision=1, note='Segunda')
        before = self.state.read_bytes()
        self.run_cli('ack', '--id', 'T01', '--revision', 1, ok=False)
        self.assertEqual(before, self.state.read_bytes())
        self.assertEqual(self.items()['T01']['assistant']['ack_revision'], 0)

    def test_agent_reply_is_not_overwritten_by_user_save(self):
        self.save(note='Primeira')
        self.run_cli('reply', '--id', 'T01', '--revision', 1, '--reply', 'Resposta simultânea')
        self.save(revision=1, note='Segunda', authorized=True)
        self.assertEqual(self.items()['T01']['assistant']['reply'], 'Resposta simultânea')

    def test_stale_user_save_preserves_current(self):
        self.save(note='Já foi atualizado')
        file = self.folder / 'input.json'
        file.write_text(json.dumps({**self.items()['T01']['user'], 'note':'antigo'}))
        before = self.state.read_bytes()
        self.run_cli('user', '--id', 'T01', '--revision', 0, '--input', file, ok=False)
        self.assertEqual(before, self.state.read_bytes())

    def test_no_change_does_not_change_timestamp(self):
        self.save(note='Igual')
        before = self.state.read_bytes()
        self.save(revision=1)
        self.assertEqual(before, self.state.read_bytes())

    def test_definition_change_revokes_authorization_preserves_text(self):
        self.save(note='Escopo anterior', authorized=True)
        self.definition['items'][0]['scope'] += ' Nova ação.'
        self.seed.write_text(json.dumps(self.definition))
        self.run_cli('sync')
        item = self.items()['T01']
        self.assertFalse(item['user']['authorized'])
        self.assertEqual(item['user']['note'], 'Escopo anterior')
        self.assertEqual(item['user']['revision'], 2)
        self.assertTrue(item['scope_changed_at'])

    def test_execution_status_requires_current_authorization(self):
        self.run_cli('reply', '--id', 'T01', '--revision', 0, '--status', 'running',
                     '--reply', 'Não deve iniciar.', ok=False)
        self.save(authorized=True)
        self.run_cli('reply', '--id', 'T01', '--revision', 1, '--status', 'running',
                     '--reply', 'Autorização verificada.')

    def test_question_and_instruction_are_separate_and_anchored(self):
        q = self.run_cli('insert', '--after', 'T01', '--kind', 'question', '--title', 'Dúvida').stdout.strip()
        i = self.run_cli('insert', '--after', 'T01', '--title', 'Proposta').stdout.strip()
        self.assertEqual(self.items()[q]['type'], 'question')
        self.assertEqual(self.items()[i]['after'], 'T01')
        file = self.folder / 'input.json'
        file.write_text(json.dumps({**self.items()[q]['user'], 'authorized':True}))
        self.run_cli('user', '--id', q, '--revision', 0, '--input', file, ok=False)

    def test_locked_file_does_not_block_ui(self):
        with open(str(self.state)+'.lock', 'r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.run_cli('sync', ok=False)

    def test_corrupt_json_and_symlink_are_preserved(self):
        self.state.write_text('{broken')
        self.run_cli('sync', ok=False)
        self.assertEqual(self.state.read_text(), '{broken')
        self.state.unlink()
        target = self.folder / 'target'
        target.write_text('preserve')
        self.state.symlink_to(target)
        self.run_cli('sync', ok=False)
        self.assertEqual(target.read_text(), 'preserve')

    def test_invalid_types_and_trailing_json_are_rejected(self):
        file = self.folder / 'input.json'
        user = self.items()['T01']['user']
        file.write_text(json.dumps({**user,'authorized':'true'}))
        self.run_cli('user', '--id', 'T01', '--revision', 0, '--input', file, ok=False)
        file.write_text(json.dumps(user)+' {}')
        self.run_cli('user', '--id', 'T01', '--revision', 0, '--input', file, ok=False)


if __name__ == '__main__':
    unittest.main()
