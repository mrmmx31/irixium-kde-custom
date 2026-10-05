# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 6: original integer-grid artwork for Qt notebook/document tabs.

ViewKit documents overlapping tabs with the selected tab in front. Its collapsed
end-tabs/popup require application code and are NOT implemented by this SVG.
The 6px shoulder, palette and close/overflow indicators are declared adaptations;
no unverified claim of pixel identity with a ViewKit screenshot is made.
"""
from __future__ import annotations

PREFIXES = ('ic-notebook-', 'floating-ic-notebook-', 'ic-notebookpage-',
            'ic-notebookbase-', 'ic-tabmark-')
STATES = ('normal', 'focused', 'toggled')
FACE = '#c1c1c1'
IDLE = '#a7a7a7'
LOCATE = '#b8b8b8'
LIGHT = '#ececec'
MID_LIGHT = '#cccccc'
DARK = '#606060'
SHADOW = '#919191'
TAB_METRICS = (6, 2, 6, 2)  # left, top, right, bottom


def blank(w: int, h: int, color=None):
    if w <= 0 or h <= 0:
        raise ValueError('Positive dimensions required.')
    return [[color for _ in range(w)] for _ in range(h)]


def tab(state='normal', w=28, h=24, floating=False):
    """North-facing tab; Kvantum transforms the same slices for S/W/E.

    No fake pressed/disabled tab shape: Kvantum 1.1.4 selects normal, focused
    or toggled here. Disabled labels and activation remain native to Qt.
    """
    if state not in STATES or w < 16 or h < 8:
        raise ValueError('Invalid tab state or dimensions.')
    active = state == 'toggled'
    face = FACE if active else LOCATE if state == 'focused' else IDLE
    im = blank(w, h)
    for y in range(h):
        # Slope is confined to the side slices, never the text/interior slice.
        inset = max(0, 4 - (4*y)//max(1, h-3))
        for x in range(inset, w-inset):
            im[y][x] = face
        im[y][inset] = DARK
        im[y][w-inset-1] = DARK
        if w-2*inset > 3:
            im[y][inset+1] = LIGHT
            im[y][w-inset-2] = SHADOW
    # The two-pixel upper edge meets the bevel inside the shoulders.
    for x in range(5, w-5):
        im[0][x] = DARK
        im[1][x] = LIGHT
    # Active notebook tabs merge with their page; document tabs have their own
    # subtle baseline because many applications use a standalone QTabBar.
    for y in (h-2, h-1):
        for x in range(2, w-2):
            im[y][x] = FACE if active and not floating else (SHADOW if y==h-2 else DARK)
    return im


def page(w=28, h=24):
    """Opaque page background with a 3px raised surround (not app content)."""
    if min(w,h) < 7:
        raise ValueError('Page is too small.')
    im=blank(w,h,FACE)
    for k,(upper,lower) in enumerate(((DARK,DARK),(LIGHT,SHADOW),(MID_LIGHT,SHADOW))):
        for x in range(k,w-k):
            im[k][x]=upper
            im[h-k-1][x]=lower
        for y in range(k,h-k):
            im[y][k]=upper
            im[y][w-k-1]=lower
    return im


def slices(image, metrics):
    left,top,right,bottom=metrics
    h,w=len(image),len(image[0])
    if min(metrics)<0 or left+right>=w or top+bottom>=h:
        raise ValueError('Invalid slice metrics.')
    boxes={'':(left,top,w-right,h-bottom),
           'top':(left,0,w-right,top),'bottom':(left,h-bottom,w-right,h),
           'left':(0,top,left,h-bottom),'right':(w-right,top,w,h-bottom),
           'topleft':(0,0,left,top),'topright':(w-right,0,w,top),
           'bottomleft':(0,h-bottom,left,h),'bottomright':(w-right,h-bottom,w,h)}
    return {part:[row[x0:x1] for row in image[y0:y1]]
            for part,(x0,y0,x1,y1) in boxes.items() if x1>x0 and y1>y0}


def junctions():
    """Exact names requested by renderFrame; each side has its own lighting.

    Junctions join the tab side rim to a 3px page border, instead of stretching
    a 3x3 page corner over the 6px shoulder. Left/right follow Kvantum's rotated
    label convention (not the cardinal meaning of the final suffix).
    """
    result={}
    for side in ('top','bottom','left','right'):
        for label in ('left','right'):
            horizontal=side in ('top','bottom')
            im=blank(6 if horizontal else 3,3 if horizontal else 6,FACE)
            # For north: leftjunct is the tab's left rim. South is mirrored.
            first = (side=='top' and label=='left') or (side=='bottom' and label=='right')
            if horizontal:
                cols=(0,1) if label=='left' else (5,4)
                for y in range(3):
                    im[y][cols[0]]=DARK
                    im[y][cols[1]]=LIGHT if first else SHADOW
            else:
                # W: leftjunct is physically lower, rightjunct is upper.
                upper=(side=='left' and label=='right') or (side=='right' and label=='left')
                rows=(0,1) if upper else (5,4)
                for x in range(3):
                    im[rows[0]][x]=DARK
                    im[rows[1]][x]=LIGHT if upper else SHADOW
            result[side+'-'+label+'junct']=im
    return result


def close(state='normal'):
    if state not in ('normal','focused','pressed','toggled','toggledFocused','toggledPressed','disabled'):
        raise ValueError('Invalid close state.')
    im=blank(12,12)
    ink='#858585' if state=='disabled' else '#000000'
    pts={(i,i) for i in range(3,9)}|{(11-i,i) for i in range(3,9)}
    if state in ('pressed','toggledPressed'):
        for x,y in pts:
            if (x+1,y+1) not in pts:
                im[y+1][x+1]=LIGHT
    for x,y in pts: im[y][x]=ink
    return im


def tear():
    """Overflow-edge indicator only; not ViewKit's collapsed-tabs popup."""
    im=blank(8,20)
    for start in (0,3,6):
        for y in range(20):
            im[y][start]=DARK
            if start+1<8: im[y][start+1]=LIGHT
    return im


def append_tab_assets(atlas):
    for floating in (False,True):
        prefix=('floating-' if floating else '')+'ic-notebook-'
        for state in STATES:
            for inactive in ('','-inactive'):
                for part,im in slices(tab(state,floating=floating),TAB_METRICS).items():
                    atlas.add(prefix+state+inactive+('-'+part if part else ''),im)
    for suffix in ('normal','normal-inactive'):
        prefix='ic-notebookpage-'+suffix
        for part,im in slices(page(),(3,3,3,3)).items():
            atlas.add(prefix+('-'+part if part else ''),im)
        for part,im in junctions().items():atlas.add(prefix+'-'+part,im)
        # A standalone tab bar has no page frame. Its base is opaque and flat;
        # the document-tab resources themselves draw their small bottom rim.
        atlas.add('ic-notebookbase-'+suffix,blank(8,8,FACE))
    for state in ('normal','focused','pressed','toggled','toggledFocused','toggledPressed','disabled'):
        for inactive in ('','-inactive'):
            atlas.add('ic-tabmark-close-'+state+inactive,close(state))
    # PE_IndicatorTabTear* requests -tear for both edges; no popup is implied.
    atlas.add('ic-tabmark-tear',tear())
    atlas.add('ic-tabmark-tear-inactive',tear())
