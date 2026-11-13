#!/usr/bin/env python3
"""Exercise the sender and Lua helpers without locating or contacting a MAME VM."""
import ctypes
import ctypes.util
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mame_control", HERE / "mame_control.py")
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class Lua:
    """Actual Lua 5.4 interpreter; MAME services below are isolated test doubles."""
    def __init__(self):
        name = ctypes.util.find_library("lua5.4")
        if not name:
            raise unittest.SkipTest("Offline Lua helpers require a local Lua 5.4 shared library")
        self.lib = ctypes.CDLL(name)
        self.lib.luaL_newstate.restype = ctypes.c_void_p
        self.lib.luaL_openlibs.argtypes = [ctypes.c_void_p]
        self.lib.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.lib.luaL_loadstring.restype = ctypes.c_int
        self.lib.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                      ctypes.c_int, ctypes.c_ssize_t, ctypes.c_void_p]
        self.lib.lua_pcallk.restype = ctypes.c_int
        self.lib.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
        self.lib.lua_tolstring.restype = ctypes.c_void_p
        self.lib.lua_settop.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.lua_close.argtypes = [ctypes.c_void_p]
        self.state = self.lib.luaL_newstate()
        self.lib.luaL_openlibs(self.state)

    def execute(self, source):
        self.lib.lua_settop(self.state, 0)
        status = self.lib.luaL_loadstring(self.state, source.encode())
        if not status:
            status = self.lib.lua_pcallk(self.state, 0, 1, 0, 0, None)
        size = ctypes.c_size_t()
        pointer = self.lib.lua_tolstring(self.state, -1, ctypes.byref(size))
        value = ctypes.string_at(pointer, size.value).decode() if pointer else "nil"
        if status:
            raise RuntimeError(value)
        return value

    def close(self):
        self.lib.lua_close(self.state)


class SyntheticBridge:
    def __init__(self, base, delay=0):
        self.base, self.delay = base, delay
        self.stop = threading.Event()
        self.consumed = threading.Event()
        self.count = 0
        self.error = None
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        lua = Lua()
        try:
            while not self.stop.is_set():
                command = self.base / "command.lua"
                if not command.exists():
                    time.sleep(0.005)
                    continue
                running = self.base / "command.running.lua"
                command.rename(running)
                source = running.read_text()
                self.consumed.set()
                time.sleep(self.delay)
                value = lua.execute(source)
                with (self.base / "result.txt").open("a") as handle:
                    handle.write(value + "\n")
                running.unlink()
                self.count += 1
        except Exception as error:
            self.error = error
        finally:
            lua.close()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(2)
        if self.error:
            raise self.error


class SenderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="mame-skill-offline-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)

    def test_correlated_unicode_and_literal_code(self):
        (self.base / "result.txt").write_text("MAME_LIVE_REPLY:" + "a" * 32 + ":OK:7374616c65\n")
        text = 'cores: ação; "quotes", $HOME, `literal`, % e\nnova linha'
        with SyntheticBridge(self.base) as bridge, control.Channel(self.base) as channel:
            reply = channel.call("return " + control.lua_string(text), 2)
            self.assertEqual(reply["value"], text)
            self.assertEqual(reply["status"], "OK")
            self.assertFalse((self.base / control.PENDING).exists())
        self.assertEqual(bridge.count, 1)

    def test_lua_error_is_correlated_without_retry(self):
        with SyntheticBridge(self.base) as bridge, control.Channel(self.base) as channel:
            reply = channel.call("error('controlled failure')", 2)
            self.assertEqual(reply["status"], "ERR")
            self.assertIn("controlled failure", reply["value"])
        self.assertEqual(bridge.count, 1)

    def test_existing_command_not_overwritten(self):
        path = self.base / "command.lua"
        path.write_text("return 'previous controller'")
        with control.Channel(self.base) as channel:
            with self.assertRaises(control.ChannelError):
                channel.call("return 'replacement'", 0.05)
        self.assertEqual(path.read_text(), "return 'previous controller'")
        self.assertFalse((self.base / control.PENDING).exists())

    def test_second_controller_cannot_overlap(self):
        with control.Channel(self.base):
            with self.assertRaises(control.ChannelError):
                with control.Channel(self.base):
                    self.fail("Lock accepted a second controller")
        self.assertFalse((self.base / "command.lua").exists())

    def test_timeout_unknown_retained_late_reply_acknowledged(self):
        with SyntheticBridge(self.base, delay=0.25) as bridge:
            with control.Channel(self.base) as channel:
                with self.assertRaises(control.RequestTimeout):
                    channel.call("return 'late but executed once'", 0.05)
                self.assertTrue(bridge.consumed.is_set())
                self.assertIsNotNone(channel.pending())
                with self.assertRaises(control.ChannelError):
                    channel.call("return 'duplicate'", 0.05)
                with self.assertRaises(control.ChannelError):
                    channel.status(acknowledge=True)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline and channel.status()["reply"] is None:
                    time.sleep(0.01)
                self.assertEqual(channel.status()["reply"]["value"], "late but executed once")
                deadline = time.monotonic() + 1
                while (self.base / "command.running.lua").exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(channel.status(acknowledge=True)["acknowledged"])
        self.assertEqual(bridge.count, 1)
        self.assertFalse((self.base / control.PENDING).exists())

    def test_symlink_result_rejected(self):
        victim = self.base / "unchanged"
        victim.write_text("original")
        (self.base / "result.txt").symlink_to(victim)
        with control.Channel(self.base) as channel:
            with self.assertRaises(OSError):
                channel.call("return 'unused'", 0.05)
        self.assertEqual(victim.read_text(), "original")
        self.assertFalse((self.base / "command.lua").exists())

    def test_encoded_limit_rejected_before_publication(self):
        with control.Channel(self.base) as channel:
            with self.assertRaises(control.ChannelError):
                channel.call("x" * (control.MAX_COMMAND // 3), 0.05)
        self.assertFalse((self.base / "command.lua").exists())
        self.assertFalse((self.base / control.PENDING).exists())

    def test_explicit_pointer_discovery(self):
        pointer = self.base / "pointer"
        pointer.write_text(str(self.base))
        self.assertEqual(control.discover(None, str(pointer)), self.base)

    def test_partial_reply_is_not_accepted_before_newline(self):
        request_id = "c" * 32
        record = {"request_id": request_id, "result_offset": 0}
        result = self.base / "result.txt"
        result.write_text(control.MARKER + request_id + ":OK:6162")
        with control.Channel(self.base) as channel:
            self.assertIsNone(channel.reply(record))
            with result.open("a") as handle:
                handle.write("6364\n")
            self.assertEqual(channel.reply(record)["value"], "abcd")


MOCK_MAME = '''
now=0; overrides=0; clears=0; mouse_option=true; subscriptions={}; stop_callbacks={}
function field(initial)
 local f={mask=255,initial=initial,sequences={standard='physical',increment='inc',decrement='dec'}}
 function f:set_value(v) self.override=v;overrides=overrides+1;if self.throw then error('input failure')end end
 function f:clear_value()self.override=nil;clears=clears+1 end
 function f:input_seq(kind)return self.sequences[kind]end
 function f:set_input_seq(kind,value)self.sequences[kind]=value end
 return f
end
button=field(0);xfield=field(250);yfield=field(5)
ports={buttons={fields={left=button}},x={fields={x=xfield}},y={fields={y=yfield}}}
for _,p in pairs(ports)do
 function p:field(mask)for _,v in pairs(self.fields)do if v.mask==mask then return v end end end
 function p:read()for _,v in pairs(self.fields)do return v.override or v.initial end end
end
manager={ui={ui_active=false},machine={
 video={frameskip=4,throttled=false},paused=false,ioport={ports=ports},screens={primary={}},
 time={as_double=function()return now end},
 options={entries={mouse={value=function(_,v)mouse_option=v end}}},
 input={code_from_token=function(_,t)return t end,code_pressed=function(_,t)return pressed and pressed[t]or false end}
}}
emu={
 input_seq=function(value)return value or 'empty'end,
 register_periodic=function(fn)periodic=fn end,
 register_stop=function(fn)stop_callbacks[#stop_callbacks+1]=fn end,
 add_machine_frame_notifier=function(fn)
  local s={fn=fn,unsubscribed=false};function s:unsubscribe()self.unsubscribed=true end
  subscriptions[#subscriptions+1]=s;return s
 end
}
function tick(at)
 now=at;for _,s in ipairs(subscriptions)do if not s.unsubscribed then s.fn()end end
end
'''


class LuaHelpersTests(unittest.TestCase):
    def setUp(self):
        self.lua = Lua()
        self.addCleanup(self.lua.close)
        self.lua.execute(MOCK_MAME)

    def load(self, name):
        return self.lua.execute((HERE / name).read_text())

    def test_probe_reads_profile_without_input(self):
        value = self.load("readonly_probe.lua")
        self.assertIn("frameskip=4", value)
        self.assertIn("throttled=false", value)
        self.assertEqual(self.lua.execute("return overrides..':'..clears..':'..tostring(mouse_option)"), "0:0:true")

    def test_hold_returns_to_release_and_preserves_video(self):
        self.load("mame_mouse_control.lua")
        self.assertEqual(self.lua.execute("return overrides"), "0")
        self.lua.execute("mame_live_mouse.hold({port='buttons',mask=255,seconds=.8,confirm_target=true})")
        self.assertEqual(self.lua.execute("return button.override"), "1")
        self.lua.execute("tick(.9)")
        self.assertEqual(self.lua.execute("return tostring(button.override)..':'..tostring(mame_live_mouse.operation.done)..':'..clears"), "nil:true:1")
        self.assertEqual(self.lua.execute("return manager.machine.video.frameskip..':'..tostring(manager.machine.video.throttled)"), "4:false")

    def test_hold_setup_error_releases_override(self):
        self.load("mame_mouse_control.lua")
        self.lua.execute("button.throw=true")
        with self.assertRaises(RuntimeError):
            self.lua.execute("mame_live_mouse.hold({port='buttons',mask=255,confirm_target=true})")
        self.assertEqual(self.lua.execute("return tostring(button.override)..':'..tostring(mame_live_mouse.operation.done)..':'..clears"), "nil:true:1")

    def test_callback_error_releases_and_reports(self):
        self.load("mame_mouse_control.lua")
        self.lua.execute("mame_live_mouse.hold({port='buttons',mask=255,confirm_target=true});manager.machine.time.as_double=function()error('clock failure')end;subscriptions[1].fn()")
        self.assertEqual(self.lua.execute("return tostring(button.override)..':'..tostring(mame_live_mouse.operation.done)"), "nil:true")
        self.assertIn("clock failure", self.lua.execute("return mame_live_mouse.operation.error"))

    def test_input_ownership_and_explicit_release(self):
        self.load("mame_mouse_control.lua")
        self.lua.execute("mame_live_mouse.hold({port='buttons',mask=255,confirm_target=true})")
        with self.assertRaises(RuntimeError):
            self.lua.execute("mame_live_mouse.hold({port='buttons',mask=255,confirm_target=true})")
        self.lua.execute("mame_live_mouse.release()")
        self.assertEqual(self.lua.execute("return tostring(button.override)..':'..tostring(mame_live_mouse.operation.done)"), "nil:true")

    def test_counter_wrap_and_stop_cleanup(self):
        self.load("mame_mouse_control.lua")
        self.lua.execute("mame_live_mouse.move_counters({x_port='x',x_mask=255,y_port='y',y_mask=255,dx=3,dy=-1,steps=3,frame_interval=1,confirm_counter_protocol=true})")
        self.lua.execute("tick(.1);tick(.2);tick(.3)")
        self.assertEqual(self.lua.execute("return xfield.override..':'..yfield.override"), "3:2")
        self.lua.execute("stop_callbacks[1]()")
        self.assertEqual(self.lua.execute("return tostring(xfield.override)..':'..tostring(yfield.override)..':'..tostring(mame_live_mouse.operation.done)"), "nil:nil:true")

    def test_cleanup_failure_blocks_more_input_then_explicit_retry(self):
        self.load("mame_mouse_control.lua")
        self.lua.execute("mame_live_mouse.hold({port='buttons',mask=255,confirm_target=true});saved_clear=button.clear_value;button.clear_value=function()error('release failure')end;tick(.9)")
        self.assertIn("release failure", self.lua.execute("return mame_live_mouse.operation.cleanup_error"))
        with self.assertRaises(RuntimeError):
            self.lua.execute("mame_live_mouse.hold({port='buttons',mask=255,confirm_target=true})")
        self.lua.execute("button.clear_value=saved_clear;mame_live_mouse.release()")
        self.assertEqual(self.lua.execute("return tostring(button.override)..':'..tostring(mame_live_mouse.operation.cleanup_error)"), "nil:nil")

    def test_capture_hook_release_recapture_wait_for_button_up(self):
        self.lua.execute("MAME_MOUSE_CAPTURE_CONFIG={port_tags={'buttons','x','y'},expected_fields=3}")
        self.load("mame_mouse_capture.lua")
        self.lua.execute("pressed={KEYCODE_RALT=true};periodic()")
        self.assertEqual(self.lua.execute("return tostring(mame_live_mouse_host.captured)..':'..button.sequences.standard"), "false:empty")
        self.lua.execute("pressed={MOUSECODE_1_BUTTON1=true};periodic()")
        self.assertEqual(self.lua.execute("return tostring(mame_live_mouse_host.captured)..':'..tostring(mame_live_mouse_host.wait_button_up)..':'..button.sequences.standard"), "true:true:empty")
        self.lua.execute("pressed={};periodic()")
        self.assertEqual(self.lua.execute("return tostring(mame_live_mouse_host.wait_button_up)..':'..button.sequences.standard"), "false:physical")

    def test_existing_capture_hook_preserved(self):
        self.lua.execute("domainos_mouse_host={captured=false};MAME_MOUSE_CAPTURE_CONFIG={port_tags={'buttons'}}")
        with self.assertRaises(RuntimeError):
            self.load("mame_mouse_capture.lua")
        self.assertEqual(self.lua.execute("return tostring(domainos_mouse_host.captured)..':'..overrides..':'..clears"), "false:0:0")

    def test_optional_bridge_executes_one_complete_command(self):
        with tempfile.TemporaryDirectory(prefix="mame-bridge-offline-") as directory:
            base = Path(directory)
            self.lua.execute("os.getenv=function(name)if name=='MAME_CONTROL_DIR'then return " + control.lua_string(directory) + " end end")
            self.load("mame_bridge.lua")
            request_id = "b" * 32
            (base / "command.lua").write_text(control.packet("return 'one execution'", request_id))
            self.lua.execute("periodic();periodic()")
            self.assertEqual(self.lua.execute("return mame_live_bridge.commands"), "1")
            self.assertIn(control.MARKER + request_id + ":OK:", (base / "result.txt").read_text())
            self.assertFalse((base / "command.running.lua").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
