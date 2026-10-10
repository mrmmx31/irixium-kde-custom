#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build/verify the applet-local public Qt menu module, before installation.

No plugin is loaded, no package is installed, and no desktop preferences are
read. ELF/Qt metadata inspection reads bounded data only. A source checkout is
built in a disposable private stage; generated files never enter the checkout.
The compiled delivery currently supports GNU/Linux x86_64, Qt 6.8 or later.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import signal
import stat
import struct
import subprocess
import tempfile

from theme_transaction import Failure, no_links

PANEL_SOURCE = 'plasma/applets/org.irixclassic.domainos.panel'
NATIVE_DIRECTORY = PANEL_SOURCE + '/contents/native/menu'
BINARY_SOURCE = NATIVE_DIRECTORY + '/libdomainosmenuplugin.so'
MANIFEST_SOURCE = NATIVE_DIRECTORY + '/native-build.json'
BUILD_INPUTS = (NATIVE_DIRECTORY + '/plugin.cpp', NATIVE_DIRECTORY + '/qmldir',
                'tools/domainos_native_menu.py',
                NATIVE_DIRECTORY + '/scrollgeometry.h', NATIVE_DIRECTORY + '/scrollgeometry.cpp',
                NATIVE_DIRECTORY + '/popupwheel.h', NATIVE_DIRECTORY + '/popupwheel.cpp')
MODULE_URI = 'org.irixclassic.domainos.menu'
PLUGIN_CLASS = 'NativeMenuPlugin'
PLUGIN_IID = 'org.qt-project.Qt.QQmlExtensionInterface/1.0'
MAX_BINARY = 8 * 1024 * 1024
FORMAT = 1
NEEDED_LIBRARIES = frozenset(('libQt6Core.so.6', 'libQt6Gui.so.6',
    'libQt6Widgets.so.6', 'libQt6Qml.so.6', 'libstdc++.so.6', 'libgcc_s.so.1',
    'libm.so.6', 'libc.so.6'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def regular_bytes(path):
    path = Path(path)
    no_links(path)
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > MAX_BINARY:
        raise Failure('Input nativo ausente, irregular ou excessivo: ' + str(path))
    return path.read_bytes()


def source_hashes(files):
    if not all(name in files for name in BUILD_INPUTS):
        raise Failure('Fontes completas do módulo nativo ausentes.')
    lines = [line.strip() for line in files[BUILD_INPUTS[1]].decode().splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if lines != ['module ' + MODULE_URI, 'plugin domainosmenuplugin',
                 'classname ' + PLUGIN_CLASS]:
        raise Failure('qmldir do módulo nativo incompatível.')
    return {name: digest(files[name]) for name in BUILD_INPUTS}


def _slice(data, offset, size):
    if not isinstance(offset, int) or not isinstance(size, int) or offset < 0 or size < 0 or offset + size > len(data):
        raise Failure('Estrutura ELF nativa truncada ou fora dos limites.')
    return data[offset:offset + size]


def _cstring(data, offset):
    if offset < 0 or offset >= len(data):
        raise Failure('String ELF nativa fora dos limites.')
    end = data.find(b'\0', offset)
    if end < 0 or end - offset > 4096:
        raise Failure('String ELF nativa truncada ou excessiva.')
    try:
        return data[offset:end].decode('ascii')
    except UnicodeError as error:
        raise Failure('String ELF nativa inválida.') from error


def _sections(data):
    if len(data) < 64 or data[:7] != b'\x7fELF\x02\x01\x01':
        raise Failure('O módulo precisa ser ELF64 little-endian Linux AMD64.')
    header = struct.unpack('<16sHHIQQQIHHHHHH', data[:64])
    _, kind, machine, _, _, _, offset, _, size, _, _, stride, count, strings = header
    if kind != 3 or machine != 62 or size != 64 or stride != 64 or not 0 < count <= 4096 or strings >= count:
        raise Failure('Arquitetura/tipo ELF nativo incompatível.')
    entries = [struct.unpack('<IIQQQQIIQQ', _slice(data, offset + index * 64, 64))
               for index in range(count)]
    table = entries[strings]
    names = _slice(data, table[4], table[5])
    result = []
    for entry in entries:
        name = _cstring(names, entry[0])
        content = b'' if entry[1] == 8 else _slice(data, entry[4], entry[5])
        result.append({'name': name, 'type': entry[1], 'link': entry[6],
                       'content': content})
    return result


class _Cbor:
    """Restricted Qt ELF-note CBOR reader; bounded values, never executable."""
    def __init__(self, data):
        self.data, self.offset, self.values = data, 0, 0

    def read(self, depth=0):
        self.values += 1
        if depth > 8 or self.values > 256:
            raise Failure('Metadados Qt excessivos.')
        lead = _slice(self.data, self.offset, 1)[0]
        self.offset += 1
        major, argument = lead >> 5, lead & 31
        if argument < 24:
            length = argument
        elif argument in (24, 25, 26, 27):
            width = {24: 1, 25: 2, 26: 4, 27: 8}[argument]
            length = int.from_bytes(_slice(self.data, self.offset, width), 'big')
            self.offset += width
        elif argument == 31 and major == 5:
            length = None
        else:
            raise Failure('Formato CBOR Qt não suportado.')
        if major == 0:
            return length
        if major == 1:
            return -1 - length
        if major in (2, 3):
            if length > 4096:
                raise Failure('String CBOR Qt excessiva.')
            result = _slice(self.data, self.offset, length)
            self.offset += length
            return result.decode('utf-8') if major == 3 else result
        if major == 4:
            if length > 64:
                raise Failure('Lista CBOR Qt excessiva.')
            return [self.read(depth + 1) for _ in range(length)]
        if major == 5:
            if length is not None and length > 32:
                raise Failure('Mapa CBOR Qt excessivo.')
            result = {}
            for _ in range(33 if length is None else length):
                if length is None and _slice(self.data, self.offset, 1) == b'\xff':
                    self.offset += 1
                    return result
                key, value = self.read(depth + 1), self.read(depth + 1)
                if not isinstance(key, (str, int)) or key in result:
                    raise Failure('Chave CBOR Qt inválida ou duplicada.')
                result[key] = value
            if length is None:
                raise Failure('Mapa CBOR Qt não terminado ou excessivo.')
            return result
        if major == 7 and lead in (0xf4, 0xf5, 0xf6):
            return {0xf4: False, 0xf5: True, 0xf6: None}[lead]
        raise Failure('Valor CBOR Qt não suportado.')


def inspect_elf(data):
    """Read public ELF structures and Qt's bounded note data, without dlopen."""
    if len(data) > MAX_BINARY:
        raise Failure('Módulo nativo excessivo.')
    sections = _sections(data)
    by_name = {item['name']: item for item in sections}
    if len(by_name) != len(sections):
        raise Failure('Seções ELF duplicadas.')
    needed, paths, requirements = [], [], {}
    for section in sections:
        if section['type'] not in (6, 0x6ffffffe):
            continue
        if section['link'] >= len(sections):
            raise Failure('Tabela de strings ELF inválida.')
        strings = sections[section['link']]['content']
        content = section['content']
        if section['type'] == 6:
            if len(content) % 16:
                raise Failure('Tabela dinâmica ELF truncada.')
            for offset in range(0, len(content), 16):
                tag, value = struct.unpack('<qQ', content[offset:offset + 16])
                if tag == 1:
                    needed.append(_cstring(strings, value))
                elif tag in (15, 29):
                    paths.append(_cstring(strings, value))
        else:
            offset, visits = 0, set()
            while offset < len(content):
                if offset in visits or len(visits) > 128:
                    raise Failure('Tabela de versões ELF cíclica ou excessiva.')
                visits.add(offset)
                version, count, filename, auxiliary, following = struct.unpack('<HHIII', _slice(content, offset, 16))
                if version != 1 or count > 256:
                    raise Failure('Versões ELF não suportadas.')
                library = _cstring(strings, filename)
                versions = requirements.setdefault(library, [])
                position, seen = offset + auxiliary, set()
                for index in range(count):
                    if position in seen:
                        raise Failure('Auxiliares ELF cíclicos.')
                    seen.add(position)
                    _, _, _, name, next_aux = struct.unpack('<IHHII', _slice(content, position, 16))
                    versions.append(_cstring(strings, name))
                    if index < count - 1 and not next_aux:
                        raise Failure('Versões ELF truncadas.')
                    position += next_aux
                if not following:
                    break
                offset += following
    if not needed or len(needed) != len(set(needed)) or set(needed) - NEEDED_LIBRARIES:
        raise Failure('Dependências ELF nativas inesperadas: ' + ', '.join(needed))
    if paths:
        raise Failure('RPATH/RUNPATH recusado no módulo nativo; use as bibliotecas do sistema.')
    if any('PRIVATE' in version for versions in requirements.values() for version in versions):
        raise Failure('ABI privada Qt recusada no módulo nativo.')
    note = by_name.get('.note.qt.metadata')
    if not note or note['type'] != 7:
        raise Failure('Nota de metadados Qt ausente no módulo nativo.')
    content = note['content']
    namesz, descsz, kind = struct.unpack('<III', _slice(content, 0, 12))
    if kind != 0x74510001 or _slice(content, 12, namesz) != b'qt-project!\0':
        raise Failure('Nota Qt nativa incompatível.')
    descriptor = _slice(content, 12 + (namesz + 3) // 4 * 4, descsz)
    version, major, minor, flags = _slice(descriptor, 0, 4)
    if version != 1 or major != 6 or minor < 8 or flags & 0x7f > 1:
        raise Failure('Metadados Qt/CPU do módulo incompatíveis.')
    cbor = _Cbor(descriptor[4:])
    metadata = cbor.read()
    if not isinstance(metadata, dict) or metadata.get(2) != PLUGIN_IID or metadata.get(3) != PLUGIN_CLASS or any(descriptor[4:][cbor.offset:]):
        raise Failure('IID/classe/metadados do plugin Qt incompatíveis.')
    return {'machine': 'x86_64', 'class': 64, 'endian': 'little',
            'needed': sorted(needed), 'versions': {key: sorted(set(value)) for key, value in sorted(requirements.items())},
            'qt': {'major': major, 'minor': minor, 'debug': bool(flags & 0x80),
                   'archLevel': flags & 0x7f, 'metadataVersion': version,
                   'iid': metadata[2], 'className': metadata[3]}}


def _command(arguments, timeout=10):
    process = None
    try:
        process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        # Compiler drivers have children (cc1plus/moc/assembler). Stop only
        # this command's process group before removing its private build stage.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate(timeout=5)
        raise Failure('Tempo limite da ferramenta nativa: ' + str(arguments[0])) from error
    except (OSError, subprocess.SubprocessError) as error:
        raise Failure('Não foi possível executar a ferramenta nativa: ' + str(arguments[0])) from error
    except BaseException:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=5)
        raise
    if process.returncode:
        raise Failure('Ferramenta nativa falhou: ' + str(arguments[0]) + '\n' + stderr[:4000])
    return stdout.strip()


def _version(value):
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', value) if isinstance(value, str) else None
    if not match:
        raise Failure('Versão Qt nativa inválida: ' + str(value))
    return tuple(map(int, match.groups()))


def runtime_info():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'AMD64'):
        raise Failure('O binário nativo desta entrega suporta somente GNU/Linux AMD64.')
    version = _command(['qtpaths6', '--qt-version'])
    if _version(version)[:2] < (6, 8):
        raise Failure('O módulo nativo exige Qt 6.8 ou superior.')
    directory = Path(_command(['qtpaths6', '--query', 'QT_INSTALL_LIBS']))
    directories = [directory, Path('/lib/x86_64-linux-gnu'), Path('/usr/lib/x86_64-linux-gnu')]
    return {'qtVersion': version, 'libraryDirectories': directories}


def _defined_versions(path):
    sections = _sections(regular_system_bytes(path))
    result = set()
    for section in sections:
        if section['type'] != 0x6ffffffd:
            continue
        if section['link'] >= len(sections):
            raise Failure('Versões da biblioteca de execução inválidas.')
        strings, data = sections[section['link']]['content'], section['content']
        offset, seen = 0, set()
        while offset < len(data):
            if offset in seen or len(seen) > 4096:
                raise Failure('Versões da biblioteca de execução excessivas.')
            seen.add(offset)
            version, _, _, count, _, auxiliary, following = struct.unpack('<HHHHIII', _slice(data, offset, 20))
            if version != 1 or count > 256:
                raise Failure('Versões da biblioteca de execução não suportadas.')
            position = offset + auxiliary
            for _ in range(count):
                name, next_aux = struct.unpack('<II', _slice(data, position, 8))
                result.add(_cstring(strings, name))
                position += next_aux
            if not following:
                break
            offset += following
    return result


def regular_system_bytes(path):
    # System soname symlinks are ordinary loader inputs, not package links.
    path = Path(path).resolve(strict=True)
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > 128 * 1024 * 1024:
        raise Failure('Biblioteca de execução irregular ou excessiva: ' + str(path))
    return path.read_bytes()


def check_compatibility(elf, runtime):
    current = _version(runtime['qtVersion'])
    if current[0] != elf['qt']['major'] or current[1] < elf['qt']['minor']:
        raise Failure('O plugin foi compilado para Qt mais novo que o Plasma atual.')
    for name in elf['needed']:
        library = next((directory / name for directory in runtime['libraryDirectories']
                        if (directory / name).is_file()), None)
        if library is None:
            raise Failure('Biblioteca nativa de execução ausente: ' + name)
        required = set(elf['versions'].get(name, []))
        if required and required - _defined_versions(library):
            raise Failure('ABI nativa indisponível em ' + name + ': ' + ', '.join(sorted(required - _defined_versions(library))))


def validate_payload(files, check_runtime=True):
    """Strict prebuilt/ZIP validation; does not load its executable code."""
    expected_sources = source_hashes(files)
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Failure('Chave duplicada no manifesto nativo.')
            result[key] = value
        return result
    try:
        record = json.loads(files[MANIFEST_SOURCE], object_pairs_hook=unique_object)
    except (KeyError, ValueError, TypeError) as error:
        raise Failure('Manifesto do módulo nativo ausente ou inválido.') from error
    if not isinstance(record, dict) or set(record) != {'format', 'module', 'sourceHashes', 'binary', 'build', 'elf'} or record['format'] != FORMAT or type(record['format']) is not int or record['module'] != MODULE_URI or record['sourceHashes'] != expected_sources:
        raise Failure('Manifesto/fontes do módulo nativo divergentes.')
    binary = files.get(BINARY_SOURCE)
    if not isinstance(binary, bytes) or record['binary'] != {'path': BINARY_SOURCE, 'bytes': len(binary), 'sha256': digest(binary)}:
        raise Failure('Hash/tamanho/caminho do módulo nativo divergente.')
    elf = inspect_elf(binary)
    if record['elf'] != elf:
        raise Failure('Manifesto não corresponde aos metadados ELF/Qt nativos.')
    build = record['build']
    if not isinstance(build, dict) or set(build) != {'qtVersion', 'compiler', 'flags'} or not isinstance(build['compiler'], str) or len(build['compiler']) > 512 or build['flags'] != BUILD_FLAGS:
        raise Failure('Identidade de compilação nativa inválida.')
    if _version(build['qtVersion'])[:2] != (elf['qt']['major'], elf['qt']['minor']):
        raise Failure('Versão de compilação não corresponde à nota Qt do binário.')
    if check_runtime:
        check_compatibility(elf, runtime_info())
    return {'status': 'verified_prebuilt', 'binarySha256': digest(binary),
            'qtVersion': build['qtVersion'], 'machine': elf['machine']}


BUILD_FLAGS = ['-std=c++17', '-shared', '-fPIC', '-O2', '-g0', '-DQT_NO_DEBUG',
               '-ffile-prefix-map=STAGE=.', '-fdebug-prefix-map=STAGE=.']


def toolchain(headers_root=None):
    runtime = runtime_info()
    if _command(['pkg-config', '--modversion', 'Qt6Widgets']) != runtime['qtVersion']:
        raise Failure('SDK Qt Widgets e execução Qt precisam ter a mesma versão.')
    cflags = shlex.split(_command(['pkg-config', '--cflags', 'Qt6Widgets']))
    libraries = shlex.split(_command(['pkg-config', '--libs', 'Qt6Widgets']))
    headers = headers_root or os.environ.get('DOMAINOS_NATIVE_HEADERS_ROOT')
    if headers:
        path = Path(headers)
        if not path.is_absolute():
            raise Failure('DOMAINOS_NATIVE_HEADERS_ROOT precisa ser um caminho absoluto.')
        no_links(path)
        version_header = regular_bytes(path / 'QtQml/qtqmlversion.h').decode()
        match = re.search(r'#define\s+QTQML_VERSION_STR\s+"([0-9.]+)"', version_header)
        if not match or match[1] != runtime['qtVersion']:
            raise Failure('Headers Qt QML e execução Qt precisam ter a mesma versão.')
        for name in ('QQmlExtensionPlugin', 'QQmlEngine', 'QQmlComponent'):
            regular_bytes(path / 'QtQml' / name)
        cflags += ['-I' + str(path), '-I' + str(path / 'QtQml'), '-I' + str(path / 'QtQmlIntegration')]
        libraries += ['-l:libQt6Qml.so.6']
    else:
        if _command(['pkg-config', '--modversion', 'Qt6Qml']) != runtime['qtVersion']:
            raise Failure('SDK Qt QML e execução Qt precisam ter a mesma versão.')
        cflags += shlex.split(_command(['pkg-config', '--cflags', 'Qt6Qml']))
        libraries += shlex.split(_command(['pkg-config', '--libs', 'Qt6Qml']))
    if any('rpath' in argument.lower() for argument in (*cflags, *libraries)):
        raise Failure('RPATH do toolchain recusado no módulo nativo.')
    compiler = os.environ.get('CXX', 'c++')
    if not compiler or any(character.isspace() for character in compiler):
        raise Failure('CXX precisa indicar um único compilador, sem argumentos shell.')
    compiler_version = _command([compiler, '--version']).splitlines()[0]
    moc = Path(_command(['qtpaths6', '--query', 'QT_INSTALL_LIBEXECS'])) / 'moc'
    if runtime['qtVersion'] not in _command([str(moc), '--version']):
        raise Failure('moc e execução Qt precisam ter a mesma versão.')
    return {'qtVersion': runtime['qtVersion'], 'compiler': compiler,
            'compilerVersion': compiler_version, 'moc': str(moc),
            'cflags': cflags, 'libraries': libraries}


def _inputs(root):
    return {name: regular_bytes(Path(root) / name) for name in BUILD_INPUTS}


def _build(root, panel, spec):
    directory = panel / 'contents/native/menu'
    source, generated, binary = directory / 'plugin.cpp', directory / 'plugin.moc', directory / 'libdomainosmenuplugin.so'
    geometry_moc = directory / 'moc_scrollgeometry.cpp'
    popup_moc = directory / 'moc_popupwheel.cpp'
    inputs = spec.get('inputFiles') or _inputs(root)
    for name, expected in inputs.items():
        if name.startswith(PANEL_SOURCE + '/') and regular_bytes(panel / name.removeprefix(PANEL_SOURCE + '/')) != expected:
            raise Failure('Fonte nativa mudou durante a preparação do stage: ' + name)
    try:
        _command([spec['moc'], *spec['cflags'], str(source), '-o', str(generated)], timeout=60)
        _command([spec['moc'], *spec['cflags'], str(directory / 'scrollgeometry.h'), '-o', str(geometry_moc)], timeout=60)
        _command([spec['moc'], *spec['cflags'], str(directory / 'popupwheel.h'), '-o', str(popup_moc)], timeout=60)
        flags = [value.replace('STAGE', str(panel)) for value in BUILD_FLAGS]
        _command([spec['compiler'], *flags, *spec['cflags'], str(source),
                  str(directory / 'scrollgeometry.cpp'), str(geometry_moc),
                  str(directory / 'popupwheel.cpp'), str(popup_moc), '-o', str(binary),
                  *spec['libraries']], timeout=120)
    finally:
        generated.unlink(missing_ok=True)
        geometry_moc.unlink(missing_ok=True)
        popup_moc.unlink(missing_ok=True)
    data = regular_bytes(binary)
    if str(panel).encode() in data or b'/irix-domainos-native-menu-sdk-' in data:
        raise Failure('Caminho privado embutido no módulo nativo.')
    if _inputs(root) != inputs:
        raise Failure('Fonte nativa mudou durante a compilação; nenhum componente instalado.')
    files = dict(inputs)
    files[BINARY_SOURCE] = data
    files[MANIFEST_SOURCE] = json_bytes({'format': FORMAT, 'module': MODULE_URI,
        'sourceHashes': source_hashes(files),
        'binary': {'path': BINARY_SOURCE, 'sha256': digest(data), 'bytes': len(data)},
        'build': {'qtVersion': spec['qtVersion'], 'compiler': spec['compilerVersion'], 'flags': BUILD_FLAGS},
        'elf': inspect_elf(data)})
    validate_payload(files)
    (directory / 'native-build.json').write_bytes(files[MANIFEST_SOURCE])
    return {name: files[name] for name in (BINARY_SOURCE, MANIFEST_SOURCE)}


@contextmanager
def prepare_native(root, dry=False, headers_root=None):
    """Yield native stage/payload; source-only dry-run never writes or builds."""
    root = Path(root)
    files = _inputs(root)
    source_hashes(files)
    present = [(root / name).exists() for name in (BINARY_SOURCE, MANIFEST_SOURCE)]
    if any(present):
        if not all(present):
            raise Failure('Binário e manifesto nativos precisam existir juntos.')
        files.update({name: regular_bytes(root / name) for name in (BINARY_SOURCE, MANIFEST_SOURCE)})
        report = validate_payload(files)
        yield {'panel': root / PANEL_SOURCE, 'payload': {name: files[name] for name in (BINARY_SOURCE, MANIFEST_SOURCE)}, 'report': report}
        return
    spec = {**toolchain(headers_root), 'inputFiles': files}
    if dry:
        yield {'panel': root / PANEL_SOURCE, 'payload': {},
               'report': {'status': 'build_required', 'qtVersion': spec['qtVersion'],
                          'machine': 'x86_64', 'compiled': False}}
        return
    with tempfile.TemporaryDirectory(prefix='irix-domainos-native-build-', dir='/tmp') as temporary:
        panel = Path(temporary) / 'applet'
        original = root / PANEL_SOURCE
        for item in original.rglob('*'):
            if item.is_symlink() or not (item.is_file() or item.is_dir()):
                raise Failure('Link/arquivo especial recusado na fonte do applet nativo.')
        shutil.copytree(original, panel)
        payload = _build(root, panel, spec)
        yield {'panel': panel, 'payload': payload,
               'report': {'status': 'built_private_stage', 'qtVersion': spec['qtVersion'],
                          'machine': 'x86_64', 'binarySha256': digest(payload[BINARY_SOURCE])}}


@contextmanager
def prepared_source_pairs(root, pairs, dry=False, headers_root=None):
    """Replace only the applet source, never a resource destination."""
    with prepare_native(root, dry=dry, headers_root=headers_root) as prepared:
        updated, count = [], 0
        for source, destination in pairs:
            if Path(source) == Path(root) / PANEL_SOURCE:
                source, count = prepared['panel'], count + 1
            updated.append((source, destination))
        if count != 1:
            raise Failure('Uma única fonte do applet DomainOS é necessária.')
        print('Módulo nativo DomainOS: ' + json.dumps(prepared['report'], ensure_ascii=False))
        yield updated
