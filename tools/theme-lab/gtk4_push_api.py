# SPDX-License-Identifier: GPL-3.0-or-later
"""Small GTK4 C ABI boundary. Importing this module never initializes GTK."""
import ctypes as C


def bind(library, name, result, *parameters):
    function = getattr(library, name)
    function.restype = result
    function.argtypes = list(parameters)
    return function


class PushAPI:
    def __init__(self):
        gtk = C.CDLL('libgtk-4.so.1')
        self.gobject = C.CDLL('libgobject-2.0.so.0')
        p, i, u, s = C.c_void_p, C.c_int, C.c_uint, C.c_char_p
        signatures = {
            'fixed_new': ('gtk_fixed_new', p, ()),
            'put': ('gtk_fixed_put', None, (p, p, C.c_double, C.c_double)),
            'button_new': ('gtk_button_new_with_label', p, (s,)),
            'toggle_new': ('gtk_toggle_button_new_with_label', p, (s,)),
            'check_new': ('gtk_check_button_new_with_label', p, (s,)),
            'scrollbar_new': ('gtk_scrollbar_new', p, (i, p)),
            'adjustment_new': ('gtk_adjustment_new', p, (C.c_double, C.c_double,
                            C.c_double, C.c_double, C.c_double, C.c_double)),
            'adjustment_value': ('gtk_adjustment_get_value', C.c_double, (p,)),
            'toggle_active': ('gtk_toggle_button_get_active', i, (p,)),
            'toggle_set_active': ('gtk_toggle_button_set_active', None, (p, i)),
            'check_active': ('gtk_check_button_get_active', i, (p,)),
            'check_set_active': ('gtk_check_button_set_active', None, (p, i)),
            'add_class': ('gtk_widget_add_css_class', None, (p, s)),
            'has_class': ('gtk_widget_has_css_class', i, (p, s)),
            'request': ('gtk_widget_set_size_request', None, (p, i, i)),
            'tooltip': ('gtk_widget_set_tooltip_text', None, (p, s)),
            'sensitive': ('gtk_widget_set_sensitive', None, (p, i)),
            'is_sensitive': ('gtk_widget_is_sensitive', i, (p,)),
            'state_flags': ('gtk_widget_get_state_flags', u, (p,)),
            'set_state': ('gtk_widget_set_state_flags', None, (p, u, i)),
            'child': ('gtk_window_set_child', None, (p, p)),
            'queue_draw': ('gtk_widget_queue_draw', None, (p,)),
            'queue_resize': ('gtk_widget_queue_resize', None, (p,)),
            'focus': ('gtk_window_set_focus', None, (p, p)),
            'button_child': ('gtk_button_get_child', p, (p,)),
            'check_child': ('gtk_check_button_get_child', p, (p,)),
            'pango_context': ('gtk_widget_get_pango_context', p, (p,)),
            'measure': ('gtk_widget_measure', None, (p, i, i, C.POINTER(i),
                         C.POINTER(i), C.POINTER(i), C.POINTER(i))),
            'provider_new': ('gtk_css_provider_new', p, ()),
            'load_css': ('gtk_css_provider_load_from_path', None, (p, s)),
            'add_provider': ('gtk_style_context_add_provider_for_display', None, (p, p, u)),
            'remove_provider': ('gtk_style_context_remove_provider_for_display', None, (p, p)),
            'display': ('gtk_widget_get_display', p, (p,)),
        }
        for attribute, (symbol, result, parameters) in signatures.items():
            setattr(self, attribute, bind(gtk, symbol, result, *parameters))
        self.ref_sink = bind(self.gobject, 'g_object_ref_sink', p, p)
        self.unref = bind(self.gobject, 'g_object_unref', None, p)
        self.connect = bind(self.gobject, 'g_signal_connect_data', C.c_ulong,
                            p, s, p, p, p, u)
        self.disconnect = bind(self.gobject, 'g_signal_handler_disconnect', None,
                               p, C.c_ulong)
        self.destroy_window = bind(gtk, 'gtk_window_destroy', None, p)
        self.x11_trap_push = bind(gtk, 'gdk_x11_display_error_trap_push', None, p)
        self.x11_trap_pop = bind(gtk, 'gdk_x11_display_error_trap_pop', i, p)
        pango = C.CDLL('libpango-1.0.so.0')
        self.font_description = bind(pango, 'pango_context_get_font_description', p, p)
        self.font_string = bind(pango, 'pango_font_description_to_string', p, p)
        self.free = bind(C.CDLL('libglib-2.0.so.0'), 'g_free', None, p)

    def native_request(self, widget, *, text_child=True, check=False):
        minimum, natural = [], []
        for orientation in (0, 1):
            low, preferred = C.c_int(), C.c_int()
            self.measure(widget, orientation, -1, C.byref(low), C.byref(preferred), None, None)
            minimum.append(low.value); natural.append(preferred.value)
        if text_child:
            label = self.check_child(widget) if check else self.button_child(widget)
            description = self.font_description(self.pango_context(label or widget))
            text = self.font_string(description)
            try:
                font = C.string_at(text).decode('utf-8') if text else ''
            finally:
                if text:self.free(text)
        else:
            font = ''
        return {'native_minimum_before_custom_size':minimum,
                'native_natural_before_custom_size':natural,
                'native_request_before_custom_size':natural,
                'font_description':font,'font_not_applicable':not text_child,
                'font_kind':1 if text_child else 2}

    def close_after_host_loss(self, window, cleanup=None):
        """Only after the bridge reports loss of the owned X11 host/child.

        The X server may have destroyed this surface with its parent. Trap its
        known stale-window cleanup; unexpected errors remain reported.
        """
        display = self.display(window)
        self.x11_trap_push(display)
        try:
            try:
                if cleanup:cleanup()
            finally:
                self.destroy_window(window)
        finally:
            error = self.x11_trap_pop(display)
        if error not in (0, 3):  # Success or BadWindow after verified host loss.
            raise RuntimeError('GTK4 host-loss cleanup X11 error: ' + str(error))
        return error

    def css_provider(self, path):
        class Error(C.Structure):
            _fields_ = [('domain', C.c_uint), ('code', C.c_int), ('message', C.c_char_p)]

        errors = []
        callback = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p,
                               C.c_void_p, C.c_void_p)(
            lambda _p, _s, error, _d:
            errors.append(C.cast(error, C.POINTER(Error)).contents.message.decode()))
        provider = self.provider_new()
        handler = self.connect(provider, b'parsing-error', C.cast(callback, C.c_void_p),
                                None, None, 0)
        try:
            self.load_css(provider, str(path).encode())
            if errors:
                raise ValueError('GTK4 CSS: ' + '; '.join(errors))
        except BaseException:
            self.disconnect(provider, handler)
            self.unref(provider)
            raise
        # A later reload must not call a callback whose owner disappeared.
        self.disconnect(provider, handler)
        return provider
