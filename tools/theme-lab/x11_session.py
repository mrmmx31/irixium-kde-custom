# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify the exact local X11 transport used by a Theme Lab preview.

Xwayland commonly publishes its X11 socket only in Linux's abstract Unix
namespace. Checking for ``/tmp/.X11-unix/Xn`` therefore rejects a legitimate
session even though XOpenDisplay can authenticate and connect to it. This
module keeps the local-display and private-authority requirements, then proves
the connection and verifies its Unix peer name.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
from pathlib import Path
import re
import socket
import stat


LOCAL_DISPLAY = re.compile(r'(?:unix/)?:(\d+)(?:\.\d+)?')


def _private_authority(path: Path) -> Path:
    try:
        info = path.lstat()
        if (not path.is_absolute() or stat.S_ISLNK(info.st_mode) or
                not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) & 0o077):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError('A autorização X11 deve ser arquivo privado do usuário.') from None
    return path


def _peer_text(peer) -> tuple[str, str]:
    if isinstance(peer, bytes):
        abstract = peer.startswith(b'\0')
        payload = peer[1:] if abstract else peer
        try:
            value = payload.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError('O socket X11 local retornou um nome de transporte inválido.') from None
        return value, 'abstract' if abstract else 'pathname'
    if isinstance(peer, str):
        return peer, 'pathname'
    raise ValueError('O socket X11 local não informou um peer Unix verificável.')


def verify_local_x11(*, display: str | None = None,
                     authority: str | Path | None = None) -> dict:
    """Return a non-secret proof for the authenticated local X11 connection."""
    display = os.environ.get('DISPLAY', '') if display is None else display
    match = LOCAL_DISPLAY.fullmatch(display)
    if not match:
        raise ValueError('A prévia requer um DISPLAY X11 local.')
    number = int(match.group(1))
    authority_value = (os.environ.get('XAUTHORITY', '')
                       if authority is None else str(authority))
    authority_path = Path(authority_value)
    if not authority_path.is_absolute():
        raise ValueError('A autorização X11 deve usar caminho absoluto.')
    authority_path = _private_authority(authority_path)

    library_name = ctypes.util.find_library('X11')
    if not library_name:
        raise ValueError('A biblioteca X11 necessária para validar a sessão não foi encontrada.')
    library = ctypes.CDLL(library_name)
    library.XOpenDisplay.argtypes = [ctypes.c_char_p]
    library.XOpenDisplay.restype = ctypes.c_void_p
    library.XConnectionNumber.argtypes = [ctypes.c_void_p]
    library.XConnectionNumber.restype = ctypes.c_int
    library.XCloseDisplay.argtypes = [ctypes.c_void_p]
    library.XCloseDisplay.restype = ctypes.c_int

    connection = library.XOpenDisplay(display.encode('ascii'))
    if not connection:
        raise ValueError('A conexão X11 local não pôde ser autenticada com a autoridade atual.')
    duplicate = None
    try:
        fd = library.XConnectionNumber(connection)
        duplicate = socket.socket(fileno=os.dup(fd))
        if duplicate.family != socket.AF_UNIX:
            raise ValueError('A conexão do DISPLAY local não usa transporte Unix.')
        peer, transport = _peer_text(duplicate.getpeername())
        expected = f'/tmp/.X11-unix/X{number}'
        if peer != expected:
            raise ValueError('A conexão X11 não corresponde ao número do DISPLAY solicitado.')
    except OSError as error:
        raise ValueError('A conexão X11 local não pôde ter seu transporte validado: ' + str(error)) from None
    finally:
        if duplicate is not None:
            duplicate.close()
        library.XCloseDisplay(connection)

    return {
        'verified': True,
        'display': display,
        'display_number': number,
        'transport': 'unix_' + transport,
        'peer': expected,
        'xauthority': str(authority_path),
        'authority_private': True,
    }
