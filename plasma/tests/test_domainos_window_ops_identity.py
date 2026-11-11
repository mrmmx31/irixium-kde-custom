#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify XRes-backed identities for legacy X11 window operations."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel/contents/code/window_ops.py"
SPEC = importlib.util.spec_from_file_location("domainos_window_ops", SOURCE)
WINDOW_OPS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WINDOW_OPS)


class X11IdentityAuthentication(unittest.TestCase):
    def request(self, *, pid=2675062, marker=None):
        window = {"key": "window:54525976", "windowIds": [54525976], "pid": pid}
        if marker is not None:
            window["x11PidAuthenticated"] = marker
        return {"action": "preflight", "windows": [window]}

    def test_xres_match_adds_private_authentication_marker(self):
        with mock.patch.object(WINDOW_OPS, "x11_client_pid", return_value=2675062):
            result = WINDOW_OPS.authenticate_x11_identities(self.request())
        self.assertTrue(result["windows"][0]["x11PidAuthenticated"])

    def test_incoming_marker_is_not_trusted_when_xres_pid_differs(self):
        with mock.patch.object(WINDOW_OPS, "x11_client_pid", return_value=999999):
            with self.assertRaisesRegex(RuntimeError, "outro processo"):
                WINDOW_OPS.authenticate_x11_identities(self.request(marker=True))

    def test_uuid_identity_drops_spoofed_x11_marker_without_xres(self):
        request = {"action": "preflight", "windows": [{
            "key": "window:9088f311-4b21-4072-bdcb-c395cb849f66",
            "windowIds": ["9088f311-4b21-4072-bdcb-c395cb849f66"],
            "pid": 2674714,
            "x11PidAuthenticated": True,
        }]}
        with mock.patch.object(WINDOW_OPS, "x11_client_pid") as xres:
            result = WINDOW_OPS.authenticate_x11_identities(request)
        xres.assert_not_called()
        self.assertNotIn("x11PidAuthenticated", result["windows"][0])


@unittest.skipUnless(shutil.which("node"), "Node is required for the production KWin JavaScript")
class LegacyX11KWinResolution(unittest.TestCase):
    def resolve(self, *, kwin_pid, authenticated):
        source = SOURCE.with_suffix(".js")
        harness = r'''
const fs=require("fs");
const production=fs.readFileSync(process.argv[1],"utf8");
const options=JSON.parse(process.argv[2]);
const desktop={id:"desk",x11DesktopNumber:1};
const output={name:"screen"};
const window={internalId:"legacy",pid:options.kwinPid,caption:"Legacy X11",
 normalWindow:true,dialog:false,specialWindow:false,deleted:false,
 transient:false,modal:false,transientFor:null,desktopFileName:"",resourceClass:"legacy",
 frameGeometry:{x:0,y:0,width:300,height:200},minSize:{width:0,height:0},
 maxSize:{width:2147483647,height:2147483647},tile:null,desktops:[desktop],output:output,
 moveable:true,resizeable:true,minimized:false,maximizeMode:0};
const record={key:"window:54525976",windowIds:[54525976],pid:2675062};
if (options.authenticated) record.x11PidAuthenticated=true;
globalThis.request={action:"preflight",windows:[record]};
globalThis.resultService="test-result";
globalThis.workspace={windowList:function(){return [window];},getClient:function(){return window;},
 currentDesktop:desktop,activeScreen:output,activeWindow:null};
globalThis.callDBus=function(service,path,iface,method,payload){process.stdout.write(payload);};
eval(production);
'''
        completed = subprocess.run(["node", "-e", harness, str(source), json.dumps({
            "kwinPid": kwin_pid, "authenticated": authenticated,
        })], capture_output=True, text=True, check=True, timeout=10)
        return json.loads(completed.stdout)

    def test_kWin_pid_zero_accepts_only_xres_authenticated_record(self):
        accepted = self.resolve(kwin_pid=0, authenticated=True)
        refused = self.resolve(kwin_pid=0, authenticated=False)
        self.assertTrue(accepted["available"], accepted)
        self.assertFalse(refused["available"], refused)
        self.assertIn("identidade de processo", refused["detail"])

    def test_nonzero_kwin_pid_mismatch_is_not_overridden_by_marker(self):
        refused = self.resolve(kwin_pid=12345, authenticated=True)
        self.assertFalse(refused["available"], refused)
        self.assertIn("identidade de processo", refused["detail"])


if __name__ == "__main__":
    unittest.main()
