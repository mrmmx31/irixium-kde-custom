#!/usr/bin/env python3
"""Build IrixClassic-SGI: original, editable SVG icons and native-size PNGs.

No SGI binary artwork, fonts, Irixium artwork or Breeze assets are copied.
Python >= 3.10. PNG generation: python3-cairosvg. Previews: python3-pil.
SPDX-License-Identifier: MIT
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
import shutil
import sys
from pathlib import Path

VERSION = '0.1.0'
THEME = 'IrixClassic-SGI'
SIZES = (16, 22, 24, 32, 48, 64, 96, 128)
INK = '#20201e'
LIGHT = '#f3f2e9'
PAPER = '#e3e1d7'
MID = '#b9b8ad'
DARK = '#777970'
SHADOW = '#50534e'
PURPLE = '#76618d'
BLUE = '#52748c'
TEAL = '#538478'
RED = '#a1514e'
GOLD = '#b29b55'


def poly(points: str, fill: str = PAPER, stroke: str = INK, w: float = 1.1) -> str:
    return f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="miter"/>'


def path(d: str, fill: str = 'none', stroke: str = INK, w: float = 1.2) -> str:
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="square"/>'


def rect(x: float, y: float, w: float, h: float, fill: str = PAPER, stroke: str = INK, sw: float = 1.1) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def circle(x: float, y: float, r: float, fill: str = PAPER, stroke: str = INK, sw: float = 1.1) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def ellipse(x: float, y: float, rx: float, ry: float, fill: str = PAPER, stroke: str = INK, sw: float = 1.1) -> str:
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def group(s: str, transform: str) -> str:
    return f'<g transform="{transform}">{s}</g>'


def svg(body: str, name: str, size: int = 64, box: int = 64) -> str:
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 {box} {box}">\n'
            f'<title>{html.escape(name)} — IrixClassic-SGI</title>\n'
            '<desc>Original artwork inspired by the SGI Indigo Magic design language. MIT license.</desc>\n'
            f'{body}\n</svg>\n')


def shadow() -> str:
    return poly('8,54 39,39 59,49 27,61', SHADOW, 'none')


def carpet() -> str:
    return (poly('6,51 38,35 59,46 27,62', SHADOW, 'none') +
            poly('6,48 38,32 59,43 27,59', LIGHT) +
            path('M9 48L27 56L55 43', stroke=MID, w=1.2))


def mark(kind: str, color: str = PURPLE) -> str:
    """A small front-facing symbol, nominal 0..20 by 0..20."""
    if kind in ('text', 'documents'):
        return ''.join(path(f'M3 {y}H{15 if y!=15 else 11}', stroke=INK, w=1.3) for y in (3, 7, 11, 15))
    if kind in ('code', 'script'):
        return path('M7 4L2 10L7 16M13 4L18 10L13 16', stroke=color, w=2) + path('M12 2L9 18', stroke=INK)
    if kind in ('image', 'pictures'):
        return rect(1, 2, 18, 16, LIGHT) + circle(14, 6, 2, GOLD, 'none') + poly('2,16 7,9 11,13 15,10 18,16', TEAL, 'none')
    if kind in ('music', 'audio'):
        return path('M8 15V4L16 2V13M8 6L16 4', stroke=color, w=2.4) + ellipse(5, 16, 3, 2, color, 'none') + ellipse(13, 14, 3, 2, color, 'none')
    if kind in ('video', 'videos'):
        return rect(1, 3, 18, 14, INK) + poly('8,6 8,14 14,10', LIGHT, 'none') + ''.join(rect(x, y, 2, 1, MID, 'none') for x in (3,8,13) for y in (4,15))
    if kind in ('download', 'down'):
        return poly('7,2 13,2 13,10 18,10 10,18 2,10 7,10', color)
    if kind == 'up':
        return group(mark('down', color), 'rotate(180 10 10)')
    if kind in ('network', 'remote', 'public'):
        return path('M10 6V12M2 12H18M3 12V17M17 12V17', w=1.4) + rect(6,1,8,5,color) + rect(0,15,6,4,MID) + rect(14,15,6,4,MID)
    if kind == 'home':
        return poly('3,8 10,2 17,8 17,18 3,18', PAPER) + poly('1,9 10,0 19,9 16,9 10,3 4,9', RED) + rect(8,11,4,7,PURPLE)
    if kind in ('search', 'find'):
        return circle(8,8,6,LIGHT) + circle(8,8,4,BLUE,'none') + path('M13 13L19 19',stroke=INK,w=4) + path('M13 13L18 18',stroke=MID,w=2)
    if kind == 'link':
        return path('M8 13L5 16C1 19 -1 14 2 11L6 7C9 4 13 7 11 10M12 7L15 4C19 1 22 6 18 10L14 14C11 17 7 13 9 11M7 13L13 7', stroke=BLUE, w=2.6)
    if kind == 'star':
        return poly('10,1 12.8,6.4 19,7.5 14.5,12 15.7,18.5 10,15.6 4.3,18.5 5.5,12 1,7.5 7.2,6.4',GOLD)
    if kind == 'pdf':
        return path('M6 18V2H12Q18 2 18 7Q18 12 12 12H6',stroke=RED,w=2.6)
    if kind == 'table':
        return rect(1,2,18,16,LIGHT) + rect(1,2,18,4,TEAL) + path('M1 10H19M1 14H19M7 6V18M13 6V18',w=.8)
    if kind == 'slides':
        return rect(1,2,18,14,LIGHT) + rect(3,4,14,3,GOLD,'none') + rect(4,10,3,4,BLUE,'none') + rect(9,8,3,6,TEAL,'none')
    if kind == 'archive':
        return rect(3,1,14,18,GOLD) + rect(8,1,4,18,PAPER) + ''.join(rect(9,y,2,1,INK,'none') for y in (3,6,9,12,15))
    if kind == 'lock':
        return path('M5 10V6C5 0 15 0 15 6V10',stroke=INK,w=2.5) + rect(2,9,16,10,GOLD) + circle(10,13,1.7,INK,'none') + path('M10 13V17',w=1.4)
    if kind == 'check':
        return path('M2 10L8 16L19 3',stroke=INK,w=4.5) + path('M2 10L8 16L19 3',stroke=TEAL,w=2.5)
    if kind == 'error':
        return path('M3 3L17 17M17 3L3 17',stroke=INK,w=4) + path('M3 3L17 17M17 3L3 17',stroke=RED,w=2)
    if kind == 'plus':
        return poly('7,1 13,1 13,7 19,7 19,13 13,13 13,19 7,19 7,13 1,13 1,7 7,7',TEAL)
    if kind == 'minus':
        return rect(2,7,16,6,RED)
    if kind == 'help':
        return path('M4 6Q4 0 10 1Q18 1 16 7Q15 10 10 11V14',stroke=BLUE,w=3) + rect(9,17,3,3,BLUE,'none')
    if kind == 'info':
        return circle(10,4,2,BLUE,'none') + rect(8.5,8,3,11,BLUE,'none')
    if kind == 'terminal':
        return rect(1,2,18,16,'#22262b') + path('M4 6L8 10L4 14M10 14H16',stroke=LIGHT,w=1.7)
    if kind == 'mail':
        return rect(1,4,18,12,LIGHT) + path('M1 4L10 11L19 4M1 16L7 10M19 16L13 10',w=1)
    if kind == 'template':
        return rect(3,1,14,18,LIGHT) + path('M5 4H15M5 8H11M5 12H15M5 16H11',stroke=BLUE)
    return circle(10,10,7,color)


def paper(kind: str = 'text') -> str:
    s=shadow()
    for x,y,c in ((14,19,MID),(17,20,LIGHT),(20,21,PAPER)):
        s += group(rect(0,0,25,33,c), f'matrix(1 -.5 0 1 {x} {y})')
    s += group(mark(kind), 'matrix(1 -.5 0 1 23 27)')
    return s


def folder(kind: str = '', opened: bool = False) -> str:
    s=shadow()
    s+=poly('12,24 25,17 31,19 45,12 50,15 50,43 19,59 12,55',MID)
    s+=poly('14,25 26,19 31,22 47,14 47,42 17,57',LIGHT)
    if opened:
        s+=poly('19,37 58,20 52,43 19,59',PAPER)
        s+=path('M20 38L55 22',stroke=LIGHT)
    else:
        s+=poly('17,31 48,15 53,39 20,57',PAPER)
        s+=path('M19 31L47 17L51 38',stroke=LIGHT)
    if kind:
        s+=group(mark(kind),'matrix(.82 -.41 .1 .82 28 34)')
    return s


def monitor(terminal: bool = False, graph: bool = False) -> str:
    s=poly('10,48 34,36 55,45 29,58',SHADOW,'none')
    s+=poly('12,18 43,3 53,10 23,25',LIGHT)
    s+=poly('12,18 23,25 23,48 12,40',DARK)
    front=rect(0,0,30,25,PAPER)+rect(3,3,24,17,'#2a3040')
    if terminal:
        front+=path('M6 6L10 9L6 12M12 13H20',stroke='#dce7d4',w=1.25)
    elif graph:
        front+=path('M5 17L9 14L13 16L17 7L20 14L26 9',stroke='#93b58d',w=1.5)
    else:
        front+=rect(5,5,12,10,PURPLE,'none')+rect(8,8,16,10,BLUE,INK,.7)
    front+=rect(24,22,2,1.4,TEAL,'none')
    s+=group(front,'matrix(1 -.5 0 1 23 25)')
    s+=poly('29,46 39,41 39,48 30,53',MID)+poly('22,55 37,47 46,51 31,59',PAPER)
    return s


def globe() -> str:
    s=circle(33,26,19,BLUE)
    s+=path('M33 7C15 15 15 37 33 45M33 7C49 16 49 37 33 45M16 16Q33 27 50 16M14 30Q33 38 51 30',stroke='#abc0c6',w=1.2)
    s+=poly('19,16 24,12 29,14 28,21 22,23 25,28 20,29 17,22',TEAL,INK,.6)
    s+=poly('35,25 44,22 48,28 44,33 43,39 38,36',TEAL,INK,.6)
    s+=path('M19 42Q10 23 22 9',stroke=PAPER,w=2)
    return s


def envelope() -> str:
    return group(rect(0,0,34,24,LIGHT)+path('M0 0L17 14L34 0M0 24L13 11M34 24L21 11',w=1.2), 'matrix(1 -.5 0 1 16 27)')


def wrench() -> str:
    return (path('M37 7L33 18L42 22L48 12C54 25 48 30 41 30L23 51C17 57 10 48 15 43L33 25C24 15 31 7 37 7Z', MID)
            +path('M18 47L39 24',stroke=LIGHT,w=2)+circle(18,47,2,INK,'none'))


def pencil() -> str:
    return poly('40,8 46,11 26,51 18,57 18,47',GOLD)+poly('40,8 43,3 49,6 46,11',RED)+poly('18,47 26,51 18,57',PAPER)+poly('18,53 21,55 18,57',INK,'none')+path('M43 11L22 49',stroke=LIGHT)


def calculator() -> str:
    c=rect(0,0,26,38,MID)+rect(3,3,20,8,'#aab7a5')
    c+=path('M10 8H13M16 6H19M16 9H19',w=1)
    for x in (3,10,17):
        for y in (15,22,29):
            c+=rect(x,y,5,5,PURPLE if x==17 else LIGHT,INK,.8)
    return group(c,'matrix(1 -.5 0 1 21 18)')


def clock() -> str:
    s=ellipse(32,28,17,21,MID)+ellipse(30,27,15,20,LIGHT)
    s+=path('M30 10V13M30 41V44M18 27H21M40 27H43',w=1.3)
    s+=path('M30 17V27L38 31',w=2)
    s+=poly('21,47 27,43 40,48 33,52',PAPER)
    return s


def archive() -> str:
    return (poly('15,18 41,5 51,11 25,24',LIGHT)+poly('15,18 25,24 25,53 15,47',DARK)+
            group(rect(0,0,26,29,MID)+rect(3,4,20,9,PAPER)+rect(3,16,20,9,PAPER)+path('M10 8H17M10 20H17',w=2), 'matrix(1 -.5 0 1 25 24)'))


def printer() -> str:
    return (shadow()+poly('10,30 35,17 54,27 28,41',LIGHT)+poly('10,30 28,41 28,54 10,44',DARK)+poly('28,41 54,27 54,43 28,56',MID)+
            group(rect(0,0,22,23,LIGHT)+path('M4 6H18M4 10H18M4 14H13',w=1), 'matrix(1 -.5 0 1 24 17)')+
            path('M31 46L50 36',w=3)+poly('31,47 49,38 49,48 31,57',LIGHT)+circle(48,31,1.4,TEAL,'none'))


def drive(kind: str = 'harddisk') -> str:
    s=shadow()+poly('8,33 36,19 56,30 29,44',LIGHT)+poly('8,33 29,44 29,54 8,43',DARK)+poly('29,44 56,30 56,42 29,56',MID)
    s+=path('M33 47L52 38',w=2.4)+circle(51,43,1.4,TEAL,'none')
    if kind=='optical':
        s+=ellipse(32,27,17,9,PAPER)+ellipse(32,27,4,2.2,DARK)+path('M21 21L27 26M38 29L45 33',stroke=BLUE,w=2)
    if kind=='usb':
        s+=group(mark('network'),'matrix(.7 -.35 0 .7 23 25)')
    return s


def trash(full: bool = False) -> str:
    s=shadow()+poly('14,26 38,14 53,23 30,35',DARK)
    if full:
        s+=poly('19,23 19,10 31,15 35,28',LIGHT)+poly('32,23 37,5 48,12 47,23',PAPER)+path('M21 14L29 18M39 11L45 14',w=.8)
    s+=poly('14,26 30,35 32,57 18,48',MID)+poly('30,35 53,23 49,46 32,57',PAPER)
    s+=path('M35 36L36 50M41 33L40 48M47 30L44 45',stroke=DARK,w=1.3)
    if full:
        s+=poly('9,17 27,3 36,10 16,24',PAPER)+poly('9,17 16,24 16,27 9,20',DARK)
    else:
        s+=poly('11,25 37,12 56,22 30,36',LIGHT)+poly('11,25 30,36 30,39 11,28',DARK)+poly('30,36 56,22 56,25 30,39',MID)+path('M28 23L36 19L41 21L33 25Z',w=1.3)
    return s


def database() -> str:
    s=shadow()
    for y in (38,27,16):
        s+=path(f'M16 {y}V{y+10}C16 {y+21} 49 {y+21} 49 {y+10}V{y}',MID)
        s+=ellipse(32.5,y,16.5,7,LIGHT)+path(f'M20 {y+10}V{y+12}',stroke=TEAL,w=2)
    return s


def book() -> str:
    return shadow()+poly('15,16 41,3 49,8 22,22',LIGHT)+poly('15,16 22,22 22,56 15,51',DARK)+poly('22,22 49,8 49,44 22,57',PURPLE)+group(mark('help',LIGHT),'matrix(1 -.5 0 1 25 26)')


def image_app() -> str:
    return group(mark('image'),'matrix(1.8 -.8 0 1.8 15 21)')+path('M33 47V55M25 55L39 48',w=2)


def speaker() -> str:
    return poly('19,25 30,20 43,7 43,47 30,38 19,40',PAPER)+poly('15,22 19,25 19,40 15,35',DARK)+path('M47 20Q55 26 47 33M51 14Q64 26 51 39',stroke=BLUE,w=2)


def app(kind: str) -> str:
    base=carpet()
    if kind=='terminal': return base+group(monitor(True),'translate(2 -1) scale(.9)')
    if kind=='computer': return base+group(monitor(),'translate(2 -1) scale(.9)')
    if kind=='monitor': return base+group(monitor(graph=True),'translate(2 -1) scale(.9)')
    if kind=='browser': return base+globe()
    if kind=='mail': return base+envelope()
    if kind=='settings': return base+wrench()
    if kind=='editor': return base+group(paper('text'),'translate(3 -1) scale(.84)')+pencil()
    if kind=='calculator': return base+calculator()
    if kind=='clock': return base+clock()
    if kind=='archive': return base+archive()
    if kind=='image': return base+image_app()
    if kind=='help': return base+group(book(),'translate(2 -1) scale(.88)')
    if kind=='database': return base+group(database(),'translate(2 -2) scale(.87)')
    if kind=='files': return base+group(folder(),'translate(2 -3) scale(.87)')
    if kind=='sound': return base+group(speaker(),'translate(2 -1) scale(.9)')
    if kind=='video': return base+group(mark('video'),'matrix(2 -.8 0 2 13 18)')
    if kind=='code': return base+group(paper('code'),'translate(3 -2) scale(.87)')
    if kind=='office': return base+group(paper('table'),'translate(3 -2) scale(.87)')+pencil()
    if kind=='calendar':
        c=rect(0,0,30,32,LIGHT)+rect(0,0,30,7,PURPLE)+path('M7 -3V4M23 -3V4',w=2)
        for x in (5,12,19):
            for y in (12,19,26):c+=rect(x,y,3,3,BLUE if x==12 and y==19 else DARK,'none')
        return base+group(c,'matrix(1 -.5 0 1 20 23)')
    if kind=='package': return base+box()
    if kind=='paint':
        return base+ellipse(30,28,20,16,PAPER)+ellipse(39,32,5,4,SHADOW)+''.join(circle(x,y,3,c) for x,y,c in ((18,22,RED),(28,17,GOLD),(39,20,BLUE),(17,33,TEAL)))+group(pencil(),'translate(15 0) scale(.8)')
    if kind=='camera':
        c=poly('12,21 39,8 53,16 27,29',LIGHT)+poly('12,21 27,29 27,47 12,39',DARK)+poly('27,29 53,16 53,35 27,48',MID)+ellipse(39,31,9,11,DARK)+ellipse(39,31,6,8,BLUE)+poly('21,17 31,12 37,16 27,21',MID)
        return base+c
    if kind=='generic': return base+box()
    raise ValueError(kind)


def box() -> str:
    return (poly('14,23 36,12 51,20 29,31',LIGHT)+poly('14,23 29,31 29,54 14,45',DARK)+poly('29,31 51,20 51,44 29,56',MID)+poly('23,18 38,26 43,23 28,16',GOLD)+poly('38,26 43,23 43,47 38,50',GOLD))


def arrow(direction: str) -> str:
    # A restrained, faceted pointer, not a modern rounded chevron.
    p=poly('8,25 32,25 32,12 56,32 32,52 32,39 8,39',PAPER,w=1.8)
    p+=path('M10 27H34V17L52 32',stroke=LIGHT,w=2.4)
    p+=path('M10 38H33L33 48L53 33',stroke=DARK,w=2)
    angle = {"right":0, "down":90, "left":180, "up":270}[direction]
    return group(p, f"rotate({angle} 32 32)")


def action(kind: str) -> str:
    if kind in ('left','right','up','down'):return arrow(kind)
    if kind in ('plus','minus','check','error','search','lock','help','info','star'):
        return group(mark(kind),'translate(7 7) scale(2.5)')
    if kind=='play':return poly('18,10 53,32 18,54',TEAL,w=1.8)+path('M20 13L48 31',stroke=LIGHT,w=2)
    if kind=='pause':return rect(14,12,12,40,PAPER,INK,1.8)+rect(38,12,12,40,PAPER,INK,1.8)+path('M16 14V50M40 14V50',stroke=LIGHT,w=2)
    if kind=='stop':return rect(13,13,38,38,RED,INK,1.8)+path('M15 49V15H49',stroke=LIGHT,w=2)
    if kind=='record':return circle(32,32,20,RED,INK,1.8)+path('M18 28Q22 15 33 17',stroke=LIGHT,w=2)
    if kind in ('skip-forward','skip-backward'):
        s=poly('10,14 34,32 10,50',PAPER,w=1.7)+poly('29,14 53,32 29,50',PAPER,w=1.7)+rect(51,14,5,36,MID)
        return group(s,'rotate(180 32 32)') if kind=='skip-backward' else s
    if kind in ('refresh','undo','redo'):
        s=path('M49 28C44 7 13 9 12 31C11 46 26 54 40 47',stroke=INK,w=8)+path('M49 28C44 7 13 9 12 31C11 46 26 54 40 47',stroke=PAPER,w=5)+poly('37,25 52,36 58,18',PAPER,w=1.5)
        return group(s,'translate(64 0) scale(-1 1)') if kind=='undo' else s
    if kind=='save':return poly('13,8 45,8 53,16 53,56 13,56',MID,w=1.7)+rect(20,8,24,18,LIGHT)+rect(35,10,6,13,DARK)+rect(20,36,26,20,LIGHT)+path('M24 42H42M24 47H42',stroke=BLUE)
    if kind=='open':return folder(opened=True)
    if kind=='new':return paper('text')+group(mark('plus'),'translate(39 39) scale(1.1)')
    if kind=='copy':return group(paper('text'),'translate(-6 -4)')+group(paper('text'),'translate(5 4) scale(.87)')
    if kind=='paste':return rect(15,10,35,45,MID)+rect(24,6,18,9,PAPER)+group(mark('text'),'translate(18 21) scale(1.4)')
    if kind=='cut':return circle(17,45,8,LIGHT)+circle(36,45,8,LIGHT)+path('M22 39L46 8M31 39L15 8',stroke=INK,w=5)+path('M22 39L46 8M31 39L15 8',stroke=MID,w=3)+circle(27,31,2.5,INK,'none')
    if kind=='print':return printer()
    if kind=='folder-new':return folder()+group(mark('plus'),'translate(39 39) scale(1.1)')
    if kind=='grid':return ''.join(rect(x,y,14,14,PAPER) + rect(x+2,y+2,5,5,PURPLE,'none') for x in (12,37) for y in (12,37))
    if kind=='list':return ''.join(rect(10,y,8,8,PAPER)+path(f'M24 {y+2}H54M24 {y+6}H48',w=1.5) for y in (12,28,44))
    if kind=='split':return rect(8,12,48,40,PAPER)+path('M32 12V52',w=2)+rect(12,17,15,29,LIGHT)+rect(37,17,15,29,LIGHT)
    if kind=='hidden':return path('M6 32Q32 6 58 32Q32 58 6 32Z',PAPER)+circle(32,32,11,BLUE)+circle(32,32,4,INK)+path('M8 8L56 56',stroke=LIGHT,w=5)+path('M8 8L56 56',stroke=INK,w=2)
    if kind=='menu':return ''.join(rect(11,y,42,6,PAPER) for y in (14,29,44))
    if kind=='logout':return rect(12,7,30,49,PAPER)+poly('12,7 29,14 29,61 12,56',MID)+group(arrow('right'),'translate(22 15) scale(.65)')
    if kind=='shutdown':return path('M20 14C-1 29 10 55 32 55C54 55 65 29 44 14',stroke=INK,w=8)+path('M20 14C-1 29 10 55 32 55C54 55 65 29 44 14',stroke=PAPER,w=5)+path('M32 7V32',stroke=INK,w=7)+path('M32 7V32',stroke=RED,w=4)
    if kind=='volume':return speaker()
    raise ValueError(kind)


def status(kind: str) -> str:
    if kind in ('warning','error','information','question','success'):
        if kind=='warning': return poly('32,5 60,55 4,55',GOLD,w=1.8)+rect(29,22,6,18,INK,'none')+rect(29,46,6,5,INK,'none')
        color={'error':RED,'information':BLUE,'question':PURPLE,'success':TEAL}[kind]
        inner={'error':'error','information':'info','question':'help','success':'check'}[kind]
        return circle(32,32,26,LIGHT,INK,1.5)+circle(32,32,22,PAPER,color,2)+group(mark(inner),'translate(14 14) scale(1.8)')
    if kind.startswith('battery'):
        parts=kind.split('-');level=int(parts[1]);charging='charging' in parts
        c=RED if level<=20 else TEAL
        s=rect(7,19,48,29,PAPER)+rect(55,27,4,13,MID)+rect(11,23,40,21,LIGHT)
        if level:s+=rect(13,25,36*level/100,17,c,'none')
        if charging:s+=poly('33,10 20,34 30,34 25,54 44,28 34,28 40,10',GOLD,w=1.8)
        return s
    if kind.startswith('volume-'):
        level=kind.split('-')[1]
        s=poly('8,25 21,25 33,13 33,51 21,39 8,39',PAPER,w=1.6)
        n={'muted':0,'low':1,'medium':2,'high':3}[level]
        for i in range(n):s+=path(f'M{38+6*i} {25-6*i}Q{46+8*i} 32 {38+6*i} {39+6*i}',stroke=BLUE,w=2)
        if level=='muted':s+=group(mark('error'),'translate(39 23)')
        return s
    if kind.startswith('network'):
        s=group(mark('network'),'translate(6 7) scale(2.5)')
        if kind=='network-offline':s+=group(mark('error'),'translate(37 36) scale(1.1)')
        return s
    raise ValueError(kind)


# (category, canonical name, kind, variant, aliases)
ITEMS: list[dict] = []
USED: set[str] = set()


def add(category: str, name: str, kind: str, variant: str='', aliases: str='') -> None:
    names=[name]+aliases.split()
    for n in names:
        if n in USED:raise ValueError(f'Duplicate icon name across contexts: {n}')
        USED.add(n)
    ITEMS.append(dict(category=category,name=name,kind=kind,variant=variant,aliases=names[1:]))


# Directories and navigation.
add('places','folder','folder',aliases='inode-directory gtk-directory stock_folder')
add('places','folder-open','folder','open',aliases='folder_open')
for variant,canonical,aliases in (
    ('home','user-home','folder-home folder_home go-home'),
    ('documents','folder-documents',''),('download','folder-download','folder-downloads'),
    ('music','folder-music',''),('pictures','folder-pictures',''),('videos','folder-videos',''),
    ('public','folder-publicshare','folder-shared'),('remote','folder-remote',''),
    ('template','folder-templates',''),('search','folder-saved-search','folder-search')):
    add('places',canonical,'folder',variant,aliases)
add('places','user-trash','trash',aliases='user-trash-empty trashcan_empty emptytrash')
add('places','user-trash-full','trash','full',aliases='trashcan_full')
add('places','user-desktop','monitor',aliases='desktop')
add('places','network-workgroup','status','network-online',aliases='network network-server preferences-system-network')
add('places','user-bookmarks','action','star',aliases='bookmarks favorites')
add('places','folder-root','folder','terminal',aliases='folder-system')

# Data-file symbols retain the three-sheet motif.
for canonical,variant,aliases in (
 ('text-plain','text','text-x-generic application-octet-stream unknown'),
 ('text-x-script','code','text-x-python text-x-shellscript application-x-shellscript text-x-java text-x-csrc text-x-c++src text-x-chdr text-x-javascript application-json application-javascript application-xml text-xml'),
 ('text-html','code','application-xhtml+xml'),
 ('application-pdf','pdf','application-postscript'),
 ('image-x-generic','image','image-png image-jpeg image-gif image-svg+xml image-webp image-tiff'),
 ('audio-x-generic','audio','audio-mpeg audio-ogg audio-flac audio-x-wav'),
 ('video-x-generic','video','video-mp4 video-webm video-x-matroska'),
 ('application-x-archive','archive','application-zip application-x-7z-compressed application-x-tar application-gzip application-x-compressed-tar application-x-rar'),
 ('x-office-document','text','application-vnd.oasis.opendocument.text application-msword application-vnd.openxmlformats-officedocument.wordprocessingml.document'),
 ('x-office-spreadsheet','table','application-vnd.oasis.opendocument.spreadsheet application-vnd.ms-excel application-vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
 ('x-office-presentation','slides','application-vnd.oasis.opendocument.presentation application-vnd.ms-powerpoint')):
    add('mimetypes',canonical,'paper',variant,aliases)
add('mimetypes','application-x-executable','app','generic',aliases='application-x-desktop application-x-sharedlib')

# Devices.
add('devices','computer','monitor',aliases='video-display')
add('devices','drive-harddisk','drive',aliases='drive-harddisk-system drive-harddisk-solidstate')
add('devices','drive-optical','drive','optical',aliases='media-optical media-optical-audio')
add('devices','drive-removable-media','drive','usb',aliases='drive-removable-media-usb drive-harddisk-usb media-flash')
add('devices','printer','printer',aliases='printer-network')

# Application identities: modern names are aliases, not invented historical SGI apps.
for canonical,variant,aliases in (
 ('utilities-terminal','terminal','org.kde.konsole konsole xterm org.wezfurlong.wezterm Alacritty kitty'),
 ('system-file-manager','files','org.kde.dolphin dolphin org.kde.krusader'),
 ('accessories-text-editor','editor','org.kde.kate kate org.kde.kwrite kwrite'),
 ('internet-web-browser','browser','firefox firefox-esr org.mozilla.firefox chromium chromium-browser google-chrome com.google.Chrome'),
 ('internet-mail','mail','org.kde.kmail kmail thunderbird org.mozilla.Thunderbird'),
 ('preferences-system','settings','systemsettings org.kde.systemsettings preferences-desktop'),
 ('utilities-system-monitor','monitor','org.kde.plasma-systemmonitor plasma-systemmonitor org.kde.ksysguard ksysguard'),
 ('accessories-calculator','calculator','org.kde.kcalc kcalc'),
 ('accessories-clock','clock','org.kde.kclock'),
 ('accessories-archiver','archive','org.kde.ark ark'),
 ('image-viewer','image','org.kde.gwenview gwenview'),
 ('help-browser','help','org.kde.khelpcenter khelpcenter'),
 ('database','database','dbeaver io.dbeaver.DBeaverCommunity'),
 ('multimedia-volume-control','sound','pavucontrol org.kde.kmix kmix'),
 ('multimedia-video-player','video','vlc org.videolan.VLC mpv'),
 ('applications-development','code','org.kde.kdevelop kdevelop code code-oss com.visualstudio.code'),
 ('applications-office','office','libreoffice-startcenter'),
 ('office-calendar','calendar','org.kde.korganizer korganizer'),
 ('system-software-install','package','org.kde.discover plasma-discover'),
 ('applications-graphics','paint','org.kde.krita krita gimp org.gimp.GIMP'),
 ('applets-screenshooter','camera','org.kde.spectacle spectacle')):
    add('apps',canonical,'app',variant,aliases)
add('categories','applications-internet','app','browser')
add('categories','applications-multimedia','app','video')
add('categories','applications-system','app','settings')
add('categories','applications-utilities','app','calculator')
add('categories','applications-other','app','generic')
add('categories','start-here','app','computer',aliases='kde plasma menu-kde')

# Toolbar actions. Symbolic names are deliberately inherited from Breeze.
for canonical,variant,aliases in (
 ('go-previous','left','back'),('go-next','right','forward'),('go-up','up',''),('go-down','down',''),
 ('document-new','new',''),('document-open','open',''),('document-save','save','document-save-as'),
 ('document-print','print',''),('edit-copy','copy',''),('edit-cut','cut',''),('edit-paste','paste',''),
 ('edit-find','search','system-search'),('view-refresh','refresh','reload'),('edit-undo','undo',''),('edit-redo','redo',''),
 ('window-close','error','dialog-close tab-close'),('dialog-cancel','error','process-stop'),
 ('dialog-ok','check','dialog-apply'),('list-add','plus','add'),('list-remove','minus','remove'),
 ('folder-new','folder-new',''),('view-list-icons','grid','view-grid'),('view-list-details','list',''),
 ('view-split-left-right','split','view-right-new'),('view-hidden','hidden',''),('application-menu','menu',''),
 ('media-playback-start','play',''),('media-playback-pause','pause',''),('media-playback-stop','stop',''),
 ('media-record','record',''),('media-skip-forward','skip-forward',''),('media-skip-backward','skip-backward',''),
 ('system-lock-screen','lock',''),('system-log-out','logout',''),('system-shutdown','shutdown',''),('system-reboot','refresh','')):
    add('actions',canonical,'action',variant,aliases)

for canonical,variant,aliases in (
 ('dialog-warning','warning',''),('dialog-error','error',''),('dialog-information','information',''),
 ('dialog-question','question',''),('task-complete','success',''),
 ('audio-volume-muted','volume-muted',''),('audio-volume-low','volume-low',''),
 ('audio-volume-medium','volume-medium',''),('audio-volume-high','volume-high',''),
 ('network-wired','network-online','network-idle'),('network-offline','network-offline','network-wired-disconnected')):
    add('status',canonical,'status',variant,aliases)
for level in (0,20,40,60,80,100):
    for charging in (False,True):
        variant=f'battery-{level}'+('-charging' if charging else '')
        aliases={0:'battery-empty',20:'battery-low',60:'battery-good',100:'battery-full'}.get(level,'') if not charging else ('battery-full-charging' if level==100 else '')
        add('status',variant,'status',variant,aliases)
for name,variant,aliases in (
 ('emblem-symbolic-link','link','link_overlay emblem-link'),('emblem-readonly','lock','lock_overlay'),
 ('emblem-favorite','star',''),('emblem-important','error',''),('emblem-default','check','')):
    add('emblems',name,'mark',variant,aliases)


def draw(item: dict) -> str:
    kind=item['kind'];v=item['variant']
    if kind=='folder':return folder('' if v=='open' else v, v=='open')
    if kind=='paper':return paper(v)
    if kind=='trash':return trash(v=='full')
    if kind=='monitor':return monitor()
    if kind=='drive':return drive(v or 'harddisk')
    if kind=='printer':return printer()
    if kind=='app':return app(v)
    if kind=='action':return action(v)
    if kind=='status':return status(v)
    if kind=='mark':return group(mark(v),'translate(8 8) scale(2.4)')
    raise ValueError(kind)


def mini(item: dict, size: int) -> str:
    """Simplified small-size silhouettes. Not a downsample of the detailed 64px art.

    Use a simplified 16-unit vector grid, rendered separately at 16/22/24.
    Fine textures are omitted. This is not individually pixel-hinted artwork.
    """
    k=item['kind'];v=item['variant']
    if k=='folder':
        s=poly('1,6 8,2 11,3 11,11 4,15 1,13',MID,w=.75)+poly('3,7 12,3 14,11 4,15',PAPER,w=.75)
        if v and v!='open':s+=group(mark(v),'matrix(.32 -.12 .025 .32 6 7)')
        if v=='open':s+=poly('4,9 15,4 13,12 4,15',LIGHT,w=.75)
    elif k=='paper':
        s=poly('2,5 8,2 8,12 2,15',MID,w=.65)+poly('4,5 12,1 12,12 4,16',PAPER,w=.65)
        s+=group(mark(v),'matrix(.32 -.13 0 .36 5.7 6)')
    elif k in ('app','monitor'):
        s=poly('1,12 9,8 15,11 7,15',LIGHT,w=.7) if k=='app' else ''
        av=v if k=='app' else 'computer'
        if av in ('terminal','computer','monitor'):
            s+=poly('2,4 10,1 14,4 6,7',LIGHT,w=.65)+poly('2,4 6,7 6,12 2,10',DARK,w=.65)
            s+=poly('6,7 14,4 14,10 6,14',PAPER,w=.65)+poly('7,8 13,5.8 13,9.5 7,12', '#27313b', 'none')
            s+=path('M8 8.3L9.4 8.8L8 10.4M10 10.2L12 9.4',stroke=LIGHT,w=.6)
        elif av=='files':s+=group(poly('1,6 9,2 13,4 13,10 4,14 1,12',MID,w=.8)+poly('4,8 14,3 15,9 5,14',PAPER,w=.8),'translate(0 -1) scale(.9)')
        elif av=='browser':s+=circle(8,6.5,5,BLUE,INK,.8)+path('M8 2Q2 7 8 12M8 2Q14 7 8 12M3 6Q8 10 13 6',stroke=LIGHT,w=.6)
        elif av=='mail':s+=poly('2,6 13,2 13,10 2,14',LIGHT,w=.8)+path('M2 6L7 9L13 2',w=.8)
        elif av in ('editor','office','code'):
            s+=poly('3,4 11,1 11,11 3,14',LIGHT,w=.7)+path('M5 6L9 4.5M5 8L9 6.5M5 10L8 9',w=.7)
            s+=path('M13 2L7 13',stroke=GOLD,w=1.7)
        elif av=='settings':s+=group(wrench(),'translate(2 0) scale(.24)')
        else:
            # The distinctive core symbol is kept, but without duplicate shadow/carpet.
            symbol={'calculator':calculator,'clock':clock,'archive':archive,'help':book,'database':database,'image':image_app,'sound':speaker,'generic':box,'package':box}.get(av)
            if symbol:s+=group(symbol(),'translate(0 -1) scale(.25)')
            elif av=='video':s+=group(mark('video'),'translate(2 2) scale(.6)')
            elif av=='paint':s+=ellipse(8,7,5.5,4.5,PAPER,INK,.8)+circle(5,6,1.3,RED,'none')+circle(9,4,1.3,BLUE,'none')+path('M13 3L8 12',stroke=GOLD,w=1.5)
            elif av=='calendar':s+=rect(3,2,10,10,LIGHT,INK,.8)+rect(3,2,10,3,PURPLE,'none')+path('M5 7H11M5 9H11',w=.7)
            elif av=='camera':s+=rect(2,4,12,7,MID,INK,.8)+circle(9,7.5,3,BLUE,INK,.7)
            else:raise ValueError(av)
    elif k=='trash':
        s=poly('3,5 9,2 14,5 12,12 7,15 4,12',PAPER,w=.75)+poly('3,5 7,8 7,15 4,12',MID,w=.7)+path('M9 8V12M11 7V11',w=.7)
        if v=='full':s+=poly('3,4 8,0.8 11,3 6,6',LIGHT,w=.7)+poly('8,5 9,1 12,3 12,5',LIGHT,w=.7)
        else:s+=poly('2,5 9,1.5 15,4.5 7,8.5',LIGHT,w=.7)
    else:
        # Large action forms are already intentionally simple. Their native
        # bitmap is redrawn from vectors, not resized from another bitmap.
        s=group(draw(item),'scale(.25)')
    # Inset all small drawings: 0.5 logical pixel safeguards outlines at the edge.
    s=group(s,'translate(.35 .25) scale(.94)')
    return svg(s,item['name'],size=size,box=16)


CONTEXTS={'actions':'Actions','apps':'Applications','categories':'Categories','devices':'Devices','emblems':'Emblems','mimetypes':'MimeTypes','places':'Places','status':'Status'}


def index_text(categories: list[str]) -> str:
    dirs=[f'{s}x{s}/{c}' for s in SIZES for c in categories]+[f'scalable/{c}' for c in categories]
    result=(f'[Icon Theme]\nName=IRIX Classic — SGI\nName[pt_BR]=IRIX Classic — SGI\n'
            f'Comment=Original Indigo Magic inspired icons for KDE; version {VERSION}\n'
            'Comment[pt_BR]=Reconstrução independente inspirada no Indigo Magic da SGI\n'
            'Inherits=breeze,hicolor\nExample=system-file-manager\n'
            f'Directories={",".join(dirs)}\n\n')
    for s in SIZES:
        for c in categories:
            result+=f'[{s}x{s}/{c}]\nSize={s}\nType=Fixed\nContext={CONTEXTS[c]}\n\n'
    for c in categories:
        result+=f'[scalable/{c}]\nSize=64\nType=Scalable\nMinSize=16\nMaxSize=512\nContext={CONTEXTS[c]}\n\n'
    # No DesktopDefault/PanelDefault: installing artwork must not dictate UI geometry.
    return result


def make_preview(out: Path, preview: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    preview.mkdir(parents=True,exist_ok=True)
    def font(n:int):
        candidates=('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf')
        for f in candidates:
            if Path(f).exists():return ImageFont.truetype(f,n)
        return ImageFont.load_default()
    cols=9;cw=146;ch=114;head=96
    rows=math.ceil(len(ITEMS)/cols)
    image=Image.new('RGB',(cols*cw,head+rows*ch+44),'#86a4b8')
    d=ImageDraw.Draw(image)
    d.rectangle((0,0,image.width,head),fill='#c1bcaa')
    d.text((24,14),'IRIX CLASSIC / SGI',font=font(28),fill=INK)
    d.text((24,53),f'{VERSION}  •  Ícones reais do pacote a 48 px  •  Reconstrução independente',font=font(16),fill=INK)
    for i,item in enumerate(ITEMS):
        x=(i%cols)*cw;y=head+(i//cols)*ch
        d.line((x,y+ch-1,x+cw,y+ch-1),fill='#7494a9')
        im=Image.open(out/f'48x48/{item["category"]}/{item["name"]}.png').convert('RGBA')
        image.paste(im,(x+(cw-48)//2,y+10),im)
        label=item['name']
        if len(label)>22:
            j=label.rfind('-',0,22)
            lines=[label[:j+1],label[j+1:]] if j>0 else [label[:22],label[22:]]
        else:lines=[label]
        for k,line in enumerate(lines):
            box=d.textbbox((0,0),line,font=font(10));ww=box[2]
            d.text((x+(cw-ww)//2,y+68+k*13),line,font=font(10),fill=INK)
    d.text((24,image.height-30),'SVG editáveis • PNGs nativos • nomes KDE/freedesktop • sem arte proprietária extraída',font=font(13),fill=INK)
    image.save(preview/'catalogo.png')
    # A compact curated preview suitable for viewing in a conversation.
    selected=['folder','user-home','user-trash','user-trash-full','utilities-terminal','internet-web-browser','accessories-text-editor','preferences-system','accessories-calculator','accessories-archiver','text-plain','application-pdf','image-x-generic','drive-harddisk','printer','office-calendar','utilities-system-monitor','database']
    tilew=180;tileh=124;ss=Image.new('RGB',(6*tilew,3*tileh+104),'#86a4b8');dd=ImageDraw.Draw(ss)
    dd.rectangle((0,0,ss.width,85),fill='#c1bcaa')
    dd.text((24,14),'IRIX CLASSIC — SGI',font=font(29),fill=INK)
    dd.text((25,52),'Prévia 0.1.0 • ícones do pacote a 64 px',font=font(15),fill=INK)
    lookup={i['name']:i for i in ITEMS}
    for j,name in enumerate(selected):
        item=lookup[name];x=(j%6)*tilew;y=89+(j//6)*tileh
        im=Image.open(out/f'64x64/{item["category"]}/{name}.png').convert('RGBA');ss.paste(im,(x+58,y+9),im)
        dd.text((x+10,y+82),name,font=font(11),fill=INK)
    ss.save(preview/'previa.png')
    # Native-size, light/dark background samples. No scaled screenshots.
    names=['folder','user-home','user-trash','utilities-terminal','internet-web-browser','text-plain','document-save','go-previous']
    scales=Image.new('RGB',(980,160+len(names)*145),'#dfdcd0');ds=ImageDraw.Draw(scales)
    ds.text((20,17),'TAMANHOS NATIVOS / 100%',font=font(24),fill=INK)
    ds.text((20,52),'Cada imagem usa seu tamanho real. Faixa inferior: fundo escuro.',font=font(14),fill=INK)
    xx=[235,290,350,415,492,591,720,860]
    for x,s in zip(xx,SIZES):ds.text((x,94),str(s)+' px',font=font(12),fill=INK)
    for row,name in enumerate(names):
        item=lookup[name];y=130+row*145
        ds.text((15,y+18),name,font=font(13),fill=INK)
        ds.rectangle((215,y+66,978,y+140),fill='#282c32')
        for x,s in zip(xx,SIZES):
            im=Image.open(out/f'{s}x{s}/{item["category"]}/{name}.png').convert('RGBA')
            # 96/128 need the full height; show them once, crossing the two backgrounds.
            if s>64:scales.paste(im,(x-10,y+6),im)
            else:
                scales.paste(im,(x,y+(64-s)//2),im)
                scales.paste(im,(x,y+72+(64-s)//2),im)
    scales.save(preview/'tamanhos.png')


def build(out: Path, preview: Path | None) -> None:
    if out.exists():raise FileExistsError(f'Destino já existe (não sobrescrito): {out}')
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError('Instale python3-cairosvg para gerar PNGs; o tema pronto não precisa desta dependência.') from exc
    out.mkdir(parents=True)
    categories=sorted({i['category'] for i in ITEMS})
    manifest=[]
    try:
        for item in ITEMS:
            cat=item['category'];name=item['name'];large=svg(draw(item),name)
            dest=out/'scalable'/cat;dest.mkdir(parents=True,exist_ok=True)
            p=dest/(name+'.svg');p.write_text(large,encoding='utf-8')
            for a in item['aliases']:shutil.copyfile(p,dest/(a+'.svg'))
            for size in SIZES:
                dest=out/f'{size}x{size}'/cat;dest.mkdir(parents=True,exist_ok=True)
                body=mini(item,size) if size<=24 else large
                target=dest/(name+'.png')
                cairosvg.svg2png(bytestring=body.encode(),write_to=str(target),output_width=size,output_height=size)
                for a in item['aliases']:shutil.copyfile(target,dest/(a+'.png'))
            manifest.append(item)
        (out/'index.theme').write_text(index_text(categories),encoding='utf-8')
        (out/'manifest.json').write_text(json.dumps({'version':VERSION,'canonical_icons':len(ITEMS),'unique_artworks':len({draw(i) for i in ITEMS}),'icon_names':len(USED),'sizes':SIZES,'icons':manifest},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        (out/'README.txt').write_text('IrixClassic-SGI '+VERSION+'\n\nReconstrução independente inspirada em SGI Indigo Magic.\nNão é um pacote oficial nem uma extração do IRIX.\nMIT: consulte LICENSE.\n\nInstalar esta pasta em ~/.local/share/icons/ e selecionar\nIRIX Classic — SGI nas Configurações do Sistema > Ícones.\nFallback: breeze,hicolor (não incluídos).\nNão altera decoração, cursores, sons, GTK ou Kvantum.\n\nSímbolos não cobertos e nomes -symbolic usam o fallback.\nAplicativos com ícones embutidos/absolutos e miniaturas podem\nnão seguir o tema. Não reproduz automaticamente a animação\nde aplicação em execução (magic carpet) do IRIX.\n',encoding='utf-8')
        license_path=Path(__file__).resolve().parents[1]/'LICENSE'
        if license_path.is_file():shutil.copyfile(license_path,out/'LICENSE')
        if preview:make_preview(out,preview)
    except Exception:
        # Leave incomplete output visible for diagnosis; do not erase anything automatically.
        print(f'Geração incompleta em {out}; examine o erro antes de usar.',file=sys.stderr)
        raise
    print(f'{len(ITEMS)} ícones-base, {len(USED)} nomes, {len(SIZES)} tamanhos PNG + SVG.')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--previews',type=Path)
    args=p.parse_args()
    try:build(args.output,args.previews)
    except (OSError,RuntimeError,ValueError) as exc:p.exit(1,f'Erro: {exc}\n')


if __name__=='__main__':main()
