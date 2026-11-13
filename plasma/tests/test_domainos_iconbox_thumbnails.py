#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the production Iconbox when preview mode cannot supply frames."""
import json
import os
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ["QT_QPA_PLATFORMTHEME"] = "generic"
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
os.environ["QML_DISABLE_DISK_CACHE"] = "1"
_private = tempfile.TemporaryDirectory(prefix=".qa-domainos-iconbox-thumbnails-",
                                       dir=Path(__file__).resolve().parents[2])
for _variable in ("HOME", "TMPDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
                  "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR"):
    _path = Path(_private.name) / _variable.lower()
    _path.mkdir(mode=0o700)
    os.environ[_variable] = str(_path)
os.environ["XDG_DATA_DIRS"] = "/usr/local/share:/usr/share"
os.environ["XDG_CONFIG_DIRS"] = "/etc/xdg"
_theme = Path(os.environ["XDG_DATA_HOME"]) / "plasma/desktoptheme/IrixClassicDomainOS"
_theme.parent.mkdir(parents=True)
_theme.symlink_to(Path(__file__).resolve().parents[1] / "IrixClassicDomainOS",
                  target_is_directory=True)

from PyQt6.QtCore import QMetaObject, QUrl, Qt, QPointF, Q_RETURN_ARG
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtTest import QTest
from PyQt6 import sip

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "plasma/tests/DomainOSIconboxPreview.qml"


class IconboxThumbnailMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.engine = QQmlApplicationEngine()
        cls.engine.load(QUrl.fromLocalFile(str(FIXTURE)))
        root = cls.engine.rootObjects()[0] if cls.engine.rootObjects() else None
        if not root:
            raise RuntimeError("Production Iconbox fixture did not load")
        cls.window = sip.cast(root, QQuickWindow)
        cls.box = cls.window.property("iconbox")
        cls.window.show()
        cls.settle()

    @classmethod
    def tearDownClass(cls):
        cls.window.close()
        cls.engine.deleteLater()
        cls.app.processEvents()
        _private.cleanup()

    @classmethod
    def settle(cls):
        cls.app.processEvents()
        QTest.qWait(40)
        cls.app.processEvents()

    @classmethod
    def descendants(cls, item):
        for child in item.childItems():
            yield child
            yield from cls.descendants(child)

    @classmethod
    def named(cls, object_name):
        result = next((item for item in cls.descendants(cls.window.contentItem())
                       if item.objectName() == object_name and item.window() is not None), None)
        if result is None:
            raise AssertionError("Missing QML item: " + object_name)
        return result

    def invoke(self, item, method):
        QMetaObject.invokeMethod(item, method, Qt.ConnectionType.DirectConnection)
        self.settle()

    def set_mode(self, previews):
        self.box.setProperty("thumbnailsEnabled", previews)
        self.box.setProperty("hintsEnabled", not previews)
        self.settle()

    def test_unavailable_group_cards_stay_clickable_in_the_real_iconbox(self):
        self.set_mode(True)
        tile = self.named("domainosLiveTask_group:terminal")
        preview = self.named("domainosTaskThumbnails_group:terminal")
        icon = self.named(tile.objectName() + "Icon")
        label = self.named(tile.objectName() + "LabelText")
        self.invoke(preview, "showToolTip")

        contents = preview.property("contentsLoader").property("item")
        cards = [item for item in self.descendants(contents)
                 if item.objectName() == "domainosThumbnailCard"]
        self.assertEqual(len(cards), 3)
        self.assertTrue(preview.property("tooltipVisible"))
        for card in cards:
            self.assertEqual(card.height(), 178)
            self.assertFalse(card.property("liveAvailable"))
            self.assertIn("indisponível", card.property("unavailableReason"))

        target = cards[0].property("modelData").toVariant()
        self.assertTrue(target["key"].startswith("window:"))
        self.assertTrue(any(child.objectName() == "domainosThumbnailPointer"
                            for child in self.descendants(cards[0])))
        point = cards[0].mapToScene(QPointF(cards[0].width() / 2,
                                            cards[0].height() / 2)).toPoint()
        QTest.mouseClick(cards[0].window(), Qt.MouseButton.LeftButton, pos=point)
        self.settle()
        raw = QMetaObject.invokeMethod(self.window, "uiState",
                                       Qt.ConnectionType.DirectConnection,
                                       Q_RETURN_ARG("QVariant"))
        state = json.loads(str(raw))
        self.assertEqual(state["requests"][-1]["action"], "activate")
        self.assertEqual(state["requests"][-1]["ids"], target["windowIds"])

        self.set_mode(False)
        self.invoke(preview, "showToolTip")
        self.assertTrue(preview.property("tooltipVisible"))
        self.assertIsNone(preview.property("contentsLoader").property("item"))
        self.assertTrue(tile.isVisible())
        self.assertTrue(icon.isVisible())
        self.assertEqual(label.property("text"), tile.property("record").toVariant()["title"])
        self.assertIs(self.named(tile.objectName() + "Icon"), icon)

        # Moving over the same tile in title mode must keep the icon and label
        # intact, with no thumbnail provider or stale preview card attached.
        position = tile.mapToScene(QPointF(tile.width() / 2, tile.height() / 2)).toPoint()
        QTest.mouseMove(self.window, position)
        self.settle()
        self.assertTrue(icon.isVisible())
        self.assertEqual(label.property("text"), tile.property("record").toVariant()["title"])
        self.assertIsNone(preview.property("contentsLoader").property("item"))
        self.assertFalse(preview.property("providersLoaded"))


if __name__ == "__main__":
    unittest.main()
