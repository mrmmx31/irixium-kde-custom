# SPDX-License-Identifier: GPL-3.0-or-later
"""Native toggle selection × inspected states × current KDE palette, two origins."""
import io
import json
import re
import subprocess
from pathlib import Path
from PIL import Image
from test_backend import ROOT,backend
from gtk4_toggles import depressed


def run(output,observation,click,wait,environment,scheme):
    builder=backend.load_builder(ROOT);captures=[]
    working=output/'home/lab/working.json';scene=output/'home/lab/scene.json'
    def data(path):return json.loads(path.read_text())
    def command(*args):
        subprocess.run(list(map(str,args)),env=environment,check=True,timeout=5)
    def windows():
        canvas=observation().get('canvas_window')
        if not canvas:return {}
        result={}
        for origin,parent in (('separate',None),('coupled',hex(canvas))):
            argv=['xwininfo','-root'] if parent is None else ['xwininfo','-id',parent]
            query=subprocess.run(argv+['-children'],env=environment,capture_output=True,text=True,timeout=5)
            matches=re.findall(r'^\s*(0x[0-9a-f]+)\s+"Theme Lab — GTK4 nativo"',query.stdout,re.M)
            if len(matches)==1:result[origin]=matches[0]
        if 'separate' in result:command('xdotool','windowmove',result['separate'],1400,0)
        return result
    def measured():
        rows=[r for r in observation().get('native_controls',[]) if r['control']==1]
        if not scene.exists() or not (output/'home/probe.json').exists():return False
        return len(rows)==2 and all((r['width'],r['height'],r['x'],r['y'])==(180,50,32,32) for r in rows) and (output/'home/probe.json').stat().st_mtime_ns>=scene.stat().st_mtime_ns
    def set_state(state):
        if data(working)['recipes']['gtk4']['edit_state']==state:return
        windows()
        (output/'home/reveal-spin').write_text('edit-state')
        wait(lambda:not (output/'home/reveal-spin').exists())
        command('xdotool','windowfocus',observation()['window'])
        x,y,w,h=observation()['edit_state_arrow']
        command('xdotool','mousemove',x+w//2,y+h//2,'click',1)
        items=wait(lambda:observation().get('edit_state_items'))
        x,y,w,h=items[state];command('xdotool','mousemove',x+w//2,y+h//2,'click',1)
        wait(lambda:data(working)['recipes']['gtk4']['edit_state']==state)
        click('apply')
        wait(lambda:data(scene)['recipes']['gtk4']['edit_state']==state)
    def paint(state,checked):
        if not measured() or data(scene)['recipes']['gtk4']['edit_state']!=state:return False
        pair=windows()
        if len(pair)!=2:return False
        latest=data(output/'home/lab/generated/latest.json')
        folder=output/'home'/latest['generation_dir'].removeprefix('/home/domainos-test/')
        colors=data(folder/'gtk4-snapshot/GTK4-NATIVE-COLORS.json')['colors']
        recipe=data(scene)['recipes']['gtk4'];effective=dict(colors)
        index=2 if state==2 else 1 if state==3 else 0
        for role in ('button','button-fg'):
            effective[builder.art.ROLES[role][0]]=colors[builder.art.ROLES[role][index]]
        shadow=recipe['geometry']['shadow_px']
        with backend.recipe_rules(builder,recipe['palette']):
            symbolic=builder.art.bevel(builder.art.blank(180,50,'face'),thickness=shadow,
                                       down=depressed(checked,state==1,state==2))
            expected=Image.open(io.BytesIO(builder.png(symbolic,'button',effective))).convert('RGB')
        edges=[(x,y) for y in range(50) for x in range(180) if min(x,y,179-x,49-y)<shadow]
        rows=[]
        for origin,window in pair.items():
            if state!=3:command('xdotool','windowfocus',window)
            command('xdotool','mousemove',2190,1190,'sleep','.15')
            path=output/(scheme+'-'+str(state)+'-'+str(checked)+'-'+origin+'.png')
            try:command('import','-window',window,path)
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired):return False
            image=Image.open(path).convert('RGB').crop((32,32,212,82))
            delta=sum(image.getpixel(v)!=expected.getpixel(v) for v in edges)
            if delta:return False
            rows.append({'scheme':scheme,'state':state,'selected':checked,'origin':origin,
                         'edge_pixels':len(edges),'differences':delta,'capture':str(path)})
        captures.extend(rows)
        (output/'gtk4-toggle-state-pixels.json').write_text(json.dumps(captures,indent=2)+'\n')
        return True
    wait(lambda:any(r['control']==1 for r in observation().get('native_controls',[])))
    initial=data(working)
    for _attempt in range(3):
        if data(working)['separate_preview']:break
        windows();click('separatePreview')
        try:wait(lambda:data(working)['separate_preview'],3)
        except AssertionError:
            if data(working)['separate_preview']:break
    assert data(working)['separate_preview']
    wait(measured)
    for checked in (False,True):
        if checked:
            set_state(0);wait(lambda:paint(0,False))
            for origin in ('coupled','separate'):
                window=windows()[origin]
                command('xdotool','mousemove','--window',window,90,55,'click',1,
                        'mousemove',2190,1190)
            wait(lambda:paint(0,True))
            command('xdotool','sleep','1')
        for state in range(4):
            set_state(state);wait(lambda:paint(state,checked),45)
    final=data(working)
    assert all(final['recipes'][name]==value for name,value in initial['recipes'].items() if name!='gtk4')
    unique={(r['state'],r['selected'],r['origin']):r for r in captures}
    assert len(unique)==16
    return {'status':'passed','scheme':scheme,'scope':'GTK4 toggle native controller: selection × four inspected states × two origins',
            'captures':list(unique.values()),'other_recipes_preserved':True,
            'historical_fidelity_claimed':False,'focus_or_combined_backdrop_disabled_certified':False}
