# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK4 push through the real C controller, with native pointer input."""
import json
import re
import subprocess
from PIL import Image, ImageColor


def run(output, observation, click, wait, environment, restart, file_dialog):
    def measured(width, height, count):
        rows=[r for r in observation().get('native_controls',[]) if r['control']==0]
        if len(rows)!=count or any((r['width'],r['height'])!=(width,height) or
                                  r['font_kind']!=1 or not r['font'] for r in rows):
            return None
        return rows

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

    def working():
        return json.loads((output/'home/lab/working.json').read_text())

    initial=wait(lambda:measured(180,50,1))
    click('separatePreview')
    both=wait(lambda:measured(180,50,2))
    pair=wait(lambda:windows() if len(windows())==2 else None)
    subprocess.run(['xdotool','windowmove',pair['separate'],'1400','0'],env=environment,check=True,timeout=5)
    subprocess.run(['xdotool','mousemove','--window',pair['coupled'],'100','60',
                    'keydown','Control_L','mousedown','1','mousemove','--window',pair['coupled'],'120','80',
                    'sleep','0.2','mouseup','1','keyup','Control_L'],env=environment,check=True,timeout=5)
    wait(lambda:working()['recipes']['gtk4']['positions'][0]==[52,52])
    wait(lambda:measured(180,50,2))
    assert observation().get('projectUndo_sensitive')
    click('projectUndo')
    wait(lambda:working()['recipes']['gtk4']['positions'][0]==[32,32])
    click('apply');wait(lambda:measured(180,50,2))
    click('projectRedo')
    wait(lambda:working()['recipes']['gtk4']['positions'][0]==[52,52])
    click('apply');wait(lambda:measured(180,50,2))
    (output/'home/reveal-spin').write_text('set-width 280')
    wait(lambda:observation().get('width_text')=='280')
    (output/'home/reveal-spin').write_text('set-height 60')
    wait(lambda:observation().get('height_text')=='60')
    click('apply')
    changed=wait(lambda:measured(280,60,2))
    assert working()['recipes']['gtk3']['sizes'][0]==[220,80]
    assert 'GTK4 acoplado' in observation().get('metrics','')
    assert 'GTK4 separado' in observation().get('metrics','')
    wait(lambda:'background-size:' in observation().get('code','') and
         'button.theme-lab-gtk4-push-' in observation().get('code',''))
    file_dialog('save','/home/domainos-test/gtk4-project.json')
    saved=json.loads((output/'home/gtk4-project.json').read_text())
    assert saved['recipes']['gtk4']['sizes'][0]==[280,60]
    assert saved['recipes']['gtk4']['positions'][0]==[52,52]
    before=(output/'home/lab/scene.json').read_bytes()
    restart();restarted=wait(lambda:measured(280,60,2))
    assert (output/'home/lab/scene.json').read_bytes()==before
    file_dialog('load','/home/domainos-test/gtk4-project.json')
    loaded=wait(lambda:measured(280,60,2))
    assert working()['recipes']==saved['recipes']
    pair=wait(lambda:windows() if len(windows())==2 else None)
    subprocess.run(['xdotool','windowmove',pair['separate'],'1400','0'],env=environment,check=True,timeout=5)
    click('separatePreview')
    wait(lambda:measured(280,60,1))
    wait(lambda:'separate' not in windows())
    latest=json.loads((output/'home/lab/generated/latest.json').read_text())
    folder=output/'home'/latest['generation_dir'].removeprefix('/home/domainos-test/')
    colors=json.loads((folder/'gtk4-snapshot/GTK4-NATIVE-COLORS.json').read_text())['colors']
    expected=[
        [ImageColor.getrgb(colors['theme_bg_color_breeze']),
         ImageColor.getrgb(colors['theme_button_background_normal_breeze'])],
        [ImageColor.getrgb(colors['theme_unfocused_bg_color_breeze']),
         ImageColor.getrgb(colors['theme_button_background_backdrop_breeze'])]]
    capture=output/'gtk4-coupled-painted.png'
    def painted():
        pair=windows()
        if 'coupled' not in pair:return None
        subprocess.run(['import','-window',pair['coupled'],str(capture)],
                       env=environment,check=True,timeout=5)
        with Image.open(capture) as image:
            image=image.convert('RGB')
            pixels=[image.getpixel((4,4)),image.getpixel((62,62))]
        return pixels if pixels in expected else None
    pixels=wait(painted,8)
    return {'status':'passed','scope':'C controller GTK4 push Apply, physical move, Undo/Redo and origins',
            'initial':initial,'both':both,'after_apply':changed,'native_drag_saved':[52,52],
            'undo_position':[32,32],'redo_position':[52,52],
            'other_family_preserved':True,'detached_closed_coupled_retained':True,
            'save_load_and_restart':True,'scene_bytes_preserved_after_restart':True,
            'restart_metrics':restarted,'load_metrics':loaded,'gtk4_css_visible_in_code_panel':True,
            'canvas_and_button_pixels_match_current_roles':pixels,
            'historical_fidelity_claimed':False}
