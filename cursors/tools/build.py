#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build three portable SGI cursor variants from the reviewed source payload.

Only writes under cursors/<known theme>. Pillow is needed for rebuilding,
not for installing or using the committed Xcursor binaries.
"""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw
from xcursor import read, write
from contours import render, premultiply

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'sources/sgi-enhanced'
SIZES = (24, 32, 48, 64, 96)
THEMES = {'sgi': 'SGI Enhanced', 'SGI-Classic': 'SGI Classic', 'SGI-Irixium': 'SGI Irixium'}
# CSS/Wayland and Qt/X11 name compatibility. Canonical artwork remains separate
# for wait vs progress and for vertical vs horizontal split/resize.
ALIASES = {
    'up-arrow': 'sb_up_arrow', 'default': 'left_ptr', 'arrow': 'left_ptr', 'top_left_arrow': 'left_ptr',
    'wait': 'watch', 'busy': 'watch', 'clock': 'watch',
    'progress': 'left_ptr_watch', 'half-busy': 'left_ptr_watch',
    '3ecb610c1bf2410f44200f48c40d3599': 'left_ptr_watch',
    '00000000000000020006000e7e9ffc3f': 'left_ptr_watch',
    '08e8e1c95fe2fc01f976f1e063a24ccd': 'left_ptr_watch',
    'pointer': 'hand1', 'pointing_hand': 'hand1', 'hand': 'hand1',
    'text': 'xterm', 'ibeam': 'xterm', 'vertical-text': 'vertical_text',
    'help': 'question_arrow', 'whats_this': 'question_arrow', 'context-menu': 'question_arrow',
    'all-scroll': 'fleur', 'all_scroll': 'fleur', 'all-resize': 'fleur',
    'grab': 'openhand', 'grabbing': 'closedhand',
    '9141b49c8149039304290b508d208c40': 'openhand',
    '05e88622050804100c20044008402080': 'closedhand',
    'ns-resize': 'sb_v_double_arrow', 'ew-resize': 'sb_h_double_arrow',
    'nesw-resize': 'fd_double_arrow', 'nwse-resize': 'bd_double_arrow',
    'n-resize': 'sb_v_double_arrow', 's-resize': 'sb_v_double_arrow',
    'e-resize': 'sb_h_double_arrow', 'w-resize': 'sb_h_double_arrow',
    'ne-resize': 'fd_double_arrow', 'nw-resize': 'bd_double_arrow',
    'se-resize': 'bd_double_arrow', 'sw-resize': 'fd_double_arrow',
    'sw_resize': 'fd_double_arrow',
    '028006030e0e7ebffc7f7070c0600140': 'sb_h_double_arrow',
    'fcf1c3c7cd4491d801f1e1c78f100000': 'fd_double_arrow',
    'c7088f0f3e6c8088236ef8e1e3e70000': 'bd_double_arrow',
    'col-resize': 'sb_h_double_arrow', 'row-resize': 'sb_v_double_arrow',
    'split_h': 'sb_h_double_arrow', 'split_v': 'sb_v_double_arrow',
    '14fef782d02440884392942c11205230': 'sb_h_double_arrow',
    '2870a09082c103050810ffdffffe0204': 'sb_v_double_arrow',
    'cell': 'plus', 'alias': 'dnd-link', 'link': 'dnd-link',
    '3085a0e285430894940527032f8b26df': 'dnd-link',
    '640fb0e74195791501fd1ed57b41487f': 'dnd-link',
    'a2a266d0498c3104214a47bd64ab0fc8': 'dnd-link',
    'no-drop': 'X_cursor', 'not-allowed': 'X_cursor', 'forbidden': 'X_cursor',
    'dnd-no-drop': 'X_cursor', 'dnd-none': 'left_ptr',
}


def image(frame):
    return Image.frombytes('RGBA', (frame['width'], frame['height']), frame['pixels'], 'raw', 'BGRA')


def frame(im, size, hotspot, delay=50):
    return {'size': size, 'width': im.width, 'height': im.height,
            'hotspot': hotspot, 'delay': delay, 'pixels': im.tobytes('raw', 'BGRA')}


def scaled(im, hotspot, size, theme='sgi'):
    factor = size/32
    dimensions = (round(im.width*factor), round(im.height*factor))
    if theme == 'sgi' or (theme == 'SGI-Classic' and size == 32):
        result = im.resize(dimensions, Image.Resampling.NEAREST)
    else:
        result = render(im, size, smooth=theme=='SGI-Irixium')
    return result, tuple(round(v*factor) for v in hotspot)


def arrow(size, smooth):
    """Continuous red/white outline fitted to the reference arrow silhouette."""
    im = Image.new('RGBA',(size*4,size*4))
    d = ScaledDraw(im,size/8)
    d.polygon([(4,5),(14,14),(10.8,14.8),(13.4,20),(10.7,21),(8.2,16),(4,18.8)],fill='white')
    d.polygon([(5,7),(12,13),(9.2,13.8),(12,19.2),(11.2,19.6),(8.4,14.4),(5,17)],fill='red')
    im = im.resize((size,size),Image.Resampling.LANCZOS if smooth else Image.Resampling.BOX)
    if not smooth:
        im.putdata([(255,255 if g>=128 else 0,255 if b>=128 else 0,255) if a>=128 else (0,0,0,0)
                    for r,g,b,a in im.getdata()])
    return im


class ScaledDraw:
    """Render procedural primitives directly at their final sampling resolution."""
    def __init__(self, im, scale):
        self.draw = ImageDraw.Draw(im)
        self.scale = scale

    def __getattr__(self, name):
        def draw(points, **kwargs):
            if isinstance(points[0], (tuple, list)):
                points = [tuple(round(v*self.scale) for v in p) for p in points]
            else:
                points = tuple(round(v*self.scale) for v in points)
            if 'width' in kwargs:
                kwargs['width'] = max(1, round(kwargs['width']*self.scale))
            return getattr(self.draw, name)(points, **kwargs)
        return draw


def clock(phase, modern=False, scale=1):
    im = Image.new('RGBA', (round(32*scale), round(32*scale)))
    d = ScaledDraw(im, scale)
    red, white = '#ff0000', '#ffffff'
    d.rectangle((13, 3, 18, 28), fill=white)
    d.rectangle((14, 4, 17, 27), fill=red)
    d.ellipse((6, 6, 25, 25), fill=white)
    d.ellipse((7, 7, 24, 24), fill=red)
    d.ellipse((9, 9, 22, 22), fill=white)
    for angle in range(0, 360, 90):
        a = math.radians(angle)
        x, y = round(15.5 + 5*math.sin(a)), round(15.5 - 5*math.cos(a))
        d.rectangle((x, y, x+0.6, y+0.6), fill=red)
    a = phase*math.pi/4
    d.line((16, 16, round(16 + 5*math.sin(a)), round(16 - 5*math.cos(a))), fill=red, width=1)
    d.line((16, 16, 13, 17), fill=red, width=1)
    if modern:
        # Modern adaptation: outer ring with a rotating red marker and no strap.
        d.rectangle((13, 0, 18, 5), fill=(0, 0, 0, 0))
        d.rectangle((13, 26, 18, 31), fill=(0, 0, 0, 0))
        x, y = round(16 + 9*math.sin(a)), round(16 - 9*math.cos(a))
        d.rectangle((x-1, y-1, x+1, y+1), fill=white)
        d.rectangle((x, y, x+0.6, y+0.6), fill=red)
    return im


def hand(closed):
    im = Image.new('RGBA', (32, 32))
    d = ImageDraw.Draw(im)
    points = ([(8, 11), (11, 8), (21, 8), (24, 12), (22, 23), (12, 23), (7, 17)] if closed
              else [(7, 17), (6, 12), (9, 11), (11, 15), (11, 6), (14, 6), (14, 13),
                    (15, 4), (18, 4), (18, 13), (19, 6), (22, 6), (21, 15),
                    (23, 10), (26, 11), (23, 23), (13, 23)])
    d.polygon(points, fill='#ff0000')
    d.line(points+[points[0]], fill='white', width=1)
    if closed:
        for x in (12, 16, 20): d.line((x, 9, x, 13), fill='white')
        d.line((9, 15, 17, 15), fill='white')
        d.line((17, 15, 19, 19), fill='white')
    return im


def build():
    original = json.loads((ROOT/'sources/aliases-original.json').read_text())
    hashes = json.loads((ROOT/'sources/manifest.json').read_text())
    for name, digest in hashes.items():
        if hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Fonte alterada: '+name)
    bases = {p.name: read(p)[0] for p in SOURCE.iterdir() if p.is_file()}
    aliases = {**original, **ALIASES}
    aliases.pop('closedhand', None)
    aliases.pop('openhand', None)
    for theme, display in THEMES.items():
        folder = ROOT/theme
        payload = folder/'cursors'
        payload.mkdir(parents=True, exist_ok=True)
        # This is a deterministic rebuild of a known source tree, never a user install.
        for p in payload.iterdir():
            if p.is_file() or p.is_symlink():
                p.unlink()
        names = set(bases) | {'openhand', 'closedhand', 'vertical_text', 'zoom-in', 'zoom-out'}
        for name in sorted(names - aliases.keys()):
            frames = []
            for size in SIZES:
                phases = range(8) if name in ('watch', 'left_ptr_watch') and theme != 'sgi' else range(1)
                for phase in phases:
                    hotspot = bases.get(name, bases['left_ptr'])['hotspot']
                    if name in ('watch', 'left_ptr_watch'):
                        if theme == 'sgi':
                            im = image(bases['watch'])
                            hotspot = bases['watch']['hotspot']
                            if name == 'left_ptr_watch':
                                busy = im.crop(im.getbbox()).resize((12, 14), Image.Resampling.NEAREST)
                                im = image(bases['left_ptr'])
                                im.alpha_composite(busy, (17, 15))
                                hotspot = bases['left_ptr']['hotspot']
                        else:
                            im = clock(phase, modern=theme=='SGI-Irixium')
                            hotspot = (16, 16)
                            if name == 'left_ptr_watch':
                                busy = im.resize((16, 16), Image.Resampling.NEAREST)
                                im = image(bases['left_ptr'])
                                im.alpha_composite(busy, (15, 14))
                                hotspot = bases['left_ptr']['hotspot']
                    elif name in ('openhand', 'closedhand'):
                        im = hand(name=='closedhand'); hotspot = (16, 14)
                    elif name == 'vertical_text':
                        base = bases['xterm']; im = image(base).transpose(Image.Transpose.ROTATE_90)
                        x, y = base['hotspot']; hotspot = (y, im.height-1-x)
                    elif name in ('zoom-in', 'zoom-out'):
                        im = Image.new('RGBA', (32, 32)); d = ImageDraw.Draw(im)
                        d.line((19, 19, 26, 26), fill='white', width=5)
                        d.line((19, 19, 26, 26), fill='red', width=3)
                        d.ellipse((5, 5, 22, 22), fill='white', outline='red', width=2)
                        d.line((9, 14, 18, 14), fill='red', width=2)
                        if name=='zoom-in': d.line((14, 9, 14, 18), fill='red', width=2)
                        hotspot = (14, 14)
                    else:
                        im = image(bases[name])
                    im, hotspot = scaled(im, hotspot, size, theme)
                    if name=='left_ptr' and theme!='sgi' and not (theme=='SGI-Classic' and size==32):
                        im = arrow(size, smooth=theme=='SGI-Irixium')
                    if name in ('watch', 'left_ptr_watch') and theme != 'sgi' and not (theme=='SGI-Classic' and size==32):
                        # Ellipses and hands are drawn anew; no magnified clock bitmap.
                        scale = size/32*4
                        busy = clock(phase, modern=theme=='SGI-Irixium', scale=scale if name=='watch' else scale/2)
                        if name=='left_ptr_watch':
                            im = arrow(size*4, smooth=False)
                            im.alpha_composite(busy, (round(15*scale),round(14*scale)))
                        else:
                            im = busy
                        im = im.resize((size,size), Image.Resampling.LANCZOS if theme=='SGI-Irixium' else Image.Resampling.BOX)
                        if theme=='SGI-Classic':
                            im.putdata([(255,255 if g>=128 else 0,255 if b>=128 else 0,255) if a>=128 else (0,0,0,0)
                                        for r,g,b,a in im.getdata()])
                    if theme=='SGI-Irixium':
                        im = premultiply(im)
                    frames.append(frame(im, size, hotspot, 125 if len(phases)>1 else 50))
            write(payload/name, frames)
        for name, target in sorted(aliases.items()):
            (payload/name).symlink_to(target)
        for p in payload.iterdir():
            if not p.exists(): raise ValueError('Alias ausente: '+str(p))
        (folder/'index.theme').write_text('[Icon Theme]\nName='+display+'\nComment=SGI/IRIX cursor adaptation for KDE\nExample=left_ptr\n')
        (folder/'cursor.theme').write_text('[Icon Theme]\nInherits='+theme+'\n')
        manifest = {p.name: ('link:'+p.readlink().as_posix() if p.is_symlink()
                           else hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(payload.iterdir())}
        (folder/'MANIFEST.json').write_text(json.dumps({'format':1,'sizes':SIZES,'cursors':manifest},indent=2)+'\n')


if __name__ == '__main__':
    build()
