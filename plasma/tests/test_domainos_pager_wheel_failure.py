#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bound wheel inputs in production Pager against a private KWin/X11.

Every case owns an Xvfb display, a D-Bus session and a compositor. Real native
desktop models confirm navigation versus activation; no user's desktop is
contacted. An external process-group timeout also detects synchronous QML loops.
Profiles, caches and temporary files remain in the repository-local fixture.
"""
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "plasma/tests/DomainOSPagerPreview.qml"


def run_worker(case):
    if os.environ.get("DOMAINOS_PRIVATE_PAGER_WHEEL") != "1":
        raise RuntimeError("Use the private test launcher")
    from PyQt6.QtCore import Q_ARG, QMetaObject, QPointF, QPoint, QUrl, Qt, qInstallMessageHandler
    from PyQt6.QtGui import QWheelEvent
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtQuick import QQuickItem
    from PyQt6.QtWidgets import QApplication

    app = QApplication([sys.argv[0]])
    messages = []
    qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    log = (Path(os.environ["TMPDIR"]) / "private-kwin.log").open("w")
    compositor = subprocess.Popen(["kwin_x11", "--replace"], stdout=log, stderr=subprocess.STDOUT)
    engine = None
    window = None

    def settle(predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            app.processEvents()
            if predicate():
                return True
            time.sleep(.01)
        return False

    def native_current():
        return subprocess.check_output(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager",
            "org.freedesktop.DBus.Properties.Get", "org.kde.KWin.VirtualDesktopManager", "current"],
            text=True, stderr=subprocess.DEVNULL, timeout=2).strip()

    try:
        def ready():
            return subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2).returncode == 0
        assert settle(ready), "Private KWin did not start"
        engine = QQmlApplicationEngine()
        engine.load(QUrl.fromLocalFile(str(FIXTURE)))
        assert engine.rootObjects(), "Production Pager preview did not load"
        window = engine.rootObjects()[0]
        pager = window.findChild(QQuickItem, "domainosRealPager")
        assert pager is not None and settle(lambda: pager.property("available")), "Native Pager unavailable"
        count = int(os.environ["DOMAINOS_PAGER_DESKTOPS"])
        assert pager.property("desktopCount") == count, "Private native desktop count differs"
        requests = []
        completions = []
        pager.operationStarted.connect(lambda operation: requests.append(operation))
        pager.operationFinished.connect(lambda operation, success, detail: completions.append((operation, success)))

        def invoke(method, *arguments):
            QMetaObject.invokeMethod(pager, method, Qt.ConnectionType.DirectConnection,
                *(Q_ARG("QVariant", argument) for argument in arguments))
            app.processEvents()

        def rows():
            return pager.property("desktopRecords").toVariant()

        def wheel(angle):
            invoke("wheelEvent", angle)

        def remainder(value):
            assert math.isfinite(pager.property("wheelRemainder")), "Remainder became nonfinite"
            assert abs(pager.property("wheelRemainder")) < 120, "Remainder left one-detent interval"
            assert pager.property("wheelRemainder") == value

        def activate(position):
            identity = rows()[position]["id"]
            invoke("activateDesktop", identity)
            assert settle(lambda: pager.property("currentDesktopId") == identity
                and pager.property("pendingActivations") == 0), "Private activation did not finish"
            assert native_current() == identity
            requests.clear()
            completions.clear()
            pager.setProperty("wheelRemainder", 0)
            return identity

        before = native_current()
        if case == "fractional":
            assert not pager.property("wheelActivatesDesktop"), "Default changed to activation"
            for delta, page, rest in ((-60,0,-60),(-60,1,0),(60,1,60),(60,0,0)):
                wheel(delta)
                assert pager.property("firstVisible") == page
                remainder(rest)
            for _ in range(5):
                wheel(-20)
                assert pager.property("firstVisible") == 0
            wheel(-20)
            assert pager.property("firstVisible") == 1
            remainder(0)
            wheel(-29.5)
            wheel(29.5)
            remainder(0)
            wheel(-240)
            assert pager.property("firstVisible") == 3, "Two detents must navigate two cards"
            wheel(360)
            assert pager.property("firstVisible") == 0
            wheel(120)
            assert pager.property("firstVisible") == 0, "Previous boundary must clamp"
            wheel(-120 * count)
            assert pager.property("firstVisible") == count - 2, "Next boundary must clamp"
            assert not requests
            assert native_current() == before, "Default wheel changed the native desktop"

        elif case == "nonfinite":
            pager.setProperty("firstVisible", 3)
            pager.setProperty("wheelRemainder", 37.5)
            for angle in (math.inf, -math.inf, math.nan):
                wheel(angle)
                assert pager.property("firstVisible") == 3
                remainder(37.5)
            assert not requests and native_current() == before

        elif case == "huge_scroll":
            for angle, page in ((2147483647,0),(-2147483647,count-2),
                                (sys.float_info.max,0),(-sys.float_info.max,count-2)):
                wheel(angle)
                assert pager.property("firstVisible") == page
                assert math.isfinite(pager.property("wheelRemainder"))
                assert abs(pager.property("wheelRemainder")) < 120
            assert not requests and native_current() == before

        elif case == "normal_activation":
            activate(3)
            pager.setProperty("wheelActivatesDesktop", True)
            for angle, position in ((-60,3),(-60,4),(240,2),(-240,4),(120,3)):
                prior = len(requests)
                prior_page = pager.property("firstVisible")
                wheel(angle)
                identity = rows()[position]["id"]
                assert settle(lambda: pager.property("pendingActivations") == 0
                    and pager.property("currentDesktopId") == identity)
                assert native_current() == identity
                assert len(requests) - prior <= 1, "One event queued repeated activations"
                assert pager.property("firstVisible") == (prior_page if angle == -60 and prior == 0
                    and not requests else min(position,count-2))
            assert completions and all(success for _,success in completions)

        elif case == "huge_activation":
            pager.setProperty("wheelActivatesDesktop", True)
            for angle, position in ((2147483647,0),(-2147483647,count-1),
                                    (sys.float_info.max,0),(-sys.float_info.max,count-1)):
                activate(3)
                wheel(angle)
                identity = rows()[position]["id"]
                assert settle(lambda: pager.property("pendingActivations") == 0
                    and pager.property("currentDesktopId") == identity)
                assert requests == ["activate-desktop"], "One large event must submit exactly one request"
                assert native_current() == identity
                assert completions == [("activate-desktop",True)]
                assert 0 <= pager.property("firstVisible") <= count-2
                assert math.isfinite(pager.property("wheelRemainder"))
                wheel(angle)
                assert requests == ["activate-desktop"], "Clamped current target must not dispatch again"

        elif case == "corrupt_remainder":
            pager.setProperty("firstVisible", 3)
            for invalid in (math.nan, math.inf, -math.inf):
                pager.setProperty("wheelRemainder", invalid)
                wheel(120)
                remainder(0)
            assert pager.property("firstVisible") == 0 and not requests
            pager.setProperty("wheelRemainder", sys.float_info.max)
            wheel(sys.float_info.max)
            assert pager.property("firstVisible") == 0, "Overflow total must be ignored"
            assert pager.property("wheelRemainder") == sys.float_info.max
            pager.setProperty("wheelRemainder", 0)
            wheel(-120)
            assert pager.property("firstVisible") == 1, "Valid input must recover after invalid input"
            assert native_current() == before

        elif case == "stale_current":
            pager.setProperty("wheelActivatesDesktop", True)
            pager.setProperty("currentDesktopId", "PRIVATE-MISSING-DESKTOP")
            wheel(-sys.float_info.max)
            assert not requests, "Missing identity must not dispatch"
            assert pager.property("firstVisible") == 0 and native_current() == before
            pager.setProperty("currentDesktopId", before)
            wheel(-120)
            assert settle(lambda: pager.property("pendingActivations") == 0)
            assert len(requests) == 1, "Valid identity must recover"

        elif case in ("one_desktop", "two_desktops"):
            for angle in (-120,120,-sys.float_info.max,sys.float_info.max):
                wheel(angle)
                assert pager.property("firstVisible") == 0
            assert not requests and native_current() == before

        elif case == "physical":
            # Dispatch through the actual onWheel MouseArea, including its
            # horizontal fallback; controller calls alone cannot prove routing.
            for delta, page in ((QPoint(0,-120),1),(QPoint(-120,0),2),(QPoint(0,240),0)):
                point = pager.mapToScene(QPointF(pager.width()/2,pager.height()/2))
                event = QWheelEvent(point,point,QPoint(),delta,Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False)
                QApplication.sendEvent(window,event)
                app.processEvents()
                assert event.isAccepted() and pager.property("firstVisible") == page
            assert not requests and native_current() == before
        else:
            raise AssertionError("Unknown private scenario: " + case)

        fatal = [message for message in messages if re.search(
            r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable",message)]
        assert not fatal, "QML errors: " + "\n".join(fatal)
        print(json.dumps({"case":case,"status":"passed","real_native_desktop_count":count,
            "requests":len(requests),"qml_errors":0}))
    finally:
        if window is not None:
            window.close()
        if engine is not None:
            engine.deleteLater()
        app.processEvents()
        compositor.terminate()
        try:
            compositor.wait(3)
        except subprocess.TimeoutExpired:
            compositor.kill()
            compositor.wait(3)
        log.close()


class PagerWheelFailure(unittest.TestCase):
    def run_case(self, case, desktop_count=8):
        with tempfile.TemporaryDirectory(prefix=".qa-pager-wheel-",dir=ROOT) as temporary:
            private = Path(temporary)
            env = dict(os.environ)
            for key in ("XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME",
                        "XDG_STATE_HOME","XDG_RUNTIME_DIR","TMPDIR"):
                folder = private / key.lower()
                folder.mkdir(mode=0o700)
                env[key] = str(folder)
            # Qt/KConfig must use these explicit directories, not the inherited
            # personal profile or other applications' override settings.
            for key in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS",
                        "DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","SESSION_MANAGER",
                        "LD_PRELOAD","QT_STYLE_OVERRIDE","QT_QPA_PLATFORMTHEME",
                        "QML_IMPORT_PATH","QML2_IMPORT_PATH","XAUTHORITY"):
                env.pop(key,None)
            env.update(QT_QPA_PLATFORM="xcb",QT_QUICK_BACKEND="software",
                QT_QUICK_CONTROLS_STYLE="Basic",QT_SCALE_FACTOR="1",QML_DISABLE_DISK_CACHE="1",
                XDG_CURRENT_DESKTOP="NONE",KWIN_COMPOSE="N",LIBGL_ALWAYS_SOFTWARE="1",
                DOMAINOS_PRIVATE_PAGER_WHEEL="1",DOMAINOS_PAGER_DESKTOPS=str(desktop_count),
                DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(private / "disabled-system-bus"))
            config = Path(env["XDG_CONFIG_HOME"])
            (config / "kwinrc").write_text("[Desktops]\nNumber="+str(desktop_count)+
                "\nRows=1\n[Compositing]\nEnabled=false\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
            (config / "kdeglobals").write_text((ROOT / "colors/DomainOS-SR10.4.colors").read_text())
            bus = private / "private-bus.conf"
            bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen>'
                '<auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/>'
                '<allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
            command = ["xvfb-run","--auto-servernum","--server-args=-screen 0 1200x700x24",
                "dbus-run-session","--config-file",str(bus),"--",sys.executable,"-B",
                str(Path(__file__).resolve()),"--worker",case]
            process = subprocess.Popen(command,env=env,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True,start_new_session=True)
            try:
                stdout,stderr = process.communicate(timeout=25)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                stdout,stderr = process.communicate(timeout=5)
                self.fail("Private Pager worker exceeded 25 seconds: "+case+"\n"+stdout+stderr)
            self.assertEqual(process.returncode,0,case+" failed:\n"+stdout+stderr)
            self.assertIn('"status": "passed"',stdout)

    def test_fractional_trackpad_and_normal_navigation(self):
        self.run_case("fractional")

    def test_nonfinite_input_preserves_state(self):
        self.run_case("nonfinite")

    def test_extreme_events_scroll_without_activation(self):
        self.run_case("huge_scroll")

    def test_optional_activation_uses_final_target_once(self):
        self.run_case("normal_activation")

    def test_extreme_activation_is_single_and_bounded(self):
        self.run_case("huge_activation")

    def test_corrupt_accumulator_and_overflow_recover(self):
        self.run_case("corrupt_remainder")

    def test_stale_current_identity_has_no_request_then_recovers(self):
        self.run_case("stale_current")

    def test_one_desktop_cannot_scroll(self):
        self.run_case("one_desktop",1)

    def test_two_desktops_do_not_scroll_cards(self):
        self.run_case("two_desktops",2)

    def test_real_mouse_area_routes_vertical_and_horizontal_wheel(self):
        self.run_case("physical")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        run_worker(sys.argv[2])
    else:
        unittest.main()
