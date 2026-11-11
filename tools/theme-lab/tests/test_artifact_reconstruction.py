# SPDX-License-Identifier: GPL-3.0-or-later
"""Real reconstruction CLI, including malformed input and independent output."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from artifact_delta import package_files


class ReconstructionTests(unittest.TestCase):
    def call(self, source, output, base=None):
        command = [sys.executable, '-B', backend.__file__, '--reconstruct-files',
                   '--file-delta', str(source), '--output', str(output)]
        if base is not None: command += ['--base-directory', str(base)]
        process = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertNotIn('Traceback', process.stderr)
        return process.returncode, json.loads(process.stdout)

    def test_exact_delta_and_snapshot_with_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); base = root / 'base'; base.mkdir()
            before = {'arrow.svg': b'unchanged', 'gtk.css': b'old', 'removed': b'delete'}
            after = {'arrow.svg': b'unchanged', 'gtk.css': b'new'}
            for name, data in before.items(): (base / name).write_bytes(data)
            package_files(before, after, root / 'delta')
            package_files(None, after, root / 'snapshot')
            for package, origin in [('delta', base), ('snapshot', None)]:
                code, result = self.call(root / package / 'FILES.json', root / 'out', origin)
                self.assertEqual(code, 0, result)
                theme = Path(result['theme_directory'])
                self.assertEqual({str(p.relative_to(theme)): p.read_bytes()
                                  for p in theme.rglob('*') if p.is_file()}, after)
                self.assertFalse(result['installed']); self.assertFalse(result['palette_revalidated'])
                self.assertEqual(json.loads((Path(result['reconstruction_dir']) / 'RECONSTRUCTION.json').read_text()), result)
                for directory in (root / 'out', root / 'out/reconstructed',
                                  Path(result['reconstruction_dir']), theme):
                    self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual({p.name: p.read_bytes() for p in base.iterdir()}, before)

    def test_invalid_contracts_do_not_create_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            good = package_files(None, {'gtk.css': b'data'}, root / 'package')
            variants = [None, [], {}, dict(good, schema=True), dict(good, mode='install'),
                        dict(good, files=None), dict(good, removed=['invented']),
                        dict(good, payload={'../outside': 'a'*64})]
            collision = copy.deepcopy(good)
            collision['files']['gtk.css/child'] = 'a'*64
            collision['payload']['gtk.css/child'] = 'a'*64
            variants.append(collision)
            for index, manifest in enumerate(variants):
                source = root / 'package/FILES.json'; source.write_text(json.dumps(manifest))
                output = root / ('out-' + str(index))
                code, result = self.call(source, output)
                self.assertEqual(code, 2, result)
                self.assertEqual(result['status'], 'error')
                self.assertFalse(output.exists())

    def test_wrong_base_links_and_overlapping_output_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); base = root / 'base'; base.mkdir()
            (base / 'dep').write_bytes(b'wrong')
            package_files({'dep': b'original'}, {'dep': b'original', 'new': b'new'}, root / 'package')
            source = root / 'package/FILES.json'
            code, _ = self.call(source, root / 'out', base)
            self.assertEqual(code, 2); self.assertFalse((root / 'out').exists())
            (base / 'dep').write_bytes(b'original')
            for output in (base / 'child', root / 'package/child'):
                code, _ = self.call(source, output, base)
                self.assertEqual(code, 2); self.assertFalse(output.exists())
            link = root / 'linked.json'; link.symlink_to(source)
            code, _ = self.call(link, root / 'out', base)
            self.assertEqual(code, 2); self.assertFalse((root / 'out').exists())
            (root / 'linked-out').symlink_to(base, target_is_directory=True)
            code, _ = self.call(source, root / 'linked-out/child', base)
            self.assertEqual(code, 2); self.assertFalse((base / 'child').exists())
            shared = root / 'shared'; shared.mkdir(mode=0o755)
            code, _ = self.call(source, shared, base)
            self.assertEqual(code, 2); self.assertEqual(list(shared.iterdir()), [])


if __name__ == '__main__': unittest.main()
