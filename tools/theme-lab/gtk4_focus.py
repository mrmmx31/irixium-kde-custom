# SPDX-License-Identifier: GPL-3.0-or-later
"""Boundary traversal for the current single-button GTK4 private scene."""
import ctypes as C
from gtk4_push_api import bind


def traversal_direction(keyval, modifiers):
    # Preserve modified application shortcuts. Shift+Tab is boundary traversal.
    if keyval not in (0xff09, 0xfe20) or modifiers & (4 | 8 | (7 << 26)):
        return None
    return bool(modifiers & 1 or keyval == 0xfe20)


class FocusKeys:
    def __init__(self, window, bridge):
        gtk = C.CDLL('libgtk-4.so.1')
        obj = C.CDLL('libgobject-2.0.so.0')
        p, u, i = C.c_void_p, C.c_uint, C.c_int
        create = bind(gtk, 'gtk_event_controller_key_new', p)
        add = bind(gtk, 'gtk_widget_add_controller', None, p, p)
        phase = bind(gtk, 'gtk_event_controller_set_propagation_phase', None, p, i)
        ref = bind(obj, 'g_object_ref', p, p)
        self.remove = bind(gtk, 'gtk_widget_remove_controller', None, p, p)
        self.unref = bind(obj, 'g_object_unref', None, p)
        connect = bind(obj, 'g_signal_connect_data', C.c_ulong, p, C.c_char_p, p, p, p, u)
        self.disconnect = bind(obj, 'g_signal_handler_disconnect', None, p, C.c_ulong)
        self.window, self.bridge = window, bridge
        self.last_error = None
        self.requests = []
        self.controller = create()
        ref(self.controller)  # Keep a reference after transfer to the GtkWindow.
        phase(self.controller, 1)
        self.callback = C.CFUNCTYPE(i, p, u, u, u, p)(self.key_pressed)
        self.handler = connect(self.controller, b'key-pressed', C.cast(self.callback, p),
                               None, None, 0)
        add(window, self.controller)

    def key_pressed(self, _controller, keyval, _keycode, modifiers, _data):
        direction = traversal_direction(keyval, modifiers)
        if direction is None:
            return 0
        try:
            self.bridge.traverse(direction)
        except (OSError, ValueError, RuntimeError) as error:
            self.last_error = str(error)
            return 0
        self.requests.append(direction)
        self.requests = self.requests[-32:]
        self.last_error = None
        return 1

    def close(self):
        if self.controller:
            self.disconnect(self.controller, self.handler)
            self.remove(self.window, self.controller)
            self.unref(self.controller)
            self.controller = None
            self.callback = None
