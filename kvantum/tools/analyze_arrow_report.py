#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read a four-path JSON and separate observed pressure failure from invalid targets.

Only reads the named file; does not run tests, edit configuration or repair KDE.
The printed assessment is not proof of which module an unrelated app has loaded.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from arrow_probe_logic import intersect_rect


def analyse(doc):
    if doc.get('kind')!='four_path_arrow_comparison':raise ValueError('Tipo de relatório não reconhecido.')
    probes=doc.get('probes',{});out={'style':doc.get('style'),'paths':{}}
    for name,probe in probes.items():
        result=probe.get('result',{})
        rows=[]
        for c in result.get('checks',[]):
            key=c.get('arrow') or ('up' if c.get('direction')=='subtract' else 'down')
            h=c.get('held_states') or c.get('held') or {}
            r=c.get('released_states') or c.get('released') or {}
            active=h.get('activeControl') if isinstance(h,dict) else None
            if isinstance(h,dict) and active is None:
                candidates=[s for s in h.get('styleItems',[]) if s.get('visible') and s.get('opacity',0)>0]
                active=next((s.get('active') for s in candidates if s.get('active')!='none'), None)
            validity=c.get('valid_target')
            if validity is None and name!='widgets':
                # Legacy records didn't observe the recipient: mismatches disqualify a
                # target, while matching hover alone is not a full validation.
                validity=False if active is not None and active!=key else None
            sunken=c.get('held_sunken')
            if sunken is None and isinstance(h,dict):
                sunken=h.get('sunken')
                if sunken is None and h.get('styleItems') is not None:
                    sunken=any(s.get('sunken') and s.get('visible') and s.get('opacity',0)>0 for s in h['styleItems'])
            movement=c.get('motion_ok') if 'motion_ok' in c else c.get('motion')=='ok' if 'motion' in c else None
            rows.append({'orientation':c.get('orientation'),'arrow':key,
                'motion_reported':movement,'held_sunken':sunken,
                'released_sunken':c.get('released_sunken'),
                'active_observed':active,'target_validated':validity,
                'arrow_pixels_changed':c.get('arrow_pixels_changed'),
                'passed_reported':c.get('passed'),
                'assessment':'invalid_target_observed' if validity is False else
                    'motion_and_pixels_observed' if name=='widgets' and movement and c.get('arrow_pixels_changed') else
                    'motion_and_pressure_observed' if movement and sunken else
                    'motion_without_pressure_observed' if movement and sunken is False else 'inconclusive'})
        out['paths'][name]={'returncode':probe.get('returncode'),'checks':rows}
    old=probes.get('quick_installed',{}).get('result',{}).get('checks',[])
    def rect(which):
        for c in old:
            h=c.get('held_states') or {}
            if c.get('orientation')==which and all(k in h for k in ('x','y','width','height')):
                return {k:h[k] for k in ('x','y','width','height')}
        return None
    v,h=rect('vertical'),rect('horizontal')
    if v and h:
        overlap=intersect_rect(v,h)
        if overlap['width']>0 and overlap['height']>0:
            out['legacy_scene_overlap']={'vertical':v,'horizontal':h,'intersection':overlap,
                'finding':'Logged test-bar rectangles overlap; this does not establish an overlap in an unrelated KDE application.'}
    out['notes']=['The legacy temporary-fix tests with activeControl=upPage did not establish arrow-down behavior.',
        'The on-disk inventory and installed application loading are separate observations.',
        'No inference of a broken mouse or a Wayland-wide failure is made.']
    return out


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('arquivo',type=Path);a=p.parse_args(argv)
    raw=a.arquivo.read_bytes()
    if len(raw)>10_000_000:raise ValueError('Relatório maior que o limite de 10 MB.')
    result=analyse(json.loads(raw));result['input_sha256']=hashlib.sha256(raw).hexdigest()
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':
    import sys
    try:sys.exit(main())
    except (OSError,ValueError,TypeError,KeyError) as exc:print('ERRO:',exc,file=sys.stderr);sys.exit(1)
