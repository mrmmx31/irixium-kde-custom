#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK3 ScrolledWindow regression for the SR10.4 table corner.

Invoked by test_domainos_native_steppers.py --corner with snapshots of real KDE
color roles: raw exports or documented normalized palette-bridge snapshots.
This fixture uses native table scrollbars, not a replacement widget;
XTest hover/press events are sent only to its own disposable Xvfb display.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def worker(output: Path, theme: str, *, boundary_only=False) -> int:
    import cairo
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkX11', '3.0')
    from gi.repository import Gtk, Gdk, GdkX11
    from PIL import Image
    sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'gtk/tools')]
    from gtk2_palette import exported_palette
    import domainos_motif_art as art
    import build_kde_domainos as builder

    palette = exported_palette((Path(os.environ['XDG_CONFIG_HOME'])/'gtk-3.0/colors.css').read_bytes())
    assert Gtk.init_check(None)[0]
    settings = Gtk.Settings.get_default()
    settings.set_property('gtk-theme-name', theme)
    settings.set_property('gtk-enable-animations', False)
    window = Gtk.Window()
    window.set_default_size(440, 280)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
    scroll.set_overlay_scrolling(False)
    store = Gtk.ListStore(str, str, str)
    for index in range(65):
        store.append([str(index), 'Artificial native scrollbar row', 'Long column forces horizontal scrolling. '*15])
    tree = Gtk.TreeView(model=store)
    for index, label in enumerate(('ID', 'Name', 'Long column')):
        tree.append_column(Gtk.TreeViewColumn(label, Gtk.CellRendererText(), text=index))
    scroll.add(tree)
    window.add(scroll)
    window.show_all()
    bars = {'vertical': scroll.get_vscrollbar(), 'horizontal': scroll.get_hscrollbar()}
    adjustments = [scroll.get_vadjustment(), scroll.get_hadjustment()]
    checks, records = {}, []

    def settle(iterations=12):
        for _ in range(iterations):
            while Gtk.events_pending(): Gtk.main_iteration_do(False)
            time.sleep(.005)

    xlib = ctypes.CDLL('libX11.so.6')
    xtst = ctypes.CDLL('libXtst.so.6')
    xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    xlib.XOpenDisplay.restype = ctypes.c_void_p
    xlib.XFlush.argtypes = [ctypes.c_void_p]
    xlib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    connection = xlib.XOpenDisplay(os.environ['DISPLAY'].encode())
    assert connection

    def midrange():
        scroll.set_sensitive(True)
        for bar in bars.values():
            bar.unset_state_flags(Gtk.StateFlags.BACKDROP)
        for adjustment in adjustments:
            adjustment.set_value((adjustment.get_upper()-adjustment.get_page_size())/2)
        xtst.XTestFakeMotionEvent(connection, -1, 600, 350, 0)
        xlib.XFlush(connection)
        settle()

    def point(direction):
        orientation = 'vertical' if direction in ('up', 'down') else 'horizontal'
        bar = bars[orientation]
        allocation = bar.get_allocation()
        center = ((7, 7 if direction == 'up' else allocation.height-7)
                  if orientation == 'vertical' else (7 if direction == 'left' else allocation.width-7, 7))
        x, y = bar.translate_coordinates(window, *center)
        origin = window.get_window().get_origin()[1:]
        xtst.XTestFakeMotionEvent(connection, -1, origin[0]+x, origin[1]+y, 0)
        xlib.XFlush(connection)
        settle()

    def capture(phase, *, disabled=False, backdrop=False, lower=False, upper=False, hover=None, pressed=None):
        allocation = scroll.get_allocation()
        full = Gdk.pixbuf_get_from_window(window.get_window(), 0, 0,
                                         window.get_allocated_width(), window.get_allocated_height())
        full.savev(str(output/(phase+'-table.png')), 'png', [], [])
        screenshot = Image.open(output/(phase+'-table.png')).convert('RGBA')
        vertical, horizontal = (bars[name].get_allocation() for name in ('vertical', 'horizontal'))
        checks[phase+':native-corner-allocation'] = (
            vertical.width == horizontal.height == 15 and vertical.height > 30 and horizontal.width > 30
            and horizontal.y-(vertical.y+vertical.height) == 4
            and vertical.x-(horizontal.x+horizontal.width) == 4
            and vertical.x+vertical.width == allocation.width
            and horizontal.y+horizontal.height == allocation.height)
        for orientation, bar in bars.items():
            alloc = bar.get_allocation()
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, alloc.width, alloc.height)
            bar.draw(cairo.Context(surface))
            path = output/(phase+'-'+orientation+'.png')
            surface.write_to_png(str(path))
            pixels = Image.open(path).convert('RGBA')
            nodes = bar.get_style_context().to_string(Gtk.StyleContextPrintFlags.RECURSE)
            # The measured native trough is one continuous inset frame.
            # Compare its integer corner joins as well as the free-standing
            # arrow; a CSS border can keep the allocation while blurring
            # these two-pixel diagonal joins.
            frame = art.bevel(art.blank(alloc.width, alloc.height), down=True)
            frame_differences = []
            for yy, row in enumerate(frame):
                for xx, token in enumerate(row):
                    if token is None: continue
                    value = art.evaluate(art.pixel_plan('button', token, inactive=backdrop, disabled=disabled), palette)
                    expected_frame = tuple(int(value[n:n+2], 16) for n in (1, 3, 5))+(255,)
                    frame_differences.append(max(abs(a-b) for a, b in zip(pixels.getpixel((xx, yy)), expected_frame)))
            checks[phase+':'+orientation+':continuous-integer-trough-frame'] = max(frame_differences) <= 1
            bx, by = bar.translate_coordinates(window, 0, 0)
            for direction in (('up', 'down') if orientation == 'vertical' else ('left', 'right')):
                insensitive = disabled or (lower and direction in ('up', 'left')) or (upper and direction in ('down', 'right'))
                mode = 'disabled' if insensitive else 'pressed' if direction == pressed else 'normal'
                box = ((2, 2, 13, 13) if direction == 'up' else (2, alloc.height-13, 13, alloc.height-2)
                       if direction == 'down' else (2, 2, 13, 13) if direction == 'left'
                       else (alloc.width-13, 2, alloc.width-2, 13))
                actual = pixels.crop(box)
                # Range-end sensitivity belongs to the child; its paint
                # remains tied to the sensitive scrollbar's current palette.
                background = art.evaluate(art.pixel_plan('button', 'trough', inactive=backdrop, disabled=disabled), palette)
                expected = Image.new('RGBA', (11, 11), tuple(int(background[n:n+2], 16) for n in (1, 3, 5))+(255,))
                for y, row in enumerate(builder.gtk3_arrow(mode, direction)):
                    for x, token in enumerate(row):
                        if token is None: continue
                        color = art.evaluate(art.pixel_plan('button', token, inactive=backdrop, disabled=disabled), palette)
                        expected.putpixel((x, y), tuple(int(color[n:n+2], 16) for n in (1, 3, 5))+(255,))
                difference = [max(abs(a-b) for a, b in zip(old, new)) for old, new in zip(actual.getdata(), expected.getdata())]
                screen = screenshot.crop((bx+box[0], by+box[1], bx+box[2], by+box[3]))
                screen_difference = [max(abs(a-b) for a, b in zip(old, new)) for old, new in zip(actual.getdata(), screen.getdata())]
                node = 'button.'+('up' if direction in ('up', 'left') else 'down')
                lines = [line.strip() for line in nodes.splitlines() if line.strip().startswith(node+':')]
                checks[phase+':'+direction+':complete-artwork'] = max(difference) <= 1 and actual.size == (11, 11)
                checks[phase+':'+direction+':real-screen-unclipped'] = max(screen_difference) <= 1
                checks[phase+':'+direction+':native-state'] = (len(lines) == 1 and ((':disabled' in lines[0]) == insensitive)
                    and ((':backdrop' in lines[0]) == backdrop)
                    and (pressed != direction or ':active' in lines[0]) and (hover != direction or ':hover' in lines[0]))
                actual.save(output/(phase+'-'+direction+'.png'))
                records.append({'phase': phase, 'direction': direction, 'mode': mode,
                                'logical_disabled': insensitive, 'parent_disabled': disabled,
                                'paint_face_role': art.role('button', inactive=backdrop, disabled=disabled),
                                'allocation': [alloc.x, alloc.y, alloc.width, alloc.height],
                                'max_channel_difference': max(difference), 'screen_difference': max(screen_difference),
                                'native_node': lines[0] if lines else None})
        screenshot.crop((allocation.width-32, allocation.height-48, allocation.width, allocation.height)).save(output/(phase+'-corner.png'))

    def blocked_click(phase, direction):
        before = tuple(adjustment.get_value() for adjustment in adjustments)
        point(direction)
        xtst.XTestFakeButtonEvent(connection, 1, 1, 0)
        xlib.XFlush(connection)
        settle(4)
        xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
        xlib.XFlush(connection)
        settle(4)
        checks[phase+':'+direction+':blocked-click-no-adjustment'] = (
            tuple(adjustment.get_value() for adjustment in adjustments) == before)

    def boundary_case(phase, *, upper=False, disabled=False, backdrop=False):
        midrange()
        for adjustment in adjustments:
            adjustment.set_value(adjustment.get_upper()-adjustment.get_page_size() if upper else adjustment.get_lower())
        scroll.set_sensitive(not disabled)
        if backdrop:
            for bar in bars.values():
                bar.set_state_flags(Gtk.StateFlags.BACKDROP, False)
        settle()
        capture(phase, disabled=disabled, backdrop=backdrop, lower=not upper, upper=upper)
        checks[phase+':parent-sensitive'] = all(bar.is_sensitive() == (not disabled) for bar in bars.values())
        blocked = ('up', 'down', 'left', 'right') if disabled else ('down', 'right') if upper else ('up', 'left')
        for direction in blocked:
            blocked_click(phase, direction)

    try:
        settle()
        midrange()
        if not boundary_only:
            capture('normal')
        for direction in (() if boundary_only else ('down', 'right')):
            midrange()
            point(direction)
            capture('hover-'+direction, hover=direction)
            xtst.XTestFakeButtonEvent(connection, 1, 1, 0)
            xlib.XFlush(connection)
            settle(4)
            capture('pressed-'+direction, pressed=direction)
            xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
            xlib.XFlush(connection)
            settle()
            capture('released-'+direction, hover=direction)
        boundary_case('lower-bound')
        boundary_case('upper-bound', upper=True)
        boundary_case('lower-bound-backdrop', backdrop=True)
        boundary_case('upper-bound-backdrop', upper=True, backdrop=True)
        boundary_case('disabled-lower-bound', disabled=True)
        boundary_case('disabled-upper-bound-backdrop', upper=True, disabled=True, backdrop=True)
        if not boundary_only:
            midrange()
            scroll.set_sensitive(False)
            settle()
            capture('disabled', disabled=True)
        result = {'GTK': [Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()],
                  'theme': settings.get_property('gtk-theme-name'), 'worker_pid': os.getpid(),
                  'window_id': GdkX11.X11Window.get_xid(window.get_window()), 'checks': checks, 'records': records,
                  'boundary_only': boundary_only,
                  'palette_policy': 'Range-end arrows retain sensitive-parent colors while remaining logically disabled; a wholly insensitive parent retains insensitive colors. Adaptation, not historical Motif disabled-state proof.',
                  'scope': 'Real GTK3 TreeView/ScrolledWindow and screen pixels at its lower-right corner; XTest hover/press/release on own Xvfb; native lower/upper adjustment disabled states. Current generated full steppers compared at every pixel with <=1 color-rounding tolerance. Inputs are KDE-derived role snapshots: raw exports or documented normalized bridge snapshots. No personal session input, exporter/live-transport validation or GTK2/GTK4 claims.'}
        (output/'NATIVE.json').write_text(json.dumps(result, indent=2)+'\n')
        return int(not all(checks.values()))
    finally:
        xtst.XTestFakeButtonEvent(connection, 1, 0, 0)
        xlib.XFlush(connection)
        xlib.XCloseDisplay(connection)
        window.destroy()
