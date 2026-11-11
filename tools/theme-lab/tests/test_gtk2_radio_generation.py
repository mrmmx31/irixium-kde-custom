# SPDX-License-Identifier: GPL-3.0-or-later
"""Generation parity against existing native radio foundation evidence."""
import argparse
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_backend import model, ROOT
import backend
from gtk2_generation import generate_scrollbar_snapshot


def run(output,reference,yellow,control='radio'):
    output.mkdir(parents=True,exist_ok=True)
    data=model();data['selected_family']='gtk2';data['color_scheme']=''
    data['recipes']['gtk2']['visible_controls']=1|2|(8 if control=='radio' else 4)|(1<<10)|(1<<11)
    before=copy.deepcopy(data)
    sources={'DomainOS':ROOT/'colors/DomainOS-SR10.4.colors',
             'BreezeLight':Path('/usr/share/color-schemes/BreezeLight.colors'),
             'BreezeDark':Path('/usr/share/color-schemes/BreezeDark.colors'),
             'TestYellow':yellow}
    rows=[]
    for name,source in sources.items():
        folder=output/name;folder.mkdir(exist_ok=True)
        receipt=generate_scrollbar_snapshot(backend,ROOT,folder,data,source)
        assert receipt['translated_controls']==['push','toggle',control,'scroll_h','scroll_v']
        assert not receipt['recipe_applied'] and not receipt['scene_integrated']
        rc=(folder/'gtk2-scrollbars'/'gtkrc').read_text()
        if control=='radio':
            assert 'GtkCheckButton::indicator-size = 15' in rc
            assert 'GtkCheckButton::indicator-spacing = 2' in rc
            assert data['recipes']['gtk2']['geometry']['arrow_px']==11
        assets=[n for n in receipt['assets'] if n.startswith(control+'-')]
        assert len(assets)==9
        for asset in assets:
            assert (folder/'gtk2-scrollbars'/asset).read_bytes()==(reference/name/asset).read_bytes(),(name,asset)
        assert backend.palette_inputs_current(receipt)
        rows.append({'scheme':name,'indicator_asset_parity':assets,'provenance_current':True})
    assert data==before
    report={'status':'passed','rows':rows,'control':control,'native_scene_proof_separate':True,'model_unchanged':True}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2)+'\n')
    print('4 palette generations; 36 '+control+' assets identical to native foundation')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--yellow',type=Path,required=True)
    parser.add_argument('--control',choices=('radio','check'),default='radio')
    args=parser.parse_args()
    run(args.output.resolve(),args.reference.resolve(),args.yellow.resolve(),args.control)
