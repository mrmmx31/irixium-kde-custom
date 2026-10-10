#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare actual native menu geometry at 50% and 100% near the screen edge.

Each case has its own HOME/XDG/bus/Xvfb/KWin and test-owned QWidget windows.
The 'before' override is read-only archived source; production is never edited.
The host opens KDE's installed ContextMenu.qml with a native right-button event.
Global coordinates are observed in X11, where they are available to Qt.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = 'org.irixclassic.domainos.panel'
IDENTIFIER = 'org.irixclassic.domainos.menu.scale.test'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output, mode):
    if os.environ.get('IRIX_DOMAINOS_MEMBERSHIP_PRIVATE') != '1':
        raise RuntimeError('Private session required')
    log = (output/'kwin.log').open('w')
    wm = subprocess.Popen(['kwin_x11'], stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            probe = subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,timeout=2)
            if probe.returncode == 0:
                break
            time.sleep(.05)
        else:
            raise RuntimeError('Private KWin did not become ready')
        env = dict(os.environ, LD_PRELOAD=str(output/'membership-host.so'),IRIX_DOMAINOS_MEMBERSHIP_OUTPUT=str(output),IRIX_DOMAINOS_MEMBERSHIP_MODE=mode,IRIX_DOMAINOS_MENU_SCALE_OUTPUT=str(output),IRIX_DOMAINOS_MENU_SCALE_REPORT=str(output/'state.json'))
        result = subprocess.run(['plasmawindowed', IDENTIFIER],env=env,capture_output=True,text=True,timeout=75)
        (output/'host.log').write_text(result.stdout+result.stderr)
        native = json.loads((output/'state.json').read_text()) if (output/'state.json').is_file() else {}
        errors = [line for line in (result.stdout+result.stderr).splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)]
        checks = native.get('checks', {})
        expected = {name: os.environ[name] for name in ('HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS')}
        checks.update(native_host_exited=result.returncode==0,qml_runtime_errors_zero=not errors,
            native_host_uses_private_namespace=native.get('namespace')==expected)
        report = {'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'native':native,'qml_errors':errors,'scope':'X11 only: actual TasksModel and KDE native QMenu with an owned QWidget group, private profiles/bus/compositor and no window commands.'}
        (output/'RAW.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        return 0
    finally:
        wm.terminate()
        try:
            wm.wait(4)
        except subprocess.TimeoutExpired:
            wm.kill();wm.wait()
        log.close()
        if (output/'RAW.json').exists():
            report = json.loads((output/'RAW.json').read_text())
            report['checks']['owned_private_kwin_stopped'] = wm.poll() is not None
            report['status'] = 'passed' if report['checks'] and all(report['checks'].values()) else 'failed'
            (output/'RAW.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')


def run_case(output, mode, baseline):
    output.mkdir(mode=0o700)
    env = os.environ.copy()
    for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','XAUTHORITY','SESSION_MANAGER','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID','PULSE_SERVER','PULSE_COOKIE'):
        env.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        path=output/name;path.mkdir(mode=0o700);env[key]=str(path)
    plasmoids=output/'data/plasma/plasmoids'
    production=plasmoids/APPLET
    shutil.copytree(REPO/'plasma/applets'/APPLET,production,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(REPO/'plasma/applets/org.irixclassic.grosview',plasmoids/'org.irixclassic.grosview',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    if mode=='before':
        shutil.copyfile(baseline,production/'contents/ui/DomainOSNativeTaskMenu.qml')
    for name in ('IrixClassic','IrixClassicDomainOS'):
        shutil.copytree(REPO/'plasma'/name,output/'data/plasma/desktoptheme'/name)
    fixture=plasmoids/IDENTIFIER;(fixture/'contents/ui').mkdir(parents=True)
    (fixture/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,'Name':'DomainOS native desktop membership test','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
    shutil.copyfile(REPO/'plasma/tests/DomainOSNativeMenuScaleFixture.qml',fixture/'contents/ui/main.qml')
    (output/'config/kwinrc').write_text('[Compositing]\nEnabled=false\n[Desktops]\nNumber=2\nName_1=Private initial\nName_2=Private untouched\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n')
    env.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',KWIN_COMPOSE='N',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',QT_ACCESSIBILITY='0',LIBGL_ALWAYS_SOFTWARE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8',GIO_USE_VFS='local',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio-server'),IRIX_DOMAINOS_MEMBERSHIP_PRIVATE='1')
    theme=output/'config/Kvantum/IrixClassic'; theme.mkdir(parents=True)
    for name in ('IrixClassic.svg','IrixClassic.kvconfig'): shutil.copyfile(REPO/'kvantum/IrixClassic'/name,theme/name)
    (theme.parent/'kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test','Qt6DBus','x11'],text=True))
    subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(REPO/'plasma/tests/domainos-native-menu-scale-host.cpp'),'-o',str(output/'membership-host.so'),*flags,'-ldl'],check=True)
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    try:
        result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1200x900x24 -nolisten tcp','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--versao',mode,'--saida',str(output)],env=env,capture_output=True,text=True,timeout=90)
        (output/'runner.log').write_text(result.stdout+result.stderr)
    except subprocess.TimeoutExpired as error:
        (output/'runner.log').write_text(str(error));return {'status':'failed','checks':{},'error':'Private runner timed out'}
    report=json.loads((output/'RAW.json').read_text()) if (output/'RAW.json').is_file() else {'status':'failed','checks':{},'error':result.stdout+result.stderr}
    report['source_menu_sha256']=sha(production/'contents/ui/DomainOSNativeTaskMenu.qml')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True)
    parser.add_argument('--menu-antes',type=Path)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--versao',choices=('before','after'),default='after',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output,args.versao)
    if not output.is_relative_to(Path('/tmp')) or output==Path('/tmp') or output.exists():parser.error('Use a new directory under /tmp')
    if not args.menu_antes or not args.menu_antes.is_file():parser.error('--menu-antes must be the archived pre-fix menu')
    output.mkdir(mode=0o700)
    config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    names=('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')
    protected={str(config/name):sha(config/name) for name in names}
    runtime=REPO/'plasma/applets'/APPLET
    source_before={str(path.relative_to(runtime)):sha(path) for path in sorted(runtime.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}
    before=run_case(output/'before','before',args.menu_antes.resolve())
    after=run_case(output/'after','after',args.menu_antes.resolve())
    safety='case_0_menu_entirely_above_real_anchor'
    checks={'baseline_reproduces_scaled_native_menu_misplacement':before.get('checks',{}).get(safety) is False,
        'baseline_common_native_checks_pass':bool(before.get('checks')) and all(value for key,value in before['checks'].items() if key!=safety),
        'current_all_native_checks_pass':after['status']=='passed',
        'protected_profiles_unchanged':protected=={str(config/name):sha(config/name) for name in names},
        'production_source_unchanged':source_before=={str(path.relative_to(runtime)):sha(path) for path in sorted(runtime.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}}
    report={'status':'passed' if all(checks.values()) else 'failed','checks':checks,'before_raw':before,'after_raw':after,'protected_config_sha256':{'before':protected,'after':{str(config/name):sha(config/name) for name in names}},'production_menu_sha256':sha(runtime/'contents/ui/DomainOSNativeTaskMenu.qml'),'baseline_menu_sha256':sha(args.menu_antes),'scope':'Actual native QMenu first-open geometry in X11/KWin/Xvfb with own group at bottom edge and real global coordinates. Compare frozen 0.2.6 with current source at 50% and 100%; all visible QAction rectangles and screen bounds observed. No user profiles or window actions.'}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'baseline_checks':len(before.get('checks',{})),'current_checks':len(after.get('checks',{})),'report':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
