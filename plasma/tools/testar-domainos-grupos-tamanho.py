#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check native group picker sizing and stable long-title hover in private KDE.

Reuses only the isolated Xvfb/KWin/D-Bus bootstrap of the Unity test. No Unity
status is published here; TasksModel contains three, fifteen and sixteen owned
native clients. QQC2 desktop style exercises its real scrollbar padding.
"""
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
MODULE=Path(__file__).with_name('testar-domainos-unity.py')
spec=importlib.util.spec_from_file_location('private_native_bootstrap',MODULE)
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
harness.__doc__=__doc__
harness.IDENTIFIER='org.irixclassic.qa.group.size.fixture'
harness.NATIVE_SOURCE=harness.REPO/'plasma/tests/domainos-group-size-host.cpp'
harness.CONTROLS_STYLE='org.kde.desktop'
harness.NATIVE_LIBRARIES=('Qt6Widgets','Qt6Test')
harness.HOST_TIMEOUT=35
harness.RUN_TIMEOUT=50
harness.QML='''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
 id:host;preferredRepresentation:fullRepresentation
 fullRepresentation:Item {
  id:fixture;objectName:"domainosGroupSizeFixture"
  Layout.minimumWidth:594;Layout.minimumHeight:150
  property int ownedPid:0;property var requests:[];property int modelChanges:0;property int rowRefreshes:0
  property var watchedPicker:null;property var popupEvents:[]
  function observePicker(picker){watchedPicker=picker}
  function popupEvent(signal){popupEvents=popupEvents.concat([{signal:signal,height:watchedPicker.height,
   preferred:watchedPicker.preferredHeight,count:watchedPicker.memberCount,visible:watchedPicker.visible,
   key:tasks.groupSelectorKey,members:tasks.groupMembers.length}])}
  function setOwnedPid(pid){ownedPid=pid}
  function state(){return JSON.stringify({rows:tasks.taskRows,windows:tasks.windowRows.filter(row=>row.pid===ownedPid),members:tasks.groupMembers,
   open:box.groupPopupVisible,requests:requests,modelChanges:modelChanges,rowRefreshes:rowRefreshes,popupEvents:popupEvents})}
  function closePicker(){tasks.finishGroupSelection(false)}
  function coordinates(){const group=tasks.taskRows.find(row=>row.group);const button=group ? box.buttonForKey(group.key) : null
   if(!button)return "{}";const point=button.mapToGlobal(button.width/2,button.height/2);return JSON.stringify({x:point.x,y:point.y})}
  Panel.DomainOSPalette {id:colors;followSystem:false}
  Panel.DomainOSTasks {id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;groupingMode:1;onlyGroupWhenFull:false;sortMode:1;onOperationRequested:request=>fixture.requests=fixture.requests.concat([request]);onWindowRowsChanged:++fixture.rowRefreshes}
  Connections {target:tasks.tasksModel;function onDataChanged(){++fixture.modelChanges}}
  Connections {target:fixture.watchedPicker;function onHeightChanged(){fixture.popupEvent("height")}
   function onVisibleChanged(){fixture.popupEvent("visible")}function onOpened(){fixture.popupEvent("opened")}
   function onClosed(){fixture.popupEvent("closed")}function onAboutToShow(){fixture.popupEvent("aboutToShow")}}
  Panel.DomainOSIconbox {id:box;objectName:"domainosTestIconbox";anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:true}
 }
}
'''
if __name__=='__main__':raise SystemExit(harness.main())
