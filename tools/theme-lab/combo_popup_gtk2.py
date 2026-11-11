# SPDX-License-Identifier: GPL-3.0-or-later
"""Scope the native menu by its public attachment, never a global menu style."""
import re


def resolved_header_color(rc_text, prefix, style_id):
    style_name = prefix + '-' + style_id + '-popup-window'
    match = re.search(r'(?ms)^style "' + re.escape(style_name) +
                      r'" \{(.*?)^\}', rc_text)
    if not match:
        raise ValueError('Estilo GTK2 de fundo do popup ausente: ' + style_name)
    color = re.search(r'^\s*bg\[NORMAL\]\s*=\s*"(#[0-9a-fA-F]{6})"\s*$',
                      match.group(1), re.M)
    if not color:
        raise ValueError('Papel Header normal ausente no popup GTK2: ' + style_name)
    return color.group(1)


def bind_popup(Gtk, Gdk, combo, prefix, style_id, header_color):
    def changed(widget, _property):
        if not widget.get_property('popup-shown'):
            return
        for window in Gtk.Window.list_toplevels():
            menu = window.get_child()
            if isinstance(menu, Gtk.Menu) and menu.get_attach_widget() is widget:
                window.set_name(prefix + 'PopupWindow_' + style_id)
                window.reset_rc_styles()
                apply_rc_style(Gtk, window)
                window.modify_bg(Gtk.StateType.NORMAL, parse_color(Gdk, header_color))
                menu.set_name(prefix + 'Popup_' + style_id)
                menu.reset_rc_styles()
                apply_rc_style(Gtk, menu)
                for index, item in enumerate(menu.get_children()):
                    item.set_name(prefix + 'PopupItem_' + style_id + '_' + str(index))
                    item.reset_rc_styles()
                    apply_rc_style(Gtk, item)
                return
        # Preserve the native menu; a failed association must remain explicit.
        widget.set_tooltip_text('Menu GTK2 aberto; associação da paleta não localizada.')
    combo.connect('notify::popup-shown', changed)


def parse_color(Gdk, color):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        raise ValueError('Cor GTK2 de popup inválida.')
    return Gdk.Color(red=int(color[1:3], 16)*257,
                     green=int(color[3:5], 16)*257,
                     blue=int(color[5:7], 16)*257)


def apply_rc_style(Gtk, widget):
    """Resolve the late-named popup widget against the current GTK2 RC paths."""
    widget_path = widget.path()[1]
    class_path = widget.class_path()[1]
    style = Gtk.rc_get_style_by_paths(Gtk.Settings.get_default(), widget_path,
                                      class_path, widget.__gtype__)
    widget.set_style(style)
    widget.queue_draw()
