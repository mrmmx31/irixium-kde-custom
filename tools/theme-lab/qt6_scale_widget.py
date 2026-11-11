# SPDX-License-Identifier: GPL-3.0-or-later
"""Small Qt6 bridge for widget window-backdrop palette state."""

from PyQt6.QtCore import QEvent, QObject


class WindowBackdropTracker(QObject):
    """Expose top-level activation as a repolished QSS dynamic property.

    Qt style sheets do not provide a reliable QSlider ``:!active`` mapping for
    an inactive top-level window: on an idle widget it can match before the
    window loses activation. The property keeps active and backdrop recipes
    distinct while leaving the widget's native editing or input semantics intact.
    """

    PROPERTY = 'domainosBackdrop'

    def __init__(self, window, slider):
        super().__init__(window)
        self._slider = slider
        self._backdrop = False
        slider.setProperty(self.PROPERTY, False)

    @property
    def backdrop(self):
        return self._backdrop

    def _set_backdrop(self, value):
        value = bool(value)
        if value == self._backdrop:
            return
        self._backdrop = value
        self._slider.setProperty(self.PROPERTY, value)
        style = self._slider.style()
        style.unpolish(self._slider)
        style.polish(self._slider)
        self._slider.update()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.WindowDeactivate:
            self._set_backdrop(True)
        elif event.type() == QEvent.Type.WindowActivate:
            self._set_backdrop(False)
        return False
