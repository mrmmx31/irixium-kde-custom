# SPDX-License-Identifier: GPL-3.0-or-later
"""Main-thread private GTK4 X11 hosting boundary with process identity checks.

Caller must establish private_namespace before creating GTK or this bridge.
Canvas markers are coordination, not a security boundary on a shared X server.
"""
import ctypes as C
import os
from pathlib import Path
import threading
import time
from gtk4_push_api import bind


def process_identity(pid):
    if type(pid) is not int or pid <= 0:
        raise ValueError('Invalid host PID')
    directory = Path('/proc') / str(pid)
    if directory.stat().st_uid != os.getuid():
        raise ValueError('Host PID belongs to another user')
    fields = (directory / 'stat').read_text().rpartition(')')[2].split()
    if len(fields) < 20 or fields[0] in ('Z', 'X'):
        raise ValueError('Host process unavailable')
    return fields[19]  # Kernel start ticks, after the command field.


class HostBridge:
    def __init__(self, library, canvas, pid):
        self._main_thread()
        if type(canvas) is not int or not 1 <= canvas <= 0xffffffff:
            raise ValueError('Invalid canvas XID')
        self.pid, self.start = pid, process_identity(pid)
        native = C.CDLL(str(Path(library).resolve()))
        if bind(native, 'tl_gtk4_host_abi', C.c_int)() != 1:
            raise ValueError('GTK4 host ABI mismatch')
        self._open = bind(native, 'tl_gtk4_host_open', C.c_void_p,
                          C.c_ulong, C.c_ulong, C.c_ulong)
        self._attach = bind(native, 'tl_gtk4_host_attach', C.c_int, C.c_void_p, C.c_ulong)
        self._attach_status = bind(native, 'tl_gtk4_host_attach_status', C.c_int, C.c_void_p)
        self._poll = bind(native, 'tl_gtk4_host_poll', C.c_int, C.c_void_p,
                          C.POINTER(C.c_int), C.POINTER(C.c_int))
        self._traverse = bind(native, 'tl_gtk4_host_traverse', C.c_int, C.c_void_p, C.c_int)
        self._result = bind(native, 'tl_gtk4_host_traversal_result', C.c_int,
                            C.c_void_p, C.POINTER(C.c_ulong), C.POINTER(C.c_int))
        self._close = bind(native, 'tl_gtk4_host_close', None, C.c_void_p)
        self.handle = self._open(canvas, pid, os.getuid())
        if not self.handle:
            raise ValueError('Unavailable or unmarked Motif canvas')

    @staticmethod
    def _main_thread():
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError('GTK4 X11 host requires the main thread')

    def attach(self, child, timeout=1.0, clock=time.monotonic, sleeper=time.sleep,
               progress=None):
        self._main_thread()
        if not self.handle or process_identity(self.pid) != self.start:
            raise RuntimeError('Motif host identity changed')
        if type(child) is not int or not 1 <= child <= 0xffffffff:
            raise ValueError('Invalid GTK4 child XID')
        if progress is not None and not callable(progress):
            raise ValueError('GTK4 attach progress callback must be callable')
        deadline=clock()+timeout
        while not self._attach(self.handle, child):
            if process_identity(self.pid) != self.start:
                raise RuntimeError('Motif host identity changed')
            if clock()>=deadline:
                code=self._attach_status(self.handle) if hasattr(self,'_attach_status') else 0
                reasons={1:'host canvas identity',2:'child PID property missing',
                         3:'child PID property differs',4:'child attributes unavailable',
                         5:'child root or class differs',7:'child was not reparented'}
                detail=('X11 error code '+str(code-100) if code>=100 else
                        reasons.get(code,'unknown validation'))
                raise ValueError('GTK4 child unavailable or cannot be attached: '+detail)
            if progress is not None:
                progress()
            sleeper(0.005)

    def poll(self):
        self._main_thread()
        if not self.handle:
            return None
        try:
            if process_identity(self.pid) != self.start:
                return None
        except (FileNotFoundError, ValueError):
            return None
        width, height = C.c_int(), C.c_int()
        if not self._poll(self.handle, C.byref(width), C.byref(height)):
            return None
        return width.value, height.value

    def close(self):
        self._main_thread()
        if self.handle:
            self._close(self.handle)
            self.handle = None

    def traverse(self, backward=False):
        self._main_thread()
        if type(backward) is not bool:
            raise ValueError('Traversal direction must be boolean')
        if self.poll() is None or not self._traverse(self.handle, int(backward)):
            raise RuntimeError('GTK4 host traversal unavailable')

    def traversal_result(self):
        self._main_thread()
        if self.poll() is None:
            return None
        sequence, completed = C.c_ulong(), C.c_int()
        if not self._result(self.handle, C.byref(sequence), C.byref(completed)):
            return None
        return {'sequence':sequence.value,'completed':bool(completed.value)}
