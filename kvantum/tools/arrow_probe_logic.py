# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Evidence rules for the arrow probes. No Qt import or UI mutation here."""
from __future__ import annotations
import math

HARNESS_VERSION = 'integrated-r1'


def point_in_rect(point, rect):
    if not isinstance(point, dict) or not isinstance(rect, dict):
        return False
    try:
        x, y, left, top, width, height = (float(v) for v in
            (point['x'], point['y'], rect['x'], rect['y'], rect['width'], rect['height']))
        return all(math.isfinite(v) for v in (x,y,left,top,width,height)) and width>0 and height>0 and left<=x<left+width and top<=y<top+height
    except (KeyError,TypeError,ValueError):
        return False


def intersect_rect(a,b):
    x,y=max(a['x'],b['x']),max(a['y'],b['y'])
    r,t=min(a['x']+a['width'],b['x']+b['width']),min(a['y']+a['height'],b['y']+b['height'])
    return {'x':x,'y':y,'width':max(0,r-x),'height':max(0,t-y)}


def judge(before, held, released, orientation, arrow):
    """Wrong receiver/target is an invalid test, NOT a failure of the scrollbar."""
    sign=-1 if arrow=='up' else 1
    reasons=[]
    target=before.get('target') or {}
    event=held.get('lastPress') or {}
    if target.get('hit')!=arrow: reasons.append('preflight_hit_mismatch')
    if not target.get('clear',False): reasons.append('target_occluded_or_outside')
    if event.get('bar')!=orientation: reasons.append('wrong_or_missing_receiver')
    if event.get('hit')!=arrow: reasons.append('press_hit_mismatch')
    if event.get('button')!=1: reasons.append('left_press_not_observed')
    delta=held.get('position',0)-before.get('position',0)
    other='contentX' if orientation=='vertical' else 'contentY'
    other_delta=held.get(other,0)-before.get(other,0)
    if abs(other_delta)>1e-6: reasons.append('other_axis_moved')
    valid=not reasons
    result={'orientation':orientation,'arrow':arrow,'valid_target':valid,
            'invalid_reasons':reasons,'before':before,'held':held,'released':released,
            'delta':delta,'other_axis_delta':other_delta,
            'motion_ok':sign*delta>1e-9 if valid else None,
            'held_sunken':bool(held.get('sunken',False)),
            'released_sunken':bool(released.get('sunken',False)),
            'passed':None}
    if valid:
        result['passed']=result['motion_ok'] and result['held_sunken'] and not result['released_sunken']
    result['status']='invalid_target' if not valid else 'passed' if result['passed'] else 'failed_interaction'
    return result


def summarize(checks):
    valid=[c for c in checks if c.get('valid_target') is True]
    invalid=[c for c in checks if c.get('status')=='invalid_target']
    unavailable=[c for c in checks if c.get('status')=='not_available']
    motion_fail=[c for c in valid if not c.get('motion_ok')]
    pressure_fail=[c for c in valid if not c.get('held_sunken') or c.get('released_sunken')]
    expected={(o,a) for o in ('vertical','horizontal') for a in ('up','down')}
    observed={(c.get('orientation'),c.get('arrow')) for c in valid}
    complete=len(checks)==4 and len(valid)==4 and observed==expected
    verdict='passed' if complete and not motion_fail and not pressure_fail else \
            'inconclusive_targets' if invalid else 'not_available' if not valid else \
            'failed_motion' if motion_fail else 'failed_pressure' if pressure_fail else 'partial'
    return {'verdict':verdict,'valid_targets':len(valid),'invalid_targets':len(invalid),
            'unavailable_targets':len(unavailable),'motion_failures':len(motion_fail),
            'pressure_failures':len(pressure_fail),'all_four_targets_valid':complete,
            'all_passed':verdict=='passed'}


def exit_code(summary):
    if summary['all_passed']:return 0
    if summary['verdict']=='not_available':return 77
    if summary['invalid_targets'] or summary['verdict']=='partial':return 2
    return 1
