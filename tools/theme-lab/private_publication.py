# SPDX-License-Identifier: GPL-3.0-or-later
"""Build privately, then publish a directory without replacing another result."""
import ctypes
import os
from pathlib import Path
import shutil
import tempfile


def private_parents(directory):
    missing = []
    directory = Path(directory)
    while not directory.exists():
        missing.append(directory)
        directory = directory.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)


def rename_noreplace(source, destination):
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    if rename is None:
        raise RuntimeError('Publicação segura requer renameat2; resultado não publicado.')
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                       ctypes.c_uint]
    rename.restype = ctypes.c_int
    # AT_FDCWD / RENAME_NOREPLACE: one atomic operation, including an empty target.
    if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def publish_directory(destination, writer):
    destination = Path(destination)
    if '..' in destination.parts or any(path.is_symlink()
            for path in (destination, *destination.parents)):
        raise ValueError('Publicação não pode atravessar links ou ..')
    if destination.exists():
        raise ValueError('Resultado já existe; não substituir.')
    private_parents(destination.parent)
    stage = Path(tempfile.mkdtemp(prefix='.' + destination.name + '-',
                                 dir=destination.parent))
    try:
        result = writer(stage)
        rename_noreplace(stage, destination)
        return result
    finally:
        if stage.exists():
            shutil.rmtree(stage)
