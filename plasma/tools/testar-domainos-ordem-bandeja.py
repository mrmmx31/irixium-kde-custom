#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native tray ordering UI: staged moves, Discard, Apply, six slots and overflow.

Uses nine owned StatusNotifierItems on a private D-Bus/Xvfb/KWin session. Shipped
production QML is read through a symlink; completed fixture themes are read-only
via XDG_DATA_DIRS. No full package/icon copy and no personal profile changes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
APPLET=REPO/'plasma/applets/org.irixclassic.domainos.panel'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    if os.environ.get('IRIX_DOMAINOS_TRAY_PRIVATE_SESSION')!='1':raise RuntimeError('Private session required')
    spec=importlib.util.spec_from_file_location('domainos_owned_sni_fixture',REPO/'plasma/tools/testar-domainos-bandeja.py')
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    fixture.IDENTIFIER='org.irixclassic.domainos.panel'
    processes=[];logs=[]
    try:
        for executable in ('kwin_x11','kactivitymanagerd','ksystemstats'):
            path=shutil.which(executable) or '/usr/lib/x86_64-linux-gnu/libexec/'+executable
            log=(output/(executable+'.log')).open('w');logs.append(log)
            processes.append(subprocess.Popen([path,*(['--remain'] if executable=='ksystemstats' else [])],stdout=log,stderr=subprocess.STDOUT))
        for _ in range(80):
            if subprocess.run(['qdbus6','org.kde.KWin','/KWin'],capture_output=True,timeout=2).returncode==0:break
            time.sleep(.05)
        return fixture.worker(output)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:process.wait(3)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        for log in logs:log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True)
    parser.add_argument('--recursos-encerrados',type=Path,required=True)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve();resources=args.recursos_encerrados.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output.exists():parser.error('Use a new owned /tmp output')
    if not resources.is_relative_to(Path('/tmp')) or resources.stat().st_uid!=os.getuid():parser.error('Use completed owned fixture resources')
    previous=json.loads((resources/'RESULTADO.json').read_text())
    if previous.get('checks',{}).get('native_host_exited') is not True:parser.error('Resource fixture host must have exited')
    output.mkdir(mode=0o700)
    env=os.environ.copy();real_config=Path(env.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected=lambda:{name:digest(real_config/name) for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=protected();sources={str(path.relative_to(APPLET)):digest(path) for path in sorted(APPLET.rglob('*')) if path.is_file()}
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','XAUTHORITY','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID'):
        env.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        folder=output/name;folder.mkdir(mode=0o700);env[key]=str(folder)
    plasmoids=output/'data/plasma/plasmoids';plasmoids.mkdir(parents=True)
    (plasmoids/'org.irixclassic.domainos.panel').symlink_to(APPLET,target_is_directory=True)
    # Observation only: inherited production page supplies every control and
    # cfg_ property. ConfigView still stages/applies its native KConfig map.
    page=output/'OrderObservation.qml'
    page.write_text('import QtQuick\nimport "'+(APPLET/'contents/ui').as_uri()+'" as Panel\nPanel.ConfigTray { readonly property string draftStateJson:JSON.stringify({order:cfg_trayOrder,visible:cfg_trayVisibleItems,hidden:cfg_trayHiddenItems,includeHidden:cfg_trayIncludeHiddenInOverflow,overflowMode:cfg_trayOverflowMode}) }\n')
    (output/'config/kwinrc').write_text('[Desktops]\nNumber=1\n[Compositing]\nEnabled=false\n')
    (output/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
    (output/'config/plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
    env.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='kde',QT_QUICK_BACKEND='software',QML_DISABLE_DISK_CACHE='1',QT_SCALE_FACTOR='1',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS=str(resources/'data')+':/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio'),KWIN_COMPOSE='N',LIBGL_ALWAYS_SOFTWARE='1',IRIX_DOMAINOS_TRAY_PRIVATE_SESSION='1',IRIX_DOMAINOS_ORDER_PAGE=str(page))
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test','Qt6DBus'],text=True))
    subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(REPO/'plasma/tests/domainos-tray-order-host.cpp'),'-o',str(output/'tray-host.so'),*flags,'-ldl'],check=True)
    moc=Path(subprocess.check_output(['qtpaths6','--query','QT_INSTALL_LIBEXECS'],text=True).strip())/'moc'
    tooltip=REPO/'plasma/tests/domainos-native-tooltip-type.cpp'
    subprocess.run([str(moc),str(tooltip),'-o',str(output/'domainos-native-tooltip-type.moc')],check=True)
    subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(tooltip),'-I'+str(output),'-o',str(output/'native-tooltip-type.so'),*flags],check=True)
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    result=subprocess.run(['xvfb-run','--auto-servernum','--server-args=-screen 0 1300x950x24','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output),'--recursos-encerrados',str(resources)],env=env,capture_output=True,text=True,timeout=40)
    (output/'runner.log').write_text(result.stdout+result.stderr)
    native=json.loads((output/'native.json').read_text()) if (output/'native.json').exists() else {}
    log=(output/'host.log').read_text() if (output/'host.log').exists() else result.stderr
    diagnostics=[line for line in log.splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable',line)]
    # Preserve every diagnostic and the general gate. The optional previously
    # audited SDK baseline distinguishes behavior from preexisting framework
    # errors; it never turns qml_runtime_errors_zero into a misleading pass.
    sdk_audit=Path('/tmp/irix-domainos-padroes-native-sdk-audit.json')
    audited=json.loads(sdk_audit.read_text()) if sdk_audit.is_file() else {}
    baseline=audited.get('qml_diagnostics_retained',[]) if audited.get('framework_diagnostics_identical_to_pre_reset_R7') is True else []
    sdk=[line for line in diagnostics if line in baseline]
    checks=native.get('checks',{})
    checks.update(native_host_exited_cleanly=result.returncode==0 and not native.get('failure'),qml_runtime_errors_zero=not diagnostics,
        real_profiles_unchanged=before==protected(),production_sources_unchanged=all(digest(APPLET/name)==value for name,value in sources.items()),
        real_installed_native_host=native.get('hostExecutable')=='/usr/bin/plasmawindowed')
    behaviors={key:value for key,value in checks.items() if key!='qml_runtime_errors_zero'}
    behavior_ok=bool(behaviors) and all(behaviors.values())
    status='passed' if behavior_ok and not diagnostics else 'behavior_passed_with_existing_framework_diagnostics' if behavior_ok and len(sdk)==len(diagnostics) else 'failed'
    report={'status':status,'checks':checks,'behavior_checks':behaviors,'native':native,'qml_diagnostics':diagnostics,'installed_sdk_baseline_report':str(sdk_audit) if baseline else None,'known_installed_sdk_prompt_warnings':sdk,'source_sha256':sources,'protected_config_sha256':{'before':before,'after':protected()},'scope':'Native production ConfigTray inherited only for read-only JSON observation inside private ConfigView. Real pointer moves, Cancel/Discard/reopen/Apply, six actual SNI/provider slots, actual overflow order and separate applet ID 101. No personal session or immutable resources changed.'}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[key for key,value in checks.items() if not value],'result':str(output/'RESULTADO.json')}))
    return 0 if report['status']!='failed' else 1


if __name__=='__main__':raise SystemExit(main())
