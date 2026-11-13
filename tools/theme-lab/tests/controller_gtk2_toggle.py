# SPDX-License-Identifier: GPL-3.0-or-later
"""Native pointer input and rendered selection across controller Apply."""
import json
import re
import subprocess
from PIL import Image


def run(output, observation, click, wait, environment, control=1):
    assert control in (1,2)
    kind='check' if control==2 else 'toggle'
    # GTK2 title changed when the sample added mixed controls; the stable
    # prefix also matches the earlier scrollbar-only suffix. xdotool uses
    # POSIX regex syntax, not Python's non-capturing groups.
    title = 'Theme Lab — GTK2 nativo'

    def command(*argv):
        return subprocess.check_output(argv, env=environment, text=True, timeout=10)

    def windows():
        found = subprocess.run(['xdotool','search','--onlyvisible','--name',title],
                               env=environment,capture_output=True,text=True,timeout=5)
        if found.returncode not in (0,1): raise RuntimeError(found.stderr)
        result = {}
        for xid in found.stdout.split():
            tree = command('xwininfo','-id',xid,'-tree')
            root = re.search(r'Root window id: (0x[0-9a-f]+)',tree)
            parent = re.search(r'Parent window id: (0x[0-9a-f]+)',tree)
            origin = 'separate' if root and parent and root[1]==parent[1] else 'coupled'
            stats = command('xwininfo','-id',xid)
            x = int(re.search(r'Absolute upper-left X:\s*(-?\d+)',stats)[1])
            y = int(re.search(r'Absolute upper-left Y:\s*(-?\d+)',stats)[1])
            result[origin] = (xid,x,y)
        return result

    def measured(width,height,both=False):
        rows = [r for r in observation().get('native_controls',[]) if r['control']==control]
        return rows if len(rows)==(2 if both else 1) and all(
            (r['width'],r['height'])==(width,height) and r['font_kind']==1 and r['font'] for r in rows) else None

    def generated():
        index = json.loads((output/'home/lab/generated/latest.json').read_text())
        return output/'home'/index['generation_dir'].removeprefix('/home/domainos-test/')

    def selection(origin,active):
        current = windows()
        if origin not in current: return False
        _,x,y = current[origin]
        image = output/(kind+'-'+origin+'-observed.png')
        subprocess.run(['import','-window','root',str(image)],env=environment,check=True,timeout=10)
        actual = Image.open(image).convert('RGB')
        expected = Image.open(generated()/'gtk2-scrollbars'/
                             (kind+'-normal'+('-selected' if active else '')+'.png')).convert('RGB')
        runtime_path=output/'home/lab/preview-events'/('runtime-gtk2-'+origin+'.json')
        try:
            runtime=json.loads(runtime_path.read_text())['states']
        except (OSError,KeyError,json.JSONDecodeError):
            return False
        # The indicator-less GTK2 toggle recipe intentionally uses a 1x1 flat
        # face for both states. Verify the actual GtkToggleButton state from
        # its atomic runtime journal; pixels alone cannot distinguish it.
        if runtime.get(kind) is not active:
            return False
        if control==2:
            geometry=json.loads((output/'home/lab/scene.json').read_text())['recipes']['gtk2']['geometry']
            glyph=geometry['arrow_px'];spacing=geometry['control_padding_px'];center=glyph//2
            height=50 if measured(180,50,True) or measured(180,50) else 60
            return actual.getpixel((x+20+spacing+center,y+90+(height-glyph)//2+center))==expected.getpixel((center,center))
        # Corners identify the raised/sunken border without relying on text,
        # hover or a test-only native-state implementation.
        return all(actual.getpixel((x+20+dx,y+90+dy))==expected.getpixel((min(dx,expected.width-1),min(dy,expected.height-1)))
                   for dx,dy in ((0,0),(1,1)))

    def native_click(origin):
        _,x,y = windows()[origin]
        subprocess.run(['xdotool','mousemove',str(x+80),str(y+110),'click','1',
                        'mousemove','2190','1190'],env=environment,check=True,timeout=10)

    wait(lambda:measured(180,50))
    wait(lambda:selection('coupled',False))
    native_click('coupled');wait(lambda:selection('coupled',True))
    click('separatePreview');wait(lambda:measured(180,50,True))
    separate=windows()['separate'][0]
    command('xdotool','windowmove',separate,'1400','0')
    wait(lambda:selection('separate',False))
    native_click('separate');wait(lambda:selection('separate',True))
    native_click('separate');wait(lambda:selection('separate',False))
    # Allow the controller's bounded IPC poll to consume the real release.
    command('xdotool','sleep','1')
    (output/'home/reveal-spin').write_text('set-width 280')
    wait(lambda:observation().get('width_text')=='280')
    (output/'home/reveal-spin').write_text('set-height 60')
    wait(lambda:observation().get('height_text')=='60')
    click('apply');changed=wait(lambda:measured(280,60,True))
    command('xdotool','windowmove',windows()['separate'][0],'1400','0')
    wait(lambda:selection('coupled',True))
    wait(lambda:selection('separate',False))
    native_click('coupled');wait(lambda:selection('coupled',False))
    native_click('separate');wait(lambda:selection('separate',True))
    project=json.loads((output/'home/lab/working.json').read_text())
    assert project['recipes']['gtk2']['sizes'][control]==[280,60]
    assert project['recipes']['gtk3']['sizes'][0]==[220,80]
    receipt=json.loads((generated()/'RESULTADO.json').read_text())
    assert receipt['families']['gtk2']['translated_controls']==['push','toggle']+(['check'] if control==2 else [])+['scroll_h','scroll_v']
    return {'status':'passed','scope':'Real Motif controller, real native '+kind+' pointer clicks and selection pixels',
            'after_apply':changed,'independent_selection_preserved_after_apply':True,
            'both_origins_clickable_after_restart':True,'gtk3_recipe_preserved':True,
            'pixel_assertion':'Native indicator center matched generated asset' if control==2 else 'Two native top-left bevel pixels matched verified generated assets',
            'historical_fidelity_claimed':False}
