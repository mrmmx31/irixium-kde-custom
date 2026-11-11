# SPDX-License-Identifier: GPL-3.0-or-later
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from preview_event_writer import EventWriter
ROOT = Path(__file__).resolve().parents[3]


class WriterTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / '.qa-i167-gtk2/writer-tests'
        base.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)
        self.writer = EventWriter(self.path, ROOT, family='gtk2')

    def test_utf8_identity_permissions_and_separate_event_files(self):
        for value in ('seleção', 'posição'):
            self.writer.emit('native', 10, 'a' * 64, state={'note': value})
        files = sorted(self.path.glob('event-*.json'))
        self.assertEqual(len(files), 2)
        self.assertEqual({json.loads(p.read_text())['state']['note'] for p in files}, {'seleção', 'posição'})
        for p in files:
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            data = json.loads(p.read_text())
            self.assertEqual((data['family'], data['control_id']), ('gtk2', 'scroll_h'))

    def test_instance_identity_is_validated_and_reserved(self):
        writer = EventWriter(self.path, ROOT, instance_id='b' * 32)
        writer.emit('select', 0, 'a' * 64)
        event = json.loads(next(self.path.glob('event-*.json')).read_text())
        self.assertEqual(event['preview_instance'], 'b' * 32)
        with self.assertRaises(ValueError):
            writer.emit('select', 0, 'a' * 64, preview_instance='c' * 32)
        for invalid in ('short', 'G' * 32, 'a' * 33, 17):
            with self.assertRaises(ValueError): EventWriter(self.path, ROOT, instance_id=invalid)

    def test_gtk4_identity_and_action_are_written(self):
        writer=EventWriter(self.path,ROOT,family='gtk4',instance_id='c'*32)
        writer.emit('native',0,'a'*64,state={'clicked':True})
        event=json.loads(next(self.path.glob('event-*.json')).read_text())
        self.assertEqual((event['family'],event['control_id']),('gtk4','push'))
        self.assertEqual(event['preview_instance'],'c'*32)

    def test_reserved_fields_and_oversize_do_not_write(self):
        for fields in ({'family': 'gtk3'}, {'control_id': 'push'}, {'state': 'x' * 17000}):
            with self.assertRaises(ValueError): self.writer.emit('native', 10, 'a' * 64, **fields)
        self.assertEqual(list(self.path.iterdir()), [])

    def test_failed_replace_cleans_temporary_and_preserves_prior_event(self):
        self.writer.emit('select', 10, 'a' * 64)
        original = {p.name: p.read_bytes() for p in self.path.iterdir()}
        with patch('preview_event_writer.os.replace', side_effect=OSError('artificial failure')):
            with self.assertRaises(OSError): self.writer.emit('select', 11, 'a' * 64)
        self.assertEqual({p.name: p.read_bytes() for p in self.path.iterdir()}, original)


if __name__ == '__main__': unittest.main()
