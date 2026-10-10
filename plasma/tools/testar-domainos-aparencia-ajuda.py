#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Observe Appearance and KDE Help launched by the genuine QML command bridge.

Only these two controller methods run, on fresh HOME/XDG, Xvfb and a private
session bus without activation directories. No session or power action runs.
The test-only preloaded observer inspects existing native widgets/QML/web pages;
it does not replace an application, provide a service, or change application UI.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "plasma/applets/org.irixclassic.domainos.panel"
UI = PACKAGE / "contents/ui"
PRODUCTION = [UI / name for name in ("DomainOSCommands.qml", "DomainOSActivity.qml", "DomainOSPalette.qml")]
PRODUCTION.append(PACKAGE / "contents/code/commands.py")
PREFERENCES = ("kdeglobals", "kwinrc", "plasmarc", "plasma-org.kde.plasma.desktop-appletsrc",
               "Kvantum/kvantum.kvconfig", "gtk-3.0/settings.ini", "gtk-4.0/settings.ini", "mimeapps.list")


def hashes(paths):
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None for path in paths}


def proc(pid):
    path = Path("/proc") / str(pid)
    try:
        fields = (path / "stat").read_text().split(") ", 1)[1].split()
        environment = dict(part.split("=", 1) for part in (path / "environ").read_bytes().decode(errors="replace").split("\0") if "=" in part)
        return {"pid": pid, "exe": str((path / "exe").resolve()), "argv": (path / "cmdline").read_bytes().decode(errors="replace").strip("\0").split("\0"),
                "startTicks": fields[19], "state": fields[0], "parent": int(fields[1]),
                "namespace": {name: environment.get(name) for name in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_SYSTEM_BUS_ADDRESS", "IRIX_DOMAINOS_APPEARANCE_DIR")}}
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return None


def private_processes(output):
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal() or int(entry.name) == os.getpid():
            continue
        info = proc(int(entry.name))
        if info and info["namespace"]["IRIX_DOMAINOS_APPEARANCE_DIR"] == str(output) and info["namespace"]["HOME"] == str(output / "home"):
            found.append(info)
    return found


def stop_owned(output):
    owned = private_processes(output)
    for info in owned:
        fresh = proc(info["pid"])
        if not fresh or fresh["startTicks"] != info["startTicks"] or fresh["namespace"] != info["namespace"]:
            continue
        # Exact namespace and creation identity, never a program-name search.
        try:
            os.kill(info["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and private_processes(output):
        time.sleep(.05)
    for info in private_processes(output):
        fresh = proc(info["pid"])
        if fresh and fresh["startTicks"] == info["startTicks"] and fresh["namespace"] == info["namespace"]:
            try:
                os.kill(info["pid"], signal.SIGKILL)
            except ProcessLookupError:
                pass
    return owned


def inside(output):
    from PyQt6.QtCore import QMetaObject, Q_RETURN_ARG, QUrl
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    app = QApplication([sys.argv[0]])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    checks = []
    report = {"status": "running", "checks": checks, "scope": "API invocation of production DomainOSCommands → real helper → native KDE applications; no panel button/whole session test",
              "actionsInvoked": [], "observations": {}, "qmlDiagnostics": warnings, "sessionOrPowerActionInvoked": False}

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})
        if not passed:
            raise AssertionError(name)

    def wait(predicate, seconds=20):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            app.processEvents()
            if predicate():
                return True
            QTest.qWait(20)
        return False

    def read_observer(name):
        try:
            return json.loads((output / (name + "-observer.json")).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def displayed(observer):
        return [window for window in observer.get("windows", []) if window["visible"] and window["width"] > 100 and window["height"] > 100]

    def snapshot(observer, name):
        windows = displayed(observer)
        if not windows:
            return False
        window = max(windows, key=lambda item: item["width"] * item["height"])
        image = app.primaryScreen().grabWindow(int(window["winId"])).toImage()
        report["observations"][name]["capturedWindow"] = window
        return not image.isNull() and image.width() > 100 and image.height() > 100 and image.save(str(output / (name.upper() + ".png")))

    fixture = output / "AppearanceHelpHarness.qml"
    fixture.write_text('''import QtQuick
import "''' + UI.as_uri() + '''" as Panel
Window {
    id: fixture; width: 340; height: 120; visible: true
    title: "DomainOS Appearance/Help — private controller test"
    Panel.DomainOSPalette { id: colors }
    Panel.DomainOSActivity { id: activity }
    Panel.DomainOSCommands { id: commands; palette: colors; activity: activity }
    function state(): string { return JSON.stringify({report: commands.lastReport,
        pending: activity.pendingCount, lit: activity.lit}) }
    function appearance() { commands.openAppearance() }
    function kdeHelp() { commands.openKdeHelp() }
}
''')
    try:
        check("private display and bus supplied, system bus isolated", bool(os.environ.get("DISPLAY")) and bool(os.environ.get("DBUS_SESSION_BUS_ADDRESS")) and os.environ.get("DBUS_SYSTEM_BUS_ADDRESS") == "unix:path=" + str(output / "no-system-bus"))
        check("all HOME/XDG roots are private and owned", all(Path(os.environ[name]).is_relative_to(output) and Path(os.environ[name]).stat().st_uid == os.getuid() for name in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR")))
        engine.load(QUrl.fromLocalFile(str(fixture)))
        check("production QML command controller loaded", bool(engine.rootObjects()))
        root = engine.rootObjects()[0]

        def state():
            return json.loads(QMetaObject.invokeMethod(root, "state", Q_RETURN_ARG(str)))

        # Set the observer only for processes created after loading this fixture.
        os.environ["LD_PRELOAD"] = str(output / "appearance-help-observer.so")
        for expected_token, (method, action, program, argument) in enumerate((("appearance", "appearance", "systemsettings", "kcm_lookandfeel"),
                                                  ("kdeHelp", "kde-help", "khelpcenter", "help:/plasma-desktop")), start=1):
            report["actionsInvoked"].append(action)
            QMetaObject.invokeMethod(root, method)
            check(action + " begins a real command", state()["pending"] == 1 and state()["lit"])
            check(action + " helper completes", wait(lambda: state()["report"].get("token") == expected_token and state()["pending"] == 0))
            result = state()["report"]
            report["observations"][program] = {"commandReport": result}
            check(action + " helper reports actual process creation", result.get("ok") is True and result.get("outcome") == "process-started" and isinstance(result.get("pid"), int))
            pid = result["pid"]
            check(action + " native observer sees the launched PID", wait(lambda: read_observer(program).get("pid") == pid))
            info = proc(pid)
            observer = read_observer(program)
            report["observations"][program].update(process=info, native=observer)
            check(action + " executable and argv are the genuine KDE program", info and info["exe"] == "/usr/bin/" + program and info["argv"] == [program, argument] and observer["argv"] == [program, argument])
            check(action + " native process retained the private namespace", info and all(info["namespace"].get(name) == os.environ[name] for name in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_SYSTEM_BUS_ADDRESS")))
            check(action + " visible native window appears", wait(lambda: bool(displayed(read_observer(program)))))
            if action == "appearance":
                def loaded():
                    native = read_observer(program)
                    text = json.dumps(native.get("objects", []), ensure_ascii=False)
                    return "Global Theme" in text and "Appearance & Style" in text
                check("Appearance & Style and Global Theme really loaded in native UI", wait(loaded))
                maps = (Path("/proc") / str(pid) / "maps").read_text()
                loaded_module = [line.rsplit(None, 1)[-1] for line in maps.splitlines() if "kcm_lookandfeel.so" in line]
                report["observations"][program]["loadedKcmPaths"] = sorted(set(loaded_module))
                check("real kcm_lookandfeel plugin mapped by System Settings", bool(loaded_module))
            else:
                def loaded_help():
                    native = read_observer(program)
                    return "The Plasma Handbook" in native.get("webBody", "") and any(view.get("url", "").startswith("help:/plasma-desktop") for view in native.get("webViews", []))
                check("KDE Help renders the actual local Plasma handbook", wait(loaded_help))
                check("manual text is content, not an error or welcome page", "Table of Contents" in read_observer(program).get("webBody", ""))
            observer = read_observer(program)
            report["observations"][program]["native"] = observer
            check(action + " visible window screenshot saved", snapshot(observer, program))
            check(action + " activity completes without a pending light", state()["pending"] == 0 and not state()["lit"])
        check("only Appearance and KDE Help were invoked", report["actionsInvoked"] == ["appearance", "kde-help"])
        check("no production QML errors or binding loops", not warnings)
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", error=str(error), traceback=traceback.format_exc())
        for program in ("systemsettings", "khelpcenter"):
            report["observations"].setdefault(program, {})["nativeAtFailure"] = read_observer(program)
            if read_observer(program):
                snapshot(read_observer(program), program)
    finally:
        os.environ.pop("LD_PRELOAD", None)
        # The outer runner owns cleanup after this JSON is complete. In here,
        # stopping the whole namespace would also stop our X server and bus.
        report["ownedProcessesBeforeCleanup"] = private_processes(output)
        report["totalChecks"] = len(checks)
        report["passedChecks"] = sum(item["passed"] for item in checks)
        (output / "NATIVE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({key: report.get(key) for key in ("status", "totalChecks", "passedChecks", "error")}))
    return report["status"] != "passed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.saida.resolve()
    if args.inside:
        if os.environ.get("IRIX_DOMAINOS_APPEARANCE_DIR") != str(output):
            parser.error("Private runner marker is required")
        return inside(output)
    if not output.is_relative_to("/tmp") or output.exists():
        parser.error("Use a fresh output directory under /tmp")
    for program in ("xvfb-run", "dbus-run-session", "xdotool", "pkg-config", "c++", "systemsettings", "khelpcenter"):
        if not shutil.which(program):
            parser.error("Missing native test dependency: " + program)
    output.mkdir(mode=0o700)
    real_config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    protected = [real_config / name for name in PREFERENCES]
    before, sources = hashes(protected), hashes(PRODUCTION)
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets"], text=True))
    build = subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(REPO / "plasma/tests/domainos-appearance-help-observer.cpp"),
                            "-o", str(output / "appearance-help-observer.so"), *flags, "-ldl"], capture_output=True, text=True)
    (output / "build.log").write_text(build.stdout + build.stderr)
    if build.returncode:
        raise RuntimeError("Native observer compilation failed; see " + str(output / "build.log"))
    env = os.environ.copy()
    for name in ("DISPLAY", "WAYLAND_DISPLAY", "WAYLAND_SOCKET", "DBUS_SESSION_BUS_ADDRESS", "DBUS_SESSION_BUS_PID", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "KDE_SESSION_UID", "XDG_SESSION_ID", "XAUTHORITY"):
        env.pop(name, None)
    for name, directory in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        root = output / directory
        root.mkdir(mode=0o700)
        env[name] = str(root)
    env.update(QT_QPA_PLATFORM="xcb", QT_QUICK_BACKEND="software", QT_QPA_PLATFORMTHEME="generic", QSG_RHI_BACKEND="software",
               XDG_CURRENT_DESKTOP="NONE", XDG_SESSION_TYPE="x11", XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg",
               LANG="C.UTF-8", LANGUAGE="en", PYTHONDONTWRITEBYTECODE="1", IRIX_DOMAINOS_APPEARANCE_DIR=str(output),
               DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(output / "no-system-bus"))
    bus = output / "bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>'
                   '<policy context="default"><allow send_destination="*"/><allow send_type="signal"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x900x24", "dbus-run-session", "--config-file", str(bus), "--",
               "/usr/bin/python3", str(Path(__file__).resolve()), "--saida", str(output), "--inside"]
    timed_out = False
    runner = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = runner.communicate(timeout=75)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(runner.pid, signal.SIGTERM)
        try:
            stdout, stderr = runner.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(runner.pid, signal.SIGKILL)
            stdout, stderr = runner.communicate()
    finally:
        leftovers = stop_owned(output)
    (output / "native.log").write_text(stdout + stderr)
    after, after_sources = hashes(protected), hashes(PRODUCTION)
    native = json.loads((output / "NATIVE.json").read_text()) if (output / "NATIVE.json").is_file() else {"status": "failed", "checks": [], "error": "Native runner did not produce a report"}
    checks = native["checks"]
    def check(name, value):
        checks.append({"name": name, "passed": bool(value)})
    check("native runner exits normally within bound", not timed_out and runner.returncode == 0)
    check("eight real protected preferences retain exact bytes", before == after)
    check("production controller helper palette and activity retain exact bytes", sources == after_sources)
    remaining = private_processes(output)
    check("all processes in the private test namespace are stopped", not remaining)
    native.update(status="passed" if all(item["passed"] for item in checks) else "failed", totalChecks=len(checks),
                  passedChecks=sum(item["passed"] for item in checks), runnerCommand=command, timedOut=timed_out,
                  protectedBefore=before, protectedAfter=after, sourceHashesBefore=sources, sourceHashesAfter=after_sources,
                  outerCleanup=leftovers, remainingProcesses=remaining,
                  result=str(output / "RESULTADO.json"), activationDirectories=False)
    (output / "RESULTADO.json").write_text(json.dumps(native, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: native.get(key) for key in ("status", "totalChecks", "passedChecks", "result", "error")}, ensure_ascii=False, indent=2))
    return native["status"] != "passed"


if __name__ == "__main__":
    raise SystemExit(main())
