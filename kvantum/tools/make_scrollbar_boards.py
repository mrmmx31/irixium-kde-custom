#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate precise-map comparison boards; needs Pillow, not a Kvantum runtime."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont,ImageColor
import scrollbar_art as S

ROOT=Path(__file__).resolve().parent.parent

def image(pixels, background='#999999'):
    im=Image.new('RGB',(len(pixels[0]),len(pixels)),background)
    im.putdata([ImageColor.getrgb(p or background) for row in pixels for p in row]);return im

def font(size):
    # Font is resolved locally for labels only; never bundled in the repository.
    try: return ImageFont.truetype('DejaVuSans.ttf',size)
    except OSError: return ImageFont.load_default()

def paste(board, pixels, x,y,scale):
    im=image(pixels);board.paste(im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST),(x,y))

def thumb(state,h=70):
    # Mirrors the Kvantum disabled path: normal panel at 0.7, disabled grip.
    panel=S.thumb('normal' if state=='disabled' else state,h)
    start=(h-S.GRIP_HEIGHT)//2
    for y,row in enumerate(S.grip(state)):
        for x,c in enumerate(row):
            if c is not None: panel[start+y][x]=c
    if state=='disabled':
        def blend(hexcolor):
            rgb=tuple(int(hexcolor[i:i+2],16) for i in (1,3,5))
            return '#%02x%02x%02x'%tuple(round(v*.7+153*.3) for v in rgb)
        panel=[[blend(c) for c in row] for row in panel]
    return panel

def main():
    data=json.loads((ROOT/'tests/data/scrollbar-baseline.json').read_text())
    prev=data['previous_art'];ref=data['reference']
    out=ROOT/'IrixClassic'
    b=Image.new('RGB',(1400,950),'white');d=ImageDraw.Draw(b)
    d.text((30,20),'IrixClassic — rolagem revisada / 0.1.0-rc2',font=font(30),fill='black')
    d.text((30,65),'Comparação das grades: referência IRIX, rc1 e rc2. Sem suavização adicional.',font=font(18),fill='black')
    d.text((30,93),'Composições técnicas de mapas/SVG, não capturas do plugin Kvantum.',font=font(18),fill='black')
    for i,title in enumerate(('IRIX — referência','IrixClassic — rc1','IrixClassic — rc2')):
        d.text((205+i*390,150),title,font=font(22),fill='black')
    d.text((30,229),'Seta ↑',font=font(22),fill='black')
    oldmask=[[p if p=='#4c4c4c' else '#999999' for p in r[6:13]] for r in prev['up'][8:12]]
    newmask=[[S.DARK if S.UP_GLYPH[y][x]=='1' else S.FACE for x in range(8)] for y in range(9)]
    for i,(pix,caption) in enumerate(((ref['glyph_up'],'8 × 9'),(oldmask,'7 × 4'),(newmask,'8 × 9'))):
        paste(b,pix,260+i*390,205,17);d.text((245+i*390,376),caption+' pixels',font=font(21),fill='black')
    d.text((30,460),'Ranhuras',font=font(22),fill='black')
    strip=S.thumb('normal')[5];new=[strip[:] for _ in range(10)]
    for y,row in enumerate(S.grip('normal')):
        for x,c in enumerate(row):
            if c is not None:new[y][x]=c
    for i,(pix,caption) in enumerate(((ref['grip_composited'],'Passo 4 px · claro / preto'),(prev['grip'],'Passo 2 px · escuro / claro'),(new,'Passo 4 px · claro / preto'))):
        paste(b,pix,235+i*390,440,12);d.text((205+i*390,590),caption,font=font(18),fill='black')
    d.text((30,690),'Perfil lateral',font=font(18),fill='black')
    for i,pix in enumerate((ref['thumb_profile'],[prev['thumb'][5]],[S.thumb('normal')[5]])):
        strip=image(pix).resize((18*12,72),Image.Resampling.NEAREST);b.paste(strip,(235+i*390,662))
    d.text((30,790),'A largura da barra continua 18. O indicador novo cruza as faixas laterais sem reduzir a área clicável.',font=font(18),fill='black')
    d.text((30,827),'Referência: Confidence Tests, PNG fornecido. ↓/←/→ e estados não mostrados são adaptações documentadas.',font=font(18),fill='black')
    d.text((30,865),'As alturas totais dos puxadores variam conforme pageStep/intervalo. Compare desenho, não comprimento.',font=font(18),fill='black')
    b.save(out/'PREVIA-ROLAGEM.png')
    b=Image.new('RGB',(1360,1090),'white');d=ImageDraw.Draw(b)
    d.text((30,20),'Estados da barra de rolagem / IrixClassic rc2',font=font(30),fill='black')
    d.text((30,65),'6×, sem interpolação. Modelo das primitivas — não execução de Qt/Kvantum.',font=font(19),fill='black')
    for col,(state,title) in enumerate((('normal','Repouso'),('focused','Ponteiro'),('pressed','Pressão'),('disabled','Desativado'))):
        x=85+col*320
        d.text((x,123),title,font=font(23),fill='black')
        pixels=S.arrow(state,'up')+thumb(state,60)+S.arrow(state,'down')
        paste(b,pixels,x+40,172,6)
        # Horizontal is a transposition, preserving the lighting axes.
        horizontal=S.transpose(S.arrow(state,'up')+thumb(state,36)+S.arrow(state,'down'))
        paste(b,horizontal,x-20,807,3)
    d.text((30,949),'Desativado: aproximação do caminho de opacidade 0,7 do Kvantum para o puxador, sobre cinza #999999.',font=font(18),fill='black')
    d.text((30,985),'A galeria prever-rolagem.sh testa setas, arraste, teclado, extremos, RTL e intervalo zero com o plugin real.',font=font(18),fill='black')
    d.text((30,1021),'Outros controles e decorações de janela preservados. Plano completo em PLANO-IRIXCLASSIC.md.',font=font(18),fill='black')
    d.text((30,1051),'Cada coluna mostra o estado de cada peça; não representa pressão simultânea nos três alvos.',font=font(17),fill='black')
    b.save(out/'ESTADOS-ROLAGEM.png')

if __name__=='__main__':main()
