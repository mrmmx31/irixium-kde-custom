# SPDX-License-Identifier: GPL-3.0-or-later
"""Real guarded worker: events, asynchronous update, refusal and recovery."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools/theme-lab'),str(ROOT/'tools/theme-lab/tests')]
from test_backend import model
import backend
from gtk4_generation import generate_snapshot
from gtk4_embed_fixture import MotifHost
from gtk4_push_api import bind


def wait(predicate,timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=predicate()
        if value:return value
        time.sleep(.05)
    raise AssertionError('GTK4 worker observation deadline expired')


def main():
    guards=backend.private_namespace(ROOT)
    home=Path(os.environ['HOME']);project=home/'worker-project.json';events=home/'worker-events'
    proposal=model();proposal['selected_family']='gtk4'
    proposal['recipes']['gtk4'].update(visible_controls=1,selected_control=0,edit_state=0,
        positions=[[32,32]]+[[0,0] for _ in range(15)],sizes=[[180,60]]+[[0,0] for _ in range(15)])
    backend.write_json(project,proposal);proposal,digest=backend.project(project)
    generated=backend.generate(ROOT,home/'backend-output',proposal,digest,
                               home/'.config/kdeglobals',family_scope=['gtk4'])
    receipt=generated['families']['gtk4']
    assert receipt['status']=='partially_generated',receipt
    # Inspect the selected source with the real GTK4 CSS parser in this
    # already guarded namespace. Definitions come from the existing push.css.
    import ctypes as C
    from gtk4_push_api import PushAPI
    bind(C.CDLL('libgtk-4.so.1'),'gtk_init',None)()
    parser_api=PushAPI();parsed_states=[]
    for state in ('normal','pressed','disabled','backdrop','hover'):
        source=backend.snippet(ROOT,proposal,'gtk4','push',state,home/'.config/kdeglobals')['source']
        fragment=Path(receipt['css']).parent/('selected-'+state+'.css')
        fragment.write_text(source,encoding='utf-8')
        provider=parser_api.css_provider(fragment);parser_api.unref(provider)
        parsed_states.append(state)
    from gtk4_route import command as route_command
    command=route_command(ROOT,receipt,proposal,events,home/'.config/kdeglobals')
    command+=['--preview-instance','e'*32]
    project=Path(receipt['snapshot'])/'PROJECT.json'
    proposal,digest=backend.project(project)
    host=None
    if os.environ.get('T04_WORKER_ORIGIN')=='coupled':
        host=MotifHost(ROOT/'.qa-t04-anchor-foundation/gtk4-embed-host',bind)
        command+=['--embed-window',str(host.canvas),'--host-pid',str(host.process.pid),
            '--host-bridge',str(ROOT/'.qa-t04-anchor-foundation/gtk4-host-build/libtheme-lab-gtk4-host.so')]
    with (home/'worker.log').open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        def state():
            if process.poll() is not None:raise AssertionError('GTK4 worker exited: '+str(process.returncode))
            path=events/'WORKER.json'
            return json.loads(path.read_text()) if path.exists() else None
        def rows():
            return [json.loads(p.read_text()) for p in sorted(events.glob('event-*.json'))]
        try:
            initial=wait(state);window=initial['window']
            wait(lambda:any(e['action']=='metrics' for e in rows()))
            initial_metrics=next(e['metrics'][0] for e in rows() if e['action']=='metrics')
            assert initial_metrics['font_description'] and not initial_metrics['font_not_applicable']
            minimum=initial_metrics['native_minimum_before_custom_size']
            natural=initial_metrics['native_natural_before_custom_size']
            assert all(0<low<=high for low,high in zip(minimum,natural))
            subprocess.run(['xdotool','mousemove','--window',str(window),'100','60',
                'keydown','Control_L','click','1','keyup','Control_L'],check=True,timeout=5)
            wait(lambda:len([e for e in rows() if e['action']=='select'])==1)
            assert not [e for e in rows() if e['action'] in ('move','native')]
            subprocess.run(['xdotool','mousemove','--window',str(window),'100','60',
                'keydown','Control_L','mousedown','1','mousemove','--window',str(window),'120','80',
                'sleep','0.2','mouseup','1','keyup','Control_L'],check=True,timeout=5)
            moved=wait(lambda:next((e for e in rows() if e['action']=='move'),None))
            assert [moved['x'],moved['y']]==[52,52],moved
            assert moved['coordinate_space']=='gtk_logical_px'
            assert not [e for e in rows() if e['action']=='native']
            wait(lambda:any(e['action']=='metrics' and e['metrics'][0]['allocation']==[52,52,180,60] for e in rows()))
            subprocess.run(['xdotool','mousemove','--window',str(window),'100','60','click','1'],check=True,timeout=5)
            wait(lambda:len([e for e in rows() if e['action']=='native'])==1)
            changed=copy.deepcopy(proposal)
            changed['recipes']['gtk4']['positions'][0]=[50,65]
            changed['recipes']['gtk4']['sizes'][0]=[200,70]
            gate=home/'color-gate';gate.touch()
            backend.write_json(project,changed);changed,new_digest=backend.project(project)
            busy=wait(lambda:state() if state().get('generation_pid') else None)
            os.kill(busy['generation_pid'],0)  # Same owned generation child is live.
            subprocess.run(['xdotool','mousemove','--window',str(window),'100','60','click','1'],check=True,timeout=5)
            wait(lambda:len([e for e in rows() if e['action']=='native'])==2,5)
            assert state()['project_sha256']==digest
            gate.unlink()
            wait(lambda:state()['project_sha256']==new_digest)
            wait(lambda:any(e['action']=='metrics' and e['project_sha256']==new_digest and
                e['metrics'][0]['allocation']==[50,65,200,70] for e in rows()))
            custom_metrics=next(e['metrics'][0] for e in rows() if e['action']=='metrics' and e['project_sha256']==new_digest)
            assert custom_metrics['native_natural_before_custom_size']==natural
            assert custom_metrics['native_minimum_before_custom_size']==minimum
            assert state()['window']==window
            small=copy.deepcopy(changed);small['recipes']['gtk4']['sizes'][0]=[40,15]
            backend.write_json(project,small);_,small_digest=backend.project(project)
            small_metrics=wait(lambda:next((e['metrics'][0] for e in rows() if e['action']=='metrics' and
                e['project_sha256']==small_digest),None))
            assert small_metrics['native_minimum_before_custom_size']==minimum
            assert small_metrics['native_natural_before_custom_size']==natural
            assert all(a>=b for a,b in zip(small_metrics['allocation'][2:],minimum))
            backend.write_json(project,changed)
            wait(lambda:state()['project_sha256']==new_digest)
            invalid=copy.deepcopy(changed);invalid['recipes']['gtk4']['visible_controls']=3
            backend.write_json(project,invalid)
            wait(lambda:state()['error'] is not None)
            assert state()['project_sha256']==new_digest
            subprocess.run(['xdotool','mousemove','--window',str(window),'110','95','click','1'],check=True,timeout=5)
            wait(lambda:len([e for e in rows() if e['action']=='native'])==3)
            assert [e for e in rows() if e['action']=='native'][-1]['project_sha256']==new_digest
            changed['recipes']['gtk4']['edit_state']=1
            backend.write_json(project,changed);_,last_digest=backend.project(project)
            wait(lambda:state()['project_sha256']==last_digest and state()['error'] is None)
            assert state()['window']==window
            assert len([e for e in rows() if e['action']=='native'])==3
            subprocess.run(['import','-window',str(window),str(home/'worker-final.png')],check=True,timeout=5)
            changed['recipes']['gtk4']['edit_state']=0
            changed['recipes']['gtk4']['sizes'][0]=[0,0]
            changed['recipes']['gtk4']['geometry']['font_px']=20
            changed['recipes']['gtk4']['geometry']['control_padding_px']=8
            backend.write_json(project,changed);_,auto_digest=backend.project(project)
            automatic=wait(lambda:next((e['metrics'][0] for e in rows() if e['action']=='metrics' and
                e['project_sha256']==auto_digest),None))
            assert automatic['font_description']!=initial_metrics['font_description']
            assert all(a>b for a,b in zip(automatic['native_natural_before_custom_size'],natural))
            assert automatic['allocation'][2:]==automatic['native_natural_before_custom_size']
            # Consume actual persisted worker events with the C reader, not
            # a re-created schema fixture. Stale hashes remain per-event.
            c_reader=ROOT/'.qa-t04-anchor-foundation/gtk4-host-build/preview-event-file-test'
            consumed=[]
            for event_file in sorted(events.glob('event-*.json')):
                event=json.loads(event_file.read_text())
                checked=subprocess.run([str(c_reader),'gtk4',event['project_sha256'],str(event_file)],
                    check=True,capture_output=True,text=True,timeout=5)
                consumed.append(json.loads(checked.stdout))
            assert {r['action'] for r in consumed}=={0,1,2,3},consumed
            process.terminate();code=process.wait(timeout=8);assert code==0,code
            final=json.loads((events/'WORKER.json').read_text());assert final['status']=='closed'
            # A fresh worker closes while its generation child is genuinely
            # live. Coupled mode loses the real host; standalone gets TERM.
            recovery_model,recovery_digest=backend.project(project)
            generate_snapshot(ROOT,home/'worker-snapshot-2',recovery_model,recovery_digest,home/'.config/kdeglobals')
            second_events=home/'worker-events-2'
            second_command=list(command)
            second_command[second_command.index('--snapshot')+1]=str(home/'worker-snapshot-2')
            second_command[second_command.index('--events-dir')+1]=str(second_events)
            second=subprocess.Popen(second_command,stdout=log,stderr=subprocess.STDOUT)
            try:
                def second_state():
                    if second.poll() is not None:raise AssertionError('Second worker exited early')
                    path=second_events/'WORKER.json'
                    return json.loads(path.read_text()) if path.exists() else None
                wait(second_state)
                gate.touch()
                recovery_model['recipes']['gtk4']['sizes'][0]=[210,75]
                backend.write_json(project,recovery_model)
                closing=wait(lambda:second_state() if second_state().get('generation_pid') else None)
                generation_pid=closing['generation_pid'];os.kill(generation_pid,0)
                if host:host.process.terminate();host.process.wait(timeout=3)
                else:second.terminate()
                second_code=second.wait(timeout=8)
                assert second_code==(1 if host else 0),second_code
                end=json.loads((second_events/'WORKER.json').read_text())
                assert end['status']==('host_lost' if host else 'closed')
                assert not Path('/proc',str(generation_pid)).exists()
            finally:
                if second.poll() is None:second.kill();second.wait(timeout=5)
                gate.unlink(missing_ok=True)
            result={'status':'passed_scoped_worker','guards':guards,'native_clicks':3,
                'backend_generation_and_preview_command':True,
                'selected_fragments_parsed_by_native_gtk4':parsed_states,
                'actual_worker_events_consumed_by_c':len(consumed),
                'ctrl_click_select_only':True,'ctrl_drag_move_without_native_activation':True,
                'drag_allocation':[52,52,180,60],
                'origin':'coupled' if host else 'separate',
                'initial_metrics':initial_metrics,'custom_metrics':custom_metrics,
                'automatic_metrics':automatic,'natural_measurements_independent_of_custom_request':True,
                'below_minimum_request_metrics':small_metrics,
                'close_during_live_generation':True,'generation_child_reaped':True,
                'host_loss_exit_code':second_code if host else None,
                'responsive_while_owned_generation_child_live':True,
                'artificial_clicks':0,'identity_preserved':True,'metrics_after_update':[50,65,200,70],
                'unsupported_scene_preserved':True,'valid_recovery':True,'closed_exit_code':code,
                'instance_preserved':all(e['preview_instance']=='e'*32 for e in rows()),
                'public_controller_connected':False,'historical_fidelity_claimed':False}
            backend.write_json(home/'WORKER-RESULTADO.json',result);print(json.dumps(result),flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            if host:host.close()


if __name__=='__main__':main()
