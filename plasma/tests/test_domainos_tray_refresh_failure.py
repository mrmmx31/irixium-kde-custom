#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inject failures at the real Tray adapter's provider/configuration boundaries.

Production QML runs offscreen with owned provider doubles and private HOME/XDG.
The fixture catches explicit-call errors for inspection; native signal-handler
errors remain observable through the QML diagnostics. No SNI/backend, application,
real session, account or preference is accessed. No native action is submitted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"

QML = r'''
import QtQuick
import QtQuick.Layouts
import "%UI%" as Production
Item {
    id: fixture
    width: 326; height: 150
    property alias tray: tray
    property alias config: configuration
    property alias visibleView: visibleView
    property alias hiddenView: hiddenView
    property string fault: ""
    property string caught: ""
    property int setterAttempts: 0
    property int writeAttempts: 0
    property int writeCommits: 0
    property bool reenterRefresh: false
    property bool reenterVisibility: false
    property var settingShown: []
    property var settingHidden: []
    property var settingsMap: null
    function makeSettings() {
        const map = {}
        Object.defineProperty(map, "trayVisibleItems", {
            get: function() { return fixture.settingShown },
            set: function(value) {
                ++fixture.setterAttempts
                if (fixture.fault === "setting-shown") throw new Error("OWNED shown setter failure")
                fixture.settingShown = Array.from(value)
            }
        })
        Object.defineProperty(map, "trayHiddenItems", {
            get: function() { return fixture.settingHidden },
            set: function(value) {
                ++fixture.setterAttempts
                if (fixture.fault === "setting-hidden") throw new Error("OWNED hidden setter failure")
                fixture.settingHidden = Array.from(value)
            }
        })
        return map
    }
    function initialize() {
        settingsMap = makeSettings()
        tray.settings = settingsMap
        tray.nativeTray = provider
        tray.attach()
    }
    function call(method) {
        caught = ""
        try {
            if (method === "refresh") tray.refresh()
            else if (method === "visibility") tray.applyVisibility()
            else if (method === "attach") tray.attach()
        } catch (error) { caught = String(error) }
    }
    function prepareWrite() {
        tray.visibilityInitialized = false
        settingsMap.trayVisibleItems = ["desired-shown"]
        settingsMap.trayHiddenItems = ["desired-hidden"]
        tray.visibilityInitialized = true
    }
    function changePolicyAgain() {
        tray.visibilityInitialized = false
        settingsMap.trayVisibleItems = ["next-shown"]
        settingsMap.trayHiddenItems = ["next-hidden"]
        tray.visibilityInitialized = true
    }
    function prepareInitial(which) {
        tray.visibilityInitialized = false
        settingsMap.trayVisibleItems = []
        settingsMap.trayHiddenItems = []
        configuration.shownItems = which === "shown" ? ["native-shown"] : []
        configuration.hiddenItems = which === "hidden" ? ["native-hidden"] : []
    }
    function nativeChange(which, value) {
        if (which === "shown") {
            configuration.shownItems = [value]
            configuration.valueChanged("shownItems", [value])
        } else {
            configuration.hiddenItems = [value]
            configuration.valueChanged("hiddenItems", [value])
        }
    }
    Production.DomainOSTray { id: tray; width: 326; height: 150 }
    Item {
        id: provider
        property alias visibleLayout: visibleView
        property alias hiddenLayout: hiddenView
        property QtObject plasmoid: QtObject { property QtObject configuration: configuration }
        property QtObject systemTrayState: QtObject { property bool expanded: false }
        Item {
            id: visibleView
            width: 100; height: 100
            property int count: 1
            property int cellWidth: 50
            property int cellHeight: 48
            property int cacheBuffer: 0
            property int forceCalls: 0
            property alias contentItem: visibleContents
            property QtObject model: QtObject {
                signal rowsInserted(); signal rowsRemoved(); signal dataChanged()
                signal layoutChanged(); signal modelReset()
            }
            function forceLayout() {
                ++forceCalls
                if (fixture.reenterRefresh) tray.refresh()
                if (fixture.fault === "force") throw new Error("OWNED forceLayout failure")
            }
            function itemAtIndex(index) {
                if (fixture.fault === "item") throw new Error("OWNED itemAtIndex failure")
                return index === 0 ? loader : null
            }
            Item { id: visibleContents }
            Item {
                id: loader
                property int status: 1
                property alias item: entry
                Item {
                    id: entry
                    property string itemId: "owned-item"
                    property string text: "Owned provider"
                    property int status: 1
                    property bool active: true
                    property var model: ({itemType: "StatusNotifier"})
                    property alias iconContainer: icon
                    Item { id: icon; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                }
            }
        }
        Item {
            id: hiddenView
            width: 100; height: 100
            property int count: 0
            property int cellWidth: 50
            property int cellHeight: 48
            property int cacheBuffer: 0
            property int forceCalls: 0
            property alias contentItem: hiddenContents
            property QtObject model: QtObject {
                signal rowsInserted(); signal rowsRemoved(); signal dataChanged()
                signal layoutChanged(); signal modelReset()
            }
            function forceLayout() { ++forceCalls }
            function itemAtIndex(index) { return null }
            Item { id: hiddenContents }
        }
    }
    QtObject {
        id: configuration
        property var shownItems: []
        property var hiddenItems: []
        signal valueChanged(string key, var value)
        function writeConfig() {
            ++fixture.writeAttempts
            if (fixture.reenterVisibility) tray.applyVisibility()
            if (fixture.fault === "write") throw new Error("OWNED writeConfig failure")
            ++fixture.writeCommits
        }
    }
}
'''


def worker(output):
    if os.environ.get("DOMAINOS_TRAY_REFRESH_PRIVATE") != "1":
        raise RuntimeError("Use the private launcher")
    from PyQt6.QtCore import Q_ARG, QMetaObject, Qt, QUrl, qInstallMessageHandler
    from PyQt6.QtQml import QQmlComponent, QQmlEngine
    from PyQt6.QtQuick import QQuickItem  # Registers the public QQuickItem wrappers.
    from PyQt6.QtWidgets import QApplication

    app = QApplication([])
    diagnostics = []
    previous = qInstallMessageHandler(lambda kind, context, message: diagnostics.append(message))
    checks, snapshots = {}, {}
    engines = []

    def value(v):
        return v.toVariant() if hasattr(v, "toVariant") else v

    def invoke(host, method, *args):
        QMetaObject.invokeMethod(host, method, Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", arg) for arg in args))

    def fresh():
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(QML.replace("%UI%", UI.as_uri()).encode(), QUrl("file:///owned-tray-guard.qml"))
        if component.isError():
            raise AssertionError("\n".join(e.toString() for e in component.errors()))
        host = component.create()
        if not host:
            raise AssertionError("\n".join(e.toString() for e in component.errors()))
        engines.append((engine, component, host))
        invoke(host, "initialize")
        for _ in range(5): app.processEvents()
        return host, host.property("tray"), host.property("config"), host.property("visibleView")

    def snap(host, tray, config, view):
        return {"refreshing": tray.property("refreshing"),
            "synchronizingVisibility": tray.property("synchronizingVisibility"),
            "initialized": tray.property("visibilityInitialized"),
            "caught": host.property("caught"), "forceCalls": view.property("forceCalls"),
            "writeAttempts": host.property("writeAttempts"), "writeCommits": host.property("writeCommits"),
            "settingShown": value(host.property("settingShown")),
            "settingHidden": value(host.property("settingHidden")),
            "shownItems": value(config.property("shownItems")),
            "hiddenItems": value(config.property("hiddenItems")),
            "entries": [entry["id"] for entry in value(tray.property("entries"))]}

    for fault in ("force", "item"):
        host, tray, config, view = fresh()
        original = snap(host, tray, config, view)
        host.setProperty("fault", fault)
        invoke(host, "call", "refresh")
        failed = snap(host, tray, config, view)
        checks[f"refresh_{fault}_exception_observable"] = "OWNED" in failed["caught"]
        checks[f"refresh_{fault}_guard_released_and_snapshot_retained"] = not failed["refreshing"] and failed["entries"] == original["entries"]
        for _ in range(3): app.processEvents()
        checks[f"refresh_{fault}_no_immediate_retry"] = view.property("forceCalls") == failed["forceCalls"]
        host.setProperty("fault", "")
        invoke(host, "call", "refresh")
        recovered = snap(host, tray, config, view)
        checks[f"refresh_{fault}_next_call_recovers_once"] = recovered["caught"] == "" \
            and not recovered["refreshing"] and recovered["forceCalls"] == failed["forceCalls"] + 1 \
            and recovered["entries"] == ["owned-item"]
        snapshots[f"refresh_{fault}"] = {"before": original, "failed": failed, "recovered": recovered}

    host, tray, config, view = fresh()
    invoke(host, "prepareWrite")
    host.setProperty("fault", "write")
    invoke(host, "call", "visibility")
    failed = snap(host, tray, config, view)
    checks["write_exception_observable_and_guard_released"] = "OWNED writeConfig" in failed["caught"] \
        and not failed["synchronizingVisibility"] and failed["writeAttempts"] == 1 and failed["writeCommits"] == 0
    for _ in range(3): app.processEvents()
    checks["failed_write_not_implicitly_retried"] = host.property("writeAttempts") == 1
    host.setProperty("fault", "")
    invoke(host, "changePolicyAgain")
    invoke(host, "call", "visibility")
    recovered = snap(host, tray, config, view)
    checks["next_explicit_policy_change_commits_once_after_failed_write"] = recovered["caught"] == "" \
        and not recovered["synchronizingVisibility"] and recovered["writeAttempts"] == 2 \
        and recovered["writeCommits"] == 1 and recovered["shownItems"] == ["next-shown"] \
        and recovered["hiddenItems"] == ["next-hidden"]
    snapshots["write"] = {"failed": failed, "recovered": recovered,
        "limit": "Failed writeConfig may leave changed in-memory values; finally is not transactional rollback or automatic retry."}

    for which in ("shown", "hidden"):
        host, tray, config, view = fresh()
        invoke(host, "prepareInitial", which)
        host.setProperty("fault", "setting-" + which)
        invoke(host, "call", "attach")
        failed = snap(host, tray, config, view)
        checks[f"attach_{which}_exception_observable"] = f"OWNED {which} setter" in failed["caught"]
        checks[f"attach_{which}_guard_released_initialization_uncommitted"] = not failed["synchronizingVisibility"] \
            and not failed["initialized"]
        host.setProperty("fault", "")
        invoke(host, "call", "attach")
        recovered = snap(host, tray, config, view)
        checks[f"attach_{which}_next_call_recovers_native_policy"] = recovered["caught"] == "" \
            and not recovered["synchronizingVisibility"] and recovered["initialized"] \
            and recovered["settingShown" if which == "shown" else "settingHidden"] == ["native-" + which]
        snapshots["attach_" + which] = {"failed": failed, "recovered": recovered}

    for which in ("shown", "hidden"):
        host, tray, config, view = fresh()
        host.setProperty("fault", "setting-" + which)
        count = len(diagnostics)
        invoke(host, "nativeChange", which, "external-first")
        failed = snap(host, tray, config, view)
        checks[f"native_{which}_setter_exception_observable"] = any(
            f"OWNED {which} setter" in message for message in diagnostics[count:])
        checks[f"native_{which}_guard_released_after_signal_exception"] = not failed["synchronizingVisibility"]
        host.setProperty("fault", "")
        invoke(host, "nativeChange", which, "external-next")
        recovered = snap(host, tray, config, view)
        checks[f"native_{which}_next_signal_recovers_without_native_write"] = not recovered["synchronizingVisibility"] \
            and recovered["settingShown" if which == "shown" else "settingHidden"] == ["external-next"] \
            and recovered["writeAttempts"] == 0
        snapshots["native_" + which] = {"failed": failed, "recovered": recovered}

    host, tray, config, view = fresh()
    before = view.property("forceCalls")
    host.setProperty("reenterRefresh", True)
    invoke(host, "call", "refresh")
    checks["refresh_reentrancy_ignored_until_outer_finally"] = view.property("forceCalls") == before + 1 \
        and not tray.property("refreshing") and host.property("caught") == ""
    invoke(host, "prepareWrite")
    host.setProperty("reenterVisibility", True)
    invoke(host, "call", "visibility")
    checks["visibility_reentrancy_ignored_until_outer_finally"] = host.property("writeAttempts") == 1 \
        and host.property("writeCommits") == 1 and not tray.property("synchronizingVisibility")

    # Signal-handler failures are expected and deliberately kept, not hidden.
    unexpected = [message for message in diagnostics if "OWNED" not in message and any(
        word in message for word in ("Error:", "Binding loop", "Cannot assign", "Unable to assign", "Cannot read", "is not a function"))]
    checks["no_unexpected_qml_errors"] = not unexpected
    result = {"status": "passed" if all(checks.values()) else "failed", "checks": checks,
        "snapshots": snapshots, "qml_diagnostics": diagnostics, "unexpected_diagnostics": unexpected,
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (UI / "DomainOSTray.qml", Path(__file__).resolve())}, "scope": __doc__}
    if output:
        output.mkdir(mode=0o700, parents=True, exist_ok=False)
        report = output / "RESULTADO.json"
        report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        report.chmod(0o600)
    qInstallMessageHandler(previous)
    print(json.dumps(result))
    return 0 if result["status"] == "passed" else 1


def run_private(output=None):
    with tempfile.TemporaryDirectory(prefix=".qa-tray-refresh-", dir=ROOT) as temporary:
        env = dict(os.environ)
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
            path = Path(temporary) / key.lower(); path.mkdir(mode=0o700); env[key] = str(path)
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "LD_PRELOAD", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "QT_STYLE_OVERRIDE"):
            env.pop(key, None)
        env.update(DOMAINOS_TRAY_REFRESH_PRIVATE="1", QT_QPA_PLATFORM="offscreen",
            QT_QUICK_BACKEND="software", QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic",
            QML_DISABLE_DISK_CACHE="1", PYTHONDONTWRITEBYTECODE="1",
            XDG_CONFIG_DIRS="/etc/xdg", XDG_DATA_DIRS="/usr/local/share:/usr/share",
            DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(Path(temporary) / "no-session-bus"),
            DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(Path(temporary) / "no-system-bus"))
        command = [sys.executable, str(Path(__file__).resolve()), "--worker"]
        if output: command.extend(["--output", str(output)])
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=20)
        lines = [line for line in run.stdout.splitlines() if line.startswith('{"status":')]
        if not lines: raise AssertionError(run.stderr[-5000:] + run.stdout[-5000:])
        return run, json.loads(lines[-1])


class TrayRefreshFailure(unittest.TestCase):
    def test_guards_release_after_injected_boundary_errors(self):
        run, result = run_private()
        self.assertEqual(run.returncode, 0, result)
        self.assertTrue(all(result["checks"].values()), result)


if __name__ == "__main__":
    if "--worker" in sys.argv or "--output" in sys.argv:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--output", type=Path)
        parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
        args = parser.parse_args()
        if args.worker: sys.exit(worker(args.output))
        run, result = run_private(args.output)
        print(json.dumps({"status": result["status"], "passed": sum(result["checks"].values()),
            "total": len(result["checks"]), "failed": [k for k, v in result["checks"].items() if not v]}))
        sys.exit(run.returncode)
    unittest.main()
