#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test transient window operations with owned windows in private KWin sessions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / "plasma/applets/org.irixclassic.domainos.panel/contents/code/window_ops.py"


def worker(args):
    output = args.saida.resolve()
    checks, operations = {}, []
    compositor_log = (output / "kwin.log").open("w")
    command = ["kwin_x11", "--replace"] if args.backend == "x11" else ["kwin_wayland", "--virtual", "--width", "1200", "--height", "700", "--output-count", "2", "--socket", "domainos-test", "--no-lockscreen", "--no-global-shortcuts", "--no-kactivities"]
    environment = dict(os.environ)
    if args.backend == "wayland":
        environment["QT_QPA_PLATFORM"] = "offscreen"
        environment["KWIN_COMPOSE"] = "Q"
    compositor = subprocess.Popen(command, env=environment, stdout=compositor_log, stderr=subprocess.STDOUT)
    owned_client = None
    def check(name, condition):
        checks[name] = bool(condition)
        if not condition: raise AssertionError(name)
    def cli(*arguments):
        return subprocess.run(["qdbus6", "org.kde.KWin", *map(str, arguments)], capture_output=True, text=True, timeout=5)
    try:
        for _ in range(100):
            ready = cli("/VirtualDesktopManager")
            if ready.returncode == 0: break
            if compositor.poll() is not None: break
            time.sleep(.05)
        check("private_compositor_ready", ready.returncode == 0 and compositor.poll() is None)
        if args.backend == "wayland":
            os.environ.update(QT_QPA_PLATFORM="wayland", WAYLAND_DISPLAY="domainos-test")
        from PyQt6.QtCore import QObject, Qt, pyqtClassInfo, pyqtSlot
        from PyQt6.QtDBus import QDBusConnection
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication, QWidget, QDialog
        app = QApplication(["domainos-window-operations-test"])
        app.setQuitOnLastWindowClosed(False)
        fixture_result = {}
        @pyqtClassInfo("D-Bus Interface", "org.irixclassic.DomainOS.WindowTest")
        class FixtureReply(QObject):
            @pyqtSlot(str)
            def completed(self, value):
                nonlocal fixture_result
                fixture_result = json.loads(value)
        fixture_endpoint = FixtureReply()
        fixture_service = "org.irixclassic.DomainOS.WindowTest.n" + uuid.uuid4().hex
        fixture_bus = QDBusConnection.sessionBus()
        check("private_fixture_endpoint_ready", fixture_bus.registerService(fixture_service)
            and fixture_bus.registerObject("/Fixture", fixture_endpoint, QDBusConnection.RegisterOption.ExportAllSlots))
        def fixture(source):
            """Prepare owned test windows through a separately scoped script."""
            nonlocal fixture_result
            fixture_result = {}
            name = "irixclassic-domainos-test-" + uuid.uuid4().hex
            path = output / (name + ".js")
            path.write_text(source + '\ncallDBus(' + json.dumps(fixture_service)
                + ', "/Fixture", "org.irixclassic.DomainOS.WindowTest", "completed", JSON.stringify(result));\n')
            loaded = cli("/Scripting", "org.kde.kwin.Scripting.loadScript", path, name)
            check("fixture_script_loaded", loaded.returncode == 0 and loaded.stdout.strip().isdecimal())
            try:
                started = cli("/Scripting/Script" + loaded.stdout.strip(), "org.kde.kwin.Script.run")
                check("fixture_script_started", started.returncode == 0)
                end = time.monotonic()+5
                while not fixture_result and time.monotonic()<end: QTest.qWait(10)
                check("fixture_result_received", bool(fixture_result))
                return fixture_result
            finally:
                cli("/Scripting", "org.kde.kwin.Scripting.unloadScript", name)
        windows = []
        for index in range(6):
            window = QWidget()
            window.setWindowTitle("DomainOS owned test " + str(index))
            window.resize(260, 180); window.move(40 + index*35, 60 + index*25)
            window.setStyleSheet("background:" + ("#607f91" if index%2 else "#7894a7") + ";")
            window.show(); windows.append(window)
        QTest.qWait(500)
        def operation(request):
            process = subprocess.Popen([sys.executable, str(HELPER), json.dumps(request)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            end = time.monotonic() + 12
            while process.poll() is None and time.monotonic() < end: QTest.qWait(10)
            if process.poll() is None: process.kill()
            stdout, stderr = process.communicate()
            result = json.loads(stdout) if stdout.strip() else {"ok": False, "detail": stderr}
            operations.append({"request": request, "result": result, "stderr": stderr})
            return result
        observed = operation({"action": "inspect"})
        check("kwin_reports_owned_windows", observed.get("ok") and sum(value["pid"] == os.getpid() for value in observed.get("windows", [])) == 6)
        ids = {value["title"]: value["id"] for value in observed["windows"]}
        desktop_id = observed["currentDesktop"]["id"]
        records = [{"key": "window:" + str(int(window.winId()) if args.backend == "x11" else ids[window.windowTitle()]),
            "windowIds": [int(window.winId()) if args.backend == "x11" else ids[window.windowTitle()]], "pid": os.getpid()} for window in windows]
        cli("/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager.createDesktop", 1, "Other test desktop")
        # Move only this test's windows to another native desktop/output first.
        placement = fixture('''
const own = workspace.windowList().filter(window => window.pid === '''+str(os.getpid())+''');
const ids = '''+json.dumps([ids[windows[0].windowTitle()], ids[windows[1].windowTitle()]])+''';
const selected = own.filter(window => ids.includes(String(window.internalId).replace(/[{}]/g,"")));
const origin = workspace.screens[0];
const remote = workspace.screens.length > 1 ? workspace.screens[1] : origin;
const otherDesktop = workspace.desktops.find(desktop => desktop.id !== workspace.currentDesktop.id);
for (const window of selected) {
    workspace.sendClientToScreen(window, remote);
    window.desktops = [otherDesktop];
}
const anchor = own.find(window => !selected.includes(window));
workspace.sendClientToScreen(anchor, origin);
workspace.activeWindow = anchor;
const result = {desktopId:otherDesktop.id,output:remote.name,outputCount:workspace.screens.length};
''')
        QTest.qWait(100)
        before_gather = operation({"action":"inspect"})
        check("targets_really_start_on_other_desktop", all(value["desktopIds"] == [placement["desktopId"]]
            for value in before_gather["windows"] if value["id"] in ids.values() and value["title"] in [window.windowTitle() for window in windows[:2]]))
        if args.backend == "wayland":
            check("targets_really_start_on_other_monitor", placement["outputCount"] == 2 and placement["output"] != before_gather["output"]
                and all(value["output"] == placement["output"] for value in before_gather["windows"] if value["title"] in [window.windowTitle() for window in windows[:2]]))
        gathered = operation({"action":"layout", "mode":"collect", "windows":records[:2], "desktopId":desktop_id})
        check("gather_from_other_desktop_monitor_confirmed", gathered.get("ok") and gathered.get("outcome")=="confirmed")
        gathered_state = operation({"action":"inspect"})
        gathered_ids = {ids[window.windowTitle()] for window in windows[:2]}
        check("gather_destination_observed_again", all(value["desktopIds"] == [desktop_id] and value["output"] == gathered_state["output"]
            for value in gathered_state["windows"] if value["id"] in gathered_ids))
        for count in (2, 3, 6):
            for mode in ("columns", "rows", "mosaic"):
                for window in windows[:count]: window.showNormal()
                QTest.qWait(30)
                result = operation({"action": "layout", "mode": mode, "windows": records[:count], "desktopId": desktop_id})
                check(mode + "_" + str(count) + "_confirmed", result.get("ok") and result.get("outcome") == "confirmed" and len(result.get("windows", [])) == count)
                actual = operation({"action": "inspect"})
                expected = {value["id"]: value for value in result["windows"]}
                check(mode + "_" + str(count) + "_observed_again", all(value["geometry"] == expected[value["id"]]["actual"] and value["desktopIds"] == [desktop_id] for value in actual["windows"] if value["id"] in expected))
        for mode in ("maximize", "minimize", "collect"):
            result = operation({"action":"layout", "mode":mode, "windows":records[:3], "desktopId":desktop_id})
            check(mode+"_batch_confirmed", result.get("ok") and result.get("outcome")=="confirmed")
            actual = operation({"action":"inspect"})
            selected = {value["id"] for value in result["windows"]}
            check(mode+"_batch_observed_again", all(value["desktopIds"]==[desktop_id] and
                (mode!="minimize" or value["minimized"]) and (mode!="maximize" or not value["minimized"])
                for value in actual["windows"] if value["id"] in selected))
        before = operation({"action": "inspect"})
        bad = dict(records[0], pid=os.getpid()+10000)
        rejected = operation({"action": "layout", "mode": "columns", "windows": [bad, records[1]], "desktopId": desktop_id})
        after = operation({"action": "inspect"})
        check("changed_process_rejected_before_mutation", not rejected.get("ok") and before.get("windows") == after.get("windows"))
        stale = operation({"action": "layout", "mode": "columns", "windows": records[:2], "desktopId": "nonexistent-desktop"})
        check("stale_desktop_rejected", not stale.get("ok"))
        dialog = QDialog(windows[0])
        dialog.setWindowTitle("DomainOS owned related dialog")
        dialog.resize(220,150)
        dialog.show()
        for _ in range(30):
            QTest.qWait(50)
            related_before = operation({"action":"inspect"})
            related = next((value for value in related_before["windows"] if value["title"]==dialog.windowTitle()),{})
            if related.get("transientFor")==ids[windows[0].windowTitle()]: break
        check("native_dialog_parent_relation_observed", related.get("transient")
            and related.get("transientFor")==ids[windows[0].windowTitle()])
        dialog_id = int(dialog.winId()) if args.backend=="x11" else related["id"]
        dialog_record = {"key":"window:"+str(dialog_id),"windowIds":[dialog_id],"pid":os.getpid()}
        for mode in ("collect","columns","maximize","minimize"):
            before_related = operation({"action":"inspect"})
            refusal = operation({"action":"layout","mode":mode,"windows":records[:2],"desktopId":desktop_id})
            after_related = operation({"action":"inspect"})
            check("unselected_dialog_"+mode+"_rejected_without_mutation", not refusal.get("ok")
                and "related dialogs" in refusal.get("detail","") and before_related["windows"]==after_related["windows"])
        before_related = operation({"action":"inspect"})
        refusal = operation({"action":"layout","mode":"collect","windows":[dialog_record],"desktopId":desktop_id})
        check("selected_transient_cannot_move_unselected_parent", not refusal.get("ok")
            and before_related["windows"]==operation({"action":"inspect"})["windows"])
        dialog.hide()
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.show()
        for _ in range(30):
            QTest.qWait(50)
            modal_before = operation({"action":"inspect"})
            if any(value["title"]==dialog.windowTitle() and value.get("modal") for value in modal_before["windows"]): break
        check("native_modal_relation_observed", any(value["title"]==dialog.windowTitle() and value.get("modal") for value in modal_before["windows"]))
        refusal = operation({"action":"layout","mode":"collect","windows":[dialog_record],"desktopId":desktop_id})
        check("selected_modal_cannot_move_unselected_parent", not refusal.get("ok")
            and modal_before["windows"]==operation({"action":"inspect"})["windows"])
        dialog.close()
        QTest.qWait(100)
        fixed_window = QWidget()
        fixed_window.setWindowTitle("DomainOS owned fixed-size test")
        fixed_window.setFixedSize(260,180)
        fixed_window.show()
        # Wayland size hints arrive with a client surface commit. Observe the
        # native capability before requesting a layout; do not assume delivery.
        for _ in range(30):
            QTest.qWait(50)
            fixed_before = operation({"action":"inspect"})
            if any(value["title"] == fixed_window.windowTitle() and not value["resizable"] for value in fixed_before["windows"]): break
        fixed_native = next((value for value in fixed_before["windows"] if value["title"] == fixed_window.windowTitle()), {})
        check("fixed_size_capability_observed", bool(fixed_native) and not fixed_native["resizable"])
        fixed_id = int(fixed_window.winId()) if args.backend=="x11" else fixed_native["id"]
        fixed_record = {"key":"window:"+str(fixed_id), "windowIds":[fixed_id], "pid":os.getpid()}
        fixed_rejected = operation({"action":"layout", "mode":"columns", "windows":[fixed_record,records[1]], "desktopId":desktop_id})
        fixed_after = operation({"action":"inspect"})
        check("nonresizable_client_rejected_before_mutation", not fixed_rejected.get("ok")
            and fixed_before["windows"] == fixed_after["windows"])
        fixed_window.close()
        QTest.qWait(100)
        sibling = operation({"action": "terminate-check", "windows": records[:1], "selectedKeys": [records[0]["key"]]})
        check("unselected_process_siblings_rejected", not sibling.get("ok") and "unselected" in sibling.get("detail", ""))
        owned_client = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--owned-client", "--saida", str(output)], stdout=subprocess.DEVNULL, stderr=compositor_log)
        client_path = output / "owned-client.json"
        end = time.monotonic()+5
        while not client_path.is_file() and time.monotonic()<end: QTest.qWait(10)
        check("dedicated_child_windows_ready", client_path.is_file() and owned_client.poll() is None)
        client = json.loads(client_path.read_text())
        QTest.qWait(200)
        child_state = operation({"action": "inspect"})
        child_windows = [value for value in child_state["windows"] if value["pid"] == owned_client.pid]
        check("only_dedicated_child_identified", len(child_windows)==2 and client["pid"]==owned_client.pid)
        child_records = [{"key":"window:"+str(client["windowIds"][index] if args.backend=="x11" else window["id"]),
            "windowIds":[client["windowIds"][index] if args.backend=="x11" else window["id"]], "pid":owned_client.pid}
            for index,window in enumerate(sorted(child_windows,key=lambda value:value["title"]))]
        refusal = operation({"action":"terminate", "window":child_records[0], "selectedKeys":[child_records[0]["key"]]})
        check("forced_termination_refuses_unselected_sibling", not refusal.get("ok") and owned_client.poll() is None)
        termination = operation({"action":"terminate", "window":child_records[0], "selectedKeys":[value["key"] for value in child_records]})
        check("forced_termination_signal_reported_truthfully", termination.get("ok") and termination.get("outcome")=="signal-sent" and termination.get("pid")==owned_client.pid)
        end = time.monotonic()+3
        while owned_client.poll() is None and time.monotonic()<end: QTest.qWait(10)
        check("only_dedicated_child_exit_observed", owned_client.returncode == -9 and sum(value["pid"]==os.getpid() for value in operation({"action":"inspect"})["windows"])==6)
        check("no_persistent_operation_scripts", cli("/Scripting").returncode == 0 and not any(Path(os.environ["XDG_DATA_HOME"]).rglob("operation.js")))
        if args.backend == "x11":
            app.primaryScreen().grabWindow(0).save(str(output / "WINDOWS-X11.png"))
            check("native_capture_saved", (output / "WINDOWS-X11.png").is_file())
        else:
            # Native clients can grab their own pixels, not the compositor's screen.
            windows[-1].grab().save(str(output / "WINDOW-WAYLAND.png"))
            check("native_client_capture_saved", (output / "WINDOW-WAYLAND.png").is_file())
        for window in windows: window.close()
        QTest.qWait(50)
    except Exception as error:
        checks["completed"] = False
        operations.append({"error": str(error)})
    finally:
        if owned_client and owned_client.poll() is None:
            owned_client.terminate()
            try: owned_client.wait(3)
            except subprocess.TimeoutExpired: owned_client.kill(); owned_client.wait()
        compositor.terminate()
        try: compositor.wait(5)
        except subprocess.TimeoutExpired: compositor.kill(); compositor.wait()
        compositor_log.close()
        report = {"status": "passed" if all(checks.values()) else "failed", "backend": args.backend,
            "checks": checks, "operations": operations,
            "source_sha256": {str(file.relative_to(REPO)): hashlib.sha256(file.read_bytes()).hexdigest() for file in (HELPER, HELPER.with_suffix(".js"))}}
        (output / "NATIVO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--backend", choices=("x11", "wayland"), default="x11")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--owned-client", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.owned_client:
        from PyQt6.QtWidgets import QApplication, QWidget
        from PyQt6.QtCore import QTimer
        app=QApplication(["domainos-owned-termination-client"])
        windows=[]
        for index in range(2):
            window=QWidget(); window.setWindowTitle("DomainOS dedicated child " + str(index)); window.resize(200,140); window.show(); windows.append(window)
        def ready():
            (args.saida/"owned-client.json").write_text(json.dumps({"pid":os.getpid(),"windowIds":[int(window.winId()) for window in windows]}))
        QTimer.singleShot(100,ready)
        return app.exec()
    if args.worker: return worker(args)
    output = args.saida.resolve()
    if output.exists() or not output.is_relative_to(Path("/tmp")): parser.error("Use a new output directory under /tmp")
    output.mkdir(mode=0o700)
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config"))
    def hashes():
        return {name: hashlib.sha256((config/name).read_bytes()).hexdigest() if (config/name).is_file() else None
            for name in ("kdeglobals", "plasmarc", "kwinrc", "plasma-org.kde.plasma.desktop-appletsrc")}
    before = hashes()
    env = dict(os.environ)
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "XAUTHORITY", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XDG_SESSION_ID"):
        env.pop(key, None)
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        folder = output / name; folder.mkdir(mode=0o700); env[key] = str(folder)
    (output/"config/kwinrc").write_text("[Desktops]\nNumber=1\nName_1=Test\n[Compositing]\nEnabled=" + ("false" if args.backend=="x11" else "true") + "\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
    env.update(QT_QPA_PLATFORM="xcb", QT_QPA_PLATFORMTHEME="generic", QT_QUICK_BACKEND="software", KWIN_COMPOSE="N", LIBGL_ALWAYS_SOFTWARE="1", QT_ACCESSIBILITY="0", XDG_CURRENT_DESKTOP="NONE", XDG_SESSION_TYPE=args.backend, XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output/"no-system-bus"))
    bus = output/"bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    command = ["dbus-run-session", "--config-file", str(bus), "--", sys.executable, str(Path(__file__).resolve()), "--worker", "--backend", args.backend, "--saida", str(output)]
    if args.backend == "x11": command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1200x700x24", *command]
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
    (output/"native.log").write_text(result.stdout+result.stderr)
    report = json.loads((output/"NATIVO.json").read_text()) if (output/"NATIVO.json").is_file() else {"checks": {"worker_report": False}, "failure": result.stdout+result.stderr}
    report["protected_configs"] = {"before": before, "after": hashes()}
    report["checks"]["host_configs_unchanged"] = before == hashes()
    report["checks"]["worker_exited_cleanly"] = result.returncode == 0
    report["status"] = "passed" if all(report["checks"].values()) else "failed"
    (output/"RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]), "result": str(output/"RESULTADO.json")}))
    return 0 if report["status"]=="passed" else 1


if __name__ == "__main__": raise SystemExit(main())
