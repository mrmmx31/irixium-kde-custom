#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Popup control contracts; execute in an owned Qt/D-Bus/XDG test session.

These tests cover public Qt input and layout. Scheme painting has its separate
native CLI proof. No application palette or real desktop preference is changed.
"""
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QML_DISABLE_DISK_CACHE"] = "1"
from PyQt6 import sip
from PyQt6.QtCore import QPoint, QUrl, Qt
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtQuick import QQuickItem, QQuickWindow
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

UI = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel/contents/ui"
QML = '''import QtQuick
import UI_URL as Panel
Window {
    id: root; visible: true; width: 700; height: 240
    property int clicks: 0
    property alias normal: normal
    property alias longButton: longButton
    property alias compact: compact
    property alias field: field
    property alias disabled: disabled
    Panel.DomainOSButton { id: normal; x: 20; y: 20; text: "Back"; onClicked: root.clicks++ }
    Panel.DomainOSButton { id: longButton; x: 150; y: 20; text: "An action with enough text to require its full width" }
    Panel.DomainOSButton { id: compact; x: 20; y: 75; width: 28; height: 28; icon.name: "list-remove"; icon.width: 16; icon.height: 16; padding: 2; onClicked: root.clicks++ }
    Panel.DomainOSButton { id: disabled; x: 150; y: 75; text: "Disabled"; enabled: false; onClicked: root.clicks++ }
    Panel.DomainOSTextField { id: field; x: 20; y: 130; text: "Search"; selectByMouse: true }
}
'''.replace("UI_URL", json.dumps(UI.as_uri()))

class PopupControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.saved_palette = cls.app.palette()

    def setUp(self):
        self.engine = QQmlEngine()
        self.component = QQmlComponent(self.engine)
        self.component.setData(QML.encode(), QUrl.fromLocalFile(str(UI / "control-contract.qml")))
        self.root = self.component.create()
        self.assertIsNotNone(self.root, [e.toString() for e in self.component.errors()])
        self.window = sip.cast(self.root, QQuickWindow)
        self.settle()

    def tearDown(self):
        self.window.close()
        self.root.deleteLater()
        self.engine.deleteLater()
        self.settle()
        self.assertEqual(self.app.palette(), self.saved_palette)

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    def item(self, name):
        return sip.cast(self.root.property(name), QQuickItem)

    def point(self, name):
        item = self.item(name)
        return QPoint(round(item.x() + item.width()/2), round(item.y() + item.height()/2))

    def test_text_buttons_keep_minimum_and_expand_with_content(self):
        short, long = self.item("normal"), self.item("longButton")
        self.assertEqual(short.property("implicitWidth"), 80)
        self.assertGreater(long.property("implicitWidth"), 80)
        self.assertGreaterEqual(long.width(), long.property("implicitContentWidth") + long.property("leftPadding") + long.property("rightPadding"))

    def test_compact_icon_button_keeps_explicit_dimensions_and_action(self):
        compact = self.item("compact")
        self.assertEqual((compact.width(), compact.height()), (28, 28))
        QTest.mouseClick(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, self.point("compact"))
        self.settle()
        self.assertEqual(self.root.property("clicks"), 1)

    def test_native_press_and_release_preserve_one_action(self):
        point = self.point("normal")
        QTest.mousePress(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        self.assertTrue(self.item("normal").property("down"))
        self.assertEqual(self.root.property("clicks"), 0)
        QTest.mouseRelease(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        self.settle()
        self.assertFalse(self.item("normal").property("down"))
        self.assertEqual(self.root.property("clicks"), 1)

    def test_disabled_button_does_not_dispatch(self):
        QTest.mouseClick(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, self.point("disabled"))
        self.settle()
        self.assertEqual(self.root.property("clicks"), 0)

    def test_textfield_preserves_layout_and_native_editing(self):
        field = self.item("field")
        self.assertGreaterEqual(field.property("implicitWidth"), 200)
        self.assertGreaterEqual(field.property("implicitHeight"), 30)
        self.assertEqual([field.property(p) for p in ("topPadding", "bottomPadding", "leftPadding", "rightPadding")], [6]*4)
        QTest.mouseClick(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, self.point("field"))
        QTest.keyClick(self.window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        for key in (Qt.Key.Key_N, Qt.Key.Key_E, Qt.Key.Key_W):
            QTest.keyClick(self.window, key)
        self.settle()
        self.assertEqual(field.property("text"), "new")

    def test_popup_controls_have_no_qstyle_painter(self):
        def walk(item):
            yield item
            for child in item.childItems():
                yield from walk(child)
        classes = [item.metaObject().className() for item in walk(self.window.contentItem())]
        self.assertFalse(any("StyleItem" in name for name in classes), classes)

if __name__ == "__main__":
    unittest.main()
