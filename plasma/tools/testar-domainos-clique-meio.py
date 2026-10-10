#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical middle-click launch through genuine KDE task models and own clients.

Reuses the Unity test's private Xvfb/KWin/D-Bus/bootstrap. Both Desktop Entries
have Actions=new-empty-window, which hides KDE's generic New Instance menu.
No user's application or desktop session is contacted. New PIDs/windows are
observed rather than treating a request signal as proof of a launch.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("private_middle_bootstrap", Path(__file__).with_name("testar-domainos-unity.py"))
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
REPO = harness.REPO
CLIENT = REPO / "plasma/tests/domainos-middle-client.py"
IDENTIFIER = "org.irixclassic.qa.middle.fixture"
PRODUCTION = REPO / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"


def stop_owned_clients(output):
    observations = []
    for path in sorted(output.glob("marker-*.json")):
        marker = json.loads(path.read_text())
        pid = marker.get("pid")
        observation = {"pid":pid,"stopped":False}
        descriptor = None
        try:
            if not isinstance(pid, int) or pid <= 1:
                raise RuntimeError("Invalid marker PID")
            descriptor = os.pidfd_open(pid)
            proc = Path("/proc") / str(pid)
            arguments = (proc / "cmdline").read_bytes().split(b"\0")
            environment = (proc / "environ").read_bytes().split(b"\0")
            if str(CLIENT).encode() not in arguments or ("IRIX_DOMAINOS_MIDDLE_OUTPUT=" + str(output)).encode() not in environment:
                observation["reason"] = "Identity differs; untouched"
            else:
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(2500):
                    signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                    observation["forced"] = True
                observation.update(stopped=bool(poller.poll(2500)), pidfd_used=True)
        except (ProcessLookupError, FileNotFoundError):
            observation.update(stopped=True, already_exited=True)
        finally:
            if descriptor is not None:
                os.close(descriptor)
        observations.append(observation)
    return observations


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_UNITY_PRIVATE") != "1":
        raise RuntimeError("Private session required")
    environment = dict(os.environ, IRIX_DOMAINOS_MIDDLE_OUTPUT=str(output))
    initial = []
    logs = []
    wm = None
    result = None
    cleanup = {}
    try:
        cache = subprocess.run(["kbuildsycoca6", "--noincremental"], env=environment,
            capture_output=True, text=True, timeout=15)
        (output / "sycoca.log").write_text(cache.stdout + cache.stderr)
        wm_log = (output / "kwin.log").open("w")
        logs.append(wm_log)
        wm = subprocess.Popen(["kwin_x11"], env=environment, stdout=wm_log, stderr=subprocess.STDOUT)
        for _ in range(100):
            if subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"],
                    env=environment, capture_output=True, timeout=2).returncode == 0:
                break
            time.sleep(.05)
        else:
            raise RuntimeError("Private KWin unavailable")
        for family, instance in (("group", "initial-1"), ("group", "initial-2"), ("single", "initial-1")):
            log = (output / (family + "-" + instance + ".log")).open("w")
            logs.append(log)
            initial.append(subprocess.Popen(["/usr/bin/python3", "-B", str(CLIENT),
                "--family", family, "--instance", instance], env=environment,
                stdout=log, stderr=subprocess.STDOUT))
        host_env = dict(environment, LD_PRELOAD=os.environ["IRIX_DOMAINOS_UNITY_LIB"])
        result = subprocess.run(["plasmawindowed", IDENTIFIER], env=host_env,
            capture_output=True, text=True, timeout=30)
        (output / "host.log").write_text(result.stdout + result.stderr)
        native = json.loads((output / "native.json").read_text()) if (output / "native.json").is_file() else {}
        errors = [line for line in (result.stdout + result.stderr).splitlines() if re.search(
            r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable", line)]
        checks = dict(native.get("checks", {}))
        checks.update(native_host_exited=result.returncode == 0, qml_diagnostics_zero=not errors,
            private_desktop_cache_created=cache.returncode == 0)
        markers = [json.loads(path.read_text()) for path in sorted(output.glob("marker-*.json"))]
        checks["five_owned_process_markers"] = len(markers) == 5 and len({marker["pid"] for marker in markers}) == 5
        checks["both_launched_programs_in_private_namespaces"] = all(
            marker["display"] == environment["DISPLAY"] and marker["bus"] == environment["DBUS_SESSION_BUS_ADDRESS"]
            and marker["runtime"] == environment["XDG_RUNTIME_DIR"] and marker["data"] == environment["XDG_DATA_HOME"]
            and marker["config"] == environment["XDG_CONFIG_HOME"] and not marker["preload"]
            for marker in markers if marker["instance"] == "launched")
        report = {"status":"passed" if checks and all(checks.values()) else "failed", "checks":checks,
            "native":native,"markers":markers,"qml_diagnostics":errors,"scope":__doc__}
        (output / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        return 0 if report["status"] == "passed" else 1
    finally:
        cleanup["clients"] = stop_owned_clients(output)
        for process in initial:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(3)
        if wm is not None:
            wm.terminate()
            try:
                wm.wait(3)
            except subprocess.TimeoutExpired:
                wm.kill()
                wm.wait(3)
        cleanup["own_initial_processes_reaped"] = all(process.poll() is not None for process in initial)
        cleanup["private_kwin_reaped"] = wm is None or wm.poll() is not None
        (output / "cleanup.json").write_text(json.dumps(cleanup, indent=2) + "\n")
        for log in logs:
            log.close()


harness.IDENTIFIER = IDENTIFIER
harness.__doc__ = __doc__
harness.NATIVE_SOURCE = REPO / "plasma/tests/domainos-middle-host.cpp"
harness.NATIVE_LIBRARIES = ("Qt6Widgets",)
harness.CONTROLS_STYLE = "org.kde.desktop"
harness.HOST_TIMEOUT = 30
harness.RUN_TIMEOUT = 45
harness.worker = worker
harness.EXTRA_APPLICATIONS = {}
for family in ("group", "single"):
    command = '/usr/bin/env -u LD_PRELOAD /usr/bin/python3 -B "' + str(CLIENT) + '" --family ' + family + ' --instance launched'
    harness.EXTRA_APPLICATIONS["org.irixclassic.qa.middle." + family + ".desktop"] = (
        "[Desktop Entry]\nType=Application\nName=DomainOS middle " + family + "\nExec=" + command
        + "\nIcon=utilities-terminal\nStartupWMClass=domainos-middle-" + family
        + "\nTerminal=false\nDBusActivatable=false\nActions=new-empty-window;\n"
        + "[Desktop Action new-empty-window]\nName=New Window\nExec=" + command + "\n")
harness.QML = '''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
 id:host;preferredRepresentation:fullRepresentation
 fullRepresentation:Item {
  id:fixture;objectName:"domainosMiddleFixture"
  Layout.minimumWidth:594;Layout.minimumHeight:150
  property var requests:[]
  function recordFor(family) {return tasks.taskRows.find(row=>row.launcherUrl===
   "applications:org.irixclassic.qa.middle."+family+".desktop")}
  function state() {
   const group=recordFor("group"),single=recordFor("single")
   return JSON.stringify({rows:tasks.taskRows,windows:tasks.windowRows,requests:requests,
    selection:tasks.selectedKeys,groupPopup:box.groupPopupVisible,lastError:box.lastError,
    group:group,single:single,groupButtonReady:!!group && !!box.buttonForKey(group.key),
    singleButtonReady:!!single && !!box.buttonForKey(single.key),
    middlePreference:box.middleClickAction,nativeModel:String(tasks.tasksModel),
    groupRole:group ? tasks.value(tasks.tasksModel,tasks.tasksModel.makeModelIndex(tasks.taskRows.indexOf(group)),
     TaskManager.AbstractTasksModel.CanLaunchNewInstance,null) : null,
    singleRole:single ? tasks.value(tasks.tasksModel,tasks.tasksModel.makeModelIndex(tasks.taskRows.indexOf(single)),
     TaskManager.AbstractTasksModel.CanLaunchNewInstance,null) : null})
  }
  function coordinates(family) {
   const record=recordFor(family),button=record?box.buttonForKey(record.key):null
   if(!button)return "{}"
   const p=button.mapToGlobal(button.width/2,button.height/2)
   return JSON.stringify({x:p.x,y:p.y,key:record.key,group:record.group})
  }
  Panel.DomainOSPalette {id:colors;followSystem:false}
  Panel.DomainOSTasks {id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;
   groupingMode:1;onlyGroupWhenFull:false;sortMode:1;
   onOperationRequested:request=>fixture.requests=fixture.requests.concat([request])}
  Panel.DomainOSIconbox {id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;
   hostItem:host;nativeMenusEnabled:true;hintsEnabled:false;highlightWindows:false}
 }
}
'''


def main():
    if "--worker" in sys.argv:
        return harness.main()
    source_files = [PRODUCTION / name for name in ("DomainOSTasks.qml", "DomainOSIconbox.qml", "DomainOSTaskButton.qml")]
    sources_before = {str(path.relative_to(REPO)):hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
    original_run = harness.subprocess.run
    with tempfile.TemporaryDirectory(prefix="ird-mc-", dir="/tmp") as runtime:
        # Two narrowly scoped transport hooks keep using the existing runner:
        # a short native socket namespace and repository-local compiler TMPDIR.
        def scoped_run(command, *arguments, **options):
            if command[0] == "c++":
                environment = dict(options.get("env", os.environ))
                environment["TMPDIR"] = str(Path(command[command.index("-o") + 1]).parent / "temp")
                options["env"] = environment
            if command[0] == "xvfb-run":
                environment = dict(options["env"], XDG_RUNTIME_DIR=runtime)
                bus = Path(command[command.index("--config-file") + 1])
                bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=' + runtime
                    + '</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/>'
                    + '<allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
                options["env"] = environment
                process = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, start_new_session=True)
                try:
                    stdout, stderr = process.communicate(timeout=options["timeout"])
                except subprocess.TimeoutExpired:
                    # Bound the whole private server/bus/worker tree, rather
                    # than killing only xvfb-run and leaving test children.
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                    raise
                return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
            return original_run(command, *arguments, **options)
        harness.subprocess.run = scoped_run
        try:
            result = harness.main()
        finally:
            harness.subprocess.run = original_run
    output = Path(sys.argv[sys.argv.index("--saida") + 1]).resolve()
    if (output / "RESULTADO.json").is_file():
        report = json.loads((output / "RESULTADO.json").read_text())
        cleanup = json.loads((output / "cleanup.json").read_text()) if (output / "cleanup.json").is_file() else {}
        report["cleanup"] = cleanup
        report["source_sha256"] = sources_before
        report["test_source_sha256"] = {str(path.relative_to(REPO)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), CLIENT, harness.NATIVE_SOURCE)}
        report["desktop_entries"] = harness.EXTRA_APPLICATIONS
        report["checks"].update(own_clients_stopped=bool(cleanup.get("clients")) and all(item["stopped"] for item in cleanup.get("clients", [])),
            own_initial_processes_reaped=cleanup.get("own_initial_processes_reaped") is True,
            private_kwin_reaped=cleanup.get("private_kwin_reaped") is True,short_private_runtime_removed=not Path(runtime).exists(),
            desktop_entry_new_window_actions_present=all("Actions=new-empty-window;\n" in entry
                and "[Desktop Action new-empty-window]\n" in entry for entry in harness.EXTRA_APPLICATIONS.values()),
            production_sources_unchanged=sources_before == {str(path.relative_to(REPO)):hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files})
        report["status"] = "passed" if result == 0 and all(report["checks"].values()) else "failed"
        (output / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"status":report["status"],"checks":len(report["checks"]),"report":str(output / "RESULTADO.json")}))
        return 0 if report["status"] == "passed" else 1
    return result


if __name__ == "__main__":
    raise SystemExit(main())
