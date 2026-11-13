#!/usr/bin/env python3
"""Optional GTK2 binary/source closure and stale/symlink refusal."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('launcher', ROOT / 'plasma/tools/abrir-laboratorio-temas.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class BridgeFilesTests(unittest.TestCase):
    def fixture(self, root):
        folder = root / 'tools/theme-lab'
        (folder / 'native-gtk2').mkdir(parents=True)
        (folder / 'build').mkdir()
        sources = [folder / 'native-gtk2' / name for name in ('press.c', 'press.h')]
        for source in sources:
            source.write_text('fixture ABI source\n')
        helper = folder / 'build/libtheme-lab-gtk2-press.so'
        helper.write_bytes(b'\x7fELFfixture-not-a-runtime-library')
        return helper, sources

    def test_absent_bridge_does_not_require_optional_sdk(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-bridge-files-') as d:
            self.assertEqual(lab.gtk2_press_files(Path(d)), [])

    def test_helper_and_both_abi_sources_are_frozen(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-bridge-files-') as d:
            helper, sources = self.fixture(Path(d))
            self.assertEqual(lab.gtk2_press_files(Path(d)), [helper, *sources])

    def test_stale_binary_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-bridge-files-') as d:
            helper, sources = self.fixture(Path(d))
            future = helper.stat().st_mtime_ns + 1000000000
            os.utime(sources[0], ns=(future, future))
            with self.assertRaisesRegex(RuntimeError, 'anterior aos fontes'):
                lab.gtk2_press_files(Path(d))

    def test_symlink_cannot_supply_native_code(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-bridge-files-') as d:
            helper, _ = self.fixture(Path(d))
            actual = helper.with_name('other.so')
            helper.rename(actual)
            helper.symlink_to(actual.name)
            with self.assertRaises(OSError):
                lab.gtk2_press_files(Path(d))


if __name__ == '__main__':
    unittest.main()
