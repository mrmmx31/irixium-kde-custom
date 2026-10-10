#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check hover ownership and cancellation; the spy is not a compositor proof."""
import os
from pathlib import Path
import tempfile
import unittest

root = Path(__file__).resolve().parents[2]
_private = tempfile.TemporaryDirectory(prefix=".qa-domainos-highlight-", dir=root)
for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR"):
    path = Path(_private.name) / key.lower()
    path.mkdir(mode=0o700)
    os.environ[key] = str(path)
os.environ.update(QT_QPA_PLATFORM="offscreen", QML_DISABLE_DISK_CACHE="1")
from PyQt6.QtCore import QCoreApplication, QUrl, Qt, QMetaObject, Q_ARG
from PyQt6.QtQml import QQmlComponent, QQmlEngine

UI = root / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"

class HighlightOwnership(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.engine = QQmlEngine()
        self.component = QQmlComponent(self.engine)
        self.component.setData(('''import QtQuick
import "''' + UI.as_uri() + '''" as Production
QtObject {
    property var bridge: QtObject {
        property var events: []
        property bool available: true
        function validHighlightRecord(record) {return available && record && record.pid===701}
        function highlightRecord(record,on) {events=events.concat([{key:record?record.key:"",on:on}]);return !!on}
    }
    property var manager: Production.DomainOSWindowHighlight {backend:bridge}
}''').encode(), QUrl.fromLocalFile(str(UI / "highlight-fixture.qml")))
        self.root = self.component.create()
        self.assertIsNotNone(self.root, "\n".join(e.toString() for e in self.component.errors()))
        self.manager = self.root.property("manager")
        self.bridge = self.root.property("bridge")

    def tearDown(self):
        self.root.deleteLater()
        self.app.processEvents()
        self.engine.deleteLater()
        self.app.processEvents()

    def call(self, method, key="one", pid=701):
        QMetaObject.invokeMethod(self.manager, method, Qt.ConnectionType.DirectConnection,
                                 Q_ARG("QVariant", {"key":key,"pid":pid}))

    def events(self):
        return self.bridge.property("events").toVariant()

    def current(self):
        value = self.manager.property("currentRecord")
        return value.toVariant() if hasattr(value, "toVariant") else value

    def test_default_hover_never_requests_a_highlight(self):
        before = self.events()
        self.call("enter")
        self.assertEqual(self.events(), before)
        self.assertFalse(self.manager.property("enabled"))
        self.assertFalse(any(e["on"] for e in self.events()))
        self.assertIsNone(self.current())

    def test_next_window_is_highlighted_and_late_exit_keeps_it(self):
        self.manager.setProperty("enabled", True)
        self.call("enter", "one")
        self.call("enter", "two")
        before = self.events()
        self.call("leave", "one")
        self.assertEqual(self.events(), before)
        self.assertEqual(self.current()["key"], "two")
        self.assertEqual([e["key"] for e in self.events() if e["on"]], ["one", "two"])
        self.call("leave", "two")
        self.assertIsNone(self.current())
        self.assertFalse(self.events()[-1]["on"])

    def test_disabling_preference_cancels_current_highlight(self):
        self.manager.setProperty("enabled", True)
        self.call("enter")
        self.manager.setProperty("enabled", False)
        self.assertIsNone(self.current())
        self.assertFalse(self.events()[-1]["on"])

    def test_invalid_process_cancels_instead_of_switching(self):
        self.manager.setProperty("enabled", True)
        self.call("enter")
        self.call("enter", "two", 799)
        self.assertIsNone(self.current())
        self.assertEqual([e["key"] for e in self.events() if e["on"]], ["one"])

    def test_disappearing_window_cancels_effect(self):
        self.manager.setProperty("enabled", True)
        self.call("enter")
        self.bridge.setProperty("available", False)
        QMetaObject.invokeMethod(self.manager, "validate", Qt.ConnectionType.DirectConnection)
        self.assertIsNone(self.current())
        self.assertFalse(self.events()[-1]["on"])

if __name__ == "__main__": unittest.main()
