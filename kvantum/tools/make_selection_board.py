#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Technical map comparison; does not impersonate a Qt runtime screenshot."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import build_classic as B
import selection_art as A

def main():
    target=Path(__file__).resolve().parents[1]/'IrixClassic/PREVIA-SELECAO.png'
    font=ImageFont.truetype('DejaVuSans.ttf',20)
    titlefont=ImageFont.truetype('DejaVuSans.ttf',30)
    small=ImageFont.truetype('DejaVuSans.ttf',16)
    sheet=Image.new('RGB',(1420,1080),'white');d=ImageDraw.Draw(sheet)
    d.text((30,24),'IrixClassic 0.4.0-rc1 — caixas de seleção e botões de opção',font=titlefont,fill='black')
    d.text((30,72),'Mapas do SVG em 8× sem interpolação. Não é uma captura do Qt/Kvantum.',font=font,fill='black')
    cols=[('Base 0.3','old'),('Novo: repouso','rest'),('Novo: ponteiro','hover'),('Indisponível¹','disabled')]
    for i,(title,_) in enumerate(cols):d.text((400+i*245,126),title,font=font,fill='black')
    def image(mat):
        im=Image.new('RGBA',(len(mat[0]),len(mat)),(0,0,0,0))
        im.putdata([(0,0,0,0) if c is None else tuple(bytes.fromhex(c[1:]))+(255,) for r in mat for c in r])
        return im
    for j,(name,kind,state,legacy) in enumerate((
        ('Checkbox desmarcado','check','off','unchecked'),('Checkbox marcado','check','on','checked'),
        ('Checkbox parcial²','check','mixed','tristate'),('Radio desmarcado','radio','off','unchecked'),
        ('Radio marcado','radio','on','checked'))):
        y=178+j*158;d.text((30,y+46),name,font=font,fill='black')
        for i,(_,key) in enumerate(cols):
            m=B.check(kind,legacy,'normal') if key=='old' else A.indicator(kind,state,key=='hover')
            im=image(m)
            bg=Image.new('RGBA',im.size,'#c1c1c1')
            if key=='disabled':
                im.putalpha(im.getchannel('A').point(lambda x:round(x*.7)))
            bg.alpha_composite(im)
            bg=bg.resize((120,120),Image.Resampling.NEAREST)
            sheet.paste(bg,(416+i*245,y))
            # Native-sized sample alongside enlarged drawing.
            native=image(m);nb=Image.new('RGBA',native.size,'#c1c1c1');nb.alpha_composite(native)
            if key!='disabled':sheet.paste(nb,(547+i*245,y+98))
    d.text((30,988),'¹ Simulação do tratamento de opacidade 0.7 sobre #C1C1C1. O plugin real precisa de teste local.',font=small,fill='black')
    d.text((30,1018),'² Estado parcial é adaptação ao Qt. SGI documenta a marca vermelha e o triângulo azul; a grade 15×15 é nova.',font=small,fill='black')
    d.text((30,1046),'Normal e hover não prometem um estado pressionado separado: Kvantum 1.1.4 não o seleciona para esses indicadores.',font=small,fill='black')
    sheet.save(target);print(target.name)
if __name__=='__main__':main()
