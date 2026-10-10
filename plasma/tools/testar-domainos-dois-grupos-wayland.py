#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Own Wayland windows: accumulate checkbox members across two real groups.

Builds, HOME/XDG, captures and caches stay in a temporary repository directory.
Only RESULTADO.json and a compressed artifact remain in the requested /tmp folder.
"""
import argparse
import hashlib
import json
import math
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

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO / "plasma/applets/org.irixclassic.domainos.panel"
IDENTIFIER = "org.irixclassic.domainos.crossgroups.wayland.test"
OWN_APP = "org.irixclassic.domainos.crossgroup.qa"
SOURCE_FILES = [APPLET / "contents/ui" / name for name in (
    "DomainOSTasks.qml", "DomainOSIconbox.qml", "DomainOSWindowOperations.qml", "DomainOSActivity.qml",
    "DomainOSTaskButton.qml", "DomainOSTaskSelection.js", "PanelButton.qml", "Bevel.qml",
    "DomainOSNativeTaskMenu.qml", "DomainOSPopupPlacement.qml", "DomainOSPopupToggle.qml")]
SOURCE_FILES += [APPLET / "contents/code" / name for name in ("window_ops.py", "window_ops.js")]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_CROSS_PRIVATE") != "1":
        raise RuntimeError("Private session required")
    checks = {}; report = {"checks": checks, "backend": "wayland"}
    processes = []; script_name = None; traces = {}

    def start(label, command, environment, log):
        code = ('import json,os,sys;from pathlib import Path;'
            'fields=("HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_RUNTIME_DIR","DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_SYSTEM_BUS_ADDRESS","PULSE_SERVER");'
            'Path(sys.argv[1]).write_text(json.dumps({"pid":os.getpid(),"namespace":{key:os.environ[key] for key in fields if key in os.environ},"observation":"before exec; same PID and inherited environment"}));'
            'os.execvpe(sys.argv[2],sys.argv[2:],os.environ)')
        process = subprocess.Popen([sys.executable, "-c", code, str(output / (label + "-namespace.json")), *command], env=environment, stdout=log, stderr=subprocess.STDOUT)
        processes.append(process); return process

    with (output / "SESSION.log").open("w") as log:
        try:
            server = start("compositor", ["kwin_wayland", "--virtual", "--width", "1200", "--height", "900",
                "--socket", "domainos-crossgroups", "--no-lockscreen", "--no-global-shortcuts", "--no-kactivities"],
                dict(os.environ, QT_QPA_PLATFORM="offscreen", KWIN_COMPOSE="Q"), log)
            for _ in range(100):
                probe = subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"], capture_output=True, timeout=2)
                if probe.returncode == 0: break
                if server.poll() is not None: raise RuntimeError("Private KWin exited before ready")
                time.sleep(.05)
            else: raise RuntimeError("Private KWin did not become ready")
            checks["private_wayland_compositor_ready"] = True
            environment = dict(os.environ, QT_QPA_PLATFORM="wayland", WAYLAND_DISPLAY="domainos-crossgroups")
            clients = [start("client" + str(index), [str(output / "owned-client"), "B" + str(index),
                str(output / ("client" + str(index) + "-state.json"))], environment, log) for index in range(2)]
            with (output / "host.log").open("w") as host_log:
                host = start("host", ["/usr/bin/plasmawindowed", IDENTIFIER], dict(environment,
                    LD_PRELOAD=str(output / "cross-groups-host.so"), IRIX_DOMAINOS_CROSS_DIR=str(output),
                    IRIX_DOMAINOS_CROSS_REPORT=str(output / "HOST.json"),
                    IRIX_DOMAINOS_CROSS_B0_PID=str(clients[0].pid), IRIX_DOMAINOS_CROSS_B1_PID=str(clients[1].pid)), host_log)
                # Exclude only the fixture's own panel; all five native clients
                # stay visible in the genuine, unmodified TasksModel.
                script = output / "own-host-skip-taskbar.js"
                script.write_text('const pid=' + str(host.pid) + ';\nfunction hide(window){if(window.pid===pid && window.caption==="DomainOS cross-group Wayland private test"){window.skipTaskbar=true;window.skipSwitcher=true;}}\nworkspace.windowList().forEach(hide);workspace.windowAdded.connect(hide);\n')
                script_name = "domainos-crossgroup-own-host-" + str(host.pid)
                loaded = subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript", str(script), script_name], capture_output=True, text=True, timeout=5)
                if loaded.returncode or not loaded.stdout.strip().isdecimal(): raise RuntimeError("Own placement script did not load: " + loaded.stderr)
                started = subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting/Script" + loaded.stdout.strip(), "org.kde.kwin.Script.run"], capture_output=True, timeout=5)
                if started.returncode: raise RuntimeError("Own placement script did not run")
                for label in ("compositor", "host", "client0", "client1"):
                    path = output / (label + "-namespace.json")
                    for _ in range(100):
                        if path.is_file(): break
                        time.sleep(.01)
                    traces[label] = json.loads(path.read_text())
                checks["all_four_processes_inherit_only_private_home_xdg_bus"] = all(
                    trace["namespace"].get(key) == os.environ[key]
                    for trace in traces.values() for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"))
                checks["private_wayland_processes_have_no_real_x11_display"] = all("DISPLAY" not in trace["namespace"] for trace in traces.values())
                host.wait(52 if os.environ.get("IRIX_DOMAINOS_POPUP_REGRESSION") == "1" else 42)
            native = json.loads((output / "HOST.json").read_text()) if (output / "HOST.json").is_file() else {}
            checks.update(native.get("checks", {}))
            checks["native_host_exited_cleanly"] = host.returncode == 0
            checks["legitimate_installed_host_identity"] = native.get("host_executable") == "/usr/bin/plasmawindowed"
            checks["host_self_reports_same_private_namespace_after_exec"] = native.get("host_namespace_after_exec") == traces["host"]["namespace"]
            checks["both_other_owned_processes_still_alive_after_batches"] = all(client.poll() is None for client in clients)
            client_state = [json.loads((output / ("client" + str(index) + "-state.json")).read_text()) for index in range(2)]
            if os.environ.get("IRIX_DOMAINOS_TEMPORARY_PINS") == "1":
                checks["pin_operations_keep_both_external_owned_window_sizes"] = all(
                    state["pid"] == client.pid and (state["width"], state["height"]) == (260, 160)
                    for state, client in zip(client_state, clients))
            else:
                checks["selected_second_process_receives_real_wayland_resize"] = client_state[0]["pid"] == clients[0].pid and client_state[0]["width"] > 260 and client_state[0]["height"] > 160
            checks["unselected_second_process_keeps_actual_widget_size"] = client_state[1]["pid"] == clients[1].pid and (client_state[1]["width"], client_state[1]["height"]) == (260, 160)
            diagnostics = [line for line in (output / "host.log").read_text().splitlines() if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Unexpected token|error when loading applet|Error loading QML|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed", line)]
            checks["qml_runtime_errors_zero"] = not diagnostics
            protocol_errors = [line for line in ((output / "SESSION.log").read_text() + "\n" + (output / "host.log").read_text()).splitlines()
                if re.search(r"xdg_surface is already mapped|fatal.*protocol|error .*xdg_popup|Wayland display.*error", line, re.I)]
            checks["no_wayland_popup_protocol_errors"] = not protocol_errors
            report["wayland_protocol_errors"] = protocol_errors
            checks["native_window_protocol_authorized_without_override"] = 'authorized "/usr/bin/plasmawindowed" "org_kde_plasma_window_management"' in (output / "SESSION.log").read_text()
            report.update(native=native, clients=client_state, process_namespace_trace=traces, qml_diagnostics=diagnostics)
        except Exception as error:
            report["error"] = str(error); checks["native_scenario_completed"] = False
        finally:
            if script_name and processes and processes[0].poll() is None:
                try: subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", script_name], capture_output=True, timeout=5)
                except (OSError, subprocess.TimeoutExpired) as error: report["fixture_unload_error"] = str(error)
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try: process.wait(5)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()
            checks["all_owned_processes_exited_after_test"] = all(process.poll() is not None for process in processes)
    report["status"] = "passed" if checks and all(checks.values()) else "failed"
    (output / "NATIVO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--popup-regression", action="store_true", help="Also exercise native popup sizing, checkbox intention and provider failure")
    parser.add_argument("--native-style", choices=("default", "kvantum"), default="default", help="Use a private IrixClassic Kvantum copy for the native menu")
    parser.add_argument("--native-scale", type=float, default=1.0, help="Scale the private Iconbox item independently of the native menu")
    parser.add_argument("--temporary-pins", action="store_true", help="Exercise accumulated group/individual selection and ephemeral native-window pins")
    args = parser.parse_args(); destination = args.saida.resolve()
    if args.worker: return worker(destination)
    if not math.isfinite(args.native_scale) or not 0.1 <= args.native_scale <= 2:
        parser.error("Use a finite native scale between 0.1 and 2")
    if not destination.is_relative_to(Path("/tmp")) or destination == Path("/tmp") or destination.exists(): parser.error("Use a fresh directory under /tmp")
    destination.mkdir(mode=0o700)
    protected = [Path.home() / ".config" / name for name in ("kdeglobals", "kwinrc", "plasmarc", "plasma-org.kde.plasma.desktop-appletsrc")]
    before = {str(path): digest(path) for path in protected}
    source_before = {str(path.relative_to(REPO)): digest(path) for path in SOURCE_FILES}
    installed = [Path("/usr/bin/plasmawindowed"), Path("/usr/share/applications/org.kde.plasmawindowed.desktop")]
    installed_before = {str(path): digest(path) for path in installed}
    native_host_source = REPO / "plasma/tests" / ("domainos-temporary-window-pins-host.cpp" if args.temporary_pins else "domainos-cross-groups-wayland-host.cpp")
    test_source_before = {str(path.relative_to(REPO)): digest(path) for path in (Path(__file__), native_host_source)}
    with tempfile.TemporaryDirectory(prefix=".g2-qa-", dir=REPO) as private:
        output = Path(private)
        environment = os.environ.copy()
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "WAYLAND_SOCKET", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "LD_PRELOAD", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "XAUTHORITY", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XDG_SESSION_ID", "PULSE_SERVER", "PULSE_COOKIE", "KWIN_WAYLAND_NO_PERMISSION_CHECKS"):
            environment.pop(key, None)
        for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime"), ("TMPDIR", "tmp")):
            (output / name).mkdir(mode=0o700); environment[key] = str(output / name)
        plasmoids = output / "data/plasma/plasmoids"
        shutil.copytree(APPLET, plasmoids / "org.irixclassic.domainos.panel", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in ("IrixClassic", "IrixClassicDomainOS"): shutil.copytree(REPO / "plasma" / name, output / "data/plasma/desktoptheme" / name)
        fixture = plasmoids / IDENTIFIER; (fixture / "contents/ui").mkdir(parents=True)
        (fixture / "metadata.json").write_text(json.dumps({"KPlugin": {"Id": IDENTIFIER, "Name": "DomainOS cross-group Wayland private test", "Version": "1.0", "License": "GPL-3.0-or-later"}, "KPackageStructure": "Plasma/Applet", "X-Plasma-API-Minimum-Version": "6.0"}))
        (fixture / "contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
 id:host;preferredRepresentation:fullRepresentation
 fullRepresentation:Item {
  id:fixture;objectName:"domainosCrossGroupsFixture"
  Layout.minimumWidth:594;Layout.minimumHeight:150;Layout.preferredWidth:594;Layout.preferredHeight:150
  property var reports:[];property var requests:[]
  function state() {
   return JSON.stringify({windows:tasks.windowRows,rows:tasks.taskRows,count:tasks.windowCount,
    groups:tasks.taskRows.filter(row=>row.group).map(row=>({key:row.key,members:row.members,selection:tasks.selectionState(row.key)})),
    selected:tasks.selectedKeys,groupPopup:box.groupPopupVisible,operationsPopup:box.operationsMenuVisible,
    reports:reports,requests:requests,effective:tasks.effectiveMinimizedOnly,threshold:tasks.automaticThreshold,
    backendAvailable:operations.available,pending:activity.pendingCount,desktop:tasks.currentDesktopId,
    memberKeys:tasks.memberSelectionKeys,memberActive:tasks.memberSelectionActive,pickerCount:tasks.pickerSelectionCount,
    nativeMenuOpen:!!box.nativeMenuBridge && !!box.nativeMenuBridge.openedMenu,
    error:box.lastError,basicPopup:box.basicContextMenu.visible,
    pins:tasks.temporaryWindowPins,menuSelection:box.menuSelection.map(row=>row.key)})
  }
  function ordinarySelection(key) {tasks.storeSelection([key]);return tasks.requestAction(key,"minimize",undefined,tasks.windowFor(key).pid)}
  function clearPreflight() {tasks.clearSelection();requests=[];return true}
  function failMenuProvider() {box.nativeMenuBridge.contextComponent=({status:Component.Ready,createObject:()=>{throw new Error("PRIVATE_PROVIDER_FAILURE")}});return true}
  function threshold(value) {tasks.automaticThreshold=value;tasks.filterMode="automatic";return true}
  function nativeTarget(key) {
   const target=tasks.nativeTaskTarget(tasks.windowFor(key))
   return JSON.stringify(target ? {key:target.record.key,pid:target.record.pid,row:target.row,child:target.child} : null)
  }
  Panel.DomainOSPalette {id:colors;followSystem:false}
  Panel.DomainOSActivity {id:activity}
  Panel.DomainOSWindowOperations {id:operations;activity:activity;onReported:report=>fixture.reports=fixture.reports.concat([report])}
  Panel.DomainOSTasks {
   id:tasks;onlyCurrentDesktop:false;onlyCurrentScreen:false;onlyCurrentActivity:false
   groupingMode:1;onlyGroupWhenFull:false;sortMode:1;geometryBackend:operations
   currentScreenGeometry:Qt.rect(Screen.virtualX,Screen.virtualY,Screen.width,Screen.height)
   currentAvailableGeometry:currentScreenGeometry;currentScreenName:Screen.name
   onOperationRequested:request=>fixture.requests=fixture.requests.concat([request])
  }
  Panel.DomainOSIconbox {id:box;objectName:"domainosCrossIconbox";width:parent.width/NATIVE_SCALE;height:parent.height/NATIVE_SCALE;scale:NATIVE_SCALE;transformOrigin:Item.TopLeft;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:POPUP_NATIVE_MENUS;hintsEnabled:false;thumbnailsEnabled:false}
 }
}
'''.replace("POPUP_NATIVE_MENUS", "true" if args.popup_regression or args.temporary_pins else "false").replace("NATIVE_SCALE", repr(args.native_scale)))
        (output / "config/kwinrc").write_text("[Desktops]\nNumber=1\nName_1=Private cross-group test\n[Compositing]\nEnabled=true\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
        (output / "config/kdeglobals").write_bytes((REPO / "colors/DomainOS-SR10.4.colors").read_bytes())
        if args.native_style == "kvantum":
            theme = output / "config/Kvantum/IrixClassic"
            theme.mkdir(parents=True)
            for name in ("IrixClassic.kvconfig", "IrixClassic.svg"):
                shutil.copy2(REPO / "kvantum/IrixClassic" / name, theme / name)
            (theme.parent / "kvantum.kvconfig").write_text("[General]\ntheme=IrixClassic\n")
            # The installed plasmawindowed propagates QT_STYLE_OVERRIDE to its
            # QML style as well. Select the QWidget style in our host instead;
            # Kvantum supplies QStyle, not a Qt Quick Controls QML module.
            environment.update(QT_QUICK_CONTROLS_STYLE="org.kde.desktop", IRIX_DOMAINOS_EXPECT_STYLE="kvantum")
        client_source = output / "owned-client.cpp"
        client_source.write_text('''#include <QApplication>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QResizeEvent>
#include <QTimer>
#include <QWidget>
class OwnWindow:public QWidget {
 QString output;
 public:OwnWindow(const QString &name,const QString &path):output(path){setWindowTitle("DomainOS CrossGroup "+name);resize(260,160);}
 void record(){if(!isVisible())return;QFile f(output);if(f.open(QIODevice::WriteOnly))f.write(QJsonDocument(QJsonObject{{"pid",int(QCoreApplication::applicationPid())},{"width",width()},{"height",height()},{"title",windowTitle()}}).toJson());}
 protected:void resizeEvent(QResizeEvent *event)override{QWidget::resizeEvent(event);record();}
};
int main(int argc,char **argv){QApplication app(argc,argv);if(argc!=3)return 2;QApplication::setApplicationName("org.irixclassic.domainos.crossgroup.qa");QApplication::setDesktopFileName("org.irixclassic.domainos.crossgroup.qa");OwnWindow window(QString::fromLocal8Bit(argv[1]),QString::fromLocal8Bit(argv[2]));window.show();QTimer::singleShot(0,&window,[&window](){window.record();});QTimer::singleShot(60000,&app,&QCoreApplication::quit);return app.exec();}
''')
        applications = output / "data/applications"; applications.mkdir()
        (applications / (OWN_APP + ".desktop")).write_text("[Desktop Entry]\nType=Application\nName=Own DomainOS cross-group clients\nExec=" + str(output / "owned-client") + "\nIcon=utilities-terminal\nCategories=Utility;\n")
        if args.popup_regression: environment["IRIX_DOMAINOS_POPUP_REGRESSION"] = "1"
        if args.temporary_pins: environment["IRIX_DOMAINOS_TEMPORARY_PINS"] = "1"
        environment.update(QT_QPA_PLATFORM="wayland", QT_QPA_PLATFORMTHEME="generic", QT_QUICK_BACKEND="software", QML_DISABLE_DISK_CACHE="1", LIBGL_ALWAYS_SOFTWARE="1", QT_SCALE_FACTOR="1", QT_ACCESSIBILITY="0", XDG_SESSION_TYPE="wayland", XDG_CURRENT_DESKTOP="NONE", XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", LANG="C.UTF-8", LC_ALL="C.UTF-8", GIO_USE_VFS="local", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(output / "no-system-bus"), PULSE_SERVER="unix:" + str(output / "no-audio"), QT_LOGGING_RULES="kwin_core.debug=true", IRIX_DOMAINOS_CROSS_PRIVATE="1")
        flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Test"], text=True))
        subprocess.run(["c++", "-shared", "-fPIC", "-std=c++17", str(native_host_source), "-o", str(output / "cross-groups-host.so"), *flags, "-ldl"], check=True, env=environment)
        subprocess.run(["c++", "-std=c++17", str(client_source), "-o", str(output / "owned-client"), *flags], check=True, env=environment)
        bus = output / "bus.conf"; bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=' + str(output / "runtime") + '</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        with (output / "runner.log").open("w") as log:
            runner = subprocess.Popen(["dbus-run-session", "--config-file", str(bus), "--", sys.executable, str(Path(__file__).resolve()), "--worker", "--saida", str(output)], env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try: runner.wait(65 if args.popup_regression else 55)
            except subprocess.TimeoutExpired:
                os.killpg(runner.pid, signal.SIGTERM)
                try: runner.wait(5)
                except subprocess.TimeoutExpired: os.killpg(runner.pid, signal.SIGKILL); runner.wait()
        report = json.loads((output / "NATIVO.json").read_text()) if (output / "NATIVO.json").is_file() else {"status": "failed", "checks": {}, "error": (output / "runner.log").read_text()}
        checks = report["checks"]
        checks.update(private_worker_exited_cleanly=runner.returncode == 0,
            real_profiles_unchanged=before == {str(path): digest(path) for path in protected},
            relevant_production_sources_unchanged=all(digest(REPO / name) == value for name, value in source_before.items()),
            test_sources_unchanged=all(digest(REPO / name) == value for name, value in test_source_before.items()),
            installed_authorized_host_unchanged=installed_before == {str(path): digest(path) for path in installed},
            native_privilege_protocol_checks_not_disabled="KWIN_WAYLAND_NO_PERMISSION_CHECKS" not in environment)
        report.update(protected_config_sha256={"before": before, "after": {str(path): digest(path) for path in protected}},
            native_scale=args.native_scale,
            source_sha256=source_before, installed_host_sha256=installed_before,
            test_source_sha256=test_source_before,
            scope=("Production Iconbox/TasksModel/native context menu with five owned Wayland UUID/PID windows. Actual checkbox/Continue across a group and a projected individual, single-checkbox Pin, append ordering, exact native child context and first Unpin, projected regrouping, own-window closure and selection cleanup. Full QPA Enter/Leave precedes cross-surface QTest mouse input; this is native GUI integration, not physical compositor seat input. No application launcher/config persistence or personal profiles/windows/devices are altered." if args.temporary_pins else "Production Iconbox/TasksModel/selection/WindowOperations with two native Wayland groups (three own QWidget windows in plasmawindowed plus two own processes sharing one private AppId). Actual checkbox, Continue, revisit, columns and minimize menu mouse events; exact UUID/PID targets and three excluded members. Threshold 4/5/6 values belong only to this fixture. No personal profiles/windows/devices or existing preview touched."),
            temporary_pins=args.temporary_pins,
            protocol_limit=("Pin metadata is presentation state only, validated against genuine UUID/PID model records. Actual owned closure proves lifetime cleanup; synthetic PID reuse is covered separately by the unit fixture. QPA input includes surface Enter/Leave with absent native mouse grab, and does not simulate a physical compositor seat." if args.temporary_pins else "Wayland xdg_toplevel has no minimized configure event; native TasksModel and helper independently confirm minimization. Client resize events confirm the selected other process receives the new geometry."),
            artifact=str(destination / "PRIVATE-PROOF.tar.gz"))
        report["status"] = "passed" if checks and all(checks.values()) else "failed"
        (destination / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        with tarfile.open(destination / "PRIVATE-PROOF.tar.gz", "w:gz") as archive:
            for path in sorted(output.iterdir()):
                if path.name not in ("runtime", "tmp", "cache"): archive.add(path, arcname=path.name)
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]), "failed": [name for name, value in report["checks"].items() if value is not True], "result": str(destination / "RESULTADO.json")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
