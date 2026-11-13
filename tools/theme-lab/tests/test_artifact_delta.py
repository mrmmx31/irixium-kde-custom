#!/usr/bin/python3
"""Exact artifact reconstruction and dependency checks; no visual claims."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from artifact_delta import package_files, reconstruct_files, digest, receipt_inventory


class ArtifactTests(unittest.TestCase):
    def fixture(self, path, files):
        path.mkdir()
        for name, data in files.items():
            file = path / name; file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        return path

    def test_only_changes_stored_and_round_trip_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = {'gtk.css': b'before', 'assets/arrow.svg': b'unchanged', 'old.svg': b'removed'}
            after = {'gtk.css': b'after', 'assets/arrow.svg': b'unchanged', 'added.svg': b'new'}
            base = self.fixture(root / 'base', before)
            manifest = package_files(before, after, root / 'package')
            self.assertEqual(set(manifest['payload']), {'gtk.css', 'added.svg'})
            self.assertEqual(manifest['removed'], ['old.svg'])
            self.assertFalse((root / 'package/payload/assets/arrow.svg').exists())
            result = reconstruct_files(manifest, root / 'package', base,
                                       root / 'result', backend.read_file)
            self.assertEqual(result['reused_files'], 1)
            self.assertEqual({str(p.relative_to(root / 'result')): p.read_bytes()
                for p in (root / 'result').rglob('*') if p.is_file()}, after)
            self.assertEqual((base / 'gtk.css').read_bytes(), b'before')

    def test_missing_or_modified_base_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = {'dep.svg': b'original'}; after = dict(before, **{'gtk.css': b'new'})
            base = self.fixture(root / 'base', before)
            manifest = package_files(before, after, root / 'package')
            (base / 'dep.svg').write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError, 'recibo'):
                reconstruct_files(manifest, root / 'package', base, root / 'result', backend.read_file)
            self.assertFalse((root / 'result').exists())
            (base / 'dep.svg').unlink()
            with self.assertRaises(OSError):
                reconstruct_files(manifest, root / 'package', base, root / 'result', backend.read_file)
            self.assertFalse((root / 'result').exists())

    def test_payload_corruption_and_overlap_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = package_files(None, {'gtk.css': b'new'}, root / 'package')
            self.assertEqual(manifest['mode'], 'snapshot')
            (root / 'package/payload/gtk.css').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                reconstruct_files(manifest, root / 'package', None, root / 'result', backend.read_file)
            manifest['reuse']['gtk.css'] = manifest['files']['gtk.css']
            with self.assertRaisesRegex(ValueError, 'sobreposto'):
                reconstruct_files(manifest, root / 'package', None, root / 'result', backend.read_file)

    def test_unchanged_package_has_no_payload_and_still_reconstructs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = {'asset.svg': b'unchanged'}; base = self.fixture(root / 'base', files)
            manifest = package_files(files, files, root / 'package')
            self.assertEqual(manifest['payload'], {})
            reconstruct_files(manifest, root / 'package', base, root / 'result', backend.read_file)
            self.assertEqual((root / 'result/asset.svg').read_bytes(), b'unchanged')

    def test_paths_links_and_existing_result_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index, name in enumerate(('../escape', '/etc/file', 'a/./b', 'a//b')):
                with self.assertRaises(ValueError):
                    package_files(None, {name: b'x'}, root / str(index))
            manifest = package_files(None, {'asset': b'data'}, root / 'package')
            (root / 'package/payload/asset').unlink()
            (root / 'package/payload/asset').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(ValueError, 'links'):
                reconstruct_files(manifest, root / 'package', None, root / 'result', backend.read_file)
            (root / 'result').mkdir()
            with self.assertRaisesRegex(ValueError, 'já existe'):
                reconstruct_files(manifest, root / 'package', None, root / 'result', backend.read_file)

    def test_toolkit_receipt_inventory_and_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            theme = self.fixture(root / 'theme', {'gtk.css': b'css', 'ORIGEM.json': b'{}'})
            hashes = {name: digest(data) for name, data in {'gtk.css': b'css', 'ORIGEM.json': b'{}'}.items()}
            (theme / 'MANIFEST.json').write_text(json.dumps({'files': hashes}))
            receipt = {'family': 'gtk3', 'status': 'generated', 'theme_path': str(theme)}
            directory, files = receipt_inventory(root, receipt, backend.read_file)
            self.assertEqual(directory, theme)
            self.assertEqual(files, {'gtk.css': b'css'})
            (theme / 'gtk.css').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'recibo'):
                receipt_inventory(root, receipt, backend.read_file)
            gtk2 = self.fixture(root / 'gtk2', {'gtkrc': b'rc', 'arrow.png': b'png'})
            receipt2 = {'family': 'gtk2', 'status': 'partially_generated', 'rc': str(gtk2 / 'gtkrc'),
                        'rc_sha256': digest(b'rc'), 'asset_sha256': {'arrow.png': digest(b'png')}}
            _, files2 = receipt_inventory(root, receipt2, backend.read_file)
            self.assertEqual(files2, {'gtkrc': b'rc', 'arrow.png': b'png'})
            receipt2['rc'] = '/etc/passwd'
            with self.assertRaisesRegex(ValueError, 'fora'):
                receipt_inventory(root, receipt2, backend.read_file)


if __name__ == '__main__': unittest.main()
