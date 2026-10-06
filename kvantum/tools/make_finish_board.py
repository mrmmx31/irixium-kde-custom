#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare actual before/after SVG maps. This is NOT a Qt screenshot."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import build_classic as B
import entry_art as E
import finish_art as F


def font(size):
    for name in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(name).is_file(): return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def image(rows, background='#c1c1c1'):
    im=Image.new('RGB',(len(rows[0]),len(rows)),background)
    for y,row in enumerate(rows):
        for x,c in enumerate(row):
            if c: im.putpixel((x,y),tuple(bytes.fromhex(c[1:])))
    return im


def main():
    sheet=Image.new('RGB',(1480,1180),'white');d=ImageDraw.Draw(sheet)
    d.text((30,25),'IrixClassic — acabamento 0.7.1-rc1',font=font(32),fill='black')
    d.text((30,76),'Mapas do SVG ampliados por vizinho mais próximo. Não é captura Qt/Kvantum.',font=font(19),fill='black')
    d.text((30,108),'A seta da barra de rolagem aprovada NÃO faz parte desta alteração.',font=font(19),fill='black')
    d.text((385,163),'Antes · 0.7.0-rc1',font=font(24),fill='black')
    d.text((925,163),'Depois · 0.7.1-rc1',font=font(24),fill='black')
    atlas=B.build();old=atlas.items['ic-toolbar-separator'];new=F.toolbar_separator()
    for x,pixels in ((420,old),(970,new)):
        # Canonical target rectangle in a horizontal toolbar, then zoom x7.
        target=image(pixels).resize((10,30),Image.Resampling.NEAREST)
        sheet.paste(target.resize((70,210),Image.Resampling.NEAREST),(x,225))
    d.multiline_text((30,250),'Toolbar horizontal\nDivisória vertical\n\nDestino 10 × 30 · 7×',font=font(21),fill='black',spacing=12)
    d.text((385,460),'Duas faixas horizontais esticadas',font=font(17),fill='black')
    d.text((925,460),'Duas colunas centrais; folgas iguais',font=font(17),fill='black')
    for x,pixels in ((385,old),(925,new)):
        target=image(pixels).resize((10,30),Image.Resampling.NEAREST).transpose(Image.Transpose.TRANSPOSE)
        sheet.paste(target.resize((210,70),Image.Resampling.NEAREST),(x,545))
    d.multiline_text((30,540),'Toolbar vertical\nDivisória horizontal\nDestino 30 × 10 · 7×',font=font(21),fill='black',spacing=9)
    d.text((30,674),'Spinbox: só os símbolos foram ampliados; botões e campo conservam suas medidas.',font=font(20),fill='black')
    states=(('normal','Repouso'),('pressed','Pressão'),('disabled','Indisponível'))
    for origin,func in ((385,E.spin_marker),(925,F.spin_marker)):
        for i,(state,label) in enumerate(states):
            x=origin+150*i
            rows=func(state,'up')
            sheet.paste(image(rows,'#999999').resize((96,96),Image.Resampling.NEAREST),(x,744))
            d.text((x,852),label,font=font(16),fill='black')
        d.text((origin,904),'Máscara '+('5 × 4' if origin==385 else '7 × 6')+' · célula 12 × 12 · 8×',font=font(19),fill='black')
    d.multiline_text((30,998),
        'Preservados: rolagem, botões, campos, seleção, menus, abas e demais controles.\n'
        'Altura dos menus e limitação de cor de somente leitura: sem alteração nesta candidata.\n'
        'Estados de pressão/indisponibilidade são adaptações; conferir no aplicativo com o plugin real.',
        font=font(19),fill='black',spacing=14)
    path=Path(__file__).resolve().parents[1]/'IrixClassic/PREVIA-ACABAMENTO.png'
    sheet.save(path);print(path.name)

if __name__=='__main__': main()
