# SPDX-License-Identifier: GPL-3.0-or-later
"""Move the native GTK3 tooltip outside its owner without changing its style."""
import logging
import weakref

from tooltip_position import outside_control

_LOG = logging.getLogger(__name__)


def _mapped(window):
    reference = getattr(window, '_theme_lab_hint_owner', None)
    owner = reference() if reference is not None else None
    if owner is None or not owner.get_realized():
        return

    try:
        from gi.repository import Gdk
        parent = owner.get_parent_window()
        if parent is None:
            raise RuntimeError('GTK3 control has no parent GdkWindow')
        allocation = owner.get_allocation()
        x, y = parent.get_root_coords(allocation.x, allocation.y)
        screen = owner.get_screen()
        monitor_index = screen.get_monitor_at_point(x, y)
        monitor = screen.get_monitor_geometry(monitor_index)
        position = outside_control(
            (x, y, allocation.width, allocation.height), window.get_size(),
            (monitor.x, monitor.y, monitor.width, monitor.height))
        if position is None:
            # Never fall back to a tooltip that covers the control when no
            # external placement fits on this monitor.
            window.hide()
        else:
            window.move(*position)
    except Exception:
        # Do not let a GTK callback error escape or leave a tooltip over the
        # control. Keep the exception in the normal diagnostic stream.
        _LOG.exception('GTK3 tooltip placement failed; suppressing the popup')
        window.hide()


def _unmapped(window):
    window._theme_lab_hint_owner = None


def track_native_tooltip(owner):
    """Associate the current GTK tooltip window with the control being queried."""
    from gi.repository import Gtk, Gdk
    for window in Gtk.Window.list_toplevels():
        if (window.get_type_hint() != Gdk.WindowTypeHint.TOOLTIP
                or window.get_display() != owner.get_display()):
            continue
        if not getattr(window, '_theme_lab_hint_position_bound', False):
            window.connect('map', _mapped)
            window.connect('unmap', _unmapped)
            window._theme_lab_hint_position_bound = True
        window._theme_lab_hint_owner = weakref.ref(owner)
