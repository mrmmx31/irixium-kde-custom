#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical minimize/restore regression with a test-owned X11 client and KWin.

Production QML is imported read-only from the repository. Completed immutable
fixture themes are reused through XDG_DATA_DIRS, without another applet/icon copy.
Every process, D-Bus connection, display and writable directory is private.
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
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
APPLET='org.irixclassic.domainos.minimized.relief.test'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    if os.environ.get('IRIX_DOMAINOS_RELIEF_PRIVATE')!='1':raise RuntimeError('Private session required')
    compositor=host=None
    with (output/'SESSION.log').open('w') as log:
        try:
            compositor=subprocess.Popen(['kwin_x11','--replace'],stdout=log,stderr=subprocess.STDOUT)
            for _ in range(100):
                probe=subprocess.run(['qdbus6','org.kde.KWin','/KWin'],capture_output=True,timeout=2)
                if probe.returncode==0:break
                if compositor.poll() is not None:raise RuntimeError('Private compositor exited')
                time.sleep(.05)
            else:raise RuntimeError('Private compositor unavailable')
            env=dict(os.environ,LD_PRELOAD=str(output/'relief-host.so'),IRIX_DOMAINOS_RELIEF_DIR=str(output))
            with (output/'host.log').open('w') as host_log:
                host=subprocess.Popen(['/usr/bin/plasmawindowed',APPLET],env=env,stdout=host_log,stderr=subprocess.STDOUT)
                host.wait(25)
            return host.returncode
        finally:
            for process in (host,compositor):
                if process and process.poll() is None:
                    process.terminate()
                    try:process.wait(3)
                    except subprocess.TimeoutExpired:process.kill();process.wait()


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
    env=os.environ.copy();config=Path(env.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected=lambda:{name:digest(config/name) for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=protected()
    sources={name:digest(REPO/'plasma/applets/org.irixclassic.domainos.panel/contents/ui'/name) for name in ('DomainOSTaskButton.qml','DomainOSTasks.qml','DomainOSIconbox.qml')}
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','XAUTHORITY','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID'):
        env.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        folder=output/name;folder.mkdir(mode=0o700);env[key]=str(folder)
    fixture=output/'data/plasma/plasmoids'/APPLET;(fixture/'contents/ui').mkdir(parents=True)
    (fixture/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':APPLET,'Name':'DomainOS minimized relief private test','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
    ui=(REPO/'plasma/applets/org.irixclassic.domainos.panel/contents/ui').as_uri()
    (fixture/'contents/ui/main.qml').write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "'''+ui+'''" as Panel
PlasmoidItem {
    id:host;preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosMinimizedReliefFixture"
        Layout.minimumWidth:610;Layout.minimumHeight:170
        readonly property var ownedRecord:tasks.windowRows.find(row=>row.title==="DomainOS owned minimized relief client") || null
        readonly property Item ownedTile:ownedRecord ? find(box,"domainosLiveTask_"+ownedRecord.key) : null
        function find(item,name){if(item.objectName===name)return item;for(const child of item.children){const hit=find(child,name);if(hit)return hit;}return null;}
        property string snapshotJson:JSON.stringify({row:ownedRecord,selected:tasks.selectedKeys,
            visual:ownedTile ? ({selected:ownedTile.selected,pressed:ownedTile.pressed,fullyMinimized:ownedTile.fullyMinimized,
                bodySunken:find(ownedTile,ownedTile.objectName+"Relief").sunken,labelSunken:find(ownedTile,ownedTile.objectName+"Label").sunken}) : null})
        Panel.DomainOSPalette{id:colors;followSystem:false}
        Panel.DomainOSTasks{id:tasks;onlyCurrentDesktop:false;onlyCurrentScreen:false;onlyCurrentActivity:false;groupingMode:0;filterMode:"normal"}
        Panel.DomainOSIconbox{id:box;x:8;y:10;width:594;height:150;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:false}
    }
}
''')
    (output/'config/kwinrc').write_text('[Desktops]\nNumber=1\n[Compositing]\nEnabled=false\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n')
    (output/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
    env.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',QML_DISABLE_DISK_CACHE='1',QT_SCALE_FACTOR='1',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS=str(resources/'data')+':/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio'),IRIX_DOMAINOS_RELIEF_PRIVATE='1')
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets'],text=True))
    subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(REPO/'plasma/tests/domainos-minimized-relief-host.cpp'),'-o',str(output/'relief-host.so'),*flags,'-ldl'],check=True)
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    result=subprocess.run(['xvfb-run','--auto-servernum','--server-args=-screen 0 1200x900x24','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output),'--recursos-encerrados',str(resources)],env=env,capture_output=True,text=True,timeout=35)
    (output/'runner.log').write_text(result.stdout+result.stderr)
    native=json.loads((output/'HOST.json').read_text()) if (output/'HOST.json').exists() else {}
    log=(output/'host.log').read_text() if (output/'host.log').exists() else result.stderr
    diagnostics=[line for line in log.splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable',line)]
    checks=native.get('checks',{})
    checks.update(native_host_exited_cleanly=result.returncode==0 and not native.get('failure'),qml_runtime_errors_zero=not diagnostics,
        real_profiles_unchanged=before==protected(),production_sources_unchanged=all(digest(REPO/'plasma/applets/org.irixclassic.domainos.panel/contents/ui'/name)==value for name,value in sources.items()),
        real_installed_native_host=native.get('hostExecutable')=='/usr/bin/plasmawindowed')
    report={'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'native':native,'qml_diagnostics':diagnostics,'source_sha256':sources,'protected_config_sha256':{'before':before,'after':protected()},'scope':'Physical xdotool pointer, owned native QWidget minimization and native TasksModel restoration inside a private KWin/Xvfb/D-Bus. No existing preview, real profile, installed host or immutable resources are changed.'}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'result':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
