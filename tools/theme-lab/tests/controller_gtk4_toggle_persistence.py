# SPDX-License-Identifier: GPL-3.0-or-later
"""Toggle Save/Load/controller restart via real native file dialogs."""
import json
import re
import subprocess


def run(output, observation, click, wait, environment, restart, file_dialog):
    working_path=output/'home/lab/working.json';scene_path=output/'home/lab/scene.json'
    def working():return json.loads(working_path.read_text())
    def scene():return json.loads(scene_path.read_text())
    def measured(width,height,count):
        rows=[r for r in observation().get('native_controls',[]) if r['control']==1]
        if not scene_path.exists() or not (output/'home/probe.json').exists():return None
        position=scene()['recipes']['gtk4']['positions'][1]
        fresh=(output/'home/probe.json').stat().st_mtime_ns>=scene_path.stat().st_mtime_ns
        return rows if fresh and len(rows)==count and all((r['width'],r['height'])==(width,height)
                            and [r['x'],r['y']]==position for r in rows) else None
    def reveal():
        query=subprocess.run(['xwininfo','-root','-children'],env=environment,
                              capture_output=True,text=True,timeout=5)
        windows=re.findall(r'^\s*(0x[0-9a-f]+)\s+"Theme Lab — GTK4 nativo"',query.stdout,re.M)
        for window in windows:
            subprocess.run(['xdotool','windowmove',window,'1400','0'],env=environment,check=True,timeout=5)
        return windows
    def show_separate():
        for _attempt in range(3):
            if working()['separate_preview']:return
            reveal();click('separatePreview')
            try:
                wait(lambda:observation() and working()['separate_preview'],3);return
            except AssertionError:
                if working()['separate_preview']:return
        raise AssertionError('Detached preview checkbox unchanged')
    def set_dimension(axis,value):
        (output/'home/reveal-spin').write_text('set-'+axis+' '+str(value))
        wait(lambda:observation().get(axis+'_text')==str(value))
    def apply(width,height):
        reveal();click('apply')
        wait(lambda:scene()['recipes']['gtk4']['sizes'][1]==[width,height])
        result=wait(lambda:measured(width,height,2));reveal();return result

    wait(lambda:measured(180,50,1));show_separate()
    wait(lambda:measured(180,50,2));reveal()
    original_others={k:v for k,v in working()['recipes'].items() if k!='gtk4'}
    set_dimension('width',280);set_dimension('height',60)
    initial=apply(280,60)
    wait(lambda:'button.theme-lab-gtk4-toggle-' in observation().get('code','') and
                '@import url("toggle.css")' in observation().get('code',''))
    reveal();file_dialog('save','/home/domainos-test/toggle-projeto.json')
    saved_path=output/'home/toggle-projeto.json';wait(saved_path.exists)
    saved=json.loads(saved_path.read_text())
    assert saved['recipes']['gtk4']['sizes'][1]==[280,60]
    assert saved['separate_preview'] is True
    assert {k:v for k,v in saved['recipes'].items() if k!='gtk4'}==original_others
    before=scene_path.read_bytes()
    reveal();restart()
    restarted=wait(lambda:measured(280,60,2));reveal()
    assert scene_path.read_bytes()==before
    assert working()['recipes']==saved['recipes']
    assert working()['separate_preview'] is True
    wait(lambda:'button.theme-lab-gtk4-toggle-' in observation().get('code',''))
    # Change the scene through native setters before Load; an unchanged scene
    # would not prove that the file dialog actually restored the saved model.
    set_dimension('width',220);set_dimension('height',55)
    changed=apply(220,55)
    assert working()['recipes']['gtk4']['sizes'][1]==[220,55]
    applied_before_load=scene_path.read_bytes()
    reveal();file_dialog('load','/home/domainos-test/toggle-projeto.json')
    wait(lambda:working()['recipes']==saved['recipes'])
    assert scene_path.read_bytes()==applied_before_load
    wait(lambda:measured(220,55,2))
    loaded=apply(280,60)
    assert working()['recipes']==saved['recipes']
    assert scene()['recipes']==saved['recipes']
    assert working()['separate_preview'] is True
    subprocess.run(['import','-window','root',str(output/'gtk4-toggle-persistence-root.png')],
                   env=environment,check=True,timeout=10)
    return {'status':'passed','scope':'Real Motif Save/Load dialogs and GTK4 toggle controller restart',
            'initial':initial,'restarted':restarted,'changed_before_load':changed,'loaded':loaded,
            'scene_bytes_preserved_after_restart':True,'all_recipes_preserved':True,
            'saved_detached_preference_preserved':True,'gtk4_toggle_css_visible':True,
            'load_preserved_previous_scene_until_apply':True,
            'runtime_selection_persisted_as_project_property':False,
            'historical_fidelity_claimed':False}
