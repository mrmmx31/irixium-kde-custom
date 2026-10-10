#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the independent DomainOS 0.2.12-beta.1 archive; never install or publish.

Use explicit resource/support scopes and exclude ignored files. The archive
contains regular files, licenses, editable sources and the user-local installer.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile
from domainos_native_menu import BINARY_SOURCE, prepare_native, validate_payload
from theme_transaction import Failure as NativeFailure

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2.12-beta.1'
NAME = 'irixclassic-domainos-' + VERSION
DATE = (1980, 1, 1, 0, 0, 0)
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_FILES = 512
TARGETS = {
    'plasma/plasmoids/org.irixclassic.domainos.panel': 'plasma/applets/org.irixclassic.domainos.panel',
    'plasma/plasmoids/org.irixclassic.grosview': 'plasma/applets/org.irixclassic.grosview',
    'plasma/desktoptheme/IrixClassicDomainOS': 'plasma/IrixClassicDomainOS',
    'color-schemes/DomainOS-SR10-4.colors': 'colors/DomainOS-SR10.4.colors',
}
SOURCE_ONLY = ('plasma/IrixClassic', 'integrations/thunderbird-domainos')
SUPPORT = ('docs/RELEASE-1.1.0-beta.1.md', 'LICENSE', 'components.json', 'docs/DOMAINOS-0.2.11.md', 'docs/VALIDACAO-DOMAINOS-0.2.11-2026-10-09.md', 'docs/DOMAINOS-0.2.10.md', 'docs/VALIDACAO-DOMAINOS-0.2.10-2026-10-09.md', 'docs/DOMAINOS-0.2.9.md', 'docs/VALIDACAO-DOMAINOS-0.2.9-2026-10-09.md', 'docs/DOMAINOS-0.2.8.md', 'docs/VALIDACAO-DOMAINOS-0.2.8-2026-10-09.md', 'docs/DOMAINOS-0.2.7.md', 'docs/VALIDACAO-DOMAINOS-0.2.7-2026-10-09.md', 'docs/VALIDACAO-DOMAINOS-0.2.6-2026-10-09.md', 'docs/VALIDACAO-DOMAINOS-0.2.5-2026-10-09.md', 'docs/DOMAINOS-AUDITORIA-2026-10-09.md', 'docs/VALIDACAO-DOMAINOS-DICAS-2026-10-09.md',
    'tools/domainos_scrollbar_rules.json', 'docs/DOMAINOS-REGRAS-ROLAGEM.md',
    'docs/DOMAINOS-FILA-REVISAO-VISUAL.md', 'docs/referencias/domainos-sr104/README.md',
    'docs/referencias/domainos-sr104/TRASH-CAN-METRICAS.json',
    'docs/referencias/domainos-sr104/SETA-INFERIOR-ESTADOS.json',
    'docs/referencias/domainos-sr104/CONFIGURACOES-VERIFICADAS.json',
    'docs/referencias/domainos-sr104/trash-can-normal.png',
    'docs/referencias/domainos-sr104/barra-vertical-normal.png',
    'docs/referencias/domainos-sr104/barra-horizontal-normal.png',
    'docs/referencias/domainos-sr104/canto-normal.png',
    'docs/VALIDACAO-DOMAINOS-AJUSTES-2026-10-09.md',
    'docs/VALIDACAO-DOMAINOS-MINIATURAS-PALETA-2026-10-09.md',
    'docs/DOMAINOS-RESILIENCIA-2026-10-09.md', 'tools/monitor_domainos.py', 'tests/test_domainos_monitor.py',
    'tools/install_domainos.py', 'tools/domainos_color_migration.py', 'tests/test_domainos_color_migration.py',
    'tools/domainos_native_menu.py', 'tests/test_domainos_native_menu.py',
    'tests/test_domainos_color_apply.py',
    'tools/configure_domainos_holidays.py', 'tests/test_domainos_holidays.py',
    'tools/activate_domainos.py', 'tools/classic_panel.py',
    'tools/panel_layout.py', 'tools/domainos_style_bridge.py',
    'tools/components.py', 'tools/install_suite.py', 'tools/classic_hook_runtime.py', 'tools/user_bundle.py',
    'tools/theme_transaction.py', 'tools/package_domainos.py', 'tests/test_domainos_package.py',
    'tests/test_domainos_style_bridge.py', 'tests/test_domainos_activation_preferences.py',
    'plasma/tests/test_domainos_native_style_palette.py',
    'plasma/tests/test_domainos_popup_palette.py', 'plasma/tests/test_domainos_controls.py',
    'plasma/tests/test_domainos_palette.py',
    'plasma/tests/test_domainos_tray_refresh_failure.py',
    'plasma/tests/DomainOSNativeStylePalettePreview.qml')
FORBIDDEN_SUFFIXES = {'.pyc', '.pyo', '.log', '.zip', '.xpi', '.so', '.o', '.wav', '.ogg', '.flac'}


class Failure(RuntimeError):
    pass


def digest(content):
    return hashlib.sha256(content).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        return False
    path = PurePosixPath(name)
    # Only this generated native path is allowed. Its independent manifest and
    # ELF/source hashes are required later; every other QA/build .so stays out.
    source_name = name.removeprefix(NAME + '/')
    native_binary = source_name == BINARY_SOURCE
    return not path.is_absolute() and name == path.as_posix() and all(
        part not in ('', '.', '..', '.git', '__pycache__', '.cache', 'local') for part in name.split('/')) \
        and not any(ord(char) < 32 for char in name) and (path.suffix.lower() not in FORBIDDEN_SUFFIXES or native_binary)


def in_scope(name):
    return name in SUPPORT or any(name == source or name.startswith(source + '/')
        for source in (*TARGETS.values(), *SOURCE_ONLY))


def read_file(root, name):
    if not safe_name(name) or not in_scope(name):
        raise Failure('Arquivo fora do escopo DomainOS: ' + name)
    path = root / name
    if any(node.is_symlink() for node in (path, *path.parents)):
        raise Failure('Links de origem recusados: ' + name)
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > MAX_FILE:
        raise Failure('Arquivo ausente, irregular ou excessivo: ' + name)
    return path.read_bytes()


def source_names(root):
    inventory = root / 'ARQUIVOS-DOMAINOS.json'
    if (root / '.git').exists():
        # New approved component sources are included while this release is being
        # committed; ignored artifacts and private caches never enter the archive.
        scopes = [*SUPPORT, *TARGETS.values(), *SOURCE_ONLY]
        command = ['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others',
            '--exclude-standard', '--', *scopes]
        names = set(subprocess.check_output(command).decode().split('\0')) - {''}
        # --cached includes tracked paths removed in the working tree. Exclude
        # only Git's deleted inventory: links and other irregular present paths
        # must still reach read_file's checks, and required SUPPORT stays required.
        deleted = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z',
            '--deleted', '--', *scopes]).decode().split('\0')
        names.difference_update(deleted)
    elif inventory.is_file():
        names = set(json.loads(inventory.read_text())['source_files'])
    else:
        raise Failure('Checkout ou inventário de fontes do pacote necessário.')
    if not set(SUPPORT).issubset(names) or not all(safe_name(name) and in_scope(name) for name in names):
        raise Failure('Inventário incompleto ou fora do escopo independente DomainOS.')
    return sorted(names)


def installer_targets(content):
    tree = ast.parse(content.decode())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'TARGETS' for target in node.targets):
            return ast.literal_eval(node.value)
    raise Failure('Não foi possível conferir os destinos do instalador.')


def build_plan(root=ROOT, native_dry=False):
    root = Path(root).absolute()
    names = source_names(root)
    files = {name: read_file(root, name) for name in names}
    try:
        with prepare_native(root, dry=native_dry) as native:
            files.update(native['payload'])
            names = sorted(set(names) | set(native['payload']))
    except NativeFailure as error:
        raise Failure(str(error)) from error
    if installer_targets(files['tools/install_domainos.py']) != TARGETS:
        raise Failure('O instalador deixou de ter os quatro destinos revisados.')
    original_catalog = json.loads(files['components.json'])
    entries = [entry for entry in original_catalog['components'] if entry['destination'] in TARGETS]
    if len(entries) != 4 or any(entry['root'] != 'data' or TARGETS[entry['destination']] != entry['source'] for entry in entries):
        raise Failure('Catálogo independente incompatível com o instalador.')
    files['components.json'] = json_bytes({'format':1, 'scope':'Independent DomainOS four-component user install',
        'profiles':{'classic':{}, 'moderno':{}}, 'components':entries})
    for source in TARGETS.values():
        if not any(name == source or name.startswith(source + '/') for name in names):
            raise Failure('Componente ausente: ' + source)
    metadata = json.loads(files['plasma/applets/org.irixclassic.domainos.panel/metadata.json'])
    if metadata['KPlugin']['Id'] != 'org.irixclassic.domainos.panel' or metadata['KPlugin']['Version'] != VERSION:
        raise Failure('O applet precisa ser a versão DomainOS ' + VERSION)
    versions = {source:json.loads(files[source + '/metadata.json'])['KPlugin']['Version']
        for source in TARGETS.values() if source + '/metadata.json' in files}
    files['ARQUIVOS-DOMAINOS.json'] = json_bytes({'format':1, 'version':VERSION,
        'source_files':names, 'install_targets':TARGETS, 'corresponding_source_only':SOURCE_ONLY})
    if len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_TOTAL:
        raise Failure('Pacote DomainOS excessivo.')
    return files, versions


def checksum_text(files):
    return ''.join(digest(data) + '  ' + name + '\n' for name, data in sorted(files.items())).encode()


def archive(files, versions):
    payload = dict(files)
    payload['PACOTE.json'] = json_bytes({'format':1, 'kind':'domainos-panel-and-user-installer',
        'version':VERSION, 'channel':'initial-use', 'signed':False, 'install_targets':TARGETS,
        'component_versions':versions, 'corresponding_source_only':SOURCE_ONLY,
        'files':{name:{'sha256':digest(data), 'bytes':len(data)} for name, data in sorted(files.items())}})
    payload['SHA256SUMS'] = checksum_text(payload)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(NAME + '/' + name, DATE)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | (0o755 if name.startswith('tools/') and name.endswith('.py') else 0o644)) << 16
            output.writestr(info, data, compresslevel=9)
    result = buffer.getvalue()
    verify_archive(result)
    return result


def verify_archive(content):
    if len(content) > MAX_TOTAL:
        raise Failure('ZIP excessivo.')
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as package:
            infos = package.infolist()
            names = [item.filename for item in infos]
            if not names or len(names) > MAX_FILES or len(names) != len(set(names)) or any(not safe_name(name) or not name.startswith(NAME + '/') for name in names):
                raise Failure('Inventário ZIP vazio, duplicado ou inseguro.')
            if sum(item.file_size for item in infos) > MAX_TOTAL or any(item.file_size > MAX_FILE for item in infos):
                raise Failure('Conteúdo descompactado excessivo.')
            if any(item.is_dir() or item.flag_bits & 1 or stat.S_IFMT(item.external_attr >> 16) != stat.S_IFREG for item in infos):
                raise Failure('O pacote precisa conter apenas arquivos regulares, sem links.')
            metadata = json.loads(package.read(NAME + '/PACOTE.json'))
            if metadata.get('format') != 1 or metadata.get('version') != VERSION or metadata.get('install_targets') != TARGETS or metadata.get('kind') != 'domainos-panel-and-user-installer':
                raise Failure('Identificação de pacote incompatível.')
            expected = metadata['files']
            if not isinstance(expected,dict) or not set(SUPPORT).issubset(expected):
                raise Failure('Instalador, auxiliares ou manuais ausentes no pacote.')
            if set(names) != {NAME + '/' + name for name in expected} | {NAME + '/PACOTE.json', NAME + '/SHA256SUMS'}:
                raise Failure('Arquivo ausente ou não declarado no manifesto.')
            files = {}
            for name, record in expected.items():
                if not safe_name(name) or not (in_scope(name) or name == 'ARQUIVOS-DOMAINOS.json'):
                    raise Failure('Arquivo fora do escopo no ZIP.')
                data = package.read(NAME + '/' + name)
                if digest(data) != record['sha256'] or len(data) != record['bytes']:
                    raise Failure('Hash/tamanho divergente: ' + name)
                files[name] = data
            files['PACOTE.json'] = package.read(NAME + '/PACOTE.json')
            if package.read(NAME + '/SHA256SUMS') != checksum_text(files):
                raise Failure('SHA256SUMS interno divergente.')
            if installer_targets(files['tools/install_domainos.py']) != TARGETS:
                raise Failure('Destinos do instalador divergentes.')
            panel=json.loads(files['plasma/applets/org.irixclassic.domainos.panel/metadata.json'])
            if panel['KPlugin']['Id']!='org.irixclassic.domainos.panel' or panel['KPlugin']['Version']!=VERSION:
                raise Failure('Identidade/versão do painel incompatível.')
            if any(not any(name==source or name.startswith(source+'/') for name in expected) for source in TARGETS.values()):
                raise Failure('Componente instalado ausente no ZIP.')
            # Inspect bytes only; archive verification does not dlopen code or
            # assume this host is the target ABI. The installer checks runtime.
            validate_payload(files, check_runtime=False)
            return {'version':VERSION, 'files':len(infos), 'sha256':digest(content),
                'bytes':len(content), 'integrity':'verified', 'signed':False}
    except (zipfile.BadZipFile, KeyError, ValueError, TypeError, OSError, NativeFailure) as error:
        raise Failure('Não foi possível validar o ZIP: ' + str(error)) from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, help='Diretório novo para o ZIP, hashes e registro de distribuição')
    parser.add_argument('--verificar', action='store_true', help='Conferir os inputs sem gerar arquivos')
    parser.add_argument('--verificar-pacote', type=Path, help='Conferir um ZIP já gerado, sem instalar')
    args = parser.parse_args()
    if args.verificar_pacote:
        print(json.dumps(verify_archive(args.verificar_pacote.read_bytes()), ensure_ascii=False))
        return 0
    files, versions = build_plan(native_dry=args.verificar)
    if args.verificar:
        native_status = 'verified_prebuilt' if BINARY_SOURCE in files else 'build_required'
        print(json.dumps({'status':'ready' if BINARY_SOURCE in files else 'build_required', 'native_plugin':native_status,
            'version':VERSION, 'source_files':len(files), 'install_targets':len(TARGETS)}, ensure_ascii=False))
        return 0
    if args.saida is None:
        parser.error('Escolha --saida para um diretório novo, ou --verificar')
    output = args.saida.absolute()
    if output.exists() or any(node.is_symlink() for node in (output, *output.parents)):
        parser.error('O destino precisa ser novo e não pode passar por links')
    content = archive(files, versions)
    verified = verify_archive(content)
    record = {'format':1, 'version':VERSION, 'kind':'standalone-domainos', 'channel':'initial-use',
        'archive':NAME + '.zip', 'verification':verified, 'install_targets':TARGETS,
        'component_versions':versions, 'signed':False,
        'scope':'Four user-local resource destinations; manual activation is separate. No global configuration, user state, audio, icon pack or remote publication.'}
    output.mkdir(mode=0o755, parents=True)
    (output / (NAME + '.zip')).write_bytes(content)
    (output / 'DISTRIBUICAO.json').write_bytes(json_bytes(record))
    (output / 'SHA256SUMS').write_bytes(checksum_text({NAME + '.zip':content, 'DISTRIBUICAO.json':json_bytes(record)}))
    print(json.dumps({'status':'built', 'output':str(output), **verified}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Failure, OSError, subprocess.SubprocessError) as error:
        sys.exit('ERRO: ' + str(error))
