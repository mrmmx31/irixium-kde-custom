# SPDX-License-Identifier: GPL-3.0-or-later
"""Parse selected toggle fragments with real GTK4 and real snapshot dependencies."""
import ctypes as C
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools/theme-lab'),str(ROOT/'tools/theme-lab/tests')]
import backend
from test_backend import model
from gtk4_generation import generate_snapshot,verify_snapshot
from gtk4_push_api import PushAPI,bind


def main():
    guards=backend.private_namespace(ROOT);home=Path(os.environ['HOME'])
    proposal=model();proposal['selected_family']='gtk4'
    proposal['recipes']['gtk4']['visible_controls']=2
    kde=home/'.config/kdeglobals';folder=home/'snapshot'
    receipt=generate_snapshot(ROOT,folder,proposal,'a'*64,kde,allow_toggle=True)
    verify_snapshot(ROOT,folder,proposal,'a'*64,allow_toggle=True)
    bind(C.CDLL('libgtk-4.so.1'),'gtk_init',None)();api=PushAPI();parsed=[]
    for state in ('normal','pressed','disabled','backdrop','hover'):
        result=backend.snippet(ROOT,proposal,'gtk4','toggle',state,kde)
        fragment=Path(receipt['css']).parent/('fragment-'+state+'.css')
        fragment.write_text(result['source'],encoding='utf-8')
        provider=api.css_provider(fragment);api.unref(provider);parsed.append(state)
    backend.write_json(home/'WORKER-RESULTADO.json',{
        'status':'passed_toggle_snippet_parser','guards':guards,'toolkit':'GTK4',
        'parsed_states':parsed,'real_snapshot_dependencies':True,
        'widget_painting_claimed':False,'historical_fidelity_claimed':False})


if __name__=='__main__':main()
