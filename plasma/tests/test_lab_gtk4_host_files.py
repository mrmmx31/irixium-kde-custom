#!/usr/bin/python3
"""GTK4 frozen host bridge: ABI closure, freshness and link rejection."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('launcher',ROOT/'plasma/tools/abrir-laboratorio-temas.py')
lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)


class HostFilesTests(unittest.TestCase):
    def fixture(self, root):
        folder=root/'tools/theme-lab'
        (folder/'native-gtk4').mkdir(parents=True);(folder/'build').mkdir()
        sources=[folder/'native-gtk4'/name for name in ('host.c','host.h')]
        for source in sources:source.write_text('fixture ABI source\n')
        helper=folder/'build/libtheme-lab-gtk4-host.so'
        helper.write_bytes(b'\x7fELFfixture-not-a-runtime-library')
        return helper,sources

    def test_absent_optional_bridge(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-host-files-') as d:
            self.assertEqual(lab.gtk4_host_files(Path(d)),[])

    def test_helper_and_abi_sources_are_frozen(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-host-files-') as d:
            helper,sources=self.fixture(Path(d))
            self.assertEqual(lab.gtk4_host_files(Path(d)),[helper,*sources])

    def test_stale_helper_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-host-files-') as d:
            helper,sources=self.fixture(Path(d));future=helper.stat().st_mtime_ns+1000000000
            os.utime(sources[0],ns=(future,future))
            with self.assertRaisesRegex(RuntimeError,'anterior aos fontes'):
                lab.gtk4_host_files(Path(d))

    def test_symlink_cannot_supply_native_code(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-host-files-') as d:
            helper,_=self.fixture(Path(d));actual=helper.with_name('other.so')
            helper.rename(actual);helper.symlink_to(actual.name)
            with self.assertRaises(OSError):lab.gtk4_host_files(Path(d))


if __name__=='__main__':unittest.main()
