#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical default wheel pagination followed by native group chooser clicks."""
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('private_bootstrap',Path(__file__).with_name('testar-domainos-unity.py'))
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
harness.__doc__=__doc__
harness.IDENTIFIER='org.irixclassic.qa.group.wheel.fixture'
harness.NATIVE_SOURCE=harness.REPO/'plasma/tests/domainos-group-wheel-host.cpp'
harness.CONTROLS_STYLE='org.kde.desktop'
harness.NATIVE_LIBRARIES=('Qt6Widgets','Qt6Test','x11')
harness.HOST_TIMEOUT=30;harness.RUN_TIMEOUT=45
harness.EXTRA_APPLICATIONS={f'org.irixclassic.qa.wheel{index}.desktop':
 f'[Desktop Entry]\nType=Application\nName=DomainOS wheel group {index}\nExec=/bin/true\nIcon=utilities-terminal\nStartupWMClass=DomainOSWheel{index}\n' for index in range(9)}
harness.QML='''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
 id:host;preferredRepresentation:fullRepresentation
 fullRepresentation:Item {
  id:fixture;objectName:"domainosGroupWheelFixture"
  Layout.minimumWidth:594;Layout.minimumHeight:150
  property var ownedPids:[];property var requests:[]
  function setOwnedPids(pids){ownedPids=JSON.parse(pids)}
  function closePicker(){tasks.finishGroupSelection(false)}
  function state(){return JSON.stringify({rows:tasks.taskRows,windows:tasks.windowRows.filter(row=>ownedPids.indexOf(row.pid)>=0),
   open:box.groupPopupVisible,members:tasks.groupMembers,key:tasks.groupSelectorKey,requests:requests,
   firstVisible:box.firstVisible,wheelActivation:box.iconboxWheelActivates})}
  function coordinates(){const record=tasks.taskRows[box.firstVisible];const button=record ? box.buttonForKey(record.key) : null
   if(!button)return "{}";const p=button.mapToGlobal(button.width/2,button.height/2);return JSON.stringify({x:p.x,y:p.y,key:record.key})}
  Panel.DomainOSPalette {id:colors;followSystem:false}
  Panel.DomainOSTasks {id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;
   groupingMode:1;onlyGroupWhenFull:false;sortMode:1;onOperationRequested:request=>fixture.requests=fixture.requests.concat([request])}
  Panel.DomainOSIconbox {id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:true}
 }
}
'''
if __name__=='__main__':raise SystemExit(harness.main())
