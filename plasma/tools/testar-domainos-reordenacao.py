#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate production Iconbox drag ordering against the real KDE TasksModel.

All inputs go to private Plasma/KWin/Xvfb and three test-owned native windows.
The fixture observes stable WinIds/PIDs, platform threshold, actual model order,
window state, pins, grouped targets and stale identity rejection; no mocks replace
TasksModel or the production Iconbox/TaskButton/controller.
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
import tempfile
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
IDENTIFIER="org.irixclassic.domainos.reorder.test"


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_REORDER_PRIVATE")!="1": raise RuntimeError("Private session required")
    log=(output/"kwin.log").open("w")
    wm=subprocess.Popen(["kwin_x11"],stdout=log,stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            probe=subprocess.run(["qdbus6","org.kde.KWin","/VirtualDesktopManager"],capture_output=True,timeout=2)
            if probe.returncode==0:break
            time.sleep(.05)
        else:raise RuntimeError("Private KWin did not become ready")
        environment=dict(os.environ,LD_PRELOAD=os.environ['IRIX_DOMAINOS_REORDER_LIB'],IRIX_DOMAINOS_REORDER_CAPTURE=str(output/"NATIVE-REORDER.png"),IRIX_DOMAINOS_REORDER_REPORT=str(output/"state.json"))
        result=subprocess.run(["plasmawindowed",IDENTIFIER],env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25)
        (output/"host.log").write_text(result.stdout)
        state=json.loads((output/"state.json").read_text()) if (output/"state.json").is_file() else {}
        errors=[line for line in result.stdout.splitlines() if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed",line)]
        checks=state.get("checks",{})
        checks.update(native_host_exited=result.returncode==0,native_frame_capture_saved=state.get("capture_saved") is True,qml_runtime_errors_zero=not errors)
        report={"status":"passed" if checks and all(checks.values()) else "failed","checks":checks,"native":state,"qml_errors":errors,"scope":"Actual pointer drag using the platform threshold, production Iconbox/controller and genuine KDE TasksModel in private X11 Plasma/KWin; three test-owned QWidget windows only."}
        (output/"NATIVO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        return 0 if report["status"]=="passed" else 1
    finally:
        wm.terminate()
        try:wm.wait(4)
        except subprocess.TimeoutExpired:wm.kill();wm.wait()
        log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",type=Path,required=True)
    parser.add_argument("--worker",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output==Path('/tmp') or output.exists():parser.error("Use a new output directory under /tmp")
    output.mkdir(mode=0o700)
    env=os.environ.copy();config=Path(env.get("XDG_CONFIG_HOME",str(Path.home()/".config")))
    def hashes():
        return {str(config/name):hashlib.sha256((config/name).read_bytes()).hexdigest() if (config/name).is_file() else None for name in ("kdeglobals","kwinrc","plasmarc","plasma-org.kde.plasma.desktop-appletsrc")}
    before=hashes()
    resources=Path(tempfile.mkdtemp(prefix='.qa-domainos-reorder-',dir=REPO))
    for key in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","LD_PRELOAD","QML_IMPORT_PATH","QML2_IMPORT_PATH","XAUTHORITY","SESSION_MANAGER","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE","KDE_FULL_SESSION","KDE_SESSION_VERSION","XDG_SESSION_ID","PULSE_SERVER","PULSE_COOKIE"):
        env.pop(key,None)
    for key,name in (("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),("XDG_CACHE_HOME","cache"),("XDG_STATE_HOME","state"),("XDG_RUNTIME_DIR","runtime")):
        path=resources/name;path.mkdir(mode=0o700);env[key]=str(path)
    plasmoids=resources/"data/plasma/plasmoids";plasmoids.mkdir(parents=True)
    (plasmoids/"org.irixclassic.domainos.panel").symlink_to(REPO/"plasma/applets/org.irixclassic.domainos.panel",target_is_directory=True)
    for name in ("IrixClassic","IrixClassicDomainOS"):
        themes=resources/"data/plasma/desktoptheme";themes.mkdir(parents=True,exist_ok=True)
        (themes/name).symlink_to(REPO/"plasma"/name,target_is_directory=True)
    fixture=plasmoids/IDENTIFIER;(fixture/"contents/ui").mkdir(parents=True)
    (fixture/"metadata.json").write_text(json.dumps({"KPlugin":{"Id":IDENTIFIER,"Name":"DomainOS native reorder test","Version":"1.0","License":"GPL-3.0-or-later"},"KPackageStructure":"Plasma/Applet","X-Plasma-API-Minimum-Version":"6.0"}))
    (fixture/"contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosReorderFixture"
        Layout.minimumWidth:594;Layout.minimumHeight:150
        Layout.preferredWidth:594;Layout.preferredHeight:150
        property var requests:[]
        property var traces:[]
        property var missingRecord:null
        function record(name) { return tasks.windowRows.find(window=>window.title==="DomainOS reorder "+name) }
        function coordinates(name) {
            const target=name==="@group" ? tasks.taskRows.find(row=>row.group) : record(name)
            if (!target)return "{}"
            const button=box.buttonForKey(target.key)
            if (!button)return "{}"
            const p=button.mapToItem(null,button.width/2,button.height/2)
            return JSON.stringify({key:target.key,pid:target.pid,x:p.x,y:p.y,dragDistance:button.dragDistance,dragActive:button.dragActive,reorderEnabled:button.reorderEnabled,activeFocus:button.activeFocus})
        }
        function state() { return JSON.stringify({rows:tasks.taskRows,order:tasks.taskRows.map(row=>row.key),
            windows:tasks.windowRows.filter(row=>row.title.startsWith("DomainOS reorder ")),
            selected:tasks.selectedKeys,sortMode:tasks.tasksModel.sortMode,manualAvailable:tasks.manualOrderAvailable,
            requests:requests,pins:box.pinnedApplications,launchers:tasks.tasksModel.launcherList,
            groupAvailable:tasks.taskRows.some(row=>row.group),groupPopup:box.groupPopupVisible,traces:traces,
            firstVisible:box.firstVisible,attention:tasks.demandsAttention,pickerCount:tasks.pickerSelectionCount,
            nativeMenuReady:!!box.nativeMenuBridge && box.nativeMenuBridge.contextComponent.status===Component.Ready,lastError:box.lastError}) }
        function action(name) {
            if(name==="alpha"){tasks.sortMode=2;return true}
            if(name==="manual"){tasks.sortMode=1;return true}
            if(name==="moveAtoC")return tasks.moveTask(record("A"),record("C"))
            if(name==="stalePid")return tasks.moveTask(Object.assign({},record("A"),{pid:record("A").pid+1}),record("C"))
            if(name==="freezeB"){missingRecord=record("B");return true}
            if(name==="missingSource")return tasks.moveTask(missingRecord,record("A"))
            if(name==="group"){tasks.groupingMode=1;tasks.onlyGroupWhenFull=false;return true}
            const group=tasks.taskRows.find(row=>row.group)
            if(name==="groupMember")return tasks.moveTask(group,record("A"))
            if(name==="staleGroup")return tasks.moveTask(Object.assign({},group,{members:group.members.map((member,index)=>Object.assign({},member,{pid:member.pid+(index===0 ? 1 : 0)}))}),group)
            if(name==="middleClose"){box.middleClickAction=1;return true}
            if(name==="middleMinimize"){box.middleClickAction=3;return true}
            if(name==="focusA"){box.buttonForKey(record("A").key).forceActiveFocus();return true}
            if(name==="closeGroup"){tasks.finishGroupSelection(false);return true}
            if(name==="wheelActivation"){box.iconboxWheelActivates=true;return true}
            if(name==="ungroup"){tasks.groupingMode=0;return true}
            return false
        }
        Panel.DomainOSPalette { id:colors;followSystem:false }
        Panel.DomainOSTasks {
            id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false
            groupingMode:0;sortMode:1
            onOperationRequested:request=>fixture.requests=fixture.requests.concat([request])
            onGroupSelectionRequested:(key,members)=>fixture.traces=fixture.traces.concat([{event:"selectionRequested",key:key,count:members.length}])
            onGroupSelectorKeyChanged:fixture.traces=fixture.traces.concat([{event:"selectorKey",key:groupSelectorKey}])
        }
        Panel.DomainOSIconbox { id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:true;pinnedApplications:["io.github.mrmmx31.irixclassic.files.desktop","org.kde.kate.desktop"];onGroupPopupVisibleChanged:fixture.traces=fixture.traces.concat([{event:"popupVisible",visible:groupPopupVisible}]) }
        Connections {
            target:box.buttonForKey(tasks.taskRows.find(row=>row.group)?.key || "")
            function onPointerPressed(){fixture.traces=fixture.traces.concat([{event:"groupPress"}])}
            function onSelectedByPointer(record,modifiers){fixture.traces=fixture.traces.concat([{event:"groupClick",key:record.key,modifiers:modifiers}])}
            function onActivatedByPointer(record){fixture.traces=fixture.traces.concat([{event:"groupDouble",key:record.key}])}
        }
    }
}
''')
    (resources/"config/kwinrc").write_text("[Compositing]\nEnabled=false\n[Desktops]\nNumber=1\nName_1=Private reorder test\n")
    (resources/'temp').mkdir(mode=0o700)
    env.update(QT_QPA_PLATFORM="xcb",QT_QPA_PLATFORMTHEME="generic",QT_QUICK_BACKEND="software",KWIN_COMPOSE="N",XDG_SESSION_TYPE="x11",XDG_CURRENT_DESKTOP="NONE",QT_ACCESSIBILITY="0",LIBGL_ALWAYS_SOFTWARE="1",LANG="C.UTF-8",LC_ALL="C.UTF-8",GIO_USE_VFS="local",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(resources/"no-system-bus"),PULSE_SERVER="unix:"+str(resources/"no-audio-server"),IRIX_DOMAINOS_REORDER_PRIVATE="1",IRIX_DOMAINOS_REORDER_LIB=str(resources/'reorder-host.so'),QML_DISABLE_DISK_CACHE='1',TMPDIR=str(resources/'temp'))
    flags=shlex.split(subprocess.check_output(["pkg-config","--cflags","--libs","Qt6Widgets","Qt6Test"],text=True))
    subprocess.run(["c++","-shared","-fPIC","-std=c++17",str(REPO/"plasma/tests/domainos-reorder-host.cpp"),"-o",str(resources/"reorder-host.so"),*flags,"-ldl"],check=True)
    bus=resources/"bus.conf";bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(resources/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    try:
        result=subprocess.run(["xvfb-run","-a","-s","-screen 0 1200x700x24 -nolisten tcp","dbus-run-session","--config-file",str(bus),"--",sys.executable,str(Path(__file__).resolve()),"--worker","--saida",str(output)],env=env,capture_output=True,text=True,timeout=40)
    finally:shutil.rmtree(resources)
    (output/"runner.log").write_text(result.stdout+result.stderr)
    report=json.loads((output/"NATIVO.json").read_text()) if (output/"NATIVO.json").is_file() else {"status":"failed","checks":{},"error":result.stdout+result.stderr}
    report["checks"]["real_profiles_unchanged"]=before==hashes()
    report["protected_config_sha256"]={"before":before,"after":hashes()}
    report["status"]="passed" if report["checks"] and all(report["checks"].values()) and result.returncode==0 else "failed"
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(report["checks"]),"report":str(output/"RESULTADO.json")}))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
