# SPDX-License-Identifier: GPL-3.0-or-later
"""Filesystem failure injection and atomic no-replace publication, no GUI."""
import errno
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from artifact_delta import package_files
from artifact_reconstruction import reconstruct
from private_publication import publish_directory


class PublicationTests(unittest.TestCase):
    def test_complete_result_appears_only_after_writer_finishes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / 'new/result'
            def writer(stage):
                self.assertFalse(target.exists())
                (stage / 'artifact').write_bytes(b'complete')
                (stage / 'receipt').write_bytes(b'checked')
                self.assertFalse(target.exists())
                return {'complete': True}
            self.assertEqual(publish_directory(target, writer), {'complete': True})
            self.assertEqual((target / 'artifact').read_bytes(), b'complete')
            self.assertEqual((target / 'receipt').read_bytes(), b'checked')
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_write_failure_removes_stage_without_publishing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / 'result'
            def writer(stage):
                (stage / 'partial').write_bytes(b'first file')
                raise OSError(errno.ENOSPC, 'injected write failure')
            with self.assertRaises(OSError): publish_directory(target, writer)
            self.assertEqual(list(root.iterdir()), [])

    def test_receipt_failure_does_not_publish_reconstruction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); base = root / 'base'; base.mkdir()
            (base / 'dep').write_bytes(b'original')
            package_files({'dep': b'original'}, {'dep': b'original', 'new': b'new'}, root / 'package')
            def fail_receipt(path, data):
                self.assertEqual((path.parent / 'theme/new').read_bytes(), b'new')
                self.assertFalse(Path(data['reconstruction_dir']).exists())
                raise OSError(errno.EIO, 'injected receipt failure')
            with self.assertRaises(OSError):
                reconstruct(root / 'package/FILES.json', base, root / 'output',
                            backend.read_file, fail_receipt)
            self.assertEqual(list((root / 'output/reconstructed').iterdir()), [])
            self.assertEqual((base / 'dep').read_bytes(), b'original')

    def test_target_created_during_write_is_never_replaced(self):
        for occupied in (False, True):
            with self.subTest(occupied=occupied), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); target = root / 'result'
                def writer(stage):
                    (stage / 'proposed').write_bytes(b'new')
                    target.mkdir()
                    if occupied: (target / 'existing').write_bytes(b'keep')
                with self.assertRaises(OSError): publish_directory(target, writer)
                self.assertTrue(target.is_dir())
                self.assertEqual(list(root.iterdir()), [target])
                if occupied:
                    self.assertEqual((target / 'existing').read_bytes(), b'keep')
                else:
                    self.assertEqual(list(target.iterdir()), [])


if __name__ == '__main__': unittest.main()
