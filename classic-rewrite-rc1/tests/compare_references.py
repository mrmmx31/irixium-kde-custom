#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere o desenho contra os PNGs originais fornecidos; requer Node.js e Pillow."""
import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]

def render(width, height):
    data=json.loads(subprocess.check_output(['node', str(ROOT/'tests/render.js'),
                                            str(width), str(height)], text=True))
    image=Image.new('RGBA',(width,height))
    draw=ImageDraw.Draw(image)
    for x,y,w,h,color in data['rectangles']:
        if w>0 and h>0:draw.rectangle((x,y,x+w-1,y+h-1),fill=color)
    return image

def compare(image, expected, title_only=False):
    total=different=0
    w,h=expected.size
    for y in range(h):
        for x in range(w):
            if 10<=y<29 and 36<=x<w-64:continue  # omit caption glyphs
            if not title_only and not(y<32 or y>=h-8 or x<8 or x>=w-8):continue
            total+=1
            if image.getpixel((x,y))!=expected.getpixel((x,y))+(255,):different+=1
    return {'pixels_conferidos':total,'divergencias':different}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--irix1',required=True,type=Path,help='referência de 1280×1024')
    parser.add_argument('--irix2',required=True,type=Path,help='referência de 1024×768')
    args=parser.parse_args()
    a=Image.open(args.irix1).convert('RGB');b=Image.open(args.irix2).convert('RGB')
    if a.size!=(1280,1024) or b.size!=(1024,768):
        raise SystemExit('Usa os PNGs originais, sem redimensionar. As coordenadas são específicas dessas referências.')
    results=[compare(render(591,540),a.crop((568,468,1159,1008))),
             compare(render(628,540),b.crop((24,380,652,412)),True)]
    print(json.dumps({'metodo':'rasterização do Artwork.js, não Qt/KWin', 'resultados':results},ensure_ascii=False,indent=2))
    return int(any(r['divergencias'] for r in results))
if __name__=='__main__':raise SystemExit(main())
