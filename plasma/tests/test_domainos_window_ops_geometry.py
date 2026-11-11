#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise staged KWin geometry requests with production JavaScript."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel/contents/code/window_ops.js"


@unittest.skipUnless(shutil.which("node"), "Node is required for the production KWin JavaScript")
class WindowGeometryStaging(unittest.TestCase):
    def run_layout(self, *, minimum=100, maximum=2147483647, delayed_restore=True,
                   action="layout", tiled=False, fixed=False):
        harness = r'''
const fs=require("fs");
const production=fs.readFileSync(process.argv[1],"utf8");
const options=JSON.parse(process.argv[2]);
const desktop={id:"desk",x11DesktopNumber:1};
const output={name:"screen"};
function signal(){
  const callbacks=[];
  return {connect:function(callback){callbacks.push(callback);},
    emit:function(){callbacks.slice().forEach(callback=>callback());}};
}
function makeWindow(id,pid,maximizeMode){
  const changed=signal();
  let geometry={x:40*pid,y:20*pid,width:320,height:200};
  const window={internalId:id,pid:pid,caption:id,normalWindow:true,dialog:false,
    specialWindow:false,deleted:false,transient:false,modal:false,transientFor:null,
    desktopFileName:id+".desktop",resourceClass:id,minSize:{width:options.minimum,height:100},
    maxSize:{width:options.maximum,height:options.maximum},
    tile:options.tiled && id==="second" ? {absoluteGeometry:{x:0,y:0,width:600,height:800},padding:0} : null,
    desktops:[desktop],output:output,
    moveable:true,resizeable:!(options.fixed && id==="second"),fullScreen:false,moveableAcrossScreens:true,
    minimizable:true,maximizable:true,minimized:options.action==="restore" && id==="first",maximizeMode:maximizeMode,
    frameGeometryChanged:changed,outputChanged:signal(),desktopsChanged:signal(),
    minimizedChanged:signal(),maximizedChanged:signal(),stackingOrderChanged:signal(),stackingOrder:pid};
  Object.defineProperty(window,"frameGeometry",{
    get:function(){return geometry;},
    set:function(value){
      if (options.action==="restore") throw new Error("restore attempted a frame geometry write");
      if (options.enforceBarrier && id==="first" && second && second.maximizeMode!==0)
        throw new Error("geometry issued before every selected window was ready");
      // Model a real client: geometry sent before the restore commit is lost.
      if (window.maximizeMode!==0) return;
      geometry={x:value.x,y:value.y,width:value.width,height:value.height};
      changed.emit();
    }});
  if (options.tiled && id==="second") {
    const nativeDesktops=window.desktops, nativeOutput=window.output, nativeMinimized=window.minimized;
    Object.defineProperty(window,"desktops",{get:function(){return nativeDesktops;},
      set:function(value){throw new Error("mutation attempted for tiled window desktops");}});
    Object.defineProperty(window,"output",{get:function(){return nativeOutput;},
      set:function(value){throw new Error("mutation attempted for tiled window output");}});
    Object.defineProperty(window,"minimized",{get:function(){return nativeMinimized;},
      set:function(value){throw new Error("mutation attempted for tiled window minimized");}});
  }
  if (options.action==="restore") {
    let nativeDesktops=window.desktops, nativeOutput=window.output;
    Object.defineProperty(window,"desktops",{get:function(){return nativeDesktops;},
      set:function(){throw new Error("restore attempted a desktop move");}});
    Object.defineProperty(window,"output",{get:function(){return nativeOutput;},
      set:function(){throw new Error("restore attempted an output move");}});
  }
  window.setMaximize=function(vertical,horizontal){
    if (options.tiled && id==="second") throw new Error("mutation attempted for tiled window maximize");
    if (vertical || horizontal) { window.maximizeMode=3;window.maximizedChanged.emit();return; }
    const restore=function(){window.maximizeMode=0;window.maximizedChanged.emit();};
    if (options.delayedRestore) setTimeout(restore,15); else restore();
  };
  return window;
}
let second;
const first=makeWindow("first",1,0);
second=makeWindow("second",2,1);
const windows=[first,second];
const activated=signal();
let activeWindow=null;
const raisedIds=[];
globalThis.request={action:options.action,mode:"columns",desktopId:"desk",windows:[
  {key:"window:first",windowIds:["first"],pid:1},
  {key:"window:second",windowIds:["second"],pid:2}
]};
globalThis.resultService="test-result";
globalThis.workspace={windowList:function(){return windows;},currentDesktop:desktop,activeScreen:output,
  stackingOrder:windows.slice(),windowActivated:activated,
  raiseWindow:function(window){
    if (raisedIds.includes(window.internalId)) throw new Error("window raised more than once");
    raisedIds.push(window.internalId);
    const index=this.stackingOrder.indexOf(window);
    if (index>=0) this.stackingOrder.splice(index,1);
    this.stackingOrder.push(window);
    this.stackingOrder.forEach((candidate,index)=>candidate.stackingOrder=index);
    window.stackingOrderChanged.emit();
  },
  clientArea:function(){return {x:0,y:0,width:1200,height:800};},
  sendClientToScreen:function(window,target){
    if (options.action==="restore") throw new Error("restore attempted sendClientToScreen");
    window.output=target;
  }};
Object.defineProperty(globalThis.workspace,"activeWindow",{
  get:function(){return activeWindow;},
  set:function(value){activeWindow=value;activated.emit(value);}
});
globalThis.KWin={MaximizeArea:0};
globalThis.callDBus=function(service,path,iface,method,payload){process.stdout.write(payload);};
globalThis.QTimer=function(){
  this.timeout=signal();
  this.start=function(){const timer=setTimeout(()=>this.timeout.emit(),this.interval);timer.unref();};
};
eval(production);
'''
        completed = subprocess.run(
            ["node", "-e", harness, str(SOURCE), json.dumps({
                "minimum": minimum, "maximum": maximum, "delayedRestore": delayed_restore,
                "action": action, "tiled": tiled, "fixed": fixed, "enforceBarrier": True})],
            capture_output=True, text=True, check=True, timeout=10)
        return json.loads(completed.stdout)

    def test_waits_for_horizontal_maximize_restore_before_single_geometry_request(self):
        report = self.run_layout()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["outcome"], "confirmed")
        self.assertEqual(report["windows"][1]["maximizeMode"], 0)
        self.assertTrue(report["windows"][1]["geometryIssued"])
        self.assertEqual(report["windows"][1]["requested"], report["windows"][1]["actual"])

    def test_impossible_minimum_is_rejected_before_any_geometry_request(self):
        report = self.run_layout(minimum=700)
        self.assertFalse(report["ok"], report)
        self.assertEqual(report["outcome"], "unavailable")
        self.assertIn("mínimo de 700x100", report["detail"])
        self.assertIn("nenhuma geometria foi solicitada", report["detail"])

    def test_impossible_maximum_is_identified_as_maximum_before_mutation(self):
        report = self.run_layout(maximum=400)
        self.assertFalse(report["ok"], report)
        self.assertEqual(report["outcome"], "unavailable")
        self.assertIn("máximo de 400x400", report["detail"])
        self.assertIn("nenhuma geometria foi solicitada", report["detail"])

    def test_read_only_preflight_exposes_partial_vertical_maximize(self):
        report = self.run_layout(action="preflight")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["outcome"], "preflight")
        self.assertTrue(report["available"])
        self.assertEqual(report["windows"][1]["maximizeMode"], 1)
        self.assertEqual(report["windows"][1]["key"], "window:second")

    def test_tiled_window_is_rejected_before_geometry_mutation(self):
        report = self.run_layout(tiled=True)
        self.assertFalse(report["ok"], report)
        self.assertEqual(report["outcome"], "unavailable")
        self.assertIn("vinculada ao mosaico", report["detail"])
        self.assertIn("nenhuma geometria foi solicitada", report["detail"])

    def test_read_only_preflight_reports_tiling_without_mutation(self):
        report = self.run_layout(action="preflight", tiled=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["outcome"], "preflight")
        self.assertTrue(report["available"])
        self.assertFalse(report["geometryAvailable"])
        self.assertIn("vinculada ao mosaico", report["detail"])

    def test_read_only_preflight_reports_native_fixed_size_before_layout(self):
        report = self.run_layout(action="preflight", fixed=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["outcome"], "preflight")
        self.assertTrue(report["available"])
        self.assertFalse(report["geometryAvailable"])
        self.assertIn("não aceita redimensionamento", report["detail"])

    def test_restore_clears_minimized_and_partial_maximize_without_geometry_or_location_write(self):
        report = self.run_layout(action="restore")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["outcome"], "confirmed")
        self.assertEqual(report["action"], "restore")
        self.assertTrue(all(not row["minimized"] and row["maximizeMode"] == 0
                            for row in report["windows"]))
        self.assertEqual([row["actual"] for row in report["windows"]], [
            {"x": 40, "y": 20, "width": 320, "height": 200},
            {"x": 80, "y": 40, "width": 320, "height": 200},
        ])
        self.assertTrue(all(row["raised"] for row in report["windows"]))
        self.assertEqual([row["stackingOrder"] for row in report["windows"]], [0, 1])
        self.assertEqual([row["active"] for row in report["windows"]], [False, True])
        self.assertEqual(report["activeWindow"], "second")
        self.assertIn("brought to the front", report["detail"])


if __name__ == "__main__":
    unittest.main()
