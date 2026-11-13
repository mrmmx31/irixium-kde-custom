#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inject provider failures into the production QML task snapshot controller."""
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"
_private = tempfile.TemporaryDirectory(prefix=".qa-domainos-refresh-", dir=ROOT)
for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR"):
    path = Path(_private.name) / key.lower()
    path.mkdir(mode=0o700)
    os.environ[key] = str(path)
os.environ.update(QT_QPA_PLATFORM="offscreen", QML_DISABLE_DISK_CACHE="1")

from PyQt6.QtCore import QCoreApplication, QMetaObject, QObject, QUrl, Qt, qInstallMessageHandler
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlComponent, QQmlEngine


class RefreshFailure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.messages = []
        self.previous_handler = qInstallMessageHandler(lambda kind, context, message: self.messages.append(message))
        self.engine = QQmlEngine()
        self.component = QQmlComponent(self.engine)
        source = ('''import QtQuick
import org.kde.taskmanager as TaskManager
import "''' + UI.as_uri() + '''" as Production
Item {
    id:fixture
    property alias controller: tasks
    property alias scope: scope
    property alias visibleTasks: visibleTasks
    property bool reenterOnCommit:false
    property int reports:0
    property string reportCode:""
    component Provider: QtObject {
        property int count:2
        property int revision:1
        property string fault:""
        property int indexReads:0
        property int dataReads:0
        function makeModelIndex(row) {
            ++indexReads
            if (fault==="count" && indexReads>count) throw new Error("PRIVATE counting failure")
            return row
        }
        function data(index,role) {
            ++dataReads
            if (fault==="records") throw new Error("PRIVATE window title during record read")
            const roles=TaskManager.AbstractTasksModel
            if (role===roles.IsWindow) return true
            if (role===roles.IsGroupParent) return false
            if (role===roles.WinIdList) return [index+1]
            if (role===roles.AppPid) return 701+index
            if (role===Qt.DisplayRole) return "Window "+revision+"/"+index
            if (role===roles.AppId) return "owned.app"
            return null
        }
    }
    Provider {id:scope; objectName:"scopeProvider"}
    Provider {id:visibleTasks; objectName:"visibleProvider"}
    Production.DomainOSTasks {
        id:tasks; nativeEnabled:false; scopeModel:scope; tasksModel:visibleTasks
        onRefreshFailed:code=>{++fixture.reports;fixture.reportCode=code}
        onWindowRowsChanged:if (fixture.reenterOnCommit) tasks.refresh()
    }
    function prepareSelection() {
        tasks.refresh()
        tasks.selectTask("window:1",0)
        tasks.setMemberSelected("window:1",true)
        tasks.groupSelectorKey="window:1"
    }
    function resetReads() {scope.indexReads=0;scope.dataReads=0;visibleTasks.indexReads=0;visibleTasks.dataReads=0}
    function refreshNow() {resetReads();tasks.refresh()}
}''')
        self.fixture_file = Path(_private.name) / "refresh-failure-fixture.qml"
        self.fixture_file.write_text(source)
        self.component.loadUrl(QUrl.fromLocalFile(str(self.fixture_file)))
        self.fixture = self.component.create()
        self.assertIsNotNone(self.fixture, "\n".join(e.toString() for e in self.component.errors()))
        self.tasks = self.fixture.property("controller")
        self.scope = self.fixture.findChild(QObject, "scopeProvider")
        self.visible_tasks = self.fixture.findChild(QObject, "visibleProvider")
        self.app.processEvents()
        self.invoke("prepareSelection")
        self.app.processEvents()

    def tearDown(self):
        if self.fixture is not None:
            self.fixture.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, 0)
        self.app.processEvents()
        qInstallMessageHandler(self.previous_handler)

    def invoke(self, method):
        QMetaObject.invokeMethod(self.fixture, method, Qt.ConnectionType.DirectConnection)

    def snapshot(self):
        return self.fixture.property("controller").property("windowRows").toVariant(), {
            name: self.variant(self.tasks.property(name)) for name in (
                "taskRows", "scopedWindowCount", "identityUnavailableCount", "selectedKeys",
                "selectedIdentities", "memberSelectionKeys", "anchorKey", "groupSelectorKey")}

    @staticmethod
    def variant(value):
        return value.toVariant() if hasattr(value, "toVariant") else value

    def assert_preserved_failure_and_recovery(self, provider, fault):
        previous = self.snapshot()
        provider.setProperty("revision", 2)
        provider.setProperty("fault", fault)
        self.invoke("refreshNow")
        self.assertFalse(self.tasks.property("refreshing"))
        self.assertEqual(self.snapshot(), previous)
        self.assertEqual(self.tasks.property("refreshFailureCount"), 1)
        self.assertEqual(self.fixture.property("reports"), 1)
        self.assertEqual(self.fixture.property("reportCode"), "task-model-unavailable")
        reads = (provider.property("indexReads"), provider.property("dataReads"))
        self.app.processEvents()
        self.assertEqual((provider.property("indexReads"), provider.property("dataReads")), reads,
                         "A failed read must not immediately retry")
        provider.setProperty("fault", "")
        self.invoke("refreshNow")
        self.assertFalse(self.tasks.property("refreshing"))
        self.assertEqual(self.tasks.property("refreshFailureCount"), 0)
        self.assertNotEqual(self.snapshot(), previous)
        self.assertEqual(self.variant(self.tasks.property("selectedKeys")), ["window:1"])
        self.assertEqual(self.variant(self.tasks.property("selectedIdentities")), {"window:1": 701})
        self.assertFalse(any("PRIVATE" in message for message in self.messages))

    def test_scope_record_failure_preserves_snapshot_and_recovers(self):
        self.assert_preserved_failure_and_recovery(self.scope, "records")

    def test_scope_counting_failure_preserves_snapshot_and_recovers(self):
        self.assert_preserved_failure_and_recovery(self.scope, "count")

    def test_visible_record_failure_preserves_entire_snapshot_and_recovers(self):
        self.assert_preserved_failure_and_recovery(self.visible_tasks, "records")

    def test_repeated_fault_has_one_report_until_successful_refresh(self):
        self.scope.setProperty("fault", "records")
        for _ in range(50):
            self.invoke("refreshNow")
            self.assertFalse(self.tasks.property("refreshing"))
        self.assertEqual(self.tasks.property("refreshFailureCount"), 50)
        self.assertEqual(self.fixture.property("reports"), 1)
        warnings = [message for message in self.messages if "task snapshot refresh failed" in message]
        self.assertEqual(len(warnings), 1)
        self.scope.setProperty("fault", "")
        self.invoke("refreshNow")
        self.scope.setProperty("fault", "records")
        self.invoke("refreshNow")
        self.assertEqual(self.fixture.property("reports"), 2)
        self.assertFalse(any("PRIVATE" in message for message in self.messages))

    def test_reentrant_refresh_from_publication_does_not_read_provider_twice(self):
        self.invoke("refreshNow")
        reads = (self.scope.property("indexReads"), self.scope.property("dataReads"))
        self.fixture.setProperty("reenterOnCommit", True)
        self.invoke("refreshNow")
        self.assertFalse(self.tasks.property("refreshing"))
        self.assertEqual((self.scope.property("indexReads"), self.scope.property("dataReads")), reads)
        self.assertEqual(self.fixture.property("reports"), 0)


if __name__ == "__main__":
    unittest.main()
