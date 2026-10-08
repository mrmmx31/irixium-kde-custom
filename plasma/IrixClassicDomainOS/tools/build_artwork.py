#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build DomainOS resources without modifying the independent Classic option.

The frame contract comes from the existing GPL theme. Panel, instrument,
Iconbox, command rail, pager, clock and field art are new integer-pixel SVG.
No screenshot bitmap is copied into the product.
"""
import sys

# These maintainer helpers live inside a catalogued theme component. Running
# them must not add interpreter caches to its installed/source inventory.
sys.dont_write_bytecode = True

from pathlib import Path
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parents[1]
BASE = HERE.parent / 'IrixClassic'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

PALETTE = {
    'face': '#7894a7', 'well': '#607f91', 'rim': '#263f4d',
    'shadow': '#405c6c', 'highlight': '#bed0d4', 'pale': '#a2d0e7',
    'blue': '#3296c4', 'white': '#ecffff', 'text': '#102b37',
    'weave': '#6a889a', 'weave_light': '#82a1b0', 'active': '#dddd28',
}
COLOR_MAP = {
    '#c1c1c1': PALETTE['face'], '#cecec6': PALETTE['face'],
    '#bdbcb4': PALETTE['face'], '#b0b0a8': PALETTE['well'],
    '#41413b': PALETTE['rim'], '#344f4f': PALETTE['rim'],
    '#77776f': PALETTE['shadow'], '#77776b': PALETTE['shadow'],
    '#637f7f': PALETTE['shadow'], '#55554f': PALETTE['shadow'],
    '#9b9b91': PALETTE['weave'], '#aaa9a2': PALETTE['weave'],
    '#f4f4e9': PALETTE['highlight'], '#dfdfd3': PALETTE['pale'],
    '#9ebfbf': PALETTE['well'], '#abcaca': PALETTE['pale'],
    '#789c9c': PALETTE['weave'], '#789292': PALETTE['weave'],
    '#bfd3d0': PALETTE['highlight'], '#cce0dc': PALETTE['pale'],
    '#cdb981': '#b98976', '#d6c58e': '#c49a87', '#89aaaa': PALETTE['well'],
    '#b98e8e': PALETTE['well'], '#e4dddd': PALETTE['highlight'],
    '#dadada': PALETTE['pale'], '#ececec': PALETTE['highlight'],
    '#919191': PALETTE['weave'], '#606060': PALETTE['shadow'],
    '#696969': PALETTE['shadow'], '#2f2f2f': PALETTE['rim'],
    '#ededed': PALETTE['highlight'], '#8caaa9': PALETTE['well'],
    '#adadad': PALETTE['face'], '#d6d6d6': PALETTE['pale'],
    '#828282': PALETTE['shadow'], '#85a4c3': PALETTE['blue'],
    '#bed6ef': PALETTE['pale'], '#6a849a': PALETTE['shadow'],
}


def node(tag, **attrs):
    return ET.Element('{'+NS+'}'+tag, {k.replace('_', '-'): str(v) for k, v in attrs.items()})


def rect(parent, x, y, w, h, color, **attrs):
    parent.append(node('rect', x=x, y=y, width=w, height=h, fill=color, **attrs))


def svg(title, width=256, height=256):
    result = node('svg', width=width, height=height, viewBox=f'0 0 {width} {height}', shape_rendering='crispEdges')
    ET.SubElement(result, '{'+NS+'}title').text = 'Irix Classic DomainOS — '+title
    return result


def write(name, result):
    target = HERE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(result, space='  ')
    target.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                      '<!-- SPDX-FileCopyrightText: 2026 IRIX Classic contributors -->\n'
                      '<!-- SPDX-License-Identifier: GPL-3.0-or-later -->\n'
                      + ET.tostring(result, encoding='unicode')+'\n')


def hint(parent, identifier, width=1, height=1):
    rect(parent, 0, 0, width, height, '#ff00ff', id=identifier, opacity=0)


def texture(group, width, height, mode):
    # Explicit pixels work in both QSvgRenderer and KSvg. There is no gradient
    # or alpha blending: the weave and grooves have fixed discrete shades.
    if mode == 'weave':
        for y in range(0, height, 4):
            for x in range(0, width, 4):
                for shift, color in [(0, 'highlight'), (1, 'weave_light'), (2, 'rim'), (3, 'shadow')]:
                    if x+shift < width and y+shift < height:
                        rect(group, x+shift, y+shift, 1, 1, PALETTE[color])
    elif mode == 'rules':
        grooves=('#a5bdcf',PALETTE['face'],'#536f84','#b3c9d9','#6c88a0',PALETTE['shadow'])
        for y in range(height):
            rect(group, 0, y, width, 1, grooves[y%len(grooves)])


def plate(parent, prefix, ox, oy, margin=4, face=None, pressed=False, mode=None, empty=False, active=False):
    """One native nine-slice with straight four-pixel stepped light edges."""
    face = face or PALETTE['face']
    size = 24
    top = [PALETTE['rim'], PALETTE['highlight'], PALETTE['pale'], face]
    bottom = [face, PALETTE['weave'], PALETTE['shadow'], PALETTE['rim']]
    if pressed:
        top = [PALETTE['rim'], PALETTE['shadow'], PALETTE['weave'], face]
        bottom = [face, PALETTE['pale'], PALETTE['highlight'], PALETTE['rim']]
    top, bottom = top[:margin], bottom[-margin:]
    if active:
        top[0] = bottom[-1] = PALETTE['active']
    label = lambda suffix: prefix+'-'+suffix if prefix else suffix
    # All pieces tile/stretch independently; no transparent holes in housings.
    for piece, x, y, w, h in [
        ('center', margin, margin, size, size),
        ('top', margin, 0, size, margin),
        ('bottom', margin, size+margin, size, margin),
        ('left', 0, margin, margin, size),
        ('right', size+margin, margin, margin, size),
        ('topleft', 0, 0, margin, margin),
        ('topright', size+margin, 0, margin, margin),
        ('bottomleft', 0, size+margin, margin, margin),
        ('bottomright', size+margin, size+margin, margin, margin),
    ]:
        group = node('g', id=label(piece), transform=f'translate({ox+x},{oy+y})')
        parent.append(group)
        if piece == 'center':
            # Pager frames are an overlay; only the underlying panel is opaque.
            rect(group, 0, 0, w, h, 'none' if empty else face)
            if mode and not empty:
                texture(group, w, h, mode)
            continue
        for py in range(h):
            for px in range(w):
                if piece == 'top': color = top[py]
                elif piece == 'bottom': color = bottom[py]
                elif piece == 'left': color = top[px]
                elif piece == 'right': color = bottom[px]
                elif piece == 'topleft': color = top[min(px, py)]
                elif piece == 'topright': color = top[py] if py < margin-1-px else bottom[px]
                elif piece == 'bottomleft': color = top[px] if px < margin-1-py else bottom[py]
                else: color = bottom[max(px, py)]
                rect(group, px, py, 1, 1, color)
    for side in ('top', 'bottom', 'left', 'right'):
        hint(parent, label('hint-'+side+'-margin'), margin, margin)
    if mode:
        hint(parent, label('hint-tile-center'))


def major_art():
    for name, prefix, pressed, face, mode in [
        ('panel-background', '', False, 'face', 'weave'),
        ('background', '', True, 'well', None),
        ('instrument-well', '', True, 'well', 'weave'),
        ('frame', 'plain', True, 'well', 'weave'),
        ('command-rail', '', False, 'face', 'rules'),
    ]:
        result = svg(name+' opaque plate', 48, 48)
        plate(result, prefix, 4, 4, face=PALETTE[face], pressed=pressed, mode=mode)
        write('widgets/'+name+'.svg', result)
    for name in ('instrument', 'button'):
        result = svg(name+' straight raised/pressed rim', 400, 64)
        states = ('normal', 'pressed') if name == 'instrument' else ('normal', 'hover', 'pressed', 'focus-background', 'toolbutton-hover', 'toolbutton-pressed', 'focus', 'toolbutton-focus')
        for index, state in enumerate(states):
            plate(result, state, 4+index*48, 4, pressed='pressed' in state,
                  mode='weave' if name == 'instrument' else None,
                  active=state in ('focus', 'toolbutton-focus'))
        write('widgets/'+name+'.svg', result)
    result = svg('recessed iconbox and ruled heading', 96, 96)
    plate(result, '', 4, 4, face=PALETTE['well'], pressed=True, mode='weave')
    plate(result, 'heading', 48, 4, face=PALETTE['face'], mode='rules')
    write('widgets/iconbox.svg', result)
    result = svg('pager overlay with narrow yellow selection rim', 256, 64)
    for index, state in enumerate(('normal', 'active', 'hover', 'active-hover', 'pressed')):
        plate(result, state, 4+index*48, 4, face=PALETTE['well'], pressed=True,
              empty=True, active='active' in state)
    write('widgets/pager.svg', result)
    for filename, variants in [('lineedit', ('base', 'focus')), ('plasmoidheading', ('header', 'footer'))]:
        result = svg(filename+' rigid field', 160, 64)
        for index, state in enumerate(variants):
            plate(result, state, 4+index*48, 4, face=PALETTE['well'], pressed=filename=='lineedit', active=state=='focus')
        if filename == 'lineedit':
            hint(result, 'hint-focus-over-base')
            hint(result, 'hint-compose-over-borders')
        write('widgets/'+filename+'.svg', result)
    for name in ('dialogs/background.svg', 'widgets/tooltip.svg'):
        result = svg('opaque popup plate', 48, 48)
        plate(result, '', 4, 4)
        write(name, result)


def clock():
    result = svg('blue diagnostic clock face and white hands', 256, 128)
    result.attrib.pop('shape-rendering')  # A circular dial, as in the reference.
    face = node('g', id='ClockFace'); result.append(face)
    face.append(node('circle', cx=32, cy=32, r=32, fill=PALETTE['blue']))
    for hour in range(12):
        rect(face, 31, 2, 2, 3 if hour % 3 == 0 else 2, PALETTE['white'], transform=f'rotate({hour*30} 32 32)')
    for identifier, x, w, h in [('HourHand',80,8,26), ('MinuteHand',104,6,32), ('SecondHand',128,4,34)]:
        hand = node('g', id=identifier, transform=f'translate({x},0)'); result.append(hand)
        middle=w//2
        hand.append(node('path', d=f'M0 0H{w}V4H{middle+1}V{h-4}L{middle} {h}L{middle-1} {h-4}V4H0Z', fill=PALETTE['white']))
        shadow=node('g',id=identifier+'Shadow',transform=f'translate({x},48)'); result.append(shadow)
        rect(shadow,0,0,w,h,'none')
        rect(result,x+middle-.5,3.5,1,1,'#ff00ff',id='hint-'+identifier.lower()+'-rotation-center-offset')
        rect(result,x+middle-.5,51.5,1,1,'#ff00ff',id='hint-'+identifier.lower()+'shadow-rotation-center-offset')
    screw=node('g',id='HandCenterScrew',transform='translate(152,0)'); result.append(screw)
    screw.append(node('circle',cx=3,cy=3,r=3,fill=PALETTE['white']))
    glass=node('g',id='Glass',transform='translate(176,0)'); result.append(glass)
    rect(glass,0,0,64,64,'none')
    hint(result,'hint-square-clock')
    write('widgets/clock.svg',result)


def derivative(source):
    """Retain existing resource IDs while replacing incompatible rendering."""
    result=ET.parse(source).getroot()
    gradients={}
    for element in result.iter():
        if element.tag.rsplit('}',1)[-1] in ('linearGradient','radialGradient'):
            stop=next((child for child in element.iter() if child.tag.rsplit('}',1)[-1]=='stop'),None)
            if stop is not None:
                match=re.search(r'stop-color:([^;]+)',stop.attrib.get('style',''))
                gradients[element.attrib['id']]=match.group(1) if match else stop.attrib.get('stop-color',PALETTE['shadow'])
    for parent in result.iter():
        for element in list(parent):
            if element.tag.rsplit('}',1)[-1] in ('linearGradient','radialGradient','filter','namedview','metadata') or element.tag.startswith('{http://www.inkscape.org'):
                parent.remove(element)
    for element in result.iter():
        for key,value in list(element.attrib.items()):
            if key.startswith('{http://www.inkscape.org') or key.startswith('{http://sodipodi.sourceforge.net'):
                del element.attrib[key];continue
            value=re.sub(r'url\(#([^)]*)\)',lambda m:gradients.get(m.group(1),m.group(0)),value)
            value=re.sub(r'#[0-9a-fA-F]{6}',lambda m: COLOR_MAP.get(m.group(0).lower(),m.group(0)),value)
            if key=='style':
                props=dict(part.split(':',1) for part in value.split(';') if ':' in part)
                for opacity in ('opacity','fill-opacity','stroke-opacity'):
                    if opacity in props and float(props[opacity]) not in (0,1): props[opacity]='1'
                props.pop('filter',None)
                props['stroke-linejoin']='miter'; props['stroke-linecap']='square'
                value=';'.join(k+':'+v for k,v in props.items())
            if key in ('opacity','fill-opacity','stroke-opacity') and float(value) not in (0,1): value='1'
            if key in ('rx','ry'):value='0'
            element.attrib[key]=value
    # Shadows remain a contract placeholder without being drawn, and hints
    # have no visible role. Pager centers are handled by their own overlay art.
    for element in result.iter():
        identifier=element.attrib.get('id','')
        if identifier.endswith('-shadow'):
            element.attrib['opacity']='0'
    result.attrib['shape-rendering']='crispEdges'
    ET.indent(result,space='  ')
    target=HERE/source.relative_to(BASE);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                      '<!-- DomainOS derivative of the IrixClassic/Irixium GPL resource. See ORIGEM.json and LICENSE. -->\n'
                      +ET.tostring(result,encoding='unicode')+'\n')


def build():
    baseline={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BASE.rglob('*')) if p.is_file()}
    for source in sorted(BASE.rglob('*.svg')): derivative(source)
    shutil.copyfile(BASE/'LICENSE',HERE/'LICENSE')
    shutil.copyfile(BASE/'LICENSE-switch.txt',HERE/'LICENSE-switch.txt')
    major_art();clock()
    (HERE/'CLASSIC-BASELINE.json').write_text(json.dumps(baseline,indent=2)+'\n')
    provenance=HERE/'ORIGEM.json'
    if provenance.exists():
        origin=json.loads(provenance.read_text())
        for name, info in origin['resources'].items():
            info['sha256']=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        provenance.write_text(json.dumps(origin,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'files':len(list(HERE.rglob('*.svg'))),'original_classic_unchanged':baseline=={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BASE.rglob('*')) if p.is_file()}},indent=2))


if __name__=='__main__':build()
