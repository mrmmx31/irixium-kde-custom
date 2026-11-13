# SPDX-License-Identifier: GPL-3.0-or-later
"""Scoped GTK2 native command/arrow-button demonstration lifecycle.

The renderer requires an explicit verified bridge. This controller does not load an
ABI bridge or change palette/input flags: its caller must provide a verified
visual setter for the exact native widget/runtime before integration.
"""


class PressedButtonDemo:
    def __init__(self, button, set_visual):
        self.button = button
        self.set_visual = set_visual
        self.handlers = []
        self.closed = False
        try:
            for signal in ('enter-notify-event', 'leave-notify-event'):
                self.handlers.append(button.connect_after(signal, self._keep))
            # GtkButton's release event returns TRUE, so an after-handler on
            # that event is skipped. Its released signal is RUN_FIRST: bind
            # after the native action/state update, without emitting a click.
            self.handlers.append(button.connect_after('released', self._released))
            self.handlers.append(button.connect('destroy', self._destroy))
            self.set_visual(True)
        except Exception as error:
            # Construction is transactional: no stale callback retains a
            # rejected candidate when a native setter or binding fails.
            try:
                self.close()
            except Exception as cleanup_error:
                raise error from cleanup_error
            raise

    def _keep(self, _button, _event):
        if not self.closed:
            try:
                self.set_visual(True)
            except Exception as error:
                try:
                    self.close()
                except Exception as cleanup_error:
                    raise error from cleanup_error
                raise
        return False

    def _destroy(self, _button):
        self.close(restore=False)

    def _released(self, button):
        self._keep(button, None)

    def close(self, restore=True):
        if self.closed:
            return
        self.closed = True
        handlers, self.handlers = self.handlers, []
        for handler in handlers:
            self.button.disconnect(handler)
        try:
            if restore:
                self.set_visual(False)
        finally:
            release = getattr(self.set_visual, 'close', None)
            if release is not None:
                release()

