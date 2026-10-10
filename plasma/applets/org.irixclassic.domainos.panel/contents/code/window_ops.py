#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Transient KWin operations, scoped to fresh window identities in this session.

No persistent KWin script/configuration is installed. X11 uses getClient(WId),
Wayland uses internalId; both are checked against the current KWin window list.
Geometry completion is observed through frameGeometryChanged. A bounded watchdog
reports unconfirmed targets; it never postpones applying the requested geometry.
"""
import json
import ctypes
import ctypes.util
import os
from pathlib import Path
import signal
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True


def validate(request):
    action = request.get("action")
    if action not in ("layout", "inspect", "terminate-check"):
        raise ValueError("Unknown window operation")
    if action == "layout" and request.get("mode") not in ("columns", "rows", "mosaic", "maximize", "minimize", "collect"):
        raise ValueError("Unknown layout")
    windows = request.get("windows", [])
    if not isinstance(windows, list) or (action != "inspect" and not windows):
        raise ValueError("Expected selected windows")
    identities = set()
    for window in windows:
        ids = window.get("windowIds", [])
        if not isinstance(ids, list) or not ids or window.get("pid", 0) <= 0:
            raise ValueError("Window identity/PID unavailable")
        identity = str(ids[0])
        if identity in identities:
            raise ValueError("Duplicate window identity")
        identities.add(identity)
        if not (identity.isdecimal() or _uuid(identity)):
            raise ValueError("Invalid native window identity")
    return request


def _uuid(value):
    try:
        uuid.UUID(value.strip("{}"))
        return True
    except (ValueError, AttributeError):
        return False


def x11_client_pid(identifier):
    """Use the X server's authenticated local client PID, never _NET_WM_PID."""
    class Spec(ctypes.Structure):
        _fields_ = [("client", ctypes.c_ulong), ("mask", ctypes.c_uint)]
    class Value(ctypes.Structure):
        _fields_ = [("spec", Spec), ("length", ctypes.c_long), ("value", ctypes.c_void_p)]
    x11_name, res_name = ctypes.util.find_library("X11"), ctypes.util.find_library("XRes")
    if not x11_name or not res_name:
        raise RuntimeError("XRes client credential support is unavailable")
    x11, res = ctypes.CDLL(x11_name), ctypes.CDLL(res_name)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]; x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    res.XResQueryClientIds.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.POINTER(Spec), ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.POINTER(Value))]
    res.XResQueryClientIds.restype = ctypes.c_int
    res.XResGetClientPid.argtypes = [ctypes.POINTER(Value)]; res.XResGetClientPid.restype = ctypes.c_int
    res.XResClientIdsDestroy.argtypes = [ctypes.c_long, ctypes.POINTER(Value)]
    display = x11.XOpenDisplay(None)
    if not display:
        raise RuntimeError("The X11 display is unavailable")
    count, values = ctypes.c_long(0), ctypes.POINTER(Value)()
    try:
        spec = Spec(int(identifier), 2)  # XRES_CLIENT_ID_PID_MASK (XRes 1.2).
        if res.XResQueryClientIds(display, 1, ctypes.byref(spec), ctypes.byref(count), ctypes.byref(values)) != 0:
            # XResQueryClientIds follows the X extension's 0=Success convention.
            raise RuntimeError("The X server did not authenticate the local client PID")
        for index in range(count.value):
            pid = res.XResGetClientPid(ctypes.byref(values[index]))
            if pid > 0: return pid
        raise RuntimeError("This X11 client has no authenticated local PID")
    finally:
        if values: res.XResClientIdsDestroy(count, values)
        x11.XCloseDisplay(display)


def kwin_operation(request):
    validate(request)
    from PyQt6.QtCore import QCoreApplication, QObject, QTimer, pyqtClassInfo, pyqtSlot
    from PyQt6.QtDBus import QDBusConnection, QDBusMessage

    app = QCoreApplication.instance() or QCoreApplication(["domainos-window-operation"])
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        raise RuntimeError("Session D-Bus is unavailable")
    nonce = uuid.uuid4().hex
    service = "org.irixclassic.DomainOS.WindowOperation.n" + nonce
    name = "irixclassic-domainos-operation-" + nonce
    result = {}

    @pyqtClassInfo("D-Bus Interface", "org.irixclassic.DomainOS.WindowOperation")
    class Reply(QObject):
        @pyqtSlot(str)
        def completed(self, text):
            nonlocal result
            try:
                result = json.loads(text)
            except (ValueError, TypeError):
                result = {"ok": False, "outcome": "failed", "detail": "Invalid KWin response"}
            app.quit()

    endpoint = Reply()
    if not bus.registerService(service) or not bus.registerObject("/Result", endpoint, QDBusConnection.RegisterOption.ExportAllSlots):
        raise RuntimeError("Could not register operation result endpoint")

    def call(path, interface, method, args=()):
        message = QDBusMessage.createMethodCall("org.kde.KWin", path, interface, method)
        message.setArguments(list(args))
        reply = bus.call(message, timeout=5000)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise RuntimeError(reply.errorMessage())
        return reply.arguments()

    script_id = -1
    try:
        with tempfile.TemporaryDirectory(prefix="irix-domainos-operation-") as directory:
            script = Path(directory) / "operation.js"
            source = Path(__file__).with_name("window_ops.js").read_text()
            script.write_text("const request = " + json.dumps(request, ensure_ascii=True) + ";\n"
                + "const resultService = " + json.dumps(service) + ";\n" + source)
            loaded = call("/Scripting", "org.kde.kwin.Scripting", "loadScript", [str(script), name])
            script_id = loaded[0] if loaded else -1
            if not isinstance(script_id, int) or script_id < 0:
                raise RuntimeError("KWin rejected the transient operation script")
            call("/Scripting/Script" + str(script_id), "org.kde.kwin.Script", "run")
            if not result:
                # Communication watchdog only; commands already ran in KWin.
                QTimer.singleShot(7000, app.quit)
                app.exec()
            if not result:
                raise RuntimeError("KWin did not report the operation result")
            return result
    finally:
        if script_id >= 0:
            try:
                call("/Scripting", "org.kde.kwin.Scripting", "unloadScript", [name])
            except RuntimeError:
                pass
        bus.unregisterObject("/Result")
        bus.unregisterService(service)


def terminate(request):
    window = request.get("window", {})
    pid = window.get("pid", 0)
    if not isinstance(pid, int) or pid <= 1 or pid == os.getpid():
        raise ValueError("Process identity unavailable")
    if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
        raise RuntimeError("Safe process termination is unavailable on this system")
    # Holding a pidfd prevents sending a signal to a recycled PID after KWin's
    # fresh identity/sibling check. The helper never elevates its credentials.
    process = Path("/proc") / str(pid)
    if process.stat().st_uid != os.getuid():
        raise RuntimeError("The process belongs to another user")
    with os.fdopen(os.pidfd_open(pid), "rb", closefd=True) as pidfd:
        checked = kwin_operation({"action": "terminate-check", "windows": [window],
            "selectedKeys": request.get("selectedKeys", [])})
        if not checked.get("ok"):
            return checked
        if checked.get("x11") and x11_client_pid(window["windowIds"][0]) != pid:
            raise RuntimeError("The X server's client PID differs from the selected process")
        signal.pidfd_send_signal(pidfd.fileno(), signal.SIGKILL)
        return {"ok": True, "outcome": "signal-sent", "pid": pid,
                "detail": "Forced termination signal sent to the verified process; exit is not yet observed"}


def execute(request):
    if request.get("action") == "terminate":
        return terminate(request)
    return kwin_operation(request)


def main():
    request = {}
    try:
        if len(sys.argv) != 2:
            raise ValueError("Expected one JSON request")
        request = json.loads(sys.argv[1])
        if not isinstance(request, dict):
            raise ValueError("Expected a JSON object")
        result = execute(request)
    except (ValueError, RuntimeError, OSError, ImportError) as error:
        result = {"ok": False, "outcome": "failed", "detail": str(error)}
    result["token"] = request.get("token") if isinstance(request, dict) else None
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
