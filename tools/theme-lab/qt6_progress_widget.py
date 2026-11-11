# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Qt6 progress bar exposing stable palette states to the recipe QSS."""

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QProgressBar


class RecipeProgressBar(QProgressBar):
    """Keep Qt's range, fill fraction and text while tracking visual state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._window_backdrop = False
        self._apply_recipe_state()

    def _apply_recipe_state(self):
        if not self.isEnabled():
            state = 'disabled'
        elif self.hasFocus():
            state = 'focused'
        elif self._window_backdrop:
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
        if event.type() in (
                QEvent.Type.Show,
                QEvent.Type.EnabledChange,
                QEvent.Type.FocusIn,
                QEvent.Type.FocusOut,
                QEvent.Type.WindowActivate,
                QEvent.Type.WindowDeactivate,
                QEvent.Type.ActivationChange):
            self._apply_recipe_state()
        return result

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.WindowDeactivate:
            self._window_backdrop = True
            self._apply_recipe_state()
        elif event.type() == QEvent.Type.WindowActivate:
            self._window_backdrop = False
            self._apply_recipe_state()
        return False
