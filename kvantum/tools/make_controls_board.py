#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Technical composition of generated SVG maps. Not a native Qt screenshot."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import build_classic as B
import range_art as R
from make_tab_board import assemble, img
ROOT=Path(__file__).resolve().parents[1]


def font(size):return ImageFont.truetype('DejaVuSans.ttf',size)

def main():
    atlas=B.build();board=Image.new('RGB',(1540,1610),'white');d=ImageDraw.Draw(board)
    def text(x,y,t,size=20):d.text((x,y),t,font=font(size),fill='black')
    def paste(im,x,y,scale=1):
        if scale!=1:im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        board.paste(im,(x,y),im)
    def panel(prefix,state,size,n):return assemble(atlas,prefix,state,size,(n,n,n,n))
    text(32,24,'IrixClassic · bloco 7 · 0.7.0-rc1',36)
    text(32,78,'Mapas do SVG em composição técnica — não é captura do Qt/Kvantum.',23)
    text(32,114,'Geometria adaptada à família IRIX. Texto ilustrativo; ampliações inteiras sem suavização.',19)
    text(32,170,'Slider / scale · antes e agora',25)
    def slider(old=False,state='normal'):
        im=Image.new('RGBA',(248,52),R.FACE)
        track=panel('ic-groove' if old else 'ic-range-track','normal',(14,232),2).transpose(Image.Transpose.TRANSPOSE)
        im.alpha_composite(track,(8,21))
        if not old:
            filled=panel('ic-range-track','toggled',(14,116),2).transpose(Image.Transpose.TRANSPOSE)
            im.alpha_composite(filled,(8,21))
        # Same vertical-master transform used for this orientation by the engine.
        handle=panel('ic-slidercursor' if old else 'ic-range-thumb',state,(26,16),2).transpose(Image.Transpose.TRANSPOSE)
        im.alpha_composite(handle,(116,15))
        mark=atlas.items['ic-slidergrip-'+state] if old else R.grip(state)
        im.alpha_composite(img(mark).resize((10,10),Image.Resampling.NEAREST).transpose(Image.Transpose.TRANSPOSE),(119,23))
        return im
    # Old IDs are determined from the frozen pre-block configuration.
    for x,label,old in ((32,'Anterior · 0.6',True),(532,'Novo · repouso',False),(1032,'Novo · pressão',False)):
        text(x,213,label,21);paste(slider(old,'pressed' if x==1032 else 'normal'),x,252,2)
    text(1032,365,'Cursor pressionado',18);text(1270,365,'≠ item selecionado',18)
    text(32,402,'Progresso · preenchimento dentro da moldura, 0 / 50 / 100%',25)
    def progress(value):
        im=panel('ic-meter-track','normal',(230,18),2)
        if value>0:
            width=max(1,round(226*value/100))
            if width>=5:im.alpha_composite(panel('ic-meter-fill','normal',(width,14),2),(2,2))
        return im
    for i,value in enumerate((0,50,100)):
        x=32+i*504;text(x,447,str(value)+'%',21);paste(progress(value),x,486,2)
    text(32,551,'Intervalo e movimento indeterminado são do Qt; a prancha só mostra preenchimentos estáticos.',18)
    text(32,614,'Cabeçalhos · repouso / apontado / pressionado',25)
    for i,(state,label) in enumerate((('normal','Nome'),('focused','Tamanho'),('pressed','Estado'))):
        tile=panel('ic-column-panel',state,(158,29),3)
        ImageDraw.Draw(tile).text((10,7),label,font=font(12),fill='black')
        tile.alpha_composite(img(R.triangle('up',state,12)),(138,8));paste(tile,32+i*500,662,3)
    text(32,785,'Linhas de dados · sem pintar o fundo normal do aplicativo',25)
    listing=Image.new('RGBA',(420,116),'#efefef');ld=ImageDraw.Draw(listing)
    for i,(state,label) in enumerate((('normal','Repouso: fundo da vista'),('focused','Ponteiro: realce de localização'),('pressed','Selecionado com foco'),('toggled','Selecionado sem foco'))):
        listing.alpha_composite(img(R.row(state,416,26)),(2,2+i*28))
        ld.text((10,8+i*28),label,font=font(12),fill='black')
    paste(listing,32,835,2)
    text(935,835,'Árvore · fechada / aberta',22)
    for i,direction in enumerate(('right','down')):
        cell=Image.new('RGBA',(17,17),'#efefef');cell.alpha_composite(img(R.triangle(direction)),(4,4));paste(cell,935+i*180,875,6)
    text(935,996,'Expansor 9 × 9, ampliado 6×.',18)
    text(32,1111,'Divisor, agrupamento, dica e componentes Qt',25)
    split=panel('ic-divider-panel','normal',(7,74),1)
    split.alpha_composite(img(R.grip('normal',5,10)),(1,32));paste(split,36,1160,3)
    text(80,1180,'Divisor 7',19);text(80,1210,'Borda 1 + 5 + 1',17)
    group=Image.new('RGBA',(224,80),R.FACE);group.alpha_composite(panel('ic-section-frame','normal',(224,80),3))
    ImageDraw.Draw(group).text((18,26),'Conteúdo não coberto',font=font(13),fill='black');paste(group,280,1160,2)
    tip=panel('ic-hint-panel','normal',(204,28),2);ImageDraw.Draw(tip).text((8,7),'Dica opaca, sem sombra externa',font=font(11),fill='black')
    paste(tip,785,1160,2)
    text(785,1241,'Dial e tamanho da janela · adaptações',19)
    di=img(R.dial());di.alpha_composite(img(R.dial('notches')));di.alpha_composite(img(R.dial('handle')),(11,5));paste(di,790,1280,3)
    paste(img(R.resize_grip()),925,1310,4)
    text(1050,1284,'MDI é subjanela interna,',18);text(1050,1312,'não decoração do KWin.',18)
    for i,kind in enumerate(('minimize','maximize','close')):
        cell=Image.new('RGBA',(18,18),'#a39f83');cell.alpha_composite(img(R.mdi_symbol(kind)),(3,3));paste(cell,1060+i*74,1350,3)
    text(32,1452,'Valores, seleção, foco, teclado, arraste e indisponibilidade são conferidos pela galeria nativa, separadamente.',18)
    text(32,1486,'Toolbox conserva o desenho calculado pelo motor. Dial tem marcas decorativas, não uma escala numérica calibrada.',18)
    text(32,1520,'Setas de rolagem: desenhos anteriores preservados; falha nas telas KDE continua registrada como pendente.',18)
    target=ROOT/'IrixClassic/PREVIA-CONTROLES.png';board.save(target);print(target)

if __name__=='__main__':main()
