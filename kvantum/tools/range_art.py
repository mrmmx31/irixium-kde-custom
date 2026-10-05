#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 7 artwork. Integer maps, not SGI code or a historical certification.

Grooves and handles are vertical master images: Kvantum rotates/transposes them.
Default-engine IDs (dial and header-separator) are intentional. See CONTROLES.md
for Qt-owned actions and controls for which a theme cannot supply new behavior.
"""
from __future__ import annotations
import math

STATES = ('normal', 'focused', 'pressed', 'toggled', 'disabled')
FACE = '#c1c1c1'
THUMB = '#999999'
LIGHT = '#e1e1e1'
EDGE = '#4c4c4c'
INK = '#000000'
FILL = '#719e9e'
SELECTED = '#9ebfbf'
UNFOCUSED_SELECTION = '#b3c3c3'
PREFIXES = ('ic-range-', 'ic-meter-', 'ic-divider-', 'ic-column-',
            'ic-branch-', 'ic-row-', 'ic-hint-', 'ic-section-',
            'ic-resize-', 'ic-dock-', 'ic-mdi-', 'dial', 'header-separator')


def blank(w: int, h: int, color=None):
    if not isinstance(w, int) or not isinstance(h, int) or w < 1 or h < 1:
        raise ValueError('Positive integer map dimensions required.')
    return [[color for _ in range(w)] for _ in range(h)]


def rect(im, x, y, w, h, color):
    for j in range(max(0, y), min(len(im), y+h)):
        for i in range(max(0, x), min(len(im[0]), x+w)):
            im[j][i] = color


def state_check(state):
    if state not in STATES:
        raise ValueError('Unknown state: '+str(state))


def rim(im, n=2, down=False, enabled=True):
    h, w = len(im), len(im[0])
    if min(w, h) < 2*n+1 or not 1 <= n <= 3:
        raise ValueError('Map too small for bevel.')
    top, bottom = [LIGHT, '#cccccc', FACE], [EDGE, '#737373', '#919191']
    if down:
        top, bottom = bottom, top
    if not enabled:
        top, bottom = ['#b1b1b1', '#bcbcbc', FACE], ['#8c8c8c', '#aaaaaa', '#b3b3b3']
    for k in range(n):
        rect(im, k, k, w-2*k, 1, top[k]); rect(im, k, k, 1, h-2*k, top[k])
        rect(im, k+1, h-k-1, w-2*k-1, 1, bottom[k])
        rect(im, w-k-1, k+1, 1, h-2*k-1, bottom[k])
    return im


def surface(kind: str, state: str='normal', w: int=24, h: int=24):
    state_check(state)
    if kind not in ('range-track','range-thumb','meter-track','meter-fill',
                    'column','hint','section','dock'):
        raise ValueError('Unknown surface: '+kind)
    n = 3 if kind in ('section','column') else 2
    fill = FACE
    if kind in ('range-track','meter-track'): fill = THUMB
    elif kind == 'range-thumb': fill = '#aaaaaa' if state=='focused' else THUMB
    elif kind == 'meter-fill': fill = '#8eaaaa' if state=='disabled' else FILL
    elif kind == 'column': fill = '#d7d7d7' if state=='focused' else '#b1b1b1' if state=='pressed' else FACE
    elif kind == 'section': fill = None
    down = kind in ('range-track','meter-track') or (kind in ('range-thumb','column') and state=='pressed')
    if kind=='range-track' and state=='toggled': fill=FILL
    im = rim(blank(w,h,fill), n, down, state!='disabled')
    if kind=='section':
        # Etched, unfilled grouping outline: no paint over the page or its title.
        im = blank(w,h)
        for k, col in ((1,'#919191'), (2,LIGHT)):
            rect(im,k,k,w-2*k,1,col);rect(im,k,k,1,h-2*k,col)
            rect(im,k,h-k-1,w-2*k,1,col);rect(im,w-k-1,k,1,h-2*k,col)
    return im,n


def grip(state='normal', w=10, h=10):
    state_check(state)
    if w<5 or h<7: raise ValueError('Grip too small.')
    im=blank(w,h)
    dark='#858585' if state=='disabled' else EDGE
    light='#cccccc' if state=='disabled' else LIGHT
    if state=='pressed':dark,light=light,dark
    for j in (1,4,7):
        if j+1<h:
            rect(im,1,j,w-2,1,light);rect(im,1,j+1,w-2,1,dark)
    return im


def divider(state='normal',w=7,h=24):
    state_check(state)
    im=blank(w,h,'#d1d1d1' if state=='focused' else FACE)
    return rim(im,1,state=='pressed',state!='disabled')


def row(state='normal',w=12,h=12):
    state_check(state)
    # Normal backgrounds belong to the viewport/app, not the style's row painter.
    color = {'normal':None,'focused':'#d7e0dc','pressed':SELECTED,
             'toggled':UNFOCUSED_SELECTION,'disabled':None}[state]
    return blank(w,h,color)


def triangle(direction='right',state='normal',size=9):
    state_check(state)
    if direction not in ('right','down','left','up') or size not in (9,12):
        raise ValueError('Unsupported triangle.')
    im=blank(size,size);off=(size-9)//2
    col='#858585' if state=='disabled' else INK
    # Hollow, right-pointing triangle. Its down-state is the transposed outline.
    pts={(1,y) for y in range(9)}
    pts.update((1+min(y,8-y),y) for y in range(9))
    for x,y in pts:
        if direction=='down':x,y=y,x
        elif direction=='left':x=8-x
        elif direction=='up':x,y=y,8-x
        im[y+off][x+off]=col
    return im


def resize_grip(state='normal',size=15):
    state_check(state)
    im=blank(size,size)
    for start in (4,8,12):
        for x in range(start,size-1):
            y=size-1+start-x
            if 0<=y<size:im[y][x]='#858585' if state=='disabled' else EDGE
            if 0<=y-1<size:im[y-1][x]='#cccccc' if state=='disabled' else LIGHT
    return im


def dial(part='body',size=32):
    if part not in ('body','handle','focus','notches'):raise ValueError(part)
    if size<8 or size>40:raise ValueError(size)
    im=blank(size,size);c=(size-1)/2;r=c-1
    if part=='handle':
        return rim(blank(8,8,THUMB),2,True)
    for y in range(size):
        for x in range(size):
            distance=math.hypot(x-c,y-c)
            if part=='body' and distance<=r:
                im[y][x]=FACE
                if distance>=r-2:im[y][x]=LIGHT if x+y<size-1 else EDGE
            elif part=='focus' and r-3<=distance<r-2 and (x+y)%2==0:
                im[y][x]=INK
    if part=='notches':
        # Decoration only. Qt determines the pointer angle/range. Not a tick scale.
        for degrees in range(30,331,30):
            a=math.radians(degrees)
            for rad in (r-4,r-5):
                x=round(c+rad*math.sin(a));y=round(c-rad*math.cos(a));im[y][x]=EDGE
    return im


def mdi_symbol(kind,state='normal',size=12):
    state_check(state)
    if kind not in ('close','maximize','minimize','restore','shade'):raise ValueError(kind)
    im=blank(size,size)
    col='#858585' if state=='disabled' else INK
    pts=set()
    if kind=='close':
        pts={(i,i) for i in range(3,9)}|{(11-i,i) for i in range(3,9)}
    elif kind=='minimize':pts={(x,y) for x in (5,6) for y in (5,6)}
    elif kind in ('maximize','restore'):
        pts={(x,y) for x in range(2,10) for y in range(2,10) if x in (2,9) or y in (2,9)}
        if kind=='restore':pts|={(x,y) for x in range(4,8) for y in range(4,8) if x in (4,7) or y in (4,7)}
    else:pts={(x,3) for x in range(2,10)}
    if state=='pressed':
        for x,y in pts:im[y+1][x+1]=LIGHT
    for x,y in pts:im[y][x]=col
    return im


def append_assets(atlas):
    for kind,prefix in (('range-track','ic-range-track'),('range-thumb','ic-range-thumb'),
                        ('meter-track','ic-meter-track'),('meter-fill','ic-meter-fill'),
                        ('column','ic-column-panel'),('hint','ic-hint-panel'),
                        ('section','ic-section-frame'),('dock','ic-dock-strip')):
        for state in STATES:
            im,n=surface(kind,state)
            for inactive in ('','-inactive'):
                atlas.frames(prefix+'-'+state+inactive,im,n)
    for state in STATES:
        for inactive in ('','-inactive'):
            tag=state+inactive
            atlas.frames('ic-divider-panel-'+tag,divider(state),1)
            atlas.add('ic-divider-grip-'+tag,grip(state,5,10))
            atlas.add('ic-range-mark-'+tag,grip(state))
            atlas.add('ic-row-panel-'+tag,row(state))
            atlas.add('ic-resize-mark-'+tag,resize_grip(state))
            for sign,direction in (('plus','right'),('minus','down')):
                atlas.add('ic-branch-mark-'+sign+'-'+tag,triangle(direction,state))
            for direction in ('up','down','left','right'):
                atlas.add('ic-column-mark-'+direction+'-'+tag,triangle(direction,state,12))
            for kind in ('close','maximize','minimize','restore','shade'):
                atlas.add('ic-mdi-mark-'+kind+'-'+tag,mdi_symbol(kind,state))
    for inactive in ('','-inactive'):
        # CC_Slider requests its tick from the groove's interior prefix.
        atlas.add('ic-range-track-tick-normal'+inactive,blank(5,1,EDGE))
        for name,part in (('dial','body'),('dial-handle','handle'),('dial-notches','notches')):
            atlas.add(name+inactive,dial(part))
        for state,face in (('normal','#999999'),('focused','#a39f83')):
            atlas.add('ic-mdi-title-'+state+inactive,blank(12,12,face))
    atlas.add('dial-focus',dial('focus'))
    # Header separator has an engine-defined, global name; it isn't an arrow.
    sep=blank(3,12,FACE);rect(sep,0,0,1,12,EDGE);rect(sep,1,0,1,12,LIGHT)
    atlas.add('header-separator',sep)

# Reviewed effective configuration changes; regression tests use the full contract.
CONFIG_PATCH = {'Slider': {'frame.element': 'ic-range-track', 'interior.element': 'ic-range-track'}, 'SliderCursor': {'frame.element': 'ic-range-thumb', 'interior.element': 'ic-range-thumb', 'indicator.element': 'ic-range-mark'}, 'Progressbar': {'frame.element': 'ic-meter-track', 'interior.element': 'ic-meter-track'}, 'ProgressbarContents': {'frame.element': 'ic-meter-fill', 'interior.element': 'ic-meter-fill'}, 'Splitter': {'frame.element': 'ic-divider-panel', 'interior.element': 'ic-divider-panel', 'indicator.element': 'ic-divider-grip', 'frame.top': '1', 'frame.bottom': '1', 'frame.left': '1', 'frame.right': '1'}, 'HeaderSection': {'frame.element': 'ic-column-panel', 'interior.element': 'ic-column-panel', 'indicator.element': 'ic-column-mark'}, 'TreeExpander': {'indicator.element': 'ic-branch-mark'}, 'ItemView': {'interior.element': 'ic-row-panel'}, 'ToolTip': {'frame.element': 'ic-hint-panel', 'interior.element': 'ic-hint-panel'}, 'GroupBox': {'frame.element': 'ic-section-frame'}, 'SizeGrip': {'indicator.element': 'ic-resize-mark'}, 'DockTitle': {'frame.element': 'ic-dock-strip', 'interior.element': 'ic-dock-strip'}, 'TitleBar': {'interior.element': 'ic-mdi-title', 'indicator.element': 'ic-mdi-mark', 'indicator.size': '12'}, '%General': {'spread_progressbar': 'false'}}
CONFIG_SECTIONS = tuple(k for k in CONFIG_PATCH if k != "%General")
