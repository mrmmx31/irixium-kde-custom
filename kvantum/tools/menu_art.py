# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 5: menu-only original artwork. No Qt input/event overrides.

The resting menubar profile is sampled from the supplied Confidence Tests
capture. Popup/armed/pressed states and arrow grids are explicit adaptations
of the SGI/Motif visual language, not certified historical pixel copies.
QMenu's selected item maps to 'toggled', NOT a checked QAction. Keep the
checkbox/radio resources from block 4 for persistent selection.
"""
STATES = ('normal', 'focused', 'pressed', 'toggled', 'disabled')
PREFIXES = ('ic-menupanel-', 'ic-menustrip-', 'ic-menurow-',
            'ic-menutitle-', 'ic-menuindicator-')
FACE = '#c1c1c1'
LOCATE = '#dfdfdf'
PRESSED = '#b3b3b3'
LIGHT = '#ececec'
DARK = '#606060'
MID = '#919191'


def blank(w, h, color=None):
    if w <= 0 or h <= 0:
        raise ValueError('Positive dimensions required.')
    return [[color for _ in range(w)] for _ in range(h)]


def rect(im, x, y, w, h, color):
    for j in range(max(0, y), min(len(im), y+h)):
        for i in range(max(0, x), min(len(im[0]), x+w)):
            im[j][i] = color


def bevel(im, down=False):
    h, w = len(im), len(im[0])
    # 2px rim. Below/right use gray on the inside and dark on the outside.
    upper, lower = (LIGHT, LIGHT), (DARK, MID)
    if down:
        upper, lower = lower, upper
    for k in range(2):
        rect(im, k, k, w-2*k, 1, upper[k])
        rect(im, k, k, 1, h-2*k, upper[k])
        rect(im, k+1, h-k-1, w-2*k-1, 1, lower[k])
        rect(im, w-k-1, k+1, 1, h-2*k-1, lower[k])
    return im


def surface(kind, state='normal', w=24, h=24):
    if kind not in ('menupanel', 'menustrip', 'menurow', 'menutitle'):
        raise ValueError('Unknown menu surface.')
    if state not in STATES or min(w, h) < 5:
        raise ValueError('Unknown state or dimensions too small.')
    if kind in ('menupanel', 'menustrip'):
        # The panel is opaque; the Qt Quick path uses the same QPalette Window.
        return bevel(blank(w, h, FACE))
    if state in ('normal', 'disabled'):
        # The engine skips a panel in these states; transparent maps also make
        # direct/alternate rendering harmless. Never highlight disabled items.
        return blank(w, h)
    # selected == toggled in CE_MenuItem, independently of check/radio state.
    return bevel(blank(w, h, PRESSED if state == 'pressed' else LOCATE),
                 down=state == 'pressed')


def direction_indicator(direction, state='normal', size=12):
    if direction not in ('up', 'down', 'left', 'right') or state not in STATES:
        raise ValueError('Unknown menu indicator.')
    if size != 12:
        raise ValueError('The reviewed indicator cell is 12x12.')
    im = blank(size, size)
    # Integer 5x9 right-pointing mask, centered inside the existing 12px cell.
    mask = ('10000','11000','11100','11110','11111',
            '11110','11100','11000','10000')
    points = {(4+x, 1+y) for y,row in enumerate(mask)
              for x,v in enumerate(row) if v == '1'}
    def rotate(p):
        x,y=p
        if direction=='left': return 11-x, y
        if direction=='down': return y, x
        if direction=='up': return y, 11-x
        return p
    points = {rotate(p) for p in points}
    ink = '#858585' if state == 'disabled' else DARK
    # A tiny bevel makes this an option/submenu mark, not a scrollbar button.
    for x,y in points:
        if (x+1,y+1) not in points and x+1<size and y+1<size:
            im[y+1][x+1] = LIGHT
    for x,y in points:
        im[y][x] = ink
    return im


def separator():
    # CE_MenuItem stretches this to menu_separator_height=6. The two lines
    # are centered vertically and span the popup's interior, not its frame.
    im = blank(20, 6)
    rect(im, 0, 2, 20, 1, MID)
    rect(im, 0, 3, 20, 1, LIGHT)
    return im


def tearoff(state='normal'):
    if state not in ('normal', 'focused'):
        raise ValueError('Only states requested by CE_MenuTearoff are supplied.')
    im = blank(20, 8, LOCATE if state=='focused' else FACE)
    for x in range(0,20,5):
        rect(im,x,3,3,1,DARK)
        rect(im,x,4,3,1,LIGHT)
    return im


def append_menu_assets(atlas):
    for kind in ('menupanel','menustrip','menurow','menutitle'):
        for state in STATES:
            im=surface(kind,state)
            for tail in ('','-inactive'):
                atlas.frames('ic-'+kind+'-'+state+tail, im, 2)
    for state in STATES:
        for direction in ('up','down','left','right'):
            im=direction_indicator(direction,state)
            atlas.add('ic-menuindicator-'+direction+'-'+state,im)
            atlas.add('ic-menuindicator-'+direction+'-'+state+'-inactive',im)
    atlas.add('ic-menuindicator-separator',separator())
    atlas.add('ic-menuindicator-separator-inactive',separator())
    for state in ('normal','focused'):
        atlas.add('ic-menuindicator-tearoff-'+state,tearoff(state))
