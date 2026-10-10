#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Select only GTK/Kvantum companions of the already selected Global Theme.

This helper does not apply a Global Theme, color scheme, layout, icons, cursor
or sounds. Native GTK cache updates and already scheduled KDE CSS generation
are outside the file transaction; incomplete recovery is reported explicitly.
"""
from contextlib import contextmanager
import argparse
import ast
import configparser
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

from components import catalog
from select_gtk import gtk_paths, verify_theme_files, wait_for_theme_files, notify, gsettings, restore_previous
from theme_transaction import Failure, atomic, decode, edit_ini, image, no_links, snapshot, replace_checked


def effective_look_and_feel(config):
    """Use public KConfig semantics, including the Plasma kdedefaults fallback."""
    for path in (config / 'kdeglobals', config / 'kdedefaults/kdeglobals'):
        no_links(path)
    environment = dict(os.environ, XDG_CONFIG_HOME=str(config))
    defaults = str(config / 'kdedefaults')
    directories = environment.get('XDG_CONFIG_DIRS') or '/etc/xdg'
    environment['XDG_CONFIG_DIRS'] = ':'.join(dict.fromkeys([defaults, *directories.split(':')]))
    result = subprocess.run(['kreadconfig6', '--file', 'kdeglobals', '--group', 'KDE',
                             '--key', 'LookAndFeelPackage'], env=environment,
                            capture_output=True, text=True, check=True, timeout=10)
    return result.stdout.rstrip('\r\n')


def require_global(config, expected):
    if effective_look_and_feel(config) != expected:
        raise Failure('O Tema Global efetivo mudou ou não corresponde a este perfil; seleção recusada.')


def kvantum_theme(path):
    no_links(path)
    parser = configparser.ConfigParser(interpolation=None, strict=False, default_section='')
    parser.optionxform = str
    parser.read_string((decode(snapshot(path)) or b'').decode('utf-8'))
    return parser.get('General', 'theme', fallback=None)


def kvantum_matches(config, state, theme):
    if kvantum_theme(config/'Kvantum/kvantum.kvconfig') == theme:
        return True
    from kvantum_palette_runtime import owned_selection
    return owned_selection(config, state, theme)


def gtk_matches(current, settings, expected):
    from gtk4_palette_runtime import accepts
    return accepts(current, expected) and ast.literal_eval(settings) == current


def theme_profile(name, data, config, home):
    doc = catalog()
    profile = doc['profiles'].get(name, {})
    if not all(isinstance(profile.get(key), str) and re.fullmatch(r'[A-Za-z0-9_.-]+', profile[key])
               for key in ('global', 'gtk', 'kvantum')):
        raise Failure('O catálogo completo dos temas Classic/Moderno é necessário.')
    gtk, kvantum = profile['gtk'], profile['kvantum']
    required = [config / 'Kvantum' / kvantum / (kvantum + suffix)
                for suffix in ('.kvconfig', '.svg')]
    required += [data / 'themes' / gtk / ('gtk-' + version) /
                 ('gtkrc' if version == '2.0' else 'gtk.css')
                 for version in ('2.0', '3.0', '4.0')]
    required.append(home / '.themes' / gtk / 'gtk-2.0/gtkrc')
    for path in required:
        no_links(path)
        if not path.is_file():
            raise Failure('Companion instalado ausente: ' + str(path))
    return profile


@contextmanager
def locked(state):
    no_links(state)
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = state / 'lock'
    no_links(lock)
    with lock.open('a+b') as stream:
        os.chmod(lock, 0o600)
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Failure('Outra seleção de companions está em andamento.') from exc
        yield


def latest(state, paths):
    pointer = state / 'latest'
    no_links(pointer)
    if not pointer.exists():
        return None
    token = pointer.read_text('ascii').strip()
    if not re.fullmatch(r'[0-9a-f]{32}', token):
        raise Failure('Referência de backup de companions inválida.')
    receipt = state / token / 'receipt.json'
    no_links(receipt)
    record = json.loads(receipt.read_text('utf-8'))
    entries = record.get('files')
    if record.get('format') != 1 or not isinstance(entries, list) or \
            len(entries) != len(paths) or \
            not all(isinstance(value, dict) and isinstance(value.get('path'), str)
                    and 'before' in value for value in entries) or \
            {Path(value['path']) for value in entries} != set(paths):
        raise Failure('O recibo não corresponde aos companions deste perfil.')
    if record.get('status') not in ('prepared', 'applied', 'restoring', 'restored',
                                    'failed_restored', 'recovery_needed') or \
            record.get('profile') not in ('classic', 'moderno') or \
            not all(isinstance(record.get(key), str) for key in (
                'global', 'theme_before', 'theme_after', 'gsettings_before')) or \
            (record['status'] in ('applied', 'restoring', 'restored') and (
                not isinstance(record.get('gsettings_after'), str) or
                any('after' not in value for value in entries))):
        raise Failure('Recibo de companions inválido ou incompleto.')
    for entry in entries:
        decode(entry['before'])
        if 'after' in entry:
            decode(entry['after'])
    return receipt, record


def save(receipt, record):
    atomic(receipt, (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode())


def select(name, data, config, state, home, *, dry=False):
    """Shared entry point for an explicit CLI or future opt-in native observer."""
    profile = theme_profile(name, data, config, home)
    palette_state = state
    state = state / 'irixium-companions'
    paths = [config / 'Kvantum/kvantum.kvconfig', *gtk_paths(config, home)]
    for path in paths:
        no_links(path)
    require_global(config, profile['global'])
    prior = latest(state, paths)
    if prior and prior[1].get('status') in ('prepared', 'restoring', 'recovery_needed'):
        raise Failure('Há seleção interrompida de companions. Preserve o backup antes de continuar: '
                      + str(prior[0].parent))
    current, settings_before = notify(), gsettings()
    if dry:
        require_global(config, profile['global'])
        return {'status': 'ready', 'profile': name, 'global': profile['global'],
                'gtk': profile['gtk'], 'kvantum': profile['kvantum']}
    try:
        matched = gtk_matches(current, settings_before, profile['gtk']) \
            and kvantum_matches(config, palette_state, profile['kvantum'])
        if matched:
            verify_theme_files(paths[1:], current)
            require_global(config, profile['global'])
            return {'status': 'unchanged', 'profile': name}
    except (Failure, ValueError, SyntaxError, configparser.Error):
        pass  # An incomplete stored selection still needs the native setter.
    with locked(state):
        # Recheck after lock acquisition; another companion process may have
        # committed meanwhile. Never overwrite its unfinished journal.
        prior = latest(state, paths)
        if prior and prior[1].get('status') in ('prepared', 'restoring', 'recovery_needed'):
            raise Failure('Há seleção interrompida de companions: ' + str(prior[0].parent))
        require_global(config, profile['global'])
        current, settings_before = notify(), gsettings()
        try:
            matched = gtk_matches(current, settings_before, profile['gtk']) \
                and kvantum_matches(config, palette_state, profile['kvantum'])
            if matched:
                verify_theme_files(paths[1:], current)
                require_global(config, profile['global'])
                return {'status': 'unchanged', 'profile': name}
        except (Failure, ValueError, SyntaxError, configparser.Error):
            pass
        before = {path: snapshot(path) for path in paths}
        kvantum_after = before[paths[0]] if kvantum_matches(config, palette_state, profile['kvantum']) else \
            image(edit_ini(decode(before[paths[0]]) or b'', 'General',
                {'theme': profile['kvantum']}), before[paths[0]].get('mode', 0o600))
        receipt = state / uuid.uuid4().hex / 'receipt.json'
        record = {'format': 1, 'status': 'prepared', 'profile': name,
                  'global': profile['global'], 'theme_before': current,
                  'theme_after': profile['gtk'], 'gsettings_before': settings_before,
                  'files': [{'path': str(path), 'before': value} for path, value in before.items()]}
        save(receipt, record)
        atomic(state / 'latest', (receipt.parent.name + '\n').encode())
        try:
            require_global(config, profile['global'])
            replace_checked(paths[0], before[paths[0]], kvantum_after)
            notify(profile['gtk'])
            if notify() != profile['gtk']:
                raise Failure('O KDE não confirmou o companion GTK.')
            settings_after = gsettings()
            if ast.literal_eval(settings_after) != profile['gtk']:
                raise Failure('GSettings não confirmou o companion GTK.')
            wait_for_theme_files(paths[1:], profile['gtk'])
            if not kvantum_matches(config, palette_state, profile['kvantum']):
                raise Failure('O companion Kvantum não foi confirmado.')
            for path, previous in before.items():
                if previous['exists'] and path.exists():
                    no_links(path)
                    os.chmod(path, previous['mode'])
            require_global(config, profile['global'])
            record.update(status='applied', gsettings_after=settings_after,
                          files=[{'path': str(path), 'before': value, 'after': snapshot(path)}
                                 for path, value in before.items()])
            save(receipt, record)
        except BaseException as error:
            errors = restore_previous(before, theme=current, settings=settings_before,
                                      notify_call=notify, settings_call=gsettings)
            record.update(status='recovery_needed' if errors else 'failed_restored',
                          error=type(error).__name__ + ': ' + str(error), recovery_errors=errors)
            try:
                save(receipt, record)
            except BaseException as journal_error:
                errors.append('Registro da recuperação: ' + str(journal_error))
            if errors:
                raise Failure('Seleção falhou: ' + str(error) + '; recuperação incompleta: '
                              + '; '.join(errors) + '. Backup: ' + str(receipt.parent)) from error
            raise
        return {'status': 'applied', 'profile': name, 'backup': str(receipt.parent)}

def restore(config, state, home, *, dry=False):
    state = state / 'irixium-companions'
    paths = [config / 'Kvantum/kvantum.kvconfig', *gtk_paths(config, home)]
    prior = latest(state, paths)
    if not prior:
        raise Failure('Nenhum backup de companions neste perfil.')
    receipt, record = prior
    if record.get('status') != 'applied':
        raise Failure('O backup não está em estado aplicado; recuperação manual necessária: '
                      + str(receipt.parent))
    def validate():
        require_global(config, record['global'])
        if any(snapshot(Path(value['path'])) != value['after'] for value in record['files']) or \
                notify() != record['theme_after'] or gsettings() != record['gsettings_after']:
            raise Failure('Companions alterados após a seleção; restauração recusada.')
    validate()
    if dry:
        return {'status': 'restore_ready', 'backup': str(receipt.parent)}
    with locked(state):
        # The pointer is part of the guard, not just the ten target files.
        if latest(state, paths)[0] != receipt:
            raise Failure('O backup corrente mudou durante a restauração.')
        validate()
        record['status'] = 'restoring'
        save(receipt, record)
        errors = restore_previous({Path(value['path']): value['before'] for value in record['files']},
                                  theme=record['theme_before'], settings=record['gsettings_before'],
                                  notify_call=notify, settings_call=gsettings)
        record.update(status='recovery_needed' if errors else 'restored', recovery_errors=errors)
        save(receipt, record)
        if errors:
            raise Failure('Restauração dos companions incompleta: ' + '; '.join(errors)
                          + '. Backup: ' + str(receipt.parent))
    return {'status': 'restored', 'backup': str(receipt.parent)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tema', choices=('classic', 'moderno'), nargs='?')
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--restaurar', action='store_true')
    args = parser.parse_args()
    from reload_decoration import check_session
    from install_suite import roots
    check_session()
    data, config, state = roots()
    if args.restaurar:
        result = restore(config, state, Path.home(), dry=args.verificar)
    else:
        if not args.tema:
            parser.error('informe classic ou moderno')
        result = select(args.tema, data, config, state, Path.home(), dry=args.verificar)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit('ERRO: ' + str(error))
