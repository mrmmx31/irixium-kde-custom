# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Local finishing assets; earlier maps/atlas positions remain untouched.

The toolbar resource is vertical in the canonical (horizontal-toolbar) draw;
Kvantum transposes the coordinate axes for vertical toolbars. Transparent padding is intentional.
Spin triangles gain legibility without enlarging their 12x12 allocation.
These are measured adaptations, not newly authenticated SGI pixel art.
"""
from __future__ import annotations

PREFIXES = ('ic-finish-toolbar-', 'ic-finish-spinmark-')
CONFIG_PATCH = {
    'Toolbar': {'indicator.element': 'ic-finish-toolbar'},
    'IndicatorSpinBox': {'indicator.element': 'ic-finish-spinmark'},
}
PRIOR = {'Toolbar': {'indicator.element': 'ic-toolbar'},
         'IndicatorSpinBox': {'indicator.element': 'ic-spinmark'}}
STATES = ('normal', 'focused', 'pressed', 'toggled', 'disabled')


def prior_effective(section, values):
    """Project only reviewed routes for older regression suites, never bad values.

The finishing suite independently verifies every current effective property
against the 0.7 baseline and the two explicit CONFIG_PATCH entries.
"""
    out = dict(values)
    for key, current in CONFIG_PATCH.get(section, {}).items():
        if out.get(key) == current:
            out[key] = PRIOR[section][key]
    return out


def toolbar_separator():
    # PM_ToolBarSeparatorExtent is 10 in this theme. Two painted columns, four
    # transparent columns on either side. Do not reuse the menu's horizontal map.
    out = [[None] * 10 for _ in range(12)]
    for y in range(1, 11):
        out[y][4], out[y][5] = '#919191', '#ececec'
    return out


def spin_marker(state, direction, size=12):
    if state not in STATES or direction not in ('up', 'down', 'left', 'right') or size != 12:
        raise ValueError('Unsupported finishing spin marker.')
    rows = ('0001000', '0011100', '0011100', '0111110', '0111110', '1111111')
    coords = {(2+x, 3+y) for y, row in enumerate(rows) for x, bit in enumerate(row) if bit == '1'}
    if direction == 'down': coords = {(11-x, 11-y) for x, y in coords}
    elif direction == 'left': coords = {(y, x) for x, y in coords}
    elif direction == 'right': coords = {(11-y, x) for x, y in coords}
    out = [[None] * size for _ in range(size)]
    if state in ('pressed', 'toggled', 'disabled'):
        light = '#cccccc' if state == 'disabled' else '#ececec'
        for x, y in coords:
            if x+1 < size and y+1 < size: out[y+1][x+1] = light
    dark = '#858585' if state == 'disabled' else '#4c4c4c'
    for x, y in coords: out[y][x] = dark
    return out


def append_assets(atlas):
    # Preserve the existing toolbar handle; only the separator is redesigned.
    for suffix in ('', '-inactive'):
        atlas.add('ic-finish-toolbar-handle'+suffix, atlas.items['ic-toolbar-handle'])
        atlas.add('ic-finish-toolbar-separator'+suffix, toolbar_separator())
    for state in STATES:
        for direction in ('up', 'down', 'left', 'right'):
            for suffix in ('', '-inactive'):
                atlas.add('ic-finish-spinmark-'+direction+'-'+state+suffix, spin_marker(state, direction))
