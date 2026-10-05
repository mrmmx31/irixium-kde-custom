# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 4: red check marks and blue triangular radio marks.

SGI's UI Guidelines establish the shapes/colors, not these exact coordinates.
This is original 15x15 artwork, fitted to the already installed check_size.
Kvantum 1.1.4 selects normal/focused/checked/tristate, not a pressed SVG for
these indicators. Disabled controls use the engine's normal artwork at 0.7
opacity. Do not fabricate a separate pressed/disabled rendering promise.
"""
SIZE = 15
RED = '#cc0000'
BLUE = '#0000cc'
PREFIXES = ('ic-checkmark-', 'menu-ic-checkmark-', 'item-ic-checkmark-',
            'ic-radiomark-', 'menu-ic-radiomark-')
TICK = ('000000011', '000000110', '000001100', '110011000',
        '111110000', '011100000', '001000000')
TRIANGLE = ('10000', '11000', '11110', '11111', '11110', '11000', '10000')


def blank():
    return [[None for _ in range(SIZE)] for _ in range(SIZE)]


def mark(image, mask, x0, y0, face, shadow):
    pts = {(x0+x, y0+y) for y, row in enumerate(mask)
           for x, bit in enumerate(row) if bit == '1'}
    for x, y in pts:
        if (x+1, y+1) not in pts and x+1 < SIZE and y+1 < SIZE:
            image[y+1][x+1] = shadow
    for x, y in pts:
        image[y][x] = face


def indicator(kind: str, value: str = 'off', hover: bool = False):
    if kind not in ('check', 'radio') or value not in ('off', 'on', 'mixed'):
        raise ValueError('Unknown indicator kind/value.')
    if kind == 'radio' and value == 'mixed':
        raise ValueError('Radio buttons have no mixed state.')
    image = blank()
    face = '#dfdfdf' if hover else '#c1c1c1'
    if value != 'off':
        face = '#b3b3b3' if hover else '#999999'
    # A square/diamond makes the shape identifiable without color alone.
    if kind == 'check':
        for y in range(1, 14):
            for x in range(1, 14):
                image[y][x] = face
        upper = ('#606060', '#919191')
        lower = ('#e1e1e1', '#cccccc')
        for k in (0, 1):
            lo, hi = 1+k, 13-k
            for x in range(lo, hi+1):
                image[lo][x] = upper[k]
                image[hi][x] = lower[k]
            for y in range(lo+1, hi):
                image[y][lo] = upper[k]
                image[y][hi] = lower[k]
        if value == 'on':
            mark(image, TICK, 3, 3, RED, '#660000')
        elif value == 'mixed':
            # Qt's tri-state extension, not asserted as an IRIX screenshot match.
            mark(image, ('1111111', '1111111'), 4, 6, RED, '#660000')
    else:
        c = SIZE // 2
        for y in range(1, 14):
            for x in range(1, 14):
                d = abs(x-c) + abs(y-c)
                if d > 6:
                    continue
                if d == 6:
                    image[y][x] = '#737373' if x+y <= 2*c else '#e1e1e1'
                elif d == 5:
                    image[y][x] = '#919191' if x+y <= 2*c else '#cccccc'
                else:
                    image[y][x] = face
        if value == 'on':
            mark(image, TRIANGLE, 5, 4, BLUE, '#000066')
    return image


def append_selection_assets(atlas):
    for kind, stem, contexts in (
        ('check', 'ic-checkmark', ('', 'menu-', 'item-')),
        ('radio', 'ic-radiomark', ('', 'menu-')),
    ):
        values = ('off', 'on', 'mixed') if kind == 'check' else ('off', 'on')
        for value in values:
            checked = '' if value == 'off' else 'checked-' if value == 'on' else 'tristate-'
            for state, hover in (('normal', False), ('focused', True)):
                image = indicator(kind, value, hover)
                for context in contexts:
                    name = context + stem + '-' + checked + state
                    atlas.add(name, image)
                    atlas.add(name + '-inactive', image)
