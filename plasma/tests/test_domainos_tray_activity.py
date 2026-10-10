#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise production Tray presentations and the actual Activity/Panel bridge.

The native tray provider is an owned GridView/state double. No personal Plasma,
SNI service, notification payload, command, application or account is accessed.
Actual Popup.Window open/close and the production activity frame receipt run in
an owned Xvfb/D-Bus namespace; input is QTest, not a physical compositor claim.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"
FIXTURE = Path(__file__).with_name("domainos-tray-activity-fixture.qml")


def worker(output):
    if os.environ.get("DOMAINOS_TRAY_ACTIVITY_PRIVATE") != "1":
        raise RuntimeError("Use the private launcher")
    from PyQt6 import sip
    from PyQt6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, Qt, QUrl
    from PyQt6.QtQml import QQmlApplicationEngine, QQmlProperty
    from PyQt6.QtQuick import QQuickItem, QQuickWindow
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication

    app = QApplication([])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.load(QUrl.fromLocalFile(str(FIXTURE)))
    assert engine.rootObjects(), "\n".join(warnings)
    host = sip.cast(engine.rootObjects()[0], QQuickWindow)
    panel, tracker = host.property("panel"), host.property("activity")
    # Disable unrelated tasks/pager before assigning the fixture integration.
    # The actual tray loader, plate/lens and frame bridge remain production.
    for obj in panel.findChildren(QObject):
        if obj.inherits("QQuickLoader") and obj.property("x") in (672, 1266):
            QQmlProperty(obj, "active", engine).write(False)

    def invoke(method, *args):
        assert QMetaObject.invokeMethod(host, method, Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", arg) for arg in args)) is not False

    def value(v):
        return v.toVariant() if hasattr(v, "toVariant") else v

    def settle(predicate=lambda: True, timeout=3):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            app.processEvents()
            if predicate():
                return True
            QTest.qWait(5)
        return False

    invoke("attach")
    assert settle(lambda: host.property("tray") is not None)
    tray = host.property("tray")
    state = host.property("nativeState")
    assert settle(lambda: len(value(tray.property("visibleEntries"))) == 7)
    checks, snapshots = {}, {}

    def snapshot(name):
        result = {k: value(tracker.property(k)) for k in (
            "sequence", "pendingCount", "lit", "tailLit", "presentationPending", "displayLit", "lastReport")}
        result.update(reports=len(value(host.property("reports"))), lastResult=value(host.property("lastResult")))
        snapshots[name] = result
        return result

    def popup_open(kind):
        name = "domainosTray" + kind + "Popup"
        obj = tray.findChild(QObject, name)
        return bool(obj and obj.property("visible"))

    def request(action, expected=True):
        sequence, reports = tracker.property("sequence"), len(value(host.property("reports")))
        invoke("invokeAction", action)
        s = snapshot(action + "_" + str(sequence + 1))
        label = {"overflow": "tray-overflow", "status": "tray-status", "notifications": "tray-notifications",
                 "false": "owned-rejected-view", "throw": "owned-throwing-view"}[action]
        checks[f"{action}_{sequence + 1}_one_begin_one_finish"] = s["sequence"] == sequence + 1 and s["reports"] == reports + 1
        checks[f"{action}_{sequence + 1}_result_and_pending"] = s["lastResult"] is expected and s["pendingCount"] == 0 \
            and s["lastReport"]["ok"] is expected and s["lastReport"]["action"] == label \
            and s["lastReport"]["outcome"] == ("presentation-requested" if expected else "failed")
        return s

    checks["panel_binds_the_actual_tracker"] = tray.property("activity") == tracker
    checks["owned_provider_adopted_and_exact_geometry"] = len(value(tray.property("entries"))) == 8 \
        and tray.property("width") == 326 and tray.property("height") == 150
    blink = tracker.findChild(QObject, "domainosBusyBlink")
    checks["default_tail_off_and_blink_idle"] = not tracker.property("keepLightAfterCompletion") \
        and blink is not None and not blink.property("running")
    overflow = request("overflow")
    checks["overflow_opens_with_presentation_receipt_not_fake_pending"] = popup_open("Overflow") \
        and overflow["presentationPending"] and not overflow["lit"] and not overflow["tailLit"]
    assert settle(lambda: not tracker.property("displayLit"))
    request("overflow")
    checks["same_overflow_request_closes"] = not popup_open("Overflow")
    assert settle(lambda: not tracker.property("displayLit"))
    request("status")
    checks["status_opens"] = popup_open("Status") and not popup_open("Overflow")
    assert settle(lambda: not tracker.property("displayLit"))
    request("status")
    checks["same_status_request_closes"] = not popup_open("Status")
    assert settle(lambda: not tracker.property("displayLit"))

    # Exercise the actual PanelButton pointer path twice. Its original toggle
    # captures press state while the native popup dismisses before release.
    button = sip.cast(tray.findChild(QObject, "domainosTrayExpand"), QQuickItem)
    point = button.mapToItem(host.contentItem(), QPointF(button.width() / 2, button.height() / 2)).toPoint()
    seq = tracker.property("sequence")
    QTest.mouseClick(host, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
    assert settle(lambda: popup_open("Status"))
    QTest.mouseClick(host, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
    checks["same_status_button_pointer_closes_without_reopening"] = settle(lambda: not popup_open("Status")) \
        and tracker.property("sequence") == seq + 2
    assert settle(lambda: not tracker.property("displayLit"))

    request("status")
    request("notifications")
    checks["native_notification_request_observed_before_dispatch"] = state.property("calls") == 1 \
        and state.property("pendingAtRequest") == 1 and state.property("lastApplet") is not None and not popup_open("Status")
    checks["no_notification_execution_completion_claim"] = "no application completion" in value(tracker.property("lastReport"))["detail"]
    state.setProperty("expanded", False)
    assert settle(lambda: not tracker.property("displayLit"))

    sequence, reports = tracker.property("sequence"), len(value(host.property("reports")))
    invoke("setAvailable", False)
    for action in ("overflow", "status", "notifications"):
        invoke("invokeAction", action)
        checks[f"unavailable_{action}_returns_false_without_false_activity"] = value(host.property("lastResult")) is False \
            and tracker.property("sequence") == sequence and len(value(host.property("reports"))) == reports
    invoke("setAvailable", True)
    assert settle(lambda: tray.property("available") and len(value(tray.property("visibleEntries"))) == 7)
    request("false", False)
    request("throw", False)
    checks["thrown_request_reports_safe_failure_and_releases"] = value(host.property("failures"))[-1] \
        == "The requested tray view could not be shown" and tracker.property("pendingCount") == 0
    state.setProperty("failRequest", True)
    request("notifications", False)
    checks["provider_exception_never_escapes_or_makes_success"] = state.property("calls") == 1 \
        and state.property("pendingAtRequest") == 1 and "Sensitive" not in " ".join(value(host.property("failures")))
    state.setProperty("failRequest", False)
    request("notifications")
    checks["next_valid_request_recovers_once"] = state.property("calls") == 2 and tracker.property("pendingCount") == 0
    state.setProperty("expanded", False)
    assert settle(lambda: not tracker.property("displayLit"))

    tracker.setProperty("keepLightAfterCompletion", True)
    tracker.setProperty("extraLightMilliseconds", 100)
    start = time.monotonic()
    tail = request("status")
    checks["optional_tail_keeps_only_light_without_delaying_request"] = time.monotonic() - start < .1 \
        and tail["tailLit"] and tail["pendingCount"] == 0 and popup_open("Status")
    checks["optional_tail_uses_existing_timer_and_ends"] = settle(lambda: not tracker.property("displayLit"))
    tracker.setProperty("keepLightAfterCompletion", False)
    request("status")
    assert settle(lambda: not tracker.property("displayLit"))

    invoke("setTracked", False)
    sequence, reports = tracker.property("sequence"), len(value(host.property("reports")))
    invoke("invokeAction", "overflow")
    checks["optional_tracker_absence_preserves_presentation"] = value(host.property("lastResult")) is True \
        and popup_open("Overflow") and tracker.property("sequence") == sequence and len(value(host.property("reports"))) == reports
    invoke("invokeAction", "overflow")
    checks["optional_tracker_absence_preserves_toggle"] = not popup_open("Overflow")
    invoke("setTracked", True)
    request("status")
    request("status")
    assert settle(lambda: not tracker.property("displayLit"))
    baseline_frames = [0]
    host.frameSwapped.connect(lambda: baseline_frames.__setitem__(0, baseline_frames[0] + 1))
    QTest.qWait(350)
    checks["no_idle_frame_loop_or_running_busy_blink"] = baseline_frames[0] <= 1 \
        and not blink.property("running")
    errors = [w for w in warnings if any(key in w for key in (
        "Error:", "Binding loop", "Cannot assign", "Unable to assign", "is not a function", "Cannot read"))]
    checks["qml_errors_zero"] = not errors
    result = {"status": "passed" if all(checks.values()) else "failed", "checks": checks,
        "snapshots": snapshots, "qml_errors": errors, "warnings": warnings,
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (UI / "DomainOSTray.qml", UI / "DomainOSPanel.qml", UI / "DomainOSActivity.qml", FIXTURE)},
        "scope": __doc__}
    report = output / "RESULTADO.json"
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n"); report.chmod(0o600)
    host.close(); app.processEvents()
    failed = [k for k, v in checks.items() if not v]
    print(json.dumps({"passed": len(checks) - len(failed), "total": len(checks), "failed": failed}))
    return bool(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args.output)
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError("Use a new private output directory")
    output.mkdir(mode=0o700)
    with tempfile.TemporaryDirectory(prefix=".qa-tray-activity-", dir=ROOT) as temporary:
        env = dict(os.environ)
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
            path = Path(temporary) / key.lower(); path.mkdir(mode=0o700); env[key] = str(path)
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "DBUS_SESSION_BUS_ADDRESS"):
            env.pop(key, None)
        env.update(DOMAINOS_TRAY_ACTIVITY_PRIVATE="1", QT_QPA_PLATFORM="xcb", QT_QUICK_BACKEND="software",
            QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic", QML_DISABLE_DISK_CACHE="1",
            PYTHONDONTWRITEBYTECODE="1", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(Path(temporary) / "disabled-system"))
        run = subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1200x900x24", "dbus-run-session", "--",
            sys.executable, str(Path(__file__).resolve()), "--worker", "--output", str(output)],
            env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=25)
        log = output / "HOST.log"; log.write_text(run.stdout); log.chmod(0o600)
        summaries = [line for line in run.stdout.splitlines() if line.startswith('{"passed":')]
        print("\n".join(summaries) if summaries else run.stdout[-5000:])
        return run.returncode


if __name__ == "__main__":
    sys.exit(main())
