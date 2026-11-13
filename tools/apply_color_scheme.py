#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply installed KDE colors even when the selected scheme kept its name."""
from __future__ import annotations
import configparser
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

from theme_transaction import Failure, atomic, no_links, sha, snapshot


def ini(path):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    if path.is_file():
        parser.read_string(path.read_text())
    return parser


def selected(config):
    for path in (config/'kdeglobals', config/'kdedefaults/kdeglobals'):
        value = ini(path).get('General', 'ColorScheme', fallback=None)
        if value:
            return value
    return None


def source_file(data, scheme):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', scheme):
        raise Failure('Identificador de esquema inválido.')
    for root in (data, *(Path(p) for p in os.environ.get(
            'XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if p)):
        path = root/'color-schemes'/(scheme+'.colors')
        no_links(path)
        if path.is_file():
            if path.stat().st_size > 1024 * 1024:
                raise Failure('Arquivo de esquema inesperadamente grande.')
            return path
    raise Failure('Esquema instalado ausente: '+scheme)


def apply(data, config, state, scheme):
    """Native KDE application; the alias has identical roles and no fixed RGB.

    KDE intentionally skips an already selected identifier. A private temporary
    alias makes that update explicit. Keep it if a failed native operation left
    it selected, so the session still references a valid installed scheme.
    The caller's selection transaction remains responsible for rollback.
    """
    source = source_file(data, scheme)
    content = source.read_bytes()
    expected = ini(source)
    if not expected.has_section('Colors:Window'):
        raise Failure('Esquema não contém os papéis de janela KDE.')
    token = uuid.uuid4().hex
    alias_name = 'IrixPaletteReload-'+token
    alias = data/'color-schemes'/(alias_name+'.colors')
    receipt = state/'irixium-color-apply'/token/'receipt.json'
    record = {'status': 'prepared', 'scheme': scheme, 'source_sha256': sha(content),
              'previous_scheme': selected(config), 'before': snapshot(config/'kdeglobals')}
    atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
    try:
        if selected(config) == scheme:
            if alias.exists():
                raise Failure('Alias de paleta já existe; aplicação recusada.')
            atomic(alias, content)
            subprocess.run(['plasma-apply-colorscheme', alias_name], check=True,
                           capture_output=True, text=True, timeout=20)
            if selected(config) != alias_name:
                raise Failure('O KDE não confirmou o alias de atualização da paleta.')
        subprocess.run(['plasma-apply-colorscheme', scheme], check=True,
                       capture_output=True, text=True, timeout=20)
        if selected(config) != scheme:
            raise Failure('O KDE não confirmou o esquema solicitado.')
        current = ini(config/'kdeglobals')
        # Check actual RGB roles, not just the name. Selection/accent colors can
        # legitimately be overridden by KDE's independent accent preference.
        checks = [(group, key) for group in ('Colors:Window', 'Colors:Button', 'Colors:View')
                  for key in ('BackgroundNormal', 'ForegroundNormal')]
        checks += [('WM', key) for key in ('activeBackground', 'inactiveBackground',
                                          'activeForeground', 'inactiveForeground')]
        differences = [group+'/'+key for group, key in checks
                       if expected.has_option(group, key) and
                       expected.get(group, key) != current.get(group, key, fallback=None)]
        if differences:
            raise Failure('Papéis KDE não acompanharam o esquema: '+', '.join(differences))
        if sha(source.read_bytes()) != record['source_sha256']:
            raise Failure('O arquivo de cores mudou durante a aplicação.')
        record.update(status='applied', after=snapshot(config/'kdeglobals'),
                      verified_roles=[g+'/'+k for g, k in checks if expected.has_option(g, k)])
        return {'status': 'applied', 'scheme': scheme, 'receipt': str(receipt),
                'verified_roles': record['verified_roles']}
    except BaseException as error:
        record.update(status='failed', error=str(error), current_scheme=selected(config))
        raise
    finally:
        if alias.is_file() and selected(config) != alias_name:
            # Refuse to remove an unexpected concurrent edit to our alias.
            if alias.read_bytes() == content:
                alias.unlink()
        elif alias.is_file():
            record['retained_alias'] = str(alias)
        atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
