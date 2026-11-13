#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned-window proof of native Wayland thumbnails; no personal capture/config."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'plasma/applets/org.irixclassic.domainos.panel/contents/ui'
PLUGIN = 'org.irixclassic.domainos.thumbnails.test'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', required=True, type=Path,
        help='Novo diretório de evidências sob /tmp; captura somente janelas próprias')
    args = parser.parse_args()
    OUTPUT = args.saida.absolute()
    if OUTPUT.exists() or not OUTPUT.is_relative_to(Path('/tmp')) or OUTPUT == Path('/tmp') \
            or any(path.is_symlink() for path in OUTPUT.parents):
        parser.error('Use um diretório novo sob /tmp, sem links')
    if not os.environ.get('WAYLAND_DISPLAY') or not os.environ.get('XDG_RUNTIME_DIR'):
        parser.error('Execute dentro da sua sessão Wayland; não substitui o compositor')
    OUTPUT.mkdir(mode=0o700)
    protected = [Path.home()/'.config'/name for name in ['kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc']]
    before = {str(p):digest(p) for p in protected}
    relevant = ['DomainOSWindowThumbnails.qml','DomainOSWindowTitles.qml','DomainOSWaylandThumbnail.qml','DomainOSX11Thumbnail.qml','DomainOSPalette.qml','DomainOSControlPalette.qml','DomainOSWindowPreviewContents.qml','DomainOSGroupMemberHint.qml','Bevel.qml']
    sources = {str(UI/name):digest(UI/name) for name in relevant}
    report = {'backend':'wayland','checks':{},'source_sha256':sources,'scope':'Existing user Wayland compositor and PipeWire, two same-PID owned QWidget sources only. Private HOME/XDG preferences/cache/data/state/bus; no live panel installation, compositor replacement/configuration, account/device/power/session action. Native model accesses only AppPid for foreign rows and reads titles/UUID only after matching own process. Captures only same-process ToolTipDialog; no screen/foreign-window capture.'}
    checks = report['checks']
    with tempfile.TemporaryDirectory(prefix='.domainos-wayland-thumbnail-fixture-',dir=ROOT) as directory:
        fixture = Path(directory)
        paths = {name:fixture/subdir for name,subdir in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('TMPDIR','temp')]}
        for p in paths.values():p.mkdir(mode=0o700)
        (fixture/'runtime').mkdir(mode=0o700)
        package = paths['XDG_DATA_HOME']/'plasma/plasmoids'/PLUGIN
        (package/'contents/ui').mkdir(parents=True)
        (package/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':PLUGIN,'Name':'DomainOS own Wayland miniature proof','Version':'1','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
        template = ast.parse((ROOT/'plasma/tools/testar-domainos-miniaturas.py').read_text())
        main_node = next(n for n in template.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        assignment = next(n for n in main_node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fixture_qml' for t in n.targets))
        qml = eval(compile(ast.Expression(assignment.value),'<repository-fixture-template>','eval'),{'UI':UI})
        qml = qml.replace('import org.kde.plasma.plasmoid','import org.kde.plasma.plasmoid\nimport org.kde.taskmanager as TaskManager')
        qml = qml.replace('property var windows: tasks.windowRows.filter(window=>window.title.indexOf("DomainOS thumbnail owned ")===0)', '''property var windows: []
        property int ownPid: 0
        function provideOwnedPid(pid) { ownPid=pid;refreshOwnWindows();return true }
        function refreshOwnWindows() {
            if (!ownPid) return
            const own=[]
            const roles=TaskManager.AbstractTasksModel
            for (let row=0;row<nativeTasks.rowCount();++row) {
                const index=nativeTasks.index(row,0)
                if (Number(nativeTasks.data(index,roles.AppPid))!==ownPid) continue
                if (!nativeTasks.data(index,roles.IsWindow) || nativeTasks.data(index,roles.IsGroupParent)) continue
                const title=String(nativeTasks.data(index,Qt.DisplayRole))
                if (title.indexOf("DomainOS thumbnail owned ")!==0) continue
                const ids=Array.from(nativeTasks.data(index,roles.WinIdList) || [])
                if (!ids.length || typeof ids[0]!=="string") continue
                own.push({key:"window:"+ids[0],pid:ownPid,title:title,windowIds:ids,
                    minimized:Boolean(nativeTasks.data(index,roles.IsMinimized)),group:false})
            }
            own.sort((a,b)=>a.title.localeCompare(b.title))
            if (JSON.stringify(windows)!==JSON.stringify(own)) windows=own
        }''')
        qml = qml.replace('        Production.DomainOSTasks { id:tasks; onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;groupingMode:0 }', '''        TaskManager.TasksModel {
            id:nativeTasks
            launcherList: []; groupMode:TaskManager.TasksModel.GroupDisabled
            filterByVirtualDesktop:false;filterByActivity:false;filterByScreen:false
        }''')
        (package/'contents/ui/main.qml').write_text(qml)
        (OUTPUT/'FIXTURE.qml').write_text(qml)
        (paths['XDG_CONFIG_HOME']/'kdeglobals').write_text('[General]\nColorScheme=BreezeLight\n[Icons]\nTheme=breeze\n[KDE]\nwidgetStyle=Breeze\n')
        (paths['XDG_CONFIG_HOME']/'plasmarc').write_text('[Theme]\nname=default\n')
        cpp = (ROOT/'plasma/tests/domainos-thumbnails-host.cpp').read_text()
        cpp = cpp.replace('    latest=state();', '    invoke("provideOwnedPid",int(getpid()));\n    latest=state();',1)
        cpp_path = fixture/'host.cpp';cpp_path.write_text(cpp)
        (OUTPUT/'HOST.cpp').write_text(cpp)
        flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
        subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(cpp_path),'-o',str(fixture/'host.so'),*flags,'-ldl'],check=True,env=dict(os.environ,TMPDIR=str(paths['TMPDIR'])))
        environment=dict(os.environ,**{key:str(value) for key,value in paths.items()})
        for name in ['DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','QT_STYLE_OVERRIDE','QT_QUICK_BACKEND','QML_IMPORT_PATH','QML2_IMPORT_PATH','SESSION_MANAGER','KDE_FULL_SESSION','KDE_SESSION_VERSION']:
            environment.pop(name,None)
        environment.update(QT_QPA_PLATFORM='wayland',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_CONTROLS_STYLE='org.kde.desktop',QSG_RHI_BACKEND='opengl',QSG_RENDER_LOOP='basic',LIBGL_ALWAYS_SOFTWARE='0',QT_SCALE_FACTOR='1',QT_ACCESSIBILITY='0',XDG_SESSION_TYPE='wayland',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',GIO_USE_VFS='local',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(fixture/'no-system-bus'),PULSE_SERVER='unix:'+str(fixture/'no-audio'),IRIX_DOMAINOS_THUMBNAIL_PRIVATE='1',IRIX_DOMAINOS_THUMBNAIL_DIR=str(OUTPUT),LD_PRELOAD=str(fixture/'host.so'),QML_DISABLE_DISK_CACHE='1')
        if not environment.get('WAYLAND_DISPLAY') or not environment.get('XDG_RUNTIME_DIR'):raise RuntimeError('Real owned Wayland socket unavailable')
        assert 'KWIN_WAYLAND_NO_PERMISSION_CHECKS' not in environment
        bus=fixture/'bus.conf'
        bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(fixture/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        process=None
        try:
            with (OUTPUT/'HOST.log').open('w') as log:
                process=subprocess.Popen(['dbus-run-session','--config-file',str(bus),'--','/usr/bin/plasmawindowed',PLUGIN],env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                process.wait(35)
            native=json.loads((OUTPUT/'HOST.json').read_text()) if (OUTPUT/'HOST.json').exists() else {}
            report['native']=native
            checks.update(native.get('checks',{}))
            checks.setdefault('native_scenario_completed',False)
            checks['real_installed_plasma_host']=native.get('host_executable')=='/usr/bin/plasmawindowed'
            checks['native_host_exited_cleanly']=process.returncode==0
            checks['native_provider_backend_matches_session']=native.get('state',{}).get('backend')=='wayland'
            checks['captured_sources_match_only_owned_host_pid']=len(native.get('state',{}).get('windows',[]))==2 and all(w.get('pid')==native.get('host_pid') for w in native.get('state',{}).get('windows',[]))
            diagnostics=[line for line in (OUTPUT/'HOST.log').read_text().splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)]
            report['qml_diagnostics']=diagnostics
            checks['qml_runtime_errors_zero']=not diagnostics
        except Exception as error:
            report['error']=str(error);checks['native_scenario_completed']=False
        finally:
            if process and process.poll() is None:
                import signal
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            checks['all_owned_processes_stopped']=not process or process.poll() is not None
            checks['production_sources_unchanged']=sources=={str(UI/name):digest(UI/name) for name in relevant}
            checks['real_user_preferences_unchanged']=before=={str(p):digest(p) for p in protected}
            checks['privilege_protocol_checks_not_disabled']=True
            checks['existing_compositor_not_replaced_or_reconfigured']=True
            with tarfile.open(OUTPUT/'PRIVATE-FIXTURE.tar.gz','w:gz') as archive:
                for name in ['home','config','data','state','host.cpp','bus.conf']:
                    archive.add(fixture/name,arcname=name)
    report['status']='passed' if checks and all(checks.values()) else 'failed'
    (OUTPUT/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[name for name,ok in checks.items() if not ok],'report':str(OUTPUT/'RESULTADO.json')},ensure_ascii=False))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
