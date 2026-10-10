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

from components import catalog
from select_gtk import (gtk_paths, edit_gtkrc, verify_theme_files, wait_for_theme_files, native_ready, notify as notify_gtk,
                        gsettings as gtk_gsettings, restore_previous, record_failure)

PROFILE_COMPONENTS = catalog()['profiles']
PROFILES = {name: (p['global'], p['kvantum'], p['decoration'])
            for name, p in PROFILE_COMPONENTS.items()}
# plasma-apply-lookandfeel is invoked without --resetLayout.
CONFIG_FILES = ('kdeglobals', 'kwinrc', 'plasmarc', 'ksplashrc', 'kcminputrc',
                'klaunchrc', 'kded5rc', 'kded6rc', 'konsolerc',
                'gtkrc', 'gtkrc-2.0', 'Trolltech.conf',
                'Kvantum/kvantum.kvconfig', 'gtk-3.0/settings.ini', 'gtk-4.0/settings.ini')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tema', choices=PROFILES, nargs='?')
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--restaurar', action='store_true')
    sounds = parser.add_mutually_exclusive_group()
    sounds.add_argument('--sem-sons', action='store_true', help='preservar a seleção de sons')
    sounds.add_argument('--exigir-sons', action='store_true', help='recusar aplicação sem o esquema SGI instalado')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    data, config, state = roots()
    state = state/'irixium-selection'
    paths = [config/name for name in CONFIG_FILES]
    paths += [config/'kdedefaults'/name for name in CONFIG_FILES if '/' not in name]
    paths += [config/'kdedefaults/package']
    paths += [p for p in gtk_paths(config) if p not in paths]
    if args.restaurar:
        token = (state/'latest').read_text().strip()
        if len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
            raise Failure('Referência de backup inválida.')
        receipt = state/token/'receipt.json'
        record = json.loads(receipt.read_text())
        for entry in record['files']:
            path = Path(entry['path'])
            if path not in paths or snapshot(path) != entry['after']:
                raise Failure(f'Configuração alterada após aplicação: {path}')
        gtk = record.get('native_gtk')
        if gtk and (not native_ready() or gtk_gsettings() != gtk['after'] or
                    ('theme_after' in gtk and notify_gtk() != gtk['theme_after'])):
            raise Failure('A seleção GTK nativa mudou; restauração recusada.')
        if not args.verificar:
            errors = restore_previous({Path(v['path']): v['before'] for v in record['files']},
                                      theme=gtk['theme_before'] if gtk else None,
                                      settings=gtk['before'] if gtk else None,
                                      notify_call=notify_gtk, settings_call=gtk_gsettings)
            if errors:
                record_failure(receipt, record, Failure('Restauração da seleção incompleta.'), errors)
            print('Configurações anteriores restauradas. Entre novamente na sessão para recarregar tudo.')
        return
    if not args.tema:
        parser.error('informe classic ou moderno')
    package, kvantum, decoration = PROFILES[args.tema]
    profile = PROFILE_COMPONENTS[args.tema]
    for required in (data/'plasma/look-and-feel'/package/'contents/defaults',
                     config/'Kvantum'/kvantum/(kvantum+'.kvconfig'),
                     data/'kwin/decorations'/decoration/'contents/ui/main.qml',
                     data/'themes'/profile['gtk']/'gtk-2.0/gtkrc',
                     Path.home()/'.themes'/profile['gtk']/'gtk-2.0/gtkrc',
                     data/'themes'/profile['gtk']/'gtk-3.0/gtk.css',
                     data/'themes'/profile['gtk']/'gtk-4.0/gtk.css',
                     data/'icons'/profile['icons']/'index.theme',
                     data/'icons'/profile['cursor']/'index.theme',
                     data/'icons'/profile['cursor']/'cursors/wait',
                     data/'icons'/profile['cursor']/'cursors/progress',
                     data/'color-schemes/Irixium.colors',
                     data/'plasma/desktoptheme'/profile['plasma']/'metadata.desktop',
                     data/'wallpapers'/profile['wallpaper']/'metadata.json',
                     data/'plasma/look-and-feel'/package/'contents/splash/Splash.qml'):
        if not required.is_file():
            raise Failure(f'Componente ausente: {required}. Execute instalar-irixium.sh.')
    sound_theme = None
    if not args.sem_sons:
        from audit_suite import sound_module
        module = sound_module()
        theme = data/'sounds'/module.THEME
        if theme.exists():
            module.validate_theme(theme, module.catalog())
            sound_theme = module.THEME
        elif args.exigir_sons:
            raise Failure('Esquema SGI ausente. Use sons/instalar.sh --origem DIRETORIO; nenhum áudio será baixado.')
    tool = shutil.which('plasma-apply-lookandfeel')
    if not tool:
        raise Failure('plasma-apply-lookandfeel ausente; requer Plasma 6.')
    print(f'Tema global: {package}; Kvantum: {kvantum}; decoração: {decoration}')
    print('Cursor: '+profile['cursor'])
    print('GTK: '+profile['gtk']+'; sons: '+(sound_theme or 'seleção atual preservada (esquema SGI não solicitado/disponível)'))
    if args.verificar:
        return
    # Capture the user files before KDE changes them; unrelated keys are left to KDE.
    before = {path: snapshot(path) for path in paths}
    native_gtk = {'before': gtk_gsettings(), 'theme_before': notify_gtk()} if native_ready() else None
    token = uuid.uuid4().hex
    receipt = state/token/'receipt.json'
    record = {'status':'prepared', 'files':[
        {'path':str(p),'before':value} for p,value in before.items()]}
    if native_gtk:
        record['native_gtk'] = native_gtk
    atomic(receipt, json.dumps(record).encode())
    try:
        kvconfig = config/'Kvantum/kvantum.kvconfig'
        atomic(kvconfig, edit_ini(decode(before[kvconfig]) or b'', 'General', {'theme':kvantum}))
        subprocess.run([tool,'--apply',package],check=True)
        cursor_config = config/'kcminputrc'
        atomic(cursor_config, edit_ini(decode(snapshot(cursor_config)) or b'',
                                       'Mouse', {'cursorTheme': profile['cursor']}))
        for version in ('3.0', '4.0'):
            gtkconfig = config/f'gtk-{version}/settings.ini'
            original = decode(snapshot(gtkconfig)) or b''
            atomic(gtkconfig, edit_ini(original, 'Settings', {
                'gtk-theme-name': PROFILE_COMPONENTS[args.tema]['gtk'],
                'gtk-icon-theme-name': PROFILE_COMPONENTS[args.tema]['icons'],
                'gtk-cursor-theme-name': profile['cursor']}))
        gtk2 = gtk_paths(config)[0]
        atomic(gtk2, edit_gtkrc(decode(before[gtk2]) or b'', {
            'gtk-theme-name': profile['gtk'], 'gtk-icon-theme-name': profile['icons'],
            'gtk-cursor-theme-name': profile['cursor']}), before[gtk2].get('mode', 0o600))
        if native_gtk:
            notify_gtk(profile['gtk'])
            if notify_gtk() != profile['gtk']:
                raise Failure('O KDE não confirmou o tema GTK selecionado.')
            native_gtk['theme_after'] = profile['gtk']
            native_gtk['after'] = gtk_gsettings()
        if native_gtk:
            wait_for_theme_files(gtk_paths(config), profile['gtk'])
        else:
            verify_theme_files(gtk_paths(config), profile['gtk'])
        if sound_theme:
            globals_file = config/'kdeglobals'
            original = decode(snapshot(globals_file)) or b''
            atomic(globals_file, edit_ini(original, 'Sounds', {'Theme': sound_theme}))
        record.update(status='applied', files=[{'path':str(p),'before':previous,'after':snapshot(p)}
                                              for p,previous in before.items()])
        if native_gtk:
            record['native_gtk'] = native_gtk
        atomic(receipt,(json.dumps(record,indent=2)+'\n').encode())
        atomic(state/'latest',(token+'\n').encode())
    except BaseException as exc:
        errors = restore_previous(before, theme=native_gtk['theme_before'] if native_gtk else None,
                                  settings=native_gtk['before'] if native_gtk else None,
                                  notify_call=notify_gtk, settings_call=gtk_gsettings)
        record_failure(receipt, record, exc, errors)
        raise
    print(f'Aplicado somente ao usuário atual. Backup: {receipt.parent}')
    print('Reabra os aplicativos para recarregar Kvantum e ícones.')
    print('Para carregar QML atualizado, salve o trabalho e entre novamente na sessão.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(f'ERRO: {exc}')
