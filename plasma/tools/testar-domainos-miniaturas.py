#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prove real optional window thumbnails in private KWin/Plasma sessions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
UI = REPO / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"
PLUGIN = "org.irixclassic.domainos.thumbnails.test"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(args):
    output = args.saida
    assert os.environ.get("IRIX_DOMAINOS_THUMBNAIL_PRIVATE") == "1"
    checks = {}
    processes = []
    report = {"backend": args.backend, "checks": checks}
    with (output / "SESSION.log").open("w") as log:
        try:
            if args.backend == "wayland":
                pipewire = subprocess.Popen(["pipewire"], stdout=log, stderr=subprocess.STDOUT)
                processes.append(pipewire)
                for _ in range(80):
                    if (output / "runtime/pipewire-0").exists(): break
                    if pipewire.poll() is not None: raise RuntimeError("Private PipeWire exited")
                    time.sleep(.05)
                command = ["kwin_wayland", "--virtual", "--width", "1200", "--height", "900", "--socket", "domainos-thumbnails-wayland", "--no-lockscreen", "--no-global-shortcuts", "--no-kactivities"]
                compositor_environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", KWIN_COMPOSE="O2")
            elif os.environ.get("IRIX_DOMAINOS_THUMBNAIL_CURRENT_DISPLAY") != "1":
                command = ["kwin_x11", "--replace"]
                compositor_environment = dict(os.environ, QT_QPA_PLATFORM="xcb", KWIN_COMPOSE="O2")
            if os.environ.get("IRIX_DOMAINOS_THUMBNAIL_CURRENT_DISPLAY") != "1":
                compositor = subprocess.Popen(command, env=compositor_environment, stdout=log, stderr=subprocess.STDOUT)
                processes.append(compositor)
                for _ in range(100):
                    ready = subprocess.run(["qdbus6", "org.kde.KWin", "/Compositor", "org.kde.kwin.Compositing.active"], capture_output=True, text=True, timeout=2)
                    if ready.returncode == 0: break
                    if compositor.poll() is not None: raise RuntimeError("Private KWin exited")
                    time.sleep(.05)
                else: raise RuntimeError("Private KWin did not become ready")
                checks["private_compositor_ready"] = ready.returncode == 0
                checks["private_compositing_active"] = ready.stdout.strip() == "true"
            else:
                checks["existing_compositor_not_replaced_or_reconfigured"] = True
            if args.backend == "x11":
                graphics = subprocess.run(["glxinfo", "-B"], capture_output=True, text=True, timeout=5)
                (output / "OPENGL.txt").write_text(graphics.stdout + graphics.stderr)
            environment = dict(os.environ, QT_QPA_PLATFORM="xcb" if args.backend == "x11" else "wayland", LD_PRELOAD=str(output / "host.so"), IRIX_DOMAINOS_THUMBNAIL_DIR=str(output))
            if args.backend == "wayland": environment["WAYLAND_DISPLAY"] = "domainos-thumbnails-wayland"
            with (output / "HOST.log").open("w") as host_log:
                host = subprocess.Popen(["/usr/bin/plasmawindowed", PLUGIN], env=environment, stdout=host_log, stderr=subprocess.STDOUT)
                processes.append(host)
                host.wait(25)
            native = json.loads((output / "HOST.json").read_text()) if (output / "HOST.json").exists() else {}
            checks.update(native.get("checks", {}))
            checks["real_installed_plasma_host"] = native.get("host_executable") == "/usr/bin/plasmawindowed"
            checks["native_host_exited_cleanly"] = host.returncode == 0
            checks["native_provider_backend_matches_session"] = native.get("state", {}).get("backend") == args.backend
            diagnostics = [line for line in (output / "HOST.log").read_text().splitlines()
                if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed", line)]
            checks["qml_runtime_errors_zero"] = not diagnostics
            report.update(native=native, qml_diagnostics=diagnostics)
        except Exception as error:
            report["error"] = str(error)
            checks["native_scenario_completed"] = False
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try: process.wait(5)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()
            checks["all_owned_processes_stopped"] = all(process.poll() is not None for process in processes)
    report["status"] = "passed" if checks and all(checks.values()) else "failed"
    (output / "NATIVO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--backend", choices=["x11", "wayland"], default="x11")
    parser.add_argument("--xephyr", action="store_true", help="Use private Xephyr/GLAMOR instead of Xvfb for genuine hardware X11 textures")
    parser.add_argument("--hardware", action="store_true", help="Use available GPU in the private compositor/client namespace")
    parser.add_argument("--current-display", action="store_true", help="Only two explicit owned windows on current X11 display; private HOME/XDG/bus, no TasksModel or compositor changes")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.saida = args.saida.absolute()
    if args.worker: return worker(args)
    if args.current_display and args.backend != "x11": parser.error("Owned-ID display probe is X11 only")
    output = args.saida
    if not output.is_relative_to(Path("/tmp")) or output.exists(): parser.error("Use a new directory under /tmp")
    output.mkdir(mode=0o700)
    protected = [Path.home() / ".config" / name for name in ("kdeglobals", "kwinrc", "plasmarc", "plasma-org.kde.plasma.desktop-appletsrc")]
    before = {str(path): digest(path) for path in protected}
    sources = {str(path): digest(path) for path in UI.glob("*") if path.is_file()}
    environment = dict(os.environ)
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "SESSION_MANAGER", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "QT_STYLE_OVERRIDE", "QT_QUICK_BACKEND", "LD_PRELOAD", "XDG_SESSION_ID", "KDE_FULL_SESSION", "KDE_SESSION_VERSION"):
        environment.pop(key, None)
    for variable, dirname in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        path = output / dirname; path.mkdir(mode=0o700); environment[variable] = str(path)
    package = output / "data/plasma/plasmoids" / PLUGIN
    (package / "contents/ui").mkdir(parents=True)
    (package / "metadata.json").write_text(json.dumps({"KPlugin": {"Id": PLUGIN, "Name": "DomainOS native thumbnail private test", "Version": "1", "License": "GPL-3.0-or-later"}, "KPackageStructure": "Plasma/Applet", "X-Plasma-API-Minimum-Version": "6.0"}))
    fixture_qml = '''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "''' + UI.as_uri() + '''" as Production
PlasmoidItem {
    id:host
    preferredRepresentation: fullRepresentation
    fullRepresentation: Item {
        id:fixture; objectName:"domainosNativeThumbnailsFixture"
        Layout.minimumWidth:640; Layout.minimumHeight:300
        property var windows: tasks.windowRows.filter(window=>window.title.indexOf("DomainOS thumbnail owned ")===0)
        function gather(item,result) {
            if (!item) return
            if (item.objectName==="domainosThumbnailNativeProvider") {
                ++result.providerCount
                if (item.item) ++result.loadedProviderCount
                if (item.item && item.item.available) ++result.availableCount
                result.providers.push({active:item.active,visible:item.visible,width:item.width,height:item.height,
                    itemLoaded:!!item.item,winId:item.item ? item.item.winId : null,
                    windowId:item.item ? item.item.windowId : null,
                    itemVisible:item.item ? item.item.visible : false,
                    itemWidth:item.item ? item.item.width : 0,itemHeight:item.item ? item.item.height : 0})
            }
            for (const child of item.children || []) gather(child,result)
        }
        function testState() {
            const result={windowCount:windows.length,backend:preview.backend,enabled:preview.previewsEnabled,
                hintsEnabled:preview.hintsEnabled,hintMainText:preview.mainText,hintSubText:preview.subText,
                tooltipVisible:preview.tooltipVisible,contentLoaded:!!preview.contentsLoader.item,providerCount:0,loadedProviderCount:0,availableCount:0,providers:[],
                windows:windows.map(window=>({id:window.windowIds[0],pid:window.pid,title:window.title}))}
            gather(preview.contentsLoader.item,result)
            return JSON.stringify(result)
        }
        function enablePreview() { preview.previewsEnabled=true;preview.showToolTip();return true }
        function showHints() { preview.hintsEnabled=true;preview.showToolTip();return true }
        function disableHints() { preview.hintsEnabled=false;return true }
        function hidePreview() { preview.hideImmediately();return true }
        function disablePreview() { preview.previewsEnabled=false;return true }
        function provideOwnedWindows(records) { windows=records;return true }
        QtObject {
            id:windowController
            function membersFor(key) { return fixture.windows }
            function windowFor(key) { return fixture.windows.find(window=>window.key===key) || null }
        }
        Production.DomainOSTasks { id:tasks; onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;groupingMode:0 }
        Production.DomainOSPalette { id:colors;followSystem:false }
        Rectangle { x:20;y:20;width:140;height:80;color:"#607f91";Text { anchors.centerIn:parent;text:"PREVIEW";color:"white" } }
        Production.DomainOSWindowThumbnails {
            id:preview;x:20;y:20;width:140;height:80
            controller:windowController;record:({key:"group:owned",title:"Owned windows",group:true});colorPalette:colors
        }
    }
}
'''
    if args.current_display:
        fixture_qml = fixture_qml.replace('property var windows: tasks.windowRows.filter(window=>window.title.indexOf("DomainOS thumbnail owned ")===0)', 'property var windows: []')
        fixture_qml = fixture_qml.replace('        Production.DomainOSTasks { id:tasks; onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;groupingMode:0 }\n', '')
    (package / "contents/ui/main.qml").write_text(fixture_qml)
    (output / "config/kwinrc").write_text("[Desktops]\nNumber=1\n[Compositing]\nEnabled=true\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
    (output / "config/kdeglobals").write_text("[General]\nColorScheme=BreezeLight\n[Icons]\nTheme=breeze\n[KDE]\nwidgetStyle=Breeze\n")
    (output / "config/plasmarc").write_text("[Theme]\nname=default\n")
    environment.update(QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="org.kde.desktop", QSG_RHI_BACKEND="opengl", QT_XCB_GL_INTEGRATION="xcb_glx", QSG_RENDER_LOOP="basic", LIBGL_ALWAYS_SOFTWARE="0" if args.hardware or args.xephyr or args.current_display else "1", QT_SCALE_FACTOR="1", QT_ACCESSIBILITY="0", XDG_SESSION_TYPE=args.backend, XDG_CURRENT_DESKTOP="NONE", XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", LANG="C.UTF-8", LC_ALL="C.UTF-8", GIO_USE_VFS="local", DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output / "no-system-bus"), PULSE_SERVER="unix:"+str(output / "no-audio"), IRIX_DOMAINOS_THUMBNAIL_PRIVATE="1")
    environment["QML_DISABLE_DISK_CACHE"] = "1"
    if args.current_display:
        if not os.environ.get("DISPLAY"): parser.error("Owned-window probe requires a graphical DISPLAY")
        environment.update(DISPLAY=os.environ["DISPLAY"], IRIX_DOMAINOS_THUMBNAIL_CURRENT_DISPLAY="1")
    graphics_fields = ("DISPLAY", "LIBGL_ALWAYS_SOFTWARE", "QT_XCB_GL_INTEGRATION", "QSG_RHI_BACKEND", "QSG_RENDER_LOOP", "MESA_LOADER_DRIVER_OVERRIDE", "GALLIUM_DRIVER", "DRI_PRIME")
    (output / "GRAPHICS-ENV.json").write_text(json.dumps({name:environment.get(name) for name in graphics_fields}, indent=2)+"\n")
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Test"], text=True))
    subprocess.run(["c++", "-shared", "-fPIC", "-std=c++17", str(REPO / "plasma/tests/domainos-thumbnails-host.cpp"), "-o", str(output / "host.so"), *flags, "-ldl"], check=True)
    bus = output / "bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output / "runtime")+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    command = ["dbus-run-session", "--config-file", str(bus), "--", sys.executable, str(Path(__file__).resolve()), "--worker", "--saida", str(output), "--backend", args.backend]
    xephyr = None
    if args.backend == "x11" and args.current_display:
        pass
    elif args.backend == "x11" and args.xephyr:
        if not os.environ.get("DISPLAY"): parser.error("Xephyr requires a parent graphical DISPLAY")
        # -displayfd lets Xorg reserve an unused display atomically. Its host
        # connection is only this own test window; clients receive the private
        # display and private HOME/XDG/bus. No actual desktop is reconfigured.
        read_fd, write_fd = os.pipe()
        server_environment = dict(environment, DISPLAY=os.environ["DISPLAY"])
        with (output / "XEPHYR.log").open("w") as log:
            xephyr = subprocess.Popen(["Xephyr", "-displayfd", str(write_fd), "-screen", "1200x900", "-glamor", "-noreset", "-nolisten", "tcp", "-ac", "-br", "-title", "DomainOS native thumbnails — isolated test"], env=server_environment, stdout=log, stderr=subprocess.STDOUT, pass_fds=(write_fd,))
        os.close(write_fd)
        with os.fdopen(read_fd, "r") as read: display = read.readline().strip()
        if not display.isdecimal(): raise RuntimeError("Private Xephyr did not announce a display")
        environment["DISPLAY"] = ":" + display
    elif args.backend == "x11": command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1200x900x24 +extension Composite +extension DAMAGE +extension GLX", *command]
    with (output / "RUNNER.log").open("w") as log:
        process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try: process.wait(40)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(5)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait()
    if xephyr and xephyr.poll() is None:
        xephyr.terminate()
        try: xephyr.wait(5)
        except subprocess.TimeoutExpired: xephyr.kill(); xephyr.wait()
    report = json.loads((output / "NATIVO.json").read_text()) if (output / "NATIVO.json").exists() else {"checks": {}, "error": (output / "RUNNER.log").read_text()}
    report["checks"].update(private_worker_exited_cleanly=process.returncode==0,
        production_sources_unchanged=sources=={str(path):digest(path) for path in UI.glob("*") if path.is_file()},
        real_user_preferences_unchanged=before=={str(path):digest(path) for path in protected},
        privilege_protocol_checks_not_disabled="KWIN_WAYLAND_NO_PERMISSION_CHECKS" not in environment)
    report["source_sha256"] = sources
    report["scope"] = "Real Plasma thumbnail providers and two owned windows; default disabled, visible capture, source repaint observed, close/disable unload. Real installed plasmawindowed executable, private HOME/XDG/bus and optional PipeWire; no real user preferences changed. " + ("Current X11 display probe uses only explicitly provided own IDs, does not instantiate TasksModel, enumerate other window titles, capture whole screen, or replace/reconfigure compositor." if args.current_display else "Private KWin compositor/session.")
    report["status"] = "passed" if report["checks"] and all(report["checks"].values()) else "failed"
    (output / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(report["checks"]),"failed":[name for name,ok in report["checks"].items() if not ok],"report":str(output / "RESULTADO.json")}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__": raise SystemExit(main())
