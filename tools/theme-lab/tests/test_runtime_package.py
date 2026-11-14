# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import uuid

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))

from package_runtime import BINARIES, FILES, _private_destination
from runtime_diagnostics import _integrity


class RuntimePackageTests(unittest.TestCase):
    def setUp(self):
        self.base = Path.home() / 'tempia/domainos-theme-work'
        self.base.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.base_mode = self.base.stat().st_mode & 0o777
        self.folder = Path(tempfile.mkdtemp(prefix='runtime-package-test-',
                                           dir=self.base))

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_destination_keeps_existing_container_mode(self):
        destination = self.base / ('new-package-' + uuid.uuid4().hex)
        self.assertEqual(_private_destination(destination), destination)
        self.assertEqual(self.base.stat().st_mode & 0o777, self.base_mode)

    def test_destination_outside_project_temp_root_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'domainos-theme-work'):
            _private_destination(Path.home() / ('outside-' + uuid.uuid4().hex))

    def test_destination_cannot_escape_with_parent_segments(self):
        destination = self.base / 'candidate' / '..' / '..' / ('escape-' + uuid.uuid4().hex)
        with self.assertRaisesRegex(ValueError, 'domainos-theme-work'):
            _private_destination(destination)

    def test_manifest_detects_payload_change(self):
        payload = self.folder / 'payload.txt'
        payload.write_bytes(b'original')
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        (self.folder / 'THEME-LAB-PACKAGE.json').write_text(json.dumps({
            'schema': 1, 'files': {'payload.txt': digest}}), encoding='utf-8')
        self.assertTrue(_integrity(self.folder)['verified'])
        payload.write_bytes(b'changed')
        result = _integrity(self.folder)
        self.assertFalse(result['verified'])
        self.assertEqual(result['failures'],
                         [{'path': 'payload.txt', 'reason': 'sha256_mismatch'}])

    def test_native_palette_reader_runtime_pair_is_packaged_and_declared(self):
        source = 'tools/theme-lab/src/native_colors.cpp'
        helper = 'tools/theme-lab/build/theme-lab-colors'
        dependencies = json.loads((LAB / 'runtime-dependencies.json').read_text(encoding='utf-8'))
        self.assertIn(source, FILES)
        self.assertIn('theme-lab-colors', BINARIES)
        self.assertIn(source, dependencies['shared']['resources'])
        self.assertIn(helper, dependencies['shared']['resources'])

    def test_kvantum_native_palette_runtime_is_packaged_and_declared(self):
        expected = {
            'tools/kvantum_native_palette.py',
            'tools/kvantum_palette_config.py',
            'tools/theme_transaction.py',
        }
        dependencies = json.loads((LAB / 'runtime-dependencies.json').read_text(encoding='utf-8'))
        self.assertTrue(expected <= set(FILES))
        self.assertTrue(expected <= set(dependencies['families']['kvantum']['resources']))


if __name__ == '__main__':
    unittest.main()
