#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Production selection and ephemeral window pins with explicit model doubles."""
import json
import unittest

# This fixture prepares private repository-local HOME/XDG/cache and offscreen Qt.
import test_domainos_middle_click as setup
from PyQt6 import sip
from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication


class TemporaryWindowPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.engine = QQmlApplicationEngine()
        self.diagnostics = []
        self.engine.warnings.connect(lambda rows: self.diagnostics.extend(row.toString() for row in rows))
        path = setup.Path(setup._private.name) / 'temporary-window-pins-fixture.qml'
        path.write_text('''import QtQuick
import "''' + (setup.ROOT / 'plasma/tests').as_uri() + '''"
DomainOSIconboxPreview {
 id:fixture
 property var captured:null
 QtObject {
  id:identityHost
  property alias windows:fixture.windows
  property int screen:0
  property QtObject controller:QtObject {
   property bool onlyCurrentDesktop:false
   property bool onlyCurrentActivity:false
   property bool onlyCurrentScreen:false
   property int currentDesktopId:1
   property string currentActivityId:"activity"
  }
  function appendRequest(request) { fixture.appendRequest(request) }
 }
 DomainOSFixtureTasks {id:identities;host:identityHost}
 function prepare() {
  resetUi();controller.temporaryWindowPins=[]
  controller.identityModel=identities
  controller.onlyCurrentDesktop=false;controller.onlyCurrentActivity=false
  controller.groupingMode=1;controller.refresh()
 }
 function openTask(key) { return iconbox.selectRecord(controller.taskFor(key),0,iconbox.buttonForKey(key)) }
 function choose(key,value) { return controller.setMemberSelected(key,value) }
 function finish(show) { controller.finishGroupSelection(show) }
 function pin(key) { return JSON.stringify(controller.pinTemporaryWindows([controller.windowFor(key)])) }
 function toggle(key) { return JSON.stringify(controller.toggleTemporaryPin(controller.windowFor(key))) }
 function pinMenu() { return iconbox.pinSelectedWindows() }
 function remember(key) { captured=controller.windowFor(key) }
 function rememberTask(key) { captured=controller.taskFor(key) }
 function pinCaptured() { return JSON.stringify(controller.pinTemporaryWindows([captured])) }
 function nativeTarget(key) {
  const target=controller.nativeTaskTarget(controller.windowFor(key))
  return JSON.stringify(target ? {row:target.row,child:target.child,key:target.record.key,pid:target.record.pid} : null)
 }
 function titles(key) { return iconbox.memberTitleClicked(controller.windowFor(key)) }
 function showContext(key) { return iconbox.openContext(controller.taskFor(key),iconbox) }
 function snapshot() {
  return JSON.stringify({rows:controller.taskRows,pins:controller.temporaryWindowPins,
   selected:controller.selectedKeys,checked:controller.memberSelectionKeys,count:controller.windowCount,
   requests:requests,group:controller.groupSelectorKey,operations:iconbox.operationsMenuVisible,
   menuSelection:iconbox.menuSelection,errors:iconbox.lastError,first:iconbox.firstVisible})
 }
}''')
        self.engine.load(QUrl.fromLocalFile(str(path)))
        self.assertTrue(self.engine.rootObjects(), '\n'.join(self.diagnostics))
        self.window = sip.cast(self.engine.rootObjects()[0], QQuickWindow)
        self.engine.globalObject().setProperty('fixture', self.engine.newQObject(self.window))
        self.evaluate('fixture.prepare()')
        self.settle()

    def tearDown(self):
        self.window.close()
        self.engine.deleteLater()
        self.app.processEvents()
        self.assertFalse(self.diagnostics, '\n'.join(self.diagnostics))

    def settle(self):
        QTest.qWait(20)
        self.app.processEvents()

    def evaluate(self, expression):
        result = self.engine.evaluate(expression)
        self.assertFalse(result.isError(), result.toString())
        self.app.processEvents()
        return result.toVariant()

    def call(self, method, *arguments):
        return self.evaluate('fixture.' + method + '(' + ','.join(json.dumps(item) for item in arguments) + ')')

    def state(self):
        self.settle()
        return json.loads(self.call('snapshot'))

    @staticmethod
    def visible_keys(state):
        return [window['key'] for row in state['rows'] for window in (row['members'] if row['group'] else [row])]

    def test_continue_then_individual_chooser_preserves_explicit_selection(self):
        self.call('openTask', 'group:terminal')
        self.call('choose', 'window:1', True)
        self.call('finish', False)
        self.call('openTask', 'window:6')
        self.assertEqual(self.state()['selected'], ['window:1'])
        self.call('choose', 'window:6', True)
        state = self.state()
        self.assertEqual(state['selected'], ['window:1', 'window:6'])
        self.assertEqual(state['checked'], ['window:1', 'window:6'])
        self.assertFalse(state['requests'])

    def test_continue_accumulates_across_two_groups_and_an_individual(self):
        for task, key in [('group:terminal', 'window:2'), ('group:browser', 'window:4'), ('window:6', 'window:6')]:
            self.call('openTask', task)
            self.call('choose', key, True)
            self.call('finish', False)
        self.assertEqual(self.state()['selected'], ['window:2', 'window:4', 'window:6'])
        self.call('finish', True)
        state = self.state()
        self.assertTrue(state['operations'])
        self.assertEqual({row['key'] for row in state['menuSelection']}, {'window:2', 'window:4', 'window:6'})

    def test_one_checkbox_offers_pin_but_no_bulk_geometry_action(self):
        self.call('openTask', 'group:terminal')
        self.call('choose', 'window:1', True)
        self.call('finish', True)
        self.settle()
        self.assertTrue(self.state()['operations'])
        self.assertTrue(self.evaluate('fixture.iconbox.batchContextMenu.itemAt(1).enabled'))
        self.assertFalse(self.evaluate('fixture.iconbox.batchContextMenu.itemAt(3).enabled'))
        self.assertTrue(self.call('pinMenu'))
        state = self.state()
        self.assertEqual(state['rows'][0]['key'], 'window:1')
        self.assertTrue(state['rows'][0]['temporaryPinned'])
        self.assertFalse(state['requests'])

    def test_pins_keep_choice_order_and_do_not_duplicate_members(self):
        self.call('pin', 'window:6')
        self.call('pin', 'window:1')
        self.call('pin', 'window:2')
        state = self.state()
        self.assertEqual([row['key'] for row in state['rows'][:3]], ['window:6', 'window:1', 'window:2'])
        self.assertEqual([row['key'] for row in state['pins']], ['window:6', 'window:1', 'window:2'])
        self.assertEqual(sorted(self.visible_keys(state)), ['window:' + str(index) for index in range(1, 10)])
        self.assertEqual(len(self.visible_keys(state)), len(set(self.visible_keys(state))))
        self.assertEqual(state['count'], 9)
        self.assertFalse(state['requests'])

    def test_unpin_returns_to_native_group_and_first_context_item_is_unpin(self):
        self.call('pin', 'window:1')
        self.call('showContext', 'window:1')
        self.assertEqual(self.evaluate('fixture.iconbox.basicContextMenu.itemAt(0).objectName'), 'domainosTemporaryUnpin')
        self.assertTrue(self.evaluate('fixture.iconbox.basicContextMenu.itemAt(0).visible'))
        self.call('toggle', 'window:1')
        state = self.state()
        self.assertFalse(state['pins'])
        terminal = next(row for row in state['rows'] if row['key'] == 'group:terminal')
        self.assertEqual(terminal['memberKeys'], ['window:1', 'window:2', 'window:3'])

    def test_pin_is_preserved_outside_scope_without_overriding_filters(self):
        self.call('pin', 'window:1')
        self.evaluate('fixture.controller.onlyCurrentDesktop=true;fixture.controller.currentDesktopId=2;fixture.controller.refresh()')
        state = self.state()
        self.assertEqual(state['pins'], [{'key':'window:1', 'pid':501}])
        self.assertEqual(self.visible_keys(state), ['window:9'])
        self.evaluate('fixture.controller.currentDesktopId=1;fixture.controller.refresh()')
        self.assertEqual(self.state()['rows'][0]['key'], 'window:1')

    def test_window_close_and_pid_reuse_release_exact_temporary_pin(self):
        self.call('pin', 'window:1')
        self.call('pin', 'window:6')
        self.call('removeWindow', 6)
        self.call('mutate', 1, 'pid', 9901)
        state = self.state()
        self.assertFalse(state['pins'])
        self.assertFalse(any(row.get('temporaryPinned') for row in state['rows']))
        self.assertFalse(state['requests'])

    def test_old_pin_snapshot_cannot_target_reused_window_or_partial_selection(self):
        self.call('remember', 'window:1')
        self.call('mutate', 1, 'pid', 9901)
        result = json.loads(self.call('pinCaptured'))
        self.assertEqual(result['state'], 'unavailable')
        self.assertFalse(self.state()['pins'])

    def test_native_target_of_separated_window_remains_exact_group_child(self):
        self.call('pin', 'window:2')
        target = json.loads(self.call('nativeTarget', 'window:2'))
        self.assertEqual(target, {'row':0, 'child':1, 'key':'window:2', 'pid':502})
        self.evaluate('fixture.controller.openUrls(fixture.controller.taskFor("window:2"),["file:///qa-owned"] )')
        self.assertEqual(self.state()['requests'], [{'action':'openUrls', 'ids':[2], 'argument':['file:///qa-owned']}])

    def prepare_different_launchers_in_projected_group(self):
        for number, name in [(1, 'pinned'), (2, 'remaining'), (3, 'third')]:
            self.call('mutate', number, 'launcher', 'applications:qa-' + name + '.desktop')
        self.call('pin', 'window:1')
        group = next(row for row in self.state()['rows'] if row['key'] == 'group:terminal')
        self.assertEqual([row['key'] for row in group['members']], ['window:2', 'window:3'])
        self.assertEqual(group['members'][0]['launcherUrl'], 'applications:qa-remaining.desktop')

    def test_projected_group_new_instance_targets_first_remaining_child(self):
        self.prepare_different_launchers_in_projected_group()
        result = self.evaluate('fixture.controller.requestGroupNewInstance(fixture.controller.taskFor("group:terminal"))')
        self.assertEqual(result['state'], 'requested')
        self.assertEqual(self.state()['requests'], [{'action':'newInstance', 'ids':[2], 'argument':None}])

    def test_projected_group_url_drop_targets_first_remaining_child(self):
        self.prepare_different_launchers_in_projected_group()
        result = self.evaluate('fixture.controller.openUrls(fixture.controller.taskFor("group:terminal"),["file:///qa-owned-group-drop"])')
        self.assertEqual(result['state'], 'requested')
        self.assertEqual(self.state()['requests'], [{'action':'openUrls', 'ids':[2], 'argument':['file:///qa-owned-group-drop']}])

    def test_projected_group_stale_pid_rejects_launch_and_drop(self):
        self.prepare_different_launchers_in_projected_group()
        self.call('rememberTask', 'group:terminal')
        self.call('mutate', 2, 'pid', 9902)
        launched = self.evaluate('fixture.controller.requestGroupNewInstance(fixture.captured)')
        dropped = self.evaluate('fixture.controller.openUrls(fixture.captured,["file:///qa-owned-stale-drop"])')
        self.assertEqual(launched['state'], 'unavailable')
        self.assertEqual(dropped['state'], 'unavailable')
        self.assertFalse(self.state()['requests'])

    def test_automatic_count_is_unchanged_by_pins_and_minimized_filter_is_respected(self):
        self.call('pin', 'window:1')
        self.evaluate('fixture.controller.filterMode="automatic";fixture.controller.automaticThreshold=8;fixture.controller.refresh()')
        state = self.state()
        self.assertEqual(state['count'], 9)
        self.assertEqual(self.visible_keys(state), ['window:2', 'window:5'])
        self.assertEqual(state['pins'], [{'key':'window:1', 'pid':501}])
        self.evaluate('fixture.controller.automaticThreshold=9;fixture.controller.refresh()')
        self.assertEqual(self.state()['rows'][0]['key'], 'window:1')

    def test_bulk_pin_uses_checkbox_order_and_returns_to_first_page(self):
        self.call('openTask', 'group:terminal')
        self.call('choose', 'window:3', True)
        self.call('choose', 'window:1', True)
        self.call('finish', True)
        self.settle()
        self.evaluate('fixture.iconbox.firstVisible=7')
        self.assertTrue(self.call('pinMenu'))
        state = self.state()
        self.assertEqual([row['key'] for row in state['rows'][:2]], ['window:3', 'window:1'])
        self.assertEqual(state['first'], 0)


if __name__ == '__main__':
    unittest.main()
