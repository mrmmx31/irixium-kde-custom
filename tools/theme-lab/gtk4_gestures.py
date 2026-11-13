# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture-phase layout gestures; unmodified sequences stay native."""
import ctypes as C
from gtk4_push_api import bind
from gtk4_layout_transaction import LayoutTransaction, layout_modifier


class LayoutGestures:
    def __init__(self, scene, emit):
        self.scene, self.last_error = scene, None
        self.controllers, self.handlers = [], []
        gtk = C.CDLL('libgtk-4.so.1')
        p, i, u, d = C.c_void_p, C.c_int, C.c_uint, C.c_double
        self.move = bind(gtk, 'gtk_fixed_move', None, p, p, d, d)
        self.pick = bind(gtk, 'gtk_widget_pick', p, p, d, d, u)
        self.parent = bind(gtk, 'gtk_widget_get_parent', p, p)
        self.scale = bind(gtk, 'gtk_widget_get_scale_factor', i, p)
        self.modifiers = bind(gtk, 'gtk_event_controller_get_current_event_state', u, p)
        self.event = bind(gtk, 'gtk_event_controller_get_current_event', p, p)
        self.position = bind(gtk, 'gdk_event_get_position', i, p, C.POINTER(d), C.POINTER(d))
        self.surface = bind(gtk, 'gdk_event_get_surface', p, p)
        self.set_state = bind(gtk, 'gtk_gesture_set_state', i, p, i)
        self.remove = bind(gtk, 'gtk_widget_remove_controller', None, p, p)
        ref = bind(scene.api.gobject, 'g_object_ref', p, p)
        add = bind(gtk, 'gtk_widget_add_controller', None, p, p)
        phase = bind(gtk, 'gtk_event_controller_set_propagation_phase', None, p, i)
        button = bind(gtk, 'gtk_gesture_single_set_button', None, p, u)
        self.transaction = LayoutTransaction(scene.records,
            lambda index, x, y: self.move(scene.fixed, scene.widgets[index], x, y), emit)
        try:
            click = bind(gtk, 'gtk_gesture_click_new', p)()
            drag = bind(gtk, 'gtk_gesture_drag_new', p)()
            for controller in (click, drag):
                ref(controller)
                phase(controller, 1); button(controller, 1)
                add(scene.fixed, controller)
                self.controllers.append(controller)
            bind(gtk, 'gtk_gesture_group', None, p, p)(click, drag)
            self.connect(click, b'pressed', C.CFUNCTYPE(None, p, i, d, d, p),
                         lambda controller, _count, x, y, _data: self.begin(controller, x, y))
            self.connect(click, b'released', C.CFUNCTYPE(None, p, i, d, d, p),
                         lambda *_args: self.finish())
            self.connect(drag, b'drag-begin', C.CFUNCTYPE(None, p, d, d, p),
                         lambda controller, x, y, _data: self.begin(controller, x, y))
            self.connect(drag, b'drag-update', C.CFUNCTYPE(None, p, d, d, p),
                         lambda controller, *_args: self.update(controller))
            self.connect(drag, b'drag-end', C.CFUNCTYPE(None, p, d, d, p),
                         lambda controller, *_args: self.finish(controller))
            for controller in self.controllers:
                self.connect(controller, b'cancel', C.CFUNCTYPE(None, p, p, p),
                             lambda *_args: self.transaction.cancel())
        except BaseException:
            self.close()
            raise

    def connect(self, controller, signal, signature, operation):
        def guarded(*args):
            try:
                operation(*args)
                self.last_error = None
            except Exception as error:
                self.last_error = str(error)
                self.transaction.cancel()
        callback = signature(guarded)
        handler = self.scene.api.connect(controller, signal, C.cast(callback, C.c_void_p), None, None, 0)
        self.handlers.append((controller, handler, callback))

    def pointer(self, controller):
        event = self.event(controller)
        x, y = C.c_double(), C.c_double()
        if not event or not self.position(event, C.byref(x), C.byref(y)):
            raise ValueError('GTK4 gesture has no surface position')
        return x.value, y.value, self.surface(event), self.scale(self.scene.fixed)

    def begin(self, controller, x, y):
        if self.transaction.active is not None:
            return
        if not layout_modifier(self.modifiers(controller)):
            self.set_state(controller, 2)
            return
        widget = self.pick(self.scene.fixed, x, y, 1)
        reverse = {widget: index for index, widget in self.scene.widgets.items()}
        while widget and widget not in reverse:
            widget = self.parent(widget)
        if not widget:
            self.set_state(controller, 2)
            return
        self.set_state(controller, 1)
        self.transaction.begin(reverse[widget], *self.pointer(controller))

    def update(self, controller):
        if self.transaction.active is not None:
            self.transaction.update(*self.pointer(controller))

    def finish(self, controller=None):
        if controller is not None:
            self.update(controller)
        self.transaction.finish()

    def close(self):
        self.transaction.cancel()
        for controller, handler, _callback in self.handlers:
            self.scene.api.disconnect(controller, handler)
        self.handlers.clear()
        for controller in self.controllers:
            self.remove(self.scene.fixed, controller)
            self.scene.api.unref(controller)
        self.controllers.clear()
