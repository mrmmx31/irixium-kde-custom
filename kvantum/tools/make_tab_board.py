#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render the exact SVG slice maps as a labelled technical board, not Qt output."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import build_classic as B
import tab_art as T
ROOT=Path(__file__).resolve().parents[1]

def img(mat):
    h,w=len(mat),len(mat[0]);im=Image.new('RGBA',(w,h));im.putdata([(0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,) for row in mat for c in row]);return im

def assemble(atlas,prefix,state,size,metrics):
    w,h=size;l,t,r,b=metrics
    parts={'':(l,t,w-l-r,h-t-b),'top':(l,0,w-l-r,t),'bottom':(l,h-b,w-l-r,b),
           'left':(0,t,l,h-t-b),'right':(w-r,t,r,h-t-b),
           'topleft':(0,0,l,t),'topright':(w-r,0,r,t),'bottomleft':(0,h-b,l,b),'bottomright':(w-r,h-b,r,b)}
    out=Image.new('RGBA',size)
    for part,(x,y,pw,ph) in parts.items():
        if pw<=0 or ph<=0:continue
        key=prefix+'-'+state+('-'+part if part else '')
        tile=img(atlas.items[key]).resize((pw,ph),Image.Resampling.NEAREST)
        out.alpha_composite(tile,(x,y))
    return out

def font(size):
    return ImageFont.truetype('DejaVuSans.ttf',size)

def composition(atlas,old=False,document=False,labels=True):
    im=Image.new('RGBA',(368,113),'#c1c1c1');d=ImageDraw.Draw(im)
    pageprefix='ic-tabframe' if old else 'ic-notebookpage'
    if not document:
        pane=assemble(atlas,pageprefix,'normal',(364,89),(3,3,3,3));im.alpha_composite(pane,(2,24))
    prefix='ic-tab' if old else ('floating-' if document else '')+'ic-notebook'
    metrics=(2,2,2,2) if old else (6,2,6,2)
    pos=(6,114,222);states=('normal','toggled','focused')
    for i in (0,2,1):
        tile=assemble(atlas,prefix,states[i],(112,26),metrics)
        # The selected shape is painted last to illustrate its foreground role.
        im.alpha_composite(tile,(pos[i],0))
        if labels:ImageDraw.Draw(im).text((pos[i]+12,6),('Geral','Detalhes','Avançado')[i],font=font(11),fill='black')
        ci=img(atlas.items['ic-tab-close-normal'] if old else T.close('toggled' if i==1 else 'normal'))
        im.alpha_composite(ci,(pos[i]+96,7))
    if not old and not document:
        # Match the native page-border cut and dedicated junctions.
        x=pos[1];ImageDraw.Draw(im).rectangle((x+6,24,x+105,26),fill=T.FACE)
        im.alpha_composite(img(T.junctions()['top-leftjunct']),(x,24))
        im.alpha_composite(img(T.junctions()['top-rightjunct']),(x+106,24))
    if labels:ImageDraw.Draw(im).text((18,51),'Área do aplicativo',font=font(12),fill='black')
    return im

def main():
    atlas=B.build();board=Image.new('RGB',(1560,1400),'white');d=ImageDraw.Draw(board)
    d.text((32,24),'IrixClassic · abas 0.6.0-rc1',font=font(34),fill='black')
    d.text((32,78),'Primitivas do SVG em composição técnica; não é captura do Qt/Kvantum.',font=font(20),fill='black')
    d.text((32,110),'A forma, as cores e o recobrimento de 4 unidades são adaptações; a seleção em primeiro plano é documentada no ViewKit.',font=font(17),fill='black')
    for x,title,old in ((32,'Antes · base 0.5',True),(808,'Agora · 0.6',False)):
        d.text((x,161),title,font=font(24),fill='black')
        sample=composition(atlas,old=old).resize((736,226),Image.Resampling.NEAREST)
        board.paste(sample,(x,207),sample)
    d.text((32,457),'Documentos / QTabBar independente',font=font(24),fill='black')
    c=composition(atlas,document=True).resize((736,226),Image.Resampling.NEAREST);board.paste(c,(32,500),c)
    d.text((808,457),'Fechar · grade 12 × 12, ampliada 6×',font=font(24),fill='black')
    for i,(state,label) in enumerate((('normal','Repouso'),('toggled','Aba ativa'),('toggledPressed','Pressão'),('disabled','Desativado'))):
        x=820+i*174
        cell=Image.new('RGBA',(16,16),T.FACE);cell.alpha_composite(img(T.close(state)),(2,2));cell=cell.resize((96,96),Image.Resampling.NEAREST)
        board.paste(cell,(x,518),cell);d.text((x,628),label,font=font(17),fill='black')
    d.text((808,674),'Aba ativa não significa botão de fechar pressionado.',font=font(19),fill='black')
    d.text((32,764),'Geometria das quatro orientações · sem texto do aplicativo',font=font(24),fill='black')
    src=composition(atlas,labels=False)
    transforms=(None,Image.Transpose.FLIP_TOP_BOTTOM,Image.Transpose.ROTATE_90,Image.Transpose.ROTATE_270)
    # Smaller samples retain integer-pixel expansion; vertical crops show tabs and page rim only.
    for i,(label,tr) in enumerate(zip(('Superior','Inferior','Esquerda','Direita'),transforms)):
        x=(32,428,824,1140)[i];d.text((x,815),label,font=font(21),fill='black')
        im=src if tr is None else src.transpose(tr)
        if i<2:
            board.paste(im,(x,860),im)
        else:
            board.paste(im,(x,854),im)
    d.text((32,1295),'Rótulos ilustrativos. Altura final depende da fonte e do aplicativo. Qt conserva foco, seleção, fechamento e transbordamento.',font=font(18),fill='black')
    d.text((32,1330),'Não implementa o menu de abas colapsadas do ViewKit; esse comportamento exige código do aplicativo, além do QStyle.',font=font(18),fill='black')
    target=ROOT/'IrixClassic/PREVIA-ABAS.png';board.save(target);print(target)
if __name__=='__main__':main()
