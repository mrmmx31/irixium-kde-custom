#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Package all three user themes with an already verified native DomainOS plugin.

Theme resources come from --origem; public installer helpers come from this
script's distribution. No compiler, user profile, service or GUI is invoked.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile
import zipfile

sys.dont_write_bytecode = True
from domainos_native_menu import BINARY_SOURCE, MANIFEST_SOURCE, BUILD_INPUTS, validate_payload
from package_domainos import verify_archive, NAME as NATIVE_PACKAGE
from theme_companion_bridge import MODULES as COMPANION_MODULES
from domainos_style_bridge import MODULES as PANEL_MODULES
from theme_transaction import Failure, no_links
from user_bundle import fingerprint, validate_source

ROOT = Path(__file__).resolve().parents[1]
NAME = 'irix-suite-1.1.0-beta.2'
PROFILES = frozenset(('classic', 'moderno', 'domainos'))
SUPPORT = (
    'LICENSE', 'docs/RELEASE-1.1.0-beta.2.md', 'docs/DISTRIBUICAO-SUITE.md', 'docs/INSTALACAO-RECUPERAVEL.md',
    'tools/domainos_scrollbar_rules.json', 'docs/DOMAINOS-REGRAS-ROLAGEM.md',
    'docs/DOMAINOS-FILA-REVISAO-VISUAL.md', 'docs/referencias/domainos-sr104/README.md',
    'docs/referencias/domainos-sr104/TRASH-CAN-METRICAS.json',
    'docs/referencias/domainos-sr104/SETA-INFERIOR-ESTADOS.json',
    'docs/referencias/domainos-sr104/CONFIGURACOES-VERIFICADAS.json',
    'docs/referencias/domainos-sr104/trash-can-normal.png',
    'docs/referencias/domainos-sr104/barra-vertical-normal.png',
    'docs/referencias/domainos-sr104/barra-horizontal-normal.png',
    'docs/referencias/domainos-sr104/canto-normal.png',
    'instalar-irixium.sh', 'aplicar-tema.sh', 'icons/tools/icon_common.py',
    'cursors/tools/cursor_audit.py', 'cursors/tools/xcursor.py',
    'decorations/classic/tools/manage.py', 'decorations/classic/instalar.sh',
    'decorations/classic/hooks/irix-classic-user.sh',
    'tests/test_suite_distribution.py',
    'plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md',
)
TOOLS = tuple(sorted(set(COMPANION_MODULES + PANEL_MODULES + (
    'classic_hook_runtime.py', 'apply_suite.py', 'package_suite.py',
    'package_domainos.py',
))))


def digest(content):
    return hashlib.sha256(content).hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and '..' not in path.parts and \
        path.as_posix() == name and '\\' not in name and ':' not in name


def read_regular(path):
    no_links(path)
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise Failure('Arquivo público ausente ou irregular: ' + str(path))
    return path.read_bytes()


def add_tree(entries, origin, relative):
    path = origin / relative
    no_links(path)
    validate_source(path)
    for item in (path, *sorted(path.rglob('*'))) if path.is_dir() else (path,):
        name = item.relative_to(origin).as_posix()
        if not safe_name(name):
            raise Failure('Caminho de componente inválido: ' + name)
        if item.is_symlink():
            target = os.readlink(item)
            if Path(target).is_absolute() or not item.resolve(strict=True).is_relative_to(path.resolve()):
                raise Failure('Alias de componente externo recusado: ' + name)
            entries[name] = ('link', target)
        elif item.is_dir():
            entries[name] = ('directory', None)
        else:
            entries[name] = ('file', item)


def build_entries(origin, native_package, *, helpers=ROOT):
    origin, helpers = Path(origin).absolute(), Path(helpers).absolute()
    no_links(origin); no_links(helpers)
    catalog_bytes = read_regular(origin / 'components.json')
    catalog = json.loads(catalog_bytes)
    if catalog.get('format') != 1 or set(catalog.get('profiles', {})) != PROFILES or \
            len(catalog.get('components', [])) != 40:
        raise Failure('A distribuição completa exige o catálogo dos três temas e 40 componentes.')
    # Helpers and artwork must agree on the same catalog; do not silently graft
    # an installer for another revision onto an immutable resource snapshot.
    if json.loads(read_regular(helpers / 'components.json')) != catalog:
        raise Failure('Catálogo das fontes e dos auxiliares públicos diverge.')
    entries = {'components.json': ('bytes', catalog_bytes)}
    destinations = set()
    for entry in catalog['components']:
        source, destination = entry.get('source'), entry.get('destination')
        if entry.get('root') not in ('data', 'config') or not isinstance(source, str) or \
                not isinstance(destination, str) or not safe_name(source) or not safe_name(destination):
            raise Failure('Componente fora das raízes/caminhos autorizados.')
        identity = (entry['root'], destination)
        if identity in destinations:
            raise Failure('Destino duplicado no catálogo completo.')
        destinations.add(identity)
        add_tree(entries, origin, source)
        if destination.startswith('kwin/decorations/'):
            manifest_name = str(Path(source).parent / 'MANIFEST.json')
            manifest = read_regular(helpers / manifest_name)
            if json.loads(manifest)['package'] != fingerprint(origin / source):
                raise Failure('Manifesto de decoração divergente: ' + source)
            entries[manifest_name] = ('bytes', manifest)
    for name in (*SUPPORT, *('tools/' + name for name in TOOLS)):
        entries[name] = ('file', helpers / name)
        read_regular(helpers / name)
    # The checkout README advertises optional development/integration helpers
    # outside this graphical delivery. Publish only its distribution manual.
    entries['README.md'] = ('file', helpers / 'docs/DISTRIBUICAO-SUITE.md')
    # The existing independent ZIP verifier checks inventory, hashes, module
    # identity, bounded ELF/Qt metadata and corresponding source without dlopen.
    archive = read_regular(Path(native_package))
    native_report = verify_archive(archive)
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        native_files = {name: package.read(NATIVE_PACKAGE + '/' + name)
                        for name in (*BUILD_INPUTS, BINARY_SOURCE, MANIFEST_SOURCE)}
    for name in BUILD_INPUTS:
        kind, value = entries[name]
        own_bytes = value if kind == 'bytes' else read_regular(value)
        if native_files[name] != own_bytes:
            raise Failure('Plugin pré-compilado pertence a outra revisão das fontes: ' + name)
    validate_payload(native_files, check_runtime=False)
    for name in (BINARY_SOURCE, MANIFEST_SOURCE):
        entries[name] = ('bytes', native_files[name])
    return entries, native_report


def write_archive(entries, destination, native_report):
    destination = Path(destination).absolute()
    no_links(destination)
    if destination.exists() or not destination.parent.is_dir():
        raise Failure('Escolha um arquivo de saída novo em uma pasta existente.')
    if destination.parent.stat().st_uid != os.getuid() and destination.parent != Path('/tmp'):
        raise Failure('A pasta de saída precisa pertencer ao usuário.')
    manifest = {}
    # PAX UTF-8 carries public names only; discard uid/gid, personal usernames,
    # timestamps and source paths. Installed copies remain normally writable.
    with destination.open('xb') as stream:
        try:
            with tarfile.open(fileobj=stream, mode='w:gz', format=tarfile.PAX_FORMAT) as archive:
                for name, (kind, value) in sorted(entries.items()):
                    info = tarfile.TarInfo(NAME + '/' + name)
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ''
                    if kind == 'directory':
                        info.type, info.mode = tarfile.DIRTYPE, 0o755
                        archive.addfile(info)
                    elif kind == 'link':
                        info.type, info.mode, info.linkname = tarfile.SYMTYPE, 0o777, value
                        manifest[name] = {'link': value}
                        archive.addfile(info)
                    else:
                        content = value if kind == 'bytes' else read_regular(value)
                        info.mode = 0o755 if kind == 'file' and value.stat().st_mode & 0o111 else 0o644
                        info.size = len(content)
                        manifest[name] = {'sha256': digest(content), 'bytes': len(content), 'mode': info.mode}
                        archive.addfile(info, io.BytesIO(content))
                report = {'format': 1, 'kind': 'three-complete-user-theme-options',
                    'components': 40, 'native_archive_sha256': native_report['sha256'],
                    'native_binary_sha256': manifest[BINARY_SOURCE]['sha256'],
                    'files': manifest, 'signed': False}
                content = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
                info = tarfile.TarInfo(NAME + '/SUITE.json'); info.mode = 0o644; info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    return {'archive': str(destination), 'sha256': digest(destination.read_bytes()),
        'components': 40, 'files': len(manifest), 'native': native_report,
        'install': 'bash ' + NAME + '/instalar-irixium.sh',
        'selection': 'Installation adds options; choose a Global Theme separately.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origem', type=Path, default=ROOT, help='árvore completa dos 40 recursos')
    parser.add_argument('--pacote-nativo', type=Path, required=True, help='ZIP independente DomainOS pré-compilado')
    parser.add_argument('--saida', type=Path, required=True, help='novo arquivo tar.gz portátil')
    args = parser.parse_args()
    entries, native = build_entries(args.origem, args.pacote_nativo)
    print(json.dumps(write_archive(entries, args.saida, native), ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, tarfile.TarError, zipfile.BadZipFile) as error:
        sys.exit('ERRO: ' + str(error))
