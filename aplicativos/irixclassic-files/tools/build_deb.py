#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Package a tested private bundle. No installation, maintainer scripts or MIME changes."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from runtime_install import verify, Failure, VERSION, ID

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'irixclassic-files'
DEBIAN_VERSION = VERSION.replace('-alpha', '~alpha') + '-1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, cwd=None, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--fonte', type=Path, required=True, help='Corresponding-source tar.gz from the successful build')
    parser.add_argument('--saida', type=Path, required=True, help='New output directory')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure('Build as a regular user; no sudo is needed')
    for tool in ('dpkg', 'dpkg-deb', 'dpkg-shlibdeps', 'strip'):
        if not shutil.which(tool):
            raise Failure('Missing packaging tool: ' + tool)
    bundle = args.bundle.expanduser().absolute()
    source = args.fonte.expanduser().absolute()
    metadata = verify(bundle)
    if not source.is_file() or source.is_symlink():
        raise Failure('Missing corresponding-source archive')
    # Verify the supplied archive corresponds to these application sources.
    prefix = 'IrixClassic-Files-' + VERSION + '-source/dolphin-debian/src/irixclassic/'
    with tarfile.open(source, 'r:gz') as archive:
        notice_path = prefix.split('/src/irixclassic/', 1)[0] + '/debian/copyright'
        notice_member = archive.getmember(notice_path)
        if not notice_member.isfile():
            raise Failure('Missing upstream copyright notices')
        upstream_notice = archive.extractfile(notice_member).read().decode('utf-8')
        for path in sorted((ROOT / 'src').iterdir()):
            if not path.is_file():
                continue
            member = archive.getmember(prefix + path.name)
            content = archive.extractfile(member)
            if not member.isfile() or content is None or content.read() != path.read_bytes():
                raise Failure('Corresponding source does not match: ' + path.name)
    arch = run(['dpkg', '--print-architecture'])
    if {'amd64': 'x86_64', 'arm64': 'aarch64'}.get(arch) != metadata.get('architecture'):
        raise Failure('Bundle architecture does not match the packaging host')
    output = args.saida.expanduser().absolute()
    if output.exists():
        raise Failure('Choose a new output directory; previous packages are preserved')
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='irixclassic-deb-') as temp:
        work = Path(temp)
        stage = work / 'stage'
        payload = stage / 'usr/lib' / PACKAGE
        payload.mkdir(parents=True)
        for name in ('bin', 'lib'):
            shutil.copytree(bundle / name, payload / name, symlinks=True)
        for path in payload.rglob('*'):
            if path.is_file() and not path.is_symlink():
                run(['strip', '--strip-unneeded', str(path)])
        bindir = stage / 'usr/bin'
        bindir.mkdir(parents=True)
        launcher = bindir / PACKAGE
        launcher.write_text('#!/bin/sh\nexec /usr/lib/irixclassic-files/bin/irixclassic-files "$@"\n')
        launcher.chmod(0o755)
        applications = stage / 'usr/share/applications'
        applications.mkdir(parents=True)
        (applications / (ID + '.desktop')).write_text(
            '[Desktop Entry]\nType=Application\nName=IrixClassic Files (experimental)\n'
            'Comment=Classic file browser based on Dolphin\nExec=irixclassic-files %U\n'
            'Icon=system-file-manager\nTerminal=false\nCategories=System;FileManager;\nStartupNotify=true\n')
        docs = stage / 'usr/share/doc' / PACKAGE
        docs.mkdir(parents=True)
        shutil.copy2(ROOT / 'debian/README.Debian', docs / 'README.Debian')
        (docs / 'copyright').write_text(upstream_notice.replace('Upstream-Name: Dolphin', 'Upstream-Name: IrixClassic Files') + '\n' + (ROOT / 'debian/copyright').read_text())
        shutil.copy2(bundle / 'LICENSE', docs / 'LICENSE')
        control = stage / 'DEBIAN'
        control.mkdir()
        packaging = work / 'debian'
        packaging.mkdir()
        (packaging / 'control').write_text('Source: irixclassic-files\nSection: utils\nPriority: optional\n'
            'Maintainer: mrmmx31 <mrmmx31@users.noreply.github.com>\n\nPackage: irixclassic-files\nArchitecture: any\nDescription: Experimental classic file browser based on Dolphin\n')
        shlibs = packaging / 'shlibs.local'
        shlibs.write_text('libirixclassic-files-private 6 irixclassic-files\nlibirixclassic-files-vcs 6 irixclassic-files\n')
        elf = [path for path in payload.rglob('*') if path.is_file() and not path.is_symlink()]
        dependencies = run(['dpkg-shlibdeps', '-O', '-x' + PACKAGE, '-l' + str(payload / 'lib'),
            '-L' + str(shlibs), *['-e' + str(path) for path in elf]], cwd=work)
        automatic = next(line.split('=', 1)[1] for line in dependencies.splitlines() if line.startswith('shlibs:Depends='))
        names = {item.strip().split()[0] for item in automatic.split(',')}
        extra = [name for name in ('kio6', 'qt6-qpa-plugins', 'qt6-image-formats-plugins') if name not in names]
        depends = ', '.join([automatic, *extra])
        size = sum(path.stat().st_size for path in stage.rglob('*') if path.is_file() and not path.is_symlink())
        (control / 'control').write_text(
            'Package: ' + PACKAGE + '\nVersion: ' + DEBIAN_VERSION + '\nArchitecture: ' + arch + '\n'
            'Maintainer: mrmmx31 <mrmmx31@users.noreply.github.com>\nSection: utils\nPriority: optional\n'
            'Installed-Size: ' + str((size + 1023) // 1024) + '\nDepends: ' + depends + '\n'
            'Homepage: https://github.com/mrmmx31/irixium-kde-custom\n'
            'Description: Experimental classic file browser based on Dolphin\n'
            ' Independent Dolphin-derived browser with Pathfinder, contextual Shelf\n'
            ' and read-only Content Viewer. Keeps per-user settings and does not\n'
            ' replace Dolphin, configure themes or change default file associations.\n')
        (control / 'md5sums').write_text(''.join(
            hashlib.md5(path.read_bytes()).hexdigest() + '  ' + path.relative_to(stage).as_posix() + '\n'
            for path in sorted((stage / 'usr').rglob('*')) if path.is_file() and not path.is_symlink()))
        # Fix permissions independent of the build checkout's umask.
        for path in stage.rglob('*'):
            if path.is_symlink():
                continue
            path.chmod(0o755 if path.is_dir() or path == launcher or path.parent == payload / 'bin' else 0o644)
        filename = PACKAGE + '_' + DEBIAN_VERSION + '_' + arch + '.deb'
        package = output / filename
        env = os.environ.copy()
        env['SOURCE_DATE_EPOCH'] = '1791244800'
        run(['dpkg-deb', '--root-owner-group', '-Zxz', '--build', str(stage), str(package)], env=env)
    shutil.copy2(source, output / source.name)
    files = {path.name: sha(path) for path in (package, output / source.name)}
    (output / 'SHA256SUMS').write_text(''.join(digest + '  ' + name + '\n' for name, digest in files.items()))
    (output / 'RESULTADO-DEB.json').write_text(json.dumps({
        'version': VERSION, 'debian_version': DEBIAN_VERSION, 'architecture': arch,
        'native_tests_passed': True, 'depends': depends, 'files': files,
        'installed': False, 'published': False, 'maintainer_scripts': False,
    }, indent=2) + '\n')
    print('Pacote gerado:', package)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Failure, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print('ERRO:', error, file=sys.stderr)
        sys.exit(1)
