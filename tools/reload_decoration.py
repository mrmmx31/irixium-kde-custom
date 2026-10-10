#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recarrega a decoração IRIX do usuário atual, preservando sua seleção e configurações."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

from theme_transaction import Failure, atomic, decode, edit_ini, image, replace_checked, snapshot

AURORAE = 'org.kde.kwin.aurorae'
BREEZE = 'org.kde.breeze'
IRIX_IDS = {'irix_classic', 'irixium_irix_classic_v4', 'irixium_irix_classic_v5', 'irixium_modern', 'irixium_modern_13', 'irixium_modern_41', 'domainos_sr104'}


def check_session():
    if os.geteuid() == 0 or os.geteuid() != os.getuid():
        raise Failure('Execute no terminal do usuário atual, sem sudo.')
    runtime = Path('/run/user')/str(os.getuid())
    address = os.environ.get('DBUS_SESSION_BUS_ADDRESS', '')
    if (os.environ.get('XDG_RUNTIME_DIR') != str(runtime) or ';' in address
            or address.split(',')[0] != 'unix:path='+str(runtime/'bus')):
        raise Failure('A recarga exige o barramento da sessão KDE do próprio usuário.')
    if not (runtime/'bus').exists() or (runtime/'bus').stat().st_uid != os.getuid():
        raise Failure('Barramento indisponível ou pertencente a outro usuário.')


def kwin(method):
    result = subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.kde.KWin',
                             '--object-path', '/KWin', '--method', 'org.kde.KWin.'+method],
                            capture_output=True, text=True, timeout=15, check=True)
    return ast.literal_eval(result.stdout)[0] if method == 'supportInformation' else None


def selection(call):
    info = call('supportInformation')
    plugin = re.search(r'^Plugin: (.+)$', info, re.M)
    theme = re.search(r'^Theme: (.+)$', info, re.M)
    return plugin[1] if plugin else None, theme[1] if theme else None


def wait_selection(call, expected, *, plugin_only=False, timeout=3):
    """KWin reconfigure is asynchronous; wait for the actual loaded plugin."""
    deadline = time.monotonic()+timeout
    while True:
        actual = selection(call)
        if (actual[0] == expected[0] if plugin_only else actual == expected):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)


def reload(config, state, *, call=kwin, dry=False):
    initial = selection(call)
    if initial[0] != AURORAE or initial[1] not in IRIX_IDS:
        print('A decoração em uso não é uma IRIX deste pacote; seleção preservada.')
        return None
    before = snapshot(config)
    if dry:
        print('Recarga disponível somente para a decoração atual: '+initial[1])
        return None
    receipt = state/uuid.uuid4().hex/'receipt.json'
    record = {'path':str(config), 'before':before, 'selection':initial, 'status':'prepared'}
    atomic(receipt, (json.dumps(record,indent=2)+'\n').encode())
    intermediate = image(edit_ini(decode(before) or b'', 'org.kde.kdecoration2',
                                  {'library':BREEZE}), before.get('mode',0o600))
    replace_checked(config, before, intermediate)
    try:
        # Aurorae caches QML components by theme ID. Using a native plugin
        # releases its QML engine before returning to the same IRIX selection.
        call('reconfigure')
        if not wait_selection(call, (BREEZE, None), plugin_only=True):
            raise Failure('KWin não carregou a decoração nativa para liberar o QML antigo.')
    finally:
        replace_checked(config, intermediate, before)
        call('reconfigure')
    if not wait_selection(call, initial):
        raise Failure('A seleção da decoração não voltou ao estado anterior. Backup: '+str(receipt))
    record['status'] = 'reloaded'
    record['after'] = snapshot(config)
    atomic(receipt, (json.dumps(record,indent=2)+'\n').encode())
    print('Decoração recarregada: '+initial[1]+'. Configuração original preservada.')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true')
    args = parser.parse_args()
    check_session()
    from install_suite import roots
    _, config, state = roots()
    reload(config/'kwinrc', state/'irixium-decoration-reload', dry=args.verificar)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(f'ERRO: {exc}')
