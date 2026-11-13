#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Add the optional Manaus 2026 holiday region for the invoking user.

This configures KHolidays data/regions only. It does not activate a calendar
provider, modify the panel, contact a server or change another user's profile.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

from install_suite import roots
from theme_transaction import Change, Failure, Transaction, edit_ini, no_links, snapshot

ROOT = Path(__file__).resolve().parents[1]
REGION = 'br-am-manaus-2026_pt-br'
REGIONS = (REGION,)
SOURCE = ROOT / ('plasma/applets/org.irixclassic.domainos.panel/contents/code/'
                 'holidays/holiday_' + REGION)


def selected_regions(content: bytes) -> list[str]:
    """Read region codes; edit_ini subsequently guards duplicate/protected keys."""
    inside = False
    result = []
    for line in content.decode('utf-8').splitlines():
        value = line.strip()
        if value.startswith('['):
            inside = value == '[General]'
        elif inside and '=' in value and value.split('=', 1)[0].strip() == 'selectedRegions':
            codes = value.split('=', 1)[1].strip()
            result = codes.split(',') if codes else []
    if any(not re.fullmatch(r'[A-Za-z0-9_.-]+', code) for code in result):
        raise Failure('Lista de regiões inesperada; use a configuração nativa para revisá-la.')
    return list(dict.fromkeys(result))


def transaction(data: Path, config: Path, state: Path) -> Transaction:
    destinations = {
        data / ('kf5/libkholidays/plan2/holiday_' + REGION): 0,
        config / 'plasma_calendar_holiday_regions': 2,
    }

    def reject_system(entries):
        raise Failure('Este configurador não tem destinos de sistema.')

    return Transaction(state / 'irixium-domainos-holidays', reject_system,
        lambda path, phase: destinations.get(path) == phase)


def changes(data: Path, config: Path) -> list[Change]:
    no_links(SOURCE)
    if not SOURCE.is_file() or SOURCE.is_symlink():
        raise Failure('Fonte regional do pacote ausente ou irregular.')
    region_path = data / ('kf5/libkholidays/plan2/holiday_' + REGION)
    config_path = config / 'plasma_calendar_holiday_regions'
    prior = snapshot(config_path)
    content = config_path.read_bytes() if prior['exists'] else b''
    # The bundled Brazil definition in KHolidays 6.13 predates current holidays
    # and marks both Carnival days as public. The explicit Manaus 2026 choice
    # replaces that one region, keeping unrelated countries/regions untouched.
    retained = [code for code in selected_regions(content) if code != 'br_pt-br']
    regions = list(dict.fromkeys([*retained, *REGIONS]))
    updated = edit_ini(content, 'General', {'selectedRegions': ','.join(regions)})
    return [Change(region_path, SOURCE.read_bytes(), mode=0o644),
        Change(config_path, updated, phase=2,
            mode=prior['mode'] if prior['exists'] else 0o600, expected=prior)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--manaus-2026', action='store_true',
        help='Selecionar feriados nacionais/locais de Manaus/AM limitados a 2026')
    mode.add_argument('--restaurar', action='store_true',
        help='Restaurar arquivos e seleção anteriores desta configuração')
    parser.add_argument('--verificar', action='store_true', help='Conferir sem alterar os destinos')
    parser.add_argument('--recuperar', action='store_true', help='Concluir restauração interrompida')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Execute como seu usuário normal, sem sudo.')
    if args.recuperar and not args.restaurar:
        parser.error('--recuperar exige --restaurar')
    data, config, state = roots()
    manager = transaction(data, config, state)
    if args.verificar:
        if args.restaurar:
            manager.restore(recovery=args.recuperar, dry=True)
        else:
            manager.install(changes(data, config), dry=True)
        return 0
    with manager.locked():
        if args.restaurar:
            manager.restore(recovery=args.recuperar)
            return 0
        receipt = manager.install(changes(data, config))
    print(json.dumps({'scope': 'invoking-user-only', 'year': 2026,
        'regions_added': list(REGIONS), 'receipt': str(receipt) if receipt else None,
        'calendar_provider_activated': False}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Failure, OSError, ValueError) as error:
        sys.exit('ERRO: ' + str(error))
