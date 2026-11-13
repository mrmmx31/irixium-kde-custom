#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify production palette calibration in an owned offscreen Qt/D-Bus profile.

The supported QtObject of KDE roles is explicitly injected. These checks prove
the QML color policy and SVG regeneration, not native KDE scheme propagation,
the appearance of a personal panel, or a complete Plasma session.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"
PREFIX = "data:image/svg+xml;charset=utf-8,"
CORALREEF = ("#78a0d5", "#6688b5", "#3297c7", "#ffffff", "#ffffff")
GRAY = ("#b8b8b8", "#858585", "#747474", "#171717", "#ffffff")
DARK = ("#282828", "#171717", "#5d90bb", "#f0f0f0", "#ffffff")
YELLOW = ("#dddd28", "#e1df72", "#dddd28", "#171717", "#171717")
# Independent measurements from the running SR10.4 VUE CoralReef colormap.
# These are numeric observations, not copies of HP artwork or font files.
NATIVE_TONES = {
    "dark": "#194b63", "shadow": "#3e536e", "highlight": "#c5e8e6",
    "pale": "#a3d0e6", "metalLight": "#c4d5ed", "metalDark": "#3e536e",
    "cyan": "#7acac5", "cyanShadow": "#406b68", "lens": "#78a0d5",
}
COLOR_ROLES = (
    "background", "recessed", "text", "black", "blue", "white", "dark",
    "shadow", "highlight", "pale", "metalLight", "metalDark", "cyan",
    "cyanShadow", "label", "lens", "focus", "green", "greenDark",
    "pagerLight", "pagerPressedLight", "activityLight",
)


class DomainOSPalettePolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("DOMAINOS_PALETTE_PRIVATE") != "1":
            raise unittest.SkipTest("Run this file's launcher for an owned Qt/D-Bus profile")
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from PyQt6.QtCore import QUrl
        from PyQt6.QtQml import QQmlApplicationEngine
        self.messages = []
        self.engine = QQmlApplicationEngine()
        self.engine.warnings.connect(
            lambda errors: self.messages.extend(error.toString() for error in errors))
        self.fixture = Path(os.environ["TMPDIR"]) / "palette-policy.qml"
        self.fixture.write_text('''import QtQuick
import "''' + UI.as_uri() + '''" as Production
QtObject {
    id:host
    property QtObject roles:QtObject {
        property color window:"#78a0d5"
        property color windowText:"#ffffff"
        property color base:"#6688b5"
        property color text:"#ffffff"
        property color button:"#78a0d5"
        property color buttonText:"#ffffff"
        property color highlight:"#3297c7"
        property color highlightedText:"#ffffff"
        property color disabledText:"#6688b5"
    }
    property QtObject palette:Production.DomainOSPalette {system:host.roles}
    function apply(surface,base,selection,foreground,selectedText) {
        roles.window=surface;roles.button=surface;roles.base=base
        roles.highlight=selection;roles.windowText=foreground
        roles.text=foreground;roles.buttonText=foreground
        roles.highlightedText=selectedText
    }
}''')
        self.engine.load(QUrl.fromLocalFile(str(self.fixture)))
        self.assertTrue(self.engine.rootObjects(), "\n".join(self.messages))
        self.host = self.engine.rootObjects()[0]
        self.palette = self.host.property("palette")

    def tearDown(self):
        self.assertFalse(self.messages, "\n".join(self.messages))
        self.engine.deleteLater()
        self.app.processEvents()

    def apply(self, values):
        from PyQt6.QtCore import Q_ARG, QMetaObject, Qt
        QMetaObject.invokeMethod(self.host, "apply", Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", value) for value in values))
        self.app.processEvents()

    def color(self, role):
        return self.palette.property(role)

    def snapshot(self):
        return {role: self.color(role).name() for role in COLOR_ROLES}

    def assets(self):
        urls = self.palette.property("assetUrls")
        return urls.toVariant() if hasattr(urls, "toVariant") else urls

    @staticmethod
    def contrast(first, second):
        def luminance(color):
            values = (color.redF(), color.greenF(), color.blueF())
            return sum(weight * (value / 12.92 if value <= .04045
                else ((value + .055) / 1.055) ** 2.4)
                for weight, value in zip((.2126, .7152, .0722), values))
        low, high = sorted((luminance(first), luminance(second)))
        return (high + .05) / (low + .05)

    def test_coralreef_reproduces_nine_measured_native_tones(self):
        self.apply(CORALREEF)
        self.assertEqual({role: self.color(role).name() for role in NATIVE_TONES},
            NATIVE_TONES)
        self.assertEqual(self.color("background").name(), "#78a0d5")
        self.assertEqual(self.color("blue").name(), "#3297c7")
        self.assertFalse(self.palette.property("pagerContrastProtected"))
        self.assertEqual(self.color("pagerLight").name(), "#dddd28")

    def test_gray_scheme_does_not_retain_blue_artwork_tones(self):
        self.apply(GRAY)
        for role in set(COLOR_ROLES) - {"pagerLight", "pagerPressedLight", "activityLight"}:
            with self.subTest(role=role):
                color = self.color(role)
                self.assertEqual(color.red(), color.green())
                self.assertEqual(color.green(), color.blue())
        # The only intentionally colored indicators are the approved yellow ones.
        self.assertEqual(self.color("pagerLight").name(), "#dddd28")
        self.assertEqual(self.color("activityLight").name(), "#dddd28")

    def test_live_gray_dark_yellow_changes_regenerate_valid_svg_without_resizing(self):
        from PyQt6.QtCore import QByteArray
        from PyQt6.QtSvg import QSvgRenderer
        previous = None
        sizes = {}
        for values in (GRAY, DARK, YELLOW, CORALREEF):
            self.apply(values)
            current = self.assets()
            self.assertGreaterEqual(len(current), 12)
            if previous is not None:
                self.assertEqual(set(current), set(previous))
                for name in ("applications.svg", "clock-face.svg", "indicator-lens.svg"):
                    with self.subTest(scheme=values, asset=name):
                        self.assertNotEqual(current[name], previous[name])
            for name, url in current.items():
                with self.subTest(scheme=values, asset=name):
                    self.assertTrue(url.startswith(PREFIX))
                    renderer = QSvgRenderer(QByteArray(unquote(url[len(PREFIX):]).encode()))
                    self.assertTrue(renderer.isValid())
                    size = (renderer.defaultSize().width(), renderer.defaultSize().height())
                    self.assertGreater(min(size), 0)
                    self.assertEqual(size, sizes.setdefault(name, size))
            previous = current

    def test_reference_mode_is_immutable_across_live_role_changes(self):
        self.assertTrue(self.palette.setProperty("followSystem", False))
        baseline, assets = self.snapshot(), self.assets()
        self.assertEqual(baseline["background"], "#7894a7")
        self.assertEqual(baseline["recessed"], "#607f91")
        for values in (GRAY, DARK, YELLOW, CORALREEF):
            self.apply(values)
            self.assertEqual(self.snapshot(), baseline)
            self.assertEqual(self.assets(), assets)
            self.assertFalse(self.palette.property("pagerContrastProtected"))

    def test_pager_keeps_yellow_and_protects_only_collision_schemes(self):
        from PyQt6.QtGui import QColor
        for values in (CORALREEF, GRAY, DARK):
            self.apply(values)
            self.assertFalse(self.palette.property("pagerContrastProtected"))
            self.assertEqual(self.color("pagerLight").name(), "#dddd28")
        self.apply(YELLOW)
        self.assertTrue(self.palette.property("pagerContrastProtected"))
        lamp, pressed = self.color("pagerLight"), self.color("pagerPressedLight")
        self.assertNotEqual(lamp.name(), "#dddd28")
        self.assertAlmostEqual(lamp.hslHueF(), QColor("#dddd28").hslHueF(), delta=.002)
        for role in ("background", "recessed"):
            with self.subTest(surround=role):
                self.assertGreaterEqual(self.contrast(lamp, self.color(role)), 4 - .03)
                self.assertGreaterEqual(self.contrast(pressed, self.color(role)), 3 - .03)
        self.assertGreater(pressed.lightnessF(), lamp.lightnessF())
        self.apply(CORALREEF)
        self.assertFalse(self.palette.property("pagerContrastProtected"))
        self.assertEqual(self.color("pagerLight").name(), "#dddd28")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(DomainOSPalettePolicy)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    with tempfile.TemporaryDirectory(prefix="domainos-palette-") as temporary:
        env = dict(os.environ)
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
                "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
            path = Path(temporary) / key.lower()
            path.mkdir(mode=0o700)
            env[key] = str(path)
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS",
                "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH",
                "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "SESSION_MANAGER"):
            env.pop(key, None)
        env.update(DOMAINOS_PALETTE_PRIVATE="1", QT_QPA_PLATFORM="offscreen",
            QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic",
            QML_DISABLE_DISK_CACHE="1", PYTHONDONTWRITEBYTECODE="1",
            XDG_CONFIG_DIRS="/etc/xdg", XDG_DATA_DIRS="/usr/local/share:/usr/share",
            DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(Path(temporary) / "disabled-system"))
        # The default native role provider is constructed before being replaced
        # by the policy fixture. Give it an explicit owned theme configuration.
        (Path(env["XDG_CONFIG_HOME"]) / "plasmarc").write_text("[Theme]\nname=default\n")
        run = subprocess.run(["dbus-run-session", "--", sys.executable,
            str(Path(__file__).resolve()), "--worker"], env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        print(run.stdout, end="")
        return run.returncode


if __name__ == "__main__":
    sys.exit(main())
