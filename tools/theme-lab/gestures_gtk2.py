# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 layout gestures; native widget input is untouched without Ctrl."""
import math


def root_position(event):
    # GTK2 GI delivers typed EventButton/EventMotion records rather than the
    # Event union exposing get_root_coords. Those two callback records declare
    # x_root/y_root explicitly; never reinterpret local x/y as root coordinates.
    getter = getattr(event, 'get_root_coords', None)
    value = getter() if getter is not None else (event.x_root, event.y_root)
    if len(value) == 3:
        if not value[0]: raise ValueError('Coordenadas do gesto indisponíveis.')
        value = value[1:]
    if len(value) != 2 or any(not math.isfinite(v) for v in value):
        raise ValueError('Coordenadas do gesto inválidas.')
    return value


class LayoutGestures:
    def __init__(self, scene, Gdk):
        self.scene, self.Gdk, self.active = scene, Gdk, None
        self.handlers = []
        for index, widget in scene.widgets.items():
            targets = getattr(scene,'radio_groups',{}).get(index)
            targets = targets.members if targets is not None else (getattr(scene,'list_controls',{}).get(index).view,) if index in getattr(scene,'list_controls',{}) else (widget,)
            for target in targets:
                self.bind(target,index)
        self.handlers.append((scene.window, scene.window.connect('destroy', self.cancel)))

    def bind(self, widget, index):
        widget.add_events(self.Gdk.EventMask.BUTTON_PRESS_MASK | self.Gdk.EventMask.BUTTON_RELEASE_MASK |
                          self.Gdk.EventMask.POINTER_MOTION_MASK)
        for signal, callback, arguments in (
                ('button-press-event', self.press, (index,)),
                ('motion-notify-event', self.motion, (index,)),
                ('button-release-event', self.release, (index,)),
                ('unmap', self.cancel, ())):
            self.handlers.append((widget, widget.connect(signal, callback, *arguments)))

    def close(self):
        self.cancel()
        for widget, handler in self.handlers:
            if widget.handler_is_connected(handler): widget.disconnect(handler)
        self.handlers.clear()

    def failure(self, error):
        self.scene.last_error = str(error)
        self.scene.window.set_title('Gesto GTK2 não salvo: ' + str(error)[:160])

    def press(self, widget, event, index):
        if event.button != 1 or not int(event.state) & int(self.Gdk.ModifierType.CONTROL_MASK):
            return False
        try:
            widget=self.scene.widgets[index]
            self.cancel()
            root = root_position(event)
            self.scene.select_control(index)
            record = self.scene.records[index]
            self.active = {'widget': widget, 'index': index, 'root': root,
                           'origin': (record['x'], record['y']), 'position': (record['x'], record['y'])}
            self.scene.Gtk.grab_add(widget)
        except (OSError, ValueError, TypeError, RuntimeError, AttributeError) as error:
            self.cancel()
            self.failure(error)
        return True

    def position(self, event):
        root = root_position(event)
        return tuple(max(0, min(2048, round(origin + current - start)))
                     for origin, current, start in zip(self.active['origin'], root, self.active['root']))

    def motion(self, widget, event, index):
        if self.active is None or self.active['index'] != index:
            return False
        try:
            widget=self.scene.widgets[index]
            position = self.position(event)
            self.scene.placement.preview(index, position)
            self.active['position'] = position
        except (ValueError, TypeError, RuntimeError, AttributeError) as error:
            self.cancel()
            self.failure(error)
        return True

    def release(self, widget, event, index):
        if self.active is None or self.active['index'] != index or event.button != 1:
            return False
        active = self.active
        try:
            widget=self.scene.widgets[index]
            position = self.position(event)
            if position != active['origin']:
                self.scene.move_control(index, *position)
            else:
                self.scene.placement.reset(index)
            # The event is persisted before the authoritative scene record is
            # changed. Cancel rolls back only while that commit is pending.
            self.active = None
            self.scene.Gtk.grab_remove(widget)
        except (OSError, ValueError, TypeError, RuntimeError, AttributeError) as error:
            self.cancel()
            self.failure(error)
        return True

    def cancel(self, *_):
        active, self.active = self.active, None
        if active is not None:
            if not self.scene.placement.closed:
                self.scene.placement.reset(active['index'])
            self.scene.Gtk.grab_remove(active['widget'])
