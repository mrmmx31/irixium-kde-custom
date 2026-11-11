#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the production KWin relation guard with deterministic JS doubles."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel/contents/code/window_ops.js"


@unittest.skipUnless(shutil.which("node"), "Node is required for the production KWin JavaScript")
class WindowRelationGuard(unittest.TestCase):
    def run_operation(self, extra_windows, action="layout"):
        harness = r'''
const fs=require("fs");
const production=fs.readFileSync(process.argv[1],"utf8");
const options=JSON.parse(process.argv[2]);
const extras=options.extraWindows;
const desktop={id:"desk",x11DesktopNumber:1};
const output={name:"screen"};
function signal(){return {connect:function(){}};}
function makeWindow(value){
  return Object.assign({internalId:value.id,pid:value.pid,caption:value.id,
    normalWindow:true,dialog:false,specialWindow:false,deleted:false,
    transient:false,modal:false,transientFor:null,desktopFileName:"",resourceClass:"",
    frameGeometry:{x:0,y:0,width:320,height:200},desktops:[desktop],output:output,
    moveable:true,resizeable:true,fullScreen:false,moveableAcrossScreens:true,
    minimizable:true,maximizable:true,minimized:false,maximizeMode:0,
    frameGeometryChanged:signal(),outputChanged:signal(),desktopsChanged:signal(),
    minimizedChanged:signal(),maximizedChanged:signal(),
    setMaximize:function(horizontal,vertical){this.maximizeMode=horizontal&&vertical?3:0;}
  },value);
}
const first=makeWindow({id:"first",pid:101,desktopFileName:"first.desktop",resourceClass:"first"});
const second=makeWindow({id:"second",pid:202,desktopFileName:"second.desktop",resourceClass:"second"});
const windows=[first,second].concat(extras.map(makeWindow));
globalThis.request={action:options.action,mode:"collect",desktopId:"desk",windows:[
  {key:"window:first",windowIds:["first"],pid:101},
  {key:"window:second",windowIds:["second"],pid:202}
]};
globalThis.resultService="test-result";
globalThis.workspace={
  windowList:function(){return windows;},currentDesktop:desktop,activeScreen:output,
  clientArea:function(){return {x:0,y:0,width:1200,height:800};},
  sendClientToScreen:function(window,target){window.output=target;}
};
globalThis.KWin={MaximizeArea:0};
globalThis.callDBus=function(service,path,iface,method,payload){process.stdout.write(payload);};
globalThis.QTimer=function(){this.start=function(){};};
eval(production);
'''
        completed = subprocess.run(
            ["node", "-e", harness, str(SOURCE), json.dumps({
                "extraWindows": extra_windows, "action": action})],
            capture_output=True, text=True, check=True, timeout=10)
        return json.loads(completed.stdout)

    def test_unrelated_unresolved_dialog_does_not_disable_batch(self):
        report=self.run_operation([{
            "id":"vpn-dialog","pid":303,"dialog":True,"normalWindow":False,
            "transient":True,"transientFor":None,
            "desktopFileName":"vpn.desktop","resourceClass":"vpn"
        }])
        self.assertTrue(report["ok"],report)
        self.assertEqual(report["outcome"],"confirmed")

    def test_same_process_unresolved_dialog_still_refuses_batch(self):
        report=self.run_operation([{
            "id":"first-dialog","pid":101,"dialog":True,"normalWindow":False,
            "transient":True,"transientFor":None,
            "desktopFileName":"first.desktop","resourceClass":"first"
        }])
        self.assertFalse(report["ok"],report)
        self.assertIn("relação de janela pai não resolvida",report["detail"])

    def test_same_application_class_unresolved_dialog_still_refuses_batch(self):
        report=self.run_operation([{
            "id":"first-helper-dialog","pid":404,"dialog":True,"normalWindow":False,
            "transient":True,"transientFor":None,
            "desktopFileName":"","resourceClass":"first"
        }])
        self.assertFalse(report["ok"],report)
        self.assertIn("relação de janela pai não resolvida",report["detail"])

    def test_unidentified_unresolved_dialog_keeps_conservative_refusal(self):
        report=self.run_operation([{
            "id":"unidentified-dialog","pid":0,"dialog":True,"normalWindow":False,
            "transient":True,"transientFor":None,
            "desktopFileName":"","resourceClass":""
        }])
        self.assertFalse(report["ok"],report)
        self.assertIn("relação de janela pai não resolvida",report["detail"])

    def test_preflight_reports_parent_relation_without_mutating_or_failing_transport(self):
        report=self.run_operation([{
            "id":"first-dialog","pid":101,"dialog":True,"normalWindow":False,
            "transient":True,"transientFor":None,
            "desktopFileName":"first.desktop","resourceClass":"first"
        }],action="preflight")
        self.assertTrue(report["ok"],report)
        self.assertEqual(report["outcome"],"preflight")
        self.assertFalse(report["available"])
        self.assertFalse(report["geometryAvailable"])
        self.assertIn("relação de janela pai não resolvida",report["detail"])

    def test_restore_keeps_parent_relation_guard(self):
        report=self.run_operation([{
            "id":"first-dialog","pid":101,"dialog":True,"normalWindow":False,
            "transient":True,"transientFor":None,
            "desktopFileName":"first.desktop","resourceClass":"first"
        }],action="restore")
        self.assertFalse(report["ok"],report)
        self.assertIn("relação de janela pai não resolvida",report["detail"])


if __name__ == "__main__":
    unittest.main()
