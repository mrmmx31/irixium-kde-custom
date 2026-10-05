#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Deterministic, integer-grid SVG artwork for IrixClassic (Kvantum 1.1.4).

New drawing, not SGI code. Plain surfaces and bevel colors were sampled from
reference screenshots; tabs, checkbox/radio shapes and unshown states are
explicitly adaptations. No fonts, screenshots or external resources are embedded.
"""
from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET
import scrollbar_art as SB
import button_art as BT

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
STATES = ('normal','focused','pressed','toggled','disabled')
PALETTE = {'window':'#c1c1c1','button':'#999999','entry':'#b6b6aa','base':'#efefef',
           'light':'#ececec','shadow':'#606060','selected':'#9ebfbf','ink':'#000000'}
PARTS = ('top','bottom','left','right','topleft','topright','bottomleft','bottomright')


def blank(w,h,color=None):
    return [[color for _ in range(w)] for _ in range(h)]

def rect(img,x,y,w,h,color):
    for j in range(max(0,y),min(len(img),y+h)):
        for i in range(max(0,x),min(len(img[0]),x+w)):
            img[j][i] = color

def bevel(img, n=3, down=False, plain=False, button=False):
    h,w=len(img),len(img[0])
    if plain: return img
    if button:
        top = ['#4c4c4c','#e1e1e1','#cccccc']
        bottom = ['#252525','#4c4c4c','#737373']
    else:
        top = ['#ececec','#dfdfdf','#c1c1c1']
        bottom = ['#606060','#919191','#b1b1b1']
    if down: top,bottom=bottom,top
    for k in range(n):
        t,b=top[min(k,2)],bottom[min(k,2)]
        rect(img,k,k,w-2*k,1,t); rect(img,k,k,1,h-2*k,t)
        rect(img,k+1,h-k-1,w-2*k-1,1,b); rect(img,w-k-1,k+1,1,h-2*k-1,b)
    return img


def surface(kind,state,w=24,h=24):
    down=state in ('pressed','toggled')
    face=PALETTE['window']
    if kind in ('button','thumb','slidercursor'): face=PALETTE['button']
    if kind=='entry': face=PALETTE['entry']
    if kind=='groove': face=PALETTE['button']
    if kind=='progress': face=PALETTE['selected']
    if kind=='tab' and not down: face='#a7a7a7'
    if kind=='item': face=PALETTE['selected'] if state=='toggled' else None
    if kind=='view': face=PALETTE['base']
    n = 3 if kind in ('button','entry','common','view','group','tabframe') else 2
    img=blank(w,h,face)
    flat=kind in ('window','item') or (kind in ('tool','menuitem','menubaritem') and state in ('normal','disabled'))
    is_down = True if kind in ('entry','groove','common','view') else down
    if kind in ('window','item'): return img, n
    if kind=='tab' and down:
        bevel(img,n=n); rect(img,0,h-2,w,2,PALETTE['window'])
    elif kind=='bar':
        rect(img,0,0,w,2,'#ececec'); rect(img,0,h-1,w,1,'#919191')
    elif kind=='group':
        bevel(img,n=3,down=True)
    else:
        bevel(img,n=n,down=is_down,plain=flat,button=kind in ('button','thumb','slidercursor'))
    if state=='disabled':
        # Avoid a black-looking available symbol; Qt additionally applies its
        # disabled palette/opacity. Full control geometry remains unchanged.
        for y in range(h):
            for x in range(w):
                if img[y][x] in ('#000000','#252525','#4c4c4c'):
                    img[y][x]='#858585'
    return img,n


def slice9(img,n):
    h,w=len(img),len(img[0])
    boxes={'':(n,n,w-n,h-n),'top':(n,0,w-n,n),'bottom':(n,h-n,w-n,h),
           'left':(0,n,n,h-n),'right':(w-n,n,w,h-n),'topleft':(0,0,n,n),
           'topright':(w-n,0,w,n),'bottomleft':(0,h-n,n,h),'bottomright':(w-n,h-n,w,h)}
    return {part:[row[x0:x1] for row in img[y0:y1]] for part,(x0,y0,x1,y1) in boxes.items()}

class Atlas:
    def __init__(self):
        self.root=ET.Element('{'+NS+'}svg',{'version':'1.1','width':'768','height':'4096','viewBox':'0 0 768 4096','shape-rendering':'crispEdges'})
        ET.SubElement(self.root,'{'+NS+'}title').text='IrixClassic — application controls, 0.2.0-rc1'
        ET.SubElement(self.root,'{'+NS+'}desc').text='New integer-grid artwork by mrmmx31. GPL-3.0-or-later. No SGI code or fonts.'
        self.items={}
    def add(self,name,img):
        if name in self.items: raise ValueError('Duplicate: '+name)
        index=len(self.items); x=(index%16)*48; y=(index//16)*40
        h,w=len(img),len(img[0])
        g=ET.SubElement(self.root,'{'+NS+'}g',{'id':name,'transform':f'translate({x},{y})'})
        # Establish bounds even for transparent states and thin glyphs.
        ET.SubElement(g,'{'+NS+'}rect',{'x':'0','y':'0','width':str(w),'height':str(h),'fill':'#000000','fill-opacity':'0'})
        # Merge identical horizontal runs vertically; retain the exact pixel map.
        active={}; blocks=[]
        for j,row in enumerate(img):
            runs=set(); start=0
            while start<w:
                color=row[start]; end=start+1
                while end<w and row[end]==color: end+=1
                if color is not None: runs.add((start,end-start,color))
                start=end
            for key in list(active):
                if key not in runs:
                    y0=active.pop(key);blocks.append((*key,y0,j-y0))
            for key in runs:
                if key not in active:active[key]=j
        for key,y0 in active.items():blocks.append((*key,y0,h-y0))
        for left,width,color,top,height in sorted(blocks,key=lambda b:(b[3],b[0],b[2])):
            ET.SubElement(g,'{'+NS+'}rect',{'x':str(left),'y':str(top),'width':str(width),'height':str(height),'fill':color})
        self.items[name]=img
    def frames(self,prefix,img,n):
        for part,pixels in slice9(img,n).items():
            self.add(prefix+('-'+part if part else ''),pixels)
        # Optional attached-tab junctions are explicit, not theme-engine fallbacks.
        parts=slice9(img,n)
        for side in ('top','bottom','left','right'):
            for pos in ('left','right'):
                corner = ('top' if side in ('top','left') else 'bottom') + pos
                self.add(prefix+'-'+side+'-'+pos+'junct',parts[corner])


def arrow(state,direction,size=12,boxed=False):
    img=blank(size,size,PALETTE['button'] if boxed else None)
    if boxed: bevel(img,n=2,down=state in ('pressed','toggled'),button=True)
    color='#858585' if state=='disabled' else '#4c4c4c'
    c=size//2; radius=3 if boxed else 3
    pts=[]
    for yy in range(radius+1):
        for xx in range(-yy,yy+1): pts.append((c+xx,c-radius//2+yy))
    for x,y in pts:
        if direction=='down': x,y=size-1-x,size-1-y
        elif direction=='left': x,y=y,x
        elif direction=='right': x,y=size-1-y,x
        if 0<=x<size and 0<=y<size: img[y][x]=color
    return img


def check(kind,checked,state,size=15):
    img=blank(size,size,None)
    col='#858585' if state=='disabled' else '#000000'
    down=checked in ('checked','tristate')
    if kind=='check':
        small=blank(size-2,size-2,PALETTE['button'] if down else PALETTE['window'])
        bevel(small,n=2,down=down or state=='pressed')
        for y,row in enumerate(small):
            for x,val in enumerate(row): img[y+1][x+1]=val
        if checked=='checked':
            for x,y in [(4,7),(5,8),(6,9),(7,8),(8,7),(9,6),(10,5)]: rect(img,x,y,2,2,col)
        elif checked=='tristate': rect(img,4,6,7,3,col)
    else:
        c=size//2
        for y in range(1,size-1):
            for x in range(1,size-1):
                d=abs(x-c)+abs(y-c)
                if d<=6:
                    img[y][x]=PALETTE['window']
                    if d>=5: img[y][x]=('#606060' if down else '#ececec') if x+y<=2*c else ('#ececec' if down else '#606060')
                    if down and d<=2: img[y][x]=col
    return img


def build():
    a=Atlas()
    kinds=['button','tool','entry','common','view','tab','tabframe','bar','menu','menuitem','menubaritem','group','groove','thumb','slidercursor','progress','item']
    for kind in kinds:
        for state in STATES:
            img,n=surface(kind,state)
            a.frames('ic-'+kind+'-'+state,img,n)
    for state in STATES:
        a.add('ic-window-'+state,blank(8,8,PALETTE['window']))
        for direction in ('up','down','left','right'):
            a.add('ic-arrow-'+direction+'-'+state,arrow(state,direction))
            a.add('ic-scrollarrow-'+direction+'-'+state,SB.arrow(state,direction))
        a.add('ic-arrow-'+state,arrow(state,'down'))
        a.add('ic-arrow-down-down-'+state,arrow(state,'down'))
        for kind in ('check','radio'):
            for checked in ('unchecked','checked','tristate'):
                a.add('ic-'+kind+'-'+checked+'-'+state,check(kind,checked,state))
                a.add('menu-ic-'+kind+'-'+checked+'-'+state,check(kind,checked,state))
        # Both naming conventions used for grip orientation are supplied.
        for prefix in ('ic-grip','ic-splitgrip','ic-toolbar','ic-slidergrip'):
            for orientation in ('horizontal','vertical'):
                img=blank(10,10,None)
                for i in (2,4,6):
                    if orientation=='horizontal':
                        rect(img,1,i,8,1,'#606060'); rect(img,1,i+1,8,1,'#ececec')
                    else:
                        rect(img,i,1,1,8,'#606060'); rect(img,i+1,1,1,8,'#ececec')
                a.add(prefix+'-'+orientation+'-'+state,img)
                a.add(prefix+'-'+state+'-'+orientation,img)
            a.add(prefix+'-'+state,a.items[prefix+'-horizontal-'+state])
        for sign in ('plus','minus'):
            img=blank(9,9,PALETTE['base']); col='#858585' if state=='disabled' else '#000000'
            rect(img,0,0,9,1,col);rect(img,0,8,9,1,col);rect(img,0,0,1,9,col);rect(img,8,0,1,9,col)
            rect(img,2,4,5,1,col)
            if sign=='plus': rect(img,4,2,1,5,col)
            a.add('ic-tree-'+sign+'-'+state,img)
        for sign,kind in [('close','close'),('left','left'),('right','right')]:
            img=arrow(state,kind) if kind!='close' else blank(12,12,None)
            if kind=='close':
                for i in range(3,9): rect(img,i,i,1,1,'#000000');rect(img,11-i,i,1,1,'#000000')
            a.add('ic-tab-'+sign+'-'+state,img)
        sizegrip=blank(15,15,None)
        for i in range(3,13,3):
            for j in range(i,14):
                x=j; y=14+i-j
                if 0<=y<15: sizegrip[y][x]='#606060'
        a.add('ic-sizegrip-'+state,sizegrip)
    a.add('ic-sizegrip', a.items['ic-sizegrip-normal'])
    # Unstated indicator names used by the Kvantum 1.1.4 toolbar/menu paths.
    a.add('ic-toolbar-handle', a.items['ic-toolbar-vertical-normal'])
    separator=blank(10,2,None)
    rect(separator,0,0,10,1,'#919191'); rect(separator,0,1,10,1,'#ececec')
    a.add('ic-toolbar-separator',separator)
    a.add('ic-arrow-separator',separator)
    # Default button indication: separate from keyboard focus and press state.
    default=blank(24,24,None)
    for k in range(2):
        rect(default,k,k,24-2*k,1,'#000000');rect(default,k,k,1,24-2*k,'#000000')
        rect(default,k,23-k,24-2*k,1,'#000000');rect(default,23-k,k,1,24-2*k,'#000000')
    a.frames('ic-button-default',default,3)
    for state in STATES:
        for part in PARTS:
            w,h=(2,1) if part in ('top','bottom') else (1,2) if part in ('left','right') else (1,1)
            pixels=blank(w,h,None); pixels[0][0]='#000000'
            a.add('ic-focus-'+state+'-'+part,pixels)
    # Frame code may request this without a state suffix.
    for part in PARTS:
        a.add('ic-focus-'+part,a.items['ic-focus-normal-'+part])
    # New, scrollbar-only assets do not move the existing atlas entries.
    SB.append_scrollbar_assets(a, STATES)
    # Append isolated block-2 resources; preserve all existing element positions.
    BT.append_assets(a)
    height=((len(a.items)+15)//16)*40
    a.root.set('height',str(height)); a.root.set('viewBox',f'0 0 768 {height}')
    ET.indent(a.root,space='  ')
    return a

if __name__=='__main__':
    path=Path(__file__).resolve().parent.parent/'IrixClassic/IrixClassic.svg'
    atlas=build()
    ET.ElementTree(atlas.root).write(path,encoding='utf-8',xml_declaration=True)
    print(f'{path.name}: {len(atlas.items)} elementos.')
