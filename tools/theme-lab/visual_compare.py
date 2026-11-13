#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Create provenance-preserving 1:1 visual comparisons for Theme Lab reviews."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile


ALLOWED_ROOT = Path.home() / 'tempia/domainos-theme-work'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def regular_input(path):
    path = Path(path).absolute()
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ValueError(f'Entrada deve ser arquivo regular, não link: {path}')
    return path


def private_output(path):
    path = Path(path).absolute()
    root = ALLOWED_ROOT.absolute()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f'Saída deve ficar abaixo de {root}.')
    for ancestor in (path, *path.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError('Saída privada não pode atravessar links.')
        if ancestor == root:
            break
    if path.exists():
        info = path.stat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) != 0o700):
            raise ValueError('Diretório de saída existente deve pertencer ao usuário e ter modo 0700.')
        if any(path.iterdir()):
            raise ValueError('Diretório de saída precisa estar vazio para preservar evidências anteriores.')
    else:
        if not path.parent.is_dir():
            raise ValueError('Crie primeiro o diretório pai privado dentro de domainos-theme-work.')
        path.mkdir(mode=0o700)
    return path


def command(name):
    result = shutil.which(name)
    if not result:
        raise RuntimeError(f'ImageMagick não disponível: comando {name}.')
    return result


def image_info(path):
    process = subprocess.run(
        [command('identify'), '-format', '%m\n%w\n%h\n', str(path)],
        check=True, text=True, capture_output=True)
    values = process.stdout.splitlines()
    if len(values) != 3 or values[0] != 'PNG':
        raise ValueError(f'Comparação atual aceita PNG regular: {path}')
    return {'path': str(path), 'width': int(values[1]), 'height': int(values[2]),
            'sha256': sha256(path)}


def atomic_json(path, value):
    payload = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    fd, temporary = tempfile.mkstemp(prefix='.visual-compare-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def compare(left_path, right_path, output_directory, gap_px=16):
    if type(gap_px) is not int or not 0 <= gap_px <= 128:
        raise ValueError('Espaço entre imagens deve ser inteiro de 0 a 128 px.')
    left, right = regular_input(left_path), regular_input(right_path)
    if left == right:
        raise ValueError('Escolha duas entradas distintas; hashes iguais ainda são permitidos.')
    output = private_output(output_directory)
    left_info, right_info = image_info(left), image_info(right)
    side = output / 'side-by-side-1x1.png'
    subprocess.run([command('montage'), str(left), str(right), '-tile', '2x1',
                    '-geometry', f'+{gap_px}+0', '-background', 'none', str(side)], check=True)
    side.chmod(0o600)
    side_info = image_info(side)
    pixel_diff = {'status': 'not_comparable', 'reason': 'dimensions_differ',
                  'rescaled': False}
    if (left_info['width'], left_info['height']) == (right_info['width'], right_info['height']):
        difference = output / 'difference-absolute.png'
        process = subprocess.run([command('compare'), '-metric', 'AE', str(left), str(right),
                                  str(difference)], text=True, capture_output=True)
        if process.returncode not in (0, 1):
            raise RuntimeError(process.stderr.strip() or 'ImageMagick compare falhou.')
        match = re.search(r'\d+', process.stderr)
        if not match:
            raise RuntimeError('ImageMagick não retornou a contagem AE esperada.')
        changed = int(match.group(0))
        difference.chmod(0o600)
        total = left_info['width'] * left_info['height']
        pixel_diff = {'status': 'computed', 'metric': 'absolute_error_pixels',
                      'changed_pixels': changed, 'total_pixels': total,
                      'changed_ratio': changed / total, 'rescaled': False,
                      'image': image_info(difference)}
    receipt = {
        'schema_version': 1,
        'kind': 'theme_lab_visual_comparison',
        'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'inputs': {'left': left_info, 'right': right_info},
        'scale': {'ratio': '1:1', 'rescaled': False, 'gap_px': gap_px},
        'alignment': {
            'status': 'unverified',
            'basis': 'canvas_dimensions_only',
            'manual_review_required': True,
        },
        'side_by_side': side_info,
        'pixel_diff': pixel_diff,
        'acceptance': 'technical_artifact_only; human_visual_review_pending'
    }
    atomic_json(output / 'receipt.json', receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left', type=Path)
    parser.add_argument('right', type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--gap-px', type=int, default=16)
    args = parser.parse_args(argv)
    try:
        receipt = compare(args.left, args.right, args.output_dir, args.gap_px)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    print(args.output_dir / 'receipt.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
