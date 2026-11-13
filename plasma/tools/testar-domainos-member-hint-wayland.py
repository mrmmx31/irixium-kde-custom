#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Directed hint leases in actual native private Wayland windows.

Qt QTest input enters the native QWindow event path. Explicit QPA Leave/Enter
pairs cover native surface transitions omitted by QTest.mouseMove. This does not
claim physical compositor-seat routing, pixel capture or any real profile change.
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
import tarfile
import tempfile
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
APPLET=REPO/'plasma/applets/org.irixclassic.domainos.panel'
IDENTIFIER='org.irixclassic.domainos.memberhint.wayland.test'
TITLE='DomainOS member hint private Wayland test'
FILES=[APPLET/'contents/ui'/name for name in (
    'DomainOSGroupMemberHint.qml','DomainOSWindowPreviewContents.qml','DomainOSIconbox.qml',
    'DomainOSTaskButton.qml','DomainOSWindowThumbnails.qml','DomainOSTasks.qml',
    'DomainOSPopupPlacement.qml','DomainOSPopupToggle.qml')]
TESTS=[Path(__file__).resolve(),REPO/'plasma/tests/domainos-member-hint-wayland-host.cpp']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def worker(output):
    if os.environ.get('IRIX_DOMAINOS_HINT_PRIVATE')!='1':raise RuntimeError('Private bus required')
    report={'checks':{},'backend':'wayland'};checks=report['checks'];processes=[];script_name=None
    with (output/'SESSION.log').open('w') as session:
        try:
            server=subprocess.Popen(['kwin_wayland','--virtual','--width','1200','--height','900',
                '--socket','domainos-member-hints','--no-lockscreen','--no-global-shortcuts','--no-kactivities'],
                env=dict(os.environ,QT_QPA_PLATFORM='offscreen',KWIN_COMPOSE='Q'),stdout=session,stderr=subprocess.STDOUT)
            processes.append(server)
            for _ in range(100):
                probe=subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,timeout=2)
                if probe.returncode==0:break
                if server.poll() is not None:raise RuntimeError('Own compositor exited before ready')
                time.sleep(.05)
            else:raise RuntimeError('Own compositor did not become ready')
            checks['private_wayland_compositor_ready']=True
            environment=dict(os.environ,QT_QPA_PLATFORM='wayland',WAYLAND_DISPLAY='domainos-member-hints',
                LD_PRELOAD=str(output/'member-hint-host.so'),IRIX_DOMAINOS_HINT_DIR=str(output),
                IRIX_DOMAINOS_HINT_REPORT=str(output/'HOST.json'))
            with (output/'host.log').open('w') as log:
                host=subprocess.Popen(['/usr/bin/plasmawindowed',IDENTIFIER],env=environment,stdout=log,stderr=subprocess.STDOUT)
                processes.append(host)
                script=output/'own-panel-placement.js'
                script.write_text('const pid='+str(host.pid)+';\nfunction place(window){if(window.pid===pid && window.caption==='+json.dumps(TITLE)+'){window.skipTaskbar=true;window.skipSwitcher=true;}}\nworkspace.windowList().forEach(place);workspace.windowAdded.connect(place);\n')
                script_name='domainos-memberhint-own-panel-'+str(host.pid)
                loaded=subprocess.run(['qdbus6','org.kde.KWin','/Scripting','org.kde.kwin.Scripting.loadScript',str(script),script_name],capture_output=True,text=True,timeout=5)
                if loaded.returncode or not loaded.stdout.strip().isdecimal():raise RuntimeError('Own placement script failed: '+loaded.stderr)
                started=subprocess.run(['qdbus6','org.kde.KWin','/Scripting/Script'+loaded.stdout.strip(),'org.kde.kwin.Script.run'],capture_output=True,timeout=5)
                if started.returncode:raise RuntimeError('Own placement script did not run')
                host.wait(50)
            native=json.loads((output/'HOST.json').read_text()) if (output/'HOST.json').is_file() else {}
            if not native and (output/'PROGRESS.json').is_file():report['last_checkpoint']=json.loads((output/'PROGRESS.json').read_text())
            report['host_exit_code']=host.returncode
            checks.update(native.get('checks',{}));checks['native_host_exited_cleanly']=host.returncode==0
            checks['legitimate_installed_host_identity']=native.get('host_executable')=='/usr/bin/plasmawindowed'
            namespace=native.get('host_namespace_after_exec',{})
            checks['host_inherits_only_private_home_xdg_bus']=all(namespace.get(key)==os.environ[key] for key in ('HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS'))
            checks['private_wayland_has_no_real_display']='DISPLAY' not in environment
            logs=(output/'host.log').read_text()
            diagnostics=[line for line in logs.splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Unexpected token|error when loading applet|Error loading QML|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)]
            protocol=[line for line in ((output/'SESSION.log').read_text()+'\n'+logs).splitlines() if re.search(r'xdg_surface is already mapped|fatal.*protocol|error .*xdg_popup|Wayland display.*error',line,re.I)]
            checks['qml_runtime_errors_zero']=not diagnostics;checks['no_wayland_popup_protocol_errors']=not protocol
            checks['native_window_protocol_authorized_without_override']='authorized "/usr/bin/plasmawindowed" "org_kde_plasma_window_management"' in (output/'SESSION.log').read_text()
            report.update(native=native,qml_diagnostics=diagnostics,wayland_protocol_errors=protocol)
        except Exception as error:report['error']=str(error);checks['native_scenario_completed']=False
        finally:
            if script_name and processes and processes[0].poll() is None:
                try:subprocess.run(['qdbus6','org.kde.KWin','/Scripting','org.kde.kwin.Scripting.unloadScript',script_name],capture_output=True,timeout=5)
                except (OSError,subprocess.TimeoutExpired) as error:report['unload_error']=str(error)
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(5)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
            checks['all_owned_processes_exited_after_test']=all(process.poll() is not None for process in processes)
    report['status']='passed' if checks and all(checks.values()) else 'failed'
    (output/'NATIVO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return 0 if report['status']=='passed' else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--saida',required=True,type=Path);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();destination=args.saida.resolve()
    if args.worker:return worker(destination)
    if not destination.is_relative_to(Path('/tmp')) or destination==Path('/tmp') or destination.exists():parser.error('Use a new /tmp directory')
    destination.mkdir(mode=0o700)
    protected=[Path.home()/'.config'/name for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')]
    before={str(path):digest(path) for path in protected};sources={str(path.relative_to(REPO)):digest(path) for path in FILES};tests={str(path.relative_to(REPO)):digest(path) for path in TESTS}
    installed=[Path('/usr/bin/plasmawindowed'),Path('/usr/share/applications/org.kde.plasmawindowed.desktop')];installed_before={str(path):digest(path) for path in installed}
    with tempfile.TemporaryDirectory(prefix='.mh-qa-',dir=REPO) as private:
        output=Path(private);env=os.environ.copy()
        for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','XAUTHORITY','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID','PULSE_SERVER','PULSE_COOKIE','KWIN_WAYLAND_NO_PERMISSION_CHECKS'):env.pop(key,None)
        for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime'),('TMPDIR','tmp')):(output/name).mkdir(mode=0o700);env[key]=str(output/name)
        plasmoids=output/'data/plasma/plasmoids';shutil.copytree(APPLET,plasmoids/'org.irixclassic.domainos.panel',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in ('IrixClassic','IrixClassicDomainOS'):shutil.copytree(REPO/'plasma'/name,output/'data/plasma/desktoptheme'/name)
        fixture=plasmoids/IDENTIFIER;(fixture/'contents/ui').mkdir(parents=True)
        (fixture/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,'Name':TITLE,'Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
        (fixture/'contents/ui/main.qml').write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
 id:host;preferredRepresentation:fullRepresentation
 fullRepresentation:Item {
  id:fixture;objectName:"domainosMemberHintFixture"
  Layout.minimumWidth:900;Layout.minimumHeight:830;Layout.preferredWidth:900;Layout.preferredHeight:830
  property var requests:[]
  property var tracedHint:null
  function trackHint(value){tracedHint=value;return true}
  function selectorPoint(target){return JSON.stringify({active:target.active,hovered:target.hovered,x:target.point.position.x,y:target.point.position.y,
   sceneX:target.point.scenePosition.x,sceneY:target.point.scenePosition.y,
   globalX:target.parent.mapToGlobal(target.point.position).x,globalY:target.parent.mapToGlobal(target.point.position).y})}
  Connections {
   id:trace;target:fixture.tracedHint
   function onLeaseActiveChanged(){if(!trace.target.leaseActive)console.log("PRIVATE_QA_HINT_RELEASE",new Error().stack,
    JSON.stringify({hovered:trace.target.hovered,previewHovered:trace.target.previewHovered,
     suppressed:trace.target.hoverSuppressed,rowX:trace.target.rowPosition.x,rowY:trace.target.rowPosition.y}))}
  }
  function state(){return JSON.stringify({windows:tasks.windowRows,rows:tasks.taskRows,count:tasks.windowCount,
   groupPopup:box.groupPopupVisible,operationsPopup:box.operationsMenuVisible,requests:requests,
   memberKeys:tasks.memberSelectionKeys,hintDelay:Kirigami.Units.toolTipDelay})}
  function hints(value){box.hintsEnabled=value;return true}
  function previews(value){box.thumbnailsEnabled=value;return true}
  function grouping(value){tasks.groupingMode=value;return true}
  function clearRequests(){requests=[];return true}
  function resetUi(){box.batchContextMenu.close();tasks.clearSelection();requests=[];return true}
  Panel.DomainOSPalette{id:colors;followSystem:false}
  Panel.DomainOSTasks{id:tasks;onlyCurrentDesktop:false;onlyCurrentScreen:false;onlyCurrentActivity:false;
   groupingMode:0;onlyGroupWhenFull:false;sortMode:1
   onOperationRequested:request=>fixture.requests=fixture.requests.concat([{state:request.state,action:request.action,key:request.key,observedTargetPid:tasks.windowFor(request.key)?.pid}])}
  Panel.DomainOSIconbox{id:box;x:150;y:620;width:594;height:150;controller:tasks;colorPalette:colors;hostItem:host;
   nativeMenusEnabled:false;hintsEnabled:true;thumbnailsEnabled:false}
 }
}''')
        (output/'config/kwinrc').write_text('[Desktops]\nNumber=1\nName_1=Private member hint test\n[Compositing]\nEnabled=true\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n')
        (output/'config/kdeglobals').write_bytes((REPO/'colors/DomainOS-SR10.4.colors').read_bytes())
        env.update(QT_QPA_PLATFORM='wayland',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',QML_DISABLE_DISK_CACHE='1',LIBGL_ALWAYS_SOFTWARE='1',QT_SCALE_FACTOR='1',QT_ACCESSIBILITY='0',XDG_SESSION_TYPE='wayland',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',GIO_USE_VFS='local',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio'),QT_LOGGING_RULES='kwin_core.debug=true',IRIX_DOMAINOS_HINT_PRIVATE='1')
        # Parse the exact private fixture before paying for a compositor. Ready
        # proves syntax/import resolution only: no object/native TasksModel is
        # created and no permission or capability is simulated.
        syntax_code='''import json,sys,time
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
from PyQt6.QtQml import QQmlEngine,QQmlComponent
app=QApplication([]);engine=QQmlEngine();component=QQmlComponent(engine)
source=Path(sys.argv[1]).read_text().replace('import org.kde.plasma.plasmoid\\n','').replace(
 'PlasmoidItem {\\n id:host;preferredRepresentation:fullRepresentation\\n fullRepresentation:Item {',
 'Item {\\n id:host\\n property Component fullRepresentation:Item {')
component.setData(source.encode(),QUrl.fromLocalFile(sys.argv[1]))
deadline=time.monotonic()+5
while component.isLoading() and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
ready=component.status()==QQmlComponent.Status.Ready
Path(sys.argv[2]).write_text(json.dumps({'ready':ready,'errors':[error.toString() for error in component.errors()],'scope':'Compile only the unchanged inner fixture body through an Item/Component wrapper; the PlasmoidItem type is registered only by the genuine host. No create, native model or permission simulation.'},indent=2)+'\\n')
raise SystemExit(0 if ready else 1)
'''
        with (output/'SYNTAX.log').open('w') as log:
            syntax=subprocess.run([sys.executable,'-B','-c',syntax_code,str(fixture/'contents/ui/main.qml'),str(output/'SYNTAX.json')],env=dict(env,QT_QPA_PLATFORM='offscreen'),stdout=log,stderr=subprocess.STDOUT,timeout=10)
        if syntax.returncode:
            report={'status':'failed','stage':'fixture_compile_preflight','checks':{'fixture_inner_qml_syntax_ready':False},
                'diagnostics':(output/'SYNTAX.log').read_text(),'scope':'No compositor or native host started.'}
            if (output/'SYNTAX.json').is_file():report['syntax']=json.loads((output/'SYNTAX.json').read_text())
            (destination/'RESULTADO.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({'status':'failed','stage':report['stage'],'result':str(destination/'RESULTADO.json')}));return 1
        flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
        subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(TESTS[1]),'-o',str(output/'member-hint-host.so'),*flags,'-ldl'],check=True,env=env)
        bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        with (output/'runner.log').open('w') as log:
            runner=subprocess.Popen(['dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output)],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:runner.wait(60)
            except subprocess.TimeoutExpired:
                os.killpg(runner.pid,signal.SIGTERM)
                try:runner.wait(5)
                except subprocess.TimeoutExpired:os.killpg(runner.pid,signal.SIGKILL);runner.wait()
        report=json.loads((output/'NATIVO.json').read_text()) if (output/'NATIVO.json').is_file() else {'checks':{},'error':(output/'runner.log').read_text()}
        checks=report['checks'];after={str(path):digest(path) for path in protected}
        checks.update(fixture_inner_qml_syntax_ready=True,private_worker_exited_cleanly=runner.returncode==0,real_profiles_unchanged=before==after,
            relevant_production_sources_unchanged=all(digest(REPO/name)==value for name,value in sources.items()),
            test_sources_unchanged=all(digest(REPO/name)==value for name,value in tests.items()),
            installed_authorized_host_unchanged=installed_before=={str(path):digest(path) for path in installed},
            native_protocol_permission_checks_not_disabled='KWIN_WAYLAND_NO_PERMISSION_CHECKS' not in env)
        report.update(source_sha256=sources,test_source_sha256=tests,protected_config_sha256={'before':before,'after':after},
            scope='Actual production Iconbox/Tasks and two own QWidget native UUID/PID clients. QPA Leave/Enter pairs are flushed together before QTest native QWindow MouseMove/Press/Release, with observed DPR 1 and QPointer guards. No direct QML handlers or fabricated native identities. Private Wayland compositor/bus/profile; no claim about physical compositor-seat input or positive thumbnail pixels. No personal profile/window/device changed.')
        report['status']='passed' if checks and all(checks.values()) else 'failed'
        artifact=destination/'PRIVATE-PROOF.tar.gz'
        with tarfile.open(artifact,'w:gz') as archive:
            for path in sorted(output.iterdir()):
                if path.name not in ('runtime','tmp','cache'):archive.add(path,arcname=path.name)
        report['artifact']={'path':str(artifact),'sha256':digest(artifact),'bytes':artifact.stat().st_size}
        (destination/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        for path in output.glob('*.png'):shutil.copy2(path,destination/path.name)
    print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[name for name,value in checks.items() if value is not True],'result':str(destination/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
