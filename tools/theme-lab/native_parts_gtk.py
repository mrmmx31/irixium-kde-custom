# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only diagnostics for one verified GTK3 binary, not a portable GTK ABI.

Layouts follow GTK 3.24.49 gtkrange.c and gtkcssgadget.c (LGPL-2.0-or-later).
No raw pointer dereference: bounded reads through /proc/self/mem fail as OSError.
Only registered gadget classes and the current widget owner are accepted.
These are allocation margin boxes, not painted glyphs/borders or Motif defaults.
"""
import ctypes as C
import hashlib
import os
from pathlib import Path
import platform
import threading

VERIFIED_SHA256 = 'a56aed9f46dc47d054555880c6dc543f41846b0732520c7d2e5ef45c5c7f2ddf'
SOURCE = 'gtk3-3.24.49-verified-margin-boxes'

class Rect(C.Structure):
    _fields_ = [(key, C.c_int) for key in ('x', 'y', 'width', 'height')]

class RangePrefix(C.Structure):
    _fields_ = [('mouse_location', C.c_void_p), ('mouse_x', C.c_int),
                ('mouse_y', C.c_int), ('grab_location', C.c_void_p),
                ('timer', C.c_void_p), ('adjustment', C.c_void_p),
                ('lower_sensitivity', C.c_int), ('upper_sensitivity', C.c_int),
                ('event_window', C.c_void_p)] + [(key, C.c_void_p) for key in (
                    'gadget', 'contents_gadget', 'stepper_a_gadget', 'stepper_b_gadget',
                    'stepper_c_gadget', 'stepper_d_gadget', 'trough_gadget',
                    'fill_gadget', 'highlight_gadget', 'slider_gadget')]

class GadgetPrefix(C.Structure):
    _fields_ = [('node', C.c_void_p), ('owner', C.c_void_p),
                ('allocation', Rect), ('baseline', C.c_int)]

def verified_runtime(Gtk):
    if platform.machine() != 'x86_64' or C.sizeof(C.c_void_p) != 8:
        return False
    if (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()) != (3, 24, 49):
        return False
    paths = set()
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and Path(fields[5]).name.startswith('libgtk-3.so.'):
            paths.add(fields[5])
    return len(paths) == 1 and hashlib.sha256(Path(paths.pop()).read_bytes()).hexdigest() == VERIFIED_SHA256

class Reader:
    def __init__(self, Gtk):
        self.Gtk = Gtk
        self.available = False
        try:
            if not verified_runtime(Gtk):
                return
            self.lib = C.CDLL('libgobject-2.0.so.0')
            for name, args, result in (
                ('g_type_from_name', [C.c_char_p], C.c_size_t),
                ('g_type_class_peek', [C.c_size_t], C.c_void_p),
                ('g_type_class_get_instance_private_offset', [C.c_void_p], C.c_int),
            ):
                function = getattr(self.lib, name)
                function.argtypes, function.restype = args, result
            self.capsule = C.pythonapi.PyCapsule_GetPointer
            self.capsule.argtypes, self.capsule.restype = [C.py_object, C.c_char_p], C.c_void_p
            self.available = True
        except (OSError, ValueError, AttributeError):
            pass

    def private_offset(self, name):
        klass = self.lib.g_type_class_peek(self.lib.g_type_from_name(name))
        if not klass:
            return None
        offset = self.lib.g_type_class_get_instance_private_offset(klass)
        return offset if -4096 <= offset < 0 else None

    @staticmethod
    def read(fd, address, kind):
        if address is None or address < 4096:
            raise ValueError('Endereço indisponível')
        data = os.pread(fd, C.sizeof(kind), address)
        if len(data) != C.sizeof(kind):
            raise ValueError('Leitura incompleta')
        return kind.from_buffer_copy(data)

    def measure(self, widget):
        if (not self.available or threading.current_thread() is not threading.main_thread()
                or type(widget) is not self.Gtk.Scrollbar or not widget.get_realized()
                or not widget.get_mapped()):
            return None
        try:
            address = self.capsule(widget.__gpointer__, None)
            range_offset = self.private_offset(b'GtkRange')
            gadget_offset = self.private_offset(b'GtkCssGadget')
            if range_offset is None or gadget_offset is None:
                return None
            classes = {self.lib.g_type_class_peek(self.lib.g_type_from_name(name))
                       for name in (b'GtkCssCustomGadget', b'GtkBuiltinIcon', b'GtkBoxGadget')}
            classes.discard(None)
            allocation = widget.get_allocation()
            # Source shift_allocation subtracts widget allocation for windowless widgets.
            dx, dy = (allocation.x, allocation.y) if not widget.get_has_window() else (0, 0)
            with open('/proc/self/mem', 'rb', buffering=0) as memory:
                prefix = self.read(memory.fileno(), address + range_offset, RangePrefix)
                def box(pointer):
                    if not pointer:
                        return None
                    klass = self.read(memory.fileno(), pointer, C.c_void_p).value
                    if klass not in classes:
                        raise ValueError('Classe interna não validada')
                    part = self.read(memory.fileno(), pointer + gadget_offset, GadgetPrefix)
                    if part.owner != address:
                        raise ValueError('Peça pertence a outro controle')
                    r = part.allocation
                    return {'x': r.x - dx, 'y': r.y - dy, 'width': r.width, 'height': r.height}
                contents = box(prefix.contents_gadget)
                slider = box(prefix.slider_gadget)
                track = box(prefix.trough_gadget)
                arrows = [box(prefix.stepper_a_gadget), box(prefix.stepper_d_gadget)]
                # Additional steppers have no one-to-one Motif counterpart here.
                if prefix.stepper_b_gadget or prefix.stepper_c_gadget:
                    return None
            public = widget.get_range_rect()
            if contents != {key: getattr(public, key) for key in ('x','y','width','height')}:
                return None
            axis = 'y' if widget.get_orientation() else 'x'
            extent = 'height' if axis == 'y' else 'width'
            start, end = widget.get_slider_range()
            if not slider or (slider[axis], slider[axis] + slider[extent]) != (start, end):
                return None
            result = {'source': SOURCE, 'coordinate_space': 'gtk_widget_local_px'}
            # Convert from the GTK window coordinates to widget-local allocations.
            for name, r in zip(('slider','track','arrow_first','arrow_last'), (slider,track,*arrows)):
                if r is None:
                    continue
                local = dict(r, x=r['x'] - allocation.x + dx, y=r['y'] - allocation.y + dy)
                if (local['x'] < 0 or local['y'] < 0 or local['width'] < 1 or local['height'] < 1
                        or local['x'] + local['width'] > allocation.width
                        or local['y'] + local['height'] > allocation.height):
                    return None
                result[name] = local
            return result
        except (OSError, ValueError, TypeError, AttributeError, OverflowError):
            return None
