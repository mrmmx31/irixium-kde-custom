#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise production QML job boundaries with a recording, failing source.

The real DomainOSActivity owns every token. No executable source is connected:
the injected provider only records strings and feeds synthetic results back.
WindowOperations watches a service registered exclusively on a private D-Bus
session. Each scenario has a process timeout and repository-local XDG/cache/tmp
directories; no desktop session, application, helper or lock action is used.
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"
CONTROLLERS = ("c1", "c2", "w1", "w2")


def run_worker(case):
    if os.environ.get("DOMAINOS_PRIVATE_JOB_TEST") != "1":
        raise RuntimeError("The QML worker requires the private test launcher")
    # This worker is reachable only through dbus-run-session in run_case().
    # Do not replace the private bus with an inherited desktop bus.
    from PyQt6.QtCore import Q_ARG, QMetaObject, QUrl, Qt, qInstallMessageHandler
    from PyQt6.QtDBus import QDBusConnection
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQml import QQmlComponent, QQmlEngine

    app = QGuiApplication([sys.argv[0]])
    bus = QDBusConnection.sessionBus()
    assert bus.isConnected(), "Private D-Bus session is unavailable"
    assert bus.registerService("org.kde.KWin"), "Cannot register the private watcher fixture"
    messages = []
    old_handler = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    fixture_file = Path(os.environ["TMPDIR"]) / "job-failure-fixture.qml"
    fixture_file.write_text('''import QtQuick
import "''' + UI.as_uri() + '''" as Production
Item {
    id:fixture
    property var reportLog: []
    property var activityLog: []
    property var lastReturn
    property var lastSnapshot
    component Provider: QtObject {
        property var owner
        property string mapName
        property var connections: []
        property var disconnections: []
        property bool throwConnect: false
        property bool completeInline: false
        property bool throwDisconnect: false
        function connectSource(source) {
            connections=connections.concat([source])
            if (completeInline) owner.handleResult(source,{stdout:JSON.stringify({
                ok:true,token:owner[mapName][source],outcome:"known-complete"})})
            if (throwConnect) throw new Error("PRIVATE connection details")
        }
        function disconnectSource(source) {
            disconnections=disconnections.concat([source])
            if (throwDisconnect) throw new Error("PRIVATE cleanup details")
        }
    }
    Production.DomainOSActivity {id:a1;onReported:report=>fixture.activityLog=fixture.activityLog.concat([{owner:"c1",report:report}])}
    Production.DomainOSActivity {id:a2;onReported:report=>fixture.activityLog=fixture.activityLog.concat([{owner:"c2",report:report}])}
    Production.DomainOSActivity {id:a3;onReported:report=>fixture.activityLog=fixture.activityLog.concat([{owner:"w1",report:report}])}
    Production.DomainOSActivity {id:a4;onReported:report=>fixture.activityLog=fixture.activityLog.concat([{owner:"w2",report:report}])}
    Provider {id:p1;owner:c1;mapName:"jobs"}
    Provider {id:p2;owner:c2;mapName:"jobs"}
    Provider {id:p3;owner:w1;mapName:"pending"}
    Provider {id:p4;owner:w2;mapName:"pending"}
    Production.DomainOSCommands {id:c1;activity:a1;executableSource:p1;onReported:report=>fixture.reportLog=fixture.reportLog.concat([{owner:"c1",report:report}])}
    Production.DomainOSCommands {id:c2;activity:a2;executableSource:p2;onReported:report=>fixture.reportLog=fixture.reportLog.concat([{owner:"c2",report:report}])}
    Production.DomainOSWindowOperations {id:w1;activity:a3;executableSource:p3;onReported:report=>fixture.reportLog=fixture.reportLog.concat([{owner:"w1",report:report}])}
    Production.DomainOSWindowOperations {id:w2;activity:a4;executableSource:p4;onReported:report=>fixture.reportLog=fixture.reportLog.concat([{owner:"w2",report:report}])}
    function controller(name) {return {c1:c1,c2:c2,w1:w1,w2:w2}[name]}
    function provider(name) {return {c1:p1,c2:p2,w1:p3,w2:p4}[name]}
    function activityFor(name) {return {c1:a1,c2:a2,w1:a3,w2:a4}[name]}
    function faults(name,connect,inlineResult,disconnect) {
        const p=provider(name)
        p.throwConnect=connect;p.completeInline=inlineResult;p.throwDisconnect=disconnect
    }
    function launch(name,circular) {
        const c=controller(name)
        const request={action:"private-test-only"}
        if (circular) request.self=request
        lastReturn=name[0]==="c"?c.launch("private-test-only",request):c.launch(request)
    }
    function result(name,source,stdout) {
        lastReturn=controller(name).handleResult(source,{stdout:stdout})
    }
    function invalidData(name,source) {lastReturn=controller(name).handleResult(source,null)}
    function snapshot(name) {
        const c=controller(name),p=provider(name),a=activityFor(name)
        const map=c[name[0]==="c"?"jobs":"pending"]
        lastSnapshot={pendingCount:a.pendingCount,lit:a.lit,mapKeys:Object.keys(map),
            token:a.sequence,lastReport:c.lastReport,connections:p.connections,
            disconnections:p.disconnections,available:name[0]==="c"||c.available,
            reports:reportLog.filter(item=>item.owner===name),
            activityReports:activityLog.filter(item=>item.owner===name)}
    }
}''')
    component.loadUrl(QUrl.fromLocalFile(str(fixture_file)))
    fixture = component.create()
    assert fixture is not None, "\n".join(error.toString() for error in component.errors())

    def variant(value):
        return value.toVariant() if hasattr(value, "toVariant") else value

    def invoke(method, *arguments):
        QMetaObject.invokeMethod(fixture, method, Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", argument) for argument in arguments))
        app.processEvents()
        return variant(fixture.property("lastReturn"))

    def snapshot(name):
        invoke("snapshot", name)
        return variant(fixture.property("lastSnapshot"))

    def valid_result(name, source=None):
        import json
        state = snapshot(name)
        return invoke("result", name, source or state["connections"][-1],
            json.dumps(dict(ok=True, token=state["token"], outcome="known-complete")))

    def settled(name, expected_reports=1, outcome=None):
        state = snapshot(name)
        assert state["pendingCount"] == 0 and not state["lit"], (name, state)
        assert not state["mapKeys"], (name, state)
        assert len(state["reports"]) == len(state["activityReports"]) == expected_reports, (name, state)
        if outcome is not None:
            assert state["lastReport"]["outcome"] == outcome, (name, state)
        return state

    def recovery(name, old_reports):
        invoke("faults", name, False, False, False)
        before = snapshot(name)
        invoke("launch", name, False)
        pending = snapshot(name)
        assert pending["pendingCount"] == 1 and pending["lit"], (name, pending)
        assert len(pending["mapKeys"]) == 1, (name, pending)
        assert len(pending["connections"]) == len(before["connections"]) + 1
        assert valid_result(name)
        return settled(name, old_reports + 1, "known-complete")

    try:
        app.processEvents()
        assert all(snapshot(name)["available"] for name in CONTROLLERS), "Private KWin watcher did not become available"
        if case == "isolation":
            for name in CONTROLLERS:
                invoke("launch", name, False)
            sources = {name:snapshot(name)["connections"][-1] for name in CONTROLLERS}
            assert len(set(sources.values())) == len(CONTROLLERS), "Sources must be unique across instances"
            for name in CONTROLLERS:
                for foreign in CONTROLLERS:
                    if name == foreign:
                        continue
                    assert valid_result(name, sources[foreign]) is False, (name, foreign)
                    state = snapshot(name)
                    assert state["pendingCount"] == 1 and len(state["mapKeys"]) == 1
                    assert not state["reports"] and not state["disconnections"]
            for name in CONTROLLERS:
                assert valid_result(name)
                settled(name, outcome="known-complete")
                recovery(name, 1)
        else:
            for name in CONTROLLERS:
                if case == "serialization":
                    invoke("launch", name, True)
                    state = settled(name, outcome="failed")
                    assert not state["connections"] and not state["disconnections"]
                    assert state["lastReport"]["code"] == ("invalid-command-request" if name[0] == "c" else "invalid-window-request")
                    recovery(name, 1)
                elif case in ("connect", "inline_connect"):
                    invoke("faults", name, True, case == "inline_connect", False)
                    invoke("launch", name, False)
                    state = settled(name, outcome="known-complete" if case == "inline_connect" else "unknown")
                    assert len(state["connections"]) == len(state["disconnections"]) == 1
                    if case == "connect":
                        assert state["lastReport"]["code"] == ("command-connection-unconfirmed" if name[0] == "c" else "window-connection-unconfirmed")
                    else:
                        assert state["lastReport"]["ok"] is True
                    app.processEvents()
                    assert len(snapshot(name)["connections"]) == 1, "Failed connections must not retry"
                    recovery(name, 1)
                elif case == "disconnect":
                    invoke("faults", name, False, False, True)
                    invoke("launch", name, False)
                    assert valid_result(name)
                    state = settled(name, outcome="known-complete")
                    assert state["lastReport"]["ok"] is True and state["lastReport"]["cleanupFailed"] is True
                    assert len(state["connections"]) == len(state["disconnections"]) == 1
                    recovery(name, 1)
                elif case == "malformed":
                    import json
                    # Include an invalid result envelope and invalid success flag.
                    for index, bad in enumerate(("truncated", "null", "token", "ok", "data")):
                        invoke("launch", name, False)
                        current = snapshot(name)
                        source = current["connections"][-1]
                        if bad == "data":
                            assert invoke("invalidData", name, source)
                        else:
                            stdout = {"truncated":'{"ok":true,', "null":"null",
                                "token":json.dumps(dict(ok=True,token="foreign-token")),
                                "ok":json.dumps(dict(ok="true",token=current["token"]))}[bad]
                            assert invoke("result", name, source, stdout)
                        state = settled(name, index * 2 + 1, "unknown")
                        assert state["lastReport"]["code"] == ("invalid-command-result" if name[0] == "c" else "invalid-window-result")
                        assert state["lastReport"]["ok"] is False
                        recovery(name, index * 2 + 1)
                elif case == "duplicates":
                    invoke("launch", name, False)
                    source = snapshot(name)["connections"][-1]
                    assert valid_result(name, source)
                    before = settled(name, outcome="known-complete")
                    for _ in range(10):
                        assert valid_result(name, source) is False
                    assert snapshot(name) == before, "Duplicate results must not disconnect or report again"
                    recovery(name, 1)
                else:
                    raise AssertionError("Unknown job scenario: " + case)
        assert not any("PRIVATE" in message for message in messages), "Exception text must not leak to Qt logs"
        runtime_errors = [message for message in messages if any(marker in message for marker in
            ("ReferenceError:", "TypeError:", "SyntaxError:", "Cannot assign", "Binding loop"))]
        assert not runtime_errors, "Unexpected QML runtime errors: " + "\n".join(runtime_errors)
    finally:
        fixture.deleteLater()
        engine.deleteLater()
        app.processEvents()
        qInstallMessageHandler(old_handler)
        bus.unregisterService("org.kde.KWin")


class JobFailure(unittest.TestCase):
    def run_case(self, case):
        with tempfile.TemporaryDirectory(prefix=".qa-domainos-jobs-", dir=ROOT) as temporary:
            private = Path(temporary)
            env = dict(os.environ)
            for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
                directory = private / key.lower()
                directory.mkdir(mode=0o700)
                env[key] = str(directory)
            for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_SESSION_BUS_PID",
                        "DBUS_SESSION_BUS_WINDOWID", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH"):
                env.pop(key, None)
            env.update(QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic",
                QML_DISABLE_DISK_CACHE="1", XDG_CURRENT_DESKTOP="NONE",
                DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(private / "disabled-system-bus"),
                DOMAINOS_PRIVATE_JOB_TEST="1")
            # Keep even the bus socket out of /tmp and omit service activation
            # directories: constructing KDE watchers cannot launch other apps.
            config = private / "private-bus.conf"
            config.write_text('''<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
"http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig><type>session</type><listen>unix:path=''' + str(private / "bus.socket") + '''</listen>
<auth>EXTERNAL</auth><policy context="default"><allow own="*"/>
<allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>''')
            try:
                process = subprocess.Popen(["dbus-run-session", "--config-file", str(config), "--", sys.executable, "-B",
                    str(Path(__file__).resolve()), "--worker", case], env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
                stdout, stderr = process.communicate(timeout=20)
            except subprocess.TimeoutExpired as error:
                # Stop both the private bus and its QML worker, even if a future
                # synchronous JavaScript regression blocks the worker loop.
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
                self.fail("QML job scenario exceeded 20 seconds; private worker stopped: " + str(error))
            self.assertEqual(process.returncode, 0, case + ":\n" + stdout + stderr)

    def test_circular_serialization_releases_activity_without_submit(self):
        self.run_case("serialization")

    def test_connect_failure_has_one_unknown_report_and_no_retry(self):
        self.run_case("connect")

    def test_connect_throw_after_synchronous_result_keeps_one_known_report(self):
        self.run_case("inline_connect")

    def test_disconnect_failure_keeps_known_result_and_releases_pending(self):
        self.run_case("disconnect")

    def test_invalid_result_variants_release_pending_and_allow_recovery(self):
        self.run_case("malformed")

    def test_duplicate_data_does_not_repeat_report_or_cleanup(self):
        self.run_case("duplicates")

    def test_simultaneous_controller_instances_do_not_consume_foreign_responses(self):
        self.run_case("isolation")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        run_worker(sys.argv[2])
    else:
        unittest.main()
