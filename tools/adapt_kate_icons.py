#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install a reversible Kate Git icon overlay for the current user only."""
import argparse,configparser,importlib.util,os,shutil,subprocess,sys,tempfile
from pathlib import Path
from install_suite import roots
from theme_transaction import Transaction,Change,Failure,snapshot,decode,edit_ini
from adapt_classic_launchers import restore_history
from adapt_pia_tray import wrapper
ROOT=Path(__file__).resolve().parents[1]
FILES=('libirix-kate-icons.so','manifest.json','kate-sgi')

def changes(data,payload,source,application=Path('/usr/bin/kate')):
    destination=data/'irixium/integrations/kate'
    if any(c.isspace() or c==':' for c in str(destination)):raise Failure('Caminho da biblioteca incompatível com LD_PRELOAD.')
    path=data/'applications/org.kde.kate.desktop';prior=snapshot(path)
    original=decode(prior) if prior['exists'] else source.read_bytes()
    launcher=destination/'kate-sgi'
    quoted=str(launcher).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('\\','\\\\').replace('%','%%')
    updated=edit_ini(original,'Desktop Entry',{'Exec':f'"{quoted}" -b %U'})
    c=configparser.ConfigParser(interpolation=None,strict=False);c.read_string(original.decode());old=c.get('Desktop Entry','Exec',fallback='')
    if old not in ('kate -b %U',f'"{quoted}" -b %U'):raise Failure('Comando personalizado do Kate: preserve-o antes de adaptar.')
    if c.getboolean('Desktop Entry','DBusActivatable',fallback=False):raise Failure('Atalho personalizado usa ativação D-Bus; requer revisão.')
    result=[Change(path,updated,0,prior.get('mode',0o644),prior)]
    for name in FILES[:2]:
        dest=destination/name;result.append(Change(dest,(payload/name).read_bytes(),0,0o644,snapshot(dest)))
    dest=destination/'kate-sgi';result.append(Change(dest,wrapper(destination/FILES[0],application),0,0o755,snapshot(dest)))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verificar',action='store_true');p.add_argument('--restaurar',action='store_true');a=p.parse_args()
    if os.geteuid()==0:raise Failure('Execute sem sudo.')
    data,config,state=roots();destination=data/'irixium/integrations/kate';allowed={data/'applications/org.kde.kate.desktop'}|{destination/n for n in FILES}
    def refuse_shared(entries):raise Failure('Arquivos compartilhados nunca são modificados.')
    tx=Transaction(state/'irix-kate-icons',refuse_shared,lambda path,phase:path in allowed and phase==0)
    if a.restaurar:
        with tx.locked():restore_history(tx,a.verificar)
    else:
        if not Path('/usr/bin/kate').is_file():raise Failure('Kate não encontrado em /usr/bin/kate.')
        spec=importlib.util.spec_from_file_location('kate_icon_builder',ROOT/'integrations/kate/build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory(prefix='irix-kate-build-') as temp:
            payload=m.build(temp)
            with tx.locked():tx.install(changes(data,payload,Path('/usr/share/applications/org.kde.kate.desktop')),a.verificar)
    if not a.verificar:
        cache=shutil.which('kbuildsycoca6')
        if cache:subprocess.run([cache,'--noincremental'],check=True)
        print('Integração local instalada. Salve seus documentos e reabra o Kate pelo menu para carregar o Git SGI.')
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:sys.exit('ERRO: '+str(e))
