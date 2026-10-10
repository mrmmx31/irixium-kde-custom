#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test empty preview cards, ownership and palette in private native Plasma.

The three native source windows belong to this host. Missing provider IDs are
deliberately exercised; successful image capture is covered by the separate
testar-domainos-miniaturas.py suite. No real session configuration is changed.
"""
import importlib.util
from pathlib import Path
import os
import sys
import tempfile

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('private_native_bootstrap', Path(__file__).with_name('testar-domainos-unity.py'))
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
harness.__doc__ = __doc__
harness.IDENTIFIER = 'org.irixclassic.qa.thumbnail.lifecycle'
harness.NATIVE_SOURCE = harness.REPO / 'plasma/tests/domainos-thumbnail-lifecycle-host.cpp'
harness.NATIVE_LIBRARIES = ('Qt6Widgets', 'Qt6Test')
harness.CONTROLS_STYLE = 'org.kde.desktop'
harness.HOST_TIMEOUT = 30
harness.RUN_TIMEOUT = 45
original_worker = harness.worker


def worker(output):
    private_config = Path(os.environ['XDG_CONFIG_HOME'])
    (private_config / 'kdeglobals').write_text((harness.REPO / 'colors/Irixium.colors').read_text()
        + '\n[General]\nColorScheme=Irixium\n')
    (private_config / 'plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
    return original_worker(output)


harness.worker = worker
harness.QML = '''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
 preferredRepresentation:fullRepresentation
 fullRepresentation:Item {
  id:fixture;objectName:"domainosThumbnailLifecycleFixture"
  Layout.minimumWidth:640;Layout.minimumHeight:120
  property int ownedPid:0
  property bool unavailable:true
  property var requests:[]
  property var originals:tasks.windowRows.filter(row=>row.pid===ownedPid && row.title.indexOf("DomainOS fallback owned ")===0)
  property var windows:originals.map(row=>unavailable ? Object.assign({},row,{windowIds:[]}) : row)
  property alias first: first
  property alias second: second
  function setOwnedPid(pid){ownedPid=pid}
  function prepare(which,previews){const cell=which===0 ? first : second;cell.previewsEnabled=previews}
  function point(which){const cell=which===0 ? first : second;const point=cell.mapToGlobal(cell.width/2,cell.height/2);return JSON.stringify({x:point.x,y:point.y})}
  function hide(){first.hideImmediately()}
  function state(){
   function cellState(cell){
    const cards=[],providers=[]
    function gather(item){if(!item)return
     if(item.objectName==="domainosThumbnailCard"){
      const point=item.mapToGlobal(item.width/2,item.height/2)
      cards.push({key:item.modelData.key,width:item.width,height:item.height,live:item.liveAvailable,x:point.x,y:point.y})}
     if(item.objectName==="domainosThumbnailNativeProvider")providers.push({active:item.active,loaded:!!item.item})
     for(const child of item.children||[])gather(child)
    }
    gather(cell.contentsLoader.item)
    return {visible:cell.tooltipVisible,contentsLoaded:!!cell.contentsLoader.item,
      containsMouse:cell.containsMouse,preparingContents:cell.preparingContents,
      cards:cards,providers:providers,bodyVisible:cell.mainItem.visible,
      bodyWidth:cell.mainItem.width,bodyHeight:cell.mainItem.height}
   }
   return JSON.stringify({count:windows.length,requests:requests,
    active:originals.filter(row=>row.active).map(row=>row.key),first:cellState(first),second:cellState(second)})
  }
  QtObject {id:controller
   function membersFor(key){return fixture.windows}
   function windowFor(key){return fixture.windows.find(row=>row.key===key)||null}
  }
  Panel.DomainOSTasks {id:tasks;onlyCurrentDesktop:false;onlyCurrentActivity:false;onlyCurrentScreen:false;groupingMode:0}
  Panel.DomainOSPalette {id:colors}
  Rectangle {x:20;y:20;width:140;height:80;color:"#c1c1c1";Text{anchors.centerIn:parent;text:"First cell"}}
  Rectangle {x:200;y:20;width:140;height:80;color:"#c1c1c1";Text{anchors.centerIn:parent;text:"Second cell"}}
  Panel.DomainOSWindowThumbnails {
   id:first;x:20;y:20;width:140;height:80;controller:controller;colorPalette:colors
   record:({key:"group:owned",group:true,title:"Owned windows"})
   onActivationRequested:row=>{fixture.requests=fixture.requests.concat([row.key]);tasks.requestAction(row.key,"activate",undefined,row.pid)}
  }
  Panel.DomainOSWindowThumbnails {
   id:second;x:200;y:20;width:140;height:80;controller:controller;colorPalette:colors
   record:fixture.windows.length ? fixture.windows[0] : null
  }
 }
}
'''

if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='.qa-domainos-thumbnail-build-', dir=harness.REPO) as compiler_tmp:
        os.environ['TMPDIR'] = compiler_tmp
        raise SystemExit(harness.main())
