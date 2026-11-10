# SPDX-License-Identifier: GPL-3.0-or-later
"""Broadcast GTK2's native X11 RC reload event to top-level client windows.

The traversal and event layout follow GTK 2.24's
gdk_screen_broadcast_client_message() implementation. GTK2 has no native
Wayland reload signal. This notifier uses DISPLAY, which may address XWayland
inside a Wayland session; the companion bridge calls it when the generated
GTK2 RC/pixmap bundle changes and native reload is required. Whether a live
GTK2 application receives and applies the event remains a separate validation.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os


class _ClientMessageData(ctypes.Union):
    _fields_ = [('b', ctypes.c_char * 20),
                ('s', ctypes.c_short * 10),
                ('l', ctypes.c_long * 5)]


class _XClientMessageEvent(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int),
                ('serial', ctypes.c_ulong),
                ('send_event', ctypes.c_int),
                ('display', ctypes.c_void_p),
                ('window', ctypes.c_ulong),
                ('message_type', ctypes.c_ulong),
                ('format', ctypes.c_int),
                ('data', _ClientMessageData)]


class _XEvent(ctypes.Union):
    _fields_ = [('xclient', _XClientMessageEvent),
                ('pad', ctypes.c_long * 24)]


class _XErrorEvent(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int),
                ('display', ctypes.c_void_p),
                ('resourceid', ctypes.c_ulong),
                ('serial', ctypes.c_ulong),
                ('error_code', ctypes.c_ubyte),
                ('request_code', ctypes.c_ubyte),
                ('minor_code', ctypes.c_ubyte)]


_XErrorHandler = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                  ctypes.POINTER(_XErrorEvent))
_CLIENT_MESSAGE = 33
_ANY_PROPERTY_TYPE = 0
_MAX_DEPTH = 64
_MAX_WINDOWS = 65536


def _library():
    name = ctypes.util.find_library('X11')
    if not name:
        raise RuntimeError('libX11 não está disponível para recarregar GTK2.')
    x11 = ctypes.CDLL(name)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.restype = ctypes.c_int
    x11.XRootWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XRootWindow.restype = ctypes.c_ulong
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XGetWindowProperty.argtypes = [
        ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_long,
        ctypes.c_long, ctypes.c_int, ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_void_p)]
    x11.XGetWindowProperty.restype = ctypes.c_int
    x11.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),
        ctypes.POINTER(ctypes.c_uint)]
    x11.XQueryTree.restype = ctypes.c_int
    x11.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
        ctypes.c_int, ctypes.c_long, ctypes.POINTER(_XEvent)]
    x11.XSendEvent.restype = ctypes.c_int
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XSetErrorHandler.argtypes = [ctypes.c_void_p]
    x11.XSetErrorHandler.restype = ctypes.c_void_p
    x11.XFree.argtypes = [ctypes.c_void_p]
    x11.XFree.restype = ctypes.c_int
    return x11


def reload_open_windows(display_name: str | None = None) -> dict:
    """Send _GTK_READ_RCFILES to GTK2-style top-level X11 clients.

    GTK2's own broadcast algorithm identifies top-levels by WM_STATE and
    traverses the X tree. Other toolkits receive an unhandled ClientMessage,
    which they ignore. A target that disappears during traversal is skipped.
    """
    if display_name is None:
        display_name = os.environ.get('DISPLAY')
    if not display_name:
        raise RuntimeError('DISPLAY indisponível; GTK2 só pode recarregar por X11.')

    x11 = _library()
    display = x11.XOpenDisplay(os.fsencode(display_name))
    if not display:
        raise RuntimeError('Não foi possível abrir o DISPLAY para recarregar GTK2.')

    xerrors = []

    @_XErrorHandler
    def ignore_racing_window(_display, event):
        if event:
            xerrors.append(int(event.contents.error_code))
        return 0

    old_handler = x11.XSetErrorHandler(
        ctypes.cast(ignore_racing_window, ctypes.c_void_p))
    sent = 0
    considered = 0
    nodes = 0
    too_many = False
    try:
        root = x11.XRootWindow(display, x11.XDefaultScreen(display))
        wm_state = x11.XInternAtom(display, b'WM_STATE', 0)
        reload_atom = x11.XInternAtom(display, b'_GTK_READ_RCFILES', 0)
        if not wm_state or not reload_atom:
            raise RuntimeError('O servidor X11 não criou os átomos necessários.')

        event = _XEvent()
        event.xclient.type = _CLIENT_MESSAGE
        event.xclient.serial = 0
        event.xclient.send_event = 1
        event.xclient.display = display
        event.xclient.message_type = reload_atom
        event.xclient.format = 32
        for index in range(5):
            event.xclient.data.l[index] = 0

        def visit(window: int, level: int) -> bool:
            nonlocal sent, considered, nodes, too_many
            nodes += 1
            if nodes > _MAX_WINDOWS or level > _MAX_DEPTH:
                too_many = True
                return False

            actual_type = ctypes.c_ulong()
            actual_format = ctypes.c_int()
            nitems = ctypes.c_ulong()
            remaining = ctypes.c_ulong()
            prop = ctypes.c_void_p()
            status = x11.XGetWindowProperty(display, window, wm_state,
                0, 0, 0, _ANY_PROPERTY_TYPE, ctypes.byref(actual_type),
                ctypes.byref(actual_format), ctypes.byref(nitems),
                ctypes.byref(remaining), ctypes.byref(prop))
            if prop.value:
                x11.XFree(prop)
            if status != 0:
                return False

            found = False
            if actual_type.value:
                considered += 1
                event.xclient.window = window
                if x11.XSendEvent(display, window, 0, 0, ctypes.byref(event)):
                    sent += 1
                found = True
            else:
                child_root = ctypes.c_ulong()
                parent = ctypes.c_ulong()
                children = ctypes.POINTER(ctypes.c_ulong)()
                count = ctypes.c_uint()
                if not x11.XQueryTree(display, window, ctypes.byref(child_root),
                        ctypes.byref(parent), ctypes.byref(children), ctypes.byref(count)):
                    return False
                try:
                    if count.value > _MAX_WINDOWS - nodes:
                        too_many = True
                        return False
                    for index in range(count.value):
                        if visit(int(children[index]), level + 1):
                            found = True
                finally:
                    if children:
                        x11.XFree(children)

            # Match GTK2: if a direct root child has no WM_STATE descendants,
            # send to that child as a fallback for unmanaged top-levels.
            if not found and level == 1:
                considered += 1
                event.xclient.window = window
                if x11.XSendEvent(display, window, 0, 0, ctypes.byref(event)):
                    sent += 1
            return found or level == 1

        visit(int(root), 0)
        x11.XSync(display, 0)
        if too_many:
            raise RuntimeError('A árvore X11 excedeu os limites de recarga GTK2.')
        return {'status': 'sent' if sent else 'no_windows',
                'windows_considered': considered,
                'events_sent': sent,
                'racing_x_errors': len(xerrors)}
    finally:
        x11.XSync(display, 0)
        x11.XSetErrorHandler(old_handler)
        x11.XCloseDisplay(display)
