#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 1: isolated IRIX-style scrollbar artwork on an integer 18-pixel grid.

Reference: user-supplied Confidence Tests screenshot, 1024x768. No raster
screenshot is embedded in the theme. Interaction states not present in that
reference are declared adaptations (see ../docs/ROLAGEM.md).
Kvantum 1.1.4 transposes vertical artwork to paint horizontal scrollbars.
"""
from __future__ import annotations

WIDTH = 18
GRIP_HEIGHT = 10
GRIP_PITCH = 4
FACE = '#999999'
LIGHT = '#e1e1e1'
MID_LIGHT = '#cccccc'
SHADE = '#737373'
DARK = '#4c4c4c'
INK = '#000000'
DISABLED = '#858585'
# The one-pixel tip and the doubled rows come from the supplied raster.
UP_GLYPH = (
    '00010000',
    '00011000',
    '00011000',
    '00111100',
    '00111100',
    '01111110',
    '01111110',
    '11111111',
    '11111111',
)


def blank(w: int, h: int, color=None):
    return [[color for _ in range(w)] for _ in range(h)]


def rect(image, x: int, y: int, w: int, h: int, color):
    for j in range(max(0, y), min(len(image), y + h)):
        for i in range(max(0, x), min(len(image[0]), x + w)):
            image[j][i] = color


def transpose(image):
    return [list(row) for row in zip(*image)]


def arrow(state: str, direction: str):
    """A square 18x18 cell with an 8x9 up/down glyph, without a label shift."""
    if direction not in ('up', 'down', 'left', 'right'):
        raise ValueError('Unknown direction: ' + direction)
    img = blank(WIDTH, WIDTH, FACE)
    top, bottom = [LIGHT, MID_LIGHT], [DARK, SHADE]
    if state in ('pressed', 'toggled'):
        top, bottom = bottom, top
    if state == 'disabled':
        top, bottom = [MID_LIGHT, '#b3b3b3'], [DISABLED, '#8c8c8c']
    for k in range(2):
        rect(img, k, k, WIDTH - 2*k, 1, top[k])
        rect(img, k, k, 1, WIDTH - 2*k, top[k])
        rect(img, k+1, WIDTH-k-1, WIDTH-2*k-1, 1, bottom[k])
        rect(img, WIDTH-k-1, k+1, 1, WIDTH-2*k-1, bottom[k])
    down = direction in ('down', 'right')
    points = [(5+x, 4+y) for y, row in enumerate(UP_GLYPH)
              for x, bit in enumerate(row) if bit == '1']
    if down:
        points = [(WIDTH-1-x, WIDTH-1-y) for x, y in points]
    if state in ('pressed', 'toggled'):
        # The rc2 only inverted the cell. Keep the triangle's dark mask fixed,
        # but add the missing light lower/right lip of its recessed impression.
        # This is a declared pressed-state adaptation, not a translated glyph.
        occupied = set(points)
        for x, y in points:
            nx, ny = x+1, y+1
            if (nx, ny) not in occupied:
                img[ny][nx] = LIGHT
    if state == 'disabled':
        # Embossed unavailable glyph; no black, no disappearing arrow cell.
        for x, y in points:
            img[y+1][x+1] = MID_LIGHT
    for x, y in points:
        img[y][x] = DISABLED if state == 'disabled' else DARK
    if direction in ('left', 'right'):
        img = transpose(img)
    return img


def groove(state: str, w: int = 24, h: int = 24):
    """Single-pixel trough edge; copied color roles, not a new global palette."""
    img = blank(w, h, FACE)
    rect(img, 0, 0, w, 1, INK)
    rect(img, 0, 1, 1, h-1, MID_LIGHT)
    rect(img, w-1, 1, 1, h-2, SHADE)
    rect(img, 1, h-2, w-1, 1, SHADE)
    rect(img, 0, h-1, w, 1, DARK)
    return img


def thumb(state: str, height: int = 32):
    """18px full-width interior, top 2px and bottom 3px.

The side strips belong to the interior, not left/right FrameSvg pieces, so
Kvantum's grip indicator spans the *entire* knob, including those strips.
At width 18 this is a 1:1 map. Nonstandard forced widths may be resampled.
"""
    if height < 6:
        raise ValueError('Thumb must have room for both end caps.')
    img = blank(WIDTH, height, FACE)
    left = [LIGHT, MID_LIGHT]
    right = [SHADE, SHADE]
    if state in ('pressed', 'toggled'):
        left, right = [DARK, SHADE], [MID_LIGHT, LIGHT]
    if state == 'disabled':
        left, right = [MID_LIGHT, '#b3b3b3'], [DISABLED, DISABLED]
    rect(img, 0, 0, 1, height, left[0])
    rect(img, 1, 1, 1, height-2, left[1])
    rect(img, WIDTH-2, 1, 1, height-2, right[0])
    rect(img, WIDTH-1, 1, 1, height-2, right[1])
    rect(img, 0, 0, WIDTH, 1, left[0])
    rect(img, 1, 1, WIDTH-2, 1, left[1])
    rect(img, 2, height-3, WIDTH-2, 1, right[0])
    rect(img, 1, height-2, WIDTH-1, 1, right[1])
    rect(img, 0, height-1, WIDTH, 1,
         DISABLED if state == 'disabled' else LIGHT if state in ('pressed','toggled') else INK)
    return img


def grip(state: str):
    """Three light/black pairs at y=0,4,8; transparent two-row intervals."""
    img = blank(WIDTH, GRIP_HEIGHT)
    light, dark = (MID_LIGHT, DISABLED) if state == 'disabled' else (LIGHT, INK)
    for y in (0, GRIP_PITCH, 2*GRIP_PITCH):
        rect(img, 0, y, WIDTH, 1, light)
        rect(img, 0, y+1, 1, 1, light)
        rect(img, 1, y+1, WIDTH-1, 1, dark)
    return img


def add_frames(atlas, prefix: str, img, left: int, top: int, right: int, bottom: int):
    """Asymmetric 9-slice elements, including harmless zero-width placeholders."""
    h, w = len(img), len(img[0])
    boxes = {'':(left, top, w-right, h-bottom),
             'top':(left,0,w-right,top), 'bottom':(left,h-bottom,w-right,h),
             'left':(0,top,left,h-bottom), 'right':(w-right,top,w,h-bottom),
             'topleft':(0,0,left,top), 'topright':(w-right,0,w,top),
             'bottomleft':(0,h-bottom,left,h), 'bottomright':(w-right,h-bottom,w,h)}
    for part, (x0,y0,x1,y1) in boxes.items():
        pixels = ([row[x0:x1] for row in img[y0:y1]]
                  if x1>x0 and y1>y0 else blank(1,1))
        atlas.add(prefix+('-'+part if part else ''), pixels)


def append_scrollbar_assets(atlas, states):
    for state in states:
        add_frames(atlas, 'ic-scroll-groove-'+state, groove(state), 1,1,1,2)
        add_frames(atlas, 'ic-scroll-thumb-'+state, thumb(state), 0,2,0,3)
        atlas.add('ic-scroll-grip-'+state, grip(state))
