# SPDX-License-Identifier: GPL-3.0-or-later
"""Native QProgressBar with an explicit state property for Qt5 QSS."""

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import QProgressBar


class RecipeProgressBar(QProgressBar):
    """Keep native range/fraction/text while exposing stable theme states."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self._apply_recipe_state()

    def _apply_recipe_state(self):
        if not self.isEnabled():
            state = 'disabled'
        elif self.hasFocus():
            state = 'focused'
        elif not self.window().isActiveWindow():
            state = 'backdrop'
        else:
            state = 'normal'
        if self.property('domainosState') == state:
            return
        self.setProperty('domainosState', state)
        style = self.style()
        style.unpolish(self)
        style.polish(self)
        self.update()

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.Show, QEvent.EnabledChange, QEvent.FocusIn, QEvent.FocusOut,
                            QEvent.WindowActivate, QEvent.WindowDeactivate,
                            QEvent.ActivationChange):
            self._apply_recipe_state()
        return result
