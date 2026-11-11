# SPDX-License-Identifier: GPL-3.0-or-later
"""Native before-Motif / GTK4-button / after-Motif keyboard traversal."""
import json
import subprocess
from gtk4_focus import FocusKeys
from gtk4_push_api import PushAPI
from gtk4_push_session import PushSession
from test_backend import model


def verify_focus(window, window_id, host, builder, palette, output, drain):
    project = model()
    project['recipes']['gtk4'].update(
        visible_controls=1, selected_control=0, edit_state=0,
        sizes=[[160,60]] + [[0,0] for _ in range(15)],
        positions=[[32,32]] + [[0,0] for _ in range(15)])
    clicked = []
    session = PushSession(PushAPI(), window, builder, clicked.append)
    keys = None
    try:
        session.replace(project, palette, output / 'focus-scene')
        keys = FocusKeys(window, host.bridge)
        drain()
        before = host.focus_widgets['before']
        subprocess.run(['import','-window',str(host.focus_widgets['shell']),
                        str(output/'motif-focus-host.png')],check=True,timeout=5)
        # Xvfb has no WM to focus a shell on mouse click. Establish only the
        # initial Motif shell focus; every subsequent crossing must be native.
        subprocess.run(['xdotool','windowfocus','--sync',str(host.focus_widgets['shell'])],
                       check=True,timeout=5)
        subprocess.run(['xdotool','mousemove','--window',str(before),'10','10','click','1'],
                       check=True, timeout=5)
        drain(); assert json.loads(host.read_line())['activated']=='before'
        subprocess.run(['xdotool','key','Tab'],check=True,timeout=5)
        drain()
        (output/'FOCUS_TRACE.json').write_text(json.dumps({
            'stage':'entered_from_before','input_focus':subprocess.check_output(
                ['xdotool','getwindowfocus','-f'],text=True,timeout=5).strip(),
            'gtk4_window':window_id,'requests':keys.requests,'error':keys.last_error},indent=2)+'\n')
        subprocess.run(['xdotool','key','space'],check=True,timeout=5)
        drain(); assert clicked==[0],clicked
        subprocess.run(['xdotool','key','Tab'],check=True,timeout=5)
        drain()
        (output/'EXIT_TRACE.json').write_text(json.dumps({
            'input_focus':subprocess.check_output(['xdotool','getwindowfocus','-f'],text=True,timeout=5).strip(),
            'requests':keys.requests,'error':keys.last_error,
            'host_ack':subprocess.check_output(['xprop','-id',str(host.canvas),
                '_THEME_LAB_GTK4_TRAVERSE_RESULT'],text=True,timeout=5)},indent=2)+'\n')
        subprocess.run(['xdotool','key','space'],check=True,timeout=5)
        drain(); assert json.loads(host.read_line())['activated']=='after'
        assert host.bridge.traversal_result()=={'sequence':1,'completed':True}
        subprocess.run(['xdotool','key','shift+Tab'],check=True,timeout=5)
        drain()
        subprocess.run(['xdotool','key','space'],check=True,timeout=5)
        drain(); assert clicked==[0,0],clicked
        subprocess.run(['xdotool','key','shift+Tab'],check=True,timeout=5)
        drain()
        subprocess.run(['xdotool','key','space'],check=True,timeout=5)
        drain(); assert json.loads(host.read_line())['activated']=='before'
        assert host.bridge.traversal_result()=={'sequence':2,'completed':True}
        assert keys.last_error is None
        assert keys.requests==[False,True],keys.requests
        return {'forward':'Motif before → GTK4 → Motif after',
                'backward':'Motif after → GTK4 → Motif before',
                'gtk4_keyboard_activations':2,'motif_activations':['before','after','before'],
                'boundary_requests':[False,True],'callback_error':None}
    finally:
        if keys:keys.close()
        session.close()
