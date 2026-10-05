#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render technical artwork boards; this is not a native Qt capture."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import button_art as A
import scrollbar_art as S
import build_classic as B


def font(n):
    for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
        if Path(path).is_file():return ImageFont.truetype(path,n)
    return ImageFont.load_default()

def image(pixels,background='#c1c1c1'):
    im=Image.new('RGB',(len(pixels[0]),len(pixels)),background)
    im.putdata([tuple(int((c or background)[j:j+2],16) for j in (1,3,5)) for row in pixels for c in row])
    return im

def apply_ring(pixels):
    p=[r[:] for r in pixels];ring=A.default_ring(len(p[0]),len(p))
    for y,row in enumerate(ring):
        for x,c in enumerate(row):
            if c:p[y][x]=c
    return p

def main():
    out=Path(__file__).resolve().parents[1]/'IrixClassic'
    sheet=Image.new('RGB',(1740,1630),'white');d=ImageDraw.Draw(sheet)
    d.text((30,22),'IrixClassic 0.2.0-rc1 — pressão e botões',font=font(34),fill='black')
    d.text((30,74),'Prévia técnica dos mapas SVG, sem interpolação. Não é captura do Kvantum/Qt.',font=font(22),fill='black')
    d.text((30,128),'SETAS · a célula, o símbolo em repouso e a barra continuam com as medidas da rc2',font=font(23),fill='black')
    for col,label in enumerate(['Repouso · mantido','Pressão rc2','Pressão nova','Indisponível · mantido']):
        d.text((210+col*375,185),label,font=font(23),fill='black')
    for row,direction in enumerate(['up','down','left','right']):
        y=235+row*170;d.text((30,y+45),direction,font=font(22),fill='black')
        new=S.arrow('pressed',direction);old=[r[:] for r in new]
        # Reconstruct the former pressed map: it inverted only the cell.
        for yy in range(2,16):
            for xx in range(2,16):
                if old[yy][xx]==S.LIGHT:old[yy][xx]=S.FACE
        for col,pix in enumerate([S.arrow('normal',direction),old,new,S.arrow('disabled',direction)]):
            im=image(pix);im=im.resize((144,144),Image.Resampling.NEAREST);sheet.paste(im,(270+col*375,y))
    d.text((30,934),'BOTÕES · repouso / ponteiro · pressionado · padrão pressionado · selecionado',font=font(23),fill='black')
    for row,(kind,label) in enumerate([('command','Comando'),('palettebutton','Paleta'),('toolbarbutton','Toolbar')]):
        y=1000+row*156;d.text((30,y+30),label,font=font(23),fill='black')
        normal,_=A.surface(kind,'normal',80,28);pressed,_=A.surface(kind,'pressed',80,28);toggled,_=A.surface(kind,'toggled',80,28)
        variants=[normal,pressed,apply_ring(pressed) if kind=='command' else A.surface(kind,'disabled',80,28)[0],toggled]
        for col,pix in enumerate(variants):
            im=image(pix);q=ImageDraw.Draw(im);q.text((18,8),'Ação',font=font(11),fill='black')
            sheet.paste(im.resize((320,112),Image.Resampling.NEAREST),(200+col*375,y))
    d.text((30,1488),'No padrão, o marcador externo não cobre as duas faixas internas do relevo.',font=font(22),fill='black')
    d.text((30,1524),'Paleta/toolbar: terceira coluna mostra o mapa indisponível; Qt pode aplicar opacidade adicional.',font=font(21),fill='black')
    d.text((30,1562),'Setas: a máscara escura não se move. O novo detalhe claro aparece abaixo/à direita durante a pressão.',font=font(21),fill='black')
    path=out/'PRESSAO-E-BOTOES.png';sheet.save(path);print(path.name)
if __name__=='__main__':main()
