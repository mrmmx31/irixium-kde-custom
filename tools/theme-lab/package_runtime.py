#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Create a relocatable, read-only Theme Lab runtime package."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import pwd
import shutil
import stat


BINARIES = (
    'theme-lab',
    'theme-lab-colors',
    'libtheme-lab-gtk2-press.so',
    'libtheme-lab-gtk4-host.so',
)
R584_ID = 'fe95ddd38ef6f61a941d420f6d3d33f376b4d34032c3fc2cf9cad77834710755'
R584_RECEIPT_SHA256 = '0f11d4aa6cb38c97f93f8035ac4ef7cab3101c944ae9d5925bd5bc5ac3de2c6b'
R584_MANIFEST_SHA256 = '565e5c9095e5ae86df516b819c55a502dcc74af8b5412e42af9e6c4a49d4b0ee'
FILES = (
    'tools/domainos_scrollbar_rules.json',
    'tools/domainos_motif_art.py',
    'tools/kvantum_native_palette.py',
    'tools/kvantum_palette_config.py',
    'tools/theme_transaction.py',
    'gtk/tools/build_kde_domainos.py',
    'gtk/tools/adaptive_assets.py',
    'decorations/domainos/LICENSE',
    'docs/review/I167-GTK2-USER-PALETTE-UPDATE-20261028-R584.json',
    'tools/theme-lab/LICENSE',
    'tools/theme-lab/README.md',
    'tools/theme-lab/sample_controls.json',
    'tools/theme-lab/runtime-dependencies.json',
    'tools/theme-lab/src/native_colors.cpp',
)
TREES = (
    'colors',
    'plasma/IrixClassicDomainOS',
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or '..' in pure.parts or not pure.parts:
        raise ValueError('Caminho de pacote inválido: ' + value)
    return Path(*pure.parts)


def _regular(path: Path, description: str) -> Path:
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError(description + ': ' + str(path)) from None
    return path


def _private_destination(path: Path) -> Path:
    home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    allowed = home / 'tempia' / 'domainos-theme-work'
    path = path.absolute()
    try:
        base_info = allowed.lstat()
        if (stat.S_ISLNK(base_info.st_mode) or not stat.S_ISDIR(base_info.st_mode) or
                base_info.st_uid != os.getuid() or stat.S_IMODE(base_info.st_mode) & 0o022 or
                path.parent != allowed or path.name in ('', '.', '..') or
                path.exists() or path.is_symlink()):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError('O pacote novo deve ficar sob um contêiner do usuário, sem links nem escrita de terceiros, em ~/tempia/domainos-theme-work.') from None
    return path


def _copy_file(source: Path, destination: Path, *, executable: bool = False) -> None:
    _regular(source, 'Recurso regular ausente')
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    destination.chmod(0o700 if executable else 0o600)


def _validate_r584(root: Path, bundle: Path) -> None:
    receipt = root / 'docs/review/I167-GTK2-USER-PALETTE-UPDATE-20261028-R584.json'
    manifest_path = bundle / 'manifest.json'
    if _sha(_regular(receipt, 'Recibo R584 ausente')) != R584_RECEIPT_SHA256:
        raise ValueError('O recibo canônico R584 não confere.')
    if _sha(_regular(manifest_path, 'Manifesto R584 ausente')) != R584_MANIFEST_SHA256:
        raise ValueError('O manifesto canônico R584 não confere.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    generated = manifest.get('generated')
    if (manifest.get('format') != 1 or manifest.get('id') != R584_ID or
            not isinstance(generated, dict) or manifest.get('asset_count') != 112 or
            len(generated) != 113):
        raise ValueError('O bundle R584 não declara a cobertura canônica.')
    for name, expected in generated.items():
        relative = _relative(name)
        source = _regular(bundle / relative, 'Arquivo R584 declarado ausente')
        if _sha(source) != expected:
            raise ValueError('O hash R584 não confere: ' + name)


def build(root: Path, build_dir: Path, output: Path,
          r584_bundle: Path | None = None) -> dict:
    root = root.resolve(strict=True)
    build_dir = build_dir.resolve(strict=True)
    output = _private_destination(output)
    if r584_bundle is None:
        home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        r584_bundle = home / '.local/share/irixium/gtk2-palette' / R584_ID
    r584_bundle = r584_bundle.absolute()
    try:
        bundle_info = r584_bundle.lstat()
        if (stat.S_ISLNK(bundle_info.st_mode) or not stat.S_ISDIR(bundle_info.st_mode) or
                r584_bundle.name != R584_ID):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError('O bundle canônico R584 não está disponível para empacotamento: ' + str(r584_bundle)) from None
    _validate_r584(root, r584_bundle)
    output.mkdir(mode=0o700)
    copied: list[Path] = []
    try:
        for pattern in ('*.py',):
            for source in sorted((root / 'tools/theme-lab').glob(pattern)):
                relative = source.relative_to(root)
                _copy_file(source, output / relative)
                copied.append(output / relative)
        for relative_text in FILES:
            relative = _relative(relative_text)
            _copy_file(root / relative, output / relative)
            copied.append(output / relative)
        for directory_text in TREES:
            directory = _relative(directory_text)
            for source in sorted((root / directory).rglob('*')):
                if source.is_dir() and not source.is_symlink():
                    continue
                relative = source.relative_to(root)
                _copy_file(source, output / relative)
                copied.append(output / relative)
        packaged_r584 = Path('resources/gtk2-r584') / R584_ID
        for source in sorted(r584_bundle.rglob('*')):
            if source.is_dir() and not source.is_symlink():
                continue
            relative = packaged_r584 / source.relative_to(r584_bundle)
            _copy_file(source, output / relative)
            copied.append(output / relative)
        galleries = root / 'plasma/tests/galerias-nativas'
        for source in sorted(galleries.glob('*.py')):
            relative = source.relative_to(root)
            _copy_file(source, output / relative)
            copied.append(output / relative)
        binary_target = output / 'tools/theme-lab/build'
        for name in BINARIES:
            source = build_dir / name
            if name == 'theme-lab-colors' and not source.is_file():
                source = build_dir / 'native-colors' / name
            _copy_file(source, binary_target / name, executable=True)
            copied.append(binary_target / name)
        launcher = output / 'theme-lab'
        launcher.write_text(
            '#!/bin/sh\nset -eu\n'
            'PACKAGE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)\n'
            'exec "$PACKAGE/tools/theme-lab/build/theme-lab" "$@"\n',
            encoding='utf-8')
        launcher.chmod(0o700)
        copied.append(launcher)
        manifest = {
            'schema': 1,
            'kind': 'theme-lab-relocatable-runtime',
            'entrypoint': 'theme-lab',
            'resource_root': '.',
            'mutable_data': '~/tempia/domainos-theme-work/theme-lab-*',
            'files': {str(path.relative_to(output)): _sha(path) for path in sorted(copied)},
        }
        manifest_path = output / 'THEME-LAB-PACKAGE.json'
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        manifest_path.chmod(0o600)
        return manifest
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--r584-bundle', type=Path)
    args = parser.parse_args()
    try:
        manifest = build(args.root, args.build_dir, args.output, args.r584_bundle)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({'status': 'ok', 'output': str(args.output.absolute()),
                      'files': len(manifest['files'])}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
