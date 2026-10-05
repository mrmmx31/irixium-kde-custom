#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 2 artwork, isolated from the legacy assets used by blocks 3--7.

Raised command profile: supplied SGI Help Viewer pushbutton screenshot.
Pressed/default/toggle variants: explicit Qt/Motif-inspired adaptations.
No text, application icons, original screenshots or fonts are embedded.
"""
from __future__ import annotations

FACE = '#999999'
WINDOW = '#c1c1c1'
OUTLINE = '#4c4c4c'
LIGHT = '#e1e1e1'
MID_LIGHT = '#cccccc'
SHADE = '#737373'
DARK = '#252525'
STATES = ('normal', 'focused', 'pressed', 'toggled', 'disabled')


def blank(w, h, color=None):
    return [[color for _ in range(w)] for _ in range(h)]


def rect(img, x, y, w, h, color):
    for j in range(max(0, y), min(len(img), y+h)):
        for i in range(max(0, x), min(len(img[0]), x+w)):
            img[j][i] = color


def surface(kind, state, w=24, h=24):
    """Keep the dark outline stationary and invert only the inner bevel.

    `focused` means pointer hover, not keyboard focus. Keyboard focus uses
    Kvantum's separate Focus primitive. Auto-raised toolbar buttons keep a
    transparent resting face; raised palette buttons remain raised.
    """
    if kind not in ('command', 'palettebutton', 'toolbarbutton'):
        raise ValueError('Unknown button kind: '+kind)
    if state not in STATES:
        raise ValueError('Unknown button state: '+state)
    n = 3 if kind == 'command' else 2
    if min(w,h) < 2*n+1:
        raise ValueError('Button too small for the bevel')
    if kind == 'toolbarbutton' and state in ('normal', 'focused', 'disabled'):
        return blank(w,h), n
    down = state in ('pressed','toggled')
    img = blank(w, h, '#919191' if state == 'toggled' else FACE)
    if n == 3:
        # The three bands of the resting command button match the screenshot.
        top = [OUTLINE, LIGHT, MID_LIGHT]
        bottom = [DARK, OUTLINE, SHADE]
        if down:
            # Do not move or cover the outer contour. The highlight stays
            # inside it and remains visible with the default-button overlay.
            top = [OUTLINE, DARK, SHADE]
            bottom = [DARK, LIGHT, MID_LIGHT]
    else:
        top, bottom = [LIGHT, MID_LIGHT], [OUTLINE, SHADE]
        if down:
            top, bottom = [OUTLINE, SHADE], [LIGHT, MID_LIGHT]
    for k in range(n):
        rect(img,k,k,w-2*k,1,top[k]); rect(img,k,k,1,h-2*k,top[k])
        rect(img,k+1,h-k-1,w-2*k-1,1,bottom[k])
        rect(img,w-k-1,k+1,1,h-2*k-1,bottom[k])
    if state == 'disabled':
        # Some Kvantum paths use normal + 0.7 opacity; these assets also cover
        # requests for an explicit disabled state, without changing geometry.
        for row in img:
            for x, color in enumerate(row):
                row[x] = {DARK:'#858585', OUTLINE:'#858585'}.get(color,color)
    return img,n


def default_ring(w=24,h=24):
    """One outer dark ring; the inner two bands stay transparent.

    The old two-pixel black overlay hid part of the lower bevel. This marker
    is independent of hover, pressure and keyboard focus, with no resizing.
    """
    img=blank(w,h)
    rect(img,0,0,w,1,'#000000'); rect(img,0,h-1,w,1,'#000000')
    rect(img,0,0,1,h,'#000000'); rect(img,w-1,0,1,h,'#000000')
    return img


def append_assets(atlas):
    for kind in ('command','palettebutton','toolbarbutton'):
        for state in STATES:
            img,n=surface(kind,state)
            atlas.frames('ic-'+kind+'-'+state,img,n)
    atlas.frames('ic-command-default',default_ring(),3)
    # Split toolbutton separators requested without a state suffix by Kvantum.
    # The separator occupies the existing right frame, not extra hit-box space.
    for kind in ('palettebutton','toolbarbutton'):
        sep=blank(2,12)
        rect(sep,0,0,1,12,OUTLINE); rect(sep,1,0,1,12,LIGHT)
        atlas.add('ic-'+kind+'-separator',sep)
        atlas.add('ic-'+kind+'-separator-top',blank(2,2))
        atlas.add('ic-'+kind+'-separator-bottom',blank(2,2))
