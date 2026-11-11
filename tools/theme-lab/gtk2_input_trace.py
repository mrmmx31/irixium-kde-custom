# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in, bounded GTK2 event trace used only to diagnose the public preview."""
import json
import os
from pathlib import Path
import sys
import time


class Gtk2InputTrace:
    """Observe existing GtkRange signals without consuming or synthesizing input."""
    def __init__(self, widgets, records, directory):
        path = Path(directory) / 'gtk2-input-trace.jsonl'
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        self.stream = os.fdopen(fd, 'wb', buffering=0)
        self.failed = False
        self.handlers = []
        for index, widget in widgets.items():
            record = records[index]
            if record['id'] not in ('scroll_h', 'scroll_v'):
                continue
            self.handlers.extend(((widget, widget.connect('event', self.event, index)),
                                  (widget, widget.connect('change-value', self.change_value, index)),
                                  (widget.get_adjustment(), widget.get_adjustment().connect(
                                      'value-changed', self.value_changed, index))))

    def write(self, index, stage, **fields):
        if self.failed:
            return
        payload = {'time_monotonic_ns': time.monotonic_ns(), 'control_index': index,
                   'stage': stage, **fields}
        try:
            self.stream.write((json.dumps(payload, allow_nan=False) + '\n').encode('utf-8'))
        except (OSError, TypeError, ValueError) as error:
            self.failed = True
            print('GTK2 input trace stopped: ' + str(error), file=sys.stderr, flush=True)

    @staticmethod
    def event_name(event):
        value = getattr(event.type, 'value_nick', None)
        return value if isinstance(value, str) else str(event.type)

    def event(self, widget, event, index):
        name = self.event_name(event)
        if name in ('button-press', 'button-release', 'motion-notify', 'enter-notify', 'leave-notify'):
            window = getattr(event, 'window', None)
            self.write(index, 'gdk-event', event=name,
                       button=int(getattr(event, 'button', 0)),
                       x=float(getattr(event, 'x', 0)), y=float(getattr(event, 'y', 0)),
                       event_window=(window.get_xid() if window is not None else None),
                       widget_window=(widget.get_window().get_xid()
                                      if widget.get_window() is not None else None))
        return False

    def change_value(self, _widget, scroll_type, new_value, index):
        self.write(index, 'gtk-range-change-value',
                   scroll_type=getattr(scroll_type, 'value_nick', str(scroll_type)),
                   requested_value=float(new_value))
        return False

    def value_changed(self, adjustment, index):
        self.write(index, 'gtk-adjustment-value', value=float(adjustment.get_value()))

    def close(self):
        for widget, handler in self.handlers:
            try:
                widget.disconnect(handler)
            except (TypeError, RuntimeError):
                pass
        self.handlers.clear()
        if self.stream is not None:
            self.stream.close()
            self.stream = None
