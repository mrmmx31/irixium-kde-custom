# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared real-controller anchor proof for native GTK2 and GTK3."""
import json
import subprocess
import time


def run(output, observation, click, wait, move_separate, allocated, edit, environment, family, file_dialog, restart):
    results = {}
    if family=='gtk3':
        # Generation and native startup are distinct stages. A single wait
        # from process creation previously spent most of its allowance on
        # theme assets, then expired without observing the native child.
        wait(lambda: allocated(220,80) or observation().get('status','').startswith('Proposta privada gerada.'))
        wait(lambda: allocated(220,80))
    else:
        wait(lambda: len(observation().get('native_bars',[]))==2)
    scene=output/'home/lab/scene.json'
    baseline=json.loads(scene.read_text())
    working=output/'home/lab/working.json'
    click('separatePreview')
    wait(lambda: allocated(220,80,True) if family=='gtk3' else len(observation().get('native_bars',[]))==4)
    move_separate()
    def bars(control):
        if (output/'home/probe.json').stat().st_mtime_ns<scene.stat().st_mtime_ns:return None
        current = observation()
        # Automatic/natural dimensions can equal the preceding allocation.
        # Those old metrics do not prove the requested generation completed.
        if current.get('status', '').startswith('Atualizando a cena nativa'):
            return None
        rows=[r for r in current.get('native_bars',[]) if r['control']==control and r['position_valid'] and r['cell_offset_valid']]
        return rows if len(rows)==2 and rows[0]['width']==rows[1]['width'] and rows[0]['height']==rows[1]['height'] else None
    cases=[]
    for control,axis in ((10,'width'),(11,'height')):
        (output/'home/reveal-spin').write_text('control '+str(control))
        wait(lambda: observation().get('anchor_sensitive') and observation().get(axis+'_sensitive'))
        # Choosing a control does not change its applied dimensions. Avoid
        # launching an unnecessary generation while opening its selector.
        wait(lambda: json.loads(working.read_text())['recipes'][family]['selected_control']==control)
        original=wait(lambda: bars(control))
        # Select the actual second native item by its Motif bounds;
        # no callback is invoked by the test fixture.
        (output/'home/reveal-spin').write_text('anchor');time.sleep(.4)
        x,y,w,h=observation()['anchor']
        subprocess.run(['xdotool','mousemove',str(x+w-8),str(y+h//2),'click','1'],env=environment,check=True)
        wait(lambda: observation().get('anchor_end_option'),5)
        click('anchor_end_option')
        wait(lambda: observation().get('anchor_selected')==1,5)
        current=wait(lambda: json.loads(scene.read_text())['recipes'][family].get('length_anchor',[0]*16)[control]==1)
        saved=json.loads(working.read_text())
        applied=json.loads(scene.read_text())
        assert saved['schema_version']==applied['schema_version']==2
        recipe=applied['recipes'][family];boundary=recipe['positions'][control][0 if control==10 else 1]
        # GTK3 first allocates the enclosing label/cell, then reconciles its
        # trailing edge in an idle callback using the measured child offset.
        # Receiving metrics is not yet proof that this placement settled.
        def preserved_position():
            rows = bars(control)
            return rows if rows and [(r['x'],r['y']) for r in rows] == [(r['x'],r['y']) for r in original] else None
        placed=wait(preserved_position)
        assert [(r['x'],r['y']) for r in placed]==[(r['x'],r['y']) for r in original]
        for length in (120,1,0,160):
            edit('controlWidth*fieldValue' if axis=='width' else 'controlHeight*fieldValue',length)
            click('apply')
            wait(lambda: json.loads(scene.read_text())['recipes'][family]['sizes'][control][0 if control==10 else 1]==length)
            def fixed():
                rows=bars(control)
                if not rows:return None
                if not all((r['x']+r['width'] if control==10 else r['y']+r['height'])==boundary for r in rows):return None
                if length>1 and not all((r['width'] if control==10 else r['height'])==length for r in rows):return None
                return rows
            rows=wait(fixed)
            assert all((r['height'] if control==10 else r['width'])==15 for r in rows)
            cases.append(dict(control=control,request=length,boundary=boundary,native=rows))
            move_separate()
        final=json.loads(scene.read_text())
        assert final['recipes'][family]['geometry']==baseline['recipes'][family]['geometry']
        for other_family,recipe in baseline['recipes'].items():
            if other_family!=family:
                expected=dict(recipe)
                expected.setdefault('length_anchor',[0]*16)
                expected.setdefault('scrollbar_parts',{})
                actual=dict(final['recipes'][other_family])
                actual.setdefault('length_anchor',[0]*16)
                actual.setdefault('scrollbar_parts',{})
                assert actual==expected,(family,actual,expected)
    assert json.loads(working.read_text())['recipes'][family]['length_anchor']==json.loads(scene.read_text())['recipes'][family]['length_anchor']
    file_dialog('save','/home/domainos-test/anchors-project.json')
    saved=json.loads((output/'home/anchors-project.json').read_text())
    assert saved['recipes'][family]['length_anchor'][10:12]==[1,1]
    move_separate();click('separatePreview')
    wait(lambda:not observation().get('separate_preview_checked',True))
    file_dialog('load','/home/domainos-test/anchors-project.json')
    wait(lambda:bars(10) and bars(11))
    assert json.loads(working.read_text())['recipes']==saved['recipes']
    move_separate();click('projectUndo')
    wait(lambda:not observation().get('separate_preview_checked',True))
    click('projectRedo');wait(lambda:bars(10) and bars(11))
    assert observation()['separate_preview_checked']
    applied_before=scene.read_bytes()
    restart();wait(lambda:bars(10) and bars(11))
    assert scene.read_bytes()==applied_before
    assert json.loads(working.read_text())['recipes']==saved['recipes']
    for control,axis in ((10,'width'),(11,'height')):
        boundary=saved['recipes'][family]['positions'][control][0 if control==10 else 1]
        def settled_restart():
            rows = bars(control)
            return rows if rows and all((r['x']+r['width'] if control==10 else r['y']+r['height'])==boundary for r in rows) else None
        rows = wait(settled_restart)
        assert all((r['x']+r['width'] if control==10 else r['y']+r['height'])==boundary for r in rows)
    results['native_save_load_project_undo_redo_restart']=True
    results.update(status='passed',anchor_native_cases=cases,
                   selector='X11 pointer, actual Motif item bounds',
                   save_schema_2=True,other_family_recipe_values_preserved=True,
                   schema_2_adds_explicit_default_anchor_and_piece_fields=True,
                   personal_profile_exposed=False,historical_fidelity_claimed=False)
    return results
