#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise KDE TasksModel against owned windows in private X11/Wayland sessions.

Runs under a private dbus-run-session; never uses the current desktop display/bus
or acts on an unowned window. X11 uses Xvfb/Openbox and a Qt model fixture. Wayland
uses the real authorized plasmawindowed executable, KWin virtual outputs and a
test-only driver: KWin intentionally denies this privileged protocol to a plain
Python/Qt client. Neither permission checks nor desktop-file identities are changed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def native_wayland_worker(output):
    """No Qt application here: the model must live in the actual Plasma host."""
    server = None
    log = (output / "SESSION.log").open("w")
    checks = {}
    report = {"status": "failed", "checks": checks, "backend": "wayland",
        "scope": "Production DomainOSTasks in genuine authorized plasmawindowed; three owned QWidget targets"}
    try:
        compositor_env = dict(os.environ, QT_QPA_PLATFORM="offscreen", KWIN_COMPOSE="Q")
        server = subprocess.Popen(["kwin_wayland", "--virtual", "--width", "1200", "--height", "900",
            "--socket", "domainos-native-tasks", "--no-lockscreen", "--no-global-shortcuts", "--no-kactivities"],
            env=compositor_env, stdout=log, stderr=subprocess.STDOUT)
        ready = False
        for _ in range(100):
            probe = subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"], capture_output=True, timeout=2)
            if probe.returncode == 0: ready = True; break
            if server.poll() is not None: break
            time.sleep(.05)
        checks["private_wayland_kwin_ready"] = ready
        if not ready: raise RuntimeError("Private KWin Wayland service unavailable")
        host_env = dict(os.environ, QT_QPA_PLATFORM="wayland", WAYLAND_DISPLAY="domainos-native-tasks",
            LD_PRELOAD=str(output / "tasks-host.so"), IRIX_DOMAINOS_TASK_CAPTURE=str(output / "NATIVE-WAYLAND.png"),
            IRIX_DOMAINOS_TASK_REPORT=str(output / "HOST.json"))
        with (output / "host.log").open("w") as host_log:
            host = subprocess.run(["/usr/bin/plasmawindowed", "org.irixclassic.domainos.tasks.test"],
                env=host_env, stdout=host_log, stderr=subprocess.STDOUT, timeout=25)
        state = json.loads((output / "HOST.json").read_text()) if (output / "HOST.json").is_file() else {}
        checks.update(state.get("checks", {}))
        checks["real_plasma_host_exited_cleanly"] = host.returncode == 0
        errors = [line for line in (output / "host.log").read_text().splitlines() if re.search(
            r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed", line)]
        checks["qml_runtime_errors_zero"] = not errors
        checks["actual_host_identity_observed"] = state.get("host_executable") == "/usr/bin/plasmawindowed"
        checks["kwin_authorized_installed_executable_without_override"] = 'authorized "/usr/bin/plasmawindowed" "org_kde_plasma_window_management"' in (output / "SESSION.log").read_text()
        report.update(state=state, qml_diagnostics=errors)
        report["status"] = "passed" if checks and all(checks.values()) else "failed"
    except Exception as error:
        report["error"] = str(error)
    finally:
        if server:
            server.terminate()
            try: server.wait(5)
            except subprocess.TimeoutExpired: server.kill(); server.wait()
        log.close()
        (output / "NATIVO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report["status"] == "passed" else 1


def native_wayland_host(output):
    output = output.resolve()
    if not output.is_relative_to(Path('/tmp')) or output.exists():
        raise ValueError("Wayland native host requires a new output directory under /tmp")
    for executable in ("kwin_wayland", "qdbus6", "plasmawindowed", "dbus-run-session", "c++", "pkg-config"):
        if not shutil.which(executable): raise RuntimeError("Missing " + executable)
    output.mkdir(mode=0o700)
    env = os.environ.copy()
    real_config = Path(env.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    def protected():
        return {str(real_config / name): digest(real_config / name) for name in
            ("kdeglobals", "kwinrc", "plasmarc", "plasma-org.kde.plasma.desktop-appletsrc")}
    before = protected()
    production = {name: digest(REPO / name) for name in (
        "plasma/applets/org.irixclassic.domainos.panel/contents/ui/DomainOSTasks.qml",
        "plasma/applets/org.irixclassic.domainos.panel/contents/ui/DomainOSTaskSelection.js")}
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE",
        "LD_PRELOAD", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "XAUTHORITY", "SESSION_MANAGER", "QT_STYLE_OVERRIDE",
        "QT_QUICK_CONTROLS_STYLE", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XDG_SESSION_ID", "PULSE_SERVER", "PULSE_COOKIE",
        "KWIN_WAYLAND_NO_PERMISSION_CHECKS", "WAYLAND_SOCKET"):
        env.pop(key, None)
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
        ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        path = output / name; path.mkdir(mode=0o700); env[key] = str(path)
    plasmoids = output / "data/plasma/plasmoids"; plasmoids.mkdir(parents=True)
    shutil.copytree(REPO / "plasma/applets/org.irixclassic.domainos.panel", plasmoids / "org.irixclassic.domainos.panel",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("IrixClassic", "IrixClassicDomainOS"):
        shutil.copytree(REPO / "plasma" / name, output / "data/plasma/desktoptheme" / name)
    fixture = plasmoids / "org.irixclassic.domainos.tasks.test"; (fixture / "contents/ui").mkdir(parents=True)
    (fixture / "metadata.json").write_text(json.dumps({"KPlugin": {"Id": "org.irixclassic.domainos.tasks.test",
        "Name": "Native DomainOS tasks test", "Version": "1.0", "License": "GPL-3.0-or-later"},
        "KPackageStructure": "Plasma/Applet", "X-Plasma-API-Minimum-Version": "6.0"}))
    (fixture / "contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id: host
    preferredRepresentation: fullRepresentation
    fullRepresentation: Item {
        objectName: "domainosTasksNativeHost"
        Layout.minimumWidth: 594; Layout.minimumHeight: 150
        Layout.preferredWidth: 594; Layout.preferredHeight: 150
        function state() { return JSON.stringify({windows:tasks.windowRows,rows:tasks.taskRows,
            selected:tasks.selectedKeys,desktop:tasks.currentDesktopId}) }
        function action(key,action) {
            const target=tasks.resolveWindow(key)
            return JSON.stringify(tasks.requestAction(key,action,undefined,target ? target.record.pid : -1))
        }
        function coordinates(title) {
            const record=tasks.windowRows.find(window=>window.title===title)
            if (!record) return "{}"
            const button=box.buttonForKey(record.key)
            if (!button) return "{}"
            const point=button.mapToItem(null,button.width/2,button.height/2)
            return JSON.stringify({x:point.x,y:point.y})
        }
        Panel.DomainOSPalette { id: colors; followSystem: false }
        Panel.DomainOSTasks { id: tasks; onlyCurrentDesktop:false; onlyCurrentActivity:false;
            onlyCurrentScreen:false; groupingMode:0 }
        Panel.DomainOSIconbox { id: box; anchors.fill:parent; controller:tasks;
            colorPalette:colors; hostItem:host; nativeMenusEnabled:false }
    }
}
''')
    (output / "config/kwinrc").write_text("[Desktops]\nNumber=1\nName_1=Private native tasks\n[Compositing]\nEnabled=true\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
    env.update(QT_QPA_PLATFORM="wayland", QT_QPA_PLATFORMTHEME="generic", QT_QUICK_BACKEND="software", LIBGL_ALWAYS_SOFTWARE="1",
        QT_SCALE_FACTOR="1", QT_ACCESSIBILITY="0", XDG_SESSION_TYPE="wayland", XDG_CURRENT_DESKTOP="NONE",
        XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", LANG="C.UTF-8", LC_ALL="C.UTF-8",
        GIO_USE_VFS="local", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(output / "no-system-bus"),
        PULSE_SERVER="unix:" + str(output / "runtime/no-pulse"), QT_LOGGING_RULES="kwin_core.debug=true")
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets"], text=True))
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(REPO / "plasma/tests/domainos-tasks-host.cpp"),
        "-o", str(output / "tasks-host.so"), *flags, "-ldl"], check=True)
    bus = output / "bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=' + str(output / 'runtime')
        + '</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/>'
        + '<allow receive_sender="*"/><allow own="*"/></policy></busconfig>\n')
    with (output / "runner.log").open("w") as runner:
        result = subprocess.run(["dbus-run-session", "--config-file", str(bus), "--", sys.executable,
            str(Path(__file__).resolve()), "--native-host-worker", "--backend", "wayland", "--saida", str(output)],
            env=env, stdout=runner, stderr=subprocess.STDOUT, timeout=40)
    report = json.loads((output / "NATIVO.json").read_text()) if (output / "NATIVO.json").is_file() else {
        "status": "failed", "checks": {}, "error": (output / "runner.log").read_text()}
    checks = report["checks"]
    checks["private_host_worker_exited_cleanly"] = result.returncode == 0
    checks["real_preferences_unchanged"] = before == protected()
    checks["production_sources_unchanged"] = all(digest(REPO / name) == value for name, value in production.items())
    checks["wayland_permission_checks_not_disabled"] = "KWIN_WAYLAND_NO_PERMISSION_CHECKS" not in env
    checks["no_artificial_application_desktop_entries"] = not (output / "data/applications").exists()
    report.update(protected_config_sha256=before, source_sha256=production, desktop_modified=False,
        installed_host_desktop_entry_sha256=digest(Path('/usr/share/applications/org.kde.plasmawindowed.desktop')),
        installed_host_executable_sha256=digest(Path('/usr/bin/plasmawindowed')))
    report["status"] = "passed" if checks and all(checks.values()) else "failed"
    (output / "RESULTADO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "report": str(output / "RESULTADO.json")}))
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--backend", choices=("x11","wayland"), default="x11")
    parser.add_argument("--private-bus", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--native-host-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.native_host_worker: return native_wayland_worker(args.saida.resolve())
    if args.backend == "wayland": return native_wayland_host(args.saida)
    if not args.private_bus:
        # No service directories: native API checks must not activate a portal,
        # activity daemon or any service with the surrounding user's profile.
        with tempfile.TemporaryDirectory(prefix="irix-domainos-task-bus-") as folder:
            bus_config = Path(folder) / "bus.conf"
            bus_config.write_text('<busconfig><type>session</type><listen>unix:tmpdir=' + folder
                + '</listen><auth>EXTERNAL</auth><policy context="default">'
                + '<allow send_destination="*"/><allow receive_sender="*"/>'
                + '<allow own="*"/></policy></busconfig>\n')
            return subprocess.call(["dbus-run-session", "--config-file", str(bus_config), "--", sys.executable,
                                    str(Path(__file__).resolve()), "--private-bus", "--backend", args.backend, "--saida", str(args.saida)])
    output = args.saida.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    protected = {str(config / name): digest(config / name) for name in
                 ("kdeglobals", "kwinrc", "plasmarc", "plasma-org.kde.plasma.desktop-appletsrc")}
    checks, warnings = {}, []
    report = {"status": "failed", "scope": "Private native KDE model, owned windows only", "backend":args.backend,
              "checks": checks, "qml_diagnostics": warnings, "protected_config_sha256": protected,
              "desktop_modified": False, "source_sha256": {name: digest(REPO / name) for name in (
                  "plasma/applets/org.irixclassic.domainos.panel/contents/ui/DomainOSTasks.qml",
                  "plasma/applets/org.irixclassic.domainos.panel/contents/ui/DomainOSTaskSelection.js")}}
    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)
    for executable in (("Xvfb", "openbox") if args.backend=="x11" else ("kwin_wayland","qdbus6")):
        if not shutil.which(executable):
            parser.error("Missing " + executable)
    with tempfile.TemporaryDirectory(prefix="irix-domainos-native-tasks-") as folder:
        private = Path(folder)
        for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                          ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
            path = private / name
            path.mkdir(mode=0o700)
            os.environ[key] = str(path)
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE",
                    "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE"):
            os.environ.pop(key, None)
        os.environ.update(QT_QPA_PLATFORM="xcb", QT_QUICK_BACKEND="software", QT_QPA_PLATFORMTHEME="generic",
                          QT_SCALE_FACTOR="1", XDG_CURRENT_DESKTOP="NONE", XDG_SESSION_TYPE="x11",
                          QT_ACCESSIBILITY="0", LIBGL_ALWAYS_SOFTWARE="1", GIO_USE_VFS="local",
                          DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(private / "disabled-system-bus"))
        read_fd, write_fd = os.pipe()
        log = (output / "SESSION.log").open("w")
        if args.backend=="x11":
            server = subprocess.Popen(["Xvfb", "-displayfd", str(write_fd), "-screen", "0", "1200x900x24", "-nolisten", "tcp"],
                                      pass_fds=[write_fd], stdout=log, stderr=log)
        else:
            (private/"config/kwinrc").write_text("[Desktops]\nNumber=1\n[Compositing]\nEnabled=true\n")
            environment=dict(os.environ,QT_QPA_PLATFORM="offscreen",KWIN_COMPOSE="Q",XDG_SESSION_TYPE="wayland")
            server=subprocess.Popen(["kwin_wayland","--virtual","--width","1200","--height","900",
                "--socket","domainos-native-tasks","--no-lockscreen","--no-global-shortcuts","--no-kactivities"],
                env=environment,stdout=log,stderr=log)
        os.close(write_fd)
        wm = None
        try:
            if args.backend=="x11":
                if not select.select([read_fd], [], [], 10)[0]:
                    raise RuntimeError("Private Xvfb did not provide a display")
                number = os.read(read_fd, 32).decode().strip()
                if not number.isdecimal():raise RuntimeError("Invalid private Xvfb display")
                os.environ["DISPLAY"] = ":" + number
                wm = subprocess.Popen(["openbox", "--sm-disable"], stdout=log, stderr=log)
            else:
                ready=False
                for _ in range(100):
                    probe=subprocess.run(["qdbus6","org.kde.KWin","/VirtualDesktopManager"],capture_output=True,timeout=2)
                    if probe.returncode==0:ready=True;break
                    if server.poll() is not None:break
                    time.sleep(.05)
                require("private_wayland_kwin_ready",ready)
                os.environ.update(QT_QPA_PLATFORM="wayland",WAYLAND_DISPLAY="domainos-native-tasks",XDG_SESSION_TYPE="wayland")
            from PyQt6.QtCore import Qt, QUrl, QMetaObject, Q_RETURN_ARG, Q_ARG, qVersion
            from PyQt6.QtGui import QColor, QGuiApplication
            from PyQt6.QtQml import QQmlApplicationEngine
            from PyQt6.QtQuick import QQuickWindow
            from PyQt6.QtTest import QTest
            app = QGuiApplication(["domainos-task-native-test"])
            app.setQuitOnLastWindowClosed(False)
            app.setApplicationName("DomainOS owned task test")
            engine = QQmlApplicationEngine()
            engine.warnings.connect(lambda messages: warnings.extend(str(message.toString()) for message in messages))
            engine.load(QUrl.fromLocalFile(str(REPO / "plasma/tests/DomainOSTasksNativePreview.qml")))
            require("native_fixture_loaded", bool(engine.rootObjects()))
            fixture = engine.rootObjects()[0]
            def call(method, *arguments):
                result = QMetaObject.invokeMethod(fixture, method, Qt.ConnectionType.DirectConnection,
                                                 Q_RETURN_ARG("QVariant"), *(Q_ARG("QVariant", value) for value in arguments))
                app.processEvents()
                return result
            def state():
                return json.loads(call("state"))
            def wait_for(predicate, timeout=4):
                until = time.monotonic() + timeout
                while time.monotonic() < until:
                    app.processEvents()
                    if predicate():
                        return True
                    QTest.qWait(20)
                return False
            owned = []
            for index in range(3):
                window = QQuickWindow()
                window.setTitle("DomainOS owned native " + str(index))
                window.setColor(QColor("#607f91"))
                window.setGeometry(80 + index * 240, 80 + index * 80, 200, 150)
                window.show()
                owned.append(window)
            require("private_windows_visible_in_native_scope", wait_for(lambda: all(
                window.title() in [row["title"] for row in state()["windows"]] for window in owned)))
            rows = state()["windows"]
            ids=[next(row["windowIds"][0] for row in rows if row["title"]==window.title()) for window in owned]
            require("native_task_ids_and_pids_match_owned_process", all(row["pid"] == os.getpid()
                    for row in rows if row["windowIds"][0] in ids))
            require("native_scope_has_only_owned_window_ids", {row["windowIds"][0] for row in rows} == set(ids))
            if args.backend=="x11":require("x11_ids_match_owned_windows",ids==[int(window.winId()) for window in owned])
            else:require("wayland_ids_are_native_uuids",all(isinstance(value,str) and len(value.strip('{}'))==36 for value in ids))
            keys = {row["windowIds"][0]: row["key"] for row in rows}
            call("choose", keys[ids[0]], 0)
            call("choose", keys[ids[1]], int(Qt.KeyboardModifier.ControlModifier.value))
            require("native_model_selection_is_immediate_and_identity_based", set(state()["selected"]) == {keys[ids[0]], keys[ids[1]]})
            result = json.loads(call("action", keys[ids[1]], "minimize"))
            require("native_minimize_request_sent", result["state"] == "requested")
            require("native_minimize_state_observed", wait_for(lambda: any(row["key"] == keys[ids[1]] and row["minimized"] for row in state()["windows"])))
            result = json.loads(call("action", keys[ids[1]], "activate"))
            require("native_activation_request_sent", result["state"] == "requested")
            require("native_restore_and_activation_observed", wait_for(lambda: any(row["key"] == keys[ids[1]] and not row["minimized"] and row["active"] for row in state()["windows"])))
            result = json.loads(call("action", keys[ids[0]], "maximize"))
            require("native_maximize_request_sent", result["state"] == "requested")
            require("native_maximize_state_observed", wait_for(lambda: any(row["key"] == keys[ids[0]] and row["maximized"] for row in state()["windows"])))
            result = json.loads(call("action", keys[ids[2]], "close"))
            require("native_close_request_sent", result["state"] == "requested")
            require("native_close_removes_only_target", wait_for(lambda: {row["windowIds"][0] for row in state()["windows"]} == set(ids[:2])))
            require("native_remaining_selection_preserved", set(state()["selected"]) == {keys[ids[0]], keys[ids[1]]})
            capture=app.primaryScreen().grabWindow(0) if args.backend=="x11" else owned[0].grabWindow()
            require("native_capture_saved",capture.save(str(output/("NATIVE-X11.png" if args.backend=="x11" else "NATIVE-WAYLAND-CLIENT.png"))))
            require("qml_diagnostics_zero", not warnings)
            require("real_preferences_unchanged", all(digest(Path(path)) == expected for path, expected in protected.items()))
            require("production_sources_unchanged", all(digest(REPO / name) == expected for name, expected in report["source_sha256"].items()))
            report.update(status="passed", qt=qVersion(), final_state=state(), owned_ids=ids)
            for window in owned:
                window.close()
            app.processEvents()
        except Exception as error:
            report["error"] = str(error)
            if "state" in locals():
                report["last_state"] = state()
        finally:
            if wm:
                wm.terminate()
                wm.wait(timeout=5)
            server.terminate()
            server.wait(timeout=5)
            os.close(read_fd)
            log.close()
            (output / "RESULTADO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "report": str(output / "RESULTADO.json"), "error": report.get("error")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
