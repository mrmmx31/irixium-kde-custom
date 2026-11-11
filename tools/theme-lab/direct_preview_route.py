# SPDX-License-Identifier: GPL-3.0-or-later
"""Narrow normal-session route for real Qt/Kvantum/Plasma previews.

The child shares only the current X11 display and session bus. Every path it
can write is redirected to an owned private Theme Lab session; the user's KDE
profile is never selected as HOME or an XDG write target.
"""
from __future__ import annotations

import configparser
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile


FAMILIES = frozenset(('qt5', 'qt6', 'kvantum', 'plasma'))


def _owned_private_directory(path: Path, message: str) -> Path:
    try:
        info = path.lstat()
        if (stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or
                info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError(message) from None
    return path


def _session_root(output: Path) -> Path:
    allowed = Path.home().resolve() / 'tempia' / 'domainos-theme-work'
    _owned_private_directory(allowed, 'A raiz privada do Theme Lab deve ser 0700.')
    output = output.absolute()
    try:
        relative = output.relative_to(allowed)
        if not relative.parts:
            raise ValueError
        session = allowed / relative.parts[0]
        _owned_private_directory(session, 'A sessão direta deve ser um diretório 0700 do usuário.')
        current = allowed
        for part in relative.parts:
            current = current / part
            _owned_private_directory(current, 'A saída direta não pode atravessar links ou diretórios compartilhados.')
    except (OSError, ValueError):
        raise ValueError('A prévia direta exige saída em uma sessão 0700 de ~/tempia/domainos-theme-work/.') from None
    return session


def guard(root, output, family, *, embed_window=None, host_pid=None,
          host_bridge=None, host_session_root=None):
    if family not in FAMILIES:
        raise ValueError('A rota direta aceita somente Qt5, Qt6, Kvantum ou Plasma Style.')
    if os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') == 'bwrap':
        raise ValueError('A rota direta não substitui o namespace bwrap já coordenado.')
    root = Path(root).resolve(strict=True)
    output = Path(output).absolute()
    session = _session_root(output)

    display = os.environ.get('DISPLAY', '')
    match = re.fullmatch(r'(?:unix/)?:(\d+)(?:\.\d+)?', display)
    if not match:
        raise ValueError('A prévia direta requer um DISPLAY X11 local.')
    socket_path = Path('/tmp/.X11-unix') / ('X' + match.group(1))
    try:
        info = socket_path.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid not in (0, os.getuid()):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError('O socket do DISPLAY X11 local não pôde ser validado.') from None

    authority = Path(os.environ.get('XAUTHORITY', '')).absolute()
    try:
        info = authority.lstat()
        if (not authority.is_absolute() or stat.S_ISLNK(info.st_mode) or
                not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) & 0o077):
            raise ValueError
    except (OSError, ValueError):
        raise ValueError('A autorização X11 deve ser arquivo privado do usuário.') from None

    bus = os.environ.get('DBUS_SESSION_BUS_ADDRESS', '')
    bus_match = re.fullmatch(r'unix:path=([^,;]+)(?:,guid=[0-9a-fA-F]+)?', bus)
    if not bus_match:
        raise ValueError('A prévia direta requer o barramento D-Bus da sessão atual.')
    try:
        bus_path = Path(bus_match.group(1)).resolve(strict=True)
        info = bus_path.stat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError
    except (OSError, ValueError):
        raise ValueError('O socket D-Bus da sessão não pôde ser validado.') from None

    embedded = embed_window is not None
    if embedded:
        if (type(embed_window) is not int or not 1 <= embed_window <= 0xffffffff or
                type(host_pid) is not int or host_pid <= 0 or host_bridge is None or
                host_session_root is None):
            raise ValueError('Acoplamento Qt/Plasma exige canvas, PID, ponte e sessão privada juntos.')
        bridge = Path(host_bridge).resolve(strict=True)
        if not bridge.is_relative_to(root) or not bridge.is_file():
            raise ValueError('A ponte X11 deve ser um artefato do próprio Theme Lab.')
        if Path(host_session_root).resolve(strict=True) != session:
            raise ValueError('O host e a prévia devem usar a mesma sessão privada.')
        process = Path('/proc') / str(host_pid)
        if process.stat().st_uid != os.getuid():
            raise ValueError('O host da prévia pertence a outro usuário.')
    elif any(value is not None for value in (host_pid, host_bridge, host_session_root)):
        raise ValueError('Parâmetros de host sem canvas de acoplamento foram recusados.')

    # Coupled and detached previews of the same family can run at once.  They
    # must not share HOME/XDG_RUNTIME_DIR (or the gallery proof directory),
    # otherwise one child can overwrite the other's Qt/KDE state or sockets.
    origin = 'coupled' if embedded else 'detached'
    profile = session / 'native-preview-profile' / family / origin
    directories = {}
    for name in ('home', 'config', 'data', 'cache', 'state', 'runtime'):
        directory = profile / name
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory.chmod(0o700)
        directories[name] = directory
    return {
        'verified': True,
        'mode': 'explicit_user_session_x11_reparent' if embedded else 'explicit_user_session_detached',
        'family': family, 'origin': origin, 'uid': os.getuid(),
        'session_root': str(session),
        'profile': {key: str(value) for key, value in directories.items()},
        'display': display, 'xauthority': str(authority),
        'dbus_socket': str(bus_path), 'fixture_root': str(root),
        'embed_window': embed_window, 'host_pid': host_pid,
        'host_bridge': str(bridge) if embedded else None,
        'personal_profile_written': False, 'filesystem_namespace': False,
        'native_renderer': True,
    }


def environment(proof):
    profile = proof['profile']
    return {
        'HOME': profile['home'], 'XDG_CONFIG_HOME': profile['config'],
        'XDG_DATA_HOME': profile['data'], 'XDG_CACHE_HOME': profile['cache'],
        'XDG_STATE_HOME': profile['state'], 'XDG_RUNTIME_DIR': profile['runtime'],
        'QT_QPA_PLATFORM': 'xcb', 'GDK_BACKEND': 'x11', 'NO_AT_BRIDGE': '1',
        'PRIVATE_XEPHYR': '1', 'IRIX_DOMAINOS_PRIVATE_XEPHYR': '1',
        'IRIX_DOMAINOS_DIRECT_PREVIEW': '1',
        'IRIX_DOMAINOS_PREVIEW_ORIGIN': proof['origin'],
        'IRIX_DOMAINOS_SESSION_ROOT': proof['session_root'],
        'IRIX_DOMAINOS_FIXTURE_ROOT': proof['fixture_root'],
    }


def seed_kde_profile(proof, kdeglobals, receipt):
    """Copy only palette/font identity already certified by the recipe."""
    source = Path(kdeglobals).resolve(strict=True)
    payload = source.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    certified = any(item.get('path') == str(source) and item.get('sha256') == digest
                    for item in receipt.get('palette_inputs', [])
                    if isinstance(item, dict))
    if not certified:
        raise ValueError('O kdeglobals atual não coincide com a origem certificada da receita Qt.')
    current = configparser.ConfigParser(interpolation=None, strict=False)
    current.optionxform = str
    current.read_string(payload.decode('utf-8'))
    private = configparser.ConfigParser(interpolation=None, strict=False)
    private.optionxform = str
    keys = {
        'General': ('ColorScheme', 'font', 'fixed', 'menuFont',
                    'smallestReadableFont', 'toolBarFont'),
        'KDE': ('LookAndFeelPackage', 'widgetStyle'),
        'Icons': ('Theme',),
    }
    for section in current.sections():
        if section.startswith('Colors:'):
            private[section] = dict(current[section])
        elif section in keys:
            values = {key: current.get(section, key) for key in keys[section]
                      if current.has_option(section, key)}
            if values:
                private[section] = values
    destination = Path(proof['profile']['config']) / 'kdeglobals'
    fd, temporary = tempfile.mkstemp(prefix='.kdeglobals-', dir=destination.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            private.write(stream, space_around_delimiters=False)
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'path': str(destination), 'source': str(source), 'sha256': digest,
            'sections': private.sections(), 'personal_profile_written': False}


def append_host_arguments(command, *, embed_window=None, host_pid=None,
                          host_bridge=None, host_session_root=None):
    embedded = embed_window is not None
    if embedded != bool(host_pid and host_bridge and host_session_root):
        raise ValueError('Canvas, PID, ponte e sessão do host devem ser informados juntos.')
    if not embedded:
        return command
    return command + [
        '--embed-window', str(embed_window), '--host-pid', str(host_pid),
        '--host-bridge', str(host_bridge),
        '--host-session-root', str(host_session_root),
    ]
