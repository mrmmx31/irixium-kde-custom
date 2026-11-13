# SPDX-License-Identifier: GPL-3.0-or-later
"""Position the existing GTK2 tooltip without changing its paint or timers.

GTK2 gtktooltip.c positions mouse hints at the pointer plus half cursor size;
tip_area only controls validity. Public map/unmap signals and GDK coordinates
let the laboratory keep that native window outside its described control.
"""
import weakref
from tooltip_position import outside_control


def _mapped(window):
    ref = getattr(window, '_theme_lab_hint_owner', None)
    owner = ref() if ref is not None else None
    if owner is None or not owner.get_realized():
        return
    from gi.repository import Gdk
    parent = owner.get_parent_window()
    allocation = owner.get_allocation()
    if parent is None:
        return
    x, y = parent.get_root_coords(allocation.x, allocation.y)
    screen = owner.get_screen()
    monitor = Gdk.Rectangle()
    screen.get_monitor_geometry(screen.get_monitor_at_point(x, y), monitor)
    position = outside_control((x, y, allocation.width, allocation.height),
                               window.get_size(),
                               (monitor.x, monitor.y, monitor.width, monitor.height))
    if position is None:
        # No space exists outside this control. Do not cover its input area.
        window.hide()
    else:
        window.move(*position)


def _unmapped(window):
    window._theme_lab_hint_owner = None


def track_native_tooltip(owner):
    from gi.repository import Gtk, Gdk
    for window in Gtk.Window.list_toplevels():
        if (window.get_type_hint() != Gdk.WindowTypeHint.TOOLTIP
                or window.get_name() != 'gtk-tooltip'
                or window.get_display() != owner.get_display()):
            continue
        if not getattr(window, '_theme_lab_hint_position_bound', False):
            window.connect('map', _mapped)
            window.connect('unmap', _unmapped)
            window._theme_lab_hint_position_bound = True
        window._theme_lab_hint_owner = weakref.ref(owner)
