# SPDX-License-Identifier: GPL-3.0-or-later
"""Real C controller, toggle selection pixels, Apply/relaunch and project history."""
import io
import json
import re
import subprocess
from PIL import Image
from test_backend import ROOT, backend


def run(output, observation, click, wait, environment, visibility_only=False):
    builder=backend.load_builder(ROOT);captures=[]
    working_path=output/'home/lab/working.json'
    def working():return json.loads(working_path.read_text())
    def measured(width,height,count):
        rows=[r for r in observation().get('native_controls',[]) if r['control']==1]
        scene_path=output/'home/lab/scene.json'
        if not scene_path.exists() or not (output/'home/probe.json').exists():return None
        position=json.loads(scene_path.read_text())['recipes']['gtk4']['positions'][1]
        fresh=(output/'home/probe.json').stat().st_mtime_ns>=scene_path.stat().st_mtime_ns
        return rows if fresh and len(rows)==count and all(
            (r['width'],r['height'])==(width,height) and [r['x'],r['y']]==position for r in rows) else None
    def windows():
        canvas=observation().get('canvas_window')
        if not canvas:return {}
        result={}
        for origin,parent in (('separate',None),('coupled',hex(canvas))):
            argv=['xwininfo','-root'] if parent is None else ['xwininfo','-id',parent]
            query=subprocess.run(argv+['-children'],env=environment,capture_output=True,text=True,timeout=5)
            if query.returncode:return {}
            found=re.findall(r'^\s*(0x[0-9a-f]+)\s+"Theme Lab — GTK4 nativo"',query.stdout,re.M)
            if len(found)==1:result[origin]=found[0]
        return result
    def reveal_separate():
        pair=windows()
        if 'separate' in pair:
            subprocess.run(['xdotool','windowmove',pair['separate'],'1400','0'],env=environment,check=True,timeout=5)
    def set_separate(enabled):
        for _attempt in range(3):
            if working()['separate_preview']==enabled:return
            reveal_separate()
            subprocess.run(['import','-window','root',str(output/('checkbox-'+str(enabled)+'-'+str(_attempt)+'.png'))],
                           env=environment,check=True,timeout=10)
            click('separatePreview')
            try:
                wait(lambda:observation() and working()['separate_preview']==enabled,3)
                return
            except AssertionError:
                # Retrying input is allowed only when the persisted option
                # did not change; never toggle a successful click again.
                if working()['separate_preview']==enabled:return
        raise AssertionError('Native checkbox did not reach requested option')
    def apply():
        position=working()['recipes']['gtk4']['positions'][1]
        click('apply')
        def committed():
            r=json.loads((output/'home/lab/scene.json').read_text())['recipes']['gtk4']
            return r['sizes'][1]==[280,60] and r['positions'][1]==position
        wait(committed)
    def native_click(origin):
        recipe=json.loads((output/'home/lab/scene.json').read_text())['recipes']['gtk4']
        x,y=recipe['positions'][1]
        subprocess.run(['xdotool','mousemove','--window',windows()[origin],str(x+60),str(y+20),'click','1',
                        'mousemove','2190','1190'],env=environment,check=True,timeout=5)
    def selection(origin,active):
        # In this WM-less fixture replacement windows start at (0, 0).
        # Relocate the current XID, not an earlier Apply's detached window.
        reveal_separate()
        pair=windows()
        if origin not in pair:return False
        latest=json.loads((output/'home/lab/generated/latest.json').read_text())
        folder=output/'home'/latest['generation_dir'].removeprefix('/home/domainos-test/')
        colors=json.loads((folder/'gtk4-snapshot/GTK4-NATIVE-COLORS.json').read_text())['colors']
        recipe=json.loads((output/'home/lab/scene.json').read_text())['recipes']['gtk4']
        x,y=recipe['positions'][1];width,height=recipe['sizes'][1];shadow=recipe['geometry']['shadow_px']
        path=output/('toggle-'+origin+'-'+str(len(captures))+'.png')
        try:
            subprocess.run(['import','-window',pair[origin],str(path)],env=environment,check=True,timeout=5)
        except (subprocess.TimeoutExpired,subprocess.CalledProcessError):
            # A controller Apply may replace the XID after windows() returned.
            # Retry observation on the same live controller, not its process.
            return False
        actual=Image.open(path).convert('RGB').crop((x,y,x+width,y+height))
        edges=[(a,b) for b in range(height) for a in range(width) if min(a,b,width-1-a,height-1-b)<shadow]
        deltas=[]
        for index in (0,1):
            effective=dict(colors)
            for role in ('button','button-fg'):
                effective[builder.art.ROLES[role][0]]=colors[builder.art.ROLES[role][index]]
            with backend.recipe_rules(builder,recipe['palette']):
                image=builder.art.bevel(builder.art.blank(width,height,'face'),thickness=shadow,down=active)
                expected=Image.open(io.BytesIO(builder.png(image,'button',effective))).convert('RGB')
            deltas.append(sum(actual.getpixel(v)!=expected.getpixel(v) for v in edges))
        if min(deltas):return False
        captures.append({'origin':origin,'selected':active,'size':[width,height],'position':[x,y],
                         'edge_pixels':len(edges),'differences':min(deltas),'capture':str(path)})
        (output/'gtk4-toggle-controller-pixels.json').write_text(json.dumps(captures,indent=2)+'\n')
        return True

    wait(lambda:measured(180,50,1));wait(lambda:selection('coupled',False))
    native_click('coupled');wait(lambda:selection('coupled',True))
    set_separate(True);wait(lambda:measured(180,50,2));reveal_separate()
    wait(lambda:selection('separate',False))
    native_click('separate');wait(lambda:selection('separate',True))
    native_click('separate');wait(lambda:selection('separate',False))
    subprocess.run(['xdotool','sleep','1'],env=environment,check=True,timeout=5)
    (output/'home/reveal-spin').write_text('set-width 280')
    wait(lambda:observation().get('width_text')=='280')
    (output/'home/reveal-spin').write_text('set-height 60')
    wait(lambda:observation().get('height_text')=='60')
    apply();wait(lambda:measured(280,60,2));reveal_separate()
    wait(lambda:selection('coupled',True));wait(lambda:selection('separate',False))
    if visibility_only:
        set_separate(False);wait(lambda:measured(280,60,1))
        set_separate(True);wait(lambda:measured(280,60,2));reveal_separate()
        wait(lambda:selection('separate',False));wait(lambda:selection('coupled',True))
        return {'status':'passed','scope':'Controller toggle detached visibility after Apply only',
                'captures':captures,'detached_close_reopen':True,'history_checked':False}
    window=windows()['coupled']
    subprocess.run(['xdotool','mousemove','--window',window,'100','60','keydown','Control_L','mousedown','1',
                    'mousemove','--window',window,'120','80','sleep','.2','mouseup','1','keyup','Control_L'],
                   env=environment,check=True,timeout=5)
    wait(lambda:working()['recipes']['gtk4']['positions'][1]==[52,52])
    wait(lambda:selection('coupled',True))
    click('projectUndo');wait(lambda:working()['recipes']['gtk4']['positions'][1]==[32,32])
    apply();wait(lambda:measured(280,60,2));reveal_separate()
    wait(lambda:selection('coupled',True));wait(lambda:selection('separate',False))
    click('projectRedo');wait(lambda:working()['recipes']['gtk4']['positions'][1]==[52,52])
    apply();wait(lambda:measured(280,60,2));reveal_separate()
    wait(lambda:selection('coupled',True));wait(lambda:selection('separate',False))
    set_separate(False);wait(lambda:measured(280,60,1))
    set_separate(True);wait(lambda:measured(280,60,2));reveal_separate()
    wait(lambda:selection('separate',False));wait(lambda:selection('coupled',True))
    assert working()['recipes']['gtk3']['sizes'][0]==[220,80]
    subprocess.run(['import','-window','root',str(output/'gtk4-toggle-controller-root.png')],
                   env=environment,check=True,timeout=5)
    (output/'gtk4-toggle-controller-pixels.json').write_text(json.dumps(captures,indent=2)+'\n')
    return {'status':'passed','scope':'C controller native GTK4 toggle Apply/relaunch, independent selection and Undo/Redo',
            'captures':captures,'independent_selection_preserved':True,'detached_close_reopen':True,
            'native_drag_without_toggle_activation':True,'project_undo_redo':True,'gtk3_recipe_preserved':True,
            'save_load_restart_certified':False,'historical_fidelity_claimed':False}
