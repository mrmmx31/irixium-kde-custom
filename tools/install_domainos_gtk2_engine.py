#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply or restore only the DomainOS GTK2 endpoint-paint adapter for this user."""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_domainos_gtk2_engine import build
from gtk2_palette_runtime import Roots as PaletteRoots, _active, _validate_active, refresh
from theme_transaction import Failure, no_links
from user_bundle import Bundle

THEME = 'DomainOS-SR10-4-KDE'
ENGINE = 'libdomainos-pixbuf.so'


def selected_theme(home: Path, *, require_domainos=True) -> str:
    env_value = os.environ.get('GTK2_RC_FILES', '')
    if env_value and ':/' not in env_value:
        rc = Path(env_value).expanduser()
        if not rc.is_absolute() or not rc.is_relative_to(home):
            raise Failure('GTK2_RC_FILES aponta para fora deste perfil.')
    else:
        # GTKConfig owns ~/.gtkrc-2.0 when GTK2_RC_FILES chains system and
        # per-user defaults, matching select_gtk.gtk_paths().
        rc = home / '.gtkrc-2.0'
    no_links(rc)
    try:
        text = rc.read_text(encoding='utf-8')
        values = re.findall(r'(?m)^[ \t]*gtk-theme-name[ \t]*=(.*)$', text)
        value = ast.literal_eval(values[-1].strip()) if values else None
    except (OSError, UnicodeError, ValueError, SyntaxError) as error:
        raise Failure('Não foi possível identificar o tema GTK2 selecionado.') from error
    if not isinstance(value, str) or not value:
        raise Failure('O perfil GTK2 não contém um tema selecionado.')
    if require_domainos and value not in (THEME, THEME + '-Reload'):
        raise Failure('O perfil GTK2 não está em uma variante DomainOS SR10.4 KDE.')
    return value


def context(*, restoring=False):
    from install_suite import roots
    data, config, state = roots()
    home = Path.home()
    selected = selected_theme(home, require_domainos=not restoring)
    palette_roots = PaletteRoots(data, config, state, home)
    active = _active(palette_roots)
    if active is None or active[1].get('status') != 'active':
        raise Failure('A paleta dinâmica GTK2 não está ativa; preservo o perfil.')
    _validate_active(palette_roots, active[1])
    if not any(item['name'] in (THEME, THEME + '-Reload') for item in active[1]['themes']):
        raise Failure('O recibo GTK2 ativo não inclui o tema DomainOS selecionado.')
    destination = home / '.gtk-2.0/2.10.0/engines' / ENGINE
    no_links(destination)
    bundle = Bundle(state / 'irixium-domainos-gtk2-engine', [destination])
    return data, config, state, home, selected, palette_roots, destination, bundle


def refresh_palette(data, config, state, home, selected, engine_name, *, dry):
    from gtk2_domainos_palette import prepare_domainos

    renderer = lambda theme, colors, destination: prepare_domainos(
        theme, colors, destination, engine_name=engine_name)
    result = refresh(data, config, state, home, selected, dry=dry,
                     renderers={THEME: renderer})
    return result


def reload_clients():
    try:
        from gtk2_reload_notify import reload_open_windows
        return reload_open_windows()
    except (OSError, RuntimeError) as error:
        return {'status': 'not_sent', 'reason': str(error)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true', help='compilar e conferir sem instalar')
    parser.add_argument('--restaurar', action='store_true', help='voltar só o engine e a receita GTK2')
    parser.add_argument('--recuperar', action='store_true', help='recuperar a última transação interrompida')
    args = parser.parse_args(argv)
    if args.recuperar and not args.restaurar:
        parser.error('--recuperar exige --restaurar')
    if os.geteuid() == 0:
        raise Failure('Execute como o usuário normal, sem sudo.')

    data, config, state, home, selected, palette_roots, destination, bundle = context(
        restoring=args.restaurar)
    work = home / 'tempia/domainos-theme-work/I167/gtk2-engine-stage'
    no_links(work)
    work.mkdir(parents=True, exist_ok=True, mode=0o700)
    stage = work / (uuid.uuid4().hex + '-' + ENGINE)

    if args.restaurar:
        latest = bundle.latest()
        if latest is None or latest[1].get('status') != 'installed':
            raise Failure('Não há atualização GTK2-only instalada por este comando para restaurar.')
        if args.verificar:
            result = refresh_palette(data, config, state, home, selected, 'pixmap', dry=True)
            print('Paleta GTK2 em modo DomainOS/pixmap:', result.get('status'))
            bundle.restore(dry=True)
            return 0
        result = refresh_palette(data, config, state, home, selected, 'pixmap', dry=False)
        bundle.restore()
        reload_result = reload_clients()
        print(json.dumps({'palette': result, 'engine': 'restored', 'reload': reload_result},
                         ensure_ascii=False))
        return 0

    try:
        build(stage)
        result = refresh_palette(data, config, state, home, selected, 'domainos-pixbuf', dry=True)
        print('Prévia de atualização GTK2:', result.get('status'))
        with bundle.locked():
            bundle.install([(stage, destination)], dry=args.verificar)
            if args.verificar:
                return 0
            try:
                applied = refresh_palette(data, config, state, home, selected,
                                          'domainos-pixbuf', dry=False)
            except BaseException:
                latest = bundle.latest()
                if latest and latest[1].get('status') == 'installed':
                    bundle.restore()
                raise
        reload_result = reload_clients()
        print(json.dumps({'theme': selected, 'palette': applied,
                          'engine': str(destination), 'reload': reload_result},
                         ensure_ascii=False))
        return 0
    finally:
        stage.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, Failure, RuntimeError) as error:
        print('ERRO: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
