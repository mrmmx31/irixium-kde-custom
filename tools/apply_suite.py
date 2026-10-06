#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply a complete user theme through KDE and select its matching Kvantum style."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from install_suite import roots
from theme_transaction import Failure, atomic, decode, edit_ini, snapshot, replace_checked

PROFILES = {
    'classic': ('org.magpie.irixclassic.desktop', 'IrixClassic', 'irixium_irix_classic_v4'),
    'moderno': ('org.magpie.irixium.desktop', 'Irixium', 'irixium_modern'),
}
# plasma-apply-lookandfeel is invoked without --resetLayout.
CONFIG_FILES = ('kdeglobals', 'kwinrc', 'plasmarc', 'ksplashrc', 'kcminputrc',
                'klaunchrc', 'kded5rc', 'kded6rc', 'konsolerc',
                'gtkrc', 'gtkrc-2.0', 'Trolltech.conf',
                'Kvantum/kvantum.kvconfig')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tema', choices=PROFILES, nargs='?')
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--restaurar', action='store_true')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    data, config, state = roots()
    state = state/'irixium-selection'
    paths = [config/name for name in CONFIG_FILES]
    paths += [config/'kdedefaults'/name for name in CONFIG_FILES if '/' not in name]
    paths += [config/'kdedefaults/package']
    if args.restaurar:
        token = (state/'latest').read_text().strip()
        if len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
            raise Failure('Referência de backup inválida.')
        record = json.loads((state/token/'receipt.json').read_text())
        for entry in record['files']:
            path = Path(entry['path'])
            if path not in paths or snapshot(path) != entry['after']:
                raise Failure(f'Configuração alterada após aplicação: {path}')
        if not args.verificar:
            for entry in record['files']:
                replace_checked(Path(entry['path']), entry['after'], entry['before'])
            print('Configurações anteriores restauradas. Entre novamente na sessão para recarregar tudo.')
        return
    if not args.tema:
        parser.error('informe classic ou moderno')
    package, kvantum, decoration = PROFILES[args.tema]
    for required in (data/'plasma/look-and-feel'/package/'contents/defaults',
                     config/'Kvantum'/kvantum/(kvantum+'.kvconfig'),
                     data/'kwin/decorations'/decoration/'contents/ui/main.qml'):
        if not required.is_file():
            raise Failure(f'Componente ausente: {required}. Execute instalar-irixium.sh.')
    tool = shutil.which('plasma-apply-lookandfeel')
    if not tool:
        raise Failure('plasma-apply-lookandfeel ausente; requer Plasma 6.')
    print(f'Tema global: {package}; Kvantum: {kvantum}; decoração: {decoration}')
    if args.verificar:
        return
    # Capture the user files before KDE changes them; unrelated keys are left to KDE.
    before = {path: snapshot(path) for path in paths}
    token = uuid.uuid4().hex
    receipt = state/token/'receipt.json'
    atomic(receipt, json.dumps({'status':'prepared','files':[
        {'path':str(p),'before':value} for p,value in before.items()]}).encode())
    try:
        kvconfig = config/'Kvantum/kvantum.kvconfig'
        atomic(kvconfig, edit_ini(decode(before[kvconfig]) or b'', 'General', {'theme':kvantum}))
        subprocess.run([tool,'--apply',package],check=True)
    except BaseException:
        for path, previous in before.items():
            replace_checked(path, snapshot(path), previous)
        raise
    record = {'status':'applied','files':[{'path':str(p),'before':previous,'after':snapshot(p)}
                                        for p,previous in before.items()]}
    atomic(receipt,(json.dumps(record,indent=2)+'\n').encode())
    atomic(state/'latest',(token+'\n').encode())
    print(f'Aplicado somente ao usuário atual. Backup: {receipt.parent}')
    print('Reabra os aplicativos para recarregar Kvantum e ícones.')
    print('Para carregar QML atualizado, salve o trabalho e entre novamente na sessão.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(f'ERRO: {exc}')
