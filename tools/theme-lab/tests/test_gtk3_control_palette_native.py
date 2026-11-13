#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify GTK3's real CSS-node selectors isolate the five button-like controls.

RGB values below are synthetic test signals only. Production CSS continues to
use KDE semantic role aliases; this probe checks selector ownership, not theme
color design or historical fidelity.
"""
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk

Gtk.init([])

signals = {
    'push': (235, 30, 40),
    'toggle': (30, 220, 80),
    'combo': (35, 80, 230),
    'spin': (240, 200, 30),
    'arrow': (180, 40, 200),
}
css = '''
button:not(.toggle):not(.combo):not(.up):not(.down):not(.theme-lab-arrow) { background-color: rgb(235,30,40); }
button.toggle { background-color: rgb(30,220,80); }
combobox > box > button.combo { background-color: rgb(35,80,230); }
spinbutton > button { background-color: rgb(240,200,30); }
button.theme-lab-arrow { background-color: rgb(180,40,200); }
'''
provider = Gtk.CssProvider.new()
errors = []
provider.connect('parsing-error', lambda _provider, _section, error: errors.append(str(error)))
provider.load_from_data(css.encode('utf-8'))
assert not errors, errors
screen = Gdk.Screen.get_default()
Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

def make_widget(kind):
    if kind == 'push':
        return Gtk.Button()
    if kind == 'toggle':
        return Gtk.ToggleButton()
    if kind == 'combo':
        combo = Gtk.ComboBoxText()
        combo.append_text('first')
        combo.append_text('second')
        combo.set_active(0)
        return combo
    if kind == 'spin':
        return Gtk.SpinButton.new_with_range(0, 99, 1)
    button = Gtk.Button()
    button.get_style_context().add_class('theme-lab-arrow')
    button.add(Gtk.Arrow(arrow_type=Gtk.ArrowType.DOWN, shadow_type=Gtk.ShadowType.NONE))
    return button

def has_signal(pixbuf, rgb):
    data = pixbuf.get_pixels()
    rowstride = pixbuf.get_rowstride()
    channels = pixbuf.get_n_channels()
    width, height = pixbuf.get_width(), pixbuf.get_height()
    for y in range(height):
        for x in range(width):
            offset = y * rowstride + x * channels
            pixel = data[offset:offset + 3]
            if len(pixel) == 3 and all(abs(pixel[i] - rgb[i]) <= 2 for i in range(3)):
                return True
    return False

def render(kind):
    window = Gtk.OffscreenWindow()
    widget = make_widget(kind)
    widget.set_size_request(110, 48)
    window.add(widget)
    window.set_default_size(150, 64)
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    pixbuf = window.get_pixbuf()
    assert pixbuf is not None, kind + ': no native offscreen pixels'
    result = pixbuf.copy()
    window.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    return result

images = {kind: render(kind) for kind in signals}
for owner, rgb in signals.items():
    assert has_signal(images[owner], rgb), owner + ': scoped selector did not paint the native widget'
    for other, image in images.items():
        if other != owner:
            assert not has_signal(image, rgb), owner + ' palette leaked into ' + other
print('GTK3 native selector isolation passed: push, toggle, combo, spin and standalone arrow.')
