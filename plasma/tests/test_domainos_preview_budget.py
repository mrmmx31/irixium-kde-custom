#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Production cards with private offscreen Qt and controlled incubation.

The X11 provider is deliberately unavailable on the offscreen platform. This
tests allocation, cancellation and clickable scaffolding, not real frames.
"""
import json
import unittest

# Reuse the existing private HOME/cache/runtime and installed QML setup.
import test_domainos_thumbnails as setup
from PyQt6.QtCore import QMetaObject, Qt, QUrl, Q_ARG
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlComponent, QQmlEngine, QQmlIncubationController
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtTest import QTest


class PreviewBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.engine = QQmlEngine()
        self.incubation = QQmlIncubationController()
        self.engine.setIncubationController(self.incubation)
        source = '''import QtQuick
import "''' + setup.UI.as_uri() + '''" as Production
Item {
    id: fixture
    width: 560; height: 220
    property bool previewsEnabled: true
    property bool tooltipVisible: true
    property string backend: "x11"
    property int columnCount: 2
    property real previewWidth: 264
    property real maximumHeight: 194
    property real contentHeight: Math.ceil(windowRecords.length / columnCount) * 190 + 16
    property var windowRecords: Array.from({length:12}, (_,index) => ({
        key:"window:" + index, pid:9000 + index, title:"Owned fixture " + index,
        windowIds:[index + 1], minimized:false}))
    property QtObject colorPalette: colors
    property string activatedKey: ""
    function hideImmediately() { tooltipVisible = false }
    signal activationRequested(var windowRecord)
    onActivationRequested: record => activatedKey = record.key
    Production.DomainOSPalette { id: colors }
    Production.DomainOSWindowPreviewContents {
        id: canvas
        width: 556; height: 194
        preview: fixture
    }
    function scan(item) {
        let found=[]
        for (const child of item.children || []) {
            found.push(child)
            found=found.concat(scan(child))
        }
        return found
    }
    function cards() { return scan(canvas).filter(item=>item.objectName === "domainosThumbnailCard") }
    function state() {
        return JSON.stringify(cards().map(card=>{
            const provider=scan(card).find(item=>item.objectName === "domainosThumbnailNativeProvider")
            return {key:card.modelData.key, width:card.width, height:card.height,
                viewport:card.intersectsViewport, active:provider.active,
                asynchronous:provider.asynchronous, loaded:!!provider.item,
                loadedId:provider.item ? provider.item.windowId : null}
        }))
    }
    function scroll(value) { canvas.contentItem.contentY=value }
    function click(key) {
        const card=cards().find(item=>item.modelData.key === key)
        scan(card).find(item=>item.objectName === "domainosThumbnailPointer").clicked(null)
    }
}'''
        self.component = QQmlComponent(self.engine)
        self.component.setData(source.encode(), QUrl.fromLocalFile(str(setup.UI / "preview-budget-fixture.qml")))
        self.root = self.component.create()
        if self.root is None:
            self.fail("\n".join(error.toString() for error in self.component.errors()))
        self.window = QQuickWindow()
        self.window.resize(560, 220)
        self.root.setParentItem(self.window.contentItem())
        self.window.show()
        self.settle()

    def tearDown(self):
        self.window.close()
        self.root.deleteLater()
        self.window.deleteLater()
        self.app.processEvents()
        self.engine.deleteLater()
        self.app.processEvents()

    def settle(self):
        # Layout/events run, while controlled incubation stays paused.
        self.app.processEvents()
        QTest.qWait(20)
        self.app.processEvents()

    def state(self):
        # Invoke the real QML helper through the engine; no parallel policy.
        self.engine.globalObject().setProperty("budgetFixture", self.engine.newQObject(self.root))
        result = self.engine.evaluate("budgetFixture.state()")
        self.assertFalse(result.isError(), result.toString())
        return json.loads(result.toString())

    def invoke(self, method, value):
        # PyQt returns None for these void QML methods; their resulting state
        # is checked by the caller, and invocation errors raise exceptions.
        QMetaObject.invokeMethod(self.root, method, Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", value))

    def test_only_visible_cards_incubate_and_labels_are_complete(self):
        cards = self.state()
        self.assertEqual(len(cards), 12)
        self.assertTrue(all(card["width"] >= 160 and card["height"] == 178 for card in cards))
        self.assertEqual([card["key"] for card in cards if card["active"]], ["window:0", "window:1"])
        self.assertTrue(all(card["asynchronous"] for card in cards))
        self.assertTrue(all(not card["loaded"] for card in cards))

    def test_scroll_discards_previous_row_and_only_creates_current_row(self):
        self.invoke("scroll", 190)
        self.settle()
        cards = self.state()
        self.assertEqual([card["key"] for card in cards if card["active"]], ["window:2", "window:3"])
        self.incubation.incubateFor(100)
        self.settle()
        cards = self.state()
        self.assertTrue(all(not card["loaded"] for card in cards if not card["active"]))
        self.assertLessEqual(sum(card["loaded"] for card in cards), 2)

    def test_owner_loss_cancels_pending_providers_without_old_frames(self):
        self.root.setProperty("tooltipVisible", False)
        self.incubation.incubateFor(100)
        self.settle()
        self.assertTrue(all(not card["active"] and not card["loaded"] for card in self.state()))
        self.root.setProperty("windowRecords", [{"key":"window:new", "pid":10000,
            "title":"New owner", "windowIds":[55], "minimized":False}])
        self.root.setProperty("tooltipVisible", True)
        self.settle()
        self.incubation.incubateFor(100)
        self.settle()
        cards = self.state()
        self.assertEqual([card["key"] for card in cards], ["window:new"])
        self.assertTrue(cards[0]["active"])
        self.assertIn(cards[0]["loadedId"], (None, 55))

    def test_empty_card_activates_before_provider_incubates(self):
        self.assertTrue(all(not card["loaded"] for card in self.state()))
        self.invoke("click", "window:0")
        self.assertEqual(self.root.property("activatedKey"), "window:0")
        self.incubation.incubateFor(100)
        self.settle()
        self.assertTrue(all(not card["active"] and not card["loaded"] for card in self.state()))


if __name__ == "__main__":
    unittest.main()
