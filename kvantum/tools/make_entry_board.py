#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Technical composition of the theme maps. Not a Qt/Kvantum screenshot."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import build_classic as B
import entry_art as E

def font(size):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(path).is_file():return ImageFont.truetype(path,size)
    return ImageFont.load_default()
def image(pixels):
    im=Image.new('RGB',(len(pixels[0]),len(pixels)),'#c1c1c1')
    im.putdata([tuple(bytes.fromhex((c or '#c1c1c1')[1:])) for r in pixels for c in r]);return im
def field(kind,state,text,new=True):
    im=image((E.surface(kind,state,230,28) if new else B.surface('entry',state,230,28))[0])
    d=ImageDraw.Draw(im);d.text((8,6),text,font=font(12),fill='black')
    if kind=='option':
        marker=E.option_marker(state) if new else B.arrow(state,'down')
        for y,r in enumerate(marker):
            for x,c in enumerate(r):
                if c:im.putpixel((208+x,8+y),tuple(bytes.fromhex(c[1:])))
    return im

def main():
    sheet=Image.new('RGB',(1400,1060),'white');d=ImageDraw.Draw(sheet)
    d.text((28,24),'IrixClassic 0.3.0-rc1 — campos e entradas',font=font(30),fill='black')
    d.text((28,76),'Composição dos mapas do SVG em 2×. Não é captura do Qt/Kvantum.',font=font(20),fill='black')
    d.text((28,110),'Botões e rolagem aprovados permanecem idênticos. As legendas não fazem parte do tema.',font=font(18),fill='black')
    d.text((265,165),'Base 0.2.0-rc1',font=font(24),fill='black');d.text((850,165),'Campos 0.3.0-rc1',font=font(24),fill='black')
    rows=[('Campo', 'input','normal','Texto editável'),('Foco por teclado','input','focused','Texto com foco'),('Opção fechada','option','normal','Original'),('Opção pressionada','option','pressed','Original')]
    for index,(label,kind,state,text) in enumerate(rows):
        y=225+index*135;d.text((28,y+15),label,font=font(19),fill='black')
        for x,new in ((265,False),(850,True)):
            im=field(kind,state,text,new);sheet.paste(im.resize((460,56),Image.Resampling.NEAREST),(x,y))
    y=770;d.text((28,y+12),'Spin / setas',font=font(19),fill='black')
    for col,state in enumerate(('normal','pressed')):
        x=265+585*col
        im=field('input','normal','24',True)
        for j,dr in enumerate(('down','up')):
            tile=image(E.surface('spin',state,22,28)[0]);glyph=E.spin_marker(state,dr)
            for yy,row in enumerate(glyph):
                for xx,c in enumerate(row):
                    if c:tile.putpixel((5+xx,8+yy),tuple(bytes.fromhex(c[1:])))
            im.paste(tile,(184+22*j,0))
        sheet.paste(im.resize((460,56),Image.Resampling.NEAREST),(x,y))
        d.text((x,y+70),'Novo: '+('repouso' if state=='normal' else 'pressão'),font=font(17),fill='black')
    d.text((28,920),'A cor de somente leitura não é simulada: o Kvantum não possui um estado SVG readonly para LineEdit.',font=font(19),fill='black')
    d.text((28,958),'A aplicação controla seleção, caret, validação, limites, layout e a composição real de combos/spinboxes.',font=font(19),fill='black')
    d.text((28,996),'Marcador horizontal de opção: adaptação Motif/IRIX. Ver docs/CAMPOS.md para fontes e limites.',font=font(19),fill='black')
    path=Path(__file__).resolve().parents[1]/'IrixClassic/PREVIA-CAMPOS.png';sheet.save(path);print(path.name)
if __name__=='__main__':main()
