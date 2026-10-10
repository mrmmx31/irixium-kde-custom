#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Own operations popup with real Qt close transitions and task model doubles.

Qt input/Popup.Window lifecycle is real, offscreen and isolated. Window jobs
are deliberately recorded by the existing fixture, not native compositor jobs.
"""
import json
import unittest

# Existing fixture isolates HOME/XDG/cache/runtime and disables both buses.
import test_domainos_middle_click as setup
from PyQt6 import sip
from PyQt6.QtCore import QEvent, QObject, QPointF, QUrl, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication


FIXTURE = '''import QtQuick
import "''' + (setup.ROOT / 'plasma/tests').as_uri() + '''"
DomainOSIconboxPreview {
 id:fixture
 property var picker:null
 property var observations:[]
 property var captured:[]
 Transition {
  id:slowExit
  NumberAnimation { property:"opacity";duration:140;to:0 }
 }
 function prepare() {
  resetUi();addGeometryBackend();controller.groupingMode=1
  observations=[];captured=[];iconbox.operationsOpened=0
 }
 function showGroup(slow) {
  picker.exit=slow ? slowExit : null
  return iconbox.selectRecord(controller.taskFor("group:terminal"),0,
      iconbox.buttonForKey("group:terminal"))
 }
 function selectTwo() {
  controller.setMemberSelected("window:1",true)
  controller.setMemberSelected("window:3",true)
 }
 function finish() { controller.finishGroupSelection(true) }
 function capture() { captured=controller.selectedWindows().slice() }
 function submitCaptured() { return iconbox.openOperations(captured) }
 function cancel() { iconbox.cancelPendingOperations() }
 function nullOwner() { return iconbox.batchContextMenu.openAt(null) }
 function snapshot() {
  return JSON.stringify({selected:controller.selectedKeys,
   group:iconbox.groupPopupVisible,operations:iconbox.operationsMenuVisible,
   modifierArmed:iconbox.modifierSelectionArmed,
   opened:iconbox.operationsOpened,pending:iconbox.pendingOperations.map(row=>({key:row.key,pid:row.pid})),
   waiting:iconbox.waitingOperationsPopups.length,generation:iconbox.operationsGeneration,
   menuSelection:iconbox.menuSelection.map(row=>({key:row.key,pid:row.pid})),
   error:iconbox.lastError,requests:requests,layouts:layouts,
   observations:observations})
 }
 Connections {
  target:fixture.iconbox.batchContextMenu
  function onAboutToShow() {
   fixture.observations=fixture.observations.concat([{event:"operations-about-to-show",
       group:fixture.iconbox.groupPopupVisible,waiting:fixture.iconbox.waitingOperationsPopups.length}])
  }
  function onOpened() { fixture.observations=fixture.observations.concat([{event:"operations-opened"}]) }
 }
}
'''


class OperationsHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.engine = QQmlApplicationEngine()
        self.diagnostics = []
        self.engine.warnings.connect(lambda rows:self.diagnostics.extend(row.toString() for row in rows))
        path=setup.Path(setup._private.name)/'operations-handoff.qml'
        path.write_text(FIXTURE)
        self.engine.load(QUrl.fromLocalFile(str(path)))
        self.assertTrue(self.engine.rootObjects(),'\n'.join(self.diagnostics))
        self.window=sip.cast(self.engine.rootObjects()[0],QQuickWindow)
        picker=self.window.findChild(QObject,'domainosGroupPicker')
        self.assertIsNotNone(picker)
        self.window.setProperty('picker',picker)
        self.engine.globalObject().setProperty('fixture',self.engine.newQObject(self.window))
        self.evaluate('fixture.prepare()')
        self.settle(30)

    def tearDown(self):
        self.evaluate('fixture.cancel();fixture.closeMenus();fixture.picker.exit=null;fixture.picker.close()')
        self.window.close()
        self.engine.deleteLater()
        self.app.processEvents()
        self.assertFalse(self.diagnostics,'\n'.join(self.diagnostics))

    def settle(self,milliseconds=15):
        self.app.processEvents()
        QTest.qWait(milliseconds)
        self.app.processEvents()

    def evaluate(self,expression):
        result=self.engine.evaluate(expression)
        self.assertFalse(result.isError(),result.toString())
        return result.toVariant()

    def state(self):
        return json.loads(self.evaluate('fixture.snapshot()'))

    @staticmethod
    def descend(item):
        yield item
        for child in item.childItems():
            yield from OperationsHandoff.descend(child)

    def item(self,name):
        for owner in self.app.allWindows():
            if not isinstance(owner,QQuickWindow) or not owner.isVisible():continue
            for item in self.descend(owner.contentItem()):
                if item.objectName()==name:return item
        self.fail('Missing visible own item '+name)

    def click(self,name,modifiers=Qt.KeyboardModifier.NoModifier):
        item=self.item(name)
        owner=item.window()
        point=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
        QTest.mouseClick(owner,Qt.MouseButton.LeftButton,modifiers,point)
        self.settle()

    def wait_for_operations(self):
        for _ in range(40):
            if self.state()['operations']:return self.state()
            self.settle(10)
        self.fail(json.dumps(self.state()))

    def test_footer_pointer_opens_once_after_synchronous_close(self):
        self.click('domainosLiveTask_group:terminal')
        self.click('domainosGroupMember_window:1')
        self.click('domainosGroupMember_window:3')
        self.click('domainosGroupOrganize')
        state=self.wait_for_operations()
        self.assertEqual(state['selected'],['window:1','window:3'])
        self.assertEqual(state['opened'],1)
        self.assertFalse(state['group'])
        self.assertFalse(state['pending'])
        self.assertFalse(state['waiting'])
        self.assertFalse(state['requests'])
        self.assertFalse(state['layouts'])
        shown=next(row for row in state['observations'] if row['event']=='operations-about-to-show')
        self.assertFalse(shown['group'])
        self.assertEqual(shown['waiting'],0)

    def test_ctrl_release_after_pointer_selection_opens_operations_once(self):
        self.evaluate('fixture.controller.groupingMode=0')
        self.settle()
        QTest.keyPress(self.window,Qt.Key.Key_Control)
        self.click('domainosLiveTask_window:6',Qt.KeyboardModifier.ControlModifier)
        self.click('domainosLiveTask_window:7',Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.state()['selected'],['window:6','window:7'])
        self.assertFalse(self.state()['operations'])
        QTest.keyRelease(self.window,Qt.Key.Key_Control)
        state=self.wait_for_operations()
        self.assertEqual(state['opened'],1)
        self.assertEqual(state['selected'],['window:6','window:7'])
        self.assertFalse(state['requests'])
        self.assertFalse(state['layouts'])
        self.evaluate('fixture.iconbox.batchContextMenu.close()')
        self.settle()
        QTest.keyClick(self.window,Qt.Key.Key_Control)
        self.settle()
        self.assertFalse(self.state()['operations'])
        self.assertEqual(self.state()['opened'],1)

    def test_ctrl_and_shift_wait_for_last_release_and_open_only_once(self):
        self.evaluate('fixture.controller.groupingMode=0')
        self.settle()
        QTest.keyPress(self.window,Qt.Key.Key_Control)
        QTest.keyPress(self.window,Qt.Key.Key_Shift)
        modifiers=Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier
        self.click('domainosLiveTask_window:1',modifiers)
        self.click('domainosLiveTask_window:3',modifiers)
        self.assertEqual(self.state()['selected'],['window:1','window:2','window:3'])
        self.assertFalse(self.state()['operations'])
        # QTest's modifier argument presses/releases those additional keys,
        # which would release Ctrl as well. Deliver the actual Shift release
        # state so this case exercises keeping Ctrl held until its own release.
        QApplication.sendEvent(self.window,QKeyEvent(QEvent.Type.KeyRelease,
            Qt.Key.Key_Shift,Qt.KeyboardModifier.ControlModifier))
        self.settle()
        self.assertFalse(self.state()['operations'])
        QTest.keyRelease(self.window,Qt.Key.Key_Control)
        state=self.wait_for_operations()
        self.assertEqual(state['opened'],1)
        self.assertEqual(state['selected'],['window:1','window:2','window:3'])
        self.assertFalse(state['requests'])
        self.assertFalse(state['layouts'])

    def test_escape_closes_selector_without_changing_selection_or_windows(self):
        self.click('domainosLiveTask_group:terminal')
        before=self.state()
        self.assertTrue(before['group'])
        QTest.keyClick(self.window,Qt.Key.Key_Escape)
        self.settle()
        after=self.state()
        self.assertFalse(after['group'])
        self.assertFalse(after['operations'])
        self.assertEqual(after['selected'],before['selected'])
        self.assertFalse(after['requests'])
        self.assertFalse(after['layouts'])

    def test_popup_escape_cancels_armed_modifier_without_reopening_operations(self):
        self.click('domainosLiveTask_group:terminal',Qt.KeyboardModifier.ControlModifier)
        self.click('domainosGroupMember_window:1')
        self.click('domainosGroupMember_window:3')
        before=self.state()
        self.assertTrue(before['group'])
        self.assertTrue(before['modifierArmed'])
        owner=self.item('domainosGroupMember_window:1').window()
        QTest.keyClick(owner,Qt.Key.Key_Escape)
        self.settle()
        self.assertFalse(self.state()['group'])
        # Offscreen has no native modifier backend. Exercise its callback after
        # the real popup Escape, with the selection deliberately conserved.
        self.evaluate('fixture.iconbox.selectionModifiersReleased(0,Qt.Key_Control)')
        self.settle()
        after=self.state()
        self.assertFalse(after['modifierArmed'])
        self.assertFalse(after['operations'])
        self.assertEqual(after['opened'],0)
        self.assertEqual(after['selected'],before['selected'])
        self.assertFalse(after['requests'])
        self.assertFalse(after['layouts'])

    def test_real_exit_transition_retains_snapshot_until_closed(self):
        self.evaluate('fixture.showGroup(true);fixture.selectTwo();fixture.capture();fixture.finish()')
        before=self.state()
        self.assertTrue(before['group'])
        self.assertFalse(before['operations'])
        self.assertEqual(before['opened'],0)
        self.assertEqual(before['waiting'],1)
        self.assertEqual(before['pending'],[{'key':'window:1','pid':501},{'key':'window:3','pid':503}])
        after=self.wait_for_operations()
        self.assertEqual(after['opened'],1)
        self.assertEqual(after['menuSelection'],before['pending'])
        self.assertEqual(after['selected'],before['selected'])
        self.assertFalse(after['waiting'])
        self.assertFalse(after['pending'])
        shown=next(row for row in after['observations'] if row['event']=='operations-about-to-show')
        self.assertFalse(shown['group'])
        self.assertEqual(shown['waiting'],0)

    def test_cancel_invalidates_pending_and_late_closed_cannot_open(self):
        self.evaluate('fixture.showGroup(true);fixture.selectTwo();fixture.finish()')
        before=self.state()
        self.assertEqual(before['waiting'],1)
        self.evaluate('fixture.cancel()')
        self.settle(220)
        after=self.state()
        self.assertEqual(after['generation'],before['generation']+1)
        self.assertFalse(after['pending'])
        self.assertFalse(after['operations'])
        self.assertEqual(after['opened'],0)
        self.assertEqual(after['selected'],before['selected'])
        self.assertFalse(after['requests'])
        self.assertFalse(after['layouts'])

    def test_stale_pid_after_close_requested_never_opens_or_dispatches(self):
        self.evaluate('fixture.showGroup(true);fixture.selectTwo();fixture.finish();fixture.mutate(1,"pid",9901)')
        self.settle(220)
        state=self.state()
        self.assertFalse(state['pending'])
        self.assertFalse(state['operations'])
        self.assertEqual(state['opened'],0)
        self.assertTrue(state['error'])
        self.assertFalse(state['requests'])
        self.assertFalse(state['layouts'])

    def test_unavailable_parent_fails_explicitly_without_opened_count(self):
        self.evaluate('fixture.showGroup(false);fixture.selectTwo();fixture.iconbox.menuSelection=fixture.controller.selectedWindows()')
        self.assertFalse(self.evaluate('fixture.nullOwner()'))
        state=self.state()
        self.assertEqual(state['opened'],0)
        self.assertFalse(state['operations'])
        self.assertTrue(state['error'])

    def test_popup_rows_pointer_route_existing_exact_layout_request(self):
        self.evaluate('fixture.showGroup(false);fixture.selectTwo();fixture.finish()')
        self.wait_for_operations()
        self.click('domainosBatchColumns')
        state=self.state()
        self.assertFalse(state['operations'])
        self.assertEqual(state['opened'],1)
        self.assertEqual(len(state['layouts']),1)
        self.assertEqual(state['layouts'][0]['mode'],'columns')
        self.assertEqual({row['key'] for row in state['layouts'][0]['windows']},{'window:1','window:3'})
        self.assertEqual(state['selected'],['window:1','window:3'])

    def test_keyboard_focus_navigation_dispatches_only_chosen_layout(self):
        self.evaluate('fixture.showGroup(false);fixture.selectTwo();fixture.finish()')
        self.wait_for_operations()
        menu=self.window.property('iconbox').property('batchContextMenu')
        owner=self.item('domainosBatchColumns').window()
        self.assertEqual(menu.property('currentIndex'),1)
        QTest.keyClick(owner,Qt.Key.Key_Down)
        self.settle()
        self.assertEqual(menu.property('currentIndex'),3)
        QTest.keyClick(owner,Qt.Key.Key_Return)
        self.settle()
        state=self.state()
        self.assertFalse(state['operations'])
        self.assertEqual(len(state['layouts']),1)
        self.assertEqual(state['layouts'][0]['mode'],'columns')


if __name__=='__main__':
    unittest.main()
