# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Package integrity and native task actions without touching a desktop session."""

import hashlib
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


PLASMA = Path(__file__).resolve().parents[1]
PACKAGE = PLASMA / "applets" / "org.irixclassic.iconbox"

try:
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtQml import QJSEngine
except ImportError:
    QCoreApplication = QJSEngine = None


class PackageIntegrityTests(unittest.TestCase):
    def test_complete_native_package_and_unchanged_interactions(self):
        origin = json.loads((PACKAGE / "ORIGEM.json").read_text())
        adapted = {
            "metadata.json", "contents/config/main.xml", "contents/ui/main.qml",
            "contents/ui/Task.qml", "contents/ui/TaskList.qml",
            "contents/ui/ConfigAppearance.qml", "contents/ui/GroupExpanderOverlay.qml",
            "contents/ui/code/layoutmetrics.js", "contents/ui/code/tools.js",
        }
        for name, digest in origin["upstream"]["files_sha256"].items():
            with self.subTest(name=name):
                path = PACKAGE / name
                self.assertTrue(path.is_file(), "Native component missing from package")
                if name not in adapted:
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest,
                                     "Native menus, gestures or previews changed unexpectedly")

    def test_every_referenced_configuration_key_is_declared(self):
        document = ET.parse(PACKAGE / "contents/config/main.xml")
        keys = {entry.attrib["name"] for entry in document.findall(
            ".//{http://www.kde.org/standards/kcfg/1.0}entry")}
        referenced = set()
        for path in (PACKAGE / "contents").rglob("*"):
            if path.suffix in (".qml", ".js"):
                referenced.update(re.findall(
                    r"(?:Plasmoid|plasmoid)\.configuration\.(\w+)", path.read_text()))
        self.assertFalse(referenced - keys, "A copied native option has no configuration entry")

    def test_standalone_qml_package_does_not_replace_native_taskmanager(self):
        metadata = json.loads((PACKAGE / "metadata.json").read_text())
        self.assertEqual(metadata["KPlugin"]["Id"], PACKAGE.name)
        self.assertEqual(metadata["KPackageStructure"], "Plasma/Applet")
        self.assertNotIn("X-Plasma-Library", metadata)
        self.assertFalse(any(PACKAGE.rglob("*.so")))


@unittest.skipIf(QJSEngine is None, "PyQt6 needed to execute the real task dispatcher")
class NativeActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.engine = QJSEngine()
        source = (PACKAGE / "contents/ui/code/tools.js").read_text()
        source = re.sub(r"^\.(?:pragma|import).*\n", "", source, flags=re.MULTILINE)
        self.evaluate(source)
        self.evaluate("""
            var Qt = {ShiftModifier: 1};
            var PlasmaCore = {Types: {LeftEdge: 1, TopEdge: 2, RightEdge: 3, BottomEdge: 4}};
            var actions = [];
            var childIds = ["first", "second"];
            var childData = {
                first: {active: false, stacking: 10}, second: {active: false, stacking: 20}
            };
            var TaskManager = {AbstractTasksModel: {IsActive: "active", StackingOrder: "stacking"}};
            var model = {IsGroupParent: false, IsMinimized: false, IsActive: false, WinIdList: [11]};
            var plasmoid = {configuration: {minimizeActiveTaskOnClick: true, groupedTaskVisualization: 0}};
            var task = {
                index: 0,
                modelIndex: function() { return "task"; },
                hideToolTip: function() { actions.push(["hideTooltip"]); },
                hideImmediately: function() { actions.push(["hideImmediately"]); },
                showToolTip: function() { actions.push(["showTooltip"]); },
                updateMainItemBindings: function() { actions.push(["updateTooltip"]); }
            };
            var tasks = {
                toolTipOpenedByClick: null, groupDialog: null,
                activateWindowView: function(ids) { actions.push(["windowView", ids]); },
                backend: {globalRect: function() { return "rect"; }},
                tasksModel: {
                    requestActivate: function(id) { actions.push(["activate", id]); },
                    requestToggleMinimized: function(id) { actions.push(["toggleMinimized", id]); },
                    requestNewInstance: function(id) { actions.push(["newInstance", id]); },
                    requestPublishDelegateGeometry: function(id) { actions.push(["geometry", id]); },
                    rowCount: function() { return childIds.length; },
                    makeModelIndex: function(parent, child) { return childIds[child]; },
                    data: function(id, role) { return childData[id][role]; }
                }
            };
        """)

    def evaluate(self, script):
        value = self.engine.evaluate(script)
        self.assertFalse(value.isError(), value.toString())
        return value

    def activate(self, setup="", modifiers=0, window_view=False):
        self.evaluate(setup)
        self.evaluate(f"activateTask('task', model, {modifiers}, task, plasmoid, tasks, "
                      f"{str(window_view).lower()});")
        return json.loads(self.evaluate("JSON.stringify(actions)").toString())

    def test_window_activation_is_immediate(self):
        self.assertEqual(self.activate(), [["activate", "task"]])

    def test_minimized_window_restores_before_activation(self):
        self.assertEqual(self.activate("model.IsMinimized = true;"),
                         [["toggleMinimized", "task"], ["activate", "task"]])

    def test_active_window_minimizes_only_when_configured(self):
        self.assertEqual(self.activate("model.IsActive = true;"), [["toggleMinimized", "task"]])
        self.evaluate("actions = []; plasmoid.configuration.minimizeActiveTaskOnClick = false;")
        self.assertEqual(self.activate(), [["activate", "task"]])

    def test_shift_click_launches_new_instance(self):
        self.assertEqual(self.activate(modifiers=1), [["newInstance", "task"]])

    def test_group_activates_most_recent_window(self):
        self.assertEqual(self.activate("model.IsGroupParent = true;"), [["activate", "second"]])

    def test_group_cycles_from_current_window(self):
        self.assertEqual(self.activate("model.IsGroupParent = true; childData.second.active = true;"),
                         [["activate", "first"]])

    def test_group_window_view_keeps_native_request(self):
        self.assertEqual(self.activate("model.IsGroupParent = true; "
                                       "plasmoid.configuration.groupedTaskVisualization = 2;",
                                       window_view=True),
                         [["hideTooltip"], ["windowView", [11]]])

    def test_pressed_lookup_preserves_base_state_fallback(self):
        for state in ("normal", "focus", "minimized", "attention"):
            with self.subTest(state=state):
                prefixes = json.loads(self.evaluate(
                    f"JSON.stringify(taskPrefixPressed('{state}', PlasmaCore.Types.BottomEdge))").toString())
                # The state's own pressed artwork wins, followed by general pressed
                # and then its original state, so skins without new artwork still render.
                self.assertEqual(prefixes[:2], [f"south-{state}-pressed", f"{state}-pressed"])
                self.assertLess(prefixes.index("pressed"), prefixes.index(state))


if __name__ == "__main__":
    unittest.main()
