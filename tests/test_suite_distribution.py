# SPDX-License-Identifier: GPL-3.0-or-later
"""Immutable source staging and native prebuilt validation, without any GUI."""
from __future__ import annotations
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from install_suite import copy_private_source, prepared_install_sources
from theme_transaction import Failure
from user_bundle import Bundle, fingerprint
import domainos_native_menu as native


class ImmutableInstallSources(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.qa-domainos-suite-staging-', dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        (self.source / 'icon').write_bytes(b'public source')
        (self.source / 'alias').symlink_to('icon')

    def freeze(self):
        (self.source / 'icon').chmod(0o444)
        self.source.chmod(0o555)
        self.addCleanup(self.source.chmod, 0o755)

    def test_immutable_internal_alias_installs_repeats_and_restores(self):
        self.freeze()
        before = fingerprint(self.source)
        destination = self.base / 'installed'
        destination.mkdir()
        (destination / 'prior').write_bytes(b'previous theme')
        previous = fingerprint(destination)
        bundle = Bundle(self.base / 'state', (destination,))
        pairs = [(self.source, destination)]
        with patch('install_suite.tempfile.tempdir', str(self.base)):
            with prepared_install_sources(pairs) as prepared:
                self.assertNotEqual(prepared[0][0], self.source)
                self.assertTrue((prepared[0][0] / 'alias').is_symlink())
                self.assertTrue((prepared[0][0] / 'icon').stat().st_mode & stat.S_IWUSR)
                bundle.install(prepared)
            useful_backup = bundle.latest()[0]
            with prepared_install_sources(pairs) as prepared:
                bundle.install(prepared)
            self.assertEqual(bundle.latest()[0], useful_backup)
            bundle.restore()
        self.assertEqual(fingerprint(destination), previous)
        self.assertEqual(fingerprint(self.source), before)
        self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), 0o555)
        self.assertEqual(stat.S_IMODE((self.source / 'icon').stat().st_mode), 0o444)

    def test_external_alias_rejected_before_copy(self):
        (self.source / 'alias').unlink()
        outside = self.base / 'private'
        outside.write_bytes(b'unrelated')
        (self.source / 'alias').symlink_to('../private')
        destination = self.base / 'staging'
        with self.assertRaises(Failure):
            copy_private_source(self.source, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(outside.read_bytes(), b'unrelated')


@unittest.skipUnless(os.environ.get('IRIX_SUITE_NATIVE_ZIP'), 'provide the published prebuilt native ZIP')
class NativePrebuiltSources(unittest.TestCase):
    def test_corrupted_binary_is_rejected_without_sdk_or_install(self):
        with tempfile.TemporaryDirectory(prefix='.qa-domainos-suite-native-', dir=ROOT) as directory:
            source = Path(directory)
            with zipfile.ZipFile(os.environ['IRIX_SUITE_NATIVE_ZIP']) as archive:
                from package_domainos import NAME
                prefix = NAME + '/'
                for name in (*native.BUILD_INPUTS, native.BINARY_SOURCE, native.MANIFEST_SOURCE):
                    path = source / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read(prefix + name))
            binary = source / native.BINARY_SOURCE
            value = bytearray(binary.read_bytes()); value[-1] ^= 1; binary.write_bytes(value)
            with patch.object(native, 'toolchain', side_effect=AssertionError('SDK must not be invoked')):
                with self.assertRaisesRegex(Failure, 'Hash/tamanho/caminho'):
                    with native.prepare_native(source):
                        self.fail('a corrupted binary was accepted')


if __name__ == '__main__':
    unittest.main()
