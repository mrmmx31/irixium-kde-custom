#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the real GTK4 scrollbar worker in either private preview origin."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import io
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools/theme-lab'),str(ROOT/'tools/theme-lab/tests')]
import backend
from test_backend import model
from gtk4_route import command as route_command
from gtk4_embed_fixture import MotifHost
from gtk4_push_api import bind
from gtk4_scrollbars import _effective_palette


def wait(predicate,timeout=30):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=predicate()
        if value:return value
        time.sleep(.05)
    raise AssertionError('GTK4 scrollbar worker observation deadline expired')


def main():
    if not os.environ.get('DISPLAY','').startswith(':'):
        raise SystemExit('Private X11 display required')
    guards=backend.private_namespace(ROOT)
    home=Path(os.environ['HOME'])
    project_path=home/'scrollbar-project.json'
    events=home/'scrollbar-events'
    proposal=model();proposal['selected_family']='gtk4'
    recipe=proposal['recipes']['gtk4']
    vertical_x=320 if os.environ.get('T04_WORKER_ORIGIN')=='coupled' else 360
    recipe.update(visible_categories=1<<2,visible_controls=(1<<10)|(1<<11),
                  selected_control=10,edit_state=int(os.environ.get('T04_SCROLLBAR_STATE','0')),
                  positions=[[32,32] if i==10 else [vertical_x,32] if i==11 else [0,0]
                              for i in range(16)],
                  sizes=[[280,15] if i==10 else [15,180] if i==11 else [0,0]
                         for i in range(16)])
    backend.write_json(project_path,proposal)
    proposal,source_digest=backend.project(project_path)
    generated=backend.generate(ROOT,home/'scrollbar-output',proposal,source_digest,
                               home/'.config/kdeglobals',family_scope=['gtk4'])
    receipt=generated['families']['gtk4']
    assert receipt['translated_controls']==['scroll_h','scroll_v'],receipt
    command=route_command(ROOT,receipt,proposal,events,home/'.config/kdeglobals')
    assert '--private-scrollbar-session' in command,command
    command+=['--preview-instance','d'*32]
    project_path=Path(receipt['snapshot'])/'PROJECT.json'
    proposal,digest=backend.project(project_path)
    host=None
    if os.environ.get('T04_WORKER_ORIGIN')=='coupled':
        host=MotifHost(ROOT/'.qa-t04-anchor-foundation/gtk4-embed-host',bind)
        command+=['--embed-window',str(host.canvas),'--host-pid',str(host.process.pid),
                  '--host-bridge',str(ROOT/'.qa-t04-anchor-foundation/gtk4-host-build/libtheme-lab-gtk4-host.so')]

    def state():
        if process.poll() is not None:
            raise AssertionError('GTK4 scrollbar worker exited: '+str(process.returncode))
        path=events/'WORKER.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

    def rows():
        return [json.loads(path.read_text(encoding='utf-8'))
                for path in sorted(events.glob('event-*.json'))]

    def capture_and_compare(window, state_value, colors, builder, target):
        path=home/('scrollbar-state-'+str(state_value)+'.png')
        # A metrics event is emitted after GTK allocates the scene; wait until
        # the X surface has painted it, avoiding a transient blank frame.
        previous=None;deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            subprocess.run(['import','-window',str(window),str(path)],
                           check=True,timeout=10,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            current=backend.sha(backend.read_file(path))
            if current==previous:break
            previous=current;time.sleep(.05)
        else:raise AssertionError('GTK4 scrollbar surface did not stabilize')
        actual=Image.open(path).convert('RGB')
        recipe_now=proposal['recipes']['gtk4']
        art=builder.art
        def expected(fill,width,height,down,effective):
            pixels=art.bevel(art.blank(width,height,fill),
                             thickness=recipe_now['geometry']['shadow_px'],down=down)
            return Image.open(io.BytesIO(builder.png(pixels,'button',effective))).convert('RGB')
        # The GTK4 adjustment is 25/100, so native thumb lengths are 25% of
        # each allocated scrollbar. Compare the exact generated pixel art to
        # the real GTK render at 1:1; mask only the slider over the trough.
        htrough=(32,32,312,47);hthumb=(102,34,172,45)
        vtrough=(vertical_x,32,vertical_x+15,212)
        vthumb=(vertical_x+2,77,vertical_x+13,122)
        comparisons=[]
        selected=proposal['recipes']['gtk4']['selected_control']
        for index,name,bar_box,thumb_box,bar_size,thumb_size in (
            (10,'horizontal',htrough,hthumb,(280,15),(70,11)),
            (11,'vertical',vtrough,vthumb,(15,180),(11,45))):
            # The recipe state belongs to one selected control. All other
            # controls remain normal, including their KDE role selection.
            control_state=state_value if index==selected else 0
            state_name={0:'normal',1:'pressed',2:'disabled',3:'backdrop'}[control_state]
            effective=_effective_palette(art,colors,state_name)
            bar=actual.crop(bar_box)
            expected_bar=expected('trough',*bar_size,True,effective)
            mask=(thumb_box[0]-bar_box[0],thumb_box[1]-bar_box[1],
                  thumb_box[2]-bar_box[0],thumb_box[3]-bar_box[1])
            differences=0
            for y in range(bar.height):
                for x in range(bar.width):
                    if mask[0]<=x<mask[2] and mask[1]<=y<mask[3]:continue
                    differences+=bar.getpixel((x,y))!=expected_bar.getpixel((x,y))
            thumb=actual.crop(thumb_box)
            # edit_state applies only to selected_control; the other bar stays
            # normal. GTK's real adjustment/session semantics remain intact.
            thumb_fill=expected('face',*thumb_size,control_state==1,effective)
            thumb_differences=sum(a!=b for a,b in zip(thumb.getdata(),thumb_fill.getdata()))
            comparisons.append({'part':name,'control_state':control_state,
                                'trough_non_thumb_differences':differences,
                                'thumb_differences':thumb_differences,
                                'trough_pixels_compared':bar.width*bar.height-thumb.width*thumb.height,
                                'thumb_pixels_compared':thumb.width*thumb.height})
            assert differences==0 and thumb_differences==0,comparisons[-1]
        return {'state':state_value,'capture':str(path),
                'capture_sha256':backend.sha(backend.read_file(path)),
                'pixel_comparisons':comparisons}

    log_path=home/'scrollbar-worker.log'
    with log_path.open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        try:
            initial=wait(state)
            assert initial['embedded']==(host is not None)
            assert initial['scrollbar_values']=={'10':25.0,'11':25.0}
            metrics=wait(lambda:next((row for row in rows()
                if row['action']=='metrics' and row['project_sha256']==digest),None))
            native=metrics['metrics']
            assert [row['index'] for row in native]==[10,11],native
            expected_allocations=[[32,32,280,15],[vertical_x,32,15,180]]
            assert [row['allocation'] for row in native]==expected_allocations,native
            for row in native:
                assert row['font_kind']==2 and row['font_not_applicable']
                assert row['font_description']==''
                assert row['scrollbar_style_class_present']
                assert row['native_minimum_before_custom_size']
            assert all(row['scale_factor']==1 for row in native)

            builder=backend.load_builder(ROOT)
            snapshot_folder=Path(receipt['snapshot'])
            saved_colors=json.loads((snapshot_folder/'GTK4-NATIVE-COLORS.json').read_text())['colors']
            initial_state=proposal['recipes']['gtk4']['edit_state']
            state_pixels=[capture_and_compare(initial['window'],initial_state,
                                              saved_colors,builder,proposal)]

            # The GTK4 scrollbar has no arrows: a real wheel event must still
            # update the native GtkAdjustment and persist a native event.
            window=str(initial['window'])
            state_value=initial_state
            chosen=next(row for row in native if row['index']==10)
            assert chosen['forced_state']==state_value,chosen
            if state_value==0:
                assert chosen['sensitive'] and not (chosen['state_flags']&64)
                assert not chosen['forced_pressed_class_present']
            elif state_value==1:
                assert chosen['sensitive'] and chosen['forced_pressed_class_present']
            elif state_value==2:
                assert not chosen['sensitive']
            else:
                assert chosen['sensitive'] and (chosen['state_flags']&64)
            state_proofs=[{'state':state_value,'allocation':chosen['allocation'],
                           'sensitive':chosen['sensitive'],
                           'state_flags':chosen['state_flags'],
                           'forced_pressed_class':chosen['forced_pressed_class_present']}]
            changed=None
            changed_state=state()
            if state_value==0:
                # Native wheel movement is separately verified in the normal
                # state; forced disabled/backdrop/pressed captures stay stable.
                subprocess.run(['xdotool','mousemove','--window',window,'100','40',
                                'click','5'],check=True,timeout=5)
                changed=wait(lambda:next((event for event in rows()
                    if event['action']=='native' and event['control_index']==10),None),10)
                assert changed['state']['value']!=25.0,changed
                assert changed['origin']==('coupled' if host else 'separate')
                changed_state=wait(lambda:(lambda current:
                    current if current['scrollbar_values']['10']!=25.0 else None)(state()),10)
                if os.environ.get('T04_SCROLLBAR_RERENDER')=='1':
                    for next_state in (1,2,3,0):
                        changed_project=copy.deepcopy(proposal)
                        changed_project['recipes']['gtk4']['edit_state']=next_state
                        backend.write_json(project_path,changed_project)
                        proposal,new_digest=backend.project(project_path)
                        event=wait(lambda:next((row for row in rows()
                            if row['action']=='metrics' and row['project_sha256']==new_digest),None),45)
                        selected_row=next(row for row in event['metrics'] if row['index']==10)
                        assert selected_row['forced_state']==next_state,selected_row
                        if next_state==0:
                            assert selected_row['sensitive'] and not (selected_row['state_flags']&64)
                            assert not selected_row['forced_pressed_class_present']
                        elif next_state==1:
                            assert selected_row['sensitive'] and selected_row['forced_pressed_class_present']
                        elif next_state==2:
                            assert not selected_row['sensitive']
                        else:
                            assert selected_row['sensitive'] and (selected_row['state_flags']&64)
                        assert [row['allocation'] for row in event['metrics']]==expected_allocations
                        # Move away from the overlay scrollbar after wheel input;
                        # GTK reveals only the bar under the pointer in this mode.
                        subprocess.run(['xdotool','mousemove','--window',window,'500','300'],
                                       check=True,timeout=5)
                        time.sleep(.2)
                        state_pixels.append(capture_and_compare(initial['window'],next_state,
                                      saved_colors,builder,proposal))
                        chosen=selected_row
                        state_proofs.append({'state':next_state,'allocation':chosen['allocation'],
                              'sensitive':chosen['sensitive'],'state_flags':chosen['state_flags'],
                              'forced_pressed_class':chosen['forced_pressed_class_present']})
                        changed_state=state()

            # Capture the final normal state as evidence from the actual GTK4
            # child surface, preserving the same scale and palette used above.
            process.terminate()
            result_code=process.wait(timeout=8)
            assert result_code==0,result_code
            final=json.loads((events/'WORKER.json').read_text(encoding='utf-8'))
            assert final['status']=='closed'
            result={'status':'passed_scoped_gtk4_scrollbar_worker',
                    'origin':'coupled' if host else 'separate','guards':guards,
                    'gtk4_version':generated['families']['gtk4'].get('gtk_version'),
                    'selected_scheme':receipt['selected_scheme'],
                    'native_controls':native,'wheel_event':changed,
                    'state_after_wheel':changed_state['scrollbar_values'],
                    'state_proofs':state_proofs,
                    'state_pixel_proofs':state_pixels,
                    'worker_log':str(log_path),'closed_exit_code':result_code,
                    'renderer_flags_explicit':True,'native_input_preserved':True,
                    'gtk4_arrows_synthesized':False,
                    'historical_fidelity_claimed':False}
            backend.write_json(home/'SCROLLBAR-WORKER-RESULTADO.json',result)
            print(json.dumps(result,ensure_ascii=False),flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=8)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            if host:host.close()


if __name__=='__main__':main()
