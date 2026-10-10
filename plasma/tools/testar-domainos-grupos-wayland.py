#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check grouped selection -> real window operations and N/L filtering on Wayland.

Production Iconbox, TasksModel, selection, activity and WindowOperations/helper
run inside the legitimate installed plasmawindowed. A private KWin virtual
output and D-Bus own every window. No privilege protocol override, real profile,
desktop-file replacement, frozen backup or existing preview is used.
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
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
APPLET=REPO/'plasma/applets/org.irixclassic.domainos.panel'
IDENTIFIER='org.irixclassic.domainos.groups.wayland.test'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    if os.environ.get('IRIX_DOMAINOS_GROUP_PRIVATE')!='1':raise RuntimeError('Private session required')
    server=outsider=host=None
    fixture_script=None
    checks={}
    report={'status':'failed','checks':checks,'backend':'wayland'}
    def start_traced(label,command,environment,stdout):
        # KWin can intentionally deny /proc/PID/environ reads even to its
        # parent. Record the inherited namespace in the child immediately
        # before exec: exec preserves this PID and environment. The Plasma
        # host independently reports its environment after the native test.
        code='import json,os,sys;from pathlib import Path;fields=("HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_RUNTIME_DIR","DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_SYSTEM_BUS_ADDRESS","PULSE_SERVER");Path(sys.argv[1]).write_text(json.dumps({"pid":os.getpid(),"namespace":{key:os.environ[key] for key in fields if key in os.environ},"observation":"immediately before exec; identical PID and inherited environment"},indent=2)+"\\n");os.execvpe(sys.argv[2],sys.argv[2:],os.environ)'
        return subprocess.Popen([sys.executable,'-c',code,str(output/('namespace-'+label+'.json')),*command],env=environment,stdout=stdout,stderr=subprocess.STDOUT)
    with (output/'SESSION.log').open('w') as log:
        try:
            server=start_traced('compositor',['kwin_wayland','--virtual','--width','1200','--height','900','--socket','domainos-groups-wayland','--no-lockscreen','--no-global-shortcuts','--no-kactivities'],dict(os.environ,QT_QPA_PLATFORM='offscreen',KWIN_COMPOSE='Q'),log)
            for _ in range(100):
                probe=subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,timeout=2)
                if probe.returncode==0:break
                if server.poll() is not None:raise RuntimeError('Private KWin exited before ready')
                time.sleep(.05)
            else:raise RuntimeError('Private KWin did not become ready')
            checks['private_wayland_compositor_ready']=True
            environment=dict(os.environ,QT_QPA_PLATFORM='wayland',WAYLAND_DISPLAY='domainos-groups-wayland')
            with (output/'outsider.log').open('w') as outsider_log,(output/'host.log').open('w') as host_log:
                outsider=start_traced('owned_outsider',[str(output/'owned-outsider'),'--desktop-id','org.irixclassic.domainos.groupoutsider','--window-title','DomainOS Wayland group outsider'],environment,outsider_log)
                host_env=dict(environment,LD_PRELOAD=str(output/'groups-host.so'),IRIX_DOMAINOS_GROUP_REPORT=str(output/'HOST.json'),IRIX_DOMAINOS_GROUP_CAPTURE=str(output/'NATIVE-WAYLAND-GROUPS.png'),IRIX_DOMAINOS_GROUP_UNSELECTED_CAPTURE=str(output/'NATIVE-WAYLAND-GROUP-NO-SELECTION.png'),IRIX_DOMAINOS_GROUP_SELECTED_CAPTURE=str(output/'NATIVE-WAYLAND-GROUP-CHECKBOX-SELECTED.png'),IRIX_DOMAINOS_GROUP_OUTSIDER_PID=str(outsider.pid))
                host=start_traced('plasma_host',['/usr/bin/plasmawindowed',IDENTIFIER],host_env,host_log)
                # A real panel is not itself a task. Wayland ignores changing
                # Qt::Tool after mapping; set only this private host's native
                # skipTaskbar flag instead of replacing/filtering TasksModel.
                script=output/'private-host-skip-taskbar.js'
                script.write_text('const hostPid='+str(host.pid)+';\nfunction hide(window){if(window.pid===hostPid && window.caption==="DomainOS grouped Wayland private test"){window.skipTaskbar=true;window.skipSwitcher=true;}}\nworkspace.windowList().forEach(hide);workspace.windowAdded.connect(hide);\n')
                fixture_script='domainos-groups-private-host-'+str(host.pid)
                loaded=subprocess.run(['qdbus6','org.kde.KWin','/Scripting','org.kde.kwin.Scripting.loadScript',str(script),fixture_script],capture_output=True,text=True,timeout=5)
                if loaded.returncode!=0 or not loaded.stdout.strip().isdecimal():raise RuntimeError('Private host placement script did not load: '+loaded.stderr)
                started=subprocess.run(['qdbus6','org.kde.KWin','/Scripting/Script'+loaded.stdout.strip(),'org.kde.kwin.Script.run'],capture_output=True,text=True,timeout=5)
                if started.returncode!=0:raise RuntimeError('Private host placement script did not run: '+started.stderr)
                process_trace={}
                for label,process in (('compositor',server),('plasma_host',host),('owned_outsider',outsider)):
                    path=output/('namespace-'+label+'.json')
                    for _ in range(100):
                        if path.exists():break
                        time.sleep(.01)
                    process_trace[label]=json.loads(path.read_text())
                (output/'PROCESSOS.json').write_text(json.dumps(process_trace,indent=2)+'\n')
                checks['owned_processes_use_private_home_xdg_and_bus']=all(entry['namespace'].get('HOME')==str(output/'home') and entry['namespace'].get('XDG_CONFIG_HOME')==str(output/'config') and entry['namespace'].get('XDG_DATA_HOME')==str(output/'data') and entry['namespace'].get('XDG_RUNTIME_DIR')==str(output/'runtime') and entry['namespace'].get('DBUS_SESSION_BUS_ADDRESS')==os.environ.get('DBUS_SESSION_BUS_ADDRESS') and 'DISPLAY' not in entry['namespace'] for entry in process_trace.values())
                report['process_namespace_trace']=process_trace
                host.wait(42)
            state=json.loads((output/'HOST.json').read_text()) if (output/'HOST.json').is_file() else {}
            checks.update(state.get('checks',{}))
            checks['native_host_exited_cleanly']=host.returncode==0
            checks['real_authorized_installed_host']=state.get('host_executable')=='/usr/bin/plasmawindowed'
            checks['native_host_self_reports_same_private_namespace_after_exec']=state.get('host_namespace_after_exec')==process_trace['plasma_host']['namespace']
            diagnostics=[line for line in (output/'host.log').read_text().splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)]
            checks['qml_runtime_errors_zero']=not diagnostics
            checks['kwin_authorized_native_protocol_without_override']='authorized "/usr/bin/plasmawindowed" "org_kde_plasma_window_management"' in (output/'SESSION.log').read_text()
            checks['independent_owned_process_remains_alive']=outsider.poll() is None
            report.update(native=state,qml_diagnostics=diagnostics,outsider_pid=outsider.pid)
        except Exception as error:report['error']=str(error);checks['native_scenario_completed']=False
        finally:
            if fixture_script and server and server.poll() is None:
                try:subprocess.run(['qdbus6','org.kde.KWin','/Scripting','org.kde.kwin.Scripting.unloadScript',fixture_script],capture_output=True,timeout=5)
                except (OSError,subprocess.TimeoutExpired) as error:report['fixture_unload_error']=str(error)
            for process in (host,outsider,server):
                if process and process.poll() is None:
                    process.terminate()
                    try:process.wait(5)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
            checks['owned_processes_exited_after_test']=all(process is None or process.poll() is not None for process in (host,outsider,server))
    report['status']='passed' if checks and all(checks.values()) else 'failed'
    (output/'NATIVO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return 0 if report['status']=='passed' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output==Path('/tmp') or output.exists():parser.error('Use a new directory under /tmp')
    output.mkdir(mode=0o700)
    environment=os.environ.copy()
    config=Path(environment.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected=lambda:{str(config/name):digest(config/name) for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=protected()
    sources={str(path.relative_to(REPO)):digest(path) for path in APPLET.rglob('*') if path.is_file() and path.suffix in ('.qml','.js','.py')}
    host_identity={str(path):digest(path) for path in (Path('/usr/bin/plasmawindowed'),Path('/usr/share/applications/org.kde.plasmawindowed.desktop'))}
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','XAUTHORITY','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID','PULSE_SERVER','PULSE_COOKIE','KWIN_WAYLAND_NO_PERMISSION_CHECKS'):
        environment.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        path=output/name;path.mkdir(mode=0o700);environment[key]=str(path)
    plasmoids=output/'data/plasma/plasmoids'
    shutil.copytree(APPLET,plasmoids/'org.irixclassic.domainos.panel',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('IrixClassic','IrixClassicDomainOS'):shutil.copytree(REPO/'plasma'/name,output/'data/plasma/desktoptheme'/name)
    fixture=plasmoids/IDENTIFIER;(fixture/'contents/ui').mkdir(parents=True)
    (fixture/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,'Name':'DomainOS grouped Wayland private test','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
    (fixture/'contents/ui/main.qml').write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosGroupsWaylandFixture"
        Layout.minimumWidth:594;Layout.minimumHeight:150
        Layout.preferredWidth:594;Layout.preferredHeight:150
        property var reports:[]
        property var requests:[]
        function state() {
            const group=tasks.taskRows.find(row=>row.group)
            return JSON.stringify({windows:tasks.windowRows,rows:tasks.taskRows,count:tasks.windowCount,
                selected:tasks.selectedKeys,groupKey:group ? group.key : "",members:group ? group.members : [],
                groupSelection:group ? tasks.selectionState(group.key) : {},groupPopup:box.groupPopupVisible,
                operationsPopup:box.operationsMenuVisible,reports:reports,requests:requests,
                effective:tasks.effectiveMinimizedOnly,threshold:tasks.automaticThreshold,filterMode:tasks.filterMode,
                backendAvailable:operations.available,pending:activity.pendingCount,desktop:tasks.currentDesktopId})
        }
        function action(name) {
            if(name==="automatic"){tasks.automaticThreshold=3;tasks.filterMode="automatic";return true}
            if(name==="equalFour" || name==="below"){tasks.automaticThreshold=4;return true}
            if(name==="aboveAgain"){tasks.automaticThreshold=3;return true}
            if(name==="restoreFirst"){
                const window=tasks.windowRows.find(row=>row.title==="DomainOS Wayland group member 0")
                return !!window && tasks.requestAction(window.key,"activate",undefined,window.pid).state==="requested"
            }
            return false
        }
        Panel.DomainOSPalette { id:colors;followSystem:false }
        Panel.DomainOSActivity { id:activity }
        Panel.DomainOSWindowOperations { id:operations;activity:activity;onReported:report=>fixture.reports=fixture.reports.concat([report]) }
        Panel.DomainOSTasks {
            id:tasks;onlyCurrentDesktop:false;onlyCurrentScreen:false;onlyCurrentActivity:false
            groupingMode:1;onlyGroupWhenFull:false;sortMode:1;geometryBackend:operations
            currentScreenGeometry:Qt.rect(Screen.virtualX,Screen.virtualY,Screen.width,Screen.height)
            currentAvailableGeometry:currentScreenGeometry;currentScreenName:Screen.name
            onOperationRequested:request=>fixture.requests=fixture.requests.concat([request])
        }
        Panel.DomainOSIconbox { id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:false }
    }
}
''')
    (output/'config/kwinrc').write_text('[Desktops]\nNumber=1\nName_1=Private grouped Wayland test\n[Compositing]\nEnabled=true\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n')
    (output/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
    environment.update(QT_QPA_PLATFORM='wayland',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',LIBGL_ALWAYS_SOFTWARE='1',QT_SCALE_FACTOR='1',QT_ACCESSIBILITY='0',XDG_SESSION_TYPE='wayland',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',GIO_USE_VFS='local',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio'),QT_LOGGING_RULES='kwin_core.debug=true',IRIX_DOMAINOS_GROUP_PRIVATE='1')
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
    subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(REPO/'plasma/tests/domainos-groups-wayland-host.cpp'),'-o',str(output/'groups-host.so'),*flags,'-ldl'],check=True)
    subprocess.run(['c++','-std=c++17',str(REPO/'plasma/tests/fixture-window.cpp'),'-o',str(output/'owned-outsider'),*flags],check=True)
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    with (output/'runner.log').open('w') as log:
        runner=subprocess.Popen(['dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output)],env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:runner.wait(55)
        except subprocess.TimeoutExpired:
            # Every child belongs to this new private process group. Stop that
            # group, never an existing desktop or another test's process.
            os.killpg(runner.pid,signal.SIGTERM)
            try:runner.wait(5)
            except subprocess.TimeoutExpired:os.killpg(runner.pid,signal.SIGKILL);runner.wait()
    report=json.loads((output/'NATIVO.json').read_text()) if (output/'NATIVO.json').is_file() else {'status':'failed','checks':{},'error':(output/'runner.log').read_text()}
    checks=report['checks']
    checks.update(private_worker_exited_cleanly=runner.returncode==0,real_profiles_unchanged=before==protected(),production_sources_unchanged=all(digest(REPO/name)==value for name,value in sources.items()),installed_authorized_host_identity_unchanged=host_identity=={name:digest(Path(name)) for name in host_identity},privilege_protocol_checks_not_disabled='KWIN_WAYLAND_NO_PERMISSION_CHECKS' not in environment,no_artificial_desktop_entries=not (output/'data/applications').exists())
    report.update(protected_config_sha256={'before':before,'after':protected()},source_sha256=sources,host_identity_sha256=host_identity,scope='Actual grouped checkbox/title/menu gestures, including direct title restoration of a minimized member without checkbox selection and selection-only title toggles once checked. Production Iconbox -> Tasks -> WindowOperations -> transient KWin helper, owned native Wayland UUIDs/PIDs, real geometry/minimized results and before-filter/before-group N/L counting. Private compositor/session/data only; no real profile or existing preview was changed.',protocol_limit='xdg_toplevel does not expose a minimized configure state to QWidget. External minimization is confirmed by KWin helper results and the separate native TasksModel observation; native title restoration is additionally confirmed by owned client focus. No QWidget::isMinimized claim is made for the external batch.')
    report['status']='passed' if checks and all(checks.values()) else 'failed'
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'result':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
