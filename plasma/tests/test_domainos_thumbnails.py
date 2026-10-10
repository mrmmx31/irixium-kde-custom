#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise optional preview lifecycle without accessing a user's compositor."""
import os
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ["QML_DISABLE_DISK_CACHE"] = "1"
os.environ["QT_QPA_PLATFORMTHEME"] = "generic"
os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"
_private = tempfile.TemporaryDirectory(prefix=".qa-domainos-thumbnail-lifecycle-", dir=Path(__file__).resolve().parents[2])
for _variable in ("HOME", "TMPDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR"):
    _path = Path(_private.name) / _variable.lower()
    _path.mkdir(mode=0o700)
    os.environ[_variable] = str(_path)

_theme = Path(os.environ["XDG_DATA_HOME"]) / "plasma/desktoptheme/IrixClassicDomainOS"
_theme.parent.mkdir(parents=True)
_theme.symlink_to(Path(__file__).resolve().parents[1] / "IrixClassicDomainOS", target_is_directory=True)
(Path(os.environ["XDG_CONFIG_HOME"]) / "kdeglobals").write_text(
    "[Colors:Window]\nBackgroundNormal=214,187,116\nForegroundNormal=32,19,5\n"
    "[Colors:Tooltip]\nBackgroundNormal=214,187,116\nForegroundNormal=32,19,5\n")
(Path(os.environ["XDG_CONFIG_HOME"]) / "plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
os.environ["XDG_DATA_DIRS"]="/usr/local/share:/usr/share"
os.environ["XDG_CONFIG_DIRS"]="/etc/xdg"

from PyQt6.QtCore import QUrl, QMetaObject, Qt, QPoint, QPointF, QObject
from PyQt6.QtGui import QGuiApplication, QPalette, QColor
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtQuick import QQuickItem, QQuickWindow
from PyQt6.QtTest import QTest

APPLET = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel"
UI = APPLET / "contents/ui"


class ThumbnailLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.engine = QQmlEngine()
        source = '''import QtQuick
import "''' + UI.as_uri() + '''" as Production
Item {
    id: fixture
    width:800; height:600
    property alias preview: candidate
    property alias model: controller
    property alias second: secondCandidate
    property string activatedKey:""
    property var windows:[
        {key:"window:1",pid:701,title:"First",windowIds:[1],minimized:false},
        {key:"window:2",pid:702,title:"Second",windowIds:[2],minimized:false}]
    QtObject {
        id:controller
        property var windows: fixture.windows
        function windowFor(key) { return windows.find(window=>window.key===key) || null }
        function membersFor(key) { return windows }
    }
    Production.DomainOSPalette { id: colors }
    Production.DomainOSWindowThumbnails {
        id:candidate; x:20;y:30;width:120;height:60
        onActivationRequested: windowRecord => fixture.activatedKey=windowRecord.key
        controller: controller
        colorPalette: colors
        record: ({key:"window:1",pid:701,group:false})
    }
    Production.DomainOSWindowThumbnails {
        id:secondCandidate; x:200;y:30;width:120;height:60
        controller:controller; colorPalette:colors
        record:({key:"window:2",pid:702,group:false,title:"Second"})
    }
}'''
        cls.component = QQmlComponent(cls.engine)
        cls.component.setData(source.encode(), QUrl.fromLocalFile(str(UI / "thumbnail-lifecycle-test.qml")))
        cls.root = cls.component.create()
        if not cls.root:
            raise RuntimeError("\n".join(error.toString() for error in cls.component.errors()))
        cls.view = QQuickWindow()
        cls.view.resize(800,600)
        cls.root.setParentItem(cls.view.contentItem())
        cls.view.show()
        cls.preview = cls.root.property("preview")
        cls.second = cls.root.property("second")

    @classmethod
    def tearDownClass(cls):
        cls.view.close()
        cls.view.deleteLater()
        cls.root.deleteLater()
        cls.app.processEvents()

    def settle(self):
        QTest.qWait(20)
        self.app.processEvents()

    def descendants(self, item):
        result = []
        for child in item.childItems():
            result.append(child)
            result.extend(self.descendants(child))
        return result

    def setUp(self):
        self.root.setProperty("windows", [
            {"key": "window:1", "pid": 701, "title": "First", "windowIds": [1], "minimized": False},
            {"key": "window:2", "pid": 702, "title": "Second", "windowIds": [2], "minimized": False},
        ])
        self.preview.setProperty("previewsEnabled", False)
        self.preview.setProperty("hintsEnabled", True)
        QMetaObject.invokeMethod(self.preview, "hideImmediately")
        self.preview.setProperty("record", {"key": "window:1", "pid": 701, "group": False, "title":"First"})
        self.second.setProperty("previewsEnabled", False)
        self.second.setProperty("hintsEnabled", True)
        self.root.setProperty("activatedKey", "")
        self.settle()

    def test_schema_defaults_to_disabled(self):
        root = ET.parse(APPLET / "contents/config/main.xml").getroot()
        entry = root.find("{*}group/{*}entry[@name='iconboxWindowThumbnails']")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.attrib["type"], "Bool")
        self.assertEqual(entry.find("{*}default").text, "false")

    def test_disabled_preview_does_not_load_content_even_on_visibility_request(self):
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        contents = self.preview.property("contentsLoader")
        self.assertFalse(contents.property("active"))
        self.assertIsNone(contents.property("item"))
        self.assertFalse(self.preview.property("providersLoaded"))

    def test_enabled_preview_stays_unloaded_until_requested(self):
        self.preview.setProperty("previewsEnabled", True)
        self.settle()
        self.assertFalse(self.preview.property("contentsLoader").property("active"))
        self.assertFalse(self.preview.property("providersLoaded"))

    def test_enabled_content_loads_then_unloads_on_hide_and_disable(self):
        self.preview.setProperty("previewsEnabled", True)
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        self.assertTrue(self.preview.property("contentsLoader").property("active"))
        self.assertIsNotNone(self.preview.property("contentsLoader").property("item"))
        QMetaObject.invokeMethod(self.preview, "hideImmediately")
        self.settle()
        self.assertIsNone(self.preview.property("contentsLoader").property("item"))
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        self.preview.setProperty("previewsEnabled", False)
        self.settle()
        self.assertFalse(self.preview.property("contentsLoader").property("active"))
        self.assertFalse(self.preview.property("providersLoaded"))

    def test_reusing_cell_for_another_identity_releases_the_previous_contents(self):
        self.preview.setProperty("previewsEnabled", True)
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        self.assertTrue(self.preview.property("tooltipVisible"))
        self.assertIsNotNone(self.preview.property("contentsLoader").property("item"))
        self.preview.setProperty("record", {"key":"window:2", "pid":702,
            "group":False, "title":"Second"})
        self.settle()
        self.assertFalse(self.preview.property("preparingContents"))
        self.assertFalse(self.preview.property("tooltipVisible"))
        self.assertIsNone(self.preview.property("contentsLoader").property("item"))

    def test_unavailable_session_is_explicit_without_loading_a_native_provider(self):
        self.assertEqual(self.preview.property("backend"), "unavailable")
        self.preview.setProperty("previewsEnabled", True)
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        item = self.preview.property("contentsLoader").property("item")
        providers = [child for child in self.descendants(item)
                     if child.objectName() == "domainosThumbnailNativeProvider"]
        self.assertTrue(providers)
        self.assertTrue(all(not child.property("active") and child.property("item") is None
                            for child in providers))
        cards = [child for child in self.descendants(item)
                 if child.objectName() == "domainosThumbnailCard"]
        self.assertTrue(cards)
        self.assertTrue(all("indisponível" in child.property("unavailableReason") for child in cards))

    def test_group_exposes_every_current_window_without_group_capture(self):
        self.preview.setProperty("record", {"key": "group:app", "group": True})
        self.preview.setProperty("previewsEnabled", True)
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        item = self.preview.property("contentsLoader").property("item")
        cards = [child for child in self.descendants(item)
                 if child.objectName() == "domainosThumbnailCard"]
        self.assertEqual(len(cards), 2)
        self.assertEqual(self.preview.property("columnCount"), 2)

    def test_reused_native_id_from_another_process_is_not_previewed(self):
        self.preview.setProperty("record", {"key": "window:1", "pid": 799, "group": False})
        self.preview.setProperty("previewsEnabled", True)
        self.settle()
        self.assertEqual(self.preview.property("windowRecords").toVariant(), [])

    def test_default_text_hint_has_no_thumbnail_content(self):
        self.assertTrue(self.preview.property("hintsEnabled"))
        self.assertEqual(self.preview.property("mainItem").objectName(), "domainosOwnedTooltipContents")
        self.assertIsNone(self.preview.property("contentsLoader").property("item"))

    def test_group_hint_preserves_member_order_and_literal_titles(self):
        self.preview.setProperty("record", {"key": "group:app", "title": "App <name> & tools", "group": True})
        self.settle()
        self.assertEqual(self.preview.property("mainText"), "App <name> & tools")
        self.assertEqual(self.preview.property("subText"), "1. First\n2. Second")
        self.assertEqual(self.preview.property("textFormat"), 0)

    def test_large_group_text_hint_has_every_title_and_no_capture_provider(self):
        windows = [{"key": "window:" + str(index), "pid": 701 + index,
                    "title": "Window " + str(index) + " <literal> & title",
                    "windowIds": [index + 1], "minimized": False} for index in range(12)]
        self.root.setProperty("windows", windows)
        self.preview.setProperty("record", {"key": "group:all", "title": "All windows", "group": True})
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        loader = self.preview.property("mainItem").findChild(QObject, "domainosWindowTitlesLoader")
        item = loader.property("item")
        titles = [child for child in self.descendants(item) if child.objectName() == "domainosWindowHintTitle"]
        self.assertEqual(len(titles), 12)
        self.assertEqual(titles[-1].property("text"), "12. Window 11 <literal> & title")
        self.assertFalse(self.preview.property("providersLoaded"))
        self.assertIsNone(self.preview.property("contentsLoader").property("item"))

    def test_no_hint_mode_never_loads_text_or_thumbnail_content(self):
        self.preview.setProperty("hintsEnabled", False)
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        self.assertFalse(self.preview.property("active"))
        self.assertEqual(self.preview.property("mainItem").objectName(), "domainosOwnedTooltipContents")
        self.assertIsNone(self.preview.property("contentsLoader").property("item"))


    def test_native_hint_frame_and_contents_follow_changed_application_palette(self):
        saved=self.app.palette()
        try:
            palette=QPalette(saved)
            for role, value in ((QPalette.ColorRole.Window,"#d6bb74"),
                                (QPalette.ColorRole.Base,"#d6bb74"),
                                (QPalette.ColorRole.WindowText,"#201305"),
                                (QPalette.ColorRole.Text,"#201305")):
                palette.setColor(role,QColor(value))
            self.app.setPalette(palette)
            QMetaObject.invokeMethod(self.preview,"showToolTip")
            self.settle()
            frame=self.preview.property("mainItem").window().grabWindow()
            self.assertFalse(frame.isNull())
            pixel=frame.pixelColor(frame.width()//2,1)
            # The old fixed cyan/blue shoulder has blue > red. The golden
            # application surface and every derived relief band retain red > blue.
            self.assertGreater(pixel.red(), pixel.blue(),pixel.name())
            frame.save("/tmp/domainos-native-tooltip-palette-lifecycle.png")
        finally:
            self.app.setPalette(saved)
            self.settle()

    def test_empty_preview_cards_have_geometry_and_activate_without_a_frame(self):
        self.preview.setProperty("record", {"key":"group:all","group":True,"title":"All"})
        self.preview.setProperty("previewsEnabled", True)
        QMetaObject.invokeMethod(self.preview, "showToolTip")
        self.settle()
        contents=self.preview.property("contentsLoader").property("item")
        cards=[c for c in self.descendants(contents) if c.objectName()=="domainosThumbnailCard"]
        self.assertEqual(len(cards),2)
        self.assertTrue(self.preview.property("tooltipVisible"))
        for index in range(2):
            contents=self.preview.property("contentsLoader").property("item")
            card=[c for c in self.descendants(contents) if c.objectName()=="domainosThumbnailCard"][index]
            expected=card.property("modelData").toVariant()["key"]
            self.assertGreaterEqual(card.width(),160)
            self.assertEqual(card.height(),178)
            self.assertFalse(card.property("liveAvailable"))
            point=card.mapToScene(QPointF(card.width()/2,card.height()/2)).toPoint()
            QTest.mouseClick(card.window(), Qt.MouseButton.LeftButton, pos=point)
            self.settle()
            self.assertEqual(self.root.property("activatedKey"), expected)
            QMetaObject.invokeMethod(self.preview,"showToolTip")
            self.settle()

    def test_switching_tooltip_owner_never_marks_previous_cell_visible(self):
        for index in range(12):
            current=self.preview if index%2==0 else self.second
            other=self.second if index%2==0 else self.preview
            current.setProperty("previewsEnabled", index%3==0)
            QMetaObject.invokeMethod(current,"showToolTip")
            self.settle()
            self.assertTrue(current.property("tooltipVisible"))
            self.assertFalse(other.property("tooltipVisible"))
            self.assertFalse(other.property("providersLoaded"))
            self.assertFalse(other.property("mainItem").isVisible())

    def test_preview_to_titles_uses_one_owned_item_and_leaves_no_provider(self):
        owned=self.preview.property("mainItem")
        for index in range(8):
            self.preview.setProperty("previewsEnabled",True)
            QMetaObject.invokeMethod(self.preview,"showToolTip")
            self.settle()
            self.assertIsNotNone(self.preview.property("contentsLoader").property("item"))
            self.preview.setProperty("previewsEnabled",False)
            QMetaObject.invokeMethod(self.preview,"showToolTip")
            self.settle()
            self.assertIs(self.preview.property("mainItem"),owned)
            self.assertTrue(self.preview.property("tooltipVisible"))
            self.assertFalse(self.preview.property("contentsLoader").isVisible())
            self.assertIsNone(self.preview.property("contentsLoader").property("item"))
            text=owned.findChild(QObject,"domainosWindowHintTitle")
            self.assertIsNone(text)
            self.assertGreater(owned.width(),0)
            self.assertGreater(owned.height(),0)


if __name__ == "__main__":
    unittest.main()
