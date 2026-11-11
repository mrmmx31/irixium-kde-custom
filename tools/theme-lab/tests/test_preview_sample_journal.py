# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('sample_journal',
    Path(__file__).resolve().parents[1] / 'preview_sample_journal.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SampleJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def journal(self, origin='coupled', family='gtk2'):
        return m.SampleJournal(self.root, family, origin)

    def history(self):
        h = m.TextHistory(('ação\nSão Paulo', 4, 0, None))
        h.push(('á🙂texto novo', 2, 1, None))
        h.step(-1)
        return h

    def test_reopen_restores_utf8_selection_and_redo_branch(self):
        j = self.journal()
        self.assertEqual(j.load(), {})
        h = self.history()
        self.assertTrue(j.save({'text': h}))
        restored = self.journal().load()['text']
        self.assertEqual(restored.snapshot(), h.snapshot())
        self.assertEqual(restored.step(1), ('á🙂texto novo', 2, 1, None))
        restored.step(-1)
        restored.push(('ramo', 4, 4, None))
        self.assertIsNone(restored.step(1))
        self.assertEqual(j.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(j.lock_path.stat().st_mode & 0o777, 0o600)

    def test_history_round_trip_in_two_distinct_processes(self):
        script = """
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('journal', sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
j = m.SampleJournal(Path(sys.argv[2]), 'gtk2', 'separate')
histories = j.load()
if sys.argv[3] == 'write':
    h = m.TextHistory(('início\\nSão Paulo', 6, 0, None))
    h.push(('versão🙂', 7, 1, None)); h.step(-1)
    j.save({'text': h})
else:
    h = histories['text']
    print(json.dumps({'current': h.states[h.position], 'redo': h.step(1),
                      'undo': h.step(-1)}, ensure_ascii=False))
"""
        module = str(Path(m.__file__).resolve())
        command = [sys.executable, '-B', '-c', script, module, str(self.root)]
        subprocess.run(command + ['write'], check=True, timeout=10, capture_output=True)
        output = subprocess.run(command + ['read'], check=True, timeout=10,
                                capture_output=True, text=True)
        result = json.loads(output.stdout)
        self.assertEqual(result['current'], ['início\nSão Paulo', 6, 0, None])
        self.assertEqual(result['redo'], ['versão🙂', 7, 1, None])
        self.assertEqual(result['undo'], result['current'])

    def test_spin_partial_text_does_not_replace_committed_number(self):
        j = self.journal()
        j.load()
        h = m.TextHistory(('42', 2, 2, 42.0))
        h.push(('-', 1, 1, 42.0))
        j.save({'spin': h})
        reopened = self.journal().load()['spin']
        self.assertEqual(reopened.states[reopened.position], ('-', 1, 1, 42.0))
        self.assertEqual(reopened.step(-1), ('42', 2, 2, 42.0))

    def test_two_live_writers_refuse_conflict_without_losing_either_history(self):
        a, b = self.journal(), self.journal()
        a.load(); b.load()
        a.save({'entry': self.history()})
        saved = a.path.read_bytes()
        other = m.TextHistory(('meu texto', 9, 9, None))
        before = other.snapshot()
        with self.assertRaisesRegex(ValueError, 'Conflito'):
            b.save({'entry': other})
        self.assertEqual(a.path.read_bytes(), saved)
        self.assertEqual(other.snapshot(), before)

    def test_origins_and_families_are_independent(self):
        for family in ('gtk2', 'gtk3'):
            for origin in ('coupled', 'separate'):
                j = self.journal(origin, family)
                j.load()
                text = family + origin
                j.save({'entry': m.TextHistory((text, len(text), 0, None))})
        for family in ('gtk2', 'gtk3'):
            for origin in ('coupled', 'separate'):
                self.assertEqual(self.journal(origin, family).load()['entry'].states[0][0], family + origin)

    def test_corruption_duplicate_keys_and_wrong_origin_are_not_overwritten(self):
        j = self.journal()
        j.load(); j.save({'entry': self.history()})
        good = j.path.read_bytes()
        for bad in (b'{', good.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1'),
                    good.replace(b'"coupled"', b'"separate"'), b'\xff'):
            j.path.write_bytes(bad)
            new = self.journal()
            with self.assertRaises(ValueError): new.load()
            with self.assertRaises(ValueError): new.save({'entry': self.history()})
            self.assertEqual(j.path.read_bytes(), bad)

    def test_atomic_write_failure_preserves_previous_bytes_and_allows_retry(self):
        j = self.journal(); j.load(); h = self.history(); j.save({'entry': h})
        before = j.path.read_bytes(); h.push(('novo', 4, 4, None))
        with patch.object(m.os, 'replace', side_effect=OSError('falha artificial')):
            with self.assertRaises(OSError): j.save({'entry': h})
        self.assertEqual(j.path.read_bytes(), before)
        self.assertFalse(list(self.root.glob('.*json-*')))
        self.assertTrue(j.save({'entry': h}))
        self.assertEqual(self.journal().load()['entry'].states[-1][0], 'novo')

    def test_directory_sync_failure_is_reported_and_retry_resyncs(self):
        j = self.journal(); j.load()
        with patch.object(j, 'sync_directory', side_effect=OSError('fsync falhou')):
            with self.assertRaises(OSError): j.save({'entry': self.history()})
        with patch.object(j, 'sync_directory', wraps=j.sync_directory) as sync:
            self.assertFalse(j.save({'entry': self.history()}))
            sync.assert_called_once()

    def test_unsafe_files_and_directories_are_refused(self):
        other = self.root / 'outside'; other.write_text('preservar')
        j = self.journal(); j.path.symlink_to(other)
        with self.assertRaises(OSError): j.load()
        j.path.unlink(); j.lock_path.unlink(); j.lock_path.symlink_to(other)
        with self.assertRaises(OSError): self.journal().load()
        self.assertEqual(other.read_text(), 'preservar')
        self.root.chmod(0o755)
        with self.assertRaises(ValueError): self.journal()

    def test_invalid_selection_value_and_oversized_history_refused_before_io(self):
        h = self.history().snapshot()
        for bad in ([h['states'][0][0], True, 0, None], ['a', 2, 0, None],
                    ['a', 1, 0, float('nan')], ['a', 1, 0, 10**1000],
                    ['a\x00', 0, 0, None], ['\ud800', 0, 0, None]):
            v = dict(h, states=[bad], position=0)
            with self.assertRaises(ValueError): m.TextHistory.from_snapshot(v)
        j = self.journal(); j.load()
        with self.assertRaises(ValueError): j.save({'unknown': self.history()})
        self.assertFalse(j.path.exists())
        with self.assertRaises(ValueError): m.decode(b' ' * (m.MAX_BYTES + 1), 'gtk2', 'coupled')

    def test_lock_contention_refuses_promptly_and_noop_save_preserves_file(self):
        j = self.journal(); j.load(); h = self.history(); j.save({'entry': h})
        before = j.path.stat().st_mtime_ns
        self.assertFalse(j.save({'entry': h}))
        self.assertEqual(j.path.stat().st_mtime_ns, before)
        with j.locked():
            with self.assertRaises(BlockingIOError): self.journal().load()


if __name__ == '__main__':
    unittest.main()
