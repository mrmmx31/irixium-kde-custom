# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded private Motif/X11 hosting experiment, not a public GTK4 adapter."""
import ctypes as C
import select
import subprocess
import os
import time
import json


class MotifHost:
    def __init__(self, binary, bind, focus_mode=False):
        self.process = subprocess.Popen([str(binary)] + (['--focus-fixture'] if focus_mode else []), stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True)
        self.display = None
        self.bridge = None
        self.guard_proof = None
        try:
            self.canvas = int(self.read_line())
            self.focus_widgets = json.loads(self.read_line()) if focus_mode else None
            if self.canvas <= 0 or self.process.poll() is not None:
                raise RuntimeError('Motif host canvas unavailable')
            self.xlib = C.CDLL('libX11.so.6')
            p, w, i = C.c_void_p, C.c_ulong, C.c_int
            self.open = bind(self.xlib, 'XOpenDisplay', p, C.c_char_p)
            self.close_display = bind(self.xlib, 'XCloseDisplay', i, p)
            self.reparent = bind(self.xlib, 'XReparentWindow', i, p, w, w, i, i)
            self.resize = bind(self.xlib, 'XResizeWindow', i, p, w, C.c_uint, C.c_uint)
            self.sync = bind(self.xlib, 'XSync', i, p, i)
            self.query_tree = bind(self.xlib, 'XQueryTree', i, p, w,
                                   C.POINTER(w), C.POINTER(w),
                                   C.POINTER(C.POINTER(w)), C.POINTER(C.c_uint))
            self.free = bind(self.xlib, 'XFree', i, p)
            self.display = self.open(None)
            if not self.display:
                raise RuntimeError('Private X11 display unavailable')
        except BaseException:
            self.close()
            raise

    def read_line(self, timeout=5):
        deadline = time.monotonic() + timeout
        result = bytearray()
        while len(result) < 4096:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError('Motif observation deadline expired')
            ready, _, _ = select.select([self.process.stdout.fileno()], [], [], remaining)
            if not ready:
                raise RuntimeError('Motif observation deadline expired')
            byte = os.read(self.process.stdout.fileno(), 1)
            if not byte:
                raise RuntimeError('Motif host output closed')
            if byte == b'\n':
                return result.decode('utf-8')
            result.extend(byte)
        raise RuntimeError('Motif host output exceeds4KiB')

    def attach(self, child, bridge_library=None):
        if bridge_library is not None:
            from gtk4_host import HostBridge
            try:
                HostBridge(bridge_library, 0xffffffff, self.process.pid)
                raise AssertionError('Missing X11 target accepted')
            except ValueError as error:
                assert 'unmarked Motif canvas' in str(error)
            self.bridge = HostBridge(bridge_library, self.canvas, self.process.pid)
            try:
                self.bridge.attach(self.canvas)
                raise AssertionError('Foreign/unowned child accepted')
            except ValueError as error:
                assert 'not owned' in str(error)
            self.bridge.attach(child)
            assert self.bridge.poll() == (360, 240)
            self.guard_proof = {'missing_canvas_refused': True,
                                'unowned_child_refused': True}
            return
        self.reparent(self.display, child, self.canvas, 0, 0)
        self.sync(self.display, 0)
        actual = self.parent(child)
        assert actual == self.canvas, {'child': child, 'expected_parent': self.canvas,
                                      'actual_parent': actual}

    def parent(self, child):
        w = C.c_ulong
        root, parent, count = w(), w(), C.c_uint()
        children = C.POINTER(w)()
        if not self.query_tree(self.display, child, C.byref(root), C.byref(parent),
                               C.byref(children), C.byref(count)):
            raise RuntimeError('Private child identity no longer exists')
        if children:
            self.free(children)
        return parent.value

    def close(self):
        if self.bridge:
            self.bridge.close()
            self.bridge = None
        if self.display:
            self.close_display(self.display)
            self.display = None
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        self.process.stdout.close()
