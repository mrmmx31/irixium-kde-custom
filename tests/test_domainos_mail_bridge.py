#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded native framing, private registration and extension failure boundaries."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "integrations/thunderbird-domainos"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HOST = load("domainos_mail_host", BRIDGE / "native_host.py")
INSTALL = load("domainos_mail_install", BRIDGE / "install.py")


def message(available=True, count=3):
    return {"schema": 1, "type": "counts", "available": available, "unreadCount": count}


def frame(value):
    raw = json.dumps(value).encode()
    return struct.pack("<I", len(raw)) + raw


class MailBridge(unittest.TestCase):
    def test_fragmented_and_concatenated_frames_keep_known_zero_distinct_from_unknown(self):
        parser = HOST.Framing()
        raw = frame(message(True, 0)) + frame(message(False, None))
        values = []
        for byte in raw:
            values.extend(parser.feed(bytes([byte])))
        self.assertEqual(values, [(True, 0), (False, None)])
        self.assertEqual(parser.buffer, bytearray())

    def test_extra_identifying_data_and_invalid_counts_are_rejected(self):
        invalid = [dict(message(), account="private-account"), message(True, True),
            message(True, -1), message(True, 0.5), message(True, HOST.MAX_COUNT + 1),
            message(False, 0), dict(message(), available="true"), dict(message(), schema=True)]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                HOST.Framing().feed(frame(value))

    def test_frame_bounds_and_bad_encoding_are_rejected_without_unbounded_buffer(self):
        for size in (0, HOST.MAX_FRAME + 1, 0xffffffff):
            with self.subTest(size=size), self.assertRaises(ValueError):
                HOST.Framing().feed(struct.pack("<I", size))
        with self.assertRaises(UnicodeError):
            HOST.Framing().feed(struct.pack("<I", 1) + b"\xff")
        parser = HOST.Framing()
        parser.feed(struct.pack("<I", HOST.MAX_FRAME) + b"x" * (HOST.MAX_FRAME - 1))
        self.assertLessEqual(len(parser.buffer), HOST.MAX_FRAME + 4)

    def test_staged_installer_builds_deterministic_xpi_and_only_private_registration(self):
        with tempfile.TemporaryDirectory(prefix=".qa-mail-install-", dir=ROOT) as temp:
            paths = []
            for name in ("first", "second"):
                home, data = Path(temp) / name / "home", Path(temp) / name / "data"
                home.mkdir(parents=True); data.mkdir()
                result = INSTALL.install(home, data)
                manifest = Path(result["native_host_manifest"])
                installed = json.loads(manifest.read_text())
                self.assertEqual(installed["allowed_extensions"], [INSTALL.EXTENSION_ID])
                self.assertEqual(Path(installed["path"]).stat().st_mode & 0o777, 0o700)
                self.assertEqual(manifest.stat().st_mode & 0o777, 0o600)
                self.assertFalse((home / ".thunderbird").exists())
                paths.append(Path(result["xpi"]))
            self.assertEqual(*(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths))
            with zipfile.ZipFile(paths[0]) as archive:
                self.assertEqual(set(archive.namelist()), {"manifest.json", "background.js"})
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(set(manifest["permissions"]), {"accountsRead", "nativeMessaging"})
                self.assertNotIn("messagesRead", manifest["permissions"])

    def test_extension_coalesces_events_and_closes_failed_transport_without_retry_or_data_leak(self):
        # Execute the actual background script with the boundary supplied by the
        # WebExtension platform replaced; no message-content API is available.
        harness = r'''
const fs=require("fs"),vm=require("vm"),assert=require("assert");
const source=fs.readFileSync(process.argv[1],"utf8");
const settle=async()=>{for(let i=0;i<8;++i)await new Promise(setImmediate)};
function setup(options={}) {
  const listeners={},sent=[],warnings=[];let disconnects=0,connects=0,queries=0;
  let folderResult=[{id:"private-folder-a",name:"PRIVATE DATA"},{id:"private-folder-b"}];
  let infoResult={unreadMessageCount:2};
  const port={onDisconnect:{addListener:f=>listeners.disconnect=f},onMessage:{addListener:f=>listeners.message=f},
    postMessage:m=>{if(options.failPost)throw Error("PRIVATE DATA");sent.push(m)},
    disconnect:()=>{disconnects++;listeners.disconnect();if(options.failDisconnect)throw Error("PRIVATE DATA")}};
  const folders={query:async filter=>{queries++;assert.deepEqual(filter,{isRoot:false,isVirtual:false,isUnified:false,isTag:false});return folderResult},
    getFolderInfo:async id=>{if(infoResult instanceof Error)throw infoResult;return infoResult}};
  for(const key of ["onFolderInfoChanged","onCreated","onDeleted","onRenamed","onMoved","onUpdated"])
    folders[key]={addListener:f=>listeners[key]=f};
  const accounts={onCreated:{addListener:f=>listeners.accountCreated=f},onDeleted:{addListener:f=>listeners.accountDeleted=f}};
  const context=vm.createContext({console:{warn:t=>warnings.push(t)},messenger:{folders,accounts,runtime:{connectNative:name=>{connects++;assert.equal(name,"org.irixclassic.domainos.thunderbird");return port}}}});
  vm.runInContext(source,context);
  return {listeners,sent,warnings,setFolders:value=>folderResult=value,setInfo:value=>infoResult=value,
    stats:()=>({disconnects,connects,queries})};
}
(async()=>{
  const normal=setup();await settle();
  assert.equal(normal.sent.at(-1).unreadCount,4);
  assert.deepEqual(Object.keys(normal.sent.at(-1)).sort(),["available","schema","type","unreadCount"]);
  normal.setInfo(new Error("PRIVATE DATA"));await normal.listeners.onFolderInfoChanged();await settle();
  assert.equal(normal.sent.at(-1).available,false);assert.equal(normal.sent.at(-1).unreadCount,null);
  assert(!normal.warnings.join(" ").includes("PRIVATE DATA"));
  normal.setInfo({unreadMessageCount:0});await normal.listeners.onFolderInfoChanged();await settle();
  assert.equal(normal.sent.at(-1).available,true);assert.equal(normal.sent.at(-1).unreadCount,0);
  normal.setFolders([]);await normal.listeners.onDeleted();await settle();assert.equal(normal.sent.at(-1).available,false);
  const before=normal.sent.length;normal.listeners.disconnect();await normal.listeners.onCreated();await settle();
  assert.equal(normal.sent.length,before);assert.equal(normal.stats().connects,1);
  const broken=setup({failPost:true,failDisconnect:true});await settle();
  assert.equal(broken.stats().disconnects,1);await broken.listeners.onCreated();await settle();
  assert.equal(broken.stats().disconnects,1);assert.equal(broken.stats().connects,1);
  assert(!broken.warnings.join(" ").includes("PRIVATE DATA"));
  const rejected=setup({failDisconnect:true});await settle();rejected.listeners.message({ok:false});await settle();
  assert.equal(rejected.stats().disconnects,1);assert.equal(rejected.stats().connects,1);
  assert(!rejected.warnings.join(" ").includes("PRIVATE DATA"));
  // Hold the first query while several native events arrive. They request one
  // follow-up read, never overlapping reads or a periodic retry.
  const queries=[];let resolveFirst,concurrent=0,maximum=0;const events={};
  const event={addListener:f=>events.refresh=f};
  const folders={query:async()=>{const index=queries.length;queries.push(index);concurrent++;maximum=Math.max(maximum,concurrent);
    if(index===0)await new Promise(resolve=>resolveFirst=resolve);concurrent--;return [{id:"own"}]},getFolderInfo:async()=>({unreadMessageCount:1}),
    onFolderInfoChanged:event,onCreated:event,onDeleted:event,onRenamed:event,onMoved:event,onUpdated:event};
  const accountEvent={addListener:()=>{}};const ownPort={postMessage:()=>{},onDisconnect:{addListener:()=>{}},onMessage:{addListener:()=>{}}};
  const context=vm.createContext({console:{warn:()=>{}},messenger:{folders,accounts:{onCreated:accountEvent,onDeleted:accountEvent},runtime:{connectNative:()=>ownPort}}});
  vm.runInContext(source,context);for(let i=0;i<6;i++)events.refresh();resolveFirst();await settle();
  assert.equal(queries.length,2);assert.equal(maximum,1);await settle();assert.equal(queries.length,2);
  process.stdout.write(JSON.stringify({passed:true}));
})().catch(error=>{process.stderr.write(error.stack);process.exit(1)});
'''
        completed = subprocess.run(["node", "-e", harness, str(BRIDGE / "extension/background.js")],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {"passed": True})


if __name__ == "__main__":
    unittest.main()
