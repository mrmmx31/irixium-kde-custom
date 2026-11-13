#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK2 tooltip geometry with four KDE-role style fixtures.

These RC files test that positioning preserves the native style; they are not
an implementation claim about GTK2 theme generation or installation.
"""
import argparse
import configparser
import json
import os
from pathlib import Path
import subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--display',required=True,help='Existing authorized Xephyr display, e.g. :74.')
parser.add_argument('--xauthority',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[3]
output=args.output.expanduser().resolve()
if not output.is_relative_to((Path.home()/'tempia').resolve()):
    parser.error('--output must be inside ~/tempia')
output.mkdir(parents=True,exist_ok=True,mode=0o700)
output.chmod(0o700)
sources={'DomainOS':root/'colors/DomainOS-SR10.4.colors',
         'BreezeLight':Path('/usr/share/color-schemes/BreezeLight.colors'),
         'BreezeDark':Path('/usr/share/color-schemes/BreezeDark.colors')}
rows=[]
for name in (*sources,'TestYellow'):
    folder=output/name
    folder.mkdir(parents=True,exist_ok=True)
    if name=='TestYellow':
        # Artificial test roles only; never installed or product colours.
        face,text='ecd870','201c0c'
    else:
        config=configparser.ConfigParser(interpolation=None,strict=False)
        config.optionxform=str
        config.read(sources[name])
        group='Colors:Tooltip' if config.has_section('Colors:Tooltip') else 'Colors:Window'
        face,text=('%02x%02x%02x'%tuple(map(int,config[group][key].split(',')))
                   for key in ('BackgroundNormal','ForegroundNormal'))
    rc=folder/'tooltip.rc'
    rc.write_text('style "T07Tooltip" {\n bg[NORMAL] = "#'+face+'"\n fg[NORMAL] = "#'+text+
                  '"\n}\nwidget "*gtk-tooltip*" style : highest "T07Tooltip"\n')
    for embedded in (False,True):
        case=folder/('coupled' if embedded else 'separate')
        case.mkdir(exist_ok=True)
        command=['/usr/bin/python3','-B',
            str(Path(__file__).with_name('probe_gtk_hint_hover.py')),'--family','gtk2',
            '--rc',str(rc),'--button-y','520' if embedded else '240','--capture',str(case/'root.png')]
        if embedded: command.append('--embedded')
        env={**os.environ,'DISPLAY':args.display,'XAUTHORITY':str(args.xauthority.expanduser()),
             'T07_PRIVATE_PROBE':'1','NO_AT_BRIDGE':'1','GTK_MODULES':'',
             'GTK2_RC_FILES':'/dev/null','T07_HINT_FACE':face,'T07_HINT_TEXT':text}
        try:
            child=subprocess.run(command,capture_output=True,text=True,timeout=20,
                env=env)
        except subprocess.TimeoutExpired as exc:
            for suffix,value in (('stdout',exc.stdout),('stderr',exc.stderr)):
                if isinstance(value,bytes): value=value.decode('utf-8','replace')
                (case/f'{suffix}.log').write_text(value or '')
            raise RuntimeError(f'{name}/{case.name}: native tooltip probe timed out after 20 s') from exc
        (case/'stdout.json').write_text(child.stdout)
        (case/'stderr.log').write_text(child.stderr)
        if child.returncode: raise RuntimeError(child.stderr)
        rows.append({'scheme':name,'native':json.loads(child.stdout),'fixture_roles':{'face':face,'text':text}})
report={'status':'passed','rows':rows,'scope':'native GTK2 tooltip geometry/timing/stability/leave/click in two origins; preserves four KDE-role RC fixtures, not generator or historical fidelity'}
(output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':'passed','native_cases':len(rows),'role_fixtures':4}))
