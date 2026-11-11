# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture rendered pixels of one live GTK4 widget from its X11 surface."""
import ctypes as C
from pathlib import Path
import re
import subprocess
import uuid
from io import BytesIO
from gtk4_push_api import bind


class Rect(C.Structure):
    _fields_ = [('x', C.c_float), ('y', C.c_float),
                ('width', C.c_float), ('height', C.c_float)]


def prepare(gtk, widget, state):
    """Apply a visual state; the worker captures on a later main-loop turn."""
    if state not in range(5):
        raise ValueError('GTK4 sample state is unsupported')
    flags = (0, 2, 1, 8, 64)[state]  # PRELIGHT, ACTIVE, INSENSITIVE, BACKDROP
    p, i = C.c_void_p, C.c_int
    bind(gtk, 'gtk_widget_set_sensitive', None, p, i)(widget, state != 3)
    bind(gtk, 'gtk_widget_set_state_flags', None, p, C.c_uint, i)(widget, flags, 1)
    bind(gtk, 'gtk_widget_queue_draw', None, p)(widget)


def capture(gtk, widget, window, window_id, output, events, control, state):
    """Save the widget's actual GTK4-rendered X11 pixels, cropped at 1:1."""
    output, events = Path(output).absolute(), Path(events).absolute()
    if (output.parent != events or output.exists() or
            not re.fullmatch(r'paint-sample-[0-9a-f]{32}\.png', output.name)):
        raise ValueError('GTK4 sample destination must be unique in its private event directory')
    if control not in (0, 1, 2, 10, 11) or state not in range(5):
        raise ValueError('GTK4 sample control or state is unsupported')

    p, i = C.c_void_p, C.c_int
    width = int(bind(gtk, 'gtk_widget_get_allocated_width', i, p)(widget))
    height = int(bind(gtk, 'gtk_widget_get_allocated_height', i, p)(widget))
    scale = int(bind(gtk, 'gtk_widget_get_scale_factor', i, p)(widget))
    box = Rect()
    if (width < 1 or height < 1 or scale < 1 or width * height * scale * scale > 16000000 or
            not bind(gtk, 'gtk_widget_compute_bounds', i, p, p, C.POINTER(Rect))(
                widget, window, C.byref(box))):
        raise ValueError('GTK4 sample allocation is outside the capture limits')

    from PIL import Image
    raw = events / ('paint-capture-' + uuid.uuid4().hex + '.xwd')
    try:
        raw.touch(mode=0o600, exist_ok=False)
        result = subprocess.run(['xwd', '-silent', '-id', str(window_id), '-out', str(raw)],
                                capture_output=True, text=True, timeout=8, check=False)
        if result.returncode:
            raise RuntimeError('GTK4 X11 surface capture failed: ' + result.stderr[-500:])
        raw.chmod(0o600)
        decoded = subprocess.run(['xwdtopnm', str(raw)], capture_output=True, timeout=8,
                                 check=False)
        if decoded.returncode:
            raise RuntimeError('GTK4 X11 image decode failed: ' +
                               decoded.stderr.decode(errors='replace')[-500:])
        with Image.open(BytesIO(decoded.stdout)) as surface:
            left, top = round(box.x * scale), round(box.y * scale)
            right, bottom = left + width * scale, top + height * scale
            if left < 0 or top < 0 or right > surface.width or bottom > surface.height:
                raise ValueError('GTK4 widget bounds fall outside the native X11 surface')
            surface.crop((left, top, right, bottom)).save(output, format='PNG')
    finally:
        raw.unlink(missing_ok=True)
    output.chmod(0o600)
    return {'status': 'captured', 'widget_source': 'native_gtk4_x11_surface',
            'control': control, 'state': state, 'width': width * scale,
            'height': height * scale, 'scale_factor': scale,
            'historical_fidelity_claimed': False}
