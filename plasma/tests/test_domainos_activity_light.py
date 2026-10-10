#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Paint the production activity lens in owned Qt/D-Bus/Xvfb namespaces.

The actual panel lens and QQuickWindow frame signals are used. The panel's three
unrelated native task/pager/tray loaders are disabled before attaching Runtime;
this is a lens/controller proof, not a full-panel or personal-session claim.
The terminal command launches only a short marker program created by this test.
Only the explicit contrast-policy phase injects a QtObject of palette roles.
That phase proves the production policy and rendered result, not a native KDE
color-scheme change; the real PlasmaCore.Theme object is restored afterwards.
Threaded Xvfb uses Qt's elapsed-time animation driver because the virtual
display has no physical VSync. Wall-clock observations therefore do not prove
the cadence of a personal desktop's hardware VSync driver.
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


def worker(output):
    if os.environ.get("DOMAINOS_ACTIVITY_LIGHT_PRIVATE") != "1":
        raise RuntimeError("Use the private launcher")
    from PyQt6 import sip
    from PyQt6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QSize, Qt, QUrl
    from PyQt6.QtGui import QColor
    from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
    from PyQt6.QtQuick import QQuickItem, QQuickWindow
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication

    app = QApplication([])
    # The real Calendar heading needs only the read-only applet form factor in
    # a plain engine. This supplies no configuration, actions or session service.
    context = Path(os.environ["TMPDIR"]) / "PrivatePlasmoidContext.qml"
    context.write_text("pragma Singleton\nimport QtQuick\nimport org.kde.plasma.core as PC\nQtObject {readonly property int formFactor:PC.Types.Planar}\n")
    qmlRegisterSingletonType(QUrl.fromLocalFile(str(context)), "org.kde.plasma.plasmoid", 1, 0, "Plasmoid")
    engine = QQmlApplicationEngine()
    messages = []
    engine.warnings.connect(lambda errors: messages.extend(error.toString() for error in errors))
    fixture = Path(os.environ["TMPDIR"]) / "activity-light.qml"
    fixture.write_text('''import QtQuick
import "''' + UI.as_uri() + '''" as Production
import org.kde.taskmanager as TaskManager
Window {
    id:host; width:971; height:109; visible:true
    property alias panel: panel
    property alias runtime: runtime
    property alias activity: runtime.activity
    property var lastToken: 0
    property var reportLog: []
    property QtObject savedNativeRoles: null
    property var savedStartupModel: null
    property var transientStartupModel: null
    readonly property bool palettePolicyActive: panel.colorPalette.system === policyRoles
    QtObject {
        id:policyRoles
        property color window:"#c1c1c1"
        property color windowText:"#102b37"
        property color base:"#9ebfbf"
        property color text:"#102b37"
        property color button:"#c1c1c1"
        property color buttonText:"#07141b"
        property color highlight:"#78a0a0"
        property color highlightedText:"#ffffff"
        property color disabledText:"#607f91"
    }
    Production.DomainOSPanel {id:panel;anchors.fill:parent}
    QtObject {
        id:startupFixture
        property int count: 0
        property var rows: []
        property bool broken: false
        signal dataChanged()
        signal modelReset()
        function makeModelIndex(row) { return row }
        function data(row,role) {
            if (broken) throw new Error("owned unavailable model")
            return role === TaskManager.AbstractTasksModel.IsStartup ? rows[row] : undefined
        }
    }
    Component {
        id:startupFactory
        QtObject {
            property int count: 1
            function makeModelIndex(row) { return row }
            function data(row,role) { return role === TaskManager.AbstractTasksModel.IsStartup ? true : undefined }
        }
    }
    Production.DomainOSRuntime {id:runtime;hostItem:null;screenGeometry:Qt.rect(0,0,1200,900);
        colorPalette:panel.colorPalette;instanceId:"owned-activity-light-test";
        settings:({tasksOnlyCurrentDesktop:false,tasksOnlyCurrentActivity:false})}
    Connections {target:runtime.activity;function onReported(report){host.reportLog=host.reportLog.concat([report])}}
    function attach() {panel.integration=runtime}
    function begin(label) {lastToken=runtime.activity.begin(label)}
    function finish(token) {runtime.activity.finish(token,{ok:true,outcome:"test-observed-result"})}
    function instant() {const t=runtime.activity.begin("synchronous-test");runtime.activity.finish(t,{ok:true,outcome:"request-accepted"})}
    function staleAck(token) {runtime.activity.acknowledgePresentation(token)}
    function clock() {runtime.dispatch("clock",panel)}
    function launch(command) {runtime.commands.settings={terminalCommand:command};runtime.commands.openTerminal()}
    function mockPalettePolicy(surface,base,selection) {
        if (savedNativeRoles === null) savedNativeRoles=panel.colorPalette.system
        policyRoles.window=surface;policyRoles.button=surface
        policyRoles.base=base;policyRoles.highlight=selection
        panel.colorPalette.system=policyRoles
    }
    function restoreNativeRoles() {panel.colorPalette.system=savedNativeRoles}
    function startupRows(rows) {
        if (savedStartupModel === null) savedStartupModel=runtime.activity.startupModel
        startupFixture.broken=false;startupFixture.rows=rows;startupFixture.count=rows.length
        runtime.activity.startupModel=startupFixture;startupFixture.dataChanged()
    }
    function breakStartupModel() {startupFixture.broken=true;startupFixture.modelReset()}
    function detachStartupModel() {runtime.activity.startupModel=null}
    function restoreStartupModel() {runtime.activity.startupModel=savedStartupModel}
    function createTransientStartup() {
        transientStartupModel=startupFactory.createObject(host)
        runtime.activity.startupModel=transientStartupModel
    }
    function destroyTransientStartup() {transientStartupModel.destroy();transientStartupModel=null}
}''')
    engine.load(QUrl.fromLocalFile(str(fixture)))
    assert engine.rootObjects(), "\n".join(messages)
    window = sip.cast(engine.rootObjects()[0], QQuickWindow)
    panel = window.property("panel")
    runtime = window.property("runtime")
    activity = window.property("activity")
    # The reference panel initially has no integration. Disable only its three
    # native loaders, preserving the actual rendered lens and its frame bridge.
    for item in panel.findChildren(QObject):
        if item.metaObject().className().startswith("QQuickLoader"):
            item.setProperty("active", False)
    checks, snapshots = {}, {}
    frame_count = [0]
    window.frameSwapped.connect(lambda: frame_count.__setitem__(0, frame_count[0] + 1))

    def invoke(method, *args):
        QMetaObject.invokeMethod(window, method, Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", arg) for arg in args))

    def settle_until(predicate, timeout=3):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            app.processEvents()
            if predicate():
                return True
            QTest.qWait(5)
        return False

    def variant(value):
        return value.toVariant() if hasattr(value, "toVariant") else value

    def state():
        return {name: variant(activity.property(name)) for name in (
            "sequence", "pendingCount", "lit", "tailLit", "presentationPending", "displayLit", "lastReport")}

    def capture(name):
        result = window.contentItem().grabToImage(QSize(971, 109))
        assert result is not None
        done = [False]
        result.ready.connect(lambda: done.__setitem__(0, True))
        assert settle_until(lambda: done[0]), "Qt did not complete the owned scene capture"
        image = result.image()
        assert not image.isNull()
        path = output / (name + ".png")
        assert image.save(str(path))
        path.chmod(0o600)
        # Exact center of the existing 13x7 inner lens, canonical panel at 50%.
        return image.pixelColor(935, 89).name()

    invoke("attach")
    assert settle_until(lambda: frame_count[0] > 0)
    graphics_api = window.rendererInterface().graphicsApi().name
    checks["requested_graphics_backend_is_active"] = graphics_api == (
        "Software" if os.environ.get("QT_QUICK_BACKEND") == "software" else "OpenGL")
    lamp = panel.findChild(QObject, "domainosActivityLamp")
    assert lamp is not None
    colors = panel.property("colorPalette")
    blink=activity.findChild(QObject,"domainosBusyBlink")
    checks["default_tail_off_and_blink_only_while_pending"] = not activity.property("keepLightAfterCompletion") \
        and blink is not None and not blink.property("running")
    checks["native_half_cycle_interval_is_500ms"] = blink is not None and blink.property("interval") == 500
    checks["lamp_matches_approved_inner_face"] = all(lamp.property(k) == v for k, v in (
        ("x", 6), ("y", 8), ("width", 26), ("height", 14)))
    off_color = capture("LENS-OFF")

    # Begin/finish in one GUI turn: no pending work is fabricated. A real scene
    # grab requested in that turn records the yellow presented by the renderer.
    invoke("instant")
    snapshots["synchronous_before_paint"] = state()
    checks["synchronous_result_immediate_no_fake_pending"] = activity.property("pendingCount") == 0 \
        and not activity.property("lit") and activity.property("presentationPending") and activity.property("displayLit")
    instant_color = capture("LENS-SYNCHRONOUS-REQUEST")
    checks["synchronous_request_painted_yellow"] = instant_color == colors.property("activityLight").name() \
        and instant_color != off_color
    checks["frame_ack_extinguishes_without_tail"] = settle_until(lambda: not activity.property("displayLit"))
    snapshots["synchronous_after_paint"] = state()

    # Two observable operations: a frame receipt does not end either operation.
    invoke("begin", "own-operation-one"); one = activity.property("sequence")
    invoke("begin", "own-operation-two"); two = activity.property("sequence")
    invoke("staleAck", one)
    checks["old_frame_receipt_cannot_clear_new_request"] = activity.property("presentationPending")
    checks["pending_operations_survive_presentation_ack"] = settle_until(lambda: not activity.property("presentationPending")) \
        and activity.property("pendingCount") == 2 and activity.property("lit")
    invoke("finish", one)
    checks["one_result_does_not_end_other_operation"] = activity.property("pendingCount") == 1 and activity.property("displayLit")
    invoke("finish", two)
    checks["last_result_extinguishes_observed_operation"] = activity.property("pendingCount") == 0 and not activity.property("displayLit")
    blink_start = time.monotonic()
    invoke("begin", "observable-pending-work")
    blinking_token=activity.property("sequence")
    assert settle_until(lambda: not activity.property("presentationPending"))
    checks["pending_work_initially_illuminates_lens"] = capture("LENS-BLINK-ON") == colors.property("activityLight").name()
    checks["native_half_cycle_extinguishes_lens_without_finishing_work"] = settle_until(lambda: not activity.property("displayLit"),.8) \
        and activity.property("pendingCount") == 1 and activity.property("lit")
    blink_off = time.monotonic()
    checks["pending_off_frame_retains_opaque_original_bezel"] = capture("LENS-BLINK-OFF") == off_color
    checks["next_half_cycle_illuminates_same_pending_operation"] = settle_until(lambda: activity.property("displayLit"),.8) \
        and activity.property("pendingCount") == 1
    blink_again = time.monotonic()
    snapshots["native_blink_timing_ms"] = {"first_half_cycle": round((blink_off-blink_start)*1000, 1),
        "second_half_cycle": round((blink_again-blink_off)*1000, 1)}
    checks["observed_half_cycles_match_500ms_with_scheduler_tolerance"] = all(
        .4 <= interval <= .8 for interval in (blink_off-blink_start, blink_again-blink_off))
    invoke("finish",blinking_token)
    checks["completion_stops_blink_without_delaying_result"] = not blink.property("running") \
        and not activity.property("displayLit") and activity.property("pendingCount") == 0

    # Explicit model double exercises provider lifetime/failure boundaries; it
    # does not claim that a KDE startup or a client window was created here.
    invoke("startupRows", [True, False, True])
    assert settle_until(lambda: activity.property("startupCount") == 2)
    checks["startup_records_are_separate_from_command_tokens"] = activity.property("pendingCount") == 0 \
        and activity.property("busyCount") == 2 and activity.property("busy")
    QTest.mouseMove(window, QPoint(384, 92))
    app.processEvents()
    checks["wait_cursor_precedes_child_mouseareas_without_stealing_clicks"] = window.cursor().shape() == Qt.CursorShape.WaitCursor
    assert settle_until(lambda: not activity.property("presentationPending"))
    checks["startup_pending_blinks_without_fake_command_report"] = settle_until(lambda: not activity.property("displayLit"), .8) \
        and activity.property("startupCount") == 2
    tracker_reports = len(variant(window.property("reportLog")))
    activity.setProperty("keepLightAfterCompletion", True)
    activity.setProperty("extraLightMilliseconds", 150)
    invoke("instant")
    checks["completed_request_cannot_mask_other_startup_blink_with_tail"] = not activity.property("tailLit") \
        and activity.property("startupCount") == 2 and activity.property("pendingCount") == 0
    invoke("startupRows", [False])
    assert settle_until(lambda: activity.property("startupCount") == 0)
    checks["last_startup_removal_begins_only_optional_light_tail"] = activity.property("tailLit") \
        and not activity.property("busy") and len(variant(window.property("reportLog"))) == tracker_reports + 1
    app.processEvents()
    checks["optional_tail_does_not_keep_wait_cursor"] = window.cursor().shape() != Qt.CursorShape.WaitCursor
    assert settle_until(lambda: not activity.property("displayLit"))
    activity.setProperty("keepLightAfterCompletion", False)
    invoke("startupRows", [True])
    assert settle_until(lambda: activity.property("startupCount") == 1)
    invoke("breakStartupModel")
    checks["unavailable_startup_model_releases_busy_and_records_failure"] = settle_until(
        lambda: activity.property("startupCount") == 0 and activity.property("startupObservationFailures") > 0)
    invoke("startupRows", [True])
    assert settle_until(lambda: activity.property("startupCount") == 1)
    invoke("detachStartupModel")
    checks["model_detach_cannot_strand_cursor_or_light"] = settle_until(lambda: not activity.property("busy"))
    invoke("createTransientStartup")
    assert settle_until(lambda: activity.property("startupCount") == 1)
    invoke("destroyTransientStartup")
    checks["provider_destruction_cannot_strand_wait"] = settle_until(lambda: not activity.property("busy"))
    invoke("restoreStartupModel")
    assert settle_until(lambda: activity.property("startupCount") == 0)

    # The approved yellow stays stable in ordinary light/dark schemes; only a
    # collision with the lens or metal surround changes its yellow lightness.
    # QApplication.setPalette does not drive PlasmaCore.Theme's KColorScheme
    # roles. Explicitly inject the policy's supported role object only here;
    # actual KDE scheme propagation is covered by separate native tests.
    palettes = (
        ("LIGHT", "#c1c1c1", "#9ebfbf", "#78a0a0"),
        ("DARK", "#282828", "#1a1a1a", "#5d90bb"),
        ("YELLOW", "#dddd28", "#e1df72", "#dddd28"),
    )
    for name, surface, base, selection in palettes:
        invoke("mockPalettePolicy", surface, base, selection)
        app.processEvents()
        invoke("begin", "owned-palette-test")
        token = activity.property("sequence")
        color = capture("LENS-" + name)
        tone = colors.property("activityLight")
        protected = colors.property("activityContrastProtected")
        snapshot = {"tone": tone.name(), "protected": protected, "role_injection": True,
            "native_kde_colorscheme_change": False, "inputs": {"window": surface, "base": base, "highlight": selection},
            "lens": colors.property("lens").name(), "metal": colors.property("metalLight").name(), "pixel": color}
        def contrast(a, b):
            def luminance(c):
                rgb = (c.redF(), c.greenF(), c.blueF())
                return sum(w * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
                    for w, v in zip((.2126, .7152, .0722), rgb))
            lo, hi = sorted((luminance(a), luminance(b)))
            return (hi + .05) / (lo + .05)
        snapshot["lens_contrast"] = contrast(tone, colors.property("lens"))
        snapshot["metal_contrast"] = contrast(tone, colors.property("metalLight"))
        snapshots[name] = snapshot
        checks[name.lower() + "_actual_lens_pixels_match_role"] = color == tone.name()
        checks[name.lower() + "_explicit_policy_roles_reach_production_palette"] = window.property("palettePolicyActive") \
            and colors.property("system").property("window").name() == surface \
            and colors.property("system").property("base").name() == base \
            and colors.property("system").property("highlight").name() == selection
        checks[name.lower() + "_yellow_policy"] = (not protected and tone.name() == "#dddd28") if name != "YELLOW" \
            else protected and min(snapshot["lens_contrast"], snapshot["metal_contrast"]) >= 3 \
                and abs(tone.hslHueF() - QColor("#dddd28").hslHueF()) < .002
        invoke("finish", token)

    invoke("restoreNativeRoles")
    app.processEvents()
    checks["policy_fixture_restores_native_roles_before_runtime_dispatch"] = not window.property("palettePolicyActive") \
        and colors.property("system") is not None \
        and colors.property("system").metaObject().className().startswith("DomainOSKDEPalette")

    activity.setProperty("keepLightAfterCompletion", True)
    activity.setProperty("extraLightMilliseconds", 150)
    start = time.monotonic(); invoke("instant")
    checks["optional_tail_never_delays_result"] = time.monotonic() - start < .1 \
        and activity.property("pendingCount") == 0 and activity.property("tailLit")
    checks["optional_tail_ends_with_existing_single_shot"] = settle_until(lambda: not activity.property("displayLit"))
    activity.setProperty("keepLightAfterCompletion", False)

    # Actual Runtime dispatch opens/toggles the native clock popup; it is a view
    # request, not an application lifetime or work remaining after acceptance.
    invoke("clock")
    snapshots["clock_open"] = state()
    checks["clock_request_observed_without_command_or_fake_execution"] = runtime.property("instruments").property("clockPopupVisible") \
        and activity.property("pendingCount") == 0 and not activity.property("lit") \
        and activity.property("presentationPending") and state()["lastReport"]["outcome"] == "presentation-requested"
    assert settle_until(lambda: not activity.property("displayLit"))
    invoke("clock")
    checks["same_clock_button_still_closes_popup"] = not runtime.property("instruments").property("clockPopupVisible")
    assert settle_until(lambda: not activity.property("displayLit"))

    # Real executable DataSource/helper in a deliberate no-KIO environment.
    # A bare QQuickWindow is not a complete KDE launcher session. The startup
    # path is covered separately with real delayed windows in a full session;
    # this non-GUI marker verifies the honest fallback outcome and frame gate.
    marker = Path(os.environ["TMPDIR"]) / "own-program-marker.json"
    program = Path(os.environ["TMPDIR"]) / "own-program.py"
    program.write_text("import json,os\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").write_text(json.dumps({'pid':os.getpid(),'home':os.environ['HOME']}))\n")
    import shlex
    private_bin = Path(os.environ["TMPDIR"]) / "no-kio-bin"
    private_bin.mkdir(mode=0o700)
    (private_bin / "python3").symlink_to(sys.executable)
    original_path = os.environ.get("PATH")
    try:
        os.environ["PATH"] = str(private_bin)
        invoke("launch", shlex.join([sys.executable, str(program)]))
        snapshots["native_launch_immediate"] = state()
        checks["real_helper_request_lights_pending_operation"] = activity.property("pendingCount") == 1 and activity.property("displayLit")
        assert settle_until(lambda: marker.exists() and activity.property("pendingCount") == 0, 8)
    finally:
        if original_path is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = original_path
    observed = json.loads(marker.read_text())
    report = state()["lastReport"]
    snapshots["native_launch_result"] = state()
    checks["real_owned_launch_result_and_namespace_match"] = report.get("ok") is True \
        and report.get("outcome") == "process-started" \
        and report.get("startupNotificationRequested") is False \
        and report.get("pid") == observed["pid"] \
        and observed["home"] == os.environ["HOME"]
    checks["real_result_releases_pending_without_claiming_process_completion"] = not activity.property("lit") \
        and "completion" in report.get("detail", "")
    assert settle_until(lambda: not activity.property("displayLit"))
    baseline_frames = frame_count[0]
    QTest.qWait(400)
    checks["no_idle_activity_frame_loop"] = frame_count[0] - baseline_frames <= 1
    errors = [message for message in messages if any(word in message for word in (
        "Error:", "Binding loop", "Cannot assign", "Unable to assign", "is not a function", "Cannot read"))]
    checks["no_qml_runtime_errors"] = not errors
    hashes = {name: hashlib.sha256((UI / name).read_bytes()).hexdigest() for name in (
        "DomainOSActivity.qml", "DomainOSRuntime.qml", "DomainOSPanel.qml", "PanelButton.qml", "DomainOSPalette.qml", "DomainOSKDEPalette.qml")}
    result = {"checks": checks, "snapshots": snapshots, "qml_errors": errors, "source_sha256": hashes,
        "render_loop": os.environ.get("QSG_RENDER_LOOP", "default"),
        "scene_graph_backend": os.environ.get("QT_QUICK_BACKEND", "default"),
        "actual_graphics_api": graphics_api,
        "animation_driver": "elapsed-time for private Xvfb" if os.environ.get("QSG_USE_SIMPLE_ANIMATION_DRIVER") == "1" else "backend default",
        "scope": "Owned QQuickWindow scene captures/frameSwapped, actual Runtime clock popup and Commands DataSource/helper with private marker program. Its PATH contains only the real Python executable: this explicitly verifies the no-KIO Popen fallback; the marker is not a native window-map/startup-lifetime proof. Startup-role lifecycle uses an explicit model double in the focused phases. Real KIO startup is covered by the separate full-session delayed-window assay. Only LIGHT/DARK/YELLOW contrast-policy phases inject a supported QtObject of roles; they are not native KDE color-scheme transitions, and native roles are restored before Runtime dispatch. Unrelated task/pager/tray loaders disabled; no full-panel, personal session, CPU benchmark, physical input or application-completion claim."}
    path = output / "RESULTADO.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n"); path.chmod(0o600)
    window.close(); app.processEvents()
    failed = [name for name, good in checks.items() if not good]
    print(json.dumps({"passed": len(checks) - len(failed), "total": len(checks), "failed": failed}))
    return bool(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--threaded", action="store_true", help="Use Qt's OpenGL threaded renderer with elapsed-time animation under Xvfb")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args.output)
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError("Use a new private output directory")
    output.mkdir(mode=0o700)
    with tempfile.TemporaryDirectory(prefix=".qa-activity-light-", dir=ROOT) as temporary:
        env = dict(os.environ)
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
            path = Path(temporary) / key.lower(); path.mkdir(mode=0o700); env[key] = str(path)
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "DBUS_SESSION_BUS_ADDRESS"):
            env.pop(key, None)
        env.update(DOMAINOS_ACTIVITY_LIGHT_PRIVATE="1", QT_QPA_PLATFORM="xcb", QT_QUICK_BACKEND="software",
            QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic", QML_DISABLE_DISK_CACHE="1",
            PYTHONDONTWRITEBYTECODE="1", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(Path(temporary) / "disabled-system"))
        if args.threaded:
            env.pop("QT_QUICK_BACKEND", None)
            # The standard threaded driver advances by VSync ticks. Xvfb/GLX
            # has no physical VSync, so use Qt's supported QElapsedTimer driver
            # for this owned elapsed-time proof, retaining the threaded renderer.
            # Qt 6.8.2: https://github.com/qt/qtdeclarative/blob/v6.8.2/src/quick/scenegraph/qsgcontext.cpp
            env.update(QSG_RENDER_LOOP="threaded", QSG_RHI_BACKEND="opengl", LIBGL_ALWAYS_SOFTWARE="1",
                QSG_USE_SIMPLE_ANIMATION_DRIVER="1")
        # D-Bus activated owned services inherit the private X display, rather
        # than repeatedly failing to start after activation with no DISPLAY.
        run = subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1200x900x24", "dbus-run-session", "--",
            sys.executable, str(Path(__file__).resolve()), "--worker", "--output", str(output)],
            env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=35)
        log = output / "HOST.log"; log.write_text(run.stdout); log.chmod(0o600)
        summaries = [line for line in run.stdout.splitlines() if line.startswith('{"passed":')]
        print("\n".join(summaries) if summaries else run.stdout[-5000:])
        return run.returncode


if __name__ == "__main__":
    sys.exit(main())
