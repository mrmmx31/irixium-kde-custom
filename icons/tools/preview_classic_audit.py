#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Show actual generated artwork, including states and newly covered names."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def preview(theme, output):
    m=json.loads((theme/'manifest.json').read_text())
    lookup={n:i['category'] for i in m['icons'] for n in [i['name'],*i['aliases']]}
    rows=[
        ('Estados distintos: bateria / entrada de audio / notificacoes',
         ['battery-empty','battery-missing','microphone-sensitivity-muted','microphone-sensitivity-high','audio-volume-muted','audio-volume-high','notifications','notification-disabled']),
        ('Rede: quatro niveis de sinal e estados separados',
         ['network-wireless-connected-00','network-wireless-connected-25','network-wireless-connected-50','network-wireless-connected-75','network-wireless-connected-100','network-wireless-disconnected','bluetooth-active','bluetooth-disabled']),
        ('Aplicacoes e configuracoes: perspectiva SGI e tapete',
         ['accessories-dictionary','idea','12AD_wordicon.0','sgi-app-spreadsheet','preferences-system-network-connection','config-users','user-info','xfwm4']),
        ('Arquivos: papeis, simbolos por familia e nomes MIME cobertos',
         ['application-arj','application-excel','application-mspowerpoint','application-pkcs10','application-ereader','application-gpx+xml','application-java-archive','application-oebps-package+xml']),
        ('Estados da bandeja: variantes simbolicas com a paleta SGI',
         ['battery-missing-symbolic','microphone-sensitivity-high-symbolic','network-wireless-connected-25-symbolic','network-wireless-connected-50-symbolic','network-wireless-connected-75-symbolic','network-wireless-connected-100-symbolic','notifications-symbolic','notification-disabled-symbolic'])]
    canvas=Image.new('RGB',(1440,1120),'#86a4b8');d=ImageDraw.Draw(canvas)
    def font(size):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
    d.rectangle((0,0,1440,86),fill='#c1bcaa')
    d.text((20,12),'IRIX CLASSIC / COBERTURA DA AUDITORIA',fill='#20201e',font=font(25))
    d.text((20,48),'Novos desenhos vetoriais; PNGs reais a 16, 32 e 64. Simbolicos mostrados sobre fundo claro.',fill='#20201e',font=font(15))
    for row,(title,names) in enumerate(rows):
        y=105+row*200
        d.text((15,y),title,fill='#20201e',font=font(17))
        for col,name in enumerate(names):
            x=col*180
            d.rectangle((x+8,y+36,x+170,y+126),fill='#dfdcd0')
            for size,offset in ((16,15),(32,43),(64,92)):
                im=Image.open(theme/f'{size}x{size}'/lookup[name]/(name+'.png')).convert('RGBA')
                canvas.paste(im,(x+offset,y+48+(64-size)//2),im)
            words=[name[i:i+23] for i in range(0,len(name),23)]
            for index,word in enumerate(words):d.text((x+10,y+134+index*14),word,font=font(10),fill='#20201e')
    canvas.save(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--theme',type=Path,default=Path(__file__).resolve().parents[1]/'themes/IrixClassic-SGI')
    p.add_argument('--saida',type=Path,required=True)
    a=p.parse_args();preview(a.theme,a.saida)
