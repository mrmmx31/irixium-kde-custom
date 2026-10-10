#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Drive the live Iconbox and KDE's installed context menu in private Plasma."""
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

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]

def finalize_report(output,returncode,before,after):
    """Require the native worker's scenario, independently of profile safety."""
    receipt=output/"NATIVO.json"
    report=json.loads(receipt.read_text()) if receipt.is_file() else {
        "status":"failed","checks":{},"error":(output/"runner.log").read_text()}
    checks=report["checks"]
    checks["native_worker_report_available"]=receipt.is_file() and report.get("state",{}).get("checks",{}).get("native_scenario_completed") is True
    checks["native_runner_exited_zero"]=returncode==0
    checks["real_profiles_unchanged"]=before==after
    report["protected_config_sha256"]=before
    report["status"]="passed" if checks and all(checks.values()) else "failed"
    return report

def worker(output):
    logs=[];processes=[]
    try:
        log=(output/"kwin.log").open("w");logs.append(log)
        processes.append(subprocess.Popen(["kwin_x11"],stdout=log,stderr=subprocess.STDOUT))
        for _ in range(100):
            probe=subprocess.run(["qdbus6","org.kde.KWin","/VirtualDesktopManager"],capture_output=True,timeout=2)
            if probe.returncode==0:break
            time.sleep(.05)
        environment=dict(os.environ,LD_PRELOAD=str(output/"iconbox-host.so"),
            IRIX_DOMAINOS_ICONBOX_CAPTURE=str(output/"ICONBOX-NATIVE.png"),
            IRIX_DOMAINOS_ICONBOX_MENU_CAPTURE=str(output/"ICONBOX-NATIVE-MENU.png"),
            IRIX_DOMAINOS_ICONBOX_REPORT=str(output/"state.json"))
        result=subprocess.run(["plasmawindowed","org.irixclassic.domainos.iconbox.test"],env=environment,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25)
        (output/"host.log").write_text(result.stdout)
        state=json.loads((output/"state.json").read_text()) if (output/"state.json").is_file() else {}
        errors=[line for line in result.stdout.splitlines() if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed",line)]
        checks=state.get("checks",{})
        checks.update(native_host_exited=result.returncode==0,native_frame_capture_saved=state.get("capture_saved") is True,qml_runtime_errors_zero=not errors)
        report={"status":"passed" if checks and all(checks.values()) else "failed","checks":checks,"state":state,"qml_errors":errors,
            "scope":"Actual Qt mouse input, owned QWidget targets, installed KDE native menu in a private Plasma/Xvfb/KWin"}
        (output/"NATIVO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        return 0 if report["status"]=="passed" else 1
    finally:
        for process in reversed(processes):
            process.terminate()
            try:process.wait(5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        for log in logs:log.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",type=Path,required=True);parser.add_argument("--worker",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output.exists():parser.error("Use a new output under /tmp")
    output.mkdir(mode=0o700)
    env=os.environ.copy();config=Path(env.get("XDG_CONFIG_HOME",str(Path.home()/".config")))
    def hashes():
        return {str(config/name):hashlib.sha256((config/name).read_bytes()).hexdigest() if (config/name).is_file() else None
            for name in ("kdeglobals","kwinrc","plasmarc","plasma-org.kde.plasma.desktop-appletsrc")}
    before=hashes()
    for key in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","LD_PRELOAD","QML_IMPORT_PATH","QML2_IMPORT_PATH","XAUTHORITY","SESSION_MANAGER","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE","KDE_FULL_SESSION","KDE_SESSION_VERSION","XDG_SESSION_ID","PULSE_SERVER","PULSE_COOKIE"):
        env.pop(key,None)
    for key,name in (("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),("XDG_CACHE_HOME","cache"),("XDG_STATE_HOME","state"),("XDG_RUNTIME_DIR","runtime")):
        path=output/name;path.mkdir(mode=0o700);env[key]=str(path)
    plasmoids=output/"data/plasma/plasmoids";plasmoids.mkdir(parents=True)
    shutil.copytree(REPO/"plasma/applets/org.irixclassic.domainos.panel",plasmoids/"org.irixclassic.domainos.panel",ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    for name in ("IrixClassic","IrixClassicDomainOS"):
        shutil.copytree(REPO/"plasma"/name,output/"data/plasma/desktoptheme"/name)
    fixture=plasmoids/"org.irixclassic.domainos.iconbox.test";(fixture/"contents/ui").mkdir(parents=True)
    (fixture/"metadata.json").write_text(json.dumps({"KPlugin":{"Id":"org.irixclassic.domainos.iconbox.test","Name":"Native Iconbox test","Version":"1.0","License":"GPL-3.0-or-later"},"KPackageStructure":"Plasma/Applet","X-Plasma-API-Minimum-Version":"6.0"}))
    (fixture/"contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        objectName:"domainosIconboxNativeCandidate"
        property var requests:[]
        Layout.minimumWidth:594;Layout.minimumHeight:150
        Layout.preferredWidth:594;Layout.preferredHeight:150
        function coordinates(title) {
            const record=tasks.windowRows.find(window=>window.title===title)
            if (!record)return "{}"
            const button=box.buttonForKey(record.key)
            if (!button)return "{}"
            const point=button.mapToItem(null,button.width/2,button.height/2)
            return JSON.stringify({key:record.key,pid:record.pid,x:point.x,y:point.y})
        }
        function nativeUiState() { return JSON.stringify({rows:tasks.taskRows,selected:tasks.selectedKeys,
            activeTitles:tasks.windowRows.filter(window=>window.active).map(window=>window.title),
            nativeMenuAvailable:!!box.nativeMenuBridge,errors:box.lastError,requests:requests,
            nativeMenuItems:box.nativeMenuBridge ? box.nativeMenuBridge.menuItems.map(item=>({name:item.objectName,text:item.text,enabled:item.enabled})) : []}) }
        Panel.DomainOSPalette { id:colors;followSystem:false }
        Panel.DomainOSTasks { id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;groupingMode:0;
            onOperationRequested:request=>parent.requests=parent.requests.concat([request]) }
        Panel.DomainOSIconbox { id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host }
    }
}
''')
    (output/"config/kwinrc").write_text("[Compositing]\nEnabled=false\n[Desktops]\nNumber=1\nName_1=Private Iconbox test\n")
    env.update(QT_QPA_PLATFORM="xcb",QT_QPA_PLATFORMTHEME="generic",QT_QUICK_BACKEND="software",KWIN_COMPOSE="N",XDG_SESSION_TYPE="x11",XDG_CURRENT_DESKTOP="NONE",QT_ACCESSIBILITY="0",LIBGL_ALWAYS_SOFTWARE="1",LANG="C.UTF-8",LC_ALL="C.UTF-8",GIO_USE_VFS="local",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output/"no-system-bus"),PULSE_SERVER="unix:"+str(output/"runtime/no-pulse"))
    flags=subprocess.check_output(["pkg-config","--cflags","--libs","Qt6Widgets"],text=True)
    subprocess.run(["g++","-shared","-fPIC","-std=c++17",str(REPO/"plasma/tests/domainos-iconbox-host.cpp"),"-o",str(output/"iconbox-host.so"),*shlex.split(flags),"-ldl"],check=True)
    bus_config=output/"bus.conf"
    bus_config.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')
        +'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/>'
        +'<allow receive_sender="*"/><allow own="*"/></policy></busconfig>\n')
    command=["xvfb-run","-a","-s","-screen 0 1200x700x24 -nolisten tcp","dbus-run-session","--config-file",str(bus_config),"--",sys.executable,str(Path(__file__).resolve()),"--worker","--saida",str(output)]
    with (output/"runner.log").open('w') as runner_log:
        result=subprocess.run(command,env=env,stdout=runner_log,stderr=subprocess.STDOUT,text=True,timeout=40)
    report=finalize_report(output,result.returncode,before,hashes())
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(report["checks"]),"report":str(output/"RESULTADO.json")}))
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":sys.exit(main())
