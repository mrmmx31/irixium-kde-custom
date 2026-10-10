#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Projected group menu roles against explicit native-role model doubles.

Loads the production NativeTaskMenu/Tasks. Doubles reproduce KDE 6.3.6 group
all/any/union role semantics; these are unit tests, not a native menu/pixel proof.
"""
import json
import os
import unittest

import test_domainos_middle_click as setup
os.environ['PULSE_SERVER'] = 'unix:' + str(setup.Path(setup._private.name) / 'no-audio')
from PyQt6 import sip
from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication


class NativeMenuProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.engine = QQmlApplicationEngine()
        self.diagnostics = []
        self.engine.warnings.connect(lambda rows: self.diagnostics.extend(row.toString() for row in rows))
        fixture = setup.Path(setup._private.name) / 'native-menu-projection.qml'
        fixture.write_text('''import QtQuick
import org.kde.taskmanager as TaskManager
import "'''+(setup.ROOT/'plasma/tests').as_uri()+'''"
import "'''+(setup.ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/ui').as_uri()+'''" as DomainOS
DomainOSIconboxPreview {
 id:fixture
 property var operationEvents:[]
 Connections {
  target:fixture.controller
  function onOperationRequested(request) { fixture.operationEvents=fixture.operationEvents.concat([request]) }
 }
 DomainOSFixtureTasks { id:groupBase;host:fixture;grouped:true }
 DomainOSFixtureTasks { id:scopeBase;host:fixture }
 QtObject {
  id:groupRoles
  readonly property int count:groupBase.count
  function makeModelIndex(row,child) { return groupBase.makeModelIndex(row,child) }
  function rowCount(index) { return groupBase.rowCount(index) }
  function requestNewVirtualDesktop(index) {
   const row=groupBase.node(index);
   fixture.appendRequest({action:"newVirtualDesktop",ids:(row.children || [row]).reduce((ids,child)=>ids.concat(child.ids),[]),argument:null});
  }
  function data(index,role) {
   const node=groupBase.node(index),atm=TaskManager.AbstractTasksModel;
   if (!node) return undefined;
   if (!node.children) return fixture.scopeRole(node,index.child<0 ? null : index,role,groupBase);
   if ([atm.IsMaximizable,atm.IsMaximized,atm.IsClosable,atm.IsMinimizable,atm.IsMinimized,atm.IsVirtualDesktopsChangeable,
        atm.IsKeepAbove,atm.IsKeepBelow,atm.IsFullScreenable,atm.IsFullScreen,atm.IsShadeable,atm.IsShaded,atm.SkipTaskbar].indexOf(role)>=0)
    return node.children.every(row=>fixture.booleanRole(row,role));
   if (role===atm.IsMovable || role===atm.IsResizable) return false;
   if (role===atm.VirtualDesktops) return [...new Set(node.children.reduce((all,row)=>all.concat(row.desktops),[]))];
   if (role===atm.Activities) return [...new Set(node.children.reduce((all,row)=>all.concat(row.activities),[]))];
   if (role===atm.WinIdList) return node.children.reduce((all,row)=>all.concat(row.ids),[]);
   return groupBase.data(index,role);
  }
 }
 QtObject {
  id:scopedRoles
  readonly property int count:scopeBase.count
  function makeModelIndex(row,child) { return scopeBase.makeModelIndex(row,child) }
  function data(index,role) { return fixture.scopeRole(scopeBase.node(index),index,role,scopeBase) }
  function requestToggleMaximized(index) { scopeBase.requestToggleMaximized(index) }
  function requestVirtualDesktops(index,desktops) { scopeBase.requestVirtualDesktops(index,desktops) }
 }
 function booleanRole(row,role) {
  const atm=TaskManager.AbstractTasksModel;
  if(role===atm.IsMaximizable)return row.maximizable;
  if(role===atm.IsClosable)return row.closable;
  if(role===atm.IsMinimizable)return row.minimizable;
  if(role===atm.IsVirtualDesktopsChangeable)return row.desktopsChangeable;
  if(role===atm.IsMaximized)return !!row.maximized;
  if(role===atm.IsMinimized)return !!row.minimized;
  if(role===atm.IsKeepAbove)return !!row.keepAbove;
  if(role===atm.IsKeepBelow)return !!row.keepBelow;
  if(role===atm.IsFullScreenable)return !!row.fullScreenable;
  if(role===atm.IsFullScreen)return !!row.fullScreen;
  if(role===atm.IsShadeable)return !!row.shadeable;
  if(role===atm.IsShaded)return !!row.shaded;
  if(role===atm.SkipTaskbar)return !!row.skipTaskbar;
  return false;
 }
 function scopeRole(row,index,role,base) {
  const atm=TaskManager.AbstractTasksModel;
  if(!row)return undefined;
  if(role===atm.LauncherUrl)return row.launcher;
  if(role===atm.AppName)return row.appId;
  if(role===atm.IsKeepAbove)return !!row.keepAbove;
  if(role===atm.IsKeepBelow)return !!row.keepBelow;
  if(role===atm.IsFullScreenable)return !!row.fullScreenable;
  if(role===atm.IsFullScreen)return !!row.fullScreen;
  if(role===atm.IsShadeable)return !!row.shadeable;
  if(role===atm.IsShaded)return !!row.shaded;
  if(role===atm.IsOnAllVirtualDesktops)return !!row.onAllDesktops;
  if(role===atm.SkipTaskbar)return !!row.skipTaskbar;
  return base.data(index || base.makeModelIndex(base.rows.indexOf(row)),role);
 }
 DomainOS.DomainOSNativeTaskMenu { id:menu;iconbox:fixture.iconbox;controller:fixture.controller }
 function prepare() {
  resetUi();windows=windows.slice(0,3).map(row=>Object.assign({},row,{minimized:false,active:false}));
  controller.tasksModel=groupRoles;controller.scopeModel=scopedRoles;controller.temporaryWindowPins=[];
  controller.onlyCurrentDesktop=false;controller.onlyCurrentActivity=false;controller.refresh();
  operationEvents=[];
 }
 function pinAndCapture() {
  controller.pinTemporaryWindows([controller.windowFor("window:1")]);controller.refresh();
  menu.targetRecord=controller.taskFor("group:terminal");
 }
 function captureSingle() { menu.targetRecord=controller.taskFor("window:1") }
 function captureGroup() { menu.targetRecord=controller.taskFor("group:terminal") }
 function unpinFirst() { controller.toggleTemporaryPin(controller.windowFor("window:1"));controller.refresh() }
 function newDesktop() { return menu.newVirtualDesktop() }
 function existingDesktop() { menu.apply("desktops",[2]) }
 function role(name) { return JSON.stringify(menu.tasksModel.data(null,TaskManager.AbstractTasksModel[name])) }
 function nativeRole(name) { return JSON.stringify(groupRoles.data(groupRoles.makeModelIndex(0),TaskManager.AbstractTasksModel[name])) }
 function change(id,field,value) { mutate(id,field,value);controller.refresh() }
 function appendMember() { addWindow(4,"terminal");controller.refresh() }
 function apply() { menu.apply("maximize") }
 function listIndex(name) { return menu.tasksModel.data(null,TaskManager.AbstractTasksModel[name]).indexOf("qa") }
 function stateJson() { return JSON.stringify({requests:requests,pins:controller.temporaryWindowPins,
  operations:operationEvents,error:iconbox.lastError,windows:windows}) }
}''')
        self.engine.load(QUrl.fromLocalFile(str(fixture)))
        self.assertTrue(self.engine.rootObjects(), '\n'.join(self.diagnostics))
        self.window = sip.cast(self.engine.rootObjects()[0], QQuickWindow)
        self.engine.globalObject().setProperty('fixture', self.engine.newQObject(self.window))
        self.call('prepare')
        self.settle()

    def tearDown(self):
        self.window.close()
        self.engine.deleteLater()
        self.app.processEvents()
        self.assertFalse(self.diagnostics, '\n'.join(self.diagnostics))

    def settle(self):
        QTest.qWait(10)
        self.app.processEvents()

    def call(self, method, *args):
        value = self.engine.evaluate('fixture.'+method+'('+','.join(json.dumps(arg) for arg in args)+')')
        self.assertFalse(value.isError(), value.toString())
        self.app.processEvents()
        return value.toVariant()

    def role(self, name):
        return json.loads(self.call('role', name))

    def test_pinned_incapable_window_does_not_disable_projected_group_capabilities(self):
        for field in ('maximizable', 'closable', 'minimizable', 'desktopsChangeable'):
            self.call('change', 1, field, False)
        self.call('pinAndCapture')
        for role in ('IsMaximizable', 'IsClosable', 'IsMinimizable', 'IsVirtualDesktopsChangeable'):
            self.assertFalse(json.loads(self.call('nativeRole', role)))
            self.assertTrue(self.role(role))
        self.assertFalse(self.role('IsMovable'))
        self.assertFalse(self.role('IsResizable'))
        self.assertEqual(self.role('ChildCount'), 2)

    def test_ids_desktops_activities_and_first_metadata_exclude_pin(self):
        self.call('change', 1, 'desktops', [2])
        self.call('change', 1, 'activities', ['outside'])
        self.call('pinAndCapture')
        self.assertEqual(json.loads(self.call('nativeRole', 'WinIdList')), [1,2,3])
        self.assertEqual(self.role('WinIdList'), [2,3])
        self.assertEqual(self.role('VirtualDesktops'), [1])
        self.assertEqual(self.role('Activities'), ['activity'])
        self.assertEqual(self.role('AppPid'), 502)
        self.assertEqual(self.role('LauncherUrl'), 'applications:app2.desktop')

    def test_all_boolean_group_state_roles_follow_kde_all_semantics_on_subset(self):
        roles = {'IsMaximized':'maximized', 'IsMinimized':'minimized', 'IsKeepAbove':'keepAbove',
            'IsKeepBelow':'keepBelow', 'IsFullScreenable':'fullScreenable', 'IsFullScreen':'fullScreen',
            'IsShadeable':'shadeable', 'IsShaded':'shaded', 'SkipTaskbar':'skipTaskbar'}
        for field in roles.values():
            self.call('change', 1, field, False)
            self.call('change', 2, field, True)
            self.call('change', 3, field, True)
        self.call('pinAndCapture')
        for role in roles:
            self.assertFalse(json.loads(self.call('nativeRole', role)))
            self.assertTrue(self.role(role))

    def test_group_state_reads_current_remaining_members(self):
        self.call('pinAndCapture')
        self.call('change', 1, 'active', True)
        self.call('change', 2, 'maximized', True)
        self.call('change', 3, 'maximized', True)
        self.assertFalse(self.role('IsActive'))
        self.assertTrue(self.role('IsMaximized'))
        self.call('change', 3, 'maximized', False)
        self.assertFalse(self.role('IsMaximized'))

    def test_changed_membership_has_typed_fallbacks_and_no_indexof_error(self):
        self.call('pinAndCapture')
        self.call('appendMember')
        for role in ('VirtualDesktops', 'Activities', 'WinIdList'):
            self.assertEqual(self.role(role), [])
            self.assertEqual(self.call('listIndex', role), -1)
        for role in ('LauncherUrl', 'LauncherUrlWithoutIcon', 'AppId'):
            self.assertEqual(self.role(role), '')
        self.assertFalse(self.role('IsMaximizable'))
        self.call('apply')
        # apply intentionally targets only the captured subset while alive.
        requests=json.loads(self.call('stateJson'))['requests']
        self.assertEqual([request['ids'] for request in requests], [[2],[3]])

    def test_reused_member_pid_invalidates_all_menu_metadata(self):
        self.call('pinAndCapture')
        self.call('change', 2, 'pid', 9902)
        self.assertEqual(self.role('WinIdList'), [])
        self.assertEqual(self.role('LauncherUrl'), '')
        self.assertFalse(self.role('IsClosable'))
        self.call('apply')
        self.assertFalse(json.loads(self.call('stateJson'))['requests'])

    def test_single_pinned_child_retains_its_own_metadata_and_capability(self):
        self.call('change', 1, 'maximizable', False)
        self.call('pinAndCapture')
        self.call('captureSingle')
        self.assertEqual(self.role('WinIdList'), [1])
        self.assertEqual(self.role('AppPid'), 501)
        self.assertEqual(self.role('LauncherUrl'), 'applications:app1.desktop')
        self.assertFalse(self.role('IsMaximizable'))

    def test_group_apply_maximize_keeps_pinned_window_out_of_requests(self):
        self.call('pinAndCapture')
        self.call('apply')
        requests=json.loads(self.call('stateJson'))['requests']
        self.assertEqual([request['ids'] for request in requests], [[2],[3]])
        self.assertTrue(all(request['action']=='toggleMaximized' for request in requests))

    def test_new_desktop_rejects_projected_group_without_request_or_activity(self):
        self.call('pinAndCapture')
        before = json.loads(self.call('stateJson'))
        self.assertFalse(self.call('newDesktop'))
        after = json.loads(self.call('stateJson'))
        self.assertEqual(after['requests'], [])
        self.assertEqual(after['operations'], [])
        self.assertEqual(after['pins'], before['pins'])
        self.assertEqual(after['windows'], before['windows'])
        self.assertIn('fixada fora do grupo', after['error'])

    def test_new_desktop_accepts_exact_integral_group_once(self):
        self.call('captureGroup')
        self.assertTrue(self.call('newDesktop'))
        state = json.loads(self.call('stateJson'))
        self.assertEqual(state['requests'], [{'action':'newVirtualDesktop','ids':[1,2,3],'argument':None}])
        self.assertEqual(state['operations'], [{'state':'requested','action':'newVirtualDesktop','key':'group:terminal'}])
        self.assertEqual(state['error'], '')

    def test_new_desktop_rejects_reused_captured_pid(self):
        self.call('captureGroup')
        self.call('change', 2, 'pid', 9902)
        self.assertFalse(self.call('newDesktop'))
        state = json.loads(self.call('stateJson'))
        self.assertEqual(state['requests'], [])
        self.assertEqual(state['operations'], [])
        self.assertIn('Reabra o menu', state['error'])

    def test_new_desktop_after_unpin_requires_fresh_capture(self):
        self.call('pinAndCapture')
        self.call('unpinFirst')
        self.assertFalse(self.call('newDesktop'))
        state = json.loads(self.call('stateJson'))
        self.assertEqual(state['requests'], [])
        self.assertEqual(state['operations'], [])
        self.call('captureGroup')
        self.assertTrue(self.call('newDesktop'))
        state = json.loads(self.call('stateJson'))
        self.assertEqual(state['requests'], [{'action':'newVirtualDesktop','ids':[1,2,3],'argument':None}])
        self.assertEqual(len(state['operations']), 1)

    def test_existing_desktop_moves_only_captured_remaining_members(self):
        self.call('pinAndCapture')
        self.call('existingDesktop')
        state = json.loads(self.call('stateJson'))
        self.assertEqual(state['requests'], [
            {'action':'desktops','ids':[2],'argument':[2]},
            {'action':'desktops','ids':[3],'argument':[2]}])
        self.assertEqual([event['key'] for event in state['operations']], ['window:2','window:3'])
        self.assertEqual(state['pins'], [{'key':'window:1','pid':501}])


if __name__=='__main__':unittest.main()
