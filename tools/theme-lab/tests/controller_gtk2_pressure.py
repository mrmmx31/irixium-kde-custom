# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Motif controller pressure edits, history, persistence and native paint."""
import io
import json
from pathlib import Path
import re
import subprocess
import time
from PIL import Image
from test_backend import backend, ROOT


def run(output, observation, click, wait, move_separate, environment, restart, file_dialog, control=0, dimensions=(180,50)):
    working = output/'home/lab/working.json'
    scene = output/'home/lab/scene.json'
    builder = backend.load_builder(ROOT)
    captures = []
    width, height = dimensions
    def native():
        rows = [r for r in observation().get('native_controls', []) if r['control'] == control]
        return rows if len(rows) == 2 and all((r['width'], r['height']) == dimensions for r in rows) else None
    def applied(state):
        return scene.exists() and json.loads(scene.read_text())['recipes']['gtk2']['edit_state'] == state
    def paint(state, label):
        rows = native()
        if not rows or not applied(state):
            return False
        index = json.loads((output/'home/lab/generated/latest.json').read_text())
        folder = output/'home'/index['generation_dir'].removeprefix('/home/domainos-test/')
        colors = json.loads((folder/'GTK2-NATIVE-COLORS.json').read_text())['colors']
        recipe = json.loads(scene.read_text())['recipes']['gtk2']
        from controller_gtk2_windows import native_windows
        windows = native_windows(observation, environment)
        if len(windows) != 2:
            return False
        # Apply can replace the detached child at its default (0,0), covering
        # the Motif-hosted Plug. Capture only after placing that owned window
        # beside the host; covered X11 pixels are not a painting comparison.
        move_separate()
        matches = []
        for window in windows:
            tree = subprocess.check_output(['xwininfo','-id',window,'-tree'],env=environment,text=True,timeout=5)
            root = re.search(r'Root window id: (0x[0-9a-f]+)',tree)
            parent = re.search(r'Parent window id: (0x[0-9a-f]+)',tree)
            separate = root[1] == parent[1]
            row = next(r for r in rows if bool(r['separate']) == separate)
            path = output/('%s-%s-%s.png' % (label, 'separate' if separate else 'coupled', len(captures)))
            subprocess.run(['import','-window',window,str(path)],env=environment,check=True,timeout=5)
            x,y,w,h = row['x'],row['y'],row['width'],row['height']
            actual = Image.open(path).convert('RGB').crop((x,y,x+w,y+h))
            shadow = recipe['geometry']['shadow_px']
            with backend.recipe_rules(builder, recipe['palette']):
                pixels = builder.art.bevel(builder.art.blank(w,h,'face'),thickness=shadow,down=bool(state))
                expected = Image.open(io.BytesIO(builder.png(pixels,'button',colors))).convert('RGB')
            edges = [(bx,by) for by in range(h) for bx in range(w)
                     if bx < shadow or by < shadow or bx >= w-shadow or by >= h-shadow]
            delta = sum(actual.getpixel(p) != expected.getpixel(p) for p in edges)
            captures.append({'label':label,'separate':separate,'state':state,'capture':str(path),
                             'edge_pixels':len(edges),'differences':delta})
            (output/'pressure-pixels.json').write_text(json.dumps(captures,indent=2)+'\n')
            matches.append(delta == 0)
        return all(matches)
    wait(lambda: observation().get('window'))
    # Establish startup separately from opening the second origin; combining
    # both schedules two generations and obscures which stage failed.
    wait(lambda: any(r['control'] == control and not r['separate'] and
                    (r['width'],r['height']) == dimensions
                    for r in observation().get('native_controls', [])))
    initial = json.loads(working.read_text())
    click('separatePreview')
    wait(native)
    move_separate()
    wait(lambda: paint(0, 'normal'))
    requested_at = time.time_ns()
    (output/'home/reveal-spin').write_text('edit-state')
    wait(lambda: not (output/'home/reveal-spin').exists() and
         (output/'home/probe.json').stat().st_mtime_ns > requested_at)
    # Xvfb has no window manager: a pointer click does not establish normal
    # desktop keyboard focus. Give the owned Motif shell explicit focus.
    subprocess.run(['xdotool','windowfocus',str(observation()['window'])],
                   env=environment,check=True,timeout=5)
    # The read-only field does not open the XmComboBox popup. Click its
    # drop-down arrow, then select using the native list's keyboard input.
    x,y,w,h = observation()['edit_state_arrow']
    subprocess.run(['xdotool','mousemove',str(x+w//2),str(y+h//2),'click','1'],
                   env=environment,check=True,timeout=5)
    wait(lambda: observation().get('edit_state_pressed_item'), 5)
    x,y,w,h = observation()['edit_state_pressed_item']
    subprocess.run(['xdotool','mousemove',str(x+w//2),str(y+h//2),'click','1'],
                   env=environment,check=True,timeout=5)
    wait(lambda: json.loads(working.read_text())['recipes']['gtk2']['edit_state'] == 1)
    assert applied(0), 'Editing must not apply implicitly'
    click('apply')
    wait(lambda: paint(1, 'pressed'))
    click('projectUndo')
    wait(lambda: json.loads(working.read_text())['recipes']['gtk2']['edit_state'] == 0)
    assert applied(1), 'Undo must preserve the separately applied scene'
    click('apply')
    wait(lambda: paint(0, 'undo'))
    move_separate()
    click('projectRedo')
    wait(lambda: json.loads(working.read_text())['recipes']['gtk2']['edit_state'] == 1)
    assert applied(0), 'Redo must preserve the separately applied scene'
    click('apply')
    wait(lambda: paint(1, 'redo'))
    move_separate()
    file_dialog('save','/home/domainos-test/pressure-project.json')
    saved = json.loads((output/'home/pressure-project.json').read_text())
    assert saved['recipes']['gtk2']['edit_state'] == 1 and saved['separate_preview']
    before = scene.read_bytes()
    restart()
    wait(native)
    move_separate()
    wait(lambda: paint(1, 'restart'))
    assert scene.read_bytes() == before
    file_dialog('load','/home/domainos-test/pressure-project.json')
    wait(lambda: paint(1, 'loaded'))
    restored = json.loads(working.read_text())
    assert restored['recipes'] == saved['recipes']
    assert all(restored['recipes'][f] == r for f,r in initial['recipes'].items() if f != 'gtk2')
    return {'status':'passed','scope':'Real Motif controller, pointer selection of measured native list item, Apply, Undo/Redo, Save/Load and restart; native GTK2 edge paint in both origins.',
            'control':control,'dimensions':list(dimensions),'captures':captures,'other_recipes_preserved':True,'historical_fidelity_claimed':False}
