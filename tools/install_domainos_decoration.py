#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install the optional DomainOS SR10.4 window decoration for one user.

Only this decoration's files are installed. Selecting it remains an explicit
action in KDE's Window Decorations settings; no active theme is changed.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

from components import ROOT, catalog
from install_suite import roots
from theme_transaction import Failure, no_links
from user_bundle import Bundle, fingerprint, validate_source

SOURCE = 'decorations/domainos/package'
DESTINATION = 'kwin/decorations/domainos_sr104'


def sources(data):
    entries = [entry for entry in catalog()['components']
               if entry['destination'] == DESTINATION]
    if entries != [{'source': SOURCE, 'root': 'data', 'destination': DESTINATION}]:
        raise Failure('Inventário da decoração DomainOS SR10.4 incompatível.')
    return [(ROOT/SOURCE, data/DESTINATION)]


def validate_package(package):
    no_links(package)
    validate_source(package)
    manifest = package.parent/'MANIFEST.json'
    no_links(manifest)
    expected = json.loads(manifest.read_text())['package']
    if not isinstance(expected, dict) or not {
            'metadata.json', 'contents/ui/main.qml'}.issubset(expected):
        raise Failure('Manifesto da decoração DomainOS SR10.4 incompleto.')
    if fingerprint(package) != expected:
        raise Failure('Manifesto divergente: decorations/domainos.')
    metadata = json.loads((package/'metadata.json').read_text())
    if metadata.get('KPackageStructure') != 'KWin/Decoration' or \
            metadata.get('KPlugin', {}).get('Id') != 'domainos_sr104' or \
            metadata['KPlugin'].get('Name') != 'DomainOS SR10.4':
        raise Failure('Identidade da decoração DomainOS SR10.4 divergente.')


def check_runtime():
    executable = shutil.which('qtpaths6')
    if not executable:
        raise Failure('qtpaths6 ausente; instale o Qt 6 da sua distribuição.')
    qml = Path(subprocess.check_output(
        [executable, '--query', 'QT_INSTALL_QML'], text=True).strip())
    missing = [label for relative, label in (
        ('QtQuick/qmldir', 'QtQuick Qt 6'),
        ('org/kde/kwin/decoration/qmldir', 'Aurorae Qt 6'))
        if not (qml/relative).is_file()]
    if missing:
        raise Failure('Dependências da decoração ausentes: ' + ', '.join(missing)
                      + '. Instale os pacotes da sua distribuição.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true',
                        help='verificar sem criar ou substituir arquivos')
    parser.add_argument('--restaurar', action='store_true',
                        help='restaurar a última instalação independente desta decoração')
    args = parser.parse_args(argv)
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    data, config, state = roots()
    pairs = sources(data)
    bundle = Bundle(state/'irixium-domainos-decoration', [dest for _, dest in pairs])
    if args.restaurar:
        if args.verificar:
            bundle.restore(dry=True)
        else:
            with bundle.locked():
                bundle.restore()
        return 0
    validate_package(pairs[0][0])
    check_runtime()
    if args.verificar:
        bundle.install(pairs, dry=True)
    else:
        with bundle.locked():
            bundle.install(pairs)
        print('DomainOS SR10.4 instalado como opção de decoração neste perfil.')
        print('Selecione em Configurações do Sistema → Cores e temas → Decorações da janela.')
        print('Restauração independente: python3 tools/install_domainos_decoration.py --restaurar')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Failure, OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError) as error:
        sys.exit('ERRO: ' + str(error))
