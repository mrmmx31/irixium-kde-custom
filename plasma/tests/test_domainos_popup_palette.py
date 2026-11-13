#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise scoped popup colors with the installed KDE Controls style.

Run under an owned D-Bus/XDG session. Inject explicit role objects into each
local scope; QApplication's palette is never assigned. Native KDE Apply is a
separate integration proof. The panel remains blue to detect inheritance leaks.
"""
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "org.kde.desktop"
os.environ["QML_DISABLE_DISK_CACHE"] = "1"

from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtQuick import QQuickItem
from PyQt6.QtWidgets import QApplication

UI = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel/contents/ui"
ROLES = {"window": "#c1c1c1", "windowText": "#000000", "base": "#9ebfbf",
         "text": "#102030", "button": "#999999", "buttonText": "#203040",
         "highlight": "#78a0a0", "highlightedText": "#000000", "disabledText": "#515253"}
QML = '''import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import UI_LOCATION as DomainOS
Window {
    id: root
    visible: true
    width: 800
    height: 450
    Kirigami.Theme.inherit: false
    Kirigami.Theme.backgroundColor: "#7894a7"
    Kirigami.Theme.textColor: "#ffffff"
    property alias roles: roles
    QtObject {
        id: roles
        property color window: "#c1c1c1"
        property color windowText: "#000000"
        property color base: "#9ebfbf"
        property color text: "#102030"
        property color button: "#999999"
        property color buttonText: "#203040"
        property color highlight: "#78a0a0"
        property color highlightedText: "#000000"
        property color disabledText: "#515253"
    }
    property alias menuScope: menuScope
    property alias viewScope: viewScope
    property alias buttonScope: buttonScope
    property alias button: button
    property alias view: view
    property alias menu: menu
    property alias dialog: dialog
    readonly property color panelColor: Kirigami.Theme.backgroundColor
    readonly property color menuSurface: menu.background.color
    readonly property color menuText: menu.itemAt(0).Kirigami.Theme.textColor
    readonly property color menuSelection: menu.itemAt(0).Kirigami.Theme.highlightColor
    readonly property color submenuSurface: submenu.background.color
    readonly property color submenuText: submenu.itemAt(0).Kirigami.Theme.textColor
    readonly property color nestedSurface: nested.background.color
    readonly property color viewColor: view.color
    readonly property color viewSurface: view.Kirigami.Theme.backgroundColor
    readonly property color buttonSurface: button.Kirigami.Theme.backgroundColor
    readonly property color buttonText: button.Kirigami.Theme.textColor
    readonly property color buttonDisabledText: button.Kirigami.Theme.disabledTextColor
    readonly property color selectionSurface: selection.Kirigami.Theme.backgroundColor
    readonly property color selectionText: selection.Kirigami.Theme.textColor
    readonly property color tooltipSurface: tooltip.Kirigami.Theme.backgroundColor
    readonly property color tooltipText: tooltip.Kirigami.Theme.textColor
    readonly property color nativeAlternate: view.Kirigami.Theme.alternateBackgroundColor
    property int requestedViewGroup: Kirigami.Theme.Active
    readonly property int viewGroup: view.Kirigami.Theme.colorGroup
    Controls.Menu {
        id: menu; objectName: "testMenu"
        Controls.MenuItem { text: "Help" }
        Controls.MenuItem { text: "Session" }
        Controls.Menu {
            id: submenu; title: "More"
            Controls.MenuItem { text: "Nested" }
            Controls.Menu { id: nested; title: "Details"; Controls.MenuItem { text: "Last" } }
        }
    }
    DomainOS.DomainOSPopupPlacement { popup: menu }
    DomainOS.DomainOSControlPalette { id: menuScope; target: menu.background }
    Controls.Dialog { id: dialog; width: 230; title: "Scoped dialog" }
    DomainOS.DomainOSPopupPlacement { popup: dialog }
    Controls.TextField { id: view; text: "Search"; Kirigami.Theme.colorGroup: root.requestedViewGroup }
    DomainOS.DomainOSControlPalette { id: viewScope; target: view }
    Item { id: selection; Kirigami.Theme.colorSet: Kirigami.Theme.Selection }
    DomainOS.DomainOSControlPalette { target: selection }
    Item { id: tooltip; Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip }
    DomainOS.DomainOSControlPalette { target: tooltip }
    Controls.Button { id: button; text: "Back" }
    DomainOS.DomainOSControlPalette { id: buttonScope; target: button }
}
'''.replace("UI_LOCATION", json.dumps(QUrl.fromLocalFile(str(UI)).toString()))


class PopupPalette(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.saved = cls.app.palette()

    def setUp(self):
        self.engine = QQmlEngine()
        self.component = QQmlComponent(self.engine)
        self.component.setData(QML.encode(), QUrl.fromLocalFile(str(UI / "palette-test.qml")))
        self.root = self.component.create()
        self.assertIsNotNone(self.root, [error.toString() for error in self.component.errors()])
        self.settle()
        def observed_objects(obj, seen):
            if obj is None or obj in seen:
                return []
            seen.add(obj)
            children = obj.children()
            if isinstance(obj, QQuickItem):
                children += obj.childItems()
            return [obj] + [child for item in children for child in observed_objects(item, seen)]
        self.scopes = [obj for obj in observed_objects(self.root, set())
                       if "DomainOSControlPalette" in obj.metaObject().className()]
        self.assertGreaterEqual(len(self.scopes), 11)
        roles = self.root.property("roles")
        for scope in self.scopes:
            self.assertTrue(scope.setProperty("colors", roles))
        self.settle()

    def tearDown(self):
        self.root.deleteLater()
        self.engine.deleteLater()
        self.settle()

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    def color(self, name):
        return self.root.property(name).name()

    def test_menu_background_and_text_follow_injected_native_roles(self):
        self.assertEqual(self.color("menuSurface"), ROLES["window"])
        self.assertEqual(self.color("menuText"), ROLES["windowText"])
        self.assertEqual(self.color("menuSelection"), ROLES["highlight"])

    def test_view_and_button_keep_their_own_roles(self):
        self.assertEqual(self.color("viewSurface"), ROLES["base"])
        self.assertEqual(self.color("viewColor"), ROLES["text"])
        self.assertEqual(self.color("buttonSurface"), ROLES["button"])
        self.assertEqual(self.color("buttonText"), ROLES["buttonText"])

    def test_submenu_windows_use_the_same_injected_roles(self):
        self.assertEqual(self.color("submenuSurface"), ROLES["window"])
        self.assertEqual(self.color("submenuText"), ROLES["windowText"])
        self.assertEqual(self.color("nestedSurface"), ROLES["window"])

    def test_disabled_text_uses_explicit_native_role_without_forcing_group(self):
        self.root.setProperty("requestedViewGroup", 2)  # Kirigami.Theme.Inactive
        self.settle()
        self.assertEqual(self.root.property("viewGroup"), 2)
        self.assertEqual(self.color("buttonDisabledText"), ROLES["disabledText"])
        self.assertEqual(self.color("menuSurface"), ROLES["window"])

    def test_color_change_updates_without_reopening(self):
        roles = self.root.property("roles")
        for name, value in {"window": "#ddd074", "base": "#31234a", "highlight": "#f0b030"}.items():
            self.assertTrue(roles.setProperty(name, value))
        self.settle()
        self.assertEqual(self.color("menuSurface"), "#ddd074")
        self.assertEqual(self.color("viewSurface"), "#31234a")
        self.assertEqual(self.color("menuSelection"), "#f0b030")

    def test_selection_uses_selected_surface_and_text_roles(self):
        self.assertEqual(self.color("selectionSurface"), ROLES["highlight"])
        self.assertEqual(self.color("selectionText"), ROLES["highlightedText"])

    def test_unexposed_tooltip_and_alternate_roles_keep_native_values(self):
        before = tuple(self.color(name) for name in ("tooltipSurface", "tooltipText", "nativeAlternate"))
        self.root.property("roles").setProperty("window", "#884411")
        self.root.property("roles").setProperty("base", "#332255")
        self.settle()
        self.assertEqual(tuple(self.color(name) for name in ("tooltipSurface", "tooltipText", "nativeAlternate")), before)

    def test_scope_does_not_recolor_panel_or_change_control_geometry(self):
        self.assertEqual(self.color("panelColor"), "#7894a7")
        self.assertEqual(self.root.property("dialog").property("width"), 230)
        self.assertEqual(self.root.property("menu").property("count"), 3)

    def test_helper_has_no_input_or_action_delay(self):
        source = (UI / "DomainOSControlPalette.qml").read_text()
        self.assertNotIn("Timer", source)
        self.assertNotIn("MouseArea", source)
        self.assertNotIn("writeConfig", source)
        self.assertNotIn("SystemPalette", source)
        self.assertEqual(self.app.palette(), self.saved)


if __name__ == "__main__":
    unittest.main()
