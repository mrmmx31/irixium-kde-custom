#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Collect four isolated native arrow probes in one report, without installing.

1: Qt Widgets. 2: installed org.kde.desktop imports. 3: local QML file as-is.
4: the existing optional fix applied only to a temporary copy.
A failed original probe is useful evidence, not proof that the fix is loaded.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from diagnose_arrows import inventory, clean
ROOT=Path(__file__).resolve().parent


def commands(style):
    return (
        ('widgets',[str(ROOT/'diagnose_arrows.py'),'--probe','widgets','--style',style]),
        ('quick_installed',[str(ROOT/'diagnose_arrows.py'),'--probe','quick','--style',style]),
        ('quick_file',[str(ROOT/'preview_qtquick_pressure.py'),'--testar','--estilo',style,'--original']),
        ('quick_temporary_fix',[str(ROOT/'preview_qtquick_pressure.py'),'--testar','--estilo',style]),
    )


def execute(argv):
    try:
        p=subprocess.run([sys.executable,*argv],capture_output=True,text=True,timeout=60)
        row={'returncode':p.returncode,'stderr':clean(p.stderr.strip())}
        try:row['result']=json.loads(p.stdout)
        except json.JSONDecodeError:row['stdout']=clean(p.stdout.strip())
        row['status']='not_run' if p.returncode==77 else 'completed' if 'result' in row else 'probe_error'
        return row
    except subprocess.TimeoutExpired:
        return {'status':'timeout','returncode':124}
    except OSError as exc:
        return {'status':'probe_error','returncode':1,'error':clean(exc)}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida',type=Path,required=True)
    p.add_argument('--estilo',choices=('Fusion','Breeze','kvantum'),default='Fusion')
    a=p.parse_args(argv)
    folder=a.saida.expanduser().absolute()
    for path in (folder,*folder.parents):
        if path.is_symlink():p.error('Pasta de saída ou ancestral é um link simbólico.')
    if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
        p.error('--saida exige uma pasta nova ou vazia.')
    folder.mkdir(parents=True,mode=0o700,exist_ok=True)
    report={'kind':'four_path_arrow_comparison','style':a.estilo,
            'inventory':inventory(),'probes':{},
            'notes':['No system patch was installed by this command.',
                     'Temporary-file loading is not evidence that the installed application loaded the same code.',
                     'Compare motion, held_sunken and released_sunken separately. A return code 77 means not executed.']}
    path=folder/'COMPARACAO-SETAS.json'
    def save():
        tmp=folder/'.report.tmp'
        tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        tmp.chmod(0o600);os.replace(tmp,path)
    save()
    try:
        for name,argv in commands(a.estilo):
            print('Ensaio:',name,flush=True)
            report['probes'][name]=execute(argv);save()
    except KeyboardInterrupt:
        report['interrupted']=True;save();return 130
    ran=[r for r in report['probes'].values() if r['status']=='completed']
    report['collection_status']='collected' if ran else 'no_native_result'
    save();print('Relatório:',path)
    print('Os códigos individuais constam do JSON; coletar não significa aprovar a correção.')
    return 0 if ran else 77 if all(r['returncode']==77 for r in report['probes'].values()) else 1

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError) as exc:print('ERRO:',clean(exc),file=sys.stderr);sys.exit(1)
