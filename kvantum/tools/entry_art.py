#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 3: new entry, option-button, spin and inset resources.

No new input behavior is implemented here. Qt owns text, focus, readonly,
selection, validation and step limits. The historical option-button marker
is a short horizontal relief, not a modern downward chevron. Its exact map
and interaction states are adaptations (see docs/CAMPOS.md).
"""
from __future__ import annotations

STATES = ('normal', 'focused', 'pressed', 'toggled', 'disabled')
FIELD = '#b6b6aa'  # neutral content scheme; not the path finder's rose scheme
FACE = '#999999'
LIGHT = '#ececec'
MID = '#c1c1c1'
DARK = '#606060'
INK = '#2f2f2f'


def blank(w, h, color=None):
    return [[color for _ in range(w)] for _ in range(h)]


def rect(img, x, y, w, h, color):
    for row in range(max(0,y), min(len(img), y+h)):
        for col in range(max(0,x), min(len(img[0]), x+w)):
            img[row][col] = color


def surface(kind, state, w=24, h=24):
    if kind not in ('input','inset','option','spin') or state not in STATES:
        raise ValueError('Invalid entry resource/state.')
    n = 2 if kind == 'spin' else 3
    if min(w,h) < 2*n+1:
        raise ValueError('Resource is smaller than its frame.')
    fill = FIELD if kind == 'input' else FACE if kind in ('spin','option') else None
    img = blank(w,h,fill)
    if kind in ('input','inset'):
        # Normal inset: progressively darker inside top/left, inverse below/right.
        top = ['#919191', DARK, INK]
        bottom = [LIGHT, MID, INK]
        if kind == 'input' and state == 'focused':
            # For LineEdit, focused means keyboard focus (not mouse-over).
            top[0] = bottom[0] = '#000000'
    elif kind == 'option':
        top = ['#4c4c4c','#e1e1e1','#cccccc']
        bottom = ['#252525','#4c4c4c','#737373']
        if state in ('pressed','toggled'):
            top[1:], bottom[1:] = bottom[1:], top[1:]
    else:
        top, bottom = ['#e1e1e1','#cccccc'], ['#4c4c4c','#737373']
        if state in ('pressed','toggled'):
            top, bottom = bottom, top
    if state == 'disabled':
        top = ['#a0a0a0','#919191','#858585'][:n]
        bottom = ['#dfdfdf','#cccccc','#858585'][:n]
    for k in range(n):
        rect(img,k,k,w-2*k,1,top[k]);rect(img,k,k,1,h-2*k,top[k])
        rect(img,k+1,h-k-1,w-2*k-1,1,bottom[k]);rect(img,w-k-1,k+1,1,h-2*k-1,bottom[k])
    return img,n


def option_marker(state, size=12):
    if state not in STATES: raise ValueError(state)
    img=blank(size,size)
    x,y,w,h=1,4,10,4
    top,bottom=('#ececec','#4c4c4c')
    if state in ('pressed','toggled'): top,bottom=bottom,top
    if state=='disabled': top,bottom='#cccccc','#858585'
    rect(img,x,y,w,h,FACE)
    rect(img,x,y,w,1,top);rect(img,x,y,1,h,top)
    rect(img,x+1,y+h-1,w-1,1,bottom);rect(img,x+w-1,y+1,1,h-1,bottom)
    return img


def spin_marker(state, direction, size=12):
    if state not in STATES or direction not in ('up','down','left','right'):
        raise ValueError('Invalid spin marker.')
    img=blank(size,size)
    dark='#858585' if state=='disabled' else '#4c4c4c'
    coords=[(5+x,3+y) for y,row in enumerate(('00100','01110','11111','11111'))
            for x,b in enumerate(row) if b=='1']
    # Center 5px glyph inside the 12px indicator.
    coords=[(x-2,y) for x,y in coords]
    if direction=='down': coords=[(size-1-x,size-1-y) for x,y in coords]
    if direction in ('left','right'):
        coords=[(y,x) for x,y in coords]
        if direction=='right': coords=[(size-1-x,y) for x,y in coords]
    if state in ('pressed','toggled','disabled'):
        light='#cccccc' if state=='disabled' else '#ececec'
        for x,y in coords:
            if x+1<size and y+1<size: img[y+1][x+1]=light
    for x,y in coords: img[y][x]=dark
    return img


def append_entry_assets(atlas):
    for kind in ('input','inset','option','spin'):
        for state in STATES:
            img,n=surface(kind,state)
            atlas.frames('ic-'+kind+'-'+state,img,n)
    for state in STATES:
        atlas.add('ic-optionmark-down-'+state,option_marker(state))
        atlas.add('ic-optionmark-'+state,option_marker(state))
        for direction in ('up','down','left','right'):
            atlas.add('ic-spinmark-'+direction+'-'+state,spin_marker(state,direction))
    # Explicit separator for the editable part / arrow part of a combo.
    for state in STATES:
        for part,h in (('',12),('-top',3),('-bottom',3)):
            img=blank(3,h)
            rect(img,0,0,1,h,'#606060');rect(img,1,0,1,h,'#ececec')
            atlas.add('ic-optionmark-separator'+part+'-'+state,img)
