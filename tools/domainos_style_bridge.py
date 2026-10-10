#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in, user-only bridge between the Classic and DomainOS Plasma styles.

The bridge observes the user's choice; it never selects a style. Installation
copies its complete Python runtime into this user's data directory. No service
is started unless --iniciar is explicitly supplied.
"""
from __future__ import annotations
import argparse
import configparser
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True
from activate_domainos import latest as activation_latest, session_owner
from install_suite import roots
from theme_transaction import Failure, atomic, image, no_links, replace_checked, snapshot
from user_bundle import Bundle, fingerprint

ROOT = Path(__file__).resolve().parents[1]
UNIT = 'irix-domainos-style-bridge.service'
MODULES = ('domainos_style_bridge.py', 'activate_domainos.py', 'panel_layout.py',
    'classic_panel.py', 'install_domainos.py', 'install_suite.py', 'components.py',
    'user_bundle.py', 'theme_transaction.py', 'domainos_color_migration.py',
    'domainos_native_menu.py')
STYLES = {'IrixClassicDomainOS': 'active', 'IrixClassic': 'restored'}


def paths(data, config, state):
    return {'runtime': data/'irixclassic/domainos-style-bridge',
        'unit': config/'systemd/user'/UNIT, 'plasmarc': config/'plasmarc',
        'state': state/'irixium-domainos-style-bridge',
        'activation': state/'irixium-domainos-panel'}


def own_file(path, private=False):
    no_links(path)
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_uid != os.getuid():
        raise Failure('Arquivo regular do próprio usuário necessário: '+str(path))
    if private and stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise Failure('Permissão 0600 necessária: '+str(path))


def private_directory(path):
    no_links(path)
    if path.exists() and (not path.is_dir() or path.stat().st_uid != os.getuid()):
        raise Failure('Pasta do próprio usuário necessária: '+str(path))
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)


def activation_record(locations):
    # The activator validates its receipt identity, plugin, token and user.
    pointer = locations['activation']/'latest'
    own_file(pointer)
    receipt, record = activation_latest(locations['activation'])
    own_file(receipt)
    return receipt, record


def read_control(locations, required=True, verify_runtime=True, allow_previous_runtime=False):
    target = locations['state']/'control.json'
    no_links(target)
    if not target.exists():
        if required: raise Failure('Instale e habilite a ponte explicitamente neste perfil primeiro.')
        return None
    own_file(target, private=True)
    control = json.loads(target.read_text())
    expected = {key:str(locations[key]) for key in ('runtime','unit','plasmarc','activation')}
    if control.get('format') != 1 or control.get('uid') != os.getuid() or control.get('paths') != expected \
            or type(control.get('enabled')) is not bool:
        raise Failure('Controle da ponte não pertence a estes caminhos/usuário.')
    if verify_runtime:
        for key in ('runtime','unit'):
            expected_fingerprint = control.get('fingerprints',{}).get(key)
            if not expected_fingerprint or fingerprint(locations[key]) != expected_fingerprint:
                raise Failure('Edição posterior detectada na ponte: '+str(locations[key]))
        own_file(locations['unit'], private=True)
        runtime = locations['runtime']
        if runtime.stat().st_uid != os.getuid() or stat.S_IMODE(runtime.stat().st_mode) != 0o700:
            raise Failure('Pasta privada da ponte alterada.')
        # A guarded upgrade can recognize the complete nine/ten-module
        # runtimes. Their recorded whole-tree fingerprint must still match before
        # replacing it; ordinary execution requires all current dependencies.
        modules = set(MODULES)
        if allow_previous_runtime:
            installed = {path.name for path in (runtime/'tools').iterdir()}
            previous = modules - {'domainos_native_menu.py'}
            older = previous - {'domainos_color_migration.py'}
            if installed not in (modules, previous, older):
                raise Failure('Runtime da ponte incompleto ou desconhecido.')
            modules = installed
        for name in modules: own_file(runtime/'tools'/name, private=True)
    return control


def quoted(value, *, command=False):
    text = str(value)
    if any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise Failure('Caractere de controle recusado no caminho do serviço.')
    # ExecStart expands variables even inside quotes; $$ represents a literal
    # dollar. Environment= performs no variable expansion and keeps $ unchanged.
    if command:
        text = text.replace('$', '$$')
    return '"'+text.replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'


def unit_content(locations, data, config, state):
    executable = locations['runtime']/'tools/domainos_style_bridge.py'
    return ('[Unit]\nDescription=DomainOS: ponte de estilos deste usuário\n'
        'After=graphical-session.target\nPartOf=graphical-session.target\n\n'
        '[Service]\nType=simple\nExecStart=/usr/bin/python3 '+quoted(executable, command=True)+' --observar\n'
        'Environment=PYTHONDONTWRITEBYTECODE=1\n'
        + ''.join('Environment='+quoted(key+'='+str(value))+'\n' for key,value in (
            ('XDG_DATA_HOME',data),('XDG_CONFIG_HOME',config),('XDG_STATE_HOME',state)))
        + 'Restart=no\n\n[Install]\nWantedBy=graphical-session.target\n').encode()


def write_control(locations, control, cause):
    target = locations['state']/'control.json'
    before = snapshot(target)
    desired = image((json.dumps(control,ensure_ascii=False,indent=2)+'\n').encode(),0o600)
    if before == desired: return None
    backup = locations['state']/'control-backups'/uuid.uuid4().hex/'receipt.json'
    atomic(backup,(json.dumps({'format':1,'uid':os.getuid(),'cause':cause,
        'path':str(target),'before':before,'after':desired},ensure_ascii=False,indent=2)+'\n').encode())
    replace_checked(target,before,desired)
    return backup


def install_bridge(data, config, state, source_root=ROOT):
    locations = paths(data,config,state)
    _, activation = activation_record(locations)
    if activation.get('status') not in ('active','restored'):
        raise Failure('Conclua ou restaure a ativação pendente antes de instalar a ponte.')
    private_directory(locations['state'])
    bundle = Bundle(locations['state']/'installations', (locations['runtime'],locations['unit']))
    with bundle.locked():
        previous = read_control(locations, required=False, allow_previous_runtime=True)
        if previous is None and any(locations[key].exists() for key in ('runtime','unit')):
            raise Failure('Destino existente sem recibo da ponte; nenhuma substituição feita.')
        with tempfile.TemporaryDirectory(prefix='.stage-',dir=locations['state']) as staging:
            stage = Path(staging); runtime = stage/'runtime'; private_directory(runtime/'tools')
            for name in MODULES:
                source = Path(source_root)/'tools'/name
                own_file(source)
                atomic(runtime/'tools'/name,source.read_bytes())
            service = stage/UNIT; atomic(service,unit_content(locations,data,config,state))
            before_install = bundle.latest()
            try:
                bundle.install(((runtime,locations['runtime']), (service,locations['unit'])))
                os.chmod(locations['runtime'],0o700)
                control = {'format':1,'uid':os.getuid(),'enabled':True,
                    'paths':{key:str(locations[key]) for key in ('runtime','unit','plasmarc','activation')},
                    'fingerprints':{key:fingerprint(locations[key]) for key in ('runtime','unit')}}
                backup = write_control(locations,control,'install')
            except BaseException:
                after_install = bundle.latest()
                if after_install and after_install != before_install and after_install[1]['status']=='installed':
                    bundle.restore()
                raise
    print('Ponte instalada somente para este usuário; serviço ainda depende de início explícito.')
    if backup: print('Backup do controle:',backup.parent)
    return locations


def service_command(arguments, check=True):
    result = subprocess.run(['systemctl','--user',*arguments],text=True,capture_output=True,timeout=30)
    if check and result.returncode: raise Failure(result.stderr.strip() or 'O serviço deste usuário não respondeu.')
    return result


def start_bridge(locations):
    control = read_control(locations)
    if not control['enabled']: raise Failure('A ponte está desativada; reinstale para habilitar.')
    session_owner()
    service_command(['daemon-reload'])
    service_command(['enable',UNIT])
    service_command(['restart',UNIT])


def disable_bridge(locations):
    control = read_control(locations)
    private_directory(locations['state'])
    bundle = Bundle(locations['state']/'installations',(locations['runtime'],locations['unit']))
    with bundle.locked():
        control['enabled'] = False
        backup = write_control(locations,control,'disable')
    if shutil.which('systemctl') and os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        session_owner()
        service_command(['disable','--now',UNIT])
    print('Ponte desativada. A barra e o estilo atuais foram preservados.')
    if backup: print('Backup do controle:',backup.parent)


def selected_style(path):
    # Applying a native Global Theme stores its defaults in kdedefaults and
    # removes the corresponding override. An explicit empty value still wins;
    # it must never accidentally authorize a transition from the fallback.
    for candidate in (path, path.parent/'kdedefaults'/path.name):
        no_links(candidate)
        if not candidate.exists(): continue
        own_file(candidate)
        value = configparser.ConfigParser(interpolation=None,strict=False)
        value.optionxform = str
        try: value.read_string(candidate.read_text())
        except (configparser.Error, UnicodeError): return None
        if value.has_option('Theme','name'):
            return value.get('Theme','name')
        if value.has_option('Theme','name[$i]'):
            return value.get('Theme','name[$i]')
        # A deleted/annotated key or group can mask inherited KConfig data.
        # Unsupported markers fail closed rather than selecting lower data.
        if any(section.startswith('Theme][') for section in value.sections()) or \
                (value.has_section('Theme') and any(key.startswith('name[')
                    for key in value['Theme'])):
            return None
    return None


def action_for(style, record):
    """Only settled, previously authorized panel transitions are eligible."""
    desired = STYLES.get(style)
    status = record.get('status')
    if desired is None or status not in ('active','restored') or desired == status: return None
    return ['--ponte'] if desired == 'active' else ['--ponte','--restaurar']


def watch(locations, app=None):
    from PyQt6.QtCore import QCoreApplication, QFileSystemWatcher, QObject, QProcess
    application = app or QCoreApplication(sys.argv)
    session_owner()
    control = read_control(locations)
    if not control['enabled']: raise Failure('A ponte foi desativada neste perfil.')
    activation_record(locations)  # Never create the first authorization.

    class Observer(QObject):
        def __init__(self):
            super().__init__(); self.watcher=QFileSystemWatcher(self)
            self.watcher.fileChanged.connect(self.changed)
            self.watcher.directoryChanged.connect(self.changed)
            self.process=None; self.attempted=None
            self.changed()

        def arm(self, receipt=None):
            wanted=[locations['plasmarc'],locations['plasmarc'].parent,
                locations['plasmarc'].parent/'kdedefaults/plasmarc',
                locations['plasmarc'].parent/'kdedefaults',
                locations['state']/'control.json',locations['state'],
                locations['activation']/'latest',locations['activation']]
            if receipt: wanted.extend([receipt,receipt.parent])
            existing=set(self.watcher.files()+self.watcher.directories())
            desired={str(path) for path in wanted if path.exists()}
            if existing-desired: self.watcher.removePaths(sorted(existing-desired))
            if desired-existing: self.watcher.addPaths(sorted(desired-existing))

        def changed(self, *_):
            try:
                current=read_control(locations)
                if not current['enabled']:
                    print('Ponte desativada pelo usuário.',flush=True); application.quit(); return
                receipt,record=activation_record(locations); self.arm(receipt)
                style=selected_style(locations['plasmarc'])
                key=(style,record['token'],record.get('status'))
                arguments=action_for(style,record)
                if self.process is not None: return
                if arguments is None:
                    self.attempted=None; return
                if key==self.attempted: return
                session_owner()
                self.attempted=key
                self.process=QProcess(self)
                self.process.finished.connect(self.finished)
                self.process.errorOccurred.connect(self.error)
                self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
                self.process.start('/usr/bin/python3',[str(locations['runtime']/'tools/activate_domainos.py'),*arguments])
                print(json.dumps({'style':style,'operation':arguments,'state':record['status']},ensure_ascii=False),flush=True)
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
                self.arm()
                print('Ponte: '+str(error),file=sys.stderr,flush=True)

        def finished(self, code, _status):
            process=self.process; self.process=None
            if process is None: return
            output=bytes(process.readAllStandardOutput()).decode(errors='replace').strip()
            if output: print(output,flush=True)
            process.deleteLater()
            if code: print('Ponte: operação recusada; nenhum novo ensaio automático até outra escolha.',file=sys.stderr,flush=True)
            self.changed()

        def error(self, error):
            if error==QProcess.ProcessError.FailedToStart:
                self.process.deleteLater(); self.process=None
                print('Ponte: não foi possível iniciar o ativador.',file=sys.stderr,flush=True)

    observer=Observer()
    if app is not None: return observer
    return application.exec()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--instalar',action='store_true',help='instalar e habilitar o controle desta instância de usuário')
    group.add_argument('--observar',action='store_true')
    group.add_argument('--desativar',action='store_true')
    group.add_argument('--verificar',action='store_true')
    parser.add_argument('--iniciar',action='store_true',help='instalar e iniciar o serviço da própria sessão KDE')
    args=parser.parse_args()
    if os.geteuid()==0: raise Failure('Execute como usuário normal, sem sudo.')
    if args.iniciar and (args.observar or args.desativar or args.verificar):
        raise Failure('--iniciar acompanha somente a instalação.')
    data,config,state=roots(); locations=paths(data,config,state)
    if args.observar: return watch(locations)
    if args.desativar: return disable_bridge(locations)
    if args.verificar:
        _,record=activation_record(locations)
        control=read_control(locations,required=False)
        print(json.dumps({'uid':os.getuid(),'panel_status':record['status'],
            'bridge_installed':control is not None,'enabled':bool(control and control['enabled']),
            'selected_style':selected_style(locations['plasmarc'])},ensure_ascii=False,indent=2)); return
    locations=install_bridge(data,config,state)
    if args.iniciar: start_bridge(locations)


if __name__=='__main__':
    try: main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error: sys.exit('ERRO: '+str(error))
