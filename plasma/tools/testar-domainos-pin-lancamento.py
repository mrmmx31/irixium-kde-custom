#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""One real pinned-app launch through production Applications/Commands/helper/KIO.

Uses controller API rather than a pointer click on the full panel. All services,
Desktop Entries, windows and HOME/XDG/display/bus belong to this disposable test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
APPLET='org.irixclassic.domainos.panel'
IDENTIFIER='org.irixclassic.domainos.pin.launch.test'
DESKTOP_ID=IDENTIFIER+'.desktop'
PREFERENCES=('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc','Kvantum/kvantum.kvconfig','gtk-3.0/settings.ini','gtk-4.0/settings.ini','mimeapps.list')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def stop_owned_program(output):
    marker=output/'program-marker.json'
    if not marker.is_file():return {'stopped':False,'reason':'No own program marker'}
    observed=json.loads(marker.read_text());pid=observed.get('pid')
    if not isinstance(pid,int) or pid<=1:return {'stopped':False,'reason':'Invalid own marker PID'}
    proc=Path('/proc')/str(pid)
    if not proc.exists():return {'stopped':True,'pid':pid,'already_exited':True}
    fd=None
    try:
        fd=os.pidfd_open(pid)
        arguments=(proc/'cmdline').read_bytes().split(b'\0')
        environment=(proc/'environ').read_bytes().split(b'\0')
        own_script=str(output/'pin-marker.py').encode()
        scoped=b'IRIX_DOMAINOS_PIN_DIR='+str(output).encode()
        if own_script not in arguments or scoped not in environment:
            return {'stopped':False,'pid':pid,'reason':'PID no longer matches this test; untouched'}
        signal.pidfd_send_signal(fd,signal.SIGTERM)
        for _ in range(60):
            if not proc.exists() or (output/'program-exited.json').is_file():return {'stopped':True,'pid':pid,'pidfd_used':True}
            time.sleep(.05)
        signal.pidfd_send_signal(fd,signal.SIGKILL)
        for _ in range(60):
            if not proc.exists():return {'stopped':True,'pid':pid,'pidfd_used':True,'forced_own_cleanup':True}
            time.sleep(.05)
        return {'stopped':False,'pid':pid,'reason':'Owned child did not disappear'}
    except ProcessLookupError:
        return {'stopped':True,'pid':pid,'already_exited':True}
    finally:
        if fd is not None:os.close(fd)


def session(output):
    if os.environ.get('IRIX_DOMAINOS_PIN_PRIVATE')!='1':raise RuntimeError('Private session required')
    daemons=[];logs=[];cleanup={}
    try:
        wm_log=(output/'kwin.log').open('w');logs.append(wm_log)
        wm=subprocess.Popen(['kwin_x11'],stdout=wm_log,stderr=subprocess.STDOUT);daemons.append(wm)
        for _ in range(100):
            if subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,timeout=2).returncode==0:break
            time.sleep(.05)
        else:raise RuntimeError('Private KWin did not become ready')
        activity_log=(output/'activitymanager.log').open('w');logs.append(activity_log)
        daemons.append(subprocess.Popen(['/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd'],stdout=activity_log,stderr=subprocess.STDOUT))
        environment=dict(os.environ,LD_PRELOAD=str(output/'pin-launch-host.so'),IRIX_DOMAINOS_PIN_DIR=str(output))
        result=subprocess.run(['plasmawindowed',IDENTIFIER],env=environment,capture_output=True,text=True,timeout=35)
        (output/'host.log').write_text(result.stdout+result.stderr)
        return result.returncode
    finally:
        cleanup['own_program']=stop_owned_program(output)
        for process in reversed(daemons):
            if process.poll() is None:
                process.terminate()
                try:process.wait(3)
                except subprocess.TimeoutExpired:process.kill();process.wait(3)
        cleanup['own_daemons_exited']=all(p.poll() is not None for p in daemons)
        cleanup['own_daemon_pids']=[p.pid for p in daemons]
        (output/'cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n')
        for log in logs:log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return session(output)
    if not output.is_relative_to(Path('/tmp')) or output==Path('/tmp') or output.exists():parser.error('Use a new directory under /tmp')
    output.mkdir(mode=0o700)
    config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected_before={name:digest(config/name) for name in PREFERENCES}
    production=REPO/'plasma/applets'/APPLET
    sources_before={str(p.relative_to(production)):digest(p) for p in sorted(production.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    env=os.environ.copy()
    for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','XAUTHORITY','SESSION_MANAGER','LD_PRELOAD','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','QML_IMPORT_PATH','QML2_IMPORT_PATH','XDG_SESSION_ID','KDE_FULL_SESSION','KDE_SESSION_VERSION'):
        env.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state')):
        path=output/name;path.mkdir(mode=0o700);env[key]=str(path)
    private_runtime=tempfile.TemporaryDirectory(prefix='ird-pin-',dir='/tmp');env['XDG_RUNTIME_DIR']=private_runtime.name
    runtime_path=Path(private_runtime.name)
    env.update(XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',XDG_CURRENT_DESKTOP='NONE',XDG_SESSION_TYPE='x11',QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',LIBGL_ALWAYS_SOFTWARE='1',KWIN_COMPOSE='N',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(runtime_path/'no-system-bus'),PULSE_SERVER='unix:'+str(runtime_path/'no-audio'),IRIX_DOMAINOS_PIN_PRIVATE='1',IRIX_DOMAINOS_PIN_DIR=str(output),LANG='C.UTF-8',LANGUAGE='en',PYTHONDONTWRITEBYTECODE='1')
    plasmoids=output/'data/plasma/plasmoids'
    for applet in (APPLET,'org.irixclassic.grosview'):
        shutil.copytree(REPO/'plasma/applets'/applet,plasmoids/applet,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for style in ('IrixClassic','IrixClassicDomainOS'):
        shutil.copytree(REPO/'plasma'/style,output/'data/plasma/desktoptheme'/style)
    fixture=plasmoids/IDENTIFIER;(fixture/'contents/ui').mkdir(parents=True)
    (fixture/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,'Name':'DomainOS pinned launch native test','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
    shutil.copyfile(REPO/'plasma/tests/DomainOSPinLaunchFixture.qml',fixture/'contents/ui/main.qml')
    marker_script=output/'pin-marker.py'
    marker_script.write_text('''import json, os, signal, sys
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QLabel
app=QApplication(sys.argv);app.setApplicationName("DomainOS own pinned client");app.setDesktopFileName("org.irixclassic.domainos.pin.launch.test")
window=QLabel("Test-owned pinned application. No account or real session data.")
window.setWindowTitle("DomainOS F32 own pinned application");window.resize(440,100);window.move(80,80);window.show()
root=Path(os.environ["IRIX_DOMAINOS_PIN_DIR"])
(root/"program-marker.json").write_text(json.dumps({"pid":os.getpid(),"argv":sys.argv,"windowId":int(window.winId()),"home":os.environ.get("HOME"),"config":os.environ.get("XDG_CONFIG_HOME"),"data":os.environ.get("XDG_DATA_HOME"),"runtime":os.environ.get("XDG_RUNTIME_DIR"),"display":os.environ.get("DISPLAY"),"bus":os.environ.get("DBUS_SESSION_BUS_ADDRESS"),"ld_preload":os.environ.get("LD_PRELOAD")}))
signal.signal(signal.SIGTERM,lambda *args:app.quit())
pump=QTimer();pump.setInterval(100);pump.timeout.connect(lambda:None);pump.start()
QTimer.singleShot(45000,app.quit)
result=app.exec();(root/"program-exited.json").write_text(json.dumps({"pid":os.getpid(),"exit":result}));raise SystemExit(result)
''')
    applications=output/'data/applications';applications.mkdir(parents=True)
    (applications/DESKTOP_ID).write_text('[Desktop Entry]\nType=Application\nName=DomainOS Private Pinned Launch\nExec=/usr/bin/env -u LD_PRELOAD /usr/bin/python3 "'+str(marker_script)+'" pin-directed-positive "argument with spaces"\nIcon=utilities-terminal\nTerminal=false\nDBusActivatable=false\nCategories=Utility;\n')
    (output/'config/kwinrc').write_text('[Compositing]\nEnabled=false\n[Desktops]\nNumber=1\nName_1=Private pin launch\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n')
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets'],text=True))
    subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(REPO/'plasma/tests/domainos-pin-launch-host.cpp'),'-o',str(output/'pin-launch-host.so'),*flags,'-ldl'],check=True)
    cache=subprocess.run(['kbuildsycoca6','--noincremental'],env=dict(env,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=20)
    (output/'sycoca.log').write_text(cache.stdout+cache.stderr)
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(runtime_path)+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    try:
        result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1100x700x24 -nolisten tcp','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output)],env=env,capture_output=True,text=True,timeout=50)
        (output/'session.log').write_text(result.stdout+result.stderr)
    finally:
        private_runtime.cleanup()
    native=json.loads((output/'native.json').read_text()) if (output/'native.json').is_file() else {}
    cleanup=json.loads((output/'cleanup.json').read_text()) if (output/'cleanup.json').is_file() else {}
    host_log=(output/'host.log').read_text() if (output/'host.log').is_file() else result.stdout+result.stderr
    errors=[line for line in host_log.splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)]
    checks=dict(native.get('checks',{}))
    checks.update(private_desktop_cache_created=cache.returncode==0,native_host_exited=result.returncode==0,qml_diagnostics_zero=not errors,eight_real_preferences_unchanged=protected_before=={name:digest(config/name) for name in PREFERENCES},production_sources_unchanged=sources_before=={str(p.relative_to(production)):digest(p) for p in sorted(production.rglob('*')) if p.is_file() and '__pycache__' not in p.parts},own_application_stopped=cleanup.get('own_program',{}).get('stopped') is True,own_private_daemons_exited=cleanup.get('own_daemons_exited') is True,short_private_runtime_removed=not runtime_path.exists())
    immediate=native.get('snapshots',{}).get('immediate_launch',{});jobs=immediate.get('jobs',{})
    helper_request={}
    if len(jobs)==1:
        arguments=shlex.split(next(iter(jobs)))
        if len(arguments)==3:
            helper_request={'command':arguments[0],'helper_path':arguments[1],'request':json.loads(arguments[2]),'token':next(iter(jobs.values()))}
    expected_helper=output/'data/plasma/plasmoids'/APPLET/'contents/code/commands.py'
    checks['real_helper_request_targets_application_and_desktop_id']=helper_request.get('helper_path')==str(expected_helper) and helper_request.get('request',{}).get('action')=='application' and helper_request.get('request',{}).get('desktopId')==DESKTOP_ID and helper_request.get('request',{}).get('token')==1
    launcher=shutil.which('kioclient6',path=env.get('PATH')) or shutil.which('kioclient',path=env.get('PATH'))
    checks['installed_kio_launcher_used_by_unmodified_helper']=bool(launcher and Path(launcher).resolve().is_relative_to(Path('/usr')) and digest(expected_helper)==digest(production/'contents/code/commands.py'))
    report={'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'native':native,'helper_request':helper_request,'installed_kio_launcher':launcher,'qml_diagnostics':errors,'cleanup':cleanup,'protected_config_sha256':{'before':protected_before,'after':{name:digest(config/name) for name in PREFERENCES}},'source_sha256':sources_before,'private_runtime_directory':str(runtime_path),'scope':'One positive production launchPin API -> DomainOSRuntime/Commands -> unmodified commands.py -> installed KIO launcher with private Desktop Entry and observed own Qt window. Actual default activity begins/finishes around request; request-accepted is not application completion. No full-panel pointer click, personal session, installation, account or global setting change.'}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'report':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
