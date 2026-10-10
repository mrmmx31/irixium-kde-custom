#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Atualiza o Kvantum IRIX a partir do esquema de cores do KDE deste usuário."""
from __future__ import annotations
import argparse
from contextlib import redirect_stdout
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
from components import catalog
from kvantum_native_palette import read
from kvantum_palette_runtime import THEMES, accepts, refresh, restore
from select_companions import effective_look_and_feel, kvantum_theme, require_global, theme_profile
from theme_companion_bridge import (effective_widget_style, native_palette_signature,
    palette_export_identity, profile_for, roots, wait_for_native_palette)
from theme_transaction import Failure, no_links


def notify_qt(config, profile):
    require_global(config, profile['global'])
    if effective_widget_style(config).lower() != 'kvantum':
        return 'preserved_independent_application_style'
    # PlasmaIntegration's public events: recreate QStyle, then restore KDE's
    # palette which Kvantum overrides while creating the style. No app restart.
    for event in (2, 0):
        require_global(config, profile['global'])
        if effective_widget_style(config).lower() != 'kvantum':
            raise Failure('O estilo mudou durante a notificação Qt.')
        subprocess.run(['dbus-send', '--session', '--type=signal', '/KGlobalSettings',
            'org.kde.KGlobalSettings.notifyChange', 'int32:'+str(event), 'int32:0'],
            capture_output=True, text=True, timeout=10, check=True)
    return 'native_style_and_palette_sent'


def export_colors(config, profile):
    """Use actual KColorScheme export, including inactive/disabled effects."""
    require_global(config, profile['global'])
    source = native_palette_signature(config)
    before = palette_export_identity(config)
    subprocess.run(['gdbus', 'emit', '--session', '--object-path', '/kdeglobals',
        '--signal', 'org.kde.kconfig.notify.ConfigChanged',
        "@a{saay} {'General': [[byte 67, 111, 108, 111, 114, 83, 99, 104, 101, 109, 101]]}"],
        capture_output=True, text=True, timeout=10, check=True)
    wait_for_native_palette(config, profile, before, source)
    # Only exports the palette already selected. Never sets the GTK theme.
    return source


def run(*, scheme=None, dry=False, restoring=False):
    data, config, state, home = roots()
    if scheme and (restoring or dry):
        raise Failure('--esquema não pode ser combinado com --restaurar ou --dry-run.')
    if scheme and not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', scheme):
        raise Failure('Nome de esquema inválido; use o identificador sem a extensão .colors.')
    if not dry:
        from reload_decoration import check_session
        check_session()
    global_theme = effective_look_and_feel(config)
    name = profile_for(global_theme)
    if restoring:
        results = []
        for theme in THEMES:
            control = state/'irixium-kvantum-palette'/theme/'control.json'
            no_links(control)
            if control.is_file(): results.append(restore(config, state, theme, dry=dry))
        if results and not dry and name:
            profile = catalog()['profiles'][name]
            if kvantum_theme(config/'Kvantum/kvantum.kvconfig') == profile['kvantum']:
                notify_qt(config, profile)
        return {'status': 'restored' if results else 'not_installed', 'results': results}
    if not name:
        raise Failure('Selecione primeiro um dos Temas Globais instalados da suíte.')
    profile = theme_profile(name, data, config, home)
    if effective_widget_style(config).lower() != 'kvantum':
        raise Failure('O estilo de aplicativos atual não é Kvantum; sua escolha foi preservada.')
    if not accepts(kvantum_theme(config/'Kvantum/kvantum.kvconfig'), profile['kvantum']):
        raise Failure('O tema Kvantum atual é independente; sua escolha foi preservada.')
    if scheme:
        subprocess.run(['plasma-apply-colorscheme', scheme], capture_output=True,
            text=True, check=True, timeout=20)
        require_global(config, profile['global'])
    if dry:
        native = read(config)
        preflight = refresh(config, state, profile, notify_style=notify_qt,
            style_name=effective_widget_style, native=native, dry=True)
        return {'status': 'ready_for_native_export', 'profile': name,
            'preflight': preflight,
            'source_signature': native['source_signature'],
            'note': 'A execução exportará as cores via GTKConfig e criará variantes locais recuperáveis.'}
    source = export_colors(config, profile)
    native = read(config)
    if native['source_signature'] != source:
        raise Failure('O esquema mudou durante a exportação; execute novamente.')
    return refresh(config, state, profile, notify_style=notify_qt,
        style_name=effective_widget_style, native=native)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--esquema', help='Aplicar primeiro um esquema instalado, por exemplo DomainOS-SR10-4.')
    parser.add_argument('--dry-run', action='store_true', help='Verificar sem gravar ou emitir notificações.')
    parser.add_argument('--restaurar', action='store_true', help='Restaurar apenas as variantes com recibo deste usuário.')
    args = parser.parse_args()
    with redirect_stdout(sys.stderr):
        result = run(scheme=args.esquema, dry=args.dry_run, restoring=args.restaurar)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit('ERRO: '+str(error))
