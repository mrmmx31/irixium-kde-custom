#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the user-local DomainOS GTK2 pixbuf engine for the host GTK2 ABI."""
from __future__ import annotations

import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'gtk/engines/domainos-pixbuf'
SOURCES = (
    'pixbuf-draw.c', 'pixbuf-main.c', 'pixbuf-render.c', 'pixbuf-rc-style.c',
)


def _pkg_config(*args: str) -> str:
    try:
        result = subprocess.run(
            ['pkg-config', *args, 'gtk+-2.0'], check=True, capture_output=True,
            text=True)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, 'stderr', '')
        raise RuntimeError(
            'Para compilar o mecanismo GTK2, instale o compilador C, pkg-config '
            'e os headers de desenvolvimento GTK2 (por exemplo, '
            '`build-essential pkg-config libgtk2.0-dev`). ' + detail.strip()) from error
    return result.stdout.strip()


def build(output: Path) -> dict[str, str]:
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise RuntimeError('O arquivo de saída já existe; escolha um caminho novo.')
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise RuntimeError('A pasta de saída deve existir e não pode ser um link.')
    for name in (*SOURCES, 'pixbuf.h', 'pixbuf-style.h', 'pixbuf-rc-style.h', 'COPYING.LIB'):
        path = SOURCE / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError('Fonte GTK2 ausente ou irregular: ' + name)

    version = _pkg_config('--modversion')
    if not version.startswith('2.'):
        raise RuntimeError('O engine DomainOS GTK2 requer GTK2; versão encontrada: ' + version)
    cflags = shlex.split(_pkg_config('--cflags'))
    libs = shlex.split(_pkg_config('--libs'))
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    command = [*compiler, '-fPIC', '-shared', '-Wl,-z,defs',
               '-Wno-deprecated-declarations', *cflags,
               *(str(SOURCE / source) for source in SOURCES),
               '-o', str(output), *libs, '-lm']
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        output.unlink(missing_ok=True)
        raise RuntimeError('Falha ao compilar o mecanismo GTK2 DomainOS.') from error
    return {'gtk2_version': version, 'output': str(output)}


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print('Uso: build_domainos_gtk2_engine.py /caminho/novo/libdomainos-pixbuf.so',
              file=sys.stderr)
        return 2
    try:
        result = build(Path(argv[0]))
    except (OSError, RuntimeError) as error:
        print('ERRO: ' + str(error), file=sys.stderr)
        return 1
    print(f"GTK2 {result['gtk2_version']}: {result['output']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
