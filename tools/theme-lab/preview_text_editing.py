# SPDX-License-Identifier: GPL-3.0-or-later
"""Undo/Redo for real GTK2/3 preview fields; native clipboard actions remain.

History belongs to this preview process (and survives its scene rebuilds),
not the project or Motif editor journal. No palette, filesystem, GI import or desktop changes.
"""
import importlib.util
from pathlib import Path
_spec = importlib.util.spec_from_file_location('theme_lab_text_history', Path(__file__).with_name('preview_text_history.py'))
_history = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_history)
TextHistory = _history.TextHistory

class PreviewTextEditing:
    def __init__(self, widget, Gtk, Gdk, GLib, history=None):
        self.widget, self.Gtk, self.Gdk, self.GLib = widget, Gtk, Gdk, GLib
        self.buffer = widget.get_buffer() if isinstance(widget, Gtk.TextView) else None
        self.applying = False
        self.pending = 0
        self.history = history or TextHistory(self.read())
        if history is not None: self.restore(history.states[history.position])
        source = self.buffer or widget
        widget.connect('button-press-event', self.before_input)
        source.connect('changed', self.changed)
        widget.connect('key-press-event', self.key)
        widget.connect('populate-popup', self.popup)
        widget.connect('destroy', self.destroy)

    def read(self):
        if self.buffer:
            b = self.buffer
            text = b.get_text(b.get_start_iter(), b.get_end_iter(), True)
            return (text, b.get_iter_at_mark(b.get_insert()).get_offset(),
                    b.get_iter_at_mark(b.get_selection_bound()).get_offset(), None)
        w = self.widget
        cursor = w.get_position()
        bounds = w.get_selection_bounds()
        if len(bounds) == 3: bounds = bounds[1:] if bounds[0] else ()
        anchor = (bounds[0] if cursor == bounds[-1] else bounds[-1]) if bounds else cursor
        value = w.get_value() if isinstance(w, self.Gtk.SpinButton) else None
        return (w.get_text(), cursor, anchor, value)

    def before_input(self, *_):
        if not self.applying:
            self.flush()
            self.history.remember_selection(self.read())
        return False

    def changed(self, *_):
        if not self.applying and not self.pending:
            self.pending = self.GLib.idle_add(self.record)

    def record(self):
        self.pending = 0
        self.history.push(self.read())
        return False

    def flush(self):
        if self.pending:
            self.GLib.source_remove(self.pending)
            self.record()

    def step(self, direction):
        if not self.widget.get_editable() or not self.widget.get_sensitive(): return
        self.flush()
        state = self.history.step(direction)
        if state is None: return
        self.restore(state)

    def restore(self, state):
        text, cursor, anchor, value = state
        self.applying = True
        try:
            if self.buffer:
                self.buffer.set_text(text)
                self.buffer.select_range(self.buffer.get_iter_at_offset(cursor),
                                         self.buffer.get_iter_at_offset(anchor))
            else:
                if value is not None: self.widget.set_value(value)
                self.widget.set_text(text)
                # Spin text and committed numeric value are separate state.
                # Restoring must not act as Enter on a partial edited field.
                self.widget.select_region(anchor, cursor)
                if anchor == cursor: self.widget.set_position(cursor)
        finally:
            self.applying = False

    def key(self, _widget, event):
        self.before_input()
        state = int(event.state)
        if not state & int(self.Gdk.ModifierType.CONTROL_MASK): return False
        if state & int(self.Gdk.ModifierType.MOD1_MASK): return False
        key = (self.Gdk.keyval_name(event.keyval) or '').lower()
        if key in ('z', 'y'):
            redo = key == 'y' or state & int(self.Gdk.ModifierType.SHIFT_MASK)
            self.step(1 if redo else -1)
            return True
        return False

    def popup(self, _widget, menu):
        self.before_input()
        for label, direction in reversed((('Undo', -1), ('Redo', 1))):
            item = self.Gtk.MenuItem.new_with_label(label)
            item.set_tooltip_text("Restore the previous preview text." if direction < 0 else "Restore the preview text undone most recently.")
            item.set_sensitive(self.widget.get_editable() and
                0 <= self.history.position + direction < len(self.history.states))
            item.connect('activate', lambda _item, d=direction: self.step(d))
            menu.prepend(item)
            item.show()

    def destroy(self, *_):
        self.flush()


def bind(widget, Gtk, Gdk, GLib, history=None):
    if not hasattr(widget, '_theme_lab_text_editing'):
        widget._theme_lab_text_editing = PreviewTextEditing(widget, Gtk, Gdk, GLib, history)
    return widget._theme_lab_text_editing
