#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build original PIA state artwork and a resource-only, process-scoped overlay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
STATES = ('alert', 'down', 'connected', 'disconnecting', 'connecting', 'snoozed')
SETS = ('dark-no-outline-margins', 'light-no-outline-margins', 'colored-no-outline-margins', 'classic-margins')


def artwork(state):
    text=(ROOT/'icons/themes/IrixClassic-SGI/scalable/status/sgi-vpn.svg').read_text()
    colours={'alert':'#b29b55','down':'#a1514e','connected':'#538478',
             'disconnecting':'#b29b55','connecting':'#52748c','snoozed':'#76618d'}
    marks={'alert':'M49 39V49M49 53V54', 'down':'M43 42L55 54M55 42L43 54',
           'connected':'M41 48L47 54L57 42', 'connecting':'M40 48H57M51 42L57 48L51 54',
           'disconnecting':'M41 48H58M47 42L41 48L47 54',
           'snoozed':'M42 42H55L42 54H55'}
    badge=(f'<rect x="36" y="36" width="25" height="25" rx="2" fill="{colours[state]}" '
           'stroke="#20201e" stroke-width="1.4"/>'
           f'<path d="{marks[state]}" fill="none" stroke="#f3f2e9" stroke-width="3" '
           'stroke-linejoin="round" stroke-linecap="square"/>')
    return text.replace('</svg>', badge+'</svg>')


def build(output):
    import cairosvg
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    rcc=shutil.which('rcc') or next((str(p) for p in (
        Path('/usr/lib/qt6/libexec/rcc'),Path('/usr/lib64/qt6/libexec/rcc')) if p.is_file()),None)
    compiler=shutil.which('cc')
    if not rcc or not compiler:raise RuntimeError('Instale o compilador C e o rcc do Qt 6 (qt6-base-dev-tools).')
    if not re.search(r'\b6\.', subprocess.check_output([rcc,'--version'],text=True,stderr=subprocess.STDOUT)):
        raise RuntimeError('Esta integração requer o rcc do Qt 6.')
    qrc=ET.Element('RCC');entries=ET.SubElement(qrc,'qresource',prefix='/img/tray')
    hashes={}
    for state in STATES:
        vector=artwork(state);(output/(state+'.svg')).write_text(vector)
        image=output/(state+'.png')
        cairosvg.svg2png(bytestring=vector.encode(),write_to=str(image),output_width=64,output_height=64)
        os.utime(image,(0,0))  # RCC v2 records file times; keep builds deterministic.
        hashes[state]=hashlib.sha256(image.read_bytes()).hexdigest()
        for icon_set in SETS:
            entry=ET.SubElement(entries,'file',alias=f'square-{icon_set}-{state}.png');entry.text=image.name
    qrc_path=output/'tray.qrc';ET.ElementTree(qrc).write(qrc_path,encoding='unicode')
    generated=output/'resources.cpp'
    subprocess.run([rcc,'--no-compress','--format-version','2','-o',str(generated),str(qrc_path)],check=True)
    arrays=re.findall(r'static const unsigned char qt_resource_(?:data|name|struct)\[\] = \{.*?\n\};',generated.read_text(),re.S)
    if len(arrays)!=3:raise RuntimeError('Formato inesperado do rcc; não foi criada uma biblioteca.')
    (output/'resources.h').write_text('\n'.join(arrays)+'\n')
    subprocess.run([compiler,'-std=c11','-shared','-fPIC','-Wall','-Wextra','-Werror',
                    '-I',str(output),str(Path(__file__).with_name('overlay.c')),
                    '-o',str(output/'libirix-pia-tray.so'),'-ldl','-pthread'],check=True)
    (output/'manifest.json').write_text(json.dumps({'format':1,'states':hashes,'sets':SETS,'paths':24,
         'source':'https://github.com/pia-foss/desktop/blob/master/client/src/linux/nativetrayqt.cpp',
         'license':'MIT','scope':'PIA GUI process only'},indent=2)+'\n')
    print('PIA: seis estados, 24 recursos; biblioteca: '+str(output/'libirix-pia-tray.so'))
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output)
