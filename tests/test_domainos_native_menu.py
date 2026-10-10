#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native payload preflight, isolated staging, and public Qt metadata proof.

Pure negative tests require no SDK. The real compilation proof needs the Qt6
QML SDK (or explicit DOMAINOS_NATIVE_HEADERS_ROOT); it never installs a theme.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import domainos_native_menu as native
import package_domainos as package


def text_cbor(value):
    data = value.encode()
    return bytes([0x60 + len(data)]) + data if len(data) < 24 else b'\x78' + bytes([len(data)]) + data


def elf_fixture(*, machine=62, qt_minor=8, rpath=None, iid=native.PLUGIN_IID,
                libraries=('libQt6Core.so.6', 'libQt6Gui.so.6', 'libQt6Widgets.so.6', 'libQt6Qml.so.6')):
    cbor = b'\xbf\x02' + text_cbor(iid) + b'\x03' + text_cbor(native.PLUGIN_CLASS) + b'\xff'
    desc = bytes([1, 6, qt_minor, 1]) + cbor
    note = struct.pack('<III', 12, len(desc), 0x74510001) + b'qt-project!\0' + desc
    strings = bytearray(b'\0')
    dynamic = bytearray()
    for name in libraries:
        dynamic += struct.pack('<qQ', 1, len(strings))
        strings += name.encode() + b'\0'
    if rpath:
        dynamic += struct.pack('<qQ', 29, len(strings))
        strings += rpath.encode() + b'\0'
    dynamic += struct.pack('<qQ', 0, 0)
    names = b'\0.note.qt.metadata\0.dynstr\0.dynamic\0.shstrtab\0'
    contents = [b'', note, bytes(strings), bytes(dynamic), names]
    data = bytearray(b'\0' * 64)
    offsets = []
    for content in contents:
        offsets.append(len(data)); data += content
    section_offset = len(data)
    for index, content in enumerate(contents):
        name = ['', '.note.qt.metadata', '.dynstr', '.dynamic', '.shstrtab'][index]
        name_offset = names.find(name.encode() + b'\0') if name else 0
        kind = [0, 7, 3, 6, 3][index]
        data += struct.pack('<IIQQQQIIQQ', name_offset, kind, 0, 0, offsets[index], len(content), 2 if index == 3 else 0, 0, 1, 16 if index == 3 else 0)
    ident = b'\x7fELF\x02\x01\x01' + b'\0' * 9
    data[:64] = struct.pack('<16sHHIQQQIHHHHHH', ident, 3, machine, 1, 0, 0, section_offset, 0, 64, 0, 0, 64, 5, 4)
    return bytes(data)


def fixture_inputs():
    return {native.BUILD_INPUTS[0]: b'// public fixture source\n',
            native.BUILD_INPUTS[1]: ('module ' + native.MODULE_URI + '\nplugin domainosmenuplugin\nclassname NativeMenuPlugin\n').encode(),
            native.BUILD_INPUTS[2]: b'# public build fixture\n',
            native.BUILD_INPUTS[3]: b'// public geometry header fixture\n',
            native.BUILD_INPUTS[4]: b'// public geometry fixture\n',
            native.BUILD_INPUTS[5]: b'// public popup route header fixture\n',
            native.BUILD_INPUTS[6]: b'// public popup route fixture\n'}


def payload(binary=None):
    files = fixture_inputs()
    data = binary or elf_fixture()
    files[native.BINARY_SOURCE] = data
    files[native.MANIFEST_SOURCE] = native.json_bytes({'format': 1, 'module': native.MODULE_URI,
        'sourceHashes': native.source_hashes(files),
        'binary': {'path': native.BINARY_SOURCE, 'bytes': len(data), 'sha256': native.digest(data)},
        'build': {'qtVersion': '6.8.2', 'compiler': 'test c++', 'flags': native.BUILD_FLAGS},
        'elf': native.inspect_elf(data)})
    return files


class PayloadTests(unittest.TestCase):
    def test_valid_bounded_note_and_manifest_are_inspected_without_loading(self):
        result = native.validate_payload(payload(), check_runtime=False)
        self.assertEqual(result['status'], 'verified_prebuilt')
        self.assertEqual(result['machine'], 'x86_64')

    def test_truncated_elf_and_offsets_are_rejected(self):
        data = elf_fixture()
        for broken in (data[:63], data[:-1], data[:40] + b'\xff' * 8 + data[48:]):
            with self.subTest(length=len(broken)), self.assertRaises(native.Failure):
                native.inspect_elf(broken)

    def test_wrong_architecture_qt_and_interface_fail(self):
        for kwargs in ({'machine': 183}, {'qt_minor': 7}, {'iid': 'unexpected'},
                       {'libraries': ('libQt6Core.so.6', 'libUnknown.so')}):
            with self.subTest(kwargs=kwargs), self.assertRaises(native.Failure):
                native.inspect_elf(elf_fixture(**kwargs))

    def test_any_rpath_is_rejected_before_native_code_runs(self):
        for path in ('/tmp/private-sdk', '$ORIGIN', '/usr/lib'):
            with self.subTest(path=path), self.assertRaisesRegex(native.Failure, 'RPATH'):
                native.inspect_elf(elf_fixture(rpath=path))

    def test_stale_source_and_binary_tampering_fail(self):
        files = payload(); files[native.BUILD_INPUTS[0]] += b'// changed\n'
        with self.assertRaisesRegex(native.Failure, 'fontes'):
            native.validate_payload(files, check_runtime=False)
        files = payload(); files[native.BINARY_SOURCE] += b'changed'
        with self.assertRaisesRegex(native.Failure, 'Hash'):
            native.validate_payload(files, check_runtime=False)

    def test_manifest_cannot_forge_binary_metadata_or_build_version(self):
        for mutate in (lambda r: r['elf']['qt'].update(minor=9),
                       lambda r: r['build'].update(qtVersion='6.9.0'),
                       lambda r: r['binary'].update(path='other.so'),
                       lambda r: r.update(extra='unexpected')):
            files = payload(); record = json.loads(files[native.MANIFEST_SOURCE]); mutate(record)
            files[native.MANIFEST_SOURCE] = native.json_bytes(record)
            with self.assertRaises(native.Failure):
                native.validate_payload(files, check_runtime=False)

    def test_null_and_missing_manifest_fail_explicitly(self):
        for value in (b'null', b'{', b'[]'):
            files = payload(); files[native.MANIFEST_SOURCE] = value
            with self.assertRaises(native.Failure):
                native.validate_payload(files, check_runtime=False)
        files = payload(); del files[native.MANIFEST_SOURCE]
        with self.assertRaises(native.Failure):
            native.validate_payload(files, check_runtime=False)

    def test_duplicate_manifest_keys_fail_explicitly(self):
        files = payload()
        files[native.MANIFEST_SOURCE] = files[native.MANIFEST_SOURCE].replace(b'"format": 1,', b'"format": 1, "format": 1,')
        with self.assertRaisesRegex(native.Failure, 'duplicada'):
            native.validate_payload(files, check_runtime=False)

    def test_runtime_older_qt_or_missing_abi_fails(self):
        elf = native.inspect_elf(elf_fixture(qt_minor=9))
        with self.assertRaisesRegex(native.Failure, 'mais novo'):
            native.check_compatibility(elf, {'qtVersion': '6.8.2', 'libraryDirectories': []})
        elf = native.inspect_elf(elf_fixture()); elf['versions']['libQt6Core.so.6'] = ['Qt_6_999']
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            directory = Path(temporary)
            for name in elf['needed']: (directory / name).write_bytes(b'fixture')
            with mock.patch.object(native, '_defined_versions', return_value={'Qt_6'}):
                with self.assertRaisesRegex(native.Failure, 'ABI'):
                    native.check_compatibility(elf, {'qtVersion': '6.8.2', 'libraryDirectories': [directory]})

    def test_extra_shared_objects_and_near_miss_paths_stay_forbidden(self):
        self.assertTrue(package.safe_name(native.BINARY_SOURCE))
        self.assertTrue(package.safe_name(package.NAME + '/' + native.BINARY_SOURCE))
        for path in ('qa/test.so', native.BINARY_SOURCE + '.so', native.BINARY_SOURCE.replace('libdomainos', 'libother'),
                     native.BINARY_SOURCE.upper(), native.BINARY_SOURCE.replace('/menu/', '/menu-extra/')):
            self.assertFalse(package.safe_name(path), path)


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.native-stage-test-', dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name, data in fixture_inputs().items():
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        self.spec = {'qtVersion': '6.8.2', 'compiler': 'fixture', 'compilerVersion': 'fixture',
                     'moc': 'fixture', 'cflags': [], 'libraries': []}

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob('*') if path.is_file()}

    def test_command_timeout_stops_own_compiler_child_before_stage_cleanup(self):
        marker = self.root / 'child-finished'
        child = 'import time;from pathlib import Path;time.sleep(.7);Path(' + repr(str(marker)) + ').write_text("unexpected live child")'
        parent = 'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",' + repr(child) + ']);time.sleep(5)'
        with self.assertRaisesRegex(native.Failure, 'Tempo limite'):
            native._command([sys.executable, '-c', parent], timeout=.15)
        time.sleep(.8)
        self.assertFalse(marker.exists())

    def test_dry_source_preflight_never_compiles_or_writes_stage(self):
        before = self.snapshot()
        with (mock.patch.object(native, 'toolchain', return_value=self.spec), mock.patch.object(native, '_build') as build,
                mock.patch.object(native.tempfile, 'TemporaryDirectory') as temporary):
            with native.prepare_native(self.root, dry=True) as prepared:
                self.assertEqual(prepared['report']['status'], 'build_required')
                self.assertEqual(prepared['panel'], self.root / native.PANEL_SOURCE)
                self.assertFalse(prepared['payload'])
            build.assert_not_called(); temporary.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_prebuilt_preflight_needs_no_toolchain_and_validates_sources(self):
        files = payload()
        for name, data in files.items():
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        with (mock.patch.object(native, 'toolchain') as toolchain,
                mock.patch.object(native, 'runtime_info', return_value={'qtVersion': '6.8.2', 'libraryDirectories': []}),
                mock.patch.object(native, 'check_compatibility') as compatibility):
            with native.prepare_native(self.root, dry=True) as prepared:
                self.assertEqual(prepared['report']['status'], 'verified_prebuilt')
            toolchain.assert_not_called(); compatibility.assert_called_once()

    def test_half_payload_and_symlink_are_rejected(self):
        binary = self.root / native.BINARY_SOURCE; binary.write_bytes(elf_fixture())
        with self.assertRaisesRegex(native.Failure, 'juntos'):
            with native.prepare_native(self.root): pass
        binary.unlink(); source = self.root / native.BUILD_INPUTS[0]
        source.unlink(); source.symlink_to(self.root / native.BUILD_INPUTS[1])
        with self.assertRaises(native.Failure):
            with native.prepare_native(self.root): pass

    def test_build_failure_never_enters_install_body_or_changes_sources(self):
        before = self.snapshot(); entered = False; stages = []
        def fail(root, panel, spec):
            stages.append(panel.parent); (panel / 'partial.o').write_bytes(b'partial')
            raise native.Failure('injected compiler failure')
        with mock.patch.object(native, 'toolchain', return_value=self.spec), mock.patch.object(native, '_build', side_effect=fail):
            with self.assertRaisesRegex(native.Failure, 'injected'):
                with native.prepare_native(self.root): entered = True
        self.assertFalse(entered); self.assertTrue(stages); self.assertFalse(stages[0].exists())
        self.assertEqual(self.snapshot(), before)

    def test_source_edit_during_build_rejects_new_binary_before_install(self):
        stages = []; entered = False
        def command(arguments, timeout=10):
            if '-shared' in arguments:
                binary = Path(arguments[arguments.index('-o') + 1])
                stages.append(binary.parents[3])
                binary.write_bytes(elf_fixture())
                (self.root / native.BUILD_INPUTS[0]).write_bytes(b'// concurrent source edit\n')
            return ''
        with mock.patch.object(native, 'toolchain', return_value=self.spec), mock.patch.object(native, '_command', side_effect=command):
            with self.assertRaisesRegex(native.Failure, 'durante a compila'):
                with native.prepare_native(self.root): entered = True
        self.assertFalse(entered); self.assertTrue(stages); self.assertFalse(stages[0].exists())
        self.assertFalse((self.root / native.BINARY_SOURCE).exists())
        self.assertFalse((self.root / native.MANIFEST_SOURCE).exists())

    def test_only_one_source_is_replaced_and_stage_survives_until_commit_returns(self):
        before = self.snapshot(); destinations = [self.root / ('private/' + str(i)) for i in range(4)]
        pairs = [(self.root / native.PANEL_SOURCE, destinations[0])] + [(self.root / ('source/' + str(i)), destinations[i]) for i in range(1, 4)]
        def build(root, panel, spec):
            (panel / 'contents/native/menu/libdomainosmenuplugin.so').write_bytes(b'generated')
            return {native.BINARY_SOURCE: b'generated'}
        with mock.patch.object(native, 'toolchain', return_value=self.spec), mock.patch.object(native, '_build', side_effect=build):
            with native.prepared_source_pairs(self.root, pairs) as prepared:
                stage = prepared[0][0]
                self.assertNotEqual(stage, pairs[0][0]); self.assertTrue(stage.is_dir())
                self.assertEqual([dest for _, dest in prepared], destinations)
                self.assertEqual(prepared[1:], pairs[1:])
            self.assertFalse(stage.exists())
        self.assertEqual(self.snapshot(), before)


class RealBuildTests(unittest.TestCase):
    def test_real_stage_public_qt_metadata_and_no_checkout_binary(self):
        try:
            native.toolchain()
        except native.Failure as error:
            self.skipTest('real Qt QML build SDK unavailable: ' + str(error))
        self.assertFalse((ROOT / native.BINARY_SOURCE).exists())
        self.assertFalse((ROOT / native.MANIFEST_SOURCE).exists())
        with native.prepare_native(ROOT) as prepared:
            stage = prepared['panel']; binary = stage / 'contents/native/menu/libdomainosmenuplugin.so'
            self.assertTrue(binary.is_file())
            self.assertFalse((binary.parent / 'plugin.moc').exists())
            self.assertFalse((binary.parent / 'moc_scrollgeometry.cpp').exists())
            result = native.validate_payload({**native._inputs(ROOT), **prepared['payload']})
            self.assertEqual(result['status'], 'verified_prebuilt')
            # Independently compare the restricted data parser with Qt's public
            # C++ QPluginLoader::metaData(). The inspector never calls load().
            cpp = stage.parent / 'inspect.cpp'; inspector = stage.parent / 'inspect'
            cpp.write_text('#include <QCoreApplication>\n#include <QPluginLoader>\n#include <QJsonDocument>\n#include <iostream>\nint main(int argc,char**argv){QCoreApplication app(argc,argv);QPluginLoader loader(QString::fromLocal8Bit(argv[1]));std::cout<<QJsonDocument(loader.metaData()).toJson(QJsonDocument::Compact).constData();return loader.isLoaded()?3:0;}\n')
            flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt6Core'], text=True))
            subprocess.run(['c++', '-std=c++17', str(cpp), '-o', str(inspector), *flags], check=True, capture_output=True, timeout=30)
            metadata = json.loads(subprocess.check_output([str(inspector), str(binary)], text=True, timeout=10))
            self.assertEqual(metadata['IID'], native.PLUGIN_IID)
            self.assertEqual(metadata['className'], native.PLUGIN_CLASS)
            elf = native.inspect_elf(binary.read_bytes())
            self.assertEqual((metadata['version'] >> 16, (metadata['version'] >> 8) & 255), (elf['qt']['major'], elf['qt']['minor']))
            first_payload = prepared['payload']
        self.assertFalse(stage.exists())
        with native.prepare_native(ROOT) as repeated:
            self.assertEqual(repeated['payload'], first_payload,
                'separate private build paths must not change plugin/manifest bytes')
        self.assertFalse((ROOT / native.BINARY_SOURCE).exists())
        self.assertFalse((ROOT / native.MANIFEST_SOURCE).exists())


if __name__ == '__main__':
    unittest.main()
