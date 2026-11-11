#!/usr/bin/python3
"""Delta import publishes a validated private project; no GUI or installation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from proposal_export import differences, model_digest
from test_backend import model as sample_model


class ImportTests(unittest.TestCase):
    def fixture(self, root):
        base_path = root / 'base.json'
        base_path.write_text(json.dumps(sample_model()))
        before, digest = backend.project(base_path)
        after = copy.deepcopy(before)
        after['recipes']['gtk3']['notes'] = 'Ação — São Paulo'
        after['recipes']['qt6']['positions'][3] = [39, 57]
        after['recipes']['gtk5']['notes'] = 'Sem runtime; preservar'
        delta = {'schema': 1, 'kind': 'theme_lab_project_delta',
                 'base_model_sha256': model_digest(before),
                 'proposal_model_sha256': model_digest(after),
                 'changes': differences(before, after)}
        delta_path = root / 'DELTA.json'; delta_path.write_text(json.dumps(delta, ensure_ascii=False))
        return base_path, before, after, digest, delta_path, delta

    def test_import_preserves_base_and_reconstructs_all_recipes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base, before, after, digest, path, _ = self.fixture(root)
            original = base.read_bytes(); previous = copy.deepcopy(before)
            result = backend.import_project_delta(Path.cwd(), root / 'output', before, digest, path)
            restored, _ = backend.project(Path(result['project_path']))
            self.assertEqual(restored, after)
            self.assertEqual(before, previous)
            self.assertEqual(base.read_bytes(), original)
            self.assertFalse(result['installed']); self.assertFalse(result['preview_applied'])
            self.assertEqual(result['delta_sha256'], backend.sha(path.read_bytes()))
            second = backend.import_project_delta(Path.cwd(), root / 'output', before, digest, path)
            self.assertNotEqual(result['project_path'], second['project_path'])

    def test_cli_roundtrip_returns_reopenable_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base, _, after, _, path, _ = self.fixture(root)
            process = subprocess.run([sys.executable, '-B', str(Path(backend.__file__)),
                '--import-delta', '--root', str(Path.cwd()), '--project', str(base),
                '--delta', str(path), '--output', str(root / 'output')],
                capture_output=True, text=True, timeout=15)
            self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
            receipt = json.loads(process.stdout)
            actual, _ = backend.project(Path(receipt['project_path']))
            self.assertEqual(actual, after)

    def test_diverged_base_and_malformed_changes_do_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, before, _, digest, path, delta = self.fixture(root)
            changed = copy.deepcopy(before); changed['name'] = 'another base'
            with self.assertRaisesRegex(ValueError, 'base divergente'):
                backend.import_project_delta(Path.cwd(), root / 'output', changed, digest, path)
            self.assertFalse((root / 'output').exists())
            for invalid in ({}, dict(delta, changes=[{'operation': 'replace', 'path': [], 'value': 1}]),
                            dict(delta, changes=[{'operation': 'replace', 'path': [True], 'value': 1}]),
                            dict(delta, changes=[{'operation': 'replace', 'path': ['missing', 'a'], 'value': 1}])):
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    backend.import_project_delta(Path.cwd(), root / 'output', before, digest, path)
                self.assertFalse((root / 'output').exists())

    def test_candidate_validation_before_publishing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, before, after, digest, path, delta = self.fixture(root)
            after['recipes']['gtk3']['geometry']['font_px'] = 999
            delta['proposal_model_sha256'] = model_digest(after)
            delta['changes'] = differences(before, after)
            path.write_text(json.dumps(delta))
            with self.assertRaisesRegex(ValueError, 'Fonte'):
                backend.import_project_delta(Path.cwd(), root / 'output', before, digest, path)
            self.assertEqual(list((root / 'output/imports').iterdir()), [])


if __name__ == '__main__': unittest.main()
