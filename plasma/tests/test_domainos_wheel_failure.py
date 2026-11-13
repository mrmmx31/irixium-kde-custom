#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bound malformed wheel inputs in the production Iconbox, with worker timeouts.

The native action double records requests; this is not a compositor test.
Every case runs in a separate Qt process so a synchronous QML loop cannot hang
the test runner. Configuration, cache and temporary files stay in the worker's
private directory in the repository, never in another user's profile.
"""
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "plasma/tests/DomainOSIconboxPreview.qml"


def run_worker(case):
    # Qt must see the isolated environment before importing/creating Qt objects.
    from PyQt6.QtCore import Q_ARG, QMetaObject, QUrl, Qt
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtWidgets import QApplication

    app = QApplication([sys.argv[0]])
    engine = QQmlApplicationEngine()
    diagnostics = []
    engine.warnings.connect(lambda messages: diagnostics.extend(message.toString() for message in messages))
    engine.load(QUrl.fromLocalFile(str(FIXTURE)))
    assert engine.rootObjects(), "Production Iconbox fixture failed to load: " + "\n".join(diagnostics)
    window = engine.rootObjects()[0]
    box = window.property("iconbox")

    def invoke(obj, method, *args):
        QMetaObject.invokeMethod(obj, method, Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", argument) for argument in args))
        app.processEvents()

    def requests():
        value = window.property("requests")
        return value.toVariant() if hasattr(value, "toVariant") else value

    def wheel(angle):
        invoke(box, "wheelEvent", angle, None)

    invoke(window, "seedMany")
    for identity in range(18, 31):
        invoke(window, "addWindow", identity, "private.wheel." + str(identity))
    app.processEvents()
    assert box.property("pageCount") >= 3, "Fixture must exercise more than two pages"
    assert not box.property("iconboxWheelActivates"), "Default wheel must only scroll"
    last_page = (box.property("pageCount") - 1) * box.property("visibleCapacity")

    try:
        if case == "fractional":
            wheel(-60)
            assert box.property("firstVisible") == 0
            assert box.property("wheelRotation") == -7.5
            wheel(-60)
            assert box.property("firstVisible") == 7
            assert box.property("wheelRotation") == 0
            wheel(60)
            assert box.property("firstVisible") == 7
            wheel(60)
            assert box.property("firstVisible") == 0
            assert not requests(), "Scrolling must not activate a window"

        elif case == "nonfinite":
            box.setProperty("firstVisible", 7)
            box.setProperty("wheelRotation", 5)
            for angle in (math.inf, -math.inf, math.nan):
                wheel(angle)
                assert box.property("firstVisible") == 7
                assert box.property("wheelRotation") == 5
                assert not requests(), "A nonfinite input must not request an action"

        elif case == "huge_scroll":
            # Repeated subtraction of 15 stops making progress at these finite
            # magnitudes. The parent process timeout catches that regression.
            box.setProperty("firstVisible", 7)
            wheel(sys.float_info.max)
            assert box.property("firstVisible") == 0
            assert math.isfinite(box.property("wheelRotation"))
            wheel(-sys.float_info.max)
            assert box.property("firstVisible") == last_page
            assert math.isfinite(box.property("wheelRotation"))
            assert not requests(), "Huge default wheel events must remain scroll-only"

        elif case == "huge_activation":
            box.setProperty("iconboxWheelActivates", True)
            for angle in (sys.float_info.max, -sys.float_info.max):
                before = len(requests())
                wheel(angle)
                current = requests()
                assert len(current) - before == 1, "One event must emit exactly one activation"
                assert current[-1]["action"] == "activate"
                assert len(current[-1]["ids"]) == 1
                assert 0 <= box.property("firstVisible") <= last_page

        elif case == "corrupt_remainder":
            box.setProperty("firstVisible", 7)
            box.setProperty("wheelRotation", math.nan)
            wheel(120)
            assert box.property("firstVisible") == 0
            assert math.isfinite(box.property("wheelRotation"))
            assert not requests()

        else:
            raise AssertionError("Unknown private test scenario: " + case)
        assert not diagnostics, "Unexpected QML diagnostics: " + "\n".join(diagnostics)
    finally:
        window.close()
        engine.deleteLater()
        app.processEvents()


class WheelFailure(unittest.TestCase):
    def run_case(self, case):
        with tempfile.TemporaryDirectory(prefix=".qa-domainos-wheel-", dir=ROOT) as temporary:
            private = Path(temporary)
            env = dict(os.environ)
            for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
                        "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
                folder = private / key.lower()
                folder.mkdir(mode=0o700)
                env[key] = str(folder)
            for key in ("DISPLAY", "WAYLAND_DISPLAY", "LD_PRELOAD", "QT_STYLE_OVERRIDE",
                        "QML_IMPORT_PATH", "QML2_IMPORT_PATH"):
                env.pop(key, None)
            env.update(QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic",
                QT_SCALE_FACTOR="1", QML_DISABLE_DISK_CACHE="1", XDG_CURRENT_DESKTOP="NONE",
                DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(private / "disabled-bus"),
                DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(private / "disabled-system-bus"))
            try:
                completed = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                    "--worker", case], env=env, capture_output=True, text=True, timeout=15)
            except subprocess.TimeoutExpired as error:
                self.fail("Production wheel handler did not finish within 15 seconds in " + case
                    + "; private worker was stopped. " + str(error))
            self.assertEqual(completed.returncode, 0,
                "Private scenario " + case + " failed:\n" + completed.stdout + completed.stderr)

    def test_fractional_default_scroll_accumulates_without_activation(self):
        self.run_case("fractional")

    def test_infinity_and_nan_are_ignored(self):
        self.run_case("nonfinite")

    def test_largest_finite_events_finish_at_bounded_pages(self):
        self.run_case("huge_scroll")

    def test_optional_activation_makes_one_request_per_large_event(self):
        self.run_case("huge_activation")

    def test_invalid_internal_remainder_recovers_without_activation(self):
        self.run_case("corrupt_remainder")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        run_worker(sys.argv[2])
    else:
        unittest.main()
