#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Text and ownership contracts; native placement has a separate Wayland proof."""
import os
from pathlib import Path
import tempfile
import unittest

_private = tempfile.TemporaryDirectory(prefix=".qa-domainos-member-hint-", dir=Path(__file__).resolve().parents[2])
for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR"):
    path = Path(_private.name) / key.lower()
    path.mkdir(mode=0o700)
    os.environ[key] = str(path)
os.environ.update(QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                  QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Fusion",
                  QML_DISABLE_DISK_CACHE="1")

from PyQt6.QtCore import QMetaObject, QUrl, Qt, QPoint, QPointF, QObject, Q_ARG, QVariant
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQuick import QQuickView
from PyQt6.QtQml import QQmlExpression, qmlContext
from PyQt6.QtTest import QTest

UI = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel/contents/ui"
LONG_TITLE = "Literal <title> & " + "long title " * 30


class MemberHint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        source = '''import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import "''' + UI.as_uri() + '''" as Production
Item {
 width:600;height:500
 property alias hint:first
 property alias second:second
 property alias picker:picker
 property alias model:model
 readonly property int platformDelay:Kirigami.Units.toolTipDelay
 QtObject {id:model
  property var current:({key:"owned",pid:701,title:"Literal <title> & "+"long title ".repeat(30),windowIds:[]})
  property var other:({key:"other",pid:702,title:"Other <literal> & "+"long title ".repeat(30),windowIds:[]})
  function windowFor(key){return key==="owned"?current:key==="other"?other:null}
 }
 Controls.Popup {
  id:picker;x:20;y:250;width:540;height:140;popupType:Controls.Popup.Window
  property var hintOwner:null
  onAboutToHide:{if(hintOwner)hintOwner.hideImmediately();hintOwner=null}
  Column {
   width:500
   Controls.ItemDelegate {id:rowA;width:500;height:36;text:model.current?model.current.title:""
    Controls.ToolTip.visible:false
    contentItem:Text{id:captionA;text:rowA.text;textFormat:Text.PlainText;elide:Text.ElideRight;verticalAlignment:Text.AlignVCenter}
    Production.DomainOSGroupMemberHint{id:first;anchors.fill:parent;controller:model;record:({key:"owned",pid:701});titleTruncated:captionA.truncated;ownerRegistry:picker}
   }
   Controls.ItemDelegate {id:rowB;width:500;height:36;text:model.other?model.other.title:""
    Controls.ToolTip.visible:false
    contentItem:Text{id:captionB;text:rowB.text;textFormat:Text.PlainText;elide:Text.ElideRight;verticalAlignment:Text.AlignVCenter}
    Production.DomainOSGroupMemberHint{id:second;anchors.fill:parent;controller:model;record:({key:"other",pid:702});titleTruncated:captionB.truncated;ownerRegistry:picker}
   }
  }
 }
 function openPicker(){picker.open()}
}'''
        self.file = Path(_private.name) / "fixture.qml"
        self.file.write_text(source)
        self.view = QQuickView()
        self.view.setSource(QUrl.fromLocalFile(str(self.file)))
        self.assertNotEqual(self.view.status(), QQuickView.Status.Error,
                            "\n".join(e.toString() for e in self.view.errors()))
        self.view.show()
        self.root = self.view.rootObject()
        self.hint = self.root.property("hint")
        self.second = self.root.property("second")
        self.picker = self.root.property("picker")
        QMetaObject.invokeMethod(self.root, "openPicker", Qt.ConnectionType.DirectConnection)
        QTest.qWait(40)
        self.popup_window = self.picker.property("contentItem").window()
        QTest.mouseMove(self.popup_window,QPoint(520,25))
        self.app.processEvents()
        self.delay = self.root.property("platformDelay")
        self.assertGreater(self.delay, 0)
        self.has_hovered = False

    def tearDown(self):
        for hint in (self.hint,self.second):
            QMetaObject.invokeMethod(hint,"hideImmediately",Qt.ConnectionType.DirectConnection)
        self.picker.setProperty("visible",False)
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def hover(self, row=0):
        if not self.has_hovered:
            QTest.mouseMove(self.popup_window,QPoint(530,120))
            QTest.qWait(20)
            self.has_hovered = True
        QTest.mouseMove(self.popup_window,QPoint(80,25+36*row))
        self.app.processEvents()

    def leave(self):
        QTest.mouseMove(self.popup_window,QPoint(520,25))
        self.app.processEvents()

    def wait_hint(self,hint=None):
        hint=hint or self.hint
        QTest.qWait(self.delay+80)
        self.assertTrue(hint.property("tooltipVisible"))

    def test_elided_title_waits_platform_delay_and_is_literal(self):
        self.assertTrue(self.hint.property("titleTruncated"))
        self.hover()
        self.assertFalse(self.hint.property("tooltipVisible"))
        QTest.qWait(max(1,self.delay//3))
        self.assertFalse(self.hint.property("tooltipVisible"))
        self.wait_hint()
        text=self.hint.property("tooltipPopup").findChild(QObject,"domainosMemberHintText")
        self.assertEqual(text.property("text"),LONG_TITLE)
        self.assertEqual(QQmlExpression(qmlContext(text),text,"textFormat===0").evaluate(),(True,False))
        self.assertFalse(self.hint.property("providersLoaded"))
        self.assertTrue(self.hint.property("contentsLoader") is None or self.hint.property("contentsLoader").property("item") is None)

    def test_short_full_title_has_no_hint_even_after_delay(self):
        self.root.property("model").setProperty("current",{"key":"owned","pid":701,"title":"Short title","windowIds":[]})
        QTest.qWait(20)
        self.assertFalse(self.hint.property("titleTruncated"))
        self.hover();QTest.qWait(self.delay+80)
        self.assertFalse(self.hint.property("tooltipVisible"))
        self.assertFalse(self.hint.property("providersLoaded"))

    def test_exit_before_delay_cancels_pending_hint(self):
        self.hover();QTest.qWait(max(1,self.delay//3));self.leave()
        QTest.qWait(self.delay+80)
        self.assertFalse(self.hint.property("tooltipVisible"))
        self.assertIsNone(self.hint.property("tooltipPopup"))

    def test_disabled_hints_do_not_open_or_create_providers(self):
        self.hint.setProperty("hintsEnabled",False)
        self.hover();QTest.qWait(self.delay+80)
        self.assertFalse(self.hint.property("tooltipVisible"))
        self.assertFalse(self.hint.property("providersLoaded"))

    def test_elided_updates_keep_literal_hint_and_picker_without_capture(self):
        self.hover();self.wait_hint()
        for index in range(10):
            text="Updated <literal> & " + str(index) + " long title"*30
            self.root.property("model").setProperty("current",{"key":"owned","pid":701,"title":text,"windowIds":[]})
            QTest.qWait(20)
            self.assertTrue(self.picker.property("visible"))
            self.assertTrue(self.hint.property("tooltipVisible"))
            self.assertEqual(self.hint.property("tooltipPopup").findChild(QObject,"domainosMemberHintText").property("text"),text)
        self.assertFalse(self.hint.property("providersLoaded"))

    def test_preview_omits_redundant_full_text_and_unloads_on_observed_exit(self):
        self.hint.setProperty("previewsEnabled",True)
        self.hover();self.wait_hint()
        loader=self.hint.property("contentsLoader")
        self.assertIsNotNone(loader.property("item"))
        self.assertEqual(self.hint.property("backend"),"unavailable")
        text=self.hint.property("tooltipPopup").findChild(QObject,"domainosMemberHintText")
        self.assertFalse(text.property("visible"))
        self.leave()
        # Row HoverHandler can retain its last point at a native window exit.
        # This component's owner supplies the fresh global point. Its actual
        # Iconbox routing is tested separately in the native Wayland host.
        QMetaObject.invokeMethod(self.hint,"observePointer",Qt.ConnectionType.DirectConnection,
                                 Q_ARG(QVariant,QPointF(799,799)))
        QTest.qWait(60)
        self.assertFalse(self.hint.property("tooltipVisible"))
        self.assertIsNone(self.hint.property("contentsLoader"))

    def test_moving_to_another_row_releases_previous_owner_and_content(self):
        self.hint.setProperty("previewsEnabled",True)
        self.second.setProperty("previewsEnabled",True)
        self.hover();self.wait_hint()
        self.hover(1);QTest.qWait(40)
        self.assertFalse(self.hint.property("tooltipVisible"))
        self.assertTrue(self.hint.property("contentsLoader") is None or self.hint.property("contentsLoader").property("item") is None)
        self.assertFalse(self.second.property("tooltipVisible"))
        self.wait_hint(self.second)
        self.assertIs(self.picker.property("hintOwner"),self.second)
        self.assertTrue(self.picker.property("visible"))

    def test_removing_window_or_closing_picker_releases_child_window(self):
        self.hover();self.wait_hint()
        self.root.property("model").setProperty("current",None)
        QTest.qWait(40)
        self.assertFalse(self.hint.property("tooltipVisible"))
        self.assertTrue(self.picker.property("visible"))
        self.hover(1);self.wait_hint(self.second)
        self.picker.setProperty("visible",False);QTest.qWait(40)
        self.assertFalse(self.second.property("tooltipVisible"))
        self.assertIsNone(self.second.property("tooltipPopup"))


class CaptionHint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        source='''import QtQuick
import org.kde.kirigami as Kirigami
import "'''+UI.as_uri()+'''" as Production
Item {
 width:320;height:260
 property alias preview:preview
 readonly property int platformDelay:Kirigami.Units.toolTipDelay
 QtObject {id:preview
  property var windowRecords:[({key:"owned",pid:701,title:"Literal <title> & "+"long title ".repeat(300),windowIds:[]})]
  property string backend:"unavailable"
  property real previewWidth:264
  property int columnCount:1
  property real contentHeight:194
  property real maximumHeight:250
  property QtObject colorPalette:null
  property bool tooltipVisible:true
  property bool previewsEnabled:true
  property bool hintsEnabled:false
  function hideImmediately(){tooltipVisible=false}
  signal activationRequested(var windowRecord)
 }
 Production.DomainOSWindowPreviewContents{preview:preview;x:20;y:20;width:280;height:210}
}'''
        file=Path(_private.name)/"caption-fixture.qml";file.write_text(source)
        self.view=QQuickView();self.view.setSource(QUrl.fromLocalFile(str(file)))
        self.assertNotEqual(self.view.status(),QQuickView.Status.Error,
                            "\n".join(error.toString() for error in self.view.errors()))
        self.view.show();QTest.qWait(30);self.root=self.view.rootObject()
        self.preview=self.root.property("preview");self.delay=self.root.property("platformDelay")
        QTest.mouseMove(self.view,QPoint(310,250));QTest.qWait(10)

    def tearDown(self):
        self.preview.setProperty("tooltipVisible",False)
        self.view.close();self.view.deleteLater();self.app.processEvents()

    def find(self,name):
        visited={}
        def visit(node):
            if id(node) in visited:return None
            visited[id(node)]=node
            if node.objectName()==name:return node
            children=node.children()
            if hasattr(node,"childItems"):children+=node.childItems()
            for child in children:
                found=visit(child)
                if found:return found
            return None
        return visit(self.root)

    def hover_caption(self):
        caption=self.find("domainosThumbnailCaption")
        point=caption.mapToItem(self.root,QPointF(caption.width()/2,caption.height()/2))
        QTest.mouseMove(self.view,point.toPoint());self.app.processEvents()
        return caption

    def test_elided_caption_waits_then_shows_literal_text_with_bounded_height(self):
        caption=self.hover_caption();popup=self.find("domainosThumbnailCaptionTooltip")
        self.assertTrue(caption.property("truncated"));self.assertFalse(popup.property("visible"))
        QTest.qWait(max(1,self.delay//3));self.assertFalse(popup.property("visible"))
        QTest.qWait(self.delay+80);self.assertTrue(popup.property("visible"))
        text=self.find("domainosThumbnailCaptionHintText")
        self.assertEqual(text.property("text"),"Literal <title> & "+"long title "*300)
        self.assertEqual(QQmlExpression(qmlContext(text),text,"textFormat===0").evaluate(),(True,False))
        self.assertLessEqual(popup.property("height"),caption.y()-8)
        self.assertLessEqual(popup.property("y")+popup.property("height"),0)
        QTest.mouseMove(self.view,QPoint(310,250));QTest.qWait(50)
        self.assertFalse(popup.property("visible"))

    def test_short_caption_does_not_repeat_visible_title(self):
        self.preview.setProperty("windowRecords",[{"key":"owned","pid":701,"title":"Short title","windowIds":[]}])
        QTest.qWait(30);caption=self.hover_caption()
        self.assertFalse(caption.property("truncated"));QTest.qWait(self.delay+80)
        self.assertFalse(self.find("domainosThumbnailCaptionTooltip").property("visible"))

    def test_caption_hint_respects_user_off_and_parent_close(self):
        self.preview.setProperty("previewsEnabled",False)
        self.preview.setProperty("hintsEnabled",False);self.hover_caption();QTest.qWait(self.delay+80)
        popup=self.find("domainosThumbnailCaptionTooltip");self.assertFalse(popup.property("visible"))
        QTest.mouseMove(self.view,QPoint(310,250));self.preview.setProperty("previewsEnabled",True)
        self.hover_caption();QTest.qWait(self.delay+80);self.assertTrue(popup.property("visible"))
        self.preview.setProperty("tooltipVisible",False);QTest.qWait(40)
        self.assertFalse(popup.property("visible"))


if __name__ == "__main__":
    unittest.main()
