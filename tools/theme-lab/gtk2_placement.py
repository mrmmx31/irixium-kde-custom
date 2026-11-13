# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK2 placement, with cancellable allocation reconciliation."""
from gtk2_anchor_geometry import allocated_origin


class Placement:
    def __init__(self, scene, GLib):
        self.scene, self.GLib = scene, GLib
        self.pending, self.overrides, self.handlers = {}, {}, []
        self.closed = False
        self.handlers.append((scene.fixed, scene.fixed.connect('destroy', self.close)))
        for index, widget in scene.widgets.items():
            if scene.records[index]['id'] in ('scroll_h', 'scroll_v'):
                self.handlers.append((widget, widget.connect('size-allocate', self.changed, index)))

    def origin(self, index, position=None):
        record = self.scene.records[index]
        if position is not None:
            record = dict(record, x=position[0], y=position[1])
        return allocated_origin(record, self.scene.widgets[index])

    def apply(self, index, position=None):
        if self.closed:
            raise RuntimeError('Posicionamento GTK2 encerrado.')
        origin = self.origin(index, position)
        widget = self.scene.widgets[index]
        allocation = widget.get_allocation()
        current = (allocation.x, allocation.y)
        if current != origin:
            self.scene.fixed.move(widget, *origin)
        return origin

    def preview(self, index, position):
        # Validate before installing an override. Allocation changes during a
        # drag must keep the provisional trailing coordinate, not snap back.
        self.origin(index, position)
        self.overrides[index] = position
        self.apply(index, position)

    def reset(self, index):
        self.overrides.pop(index, None)
        self.apply(index)

    def changed(self, _widget, _allocation, index):
        if (not self.closed and self.scene.records[index].get('length_anchor')
                and index not in self.pending):
            self.pending[index] = self.GLib.idle_add(self.reconcile, index)

    def reconcile(self, index):
        self.pending.pop(index, None)
        if self.closed:
            return False
        try:
            self.apply(index, self.overrides.get(index))
        except (ValueError, TypeError, RuntimeError) as error:
            self.scene.last_error = str(error)
            self.scene.window.set_title('Posição GTK2 não aplicada: ' + str(error)[:160])
        return False

    def close(self, *_):
        if self.closed:
            return
        self.closed = True
        for source in self.pending.values():
            self.GLib.source_remove(source)
        self.pending.clear()
        self.overrides.clear()
        for widget, handler in self.handlers:
            if widget.handler_is_connected(handler):
                widget.disconnect(handler)
        self.handlers.clear()
