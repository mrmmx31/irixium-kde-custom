#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test real native Iconbox audio against a private PulseAudio null sink.

Production QML, native TasksModel, KDE PulseAudio.qml and two real libpulse
streams are exercised by physical X11 pointer clicks. All resources live in
temporary workspace directories; only small evidence files are saved in /tmp.
No installed applet, personal configuration, audio stream or device is changed.
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
IDENTIFIER="org.irixclassic.domainos.audio.test"


def stop(process):
    if process is None:return
    if process.poll() is None:process.terminate()
    try:process.wait(4)
    except subprocess.TimeoutExpired:process.kill();process.wait()


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_AUDIO_PRIVATE")!="1":raise RuntimeError("Private session required")
    resource=Path(os.environ["IRIX_DOMAINOS_AUDIO_RESOURCES"])
    pulse_log=(output/"pulse.log").open("w")
    kwin_log=(output/"kwin.log").open("w")
    pulse=wm=None
    try:
        pulse=subprocess.Popen(["pulseaudio","-n","--daemonize=no","--use-pid-file=no","--exit-idle-time=-1","--disable-shm=yes","--enable-memfd=no","--high-priority=no","--realtime=no","--log-target=stderr","--log-level=warning","--file="+str(resource/"pulse.pa")],stdout=pulse_log,stderr=subprocess.STDOUT)
        for _ in range(100):
            info=subprocess.run(["pactl","--format=json","list","sinks"],capture_output=True,text=True,timeout=2)
            if info.returncode==0:break
            if pulse.poll() is not None:raise RuntimeError("Private PulseAudio exited before readiness")
            time.sleep(.05)
        else:raise RuntimeError("Private PulseAudio did not become ready")
        sinks=json.loads(info.stdout)
        cards=subprocess.run(["pactl","--format=json","list","cards"],capture_output=True,text=True,check=True,timeout=2)
        server={"sinks":sinks,"cards":json.loads(cards.stdout),"socket":os.environ["PULSE_SERVER"]}
        (output/"PRIVATE-SERVER.json").write_text(json.dumps(server,indent=2)+"\n")
        wm=subprocess.Popen(["kwin_x11"],stdout=kwin_log,stderr=subprocess.STDOUT)
        for _ in range(100):
            probe=subprocess.run(["qdbus6","org.kde.KWin","/VirtualDesktopManager"],capture_output=True,timeout=2)
            if probe.returncode==0:break
            time.sleep(.05)
        else:raise RuntimeError("Private KWin did not become ready")
        environment=dict(os.environ,LD_PRELOAD=str(resource/"audio-host.so"),IRIX_DOMAINOS_AUDIO_OUTPUT=str(output))
        result=subprocess.run(["plasmawindowed",IDENTIFIER],env=environment,capture_output=True,text=True,timeout=25)
        (output/"host.log").write_text(result.stdout+result.stderr)
        state=json.loads((output/"state.json").read_text()) if (output/"state.json").is_file() else {}
        errors=[line for line in (result.stdout+result.stderr).splitlines() if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed",line)]
        checks=state.get("checks",{})
        checks.update(private_server_has_only_null_sink=len(sinks)==1 and sinks[0].get("name")=="domainos_private_null",
            private_server_has_no_hardware_cards=not server["cards"],native_host_exited=result.returncode==0,qml_runtime_errors_zero=not errors,
            audio_socket_inside_private_resources=server["socket"]=="unix:"+str(resource/"runtime/pulse/native"))
        report={"status":"passed" if checks and all(checks.values()) else "failed","checks":checks,"native":state,"qml_errors":errors,
            "scope":"Production native Iconbox, actual KDE PulseAudio.qml, two libpulse streams in the owned window's PID, physical xdotool clicks, private PulseAudio with only a null sink; no hardware or personal session."}
        (output/"NATIVO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        return 0 if report["status"]=="passed" else 1
    finally:
        stop(wm);stop(pulse);kwin_log.close();pulse_log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",type=Path,required=True)
    parser.add_argument("--worker",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output==Path('/tmp') or output.exists():parser.error("Use a new output directory under /tmp")
    output.mkdir(mode=0o700)
    env=os.environ.copy();config=Path(env.get("XDG_CONFIG_HOME",str(Path.home()/".config")))
    production=REPO/"plasma/applets/org.irixclassic.domainos.panel/contents/ui"
    protected=[config/name for name in ("kdeglobals","kwinrc","plasmarc","plasma-org.kde.plasma.desktop-appletsrc")]
    protected.extend(production/name for name in ("DomainOSNativeTaskMenu.qml","DomainOSTaskButton.qml","DomainOSIconbox.qml","DomainOSTasks.qml"))
    def hashes():return {str(path):hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None for path in protected}
    before=hashes();resources=Path(tempfile.mkdtemp(prefix='.qa-domainos-audio-',dir=REPO))
    try:
        for key in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","LD_PRELOAD","QML_IMPORT_PATH","QML2_IMPORT_PATH","XAUTHORITY","SESSION_MANAGER","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE","KDE_FULL_SESSION","KDE_SESSION_VERSION","KDE_SESSION_UID","KDEHOME","KDEROOTHOME","XDG_SESSION_ID","PULSE_SERVER","PULSE_COOKIE","PULSE_PROP","PULSE_CLIENTCONFIG","PULSE_CONFIG_PATH","PIPEWIRE_REMOTE","PIPEWIRE_RUNTIME_DIR"):
            env.pop(key,None)
        for key,name in (("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),("XDG_CACHE_HOME","cache"),("XDG_STATE_HOME","state"),("XDG_RUNTIME_DIR","runtime")):
            path=resources/name;path.mkdir(mode=0o700);env[key]=str(path)
        plasmoids=resources/"data/plasma/plasmoids";plasmoids.mkdir(parents=True)
        (plasmoids/"org.irixclassic.domainos.panel").symlink_to(REPO/"plasma/applets/org.irixclassic.domainos.panel",target_is_directory=True)
        for name in ("IrixClassic","IrixClassicDomainOS"):
            themes=resources/"data/plasma/desktoptheme";themes.mkdir(parents=True,exist_ok=True)
            (themes/name).symlink_to(REPO/"plasma"/name,target_is_directory=True)
        fixture=plasmoids/IDENTIFIER;(fixture/"contents/ui").mkdir(parents=True)
        (fixture/"metadata.json").write_text(json.dumps({"KPlugin":{"Id":IDENTIFIER,"Name":"DomainOS native audio test","Version":"1.0","License":"GPL-3.0-or-later"},"KPackageStructure":"Plasma/Applet","X-Plasma-API-Minimum-Version":"6.0"}))
        (fixture/"contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host;preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosAudioFixture"
        Layout.minimumWidth:594;Layout.minimumHeight:150
        Layout.preferredWidth:594;Layout.preferredHeight:150
        property var requests:[]
        function owned() { return tasks.windowRows.find(window=>window.title==="DomainOS owned audio window") }
        function button() { const record=owned();return record ? box.buttonForKey(record.key) : null }
        function state() {
            const task=button(), audio=task ? task.children.find(item=>item.objectName===task.objectName+"Audio") : null
            return JSON.stringify({rows:tasks.taskRows,windows:tasks.windowRows.filter(row=>row.title==="DomainOS owned audio window"),
                streams:task ? task.audioStreams.length : -1,streamStates:task ? task.audioStreams.map(stream=>({pid:stream.pid,muted:stream.muted,corked:stream.corked})) : [],
                playing:task ? task.playingAudio : false,muted:task ? task.muted : false,badgeVisible:audio ? audio.visible : false,
                interactiveMute:task ? task.interactiveMute : false,selected:tasks.selectedKeys,requests:requests,popup:box.groupPopupVisible,
                providerLoaded:!!box.nativeMenuBridge && !!box.nativeMenuBridge.pulseAudio})
        }
        function coordinates() { const task=button();if (!task)return "{}";const p=task.mapToItem(null,50,18);return JSON.stringify({x:p.x,y:p.y}) }
        function action(name) {
            if(name==="disableMute"){box.interactiveMute=false;return true}
            if(name==="enableMute"){box.interactiveMute=true;return true}
            if(name==="closePicker"){tasks.finishGroupSelection(false);return true}
            return false
        }
        Panel.DomainOSPalette { id:colors;followSystem:false }
        Panel.DomainOSTasks {
            id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;groupingMode:0;sortMode:1
            onOperationRequested:request=>fixture.requests=fixture.requests.concat([request])
        }
        Panel.DomainOSIconbox { id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:true;thumbnailsEnabled:false;hintsEnabled:false }
    }
}
''')
        (resources/"config/kwinrc").write_text("[Compositing]\nEnabled=false\n[Desktops]\nNumber=1\nName_1=Private audio test\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
        (resources/"config/pulse").mkdir()
        (resources/"config/pulse/client.conf").write_text("autospawn = no\nenable-shm = no\n")
        cookie=resources/"config/pulse/cookie";cookie.write_bytes(os.urandom(256));cookie.chmod(0o600)
        (resources/"runtime/pulse").mkdir(mode=0o700)
        (resources/"pulse.pa").write_text("load-module module-native-protocol-unix socket="+str(resources/"runtime/pulse/native")+" auth-cookie="+str(cookie)+"\nload-module module-null-sink sink_name=domainos_private_null rate=48000 channels=1\nset-default-sink domainos_private_null\n")
        (resources/'temp').mkdir(mode=0o700)
        env.update(QT_QPA_PLATFORM="xcb",QT_QPA_PLATFORMTHEME="generic",QT_QUICK_BACKEND="software",KWIN_COMPOSE="N",XDG_SESSION_TYPE="x11",XDG_CURRENT_DESKTOP="NONE",XDG_CONFIG_DIRS="/etc/xdg",XDG_DATA_DIRS="/usr/local/share:/usr/share",QT_ACCESSIBILITY="0",LIBGL_ALWAYS_SOFTWARE="1",LANG="C.UTF-8",LC_ALL="C.UTF-8",GIO_USE_VFS="local",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(resources/"no-system-bus"),PULSE_SERVER="unix:"+str(resources/"runtime/pulse/native"),PULSE_COOKIE=str(cookie),PULSE_RUNTIME_PATH=str(resources/"runtime/pulse"),IRIX_DOMAINOS_AUDIO_PRIVATE="1",IRIX_DOMAINOS_AUDIO_RESOURCES=str(resources),QML_DISABLE_DISK_CACHE='1',TMPDIR=str(resources/'temp'))
        flags=shlex.split(subprocess.check_output(["pkg-config","--cflags","--libs","Qt6Widgets","libpulse"],text=True))
        subprocess.run(["c++","-shared","-fPIC","-std=c++17",str(REPO/"plasma/tests/domainos-audio-host.cpp"),"-o",str(resources/"audio-host.so"),*flags,"-ldl"],check=True)
        bus=resources/"bus.conf";bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(resources/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        result=subprocess.run(["xvfb-run","-a","-s","-screen 0 1200x700x24 -nolisten tcp","dbus-run-session","--config-file",str(bus),"--",sys.executable,str(Path(__file__).resolve()),"--worker","--saida",str(output)],env=env,capture_output=True,text=True,timeout=40)
    finally:shutil.rmtree(resources)
    (output/"runner.log").write_text(result.stdout+result.stderr)
    report=json.loads((output/"NATIVO.json").read_text()) if (output/"NATIVO.json").is_file() else {"status":"failed","checks":{},"error":result.stdout+result.stderr}
    report["checks"]["real_profiles_and_production_unchanged"]=before==hashes()
    report["protected_sha256"]={"before":before,"after":hashes()}
    report["status"]="passed" if report["checks"] and all(report["checks"].values()) and result.returncode==0 else "failed"
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(report["checks"]),"report":str(output/"RESULTADO.json")}))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
