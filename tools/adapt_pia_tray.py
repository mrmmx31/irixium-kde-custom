#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install or restore the optional SGI tray integration for this user's PIA GUI."""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from install_suite import roots
from theme_transaction import Transaction, Change, Failure, snapshot, decode, edit_ini
from adapt_classic_launchers import restore_history

ROOT=Path(__file__).resolve().parents[1]
PIA=Path('/opt/piavpn/bin/pia-client')


def wrapper(library, application=PIA):
    # Python literals safely preserve spaces/quotes; no shell command evaluation.
    return ('#!/usr/bin/python3\n# SPDX-License-Identifier: MIT\n'
            'import os, sys\n'
            f'library={str(library)!r}\n'
            'prior=os.environ.get("LD_PRELOAD", "")\n'
            'os.environ["LD_PRELOAD"]=library+(":"+prior if prior else "")\n'
            f'os.execv({str(application)!r}, [{str(application)!r}, *sys.argv[1:]])\n').encode()


def desktop_entry(original, launcher):
    # Desktop Exec quoting: reserved characters must survive the desktop parser.
    text=str(launcher).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')
    # Desktop entry string unescaping happens before Exec parsing.
    text=text.replace('\\','\\\\').replace('%','%%')
    return edit_ini(original,'Desktop Entry',{
        'Exec':f'env XDG_SESSION_TYPE=X11 "{text}" %u','Icon':'piavpn'})


def changes(data, payload, source):
    destination=data/'irixium/integrations/pia'
    if any(c.isspace() or c==':' for c in str(destination)):
        raise Failure('O caminho da biblioteca deve estar sem espaços ou dois-pontos (limitação do LD_PRELOAD).')
    prior=snapshot(data/'applications/piavpn.desktop')
    original=decode(prior) if prior['exists'] else source.read_bytes()
    # Preserve user-provided launch arguments; refuse to silently replace a
    # customized command outside the two exact commands owned by this helper.
    import configparser
    cp=configparser.ConfigParser(interpolation=None,strict=False);cp.read_string(original.decode())
    old=cp.get('Desktop Entry','Exec',fallback='')
    expected='env XDG_SESSION_TYPE=X11 /opt/piavpn/bin/pia-client %u'
    updated=desktop_entry(original,destination/'pia-client-sgi')
    check=configparser.ConfigParser(interpolation=None,strict=False);check.read_string(updated.decode())
    if old not in (expected,check['Desktop Entry']['Exec']):
        raise Failure('O comando do atalho PIA foi personalizado. Preserve-o e revise a integração antes de instalar.')
    result=[Change(data/'applications/piavpn.desktop',updated,0,prior.get('mode',0o644),prior)]
    for name in ('libirix-pia-tray.so','manifest.json'):
        dest=destination/name;result.append(Change(dest,(payload/name).read_bytes(),0,0o644,snapshot(dest)))
    dest=destination/'pia-client-sgi'
    result.append(Change(dest,wrapper(destination/'libirix-pia-tray.so'),0,0o755,snapshot(dest)))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar',action='store_true');parser.add_argument('--restaurar',action='store_true')
    args=parser.parse_args()
    if os.geteuid()==0:raise Failure('Execute sem sudo.')
    data,config,state=roots();destination=data/'irixium/integrations/pia'
    allowed={data/'applications/piavpn.desktop'}|{destination/n for n in ('libirix-pia-tray.so','manifest.json','pia-client-sgi')}
    def refuse_shared(entries):raise Failure('Esta integração não modifica arquivos compartilhados.')
    tx=Transaction(state/'irix-pia-tray',refuse_shared,lambda p,phase:p in allowed and phase==0)
    if args.restaurar:
        with tx.locked():restore_history(tx,args.verificar)
    else:
        if not PIA.is_file() or not Path('/opt/piavpn/lib/libQt6Core.so.6').is_file():
            raise Failure('Requer PIA para Linux com Qt 6 em /opt/piavpn.')
        module_path=ROOT/'integrations/pia/build.py'
        spec=importlib.util.spec_from_file_location('pia_artwork_builder',module_path)
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory(prefix='irix-pia-build-') as temp:
            payload=builder.build(temp)
            plan=changes(data,payload,Path('/usr/share/applications/piavpn.desktop'))
            with tx.locked():tx.install(plan,args.verificar)
    if not args.verificar:
        import shutil
        tool=shutil.which('kbuildsycoca6')
        if tool:subprocess.run([tool,'--noincremental'],check=True)
        print('Integração apenas no atalho deste usuário. Reabra a interface do PIA pelo menu de aplicações.')
        print('A conexão, o daemon e os arquivos em /opt não foram alterados.')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:sys.exit('ERRO: '+str(exc))
