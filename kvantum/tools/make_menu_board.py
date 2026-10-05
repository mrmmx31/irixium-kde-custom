#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Technical composition of SVG source maps, NOT a Qt/Kvantum screenshot.

Requires Pillow only. No fonts or reference screenshots are redistributed.
The reference stripe repeats the measured 24px central vertical sample.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import menu_art as M
import build_classic as B
import selection_art as S
ROOT=Path(__file__).resolve().parents[1]

def font(size,italic=False):
    name='DejaVuSans-Oblique.ttf' if italic else 'DejaVuSans.ttf'
    try:return ImageFont.truetype(name,size)
    except OSError:return ImageFont.load_default(size=size)

def image(matrix):
    result=Image.new('RGBA',(len(matrix[0]),len(matrix)))
    result.putdata([(0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,) for r in matrix for c in r])
    return result

def overlay(target,mat,xy):
    target.alpha_composite(image(mat),xy)

def popup(old=False,pressed=False):
    width,height=244,186
    surface=B.surface('menu','normal',width,height)[0] if old else M.surface('menupanel',w=width,h=height)
    result=image(surface);d=ImageDraw.Draw(result);f=font(12,True)
    rows=[('Abrir...', 'Ctrl+O',None),('Salvar indisponível','',None),
          ('Detalhes','',('check','on')),('Formato','',('radio','on')),
          ('Mais opções','',None),('Fechar','',None)]
    for i,(text,shortcut,mark) in enumerate(rows):
        y=4+i*28
        st='pressed' if pressed and i==4 else 'toggled' if i==4 else 'normal'
        if old:
            if st!='normal':overlay(result,B.surface('menuitem',st,width-4,24)[0],(2,y))
        else:overlay(result,M.surface('menurow',st,width-4,24),(2,y))
        if mark:overlay(result,S.indicator(*mark),(8,y+4))
        d=ImageDraw.Draw(result);color='#777777' if i==1 else 'black'
        d.text((28,y+4),text,font=f,fill=color)
        if shortcut:d.text((177,y+4),shortcut,font=f,fill=color)
        if i==4:
            overlay(result,M.direction_indicator('right'),(width-21,y+6))
        if i==1:
            sep=image(M.separator()).resize((width-4,6),Image.Resampling.NEAREST)
            result.alpha_composite(sep,(2,y+24))
    return result

def main():
    board=Image.new('RGB',(1580,1120),'white');d=ImageDraw.Draw(board)
    heading=font(32);body=font(19);small=font(17)
    d.text((32,24),'IrixClassic 0.5.0-rc1 — menus',font=heading,fill='black')
    d.text((32,70),'Mapas usados no SVG. Composição técnica; não é captura do Qt/Kvantum.',font=body,fill='black')
    d.text((32,100),'Ampliação por vizinho mais próximo. Tipografia e layout ilustrativos; controles reais na galeria.',font=small,fill='black')
    d.text((32,155),'Perfil central da barra de menus · 4×',font=font(23),fill='black')
    measured=['#ececec']*2+['#c1c1c1']*20+['#919191','#606060']
    ref=[[c]*100 for c in measured]
    new=M.surface('menustrip',w=110,h=24)
    new=[row[5:105] for row in new]
    for x,label,mat in ((32,'IRIX · perfil medido (coluna repetida)',ref),(575,'Classic · perfil reconstruído',new)):
        d.text((x,195),label,font=small,fill='black')
        strip=image(mat).resize((400,96),Image.Resampling.NEAREST)
        board.paste(strip,(x,225),strip)
    d.text((1060,231),'24 linhas conferidas:',font=small,fill='black')
    d.multiline_text((1060,262),'2 claras · 20 cinzas\n1 intermediária · 1 escura',font=small,fill='black',spacing=8)
    d.text((32,360),'Itens e popups · 2×',font=font(23),fill='black')
    for x,label,old,press in ((32,'Base 0.4 · item apontado',True,False),(548,'0.5 · item apontado / selecionado',False,False),(1064,'0.5 · pressão',False,True)):
        d.text((x,402),label,font=small,fill='black')
        p=popup(old,press).resize((488,372),Image.Resampling.NEAREST)
        board.paste(p,(x,437),p)
    d.text((32,842),'A pressão exige State_Sunken. A seleção do item não marca automaticamente checkbox ou radio.',font=small,fill='black')
    d.text((32,893),'Indicadores próprios · 4×',font=font(23),fill='black')
    for i,direction in enumerate(('left','right','up','down')):
        x=32+i*178
        im=image(M.direction_indicator(direction)).resize((48,48),Image.Resampling.NEAREST)
        board.paste(im,(x,942),im);d.text((x+60,957),direction,font=small,fill='black')
    im=image(M.separator()).resize((240,24),Image.Resampling.NEAREST)
    board.paste(im,(810,948),im);d.text((810,987),'Separador 6 px · duas linhas',font=small,fill='black')
    im=image(M.tearoff()).resize((200,32),Image.Resampling.NEAREST)
    board.paste(im,(1160,942),im);d.text((1160,987),'Tear-off nativo opcional',font=small,fill='black')
    d.text((32,1050),'Preserva a lógica das ações do KWin, os atalhos globais, as fontes e o desenho aprovado da rolagem.',font=small,fill='black')
    d.text((32,1080),'Popups, estados não fotografados e grade de setas são adaptações documentadas; não cópias exatas certificadas.',font=small,fill='black')
    out=ROOT/'IrixClassic/PREVIA-MENUS.png';board.save(out);print(out)
if __name__=='__main__':main()
