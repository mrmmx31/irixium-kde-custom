# SPDX-License-Identifier: GPL-3.0-or-later
"""One GTK4 control, native state selection and both origins per palette."""
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import backend


def run(output, observation, click, wait, environment, scheme):
    captures=[]
    root=Path(__file__).resolve().parents[3]
    builder=backend.load_builder(root)
    scene=output/'home/lab/scene.json'
    working=output/'home/lab/working.json'
    def windows():
        canvas=observation().get('canvas_window')
        if not canvas:return {}
        result={}
        for origin,parent in (('separate',None),('coupled',hex(canvas))):
            argv=['xwininfo','-root'] if parent is None else ['xwininfo','-id',parent]
            query=subprocess.run(argv+['-children'],env=environment,capture_output=True,text=True,timeout=5)
            if query.returncode:return {}
            candidates=re.findall(r'^\s*(0x[0-9a-f]+)\s+"Theme Lab — GTK4 nativo"',query.stdout,re.M)
            if len(candidates)==1:result[origin]=candidates[0]
        return result
    def measurements():
        rows=[r for r in observation().get('native_controls',[]) if r['control']==0]
        return rows if len(rows)==2 and all((r['width'],r['height'])==(180,50) for r in rows) else None
    def paint(state):
        if not measurements() or json.loads(scene.read_text())['recipes']['gtk4']['edit_state']!=state:
            return False
        pair=windows()
        if len(pair)!=2:return False
        subprocess.run(['xdotool','windowmove',pair['separate'],'1400','0'],env=environment,check=True,timeout=5)
        latest=json.loads((output/'home/lab/generated/latest.json').read_text())
        folder=output/'home'/latest['generation_dir'].removeprefix('/home/domainos-test/')
        colors=json.loads((folder/'gtk4-snapshot/GTK4-NATIVE-COLORS.json').read_text())['colors']
        recipe=json.loads(scene.read_text())['recipes']['gtk4']
        with backend.recipe_rules(builder,recipe['palette']):
            effective=dict(colors)
            index=2 if state==2 else 1 if state==3 else 0
            for role in ('button','button-fg'):
                effective[builder.art.ROLES[role][0]]=colors[builder.art.ROLES[role][index]]
            shadow=recipe['geometry']['shadow_px']
            symbolic=builder.art.bevel(builder.art.blank(180,50,'face'),thickness=shadow,down=state==1)
            expected=Image.open(io.BytesIO(builder.png(symbolic,'button',effective))).convert('RGB')
        edges=[(x,y) for y in range(50) for x in range(180) if x<shadow or y<shadow or x>=180-shadow or y>=50-shadow]
        matched=[]
        for origin,window in pair.items():
            if state!=3:
                subprocess.run(['xdotool','windowfocus',window],env=environment,check=True,timeout=5)
            # Wait for the native focus transition; this is test input, not
            # a production animation or an assumed process completion.
            subprocess.run(['xdotool','sleep','0.15'],env=environment,check=True,timeout=5)
            path=output/(scheme+'-'+str(state)+'-'+origin+'.png')
            subprocess.run(['import','-window',window,str(path)],env=environment,check=True,timeout=5)
            actual=Image.open(path).convert('RGB').crop((32,32,212,82))
            delta=sum(actual.getpixel(p)!=expected.getpixel(p) for p in edges)
            matched.append(delta==0)
            captures.append({'scheme':scheme,'state':state,'origin':origin,'capture':str(path),
                             'edge_pixels':len(edges),'differences':delta})
        (output/'gtk4-controller-pixels.json').write_text(json.dumps(captures,indent=2)+'\n')
        return all(matched)
    wait(lambda:any(r['control']==0 and not r['separate'] for r in observation().get('native_controls',[])))
    initial=json.loads(working.read_text())
    # Asynchronous startup can scroll the recipe after the first reveal.
    # Reissue only a native click whose saved choice did not change; never
    # toggle an already enabled origin or write its preference as test setup.
    for attempt in range(3):
        if json.loads(working.read_text())['separate_preview']:break
        click('separatePreview')
        try:
            wait(lambda:json.loads(working.read_text())['separate_preview'],3)
        except AssertionError as error:
            if str(error)!='Timeout waiting for native controller/preview condition':raise
    assert json.loads(working.read_text())['separate_preview'], 'Native separate-preview checkbox did not enable'
    wait(measurements)
    for state in range(4):
        if state:
            (output/'home/reveal-spin').write_text('edit-state')
            wait(lambda:not (output/'home/reveal-spin').exists())
            subprocess.run(['xdotool','windowfocus',str(observation()['window'])],env=environment,check=True,timeout=5)
            x,y,w,h=observation()['edit_state_arrow']
            subprocess.run(['xdotool','mousemove',str(x+w//2),str(y+h//2),'click','1'],env=environment,check=True,timeout=5)
            items=wait(lambda:observation().get('edit_state_items'))
            x,y,w,h=items[state]
            subprocess.run(['xdotool','mousemove',str(x+w//2),str(y+h//2),'click','1'],env=environment,check=True,timeout=5)
            wait(lambda:json.loads(working.read_text())['recipes']['gtk4']['edit_state']==state)
            click('apply')
        # Generation completion and replacement of the two owned workers are
        # separate observations. Poll the same live controller with the
        # harness's usual deadline rather than a shorter pixel-only timeout.
        wait(lambda:paint(state),45)
    final=json.loads(working.read_text())
    assert all(final['recipes'][name]==value for name,value in initial['recipes'].items() if name!='gtk4')
    return {'status':'passed','scope':'Native GTK4 controller forced states and current palette edges',
            'scheme':scheme,'captures':captures,'other_recipes_preserved':True,
            'historical_fidelity_claimed':False,'combined_states_certified':False}
