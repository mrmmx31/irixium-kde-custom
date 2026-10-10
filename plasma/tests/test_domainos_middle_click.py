#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Middle-click dispatch and stale identity checks in the production Iconbox.

The model records native requests; this test does not start a real application.
CanLaunchNewInstance=false also occurs with a Desktop Entry New Window action.
"""
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
_private = tempfile.TemporaryDirectory(prefix=".qa-domainos-middle-", dir=ROOT)
for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
    path = Path(_private.name) / key.lower()
    path.mkdir(mode=0o700)
    os.environ[key] = str(path)
for key in ("DISPLAY", "WAYLAND_DISPLAY", "QT_STYLE_OVERRIDE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "LD_PRELOAD"):
    os.environ.pop(key, None)
os.environ.update(QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
    QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic", QML_DISABLE_DISK_CACHE="1",
    DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(Path(_private.name) / "disabled-session"),
    DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(Path(_private.name) / "disabled-system"))

from PyQt6 import sip
from PyQt6.QtCore import Q_ARG, QMetaObject, QPointF, QUrl, Qt
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication


class MiddleClick(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.engine = QQmlApplicationEngine()
        self.diagnostics = []
        self.engine.warnings.connect(lambda messages: self.diagnostics.extend(message.toString() for message in messages))
        self.fixture_path = Path(_private.name) / "middle-fixture.qml"
        self.fixture_path.write_text('''import QtQuick
import "''' + (ROOT / "plasma/tests").as_uri() + '''"
DomainOSIconboxPreview {
    id: fixture
    property var captured: null
    function prepare(grouped) {
        resetUi()
        controller.groupingMode = grouped ? 1 : 0
        controller.onlyCurrentDesktop = false
        controller.onlyCurrentActivity = false
        windows = windows.map(row => Object.assign({}, row, {canLaunchNewInstance:false}))
    }
    function capture(key) { captured = controller.taskFor(key) }
    function middleCaptured() { iconbox.middleAction(captured) }
    function middle(key) { iconbox.middleAction(controller.taskFor(key)) }
    function rememberSelection() { controller.selectTask("window:6",0) }
}''')
        self.engine.load(QUrl.fromLocalFile(str(self.fixture_path)))
        self.assertTrue(self.engine.rootObjects(), "\n".join(self.diagnostics))
        self.window = sip.cast(self.engine.rootObjects()[0], QQuickWindow)
        self.box = self.window.property("iconbox")
        self.tasks = self.window.property("controller")
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.engine.deleteLater()
        self.app.processEvents()
        self.assertFalse(self.diagnostics, "\n".join(self.diagnostics))

    @staticmethod
    def variant(value):
        return value.toVariant() if hasattr(value, "toVariant") else value

    def invoke(self, method, *arguments):
        QMetaObject.invokeMethod(self.window, method, Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", argument) for argument in arguments))
        self.app.processEvents()

    def requests(self):
        return self.variant(self.window.property("requests"))

    def button(self, key):
        def descend(item):
            yield item
            for child in item.childItems():
                yield from descend(child)
        return next(item for item in descend(self.window.contentItem())
            if item.objectName() == "domainosLiveTask_" + key)

    def click_middle(self, key):
        button = self.button(key)
        QTest.mouseClick(self.window, Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.NoModifier,
            button.mapToScene(QPointF(button.width()/2, button.height()/2)).toPoint())
        self.app.processEvents()

    def test_group_with_hidden_generic_menu_action_still_requests_once(self):
        self.invoke("prepare", True)
        self.invoke("rememberSelection")
        previous = self.variant(self.tasks.property("selectedKeys"))
        self.click_middle("group:terminal")
        self.assertEqual([request["action"] for request in self.requests()], ["newInstance"])
        self.assertEqual(self.variant(self.tasks.property("selectedKeys")), previous)
        self.assertFalse(self.box.property("groupPopupVisible"))
        self.assertEqual(self.box.property("lastError"), "")

    def test_single_window_with_hidden_generic_menu_action_requests_once(self):
        self.invoke("prepare", False)
        self.click_middle("window:1")
        self.assertEqual(self.requests(), [{"action":"newInstance", "ids":[1], "argument":None}])
        self.assertFalse(self.box.property("groupPopupVisible"))
        self.assertEqual(self.box.property("lastError"), "")

    def test_disabled_middle_preference_requests_nothing(self):
        self.invoke("prepare", True)
        self.box.setProperty("middleClickAction", 0)
        self.click_middle("group:terminal")
        self.assertEqual(self.requests(), [])

    def test_changed_group_pid_does_not_launch_reused_identity(self):
        self.invoke("prepare", True)
        self.invoke("capture", "group:terminal")
        self.invoke("mutate", 1, "pid", 9991)
        self.invoke("middleCaptured")
        self.assertEqual(self.requests(), [])
        self.assertIn("identity", self.box.property("lastError"))

    def test_reordered_group_is_resolved_again_and_launches_once(self):
        self.invoke("prepare", True)
        self.invoke("capture", "group:terminal")
        self.invoke("reverseWindows")
        self.invoke("middleCaptured")
        self.assertEqual([request["action"] for request in self.requests()], ["newInstance"])
        self.assertEqual(self.box.property("lastError"), "")

    def test_single_window_pid_reuse_does_not_launch(self):
        self.invoke("prepare", False)
        self.invoke("capture", "window:1")
        self.invoke("mutate", 1, "pid", 9991)
        self.invoke("middleCaptured")
        self.assertEqual(self.requests(), [])


if __name__ == "__main__":
    unittest.main()
