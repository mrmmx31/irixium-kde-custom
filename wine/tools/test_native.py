#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Wine apply/restore and native control input in a private prefix/display.

Run: xvfb-run -a python3 wine/tools/test_native.py --output /tmp/irix-wine-test
Never reads or modifies the user's real Wine prefix. Output contains only this
fixture's synthetic application and test results, not personal configuration.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('wine_manage',ROOT/'wine/IrixClassic/package/manage.py')
manage=importlib.util.module_from_spec(spec)
previous=sys.dont_write_bytecode
try:
    sys.dont_write_bytecode=True;spec.loader.exec_module(manage)
finally:sys.dont_write_bytecode=previous


def run(output):
    if not os.environ.get('DISPLAY','').startswith(':'):
        raise RuntimeError('Execute em um Xvfb privado.')
    os.environ.pop('WAYLAND_DISPLAY',None)
    if output.exists(): raise RuntimeError('Use um diretório de teste novo.')
    output.mkdir(mode=0o700,parents=True);(output/'runtime').mkdir(mode=0o700)
    prefix=output/'prefix'
    os.environ.update(HOME=str(output),XDG_RUNTIME_DIR=str(output/'runtime'),
        WINEPREFIX=str(prefix),WINEARCH='win64',WINEDEBUG='-all',WINEDLLOVERRIDES='mscoree,mshtml=d',
        DBUS_SESSION_BUS_ADDRESS='unix:path='+str(output/'disabled-bus'))
    env=os.environ.copy();report={};proc=None;log=None
    try:
        subprocess.run(['wineboot','-i'],env=env,capture_output=True,check=True,timeout=90)
        subprocess.run(['wineserver','-p'],env=env,check=True)
        wine=manage.Wine(prefix)
        print('Wine initialized; testing theme and registry.',flush=True)
        before_theme=wine.theme('inspect');before=wine.registry()
        fonts={k:v for k,v in before.items() if 'font' in k.lower()}
        applied=manage.install(wine)
        print('Classic applied; testing native controls.',flush=True)
        assert applied['status']=='applied'
        after=wine.registry()
        assert {k:v for k,v in after.items() if 'font' in k.lower()}==fonts
        report['fonts_preserved']=True
        assert manage.install(wine)['status']=='already_applied'
        report['repeat_apply_idempotent']=True
        log=(output/'preview.log').open('w')
        proc=subprocess.Popen(['wine',str(manage.PACKAGE/'irix-preview.exe')],env=wine.env,stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            text=(output/'preview.log').read_text()
            if 'preview_ready' in text:break
            if proc.poll() is not None:raise RuntimeError(text)
            time.sleep(.1)  # Test harness only; no timer in the theme or utility.
        else:raise RuntimeError('Native control gallery did not start.')
        preview=json.loads(next(line for line in text.splitlines() if 'preview_ready' in line))
        assert all(part['defined'] and part['bitmap'] for part in preview['parts']),preview
        ident=subprocess.check_output(['xdotool','search','--name','IRIX Classic - Wine native controls'],env=env,text=True).splitlines()[0]
        subprocess.run(['import','-window',ident,str(output/'CONTROLS.png')],env=env,check=True)
        x,y,width,height=preview['apply_rect']
        subprocess.run(['xdotool','mousemove',str(x+width//2),str(y+height//2),'mousedown','1'],env=env,check=True)
        time.sleep(.05)
        subprocess.run(['import','-window',ident,str(output/'PRESSED.png')],env=env,check=True)
        assert 'apply_clicked' not in (output/'preview.log').read_text()
        subprocess.run(['xdotool','mouseup','1'],env=env,check=True)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline and 'apply_clicked' not in (output/'preview.log').read_text():time.sleep(.02)
        assert 'apply_clicked' in (output/'preview.log').read_text()
        normal=Image.open(output/'CONTROLS.png').convert('RGB');pressed=Image.open(output/'PRESSED.png').convert('RGB')
        assert normal.size==pressed.size and ImageChops.difference(normal,pressed).getbbox()
        report.update(native_parts=preview['parts'],native_click=True,held_feedback=True)
        x,y,width,height=preview['close_rect']
        subprocess.run(['xdotool','mousemove',str(x+width//2),str(y+height//2),'click','1'],env=env,check=True)
        proc.wait(timeout=15);proc=None;log.close();log=None
        # Change a genuine preference that the Classic style did not modify.
        key='HKEY_CURRENT_USER\\Control Panel\\Desktop\\WindowMetrics'
        wine.run(['wine','reg.exe','add',key,'/v','IconTitleWrap','/t','REG_SZ','/d','0','/f'])
        later=wine.registry();desired=manage.merged_restore(later,before,after)
        restored=manage.restore(wine)
        print('Previous theme restored; testing receipt failure recovery.',flush=True)
        for name in ('active','path','color','size'):assert restored['theme'][name]==before_theme[name]
        assert wine.registry()==desired
        report.update(previous_theme_restored=True,later_preference_preserved=True)
        assert not (prefix/manage.TARGET).exists()
        report['new_file_removed_on_restore']=True
        assert manage.restore(wine)['status']=='already_restored'
        # Exercise rollback after native theme application when receipt writing fails.
        baseline=wine.registry();old_save=manage.save
        def failing_save(path,doc):
            if doc['status']=='applied':raise OSError('Injected receipt write failure')
            old_save(path,doc)
        manage.save=failing_save
        try:
            try:manage.install(wine)
            except OSError:pass
            else:raise AssertionError('Expected injected receipt failure')
        finally:manage.save=old_save
        assert wine.registry()==baseline and not (prefix/manage.TARGET).exists()
        report['receipt_failure_rolls_back']=True
        report.update(status='passed',wine_version=wine.run(['wine','--version']).decode().strip())
        manage.save(output/'RESULT.json',report);print(json.dumps(report,indent=2))
    finally:
        subprocess.run(['wineserver','-k'],env=env,capture_output=True)
        if proc:proc.wait(timeout=15)
        if log:log.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output.absolute())
