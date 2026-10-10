#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install only DomainOS, gr_osview, its Plasma Style and colors for one user.

No profile application, panel insertion, cache refresh, D-Bus signal or hook.
The independent receipt can restore just these four component destinations.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

from components import ROOT, catalog
from install_suite import roots, check_domainos_qt
from theme_transaction import Failure
from user_bundle import Bundle
from domainos_color_migration import LEGACY_FILENAME, prepare_migration, install_with_migration, restore_migration
from domainos_native_menu import prepared_source_pairs

TARGETS = {
    'plasma/plasmoids/org.irixclassic.domainos.panel': 'plasma/applets/org.irixclassic.domainos.panel',
    'plasma/plasmoids/org.irixclassic.grosview': 'plasma/applets/org.irixclassic.grosview',
    'plasma/desktoptheme/IrixClassicDomainOS': 'plasma/IrixClassicDomainOS',
    'color-schemes/DomainOS-SR10-4.colors': 'colors/DomainOS-SR10.4.colors',
}


def sources(data):
    """Constrain the shared inventory to the four explicitly allowed destinations."""
    entries = {entry['destination']: entry for entry in catalog()['components']
               if entry['destination'] in TARGETS}
    if set(entries) != set(TARGETS) or any(entries[dest]['root'] != 'data'
            or entries[dest]['source'] != source for dest, source in TARGETS.items()):
        raise Failure('Inventário DomainOS incompatível: os quatro componentes esperados precisam existir.')
    return [(ROOT/source, data/dest) for dest, source in TARGETS.items()]


def check_runtime(data):
    """Native dependencies of these components, without unrelated suite themes."""
    required = ('plasmashell', 'qtpaths6', 'qdbus6', 'kreadconfig6', 'ksystemstats')
    missing = [name for name in required if not shutil.which(name)]
    if shutil.which('qtpaths6'):
        check_domainos_qt()
        qml = Path(subprocess.check_output(['qtpaths6', '--query', 'QT_INSTALL_QML'], text=True).strip())
        # Plasmoid/configuration are registered by the Plasma host, not separate
        # qmldir files. Require the genuine host and check only file-backed modules.
        modules = ('QtCore', 'QtQml', 'QtQml/Models', 'QtQuick', 'QtQuick/Controls', 'QtQuick/Layouts', 'QtQuick/Window',
            'org/kde/config', 'org/kde/kirigami', 'org/kde/kitemmodels', 'org/kde/kcmutils',
            'org/kde/kwindowsystem',
            'org/kde/ksvg', 'org/kde/ksysguard/sensors', 'org/kde/ksysguard/formatter',
            'org/kde/taskmanager', 'org/kde/plasma/core', 'org/kde/plasma/components',
            'org/kde/plasma/extras', 'org/kde/plasma/plasma5support',
            'org/kde/plasma/private/digitalclock', 'org/kde/plasma/private/kicker',
            'org/kde/plasma/private/keyboardindicator',
            'org/kde/plasma/private/pager', 'org/kde/plasma/private/taskmanager',
            'org/kde/plasma/private/mpris', 'org/kde/plasma/private/volume',
            'org/kde/plasma/private/systemtray', 'org/kde/plasma/private/sessions',
            'org/kde/plasma/workspace/calendar', 'org/kde/plasma/workspace/dbus')
        missing.extend(module.replace('/', '.') + ' Qt 6' for module in modules if not (qml/module/'qmldir').is_file())
    native_data = [data] + [Path(value) for value in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(os.pathsep) if value]
    for relative in ('plasma/plasmoids/org.kde.plasma.systemtray/contents/ui/main.qml',
                     'plasma/plasmoids/org.kde.plasma.taskmanager/contents/ui/ContextMenu.qml',
                     'plasma/plasmoids/org.kde.plasma.taskmanager/contents/ui/PulseAudio.qml'):
        if not any((base/relative).is_file() for base in native_data):
            missing.append(relative + ' do Plasma 6')
    if not any(shutil.which(name) for name in ('kioclient6', 'kioclient', 'gtk-launch')):
        missing.append('launcher de aplicativos KDE/GTK')
    python = Path('/usr/bin/python3')
    if not python.is_file() or subprocess.run([str(python), '-c', 'from PyQt6 import QtCore, QtDBus'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        missing.append('PyQt6 QtCore/QtDBus do Python da distribuição')
    if missing:
        raise Failure('Dependências nativas DomainOS ausentes: ' + ', '.join(missing)
            + '. Instale os pacotes da sua distribuição antes de continuar. Nenhum pacote de sistema foi alterado.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true', help='verificar sem substituir componentes')
    parser.add_argument('--restaurar', action='store_true', help='restaurar a última instalação independente DomainOS')
    parser.add_argument('--recuperar', action='store_true', help='concluir a restauração de uma migração interrompida; exige --restaurar')
    args = parser.parse_args()
    if args.recuperar and not args.restaurar:
        parser.error('--recuperar exige --restaurar')
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    data, config, state = roots()
    pairs = sources(data)
    # Old receipts remain restorable after correcting the installed scheme ID.
    legacy = data/'color-schemes'/LEGACY_FILENAME
    bundle = Bundle(state/'irixium-domainos', [dest for _, dest in pairs] + [legacy])
    if args.restaurar:
        restore_migration(data, state, dry=True, recovery=args.recuperar)
        bundle.restore(dry=True)
        if args.verificar:
            return
        else:
            with bundle.locked():
                # Recheck both journals under the component lock before writing
                # either. Restore the old scheme before removing its replacement.
                restore_migration(data, state, dry=True, recovery=args.recuperar)
                bundle.restore(dry=True)
                restore_migration(data, state, recovery=args.recuperar)
                bundle.restore()
        return
    check_runtime(data)
    # A checkout compiles only into a disposable applet stage. Archives reuse
    # their verified native payload. Both finish before any install journal.
    with prepared_source_pairs(ROOT, pairs, dry=args.verificar) as prepared:
        migration = prepare_migration(data, state)
        install_with_migration(bundle, prepared, migration, dry=args.verificar)
    if not args.verificar:
        print('DomainOS, gr_osview, seu Plasma Style e esquema de cores instalados somente neste perfil.')
        print('Preferências e painel ativo preservados. Adicione o widget Irix Classic DomainOS quando quiser utilizá-lo.')
        print('Restauração independente: python3 tools/install_domainos.py --restaurar')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit('ERRO: ' + str(error))
