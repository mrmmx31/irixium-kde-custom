#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Seleciona apenas o GTK do perfil, pelo módulo KDE, com backup local verificável."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

from components import catalog
from theme_transaction import Failure, atomic, no_links, snapshot, replace_checked


def edit_gtkrc(original, values):
    text = original.decode('utf-8')
    for key, value in values.items():
        line = key+'='+json.dumps(value, ensure_ascii=False)+'\n'
        pattern = re.compile(r'^\s*'+re.escape(key)+r'\s*=.*(?:\n|$)', re.M)
        text = pattern.sub(lambda _: line, text) if pattern.search(text) else text.rstrip('\n')+'\n'+line
    return text.encode('utf-8')


def native_ready():
    from reload_decoration import check_session
    try:
        check_session()
    except Failure:
        return False
    return True


def gtk_paths(config, home=None):
    home = Path.home() if home is None else home
    value = os.environ.get('GTK2_RC_FILES', '')
    rc = Path(value) if value and ':/' not in value else home/'.gtkrc-2.0'
    if not rc.is_absolute() or not rc.is_relative_to(home):
        raise Failure('GTK2_RC_FILES aponta para fora deste perfil; seleção GTK recusada.')
    return [rc, *[config/f'gtk-{version}'/name for version in ('3.0', '4.0')
                  for name in ('settings.ini', 'window_decorations.css')]]


def notify(theme=None):
    """KDE updates GTK2, GTK3/4, GSettings and live XSettings on this user's bus."""
    from reload_decoration import check_session
    check_session()
    method = 'gtkTheme' if theme is None else 'setGtkTheme'
    command = ['gdbus', 'call', '--session', '--dest', 'org.kde.kded6',
               '--object-path', '/modules/gtkconfig', '--method', 'org.kde.GtkConfig.'+method]
    if theme is not None:
        command.append(theme)
    result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=True)
    return ast.literal_eval(result.stdout)[0] if theme is None else None


def gsettings(value=None):
    command = ['gsettings', 'get' if value is None else 'set', 'org.gnome.desktop.interface', 'gtk-theme']
    if value is not None:
        command.append(value)
    result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=True)
    return result.stdout.strip() if value is None else None


def restore_previous(files, *, theme=None, settings=None, notify_call=None, settings_call=None):
    """Try every recovery step even when the live KDE bus is unavailable."""
    errors = []
    for label, callback, value in (('KDE GTK', notify if notify_call is None else notify_call, theme),
                                  ('GSettings GTK', gsettings if settings_call is None else settings_call, settings)):
        if value is None:
            continue
        try:
            callback(value)
        except BaseException as exc:
            errors.append(label+': '+str(exc))
    for path, previous in files.items():
        try:
            replace_checked(path, snapshot(path), previous)
        except BaseException as exc:
            errors.append(str(path)+': '+str(exc))
    return errors


def record_failure(receipt, record, error, recovery_errors):
    """Keep the original error and incomplete recovery in the private journal."""
    record.update(status='recovery_needed' if recovery_errors else 'failed_restored',
                  error=type(error).__name__+': '+str(error),
                  recovery_errors=list(recovery_errors))
    try:
        atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
    except BaseException as exc:
        recovery_errors.append('Registro da recuperação: '+str(exc))
    if recovery_errors:
        raise Failure('Falha na seleção: '+str(error)+
                      '; recuperação incompleta: '+'; '.join(recovery_errors)+
                      '. Backup: '+str(receipt.parent)) from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tema', choices=('classic', 'moderno'), nargs='?')
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--restaurar', action='store_true')
    args = parser.parse_args()
    from reload_decoration import check_session
    check_session()
    from install_suite import roots
    data, config, state = roots()
    state = state/'irixium-gtk-selection'
    paths = gtk_paths(config)
    for path in paths:
        no_links(path)
    if args.restaurar:
        token = (state/'latest').read_text().strip()
        if len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
            raise Failure('Referência de backup inválida.')
        receipt = json.loads((state/token/'receipt.json').read_text())
        if {Path(v['path']) for v in receipt['files']} != set(paths):
            raise Failure('O recibo não corresponde aos arquivos GTK deste perfil.')
        if (notify() != receipt['theme_after'] or gsettings() != receipt['gsettings_after'] or
                any(snapshot(Path(v['path'])) != v['after'] for v in receipt['files'])):
            raise Failure('Configurações GTK alteradas após a seleção; restauração recusada.')
        if not args.verificar:
            errors = restore_previous({Path(v['path']): v['before'] for v in receipt['files']},
                                      theme=receipt['theme_before'], settings=receipt['gsettings_before'])
            if errors:
                record_failure(state/token/'receipt.json', receipt,
                               Failure('Restauração GTK incompleta.'), errors)
            receipt['status'] = 'restored'
            atomic(state/token/'receipt.json', (json.dumps(receipt, indent=2)+'\n').encode())
        print('GTK anterior restaurado.' if not args.verificar else 'Backup GTK conferido.')
        return
    if not args.tema:
        parser.error('informe classic ou moderno')
    theme = catalog()['profiles'][args.tema]['gtk']
    legacy = Path.home()/'.themes'/theme/'gtk-2.0/gtkrc'
    if not legacy.is_file():
        raise Failure('Tema GTK2 não disponível por nome: '+str(legacy)+'. Execute instalar-irixium.sh.')
    for version in ('2.0', '3.0', '4.0'):
        required = data/'themes'/theme/('gtk-'+version)/('gtkrc' if version == '2.0' else 'gtk.css')
        if not required.is_file():
            raise Failure('Tema GTK incompleto: '+str(required)+'. Execute instalar-irixium.sh.')
    current = notify()
    old_gsettings = gsettings()
    print('GTK: '+str(current)+' → '+theme+' (somente este usuário)')
    if args.verificar:
        return
    before = {path: snapshot(path) for path in paths}
    token = uuid.uuid4().hex
    receipt = state/token/'receipt.json'
    record = {'status': 'prepared', 'theme_before': current, 'theme_after': theme,
              'gsettings_before': old_gsettings,
              'files': [{'path': str(p), 'before': v} for p, v in before.items()]}
    atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
    try:
        notify(theme)
        if notify() != theme:
            raise Failure('O módulo KDE não confirmou o tema GTK.')
        # KDE recreates Gtk2's rc; retain modes of any existing private files.
        for path, previous in before.items():
            if previous['exists'] and path.exists():
                no_links(path)
                os.chmod(path, previous['mode'])
        record.update(status='applied', gsettings_after=gsettings(), files=[
            {'path': str(p), 'before': v, 'after': snapshot(p)} for p, v in before.items()])
        atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
        atomic(state/'latest', (token+'\n').encode())
    except BaseException as exc:
        errors = restore_previous(before, theme=current, settings=old_gsettings)
        record_failure(receipt, record, exc, errors)
        raise
    print('Backup GTK: '+str(receipt.parent))
    print('Reabra os aplicativos GTK para carregar todos os controles.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit('ERRO: '+str(exc))
