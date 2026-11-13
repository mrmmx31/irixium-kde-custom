# SPDX-License-Identifier: GPL-3.0-or-later
"""Real grouped radio input and painting after Motif controller Apply."""
import json
import re
import subprocess
from PIL import Image


def run(output, observation, click, wait, environment):
    def command(*argv):
        return subprocess.check_output(argv,env=environment,text=True,timeout=10)

    def windows():
        process=subprocess.run(['xdotool','search','--onlyvisible','--name',
                                'Theme Lab — GTK2 nativo'],
                               env=environment,text=True,capture_output=True,timeout=5)
        if process.returncode not in (0,1):raise RuntimeError(process.stderr)
        found={}
        for xid in process.stdout.split():
            tree=command('xwininfo','-id',xid,'-tree')
            root=re.search(r'Root window id: (0x[0-9a-f]+)',tree)
            parent=re.search(r'Parent window id: (0x[0-9a-f]+)',tree)
            origin='separate' if root and parent and root[1]==parent[1] else 'coupled'
            stats=command('xwininfo','-id',xid)
            found[origin]=(xid,int(re.search(r'Absolute upper-left X:\s*(-?\d+)',stats)[1]),
                               int(re.search(r'Absolute upper-left Y:\s*(-?\d+)',stats)[1]))
        return found

    def measured(width,height,both=False):
        rows=[r for r in observation().get('native_controls',[]) if r['control']==3]
        return rows if len(rows)==(2 if both else 1) and all(
            (r['width'],r['height'])==(width,height) and r['font_kind']==1 and r['font']
            and r['natural_width']>0 and r['natural_height']>0 for r in rows) else None

    def generated():
        index=json.loads((output/'home/lab/generated/latest.json').read_text())
        return output/'home'/index['generation_dir'].removeprefix('/home/domainos-test/')

    def selected(origin,member,height):
        entries=windows()
        if origin not in entries:return False
        _,x,y=entries[origin]
        path=output/('radio-'+origin+'-observed.png')
        subprocess.run(['import','-window','root',str(path)],env=environment,check=True,timeout=10)
        actual=Image.open(path).convert('RGB')
        geometry=json.loads((output/'home/lab/scene.json').read_text())['recipes']['gtk2']['geometry']
        glyph=geometry['arrow_px'];spacing=geometry['control_padding_px']
        center=glyph//2
        runtime_path=output/'home/lab/preview-events'/('runtime-gtk2-'+origin+'.json')
        try:
            runtime=json.loads(runtime_path.read_text())['states']
        except (OSError,KeyError,json.JSONDecodeError):
            return False
        if runtime.get('radio') != member:
            return False
        for index in (0,1):
            asset=Image.open(generated()/'gtk2-scrollbars'/
                            ('radio-normal'+('-selected' if index==member else '')+'.png')).convert('RGBA')
            # Radio assets are 15px indicators; unselected pixels are partly
            # transparent, so compare the opaque glyph over the live scheme
            # background and use the indicator's own center, not arrow_px.
            asset_center=asset.width//2
            indicator_x=x+260+spacing+center
            indicator_y=y+20+(height//2-glyph)//2+center+index*(height//2)
            left,top=indicator_x-asset_center,indicator_y-asset_center
            for ay in range(asset.height):
                for ax in range(asset.width):
                    red,green,blue,alpha=asset.getpixel((ax,ay))
                    if alpha and actual.getpixel((left+ax,top+ay))!=(red,green,blue):
                        return False
        return True

    def native_click(origin,member,height):
        _,x,y=windows()[origin]
        subprocess.run(['xdotool','mousemove',str(x+320),str(y+20+height//4+member*(height//2)),
                        'click','1','mousemove','2190','1190'],env=environment,check=True,timeout=10)

    wait(lambda:measured(180,100))
    wait(lambda:selected('coupled',0,100))
    native_click('coupled',1,100);wait(lambda:selected('coupled',1,100))
    click('separatePreview');wait(lambda:measured(180,100,True))
    command('xdotool','windowmove',windows()['separate'][0],'1400','0')
    wait(lambda:selected('separate',0,100))
    native_click('separate',1,100);wait(lambda:selected('separate',1,100))
    native_click('separate',0,100);wait(lambda:selected('separate',0,100))
    command('xdotool','sleep','1')
    (output/'home/reveal-spin').write_text('set-width 280')
    wait(lambda:observation().get('width_text')=='280')
    (output/'home/reveal-spin').write_text('set-height 120')
    wait(lambda:observation().get('height_text')=='120')
    click('apply');changed=wait(lambda:measured(280,120,True))
    command('xdotool','windowmove',windows()['separate'][0],'1400','0')
    wait(lambda:selected('coupled',1,120))
    wait(lambda:selected('separate',0,120))
    native_click('coupled',0,120);wait(lambda:selected('coupled',0,120))
    native_click('separate',1,120);wait(lambda:selected('separate',1,120))
    project=json.loads((output/'home/lab/working.json').read_text())
    assert project['recipes']['gtk2']['sizes'][3]==[280,120]
    assert project['recipes']['gtk3']['sizes'][0]==[220,80]
    return {'status':'passed','scope':'Native GTK2 grouped radio via real Motif controller',
            'group_after_apply':changed,'independent_member_preserved_after_restart':True,
            'both_origins_clickable_after_restart':True,'gtk3_recipe_preserved':True,
            'pixel_assertion':'Native center pixel of both indicators matched selected/unselected generated role assets',
            'historical_fidelity_claimed':False}
