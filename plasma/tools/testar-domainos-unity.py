#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Publish real Unity LauncherEntry updates to the production SmartLauncherItem.

Only a private D-Bus/Xvfb/KWin and one owned QWidget client are involved.
No arrays, fake status providers, personal services or profiles are used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
IDENTIFIER='org.irixclassic.qa.unity.fixture'
NATIVE_SOURCE=REPO/'plasma/tests/domainos-unity-host.cpp'
CONTROLS_STYLE=None
NATIVE_LIBRARIES=('Qt6Widgets','Qt6DBus')
HOST_TIMEOUT=20
RUN_TIMEOUT=35
EXTRA_APPLICATIONS={}

QML='''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
 id:host;preferredRepresentation:fullRepresentation
 fullRepresentation:Item {
  id:fixture;objectName:"domainosUnityFixture"
  Layout.minimumWidth:594;Layout.minimumHeight:150
  property int ownedPid:0;property var requests:[]
  function setOwnedPid(pid){ownedPid=pid}
  function snapshot(){
   const record=tasks.windowRows.find(row=>row.pid===ownedPid && row.title==="DomainOS Unity owned client")
   const button=record ? box.buttonForKey(record.key) : null
   const provider=record && box.nativeMenuBridge ? box.nativeMenuBridge.smartLauncherFor(record.key) : null
   function overlay(suffix){return button ? button.children.find(child=>child.objectName===button.objectName+suffix) : null}
   return JSON.stringify({rows:tasks.taskRows,requests:requests,pid:record?.pid,winId:record?.windowIds[0],launcher:record?.launcherUrl,
    providerReal:!!provider && button?.smartLauncherItem===provider,providerType:provider ? String(provider) : "",
    progress:provider?.progress,progressVisible:provider?.progressVisible,count:provider?.count,countVisible:provider?.countVisible,urgent:provider?.urgent,
    attention:tasks.demandsAttention,taskAttention:button?.demandsAttention,progressOverlayVisible:overlay("Progress")?.visible,
    countOverlayVisible:overlay("Count")?.visible,cellWidth:button?.width,cellHeight:button?.height})
  }
  Panel.DomainOSPalette {id:colors;followSystem:false}
  Panel.DomainOSTasks {id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;groupingMode:0;sortMode:1;onOperationRequested:request=>fixture.requests=fixture.requests.concat([request])}
  Panel.DomainOSIconbox {id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:true}
 }
}
'''

def worker(output):
    if os.environ.get('IRIX_DOMAINOS_UNITY_PRIVATE')!='1':raise RuntimeError('Private session required')
    with (output/'kwin.log').open('w') as log:
        wm=subprocess.Popen(['kwin_x11'],stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,timeout=2).returncode==0:break
                time.sleep(.05)
            else:raise RuntimeError('Private KWin unavailable')
            env=dict(os.environ,LD_PRELOAD=os.environ['IRIX_DOMAINOS_UNITY_LIB'],IRIX_DOMAINOS_UNITY_OUTPUT=str(output))
            result=subprocess.run(['plasmawindowed',IDENTIFIER],env=env,capture_output=True,text=True,timeout=HOST_TIMEOUT)
            (output/'host.log').write_text(result.stdout+result.stderr)
            native=json.loads((output/'native.json').read_text()) if (output/'native.json').is_file() else {}
            errors=[line for line in (result.stdout+result.stderr).splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable',line)]
            checks=native.get('checks',{});checks.update(native_host_exited=result.returncode==0,qml_diagnostics_zero=not errors)
            report={'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'native':native,'qml_diagnostics':errors,'scope':__doc__}
            (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
            return 0 if report['status']=='passed' else 1
        finally:
            wm.terminate()
            try:wm.wait(4)
            except subprocess.TimeoutExpired:wm.kill();wm.wait()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--saida',type=Path,required=True);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if output.exists() or not output.is_relative_to('/tmp') or output==Path('/tmp'):parser.error('Use a new evidence folder under /tmp')
    output.mkdir(mode=0o700);config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    def hashes():return {name:hashlib.sha256((config/name).read_bytes()).hexdigest() if (config/name).is_file() else None for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=hashes()
    with tempfile.TemporaryDirectory(prefix='.qa-domainos-unity-',dir=REPO) as folder:
        resources=Path(folder);env=os.environ.copy()
        for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','XAUTHORITY','SESSION_MANAGER','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID','PULSE_SERVER','PULSE_COOKIE'):env.pop(key,None)
        for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime'),('TMPDIR','temp')):
            p=resources/name;p.mkdir(mode=0o700);env[key]=str(p)
        plasmoids=resources/'data/plasma/plasmoids';plasmoids.mkdir(parents=True)
        (plasmoids/'org.irixclassic.domainos.panel').symlink_to(REPO/'plasma/applets/org.irixclassic.domainos.panel',target_is_directory=True)
        ui=plasmoids/IDENTIFIER/'contents/ui';ui.mkdir(parents=True)
        (plasmoids/IDENTIFIER/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,'Name':'Private Unity proof','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
        (ui/'main.qml').write_text(QML)
        themes=resources/'data/plasma/desktoptheme';themes.mkdir(parents=True)
        for name in ('IrixClassic','IrixClassicDomainOS'):(themes/name).symlink_to(REPO/'plasma'/name,target_is_directory=True)
        applications=resources/'data/applications';applications.mkdir()
        (applications/'org.irixclassic.qa.unity.desktop').write_text('[Desktop Entry]\nType=Application\nName=DomainOS Unity owned client\nExec=/bin/true\nIcon=utilities-terminal\nStartupWMClass=plasmawindowed\n')
        for filename,entry in EXTRA_APPLICATIONS.items():(applications/filename).write_text(entry)
        (resources/'config/kwinrc').write_text('[Compositing]\nEnabled=false\n[Desktops]\nNumber=1\nName_1=Private Unity proof\n')
        library=resources/'unity-host.so';flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs',*NATIVE_LIBRARIES],text=True))
        subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(NATIVE_SOURCE),'-o',str(library),*flags,'-ldl'],check=True)
        bus=resources/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(resources/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        env.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',KWIN_COMPOSE='N',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',QT_ACCESSIBILITY='0',LIBGL_ALWAYS_SOFTWARE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8',GIO_USE_VFS='local',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(resources/'no-system-bus'),PULSE_SERVER='unix:'+str(resources/'no-audio-server'),IRIX_DOMAINOS_UNITY_PRIVATE='1',IRIX_DOMAINOS_UNITY_LIB=str(library),QML_DISABLE_DISK_CACHE='1')
        if CONTROLS_STYLE:env['QT_QUICK_CONTROLS_STYLE']=CONTROLS_STYLE
        # A focused caller can reuse this bootstrap with its own worker entry.
        result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1200x700x24 -nolisten tcp','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(sys.argv[0]).resolve()),'--worker','--saida',str(output)],env=env,capture_output=True,text=True,timeout=RUN_TIMEOUT)
        (output/'runner.log').write_text(result.stdout+result.stderr)
    report=json.loads((output/'RESULTADO.json').read_text()) if (output/'RESULTADO.json').is_file() else {'status':'failed','checks':{},'error':result.stdout+result.stderr}
    report['checks']['real_profiles_unchanged']=before==hashes();report['protected_config_sha256']={'before':before,'after':hashes()}
    report['status']='passed' if report['checks'] and all(report['checks'].values()) and result.returncode==0 else 'failed'
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':report['status'],'checks':len(report['checks']),'report':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
