# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preview_runtime_journal import RuntimeJournal


class RuntimeJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def journal(self, origin='coupled'): return RuntimeJournal(self.root, 'gtk2', origin)
    def values(self): return {'toggle': True, 'radio': 1, 'combo': 2,
        'scroll_h': {'value': 61, 'lower': 0, 'upper': 100, 'page_size': 20},
        'list': {'rows': ['ação🙂', 'São Paulo'], 'selected': ['1'], 'horizontal': 70, 'vertical': 260}}
    def test_roundtrip_all_types_and_origins(self):
        for origin in ('coupled', 'separate'):
            j = self.journal(origin); self.assertEqual(j.load(), {})
            states = self.values(); states['toggle'] = origin == 'coupled'
            self.assertTrue(j.save(states)); self.assertFalse(j.save(states))
            self.assertEqual(self.journal(origin).load(), states)
            self.assertEqual(j.path.stat().st_mode & 0o777, 0o600)
    def test_conflict_preserves_previous_and_new_live_states(self):
        a, b = self.journal(), self.journal(); a.load(); b.load(); a.save(self.values())
        before = a.path.read_bytes(); mine = {'toggle': False}
        with self.assertRaisesRegex(ValueError, 'Conflito'): b.save(mine)
        self.assertEqual(a.path.read_bytes(), before); self.assertEqual(mine, {'toggle': False})
    def test_corruption_is_not_reset(self):
        j = self.journal(); j.load(); j.save(self.values())
        j.path.write_bytes(b'{broken')
        other = self.journal()
        with self.assertRaises(ValueError): other.load()
        with self.assertRaises(ValueError): other.save(self.values())
        self.assertEqual(j.path.read_bytes(), b'{broken')
    def test_failed_publication_preserves_old_file_and_retry(self):
        j = self.journal(); j.load(); j.save(self.values()); before = j.path.read_bytes()
        with patch.object(j, 'write_payload', side_effect=OSError('falha artificial')):
            with self.assertRaises(OSError): j.save({'toggle': False})
        self.assertEqual(j.path.read_bytes(), before)
        j.save({'toggle': False}); self.assertEqual(self.journal().load(), {'toggle': False})
    def test_invalid_state_does_not_create_file(self):
        j = self.journal(); j.load()
        with self.assertRaises(ValueError): j.save({'toggle': 1})
        self.assertFalse(j.path.exists())
    def test_wrong_origin_is_not_accepted_and_old_bytes_preserved(self):
        j = self.journal(); j.load(); j.save(self.values())
        before = j.path.read_bytes().replace(b'"coupled"', b'"separate"'); j.path.write_bytes(before)
        with self.assertRaises(ValueError): self.journal().load()
        self.assertEqual(j.path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
