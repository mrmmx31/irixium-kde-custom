#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Create only artificial test data in a new directory, never in existing folders."""
from pathlib import Path
import argparse, struct, zlib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
r=a.saida.expanduser().absolute()
if r.exists():p.error('A pasta precisa ser nova.')
r.mkdir(parents=True);(r/'Pasta com espaços').mkdir();(r/'Outra pasta').mkdir()
(r/'Leia-me.txt').write_text('Dados artificiais do IrixClassic Files.\n\nSelecione para visualizar; abra por ativação explícita.\nA Shelf contém referências, não cópias.\n',encoding='utf-8')
(r/'ação-e-acentuação.txt').write_text('Acentos: ação, informação, seleção.\n'*25,encoding='utf-8')
(r/'HTML-como-texto.html').write_text('<html><body><script>NAO_EXECUTAR()</script></body></html>\n')
(r/'binario-sem-renderizador.bin').write_bytes(bytes(range(256))*4)
w,h=256,160
raw=b''.join(b'\0'+bytes(c for x in range(w) for c in (x,y*255//(h-1),128)) for y in range(h))
def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
(r/'amostra.png').write_bytes(png);print(r)
