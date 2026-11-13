# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from test_backend import backend, ROOT, model
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
from gtk2_generation import generate_scrollbar_snapshot
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--yellow', type=Path, required=True)
parser.add_argument('--toggle',action='store_true')
parser.add_argument('--radio',action='store_true')
parser.add_argument('--check',action='store_true')
args = parser.parse_args(); args.output = args.output.absolute()
data = model(); data['selected_family'] = 'gtk2'
recipe = data['recipes']['gtk2']
recipe.update(visible_controls=1 | (1<<10) | (1<<11), selected_control=0,
              positions=[[20,20] for _ in range(16)], sizes=[[0,0] for _ in range(16)])
recipe['sizes'][0]=[180,50]; recipe['positions'][10]=[20,150]; recipe['sizes'][10]=[220,15]
recipe['positions'][11]=[300,20]; recipe['sizes'][11]=[15,180]
if args.toggle:
    recipe['visible_controls'] |= 2
    recipe['positions'][1]=[20,90];recipe['sizes'][1]=[180,50]
    recipe['positions'][10]=[20,200];recipe['positions'][11]=[500,20]
before = copy.deepcopy(data); results=[]
if args.radio:
    recipe['visible_controls']|=8
    recipe['positions'][3]=[260,20];recipe['sizes'][3]=[180,100]
    recipe['positions'][11]=[500,20]
    before=copy.deepcopy(data)
if args.check:
    recipe['visible_controls']|=4
    recipe['positions'][2]=[260,20];recipe['sizes'][2]=[180,50]
    recipe['positions'][11]=[500,20]
    before=copy.deepcopy(data)
sources={'DomainOS':ROOT/'colors/DomainOS-SR10.4.colors',
         'BreezeLight':Path('/usr/share/color-schemes/BreezeLight.colors'),
         'BreezeDark':Path('/usr/share/color-schemes/BreezeDark.colors'), 'TestYellow':args.yellow.resolve()}
for scheme, source in sources.items():
    folder = backend.private_output(args.output / scheme, ROOT)
    receipt = generate_scrollbar_snapshot(backend, ROOT, folder, data, source)
    expected=['push','toggle']+(['check'] if args.check else [])+(['radio'] if args.radio else [])+['scroll_h','scroll_v']
    assert receipt['translated_controls'] == expected
    project=folder/'PROJECT.json'; backend.write_json(project,data)
    for origin in ('separate','coupled'):
        target=backend.private_output(folder/origin,ROOT)
        command=['xvfb-run','-a','/usr/bin/python3','-B',str(ROOT/'tools/theme-lab/tests/probe_gtk2_button_scene.py'),
                 '--project',str(project),'--rc',receipt['rc'],'--output',str(target)]
        if origin=='coupled':command.append('--embedded')
        if args.toggle:command.append('--toggle')
        if args.radio:command.append('--radio')
        if args.check:command.append('--check')
        child=subprocess.run(command,env=dict(os.environ,I167_PRIVATE_PROBE='1',GTK_MODULES='',GTK2_RC_FILES='/dev/null'),
                             text=True,capture_output=True,timeout=20)
        (target/'native.json').write_text(child.stdout);(target/'stderr.log').write_text(child.stderr)
        if child.returncode or child.stderr:raise RuntimeError(child.stderr or child.stdout)
        native=json.loads(child.stdout)
        for event in (target/'events').glob('*.json'):
            payload=json.loads(event.read_text())
            parsed=subprocess.run([str(ROOT/'tools/theme-lab/build/preview-event-file-test'),
                                    'gtk2',payload['project_sha256'],str(event)],capture_output=True,text=True)
            assert parsed.returncode==0,(event,parsed.stdout,parsed.stderr)
        results.append(dict(native,scheme=scheme))
assert data==before
(args.output/'results.json').write_text(json.dumps({'status':'passed','rows':results,'model_unchanged':True},indent=2))
print(json.dumps({'status':'passed','native_origins':len(results),'native_input_and_replacements':len(results)}))
