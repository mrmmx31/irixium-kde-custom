# SPDX-License-Identifier: GPL-3.0-or-later
"""Native unlabelled frame sample, with a role-coloured event enclosure."""
from sample_contract import SAMPLES
from gtk2_buttons import geometry


class FrameControl:
    def __init__(self, Gtk, recipe, prefix, identity, sensitive=True):
        self.widget = Gtk.EventBox()
        self.widget.set_visible_window(True)
        self.widget.set_above_child(True)
        self.widget.set_name(prefix + 'Content_' + identity)
        self.frame = Gtk.Frame()
        self.frame.set_name(prefix + '_' + identity)
        # Match the native XmFrame sample (XmSHADOW_IN, 2 px).
        self.frame.set_shadow_type(Gtk.ShadowType.IN)
        self.alignment = Gtk.Alignment.new(.5, .5, 1, 1)
        padding = geometry(recipe)[1]
        self.alignment.set_padding(padding, padding, padding, padding)
        self.label = Gtk.Label(label=SAMPLES['frame'])
        self.label.set_name(prefix + 'Content_' + identity)
        self.label.set_sensitive(sensitive)
        self.alignment.add(self.label)
        self.frame.add(self.alignment)
        self.widget.add(self.frame)
        self.frame.show_all()
