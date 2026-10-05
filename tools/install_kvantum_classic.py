#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install/restore only the IrixClassic Kvantum files; activation is opt-in."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import xml.etree.ElementTree as ET
from theme_transaction import Change, Failure, Transaction, no_links, snapshot, decode, sha, edit_ini
REPO = Path(__file__).resolve().parent.parent


def theme_files(repo: Path) -> dict[str, bytes]:
    source = repo / 'kvantum/IrixClassic'
    no_links(source)
    doc = json.loads((source / 'MANIFEST.json').read_text('utf-8'))
    if doc.get('version') not in ('0.1.0-rc1', '0.1.0-rc2', '0.2.0-rc1', '0.3.0-rc1', '0.4.0-rc1', '0.5.0-rc1', '0.6.0-rc1'):
        raise Failure('Versão do tema não reconhecida.')
    result = {}
    if not {'IrixClassic.svg','IrixClassic.kvconfig','LICENSE'}.issubset(doc['files']):
        raise Failure('Manifesto incompleto.')
    for name, expected in doc['files'].items():
        if Path(name).name != name or name.startswith('.'):
            raise Failure('Nome inválido no manifesto.')
        file = source / name; no_links(file)
        content = file.read_bytes()
        if sha(content) != expected:
            raise Failure('Integridade divergente: ' + name)
        result[name] = content
    if b'<!DOCTYPE' in result['IrixClassic.svg'] or b'<!ENTITY' in result['IrixClassic.svg']:
        raise Failure('SVG com entidade externa recusado.')
    root=ET.fromstring(result['IrixClassic.svg'])
    if root.tag != '{http://www.w3.org/2000/svg}svg':
        raise Failure('SVG inválido.')
    return result


def plan(repo: Path, config: Path, activate: bool) -> list[Change]:
    result=[]
    for name,data in theme_files(repo).items():
        path=config/'Kvantum/IrixClassic'/name
        result.append(Change(path,data,0,0o644,snapshot(path)))
    if activate:
        path=config/'Kvantum/kvantum.kvconfig'; before=snapshot(path)
        result.append(Change(path,edit_ini(decode(before) or b'','General',{'theme':'IrixClassic'}),
                             2,before.get('mode',0o600),before))
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verificar',action='store_true')
    p.add_argument('--ativar',action='store_true')
    p.add_argument('--restaurar',action='store_true')
    p.add_argument('--recuperar',action='store_true')
    args=p.parse_args(argv)
    if os.geteuid()==0: raise Failure('Execute como usuário normal, sem sudo.')
    if args.recuperar and not args.restaurar: raise Failure('--recuperar exige --restaurar.')
    if args.restaurar and args.ativar: raise Failure('Não combine --restaurar com --ativar.')
    config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config'))).expanduser()
    state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state'))).expanduser()
    no_links(config); no_links(state)
    target=config/'Kvantum/IrixClassic'
    def allowed(path,phase):
        return (phase==0 and path.parent==target) or (phase==2 and path==config/'Kvantum/kvantum.kvconfig')
    def no_root(entries): raise Failure('Este instalador não possui operações administrativas.')
    tx=Transaction(state/'irixclassic-kvantum',no_root,allowed)
    def run():
        if args.restaurar: tx.restore(args.recuperar,args.verificar)
        else: tx.install(plan(REPO,config,args.ativar),args.verificar)
        if not args.verificar:
            print('Irixium moderno, decoração de janela, fontes globais e esquema KDE não foram alterados.')
            if args.ativar:
                print('IrixClassic selecionado no Kvantum. O Application Style deve estar em kvantum. Reabra os aplicativos para testar.')
            elif not args.restaurar:
                print('Tema instalado sem ativar. Selecione IrixClassic no Kvantum Manager.')
            else: print('Reabra os aplicativos para carregar a seleção anterior.')
    if args.verificar: run()
    else:
        with tx.locked(): run()
    return 0

if __name__=='__main__':
    def interrupted(signum,frame): raise KeyboardInterrupt('Sinal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    try: sys.exit(main())
    except (Failure,OSError,ValueError,KeyError,TypeError,ET.ParseError) as exc:
        print('ERRO:',exc,file=sys.stderr);sys.exit(1)
    except KeyboardInterrupt: sys.exit(130)
