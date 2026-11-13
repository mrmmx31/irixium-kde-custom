#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply the generated GTK4 recipe to real gallery scrollbars on caller Xvfb."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'tools/theme-lab'))
sys.path.insert(0,str(root/'tools/theme-lab/tests'))
import backend
from gtk4_scrollbar_snapshot import generate_snapshot
from test_backend import model


parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True,
                    help='Persistent receipt/capture directory outside the private project scratch')
args=parser.parse_args()
assert os.environ.get('T07_PRIVATE_PROBE')=='1'
assert os.environ.get('DISPLAY','').startswith(':')
output=args.output.absolute()
output.mkdir(parents=True,exist_ok=False,mode=0o700)
os.chmod(output,0o700)
palette_source=root/'colors/DomainOS-SR10.4.colors'
proposal=model(); proposal['selected_family']='gtk4'
project_digest=backend.sha(json.dumps(proposal,sort_keys=True,separators=(',',':')).encode())
with tempfile.TemporaryDirectory(prefix='.qa-i168-gtk4-scrollbar-',dir=root) as scratch:
    snapshot=Path(scratch)/'snapshot'
    generated=generate_snapshot(root,snapshot,proposal,project_digest,palette_source)
    capture=output/'gtk4-scrollbars.xwd'
    command=['/usr/bin/python3','-B',str(root/'tools/theme-lab/tests/probe_gtk4_gallery_hints.py'),
             '--scrollbar-css',generated['css'],'--scrollbar-class',generated['style_class'],
             '--capture',str(capture)]
    child=subprocess.run(command,env=dict(os.environ,T07_PRIVATE_PROBE='1',PYTHONDONTWRITEBYTECODE='1'),
                         capture_output=True,text=True,timeout=50)
    if child.returncode:
        raise SystemExit('Native GTK4 probe failed: '+child.stderr+'\n'+child.stdout)
    native=json.loads(child.stdout)
    png=output/'gtk4-scrollbars.png'
    convert=subprocess.run(['magick',str(capture),str(png)],capture_output=True,text=True,timeout=15)
    if convert.returncode:
        raise SystemExit('XWD conversion failed: '+convert.stderr)
    inputs=[root/'tools/theme-lab/gtk4_scrollbars.py',
            root/'tools/theme-lab/gtk4_scrollbar_snapshot.py',
            root/'plasma/tests/galerias-nativas/gtk4_demo.py',
            root/'tools/theme-lab/tests/probe_gtk4_gallery_hints.py']
    result={'status':'passed','item':'I168','gtk_version':native['native_gallery']['version'],
            'theme_in_gallery':native['native_gallery']['theme'],
            'selected_palette':generated['selected_scheme'],
            'recipe':{key:generated[key] for key in ('geometry','states','native_nodes','arrows','translated_controls')},
            'runtime':native['native_gallery']['scrollbar_css_proof'],
            'capability':native['native_gallery']['hintCoverage']['internal']['scrollbar_contract'],
            'capture':{'xwd':str(capture),'xwd_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),
                       'png':str(png),'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest()},
            'source_hashes':{str(path.relative_to(root)):backend.sha(backend.read_file(path)) for path in inputs},
            'limits':['CSS provider parsed and was applied to real GtkScrollbar nodes.',
                      'Cross-axis allocations were measured at 15 logical px.',
                      'Only visible gallery state was rendered; no pixel comparison or state-complete claim.',
                      'GTK gallery theme was Default; selected KDE scheme drove private generated assets.',
                      'No personal profile, installation, Xephyr or MAME session changed.']}
    result_path=output/'RESULTADO-I168-GTK4-SCROLLBAR.json'
    result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
