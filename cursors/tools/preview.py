#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render a contact sheet from the actual Xcursor pixels, without changing the session."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from xcursor import read

ROOT = Path(__file__).resolve().parents[1]


def display_image(f):
    im=Image.frombytes('RGBA',(f['width'],f['height']),f['pixels'],'raw','BGRA')
    im.putdata([(min(255,round(r*255/a)),min(255,round(g*255/a)),min(255,round(b*255/a)),a)
                if a else (0,0,0,0) for r,g,b,a in im.getdata()])
    return im


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida', type=Path, required=True)
    args=p.parse_args()
    names=['default','wait','progress','pointer','text','grab','grabbing','copy','alias','not-allowed','col-resize','row-resize']
    canvas=Image.new('RGB',(1440,1000),'#d3d2ce');d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    d.text((15,12),'Comparacao a 48: tamanho real acima; lupa 2x abaixo. sgi = ampliacao antiga; Classic / Irixium = contornos novos.',fill='black',font=font)
    for row,theme in enumerate(('sgi','SGI-Classic','SGI-Irixium')):
        top=45+row*200
        d.text((15,top),theme,fill='black',font=font)
        for col,name in enumerate(names):
            x=15+col*118;y=top+25
            f=next(f for f in read(ROOT/theme/'cursors'/name) if f['size']==48)
            im=display_image(f)
            canvas.paste(im,(x+6,y),im)
            enlarged=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
            canvas.paste(enlarged,(x+2,y+52),enlarged)
            d.text((x,top+182),name,fill='black',font=font)
    for row,theme in enumerate(('SGI-Classic','SGI-Irixium')):
        y=665+row*155
        d.text((15,y),theme+': setas reais em 24 / 32 / 48 / 64 / 96, sobre fundos claro e escuro.',fill='black',font=font)
        x=15
        for f in read(ROOT/theme/'cursors/default'):
            im=display_image(f)
            canvas.paste(im,(x,y+25),im)
            d.rectangle((x+650,y+20,x+650+im.width+5,y+25+im.height+5),fill='#303030')
            canvas.paste(im,(x+650,y+25),im)
            d.text((x+im.width+4,y+35),str(f['size']),fill='black',font=font);x+=im.width+55
    canvas.save(args.saida)


if __name__=='__main__': main()
