#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Physically activate owned windows through geometric Pager rectangles.

Every desktop/window action runs inside private Xvfb/KWin/D-Bus. Production
QML is imported directly. Profiles/cache use the workspace filesystem; /tmp
contains only the final reports, own-window PNGs and archived fixture.
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
import tarfile
import tempfile
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
UI=ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/ui'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def setup(output,backend):
    if output.exists():raise SystemExit('Use a new output directory')
    output.mkdir(mode=0o700,parents=True)
    protected=[Path.home()/'.config'/name for name in ['kdeglobals','plasmarc','kwinrc','plasma-org.kde.plasma.desktop-appletsrc']]
    before={str(path):digest(path) for path in protected}
    sources={str(UI/name):digest(UI/name) for name in ['DomainOSDesktopTile.qml','DomainOSPager.qml','PanelButton.qml','DomainOSPalette.qml']}
    with tempfile.TemporaryDirectory(prefix='.domainos-pager-windows-fixture-',dir=ROOT) as directory:
        fixture=Path(directory)
        paths={name:fixture/subdir for name,subdir in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')]}
        for path in paths.values():path.mkdir(mode=0o700)
        (paths['XDG_CONFIG_HOME']/'kwinrc').write_text('[Desktops]\nNumber=2\nRows=1\nName_1=First\nName_2=Second\n[Compositing]\nEnabled=false\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n')
        (paths['XDG_CONFIG_HOME']/'kdeglobals').write_text((ROOT/'colors/DomainOS-SR10.4.colors').read_text())
        (paths['XDG_CONFIG_HOME']/'plasmarc').write_text('[Theme]\nname=default\n')
        bus=fixture/'bus.conf'
        bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(paths['XDG_RUNTIME_DIR'])+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        env=dict(os.environ,**{name:str(path) for name,path in paths.items()})
        for name in ['DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','XAUTHORITY','LD_PRELOAD','QT_STYLE_OVERRIDE','QML_IMPORT_PATH','QML2_IMPORT_PATH','KDE_FULL_SESSION','KDE_SESSION_VERSION']:
            env.pop(name,None)
        env.update(QT_QPA_PLATFORM='xcb',QT_QUICK_BACKEND='software',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_CONTROLS_STYLE='org.kde.desktop',QT_ACCESSIBILITY='0',LIBGL_ALWAYS_SOFTWARE='1',KWIN_COMPOSE='N',QML_DISABLE_DISK_CACHE='1',XDG_CURRENT_DESKTOP='NONE',XDG_CONFIG_DIRS='/etc/xdg',XDG_DATA_DIRS='/usr/local/share:/usr/share',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(fixture/'no-system-bus'))
        if backend=='wayland':
            package=paths['XDG_DATA_HOME']/'plasma/plasmoids/org.irixclassic.domainos.pager.test'
            (package/'contents/ui').mkdir(parents=True)
            (package/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':'org.irixclassic.domainos.pager.test','Name':'DomainOS owned Pager Wayland proof','Version':'1','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
            (package/'contents/ui/main.qml').write_text(wayland_qml())
            flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
            subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(ROOT/'plasma/tests/domainos-pager-window-host.cpp'),'-o',str(fixture/'host.so'),*flags,'-ldl'],check=True)
            env.update(QT_QPA_PLATFORM='offscreen',KWIN_COMPOSE='Q',IRIX_DOMAINOS_PAGER_WINDOW_PRIVATE='1',IRIX_DOMAINOS_PAGER_WINDOW_DIR=str(output),IRIX_DOMAINOS_PAGER_WINDOW_HOST=str(fixture/'host.so'))
        command=['dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output),'--backend',backend]
        if backend=='x11':command=['xvfb-run','--auto-servernum','--server-args=-screen 0 1200x900x24',*command]
        with (output/'RUNNER.log').open('w') as log:
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=70)
        report=json.loads((output/'NATIVO.json').read_text()) if (output/'NATIVO.json').exists() else {'checks':{},'error':(output/'RUNNER.log').read_text()}
        report['checks'].update(native_worker_exited_cleanly=result.returncode==0,
            protected_user_configuration_hashes_preserved=before=={str(p):digest(p) for p in protected},
            production_sources_unchanged=sources=={name:digest(Path(name)) for name in sources})
        report['source_sha256']=sources
        report['backend']=backend
        report['scope']='Production Pager/DesktopTile in private KWin/'+backend+'/session bus and HOME/XDG (Xvfb only X11; installed authorized plasmawindowed only Wayland). Only same-process QWidget targets; physical Qt input, native window focus/desktops/minimization, stale-identity rejection. No live panel/profile/compositor or frozen backup modified.'
        with tarfile.open(output/'PRIVATE-FIXTURE.tar.gz','w:gz') as archive:
            for name in ['home','config','data','state','bus.conf']:archive.add(fixture/name,arcname=name)
    report['status']='passed' if report['checks'] and all(report['checks'].values()) else 'failed'
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(report['checks']),'failed':[name for name,ok in report['checks'].items() if not ok],'report':str(output/'RESULTADO.json')},ensure_ascii=False))
    return 0 if report['status']=='passed' else 1

def wayland_qml():
    return '''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager
import org.kde.kwindowsystem
import "'''+UI.as_uri()+'''" as Production
PlasmoidItem {
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosPagerOwnedFixture"
        Layout.minimumWidth:700;Layout.minimumHeight:400
        property int ownPid:0
        property var operations:[]
        property var errors:[]
        function hostGeometryPresent(item){
            if(item.windowTitle!==undefined && item.windowTitle==="DOMAINOS-GEOMETRY-HOST")return true
            for(const child of item.children || [])if(hostGeometryPresent(child))return true
            return false
        }
        function setOwnedPid(pid){ownPid=Number(pid);return true}
        function ownWindows(){
            const windows=[],roles=TaskManager.AbstractTasksModel
            for(let row=0;row<ownTasks.rowCount();++row){
                const index=ownTasks.index(row,0)
                if(Number(ownTasks.data(index,roles.AppPid))!==ownPid)continue
                if(!ownTasks.data(index,roles.IsWindow) || ownTasks.data(index,roles.IsGroupParent))continue
                const title=String(ownTasks.data(index,Qt.DisplayRole))
                if(title.indexOf("DOMAINOS-GEOMETRY-OWN-")!==0)continue
                windows.push({index:index,title:title,pid:ownPid,windowIds:Array.from(ownTasks.data(index,roles.WinIdList)||[])})
            }
            return windows
        }
        function testState(){return JSON.stringify({available:pager.available,desktops:pager.desktopRecords,
            current:pager.currentDesktopId,pendingActivations:pager.pendingActivations,width:pager.width,height:pager.height,
            backend:KWindowSystem.isPlatformWayland ? "wayland":"other",hostPresentInPager:hostGeometryPresent(pager),ownWindows:ownWindows().map(window=>
                ({title:window.title,pid:window.pid,ids:window.windowIds})),operations:operations.length,
            lastOperation:operations.length ? operations[operations.length-1].operation:"",errors:errors})}
        function activateOwn(title){
            const target=ownWindows().find(window=>window.title===title)
            if(!target)return false
            ownTasks.requestActivate(target.index);return true
        }
        function activateOwnHost(){
            const roles=TaskManager.AbstractTasksModel
            for(let row=0;row<ownTasks.rowCount();++row){
                const index=ownTasks.index(row,0)
                if(Number(ownTasks.data(index,roles.AppPid))!==ownPid)continue
                if(String(ownTasks.data(index,Qt.DisplayRole))!=="DOMAINOS-GEOMETRY-HOST")continue
                ownTasks.requestActivate(index);return true
            }
            return false
        }
        function moveOwnSecond(position){
            const target=ownWindows().find(window=>window.title==="DOMAINOS-GEOMETRY-OWN-1")
            const id=desktops.desktopIds[Number(position)]
            if(!target || id===undefined)return false
            ownTasks.requestVirtualDesktops(target.index,[id]);return true
        }
        function secondIdentity(){
            const target=ownWindows().find(window=>window.title==="DOMAINOS-GEOMETRY-OWN-1")
            return JSON.stringify(target ? {windowIds:target.windowIds,pid:target.pid}:null)
        }
        function rejectWrongIdentities(){
            const identity=JSON.parse(secondIdentity());if(!identity)return false
            return !pager.activateWindow(pager.desktopRecords[1].id,{windowIds:identity.windowIds,pid:identity.pid+1})
                && !pager.activateWindow(pager.desktopRecords[0].id,identity)
        }
        function activateOldIdentity(identity){return pager.activateWindow(pager.desktopRecords[1].id,JSON.parse(identity))}
        function activateDesktopPosition(position){return pager.activateDesktop(pager.desktopRecords[Number(position)].id)}
        TaskManager.VirtualDesktopInfo{id:desktops}
        TaskManager.TasksModel{id:ownTasks;launcherList:[];groupMode:TaskManager.TasksModel.GroupDisabled;
            filterByVirtualDesktop:false;filterByActivity:false;filterByScreen:false}
        Item {
            x:12;y:12;width:342;height:150
            readonly property real domainosRenderScale:1
            Production.DomainOSPager {
                id:pager;anchors.fill:parent
                onOperationFinished:(operation,success,details)=>fixture.operations=fixture.operations.concat([{operation:operation,success:success,details:details}])
                onFailure:message=>fixture.errors=fixture.errors.concat([message])
            }
        }
    }
}
'''

def worker_wayland(output):
    checks={};report={'checks':checks};compositor=None;host=None
    try:
        with (output/'KWIN.log').open('w') as log:
            compositor=subprocess.Popen(['kwin_wayland','--virtual','--width','1200','--height','900','--socket','domainos-pager-own-wayland','--no-lockscreen','--no-global-shortcuts','--no-kactivities'],stdout=log,stderr=subprocess.STDOUT)
        for _ in range(100):
            ready=subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,text=True,timeout=2)
            if ready.returncode==0:break
            if compositor.poll() is not None:raise RuntimeError('Private KWin Wayland exited')
            time.sleep(.05)
        if ready.returncode:raise RuntimeError('Private KWin Wayland not ready')
        checks['private_kwin_wayland_ready']=True
        # Ordinary Wayland QWidget.move() is ignored. Position ONLY our two
        # test sources through the private compositor, and keep the normal
        # plasmawindowed controller out of the Pager like a real Dock panel.
        script=Path(os.environ['HOME']).parent/'owned-geometry.js'
        script.write_text('''const positioned={};
function configure(window){
    if(window.caption==="DOMAINOS-GEOMETRY-HOST"){
        window.skipPager=true;window.onAllDesktops=true;return;
    }
    if(window.caption!=="DOMAINOS-GEOMETRY-OWN-0" && window.caption!=="DOMAINOS-GEOMETRY-OWN-1")return;
    const id=String(window.internalId);if(positioned[id])return;positioned[id]=true;
    const second=window.caption==="DOMAINOS-GEOMETRY-OWN-1";
    window.frameGeometry={x:second ? 630:90,y:second ? 230:120,width:320,height:240};
}
workspace.windowAdded.connect(function(window){configure(window);window.captionChanged.connect(function(){configure(window)});});
workspace.windowList().forEach(configure);
''')
        script_id=subprocess.check_output(['qdbus6','org.kde.KWin','/Scripting','org.kde.kwin.Scripting.loadScript',str(script),'domainos-owned-pager-fixture'],text=True,timeout=5).strip()
        subprocess.run(['qdbus6','org.kde.KWin','/Scripting/Script'+script_id,'org.kde.kwin.Script.run'],check=True,timeout=5)
        checks['owned_geometry_positioned_by_private_native_compositor']=True
        environment=dict(os.environ,QT_QPA_PLATFORM='wayland',WAYLAND_DISPLAY='domainos-pager-own-wayland',LD_PRELOAD=os.environ['IRIX_DOMAINOS_PAGER_WINDOW_HOST'])
        assert 'KWIN_WAYLAND_NO_PERMISSION_CHECKS' not in environment
        with (output/'HOST.log').open('w') as log:
            host=subprocess.Popen(['/usr/bin/plasmawindowed','org.irixclassic.domainos.pager.test'],env=environment,stdout=log,stderr=subprocess.STDOUT)
            host.wait(30)
        native=json.loads((output/'HOST.json').read_text()) if (output/'HOST.json').exists() else {}
        checks.update(native.get('checks',{}));checks.setdefault('native_scenario_completed',False)
        checks['real_installed_authorized_plasma_host']=native.get('host_executable')=='/usr/bin/plasmawindowed'
        checks['native_host_exited_cleanly']=host.returncode==0
        errors=[line for line in (output/'HOST.log').read_text().splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)]
        checks['qml_runtime_errors_zero']=not errors
        checks['privilege_protocol_checks_not_disabled']=True
        report.update(native=native,qml_diagnostics=errors)
    except Exception as error:
        report['error']=str(error);checks['native_scenario_completed']=False
    finally:
        for process in [host,compositor]:
            if process and process.poll() is None:
                process.terminate()
                try:process.wait(5)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        checks['all_owned_processes_stopped']=all(not process or process.poll() is not None for process in [host,compositor])
        (output/'NATIVO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return 0 if checks and all(checks.values()) else 1

def worker(output):
    from PyQt6 import sip
    from PyQt6.QtCore import QCoreApplication,QEvent
    from PyQt6.QtCore import QPointF,QUrl,Qt,qInstallMessageHandler
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtQuick import QQuickItem,QQuickWindow
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication,QWidget
    checks={};evidence={};messages=[];windows=[];compositor=None;app=None;engine=None
    qInstallMessageHandler(lambda kind,context,message:messages.append(message))
    def check(name,condition):
        checks[name]=bool(condition)
        if not condition:raise AssertionError(name)
    def settle(predicate,timeout=5):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            app.processEvents()
            if predicate():return True
            time.sleep(.015)
        return False
    def xdo(*args):return subprocess.check_output(['xdotool',*map(str,args)],text=True,timeout=5).strip()
    def current():return subprocess.check_output(['qdbus6','org.kde.KWin','/VirtualDesktopManager','org.freedesktop.DBus.Properties.Get','org.kde.KWin.VirtualDesktopManager','current'],text=True,timeout=5).strip()
    try:
        with (output/'KWIN.log').open('w') as log:compositor=subprocess.Popen(['kwin_x11','--replace'],stdout=log,stderr=subprocess.STDOUT)
        for _ in range(80):
            ready=subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=2)
            if ready.returncode==0:break
            time.sleep(.05)
        check('private_kwin_ready',ready.returncode==0)
        app=QApplication([]);app.setApplicationName('domainos-pager-owned-activation')
        engine=QQmlApplicationEngine();engine.load(QUrl.fromLocalFile(str(ROOT/'plasma/tests/DomainOSPagerPreview.qml')))
        check('production_qml_loaded',bool(engine.rootObjects()))
        host=engine.rootObjects()[0];pager=host.findChild(QQuickItem,'domainosRealPager')
        engine.globalObject().setProperty('pagerTest',engine.newQObject(pager))
        def evaluate(code):
            result=engine.evaluate(code)
            if result.isError():raise RuntimeError(result.toString())
            return result
        def invoke(code):return evaluate('pagerTest.'+code).toBool()
        def items():
            def descend(item):
                yield item
                for child in item.childItems():yield from descend(child)
            return [item for win in app.allWindows() if isinstance(win,QQuickWindow) for item in descend(win.contentItem())]
        def geometry(title,desktop=None):return next((item for item in items() if item.objectName().startswith('domainosNativeWindow_') and not item.objectName().endswith('Pointer') and item.property('windowTitle')==title and (desktop is None or item.objectName().startswith('domainosNativeWindow_'+desktop+'_'))),None)
        def point(item):return item.mapToItem(host.contentItem(),QPointF(item.width()/2,item.height()/2)).toPoint()
        def click(item):QTest.mouseClick(host,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(item));app.processEvents()
        def active(window):return int(xdo('getactivewindow'))==int(window.winId())
        def operation_count():return len(host.property('completedOperations').toVariant())
        def identity(item):
            engine.globalObject().setProperty('rectangleTest',engine.newQObject(item))
            return json.loads(evaluate('JSON.stringify(rectangleTest.captureIdentity())').toString())
        check('two_desktops_available',settle(lambda:pager.property('available') and pager.property('desktopCount')==2))
        desktops=json.loads(evaluate('JSON.stringify(pagerTest.desktopRecords)').toString());first,second=[row['id'] for row in desktops]
        for index in range(2):
            source=QWidget();source.setWindowTitle('DOMAINOS-GEOMETRY-OWN-'+str(index));source.setGeometry(90+index*540,120+index*100,320,240);source.show();windows.append(source)
        a,b=windows
        check('two_real_geometries_available',settle(lambda:geometry(a.windowTitle(),first) is not None and geometry(b.windowTitle(),first) is not None))
        xdo('windowactivate','--sync',int(a.winId()))
        check('own_first_window_focused',active(a))
        before=operation_count();click(geometry(b.windowTitle(),first))
        check('geometric_click_activates_inactive_window',settle(lambda:active(b)))
        check('window_click_dispatches_once_not_desktop_click',operation_count()==before+1 and host.property('completedOperations').toVariant()[-1]['operation']=='activate-pager-window')
        check('same_desktop_window_activation_preserves_desktop',current()==first)
        b.showMinimized();check('own_minimized_state_native',settle(lambda:geometry(b.windowTitle(),first).property('minimized')))
        xdo('windowactivate','--sync',int(a.winId()));click(geometry(b.windowTitle(),first))
        check('outline_click_restores_and_focuses_window',settle(lambda:active(b) and not geometry(b.windowTitle(),first).property('minimized')))
        check('geometric_click_does_not_maximize_window',not b.isMaximized())
        check('own_window_geometry_capture',host.grabWindow().save(str(output/'GEOMETRIC-ACTIVATION.png')))
        xdo('set_desktop_for_window',int(b.winId()),1)
        check('real_second_desktop_geometry',settle(lambda:geometry(b.windowTitle(),second) is not None and geometry(b.windowTitle(),first) is None))
        b_identity=identity(geometry(b.windowTitle(),second))
        bad_pid=dict(b_identity,pid=b_identity['pid']+1)
        before=operation_count()
        check('wrong_pid_cannot_target_reused_window',not invoke('activateWindow('+json.dumps(second)+','+json.dumps(bad_pid)+')'))
        check('wrong_desktop_cannot_activate_window',not invoke('activateWindow('+json.dumps(first)+','+json.dumps(b_identity)+')'))
        check('rejections_send_no_native_operation',operation_count()==before and current()==first and not active(b))
        click(geometry(b.windowTitle(),second))
        check('other_desktop_window_click_switches_and_focuses',settle(lambda:current()==second and pager.property('currentDesktopId')==second and active(b)))
        invoke('activateDesktop('+json.dumps(first)+')')
        check('return_to_first_desktop',settle(lambda:current()==first and pager.property('currentDesktopId')==first and not pager.property('pendingActivations')))
        second_tile=next(item for item in items() if item.objectName()=='domainosDesktopTile_1')
        header=second_tile.mapToItem(host.contentItem(),QPointF(second_tile.width()/2,12)).toPoint()
        before=operation_count();QTest.mouseClick(host,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,header)
        check('card_header_still_activates_desktop',settle(lambda:current()==second and pager.property('currentDesktopId')==second and not pager.property('pendingActivations')))
        check('header_is_not_window_activation',operation_count()==before+1 and host.property('completedOperations').toVariant()[-1]['operation']=='activate-desktop')
        invoke('activateDesktop('+json.dumps(first)+')');check('return_for_cancel_keyboard',settle(lambda:current()==first and pager.property('currentDesktopId')==first and not pager.property('pendingActivations')))
        a_rect=geometry(a.windowTitle(),first);a_identity=identity(a_rect)
        before=operation_count();QTest.mousePress(host,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(a_rect));app.processEvents()
        check('press_captures_native_window_identity',a_rect.property('pressedIdentity').toVariant()==a_identity)
        check('geometric_press_does_not_dispatch_early',operation_count()==before)
        QTest.mouseMove(host,host.contentItem().mapToItem(host.contentItem(),QPointF(host.width()-2,host.height()-2)).toPoint())
        QTest.mouseRelease(host,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,QPointF(host.width()-2,host.height()-2).toPoint());app.processEvents()
        check('cancelled_geometric_press_is_no_operation',operation_count()==before and a_rect.property('pressedIdentity') is None)
        xdo('set_desktop_for_window',int(b.winId()),0);check('second_window_returns_first',settle(lambda:geometry(b.windowTitle(),first) is not None))
        xdo('windowactivate','--sync',int(host.winId()))
        check('owned_host_receives_native_keyboard_focus',settle(host.isActive))
        a_rect=geometry(a.windowTitle(),first);a_rect.forceActiveFocus()
        check('geometric_window_has_keyboard_focus',settle(a_rect.hasActiveFocus))
        before=operation_count()
        QTest.keyPress(host,Qt.Key.Key_Return);app.processEvents()
        evidence['keyboard_after_press']={'pressed_key':a_rect.property('pressedKey'),'focused':a_rect.hasActiveFocus(),'operations':operation_count()}
        check('keyboard_press_captures_window_identity',a_rect.property('pressedKey')==int(Qt.Key.Key_Return))
        check('keyboard_press_does_not_activate_early',operation_count()==before)
        QTest.keyRelease(host,Qt.Key.Key_Return)
        check('keyboard_release_activates_native_window',settle(lambda:active(a)) and operation_count()==before+1)
        b.close();check('closed_window_geometry_removed',settle(lambda:geometry(b.windowTitle()) is None))
        before=operation_count();check('closed_native_identity_cannot_activate_replacement',not invoke('activateWindow('+json.dumps(first)+','+json.dumps(b_identity)+')') and operation_count()==before)
        check('pager_dimensions_preserved',pager.width()==342 and pager.height()==150)
        for _ in range(30):invoke('readState()')
        check('native_dbus_replies_pending_before_removal',evaluate('pagerTest.pendingReplies.length').toInt()>0)
        pager.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        check('pager_removed_with_native_dbus_requests_in_flight',sip.isdeleted(pager))
        end=time.monotonic()+.4
        while time.monotonic()<end:app.processEvents();time.sleep(.01)
        check('destroyed_pager_replies_do_not_invoke_deleted_qml',not any('unbox' in message or 'object [null]' in message for message in messages))
        errors=[m for m in messages if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',m)]
        evidence.update(desktops=desktops,owned_window_ids=[int(w.winId()) for w in windows],completed_operations=host.property('completedOperations').toVariant(),qml_errors=errors)
        check('qml_runtime_errors_zero',not errors)
        checks['native_scenario_completed']=True
    except Exception as error:
        evidence['error']=str(error);checks['native_scenario_completed']=False
    finally:
        if engine:
            for window in engine.rootObjects():window.close()
        for window in windows:window.close()
        if compositor:
            compositor.terminate()
            try:compositor.wait(5)
            except subprocess.TimeoutExpired:compositor.kill();compositor.wait()
        evidence['qt_messages']=messages
        (output/'NATIVO.json').write_text(json.dumps({'checks':checks,'evidence':evidence},indent=2,ensure_ascii=False)+'\n')
    return 0 if checks and all(checks.values()) else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--saida',required=True,type=Path);parser.add_argument('--backend',choices=['x11','wayland'],default='x11');parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.worker:return worker_wayland(args.saida.absolute()) if args.backend=='wayland' else worker(args.saida.absolute())
    return setup(args.saida.absolute(),args.backend)

if __name__=='__main__':raise SystemExit(main())
