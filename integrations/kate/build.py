#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a process-scoped override of Kate's embedded Git SVG."""
import argparse,hashlib,json,re,shutil,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RESOURCE='/icons/icons/sc-apps-git.svg'

def build(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rcc=shutil.which('rcc') or '/usr/lib/qt6/libexec/rcc';cc=shutil.which('cc')
    if not cc or not Path(rcc).is_file():raise RuntimeError('Requer compilador C e rcc do Qt 6.')
    if not re.search(r'\b6\.',subprocess.check_output([rcc,'--version'],text=True,stderr=subprocess.STDOUT)):raise RuntimeError('Requer rcc do Qt 6.')
    image=output/'git.svg';image.write_bytes((ROOT/'icons/themes/IrixClassic-SGI/scalable/actions/git.svg').read_bytes());os.utime(image,(0,0))
    qrc=output/'icons.qrc';qrc.write_text('<RCC><qresource prefix="/icons/icons"><file alias="sc-apps-git.svg">git.svg</file></qresource></RCC>')
    generated=output/'resources.cpp';subprocess.run([rcc,'--no-compress','--format-version','2','-o',str(generated),str(qrc)],check=True)
    arrays=re.findall(r'static const unsigned char qt_resource_(?:data|name|struct)\[\] = \{.*?\n\};',generated.read_text(),re.S)
    if len(arrays)!=3:raise RuntimeError('Formato de recursos Qt inesperado.')
    (output/'resources.h').write_text('\n'.join(arrays)+'\n')
    subprocess.run([cc,'-std=c11','-shared','-fPIC','-Wall','-Wextra','-Werror','-I',str(output),str(Path(__file__).with_name('overlay.c')),'-o',str(output/'libirix-kate-icons.so'),'-ldl','-pthread'],check=True)
    (output/'manifest.json').write_text(json.dumps({'format':1,'resource':RESOURCE,'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'scope':'Kate process only','license':'MIT'},indent=2)+'\n')
    return output
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);build(p.parse_args().output)
