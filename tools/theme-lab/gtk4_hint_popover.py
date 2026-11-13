# SPDX-License-Identifier: GPL-3.0-or-later
"""Delayed, theme-native GTK4 hints that do not cover vertical scrollbars."""
import ctypes as C
import time


def _bind(library, name, result, *parameters):
    function = getattr(library, name)
    function.restype = result
    function.argtypes = list(parameters)
    return function


class DelayedPopoverHint:
    """Show a non-modal GtkPopover beside a control after a cold-hover delay.

    ``overlay`` is a GtkFixed covering the same coordinates as the owning
    window's content. Its invisible GtkMenuButton is the supported GtkPopover
    parent; the actual control retains its native painting and input handling.
    """

    def __init__(self, owner, overlay, x, y, width, height, text, delay_ms=500):
        self.gtk = C.CDLL('libgtk-4.so.1')
        self.gobject = C.CDLL('libgobject-2.0.so.0')
        self.glib = C.CDLL('libglib-2.0.so.0')
        p, i, u, s, d = C.c_void_p, C.c_int, C.c_uint, C.c_char_p, C.c_double
        self._ref = _bind(self.gobject, 'g_object_ref', p, p)
        self._unref = _bind(self.gobject, 'g_object_unref', None, p)

        self._menu_button_new = _bind(self.gtk, 'gtk_menu_button_new', p)
        self._menu_button_popover = _bind(self.gtk, 'gtk_menu_button_set_popover', None, p, p)
        self._menu_button_frame = _bind(self.gtk, 'gtk_menu_button_set_has_frame', None, p, i)
        self._menu_button_direction = _bind(self.gtk, 'gtk_menu_button_set_direction', None, p, i)
        self._popover_new = _bind(self.gtk, 'gtk_popover_new', p)
        self._widget_css_class = _bind(self.gtk, 'gtk_widget_add_css_class', None, p, s)
        self._popover_child = _bind(self.gtk, 'gtk_popover_set_child', None, p, p)
        self._popover_arrow = _bind(self.gtk, 'gtk_popover_set_has_arrow', None, p, i)
        self._popover_autohide = _bind(self.gtk, 'gtk_popover_set_autohide', None, p, i)
        self._popover_position = _bind(self.gtk, 'gtk_popover_set_position', None, p, i)
        self._popover_offset = _bind(self.gtk, 'gtk_popover_set_offset', None, p, i, i)
        self._popover_popup = _bind(self.gtk, 'gtk_popover_popup', None, p)
        self._popover_popdown = _bind(self.gtk, 'gtk_popover_popdown', None, p)
        self._object_set_data = _bind(self.gobject, 'g_object_set_data', None, p, s, p)
        self._widget_mapped = _bind(self.gtk, 'gtk_widget_get_mapped', i, p)
        self._widget_opacity = _bind(self.gtk, 'gtk_widget_set_opacity', None, p, d)
        self._widget_can_target = _bind(self.gtk, 'gtk_widget_set_can_target', None, p, i)
        self._widget_focusable = _bind(self.gtk, 'gtk_widget_set_focusable', None, p, i)
        self._widget_parent = _bind(self.gtk, 'gtk_widget_get_parent', p, p)
        self._widget_get_has_tooltip = _bind(self.gtk, 'gtk_widget_get_has_tooltip', i, p)
        self._widget_has_tooltip = _bind(self.gtk, 'gtk_widget_set_has_tooltip', None, p, i)
        self._widget_size = _bind(self.gtk, 'gtk_widget_set_size_request', None, p, i, i)
        self._widget_width = _bind(self.gtk, 'gtk_widget_get_width', i, p)
        self._widget_height = _bind(self.gtk, 'gtk_widget_get_height', i, p)
        self._fixed_put = _bind(self.gtk, 'gtk_fixed_put', None, p, p, d, d)
        self._fixed_remove = _bind(self.gtk, 'gtk_fixed_remove', None, p, p)
        self._label_new = _bind(self.gtk, 'gtk_label_new', p, s)
        self._label_wrap = _bind(self.gtk, 'gtk_label_set_wrap', None, p, i)
        self._label_width = _bind(self.gtk, 'gtk_label_set_max_width_chars', None, p, i)
        self._motion_new = _bind(self.gtk, 'gtk_event_controller_motion_new', p)
        self._controller_phase = _bind(self.gtk, 'gtk_event_controller_set_propagation_phase', None, p, i)
        self._add_controller = _bind(self.gtk, 'gtk_widget_add_controller', None, p, p)
        self._remove_controller = _bind(self.gtk, 'gtk_widget_remove_controller', None, p, p)
        self._connect = _bind(self.gobject, 'g_signal_connect_data', C.c_ulong,
                              p, s, p, p, p, u)
        self._disconnect = _bind(self.gobject, 'g_signal_handler_disconnect', None, p, C.c_ulong)
        self._timeout_add = _bind(self.glib, 'g_timeout_add', u, u, p, p)
        self._source_remove = _bind(self.glib, 'g_source_remove', i, u)

        self.owner = owner
        self.overlay = overlay
        self.controller = None
        self.anchor = None
        self.popover = None
        self.timer = 0
        self.visible = False
        self.shown_at = None
        self.closed = False
        self.delay_ms = max(1, int(delay_ms))
        self.position_strategy = None
        self.layout_diagnostics = {'owner_bounds_px': [int(x), int(y), int(width), int(height)]}
        self.handler_ids = []
        self.original_has_tooltip = bool(self._widget_get_has_tooltip(owner))
        self.tooltip_suppressed = False
        self.ancestor_tooltips = []
        self.ancestor_suppressed = False
        self.anchor_added = False
        self.anchor_ref = False
        self.controller_added = False
        self.owner_ref = self.overlay_ref = False
        enter_type = C.CFUNCTYPE(None, p, d, d, p)
        leave_type = C.CFUNCTYPE(None, p, p)
        timeout_type = C.CFUNCTYPE(i, p)
        self._enter_callback = enter_type(self._entered)
        self._leave_callback = leave_type(self._left)
        self._timeout_callback = timeout_type(self._show)

        try:
            self.owner = self._ref(owner)
            self.owner_ref = True
            self.overlay = self._ref(overlay)
            self.overlay_ref = True
            ancestor = self._widget_parent(owner)
            while ancestor:
                if self._widget_get_has_tooltip(ancestor):
                    self.ancestor_tooltips.append((self._ref(ancestor), True))
                ancestor = self._widget_parent(ancestor)
            # Keep the text available to inspection/accessibility clients, but
            # suppress GTK's centered tooltip window for this control.
            if self.original_has_tooltip:
                self._widget_has_tooltip(owner, 0)
                self.tooltip_suppressed = True

            # Place the popup wholly beside a tall scrollbar whenever the
            # current overlay has room. The former fixed left placement let
            # a 420px hint cross the scrollbar itself in the centered gallery.
            overlay_width = max(0, self._widget_width(overlay))
            overlay_height = max(0, self._widget_height(overlay))
            self.layout_diagnostics['overlay_size_px'] = [overlay_width, overlay_height]
            popup_width = 420  # measured GTK4 gallery width for this 48-char hint
            popup_height = 64   # conservative wrapped height for vertical fallback
            gap = 16
            right_space = overlay_width - (x + width + gap)
            left_space = x - gap
            if right_space >= popup_width:
                position, direction = 1, 3  # GTK_POS_RIGHT, GTK_ARROW_RIGHT
                anchor_x, anchor_y, offset_x, offset_y = x + width, y + height / 2, gap, 0
                label_chars = 48
                self.position_strategy = 'right'
            elif left_space >= popup_width:
                position, direction = 0, 2  # GTK_POS_LEFT, GTK_ARROW_LEFT
                anchor_x, anchor_y, offset_x, offset_y = x, y + height / 2, -gap, 0
                label_chars = 48
                self.position_strategy = 'left'
            elif overlay_height and y >= popup_height + gap:
                position, direction = 2, 0  # GTK_POS_TOP, GTK_ARROW_UP
                anchor_x, anchor_y, offset_x, offset_y = x + width / 2, y, 0, -gap
                # Keep enough horizontal slack for GTK's minimum popover
                # padding when a wide owner nearly fills the viewport.
                label_chars = 44
                self.position_strategy = 'top'
            elif overlay_height and overlay_height - (y + height) >= popup_height + gap:
                position, direction = 3, 1  # GTK_POS_BOTTOM, GTK_ARROW_DOWN
                anchor_x, anchor_y, offset_x, offset_y = x + width / 2, y + height, 0, gap
                label_chars = 44
                self.position_strategy = 'bottom'
            elif right_space >= left_space:
                position, direction = 1, 3
                anchor_x, anchor_y, offset_x, offset_y = x + width, y + height / 2, gap, 0
                label_chars = max(12, min(48, int(max(96, right_space - gap) / 8)))
                self.position_strategy = 'right-wrapped'
            else:
                position, direction = 0, 2
                anchor_x, anchor_y, offset_x, offset_y = x, y + height / 2, -gap, 0
                label_chars = max(12, min(48, int(max(96, left_space - gap) / 8)))
                self.position_strategy = 'left-wrapped'
            self.layout_diagnostics['anchor_request_px'] = [int(anchor_x), int(anchor_y)]
            self.layout_diagnostics['placement_strategy'] = self.position_strategy

            self.anchor = self._menu_button_new()
            self._menu_button_frame(self.anchor, 0)
            self._menu_button_direction(self.anchor, direction)
            self._widget_size(self.anchor, 1, 1)
            self._widget_opacity(self.anchor, 0.0)
            self._widget_can_target(self.anchor, 0)
            self._widget_focusable(self.anchor, 0)

            self.popover = self._popover_new()
            self._object_set_data(self.popover, b'theme-lab-delayed-hint', C.c_void_p(1))
            # Although GTK4 uses a GtkPopover for placement, this surface is a
            # tooltip semantically. The class lets the theme keep its own
            # tooltip palette instead of inheriting the generic popover face.
            self._widget_css_class(self.popover, b'theme-lab-hint')
            self._popover_arrow(self.popover, 0)
            self._popover_autohide(self.popover, 0)  # non-modal; preserve control input
            self._popover_position(self.popover, position)
            self._popover_offset(self.popover, offset_x, offset_y)
            label = self._label_new(text.encode('utf-8'))
            self._label_wrap(label, 1)
            self._label_width(label, label_chars)
            self._popover_child(self.popover, label)
            self._menu_button_popover(self.anchor, self.popover)
            self._fixed_put(overlay, self.anchor, float(anchor_x), float(anchor_y))
            self.anchor_added = True
            self._ref(self.anchor)
            self.anchor_ref = True

            self.controller = self._motion_new()
            # Capture motion over internal children (for example, the label
            # inside GtkCheckButton) while allowing normal widget input.
            self._controller_phase(self.controller, 1)  # GTK_PHASE_CAPTURE
            self._handler(self.controller, b'enter', self._enter_callback)
            self._handler(self.controller, b'leave', self._leave_callback)
            self._add_controller(owner, self.controller)
            self.controller_added = True
        except BaseException:
            self.close()
            raise

    def _handler(self, instance, signal, callback):
        handler = self._connect(instance, signal, C.cast(callback, C.c_void_p), None, None, 0)
        if not handler:
            raise RuntimeError('GTK4 could not connect hint ' + signal.decode('ascii'))
        self.handler_ids.append((instance, handler))

    def _entered(self, _controller, _x, _y, _data):
        if self.closed or self.visible or self.timer:
            return
        # A native tooltip on an ancestor (for example GtkScrolledWindow)
        # would otherwise appear alongside this scrollbar-specific hint.
        for ancestor, _original in self.ancestor_tooltips:
            self._widget_has_tooltip(ancestor, 0)
        self.ancestor_suppressed = bool(self.ancestor_tooltips)
        self.timer = self._timeout_add(self.delay_ms, C.cast(self._timeout_callback, C.c_void_p), None)

    def _left(self, _controller, _data):
        if self.closed:
            return
        if self.timer:
            self._source_remove(self.timer)
            self.timer = 0
        if self.visible and self.popover:
            self._popover_popdown(self.popover)
            self.visible = False
        self._restore_ancestor_tooltips()

    def _restore_ancestor_tooltips(self):
        if not self.ancestor_suppressed:
            return
        for ancestor, original in self.ancestor_tooltips:
            self._widget_has_tooltip(ancestor, int(original))
        self.ancestor_suppressed = False

    def _show(self, _data):
        self.timer = 0
        if not self.closed and self.popover and self.owner:
            self._popover_popup(self.popover)
            self.shown_at = time.monotonic()
            self.visible = True
        return 0

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.timer:
            self._source_remove(self.timer)
            self.timer = 0
        if self.visible and self.popover:
            self._popover_popdown(self.popover)
        self.visible = False
        if self.controller_added and self.controller and self.owner:
            for instance, handler in self.handler_ids:
                try:
                    self._disconnect(instance, handler)
                except Exception:
                    pass
            self.handler_ids.clear()
            self._remove_controller(self.owner, self.controller)
            self.controller_added = False
        if self.tooltip_suppressed and self.owner:
            self._widget_has_tooltip(self.owner, int(self.original_has_tooltip))
            self.tooltip_suppressed = False
        self._restore_ancestor_tooltips()
        for ancestor, _original in self.ancestor_tooltips:
            self._unref(ancestor)
        self.ancestor_tooltips.clear()
        if (self.anchor_added and self.overlay and self.anchor
                and self._widget_parent(self.anchor) == self.overlay):
            self._fixed_remove(self.overlay, self.anchor)
            self.anchor_added = False
        if self.anchor_ref and self.anchor:
            self._unref(self.anchor)
            self.anchor_ref = False
        elif self.anchor and not self.anchor_added:
            # gtk_menu_button_new() returns a floating reference if insertion
            # into the GtkFixed never succeeded.
            self._unref(self.anchor)
        if self.overlay_ref and self.overlay:
            self._unref(self.overlay)
            self.overlay_ref = False
        if self.owner_ref and self.owner:
            self._unref(self.owner)
            self.owner_ref = False
        self.owner = self.overlay = self.controller = self.anchor = self.popover = None
