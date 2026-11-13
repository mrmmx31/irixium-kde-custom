# SPDX-License-Identifier: GPL-3.0-or-later
"""Guarded actual toggle worker: selection, identities, reload and Ctrl layout."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools/theme-lab'),str(ROOT/'tools/theme-lab/tests')]
import backend
from test_backend import model
from gtk4_route import command as route_command
from gtk4_embed_fixture import MotifHost
from gtk4_push_api import bind


def main():
    guards=backend.private_namespace(ROOT)
    home=Path(os.environ['HOME']);project=home/'toggle-project.json';events=home/'toggle-events'
    proposal=model();proposal['selected_family']='gtk4'
    proposal['recipes']['gtk4'].update(visible_controls=2,selected_control=1,edit_state=0,
        positions=[[32,32] for _ in range(16)],sizes=[[180,60] for _ in range(16)])
    backend.write_json(project,proposal);proposal,digest=backend.project(project)
    generation=backend.generate(ROOT,home/'backend-output',proposal,digest,
                                home/'.config/kdeglobals',family_scope=['gtk4'])
    receipt=generation['families']['gtk4']
    assert receipt['translated_controls']==['push','toggle'],receipt
    command=route_command(ROOT,receipt,proposal,events,home/'.config/kdeglobals')
    command+=['--preview-instance','f'*32]
    project=Path(receipt['snapshot'])/'PROJECT.json'
    proposal,digest=backend.project(project)
    host=None
    if os.environ.get('T04_WORKER_ORIGIN')=='coupled':
        host=MotifHost(ROOT/'.qa-t04-anchor-foundation/gtk4-embed-host',bind)
        command+=['--embed-window',str(host.canvas),'--host-pid',str(host.process.pid),
            '--host-bridge',str(ROOT/'.qa-t04-anchor-foundation/gtk4-host-build/libtheme-lab-gtk4-host.so')]
    with (home/'toggle-worker.log').open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        def state():
            if process.poll() is not None:raise AssertionError('Owned worker exited: '+str(process.returncode))
            path=events/'WORKER.json'
            return json.loads(path.read_text()) if path.exists() else None
        def rows():return [json.loads(p.read_text()) for p in sorted(events.glob('event-*.json'))]
        def wait(predicate,timeout=45):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                state();value=predicate()
                if value:return value
                time.sleep(.05)
            raise AssertionError('Same worker observation deadline')
        def selected():return state()['toggle_selection'].get('1')
        def native():return [r for r in rows() if r['action']=='native']
        def pointer(*args):subprocess.run(['xdotool',*map(str,args)],check=True,timeout=5)
        try:
            initial=wait(state);window=initial['window']
            wait(lambda:any(r['action']=='metrics' for r in rows()))
            assert selected() is False
            pointer('mousemove','--window',window,100,60,'keydown','Control_L','click',1,'keyup','Control_L')
            wait(lambda:any(r['action']=='select' for r in rows()))
            assert not native() and selected() is False
            pointer('mousemove','--window',window,100,60,'keydown','Control_L','mousedown',1,
                    'mousemove','--window',window,120,80,'sleep','.2','mouseup',1,'keyup','Control_L')
            moved=wait(lambda:next((r for r in rows() if r['action']=='move'),None))
            assert [moved['x'],moved['y']]==[52,52] and moved['control_index']==1
            assert not native() and selected() is False
            pointer('mousemove','--window',window,100,80,'click',1)
            wait(lambda:len(native())==1 and selected() is True)
            assert native()[0]['state']=={'clicked':True,'selected':True,'active':True}
            changed=copy.deepcopy(proposal);changed['recipes']['gtk4']['sizes'][1]=[210,70]
            gate=home/'color-gate';gate.touch()
            backend.write_json(project,changed);changed,new_digest=backend.project(project)
            wait(lambda:state().get('generation_pid'))
            pointer('mousemove','--window',window,100,80,'click',1)
            wait(lambda:len(native())==2 and selected() is False)
            assert native()[-1]['project_sha256']==digest
            gate.unlink()
            wait(lambda:state()['project_sha256']==new_digest)
            wait(lambda:any(r['action']=='metrics' and r['project_sha256']==new_digest for r in rows()))
            assert selected() is False and state()['window']==window and len(native())==2
            invalid=copy.deepcopy(changed);invalid['recipes']['gtk4']['visible_controls']=4
            backend.write_json(project,invalid)
            wait(lambda:state()['error'] is not None)
            assert selected() is False and state()['project_sha256']==new_digest
            pointer('mousemove','--window',window,100,60,'click',1)
            wait(lambda:len(native())==3 and selected() is True)
            recovered=copy.deepcopy(changed);recovered['recipes']['gtk4']['positions'][1]=[40,40]
            backend.write_json(project,recovered);_,recovered_digest=backend.project(project)
            wait(lambda:state()['project_sha256']==recovered_digest and state()['error'] is None)
            assert selected() is True
            recorded=rows()
            assert all(r['control_index']==1 and r['control_id']=='toggle' and r['preview_instance']=='f'*32 for r in recorded)
            assert {r['project_sha256'] for r in native()}=={digest,new_digest}
            reader=ROOT/'.qa-t04-anchor-foundation/gtk4-host-build/preview-event-file-test'
            consumed=[]
            for path in sorted(events.glob('event-*.json')):
                event=json.loads(path.read_text())
                raw=subprocess.check_output([str(reader),'gtk4',event['project_sha256'],str(path)],timeout=5)
                parsed=json.loads(raw);assert parsed['control']==1,parsed
                consumed.append(parsed)
            process.terminate();assert process.wait(timeout=8)==0
            backend.write_json(home/'WORKER-RESULTADO.json',{'status':'passed_toggle_worker',
                'guards':guards,'origin':'coupled' if host else 'separate','native_clicks':3,
                'ctrl_layout_without_toggle_activation':True,'responsive_during_generation':True,
                'selection_preserved_on_reload':True,'unsupported_preserves_scene':True,
                'events_identity_verified':True,'events':recorded,'closed_exit_code':0,
                'backend_route_used':True,'actual_events_consumed_by_c':consumed,
                'public_controller_connected':False,'historical_fidelity_claimed':False})
        finally:
            pointer('mouseup',1,'keyup','Control_L')
            if process.poll() is None:process.terminate();process.wait(timeout=8)
            if host:host.close()


if __name__=='__main__':main()
