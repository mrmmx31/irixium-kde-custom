# SPDX-License-Identifier: GPL-3.0-or-later
"""Native list sample state, separate from scene layout and user project data."""
from sample_contract import SAMPLES


class ListControl:
    def __init__(self, Gtk, prefix, identity, sensitive=True):
        self.Gtk = Gtk
        self.widget = Gtk.ScrolledWindow()
        self.widget.set_name(prefix + 'Enclosure_' + identity)
        self.widget.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.widget.set_shadow_type(Gtk.ShadowType.IN)
        self.store = Gtk.ListStore(str)
        for key in ('list_a', 'list_b', 'list_c'):
            self.store.append([SAMPLES[key]])
        self.view = Gtk.TreeView(model=self.store)
        self.view.set_name(prefix + 'View_' + identity)
        self.view.set_headers_visible(False)
        self.view.set_sensitive(sensitive)
        self.view.append_column(Gtk.TreeViewColumn('Item', Gtk.CellRendererText(), text=0))
        self.view.get_selection().select_path(Gtk.TreePath.new_from_string('1'))
        self.widget.add(self.view)
        self.view.show_all()

    def snapshot(self):
        model, paths = self.view.get_selection().get_selected_rows()
        return {'rows': [row[0] for row in self.store],
                'selected': [p.to_string() for p in paths],
                'horizontal': self.widget.get_hadjustment().get_value(),
                'vertical': self.widget.get_vadjustment().get_value()}

    def restore(self, state):
        self.store.clear()
        for text in state['rows']:
            self.store.append([text])
        selection = self.view.get_selection()
        selection.unselect_all()
        for path in state['selected']:
            selection.select_path(self.Gtk.TreePath.new_from_string(path))
        # Allocation recomputes adjustment ranges. Apply once after it settles,
        # not before show_all (which would clamp valid saved offsets to zero).
        from gi.repository import GLib
        def offsets():
            if self.widget.get_parent() is not None:
                self.widget.get_hadjustment().set_value(state['horizontal'])
                self.widget.get_vadjustment().set_value(state['vertical'])
            return False
        GLib.idle_add(offsets)
