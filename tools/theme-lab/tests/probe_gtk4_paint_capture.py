# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise GTK4 Paint captures through the production native worker."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools/theme-lab'),str(ROOT/'tools/theme-lab/tests')]
import backend
from test_backend import model


def png_size(path):
    data=Path(path).read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    return struct.unpack('>II',data[16:24])


def main():
    backend.private_namespace(ROOT)
    home=Path(os.environ['HOME'])
    project=home/'gtk4-paint-project.json'
    sample_events=backend.private_output(home/'gtk4-paint-events',ROOT)
    proposal=model();proposal['selected_family']='gtk4'
    recipe=proposal['recipes']['gtk4']
    recipe['visible_categories']=31;recipe['visible_controls']=65535
    recipe['selected_control']=0;recipe['edit_state']=0
    recipe['sizes']=[[0,0] for _ in range(16)]
    recipe['sizes'][0]=[180,60]
    backend.write_json(project,proposal)
    original=backend.read_file(project)
    rows=[]
    cases=[{'control':control,'state':0} for control in (0,1,2,10,11)]
    cases += [{'control':0,'state':state} for state in (1,2,3,4)]
    cases += [
        {'control':10,'state':0,'length':240,'thickness':19,'value':10,'page_size':40},
        {'control':11,'state':0,'length':260,'thickness':17,'value':50,'page_size':25},
    ]
    for case in cases:
        control,state=case['control'],case['state']
        destination=sample_events/('paint-sample-'+uuid.uuid4().hex+'.png')
        command=[sys.executable,'-B',str(ROOT/'tools/theme-lab/preview_gtk4.py'),
                 '--project',str(project),'--root',str(ROOT),'--events-dir',str(sample_events),
                 '--preview-instance',uuid.uuid4().hex,'--snapshot',str(home/'snapshot-from-controller'),
                 '--capture-control',str(control),'--capture-state',str(state),
                 '--capture-output',str(destination)]
        if 'length' in case:
            command += ['--capture-length',str(case['length']),
                        '--capture-thickness',str(case['thickness']),
                        '--capture-value',str(case['value']),
                        '--capture-page-size',str(case['page_size'])]
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=35)
        except subprocess.TimeoutExpired as error:
            stderr=error.stderr.decode(errors='replace') if isinstance(error.stderr,bytes) else (error.stderr or '')
            stdout=error.stdout.decode(errors='replace') if isinstance(error.stdout,bytes) else (error.stdout or '')
            raise RuntimeError('GTK4 sample timed out; stdout='+stdout[-1000:]+' stderr='+stderr[-2000:]) from error
        if result.returncode:
            raise RuntimeError('GTK4 sample failed: '+result.stderr[-2000:])
        payload=json.loads(result.stdout)
        assert payload['status']=='captured',payload
        assert payload['widget_source']=='native_gtk4_x11_surface',payload
        width,height=png_size(destination)
        assert [width,height]==[payload['width'],payload['height']],(payload,width,height)
        if 'length' in case:
            expected=([case['length'],case['thickness']] if control==10
                      else [case['thickness'],case['length']])
            assert [width,height]==expected,(payload,width,height,expected)
            assert payload['scrollbar_probe']=={
                'size':expected,'value':case['value'],'page_size':case['page_size'],
                'part':'whole','direction':'auto',
                'effective':{'value':float(case['value']),
                             'page_size':float(case['page_size'])}},payload
        assert destination.stat().st_mode & 0o777 == 0o600
        rows.append({'control':control,'state':state,'width':width,'height':height,
                     'scale_factor':payload['scale_factor'],'sha256':backend.sha(backend.read_file(destination))})
    assert backend.read_file(project)==original,"Capture modified the user's project JSON."
    unsupported=sample_events/('paint-sample-'+uuid.uuid4().hex+'.png')
    rejected=subprocess.run([sys.executable,'-B',str(ROOT/'tools/theme-lab/preview_gtk4.py'),
        '--project',str(project),'--root',str(ROOT),'--events-dir',str(sample_events),
        '--snapshot',str(home/'unsupported-snapshot'),'--capture-control','3',
        '--capture-output',str(unsupported)],capture_output=True,text=True,timeout=10)
    assert rejected.returncode!=0 and not unsupported.exists()
    unsupported_part=sample_events/('paint-sample-'+uuid.uuid4().hex+'.png')
    rejected_part=subprocess.run([sys.executable,'-B',str(ROOT/'tools/theme-lab/preview_gtk4.py'),
        '--project',str(project),'--root',str(ROOT),'--events-dir',str(sample_events),
        '--snapshot',str(home/'unsupported-part-snapshot'),'--capture-control','10',
        '--capture-part','arrow','--capture-direction','left',
        '--capture-output',str(unsupported_part)],capture_output=True,text=True,timeout=10)
    assert (rejected_part.returncode!=0 and not unsupported_part.exists() and
            'only whole/auto' in rejected_part.stderr and
            'Traceback' not in rejected_part.stderr),rejected_part.stderr
    result={'status':'passed','capture_count':len(rows),
            'native_source':'native_gtk4_x11_surface',
            'controls':[0,1,2,10,11],'push_states':[0,1,2,3,4],
            'unsupported_control_rejected':True,'project_unchanged':True,
            'scrollbar_private_geometry':True,
            'unimplemented_scrollbar_part_rejected':True,
            'private_png_mode':'0600','captures':rows,
            'historical_fidelity_claimed':False}
    backend.write_json(home/'PAINT-CAPTURE-RESULTADO.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
