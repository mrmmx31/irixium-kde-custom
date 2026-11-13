# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Qt5 tool button with recipe-owned, KDE-role arrow glyph states."""
from pathlib import Path

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QToolButton


class RecipeArrowButton(QToolButton):
    """Keep QToolButton interaction and paint only its generated arrow glyph."""

    def __init__(self, asset_dir, shadow_px=2, parent=None):
        super().__init__(parent)
        self._images = {
            state: QImage(str(Path(asset_dir) / f'standalone-arrow-down-{state}.png'))
            for state in ('normal', 'pressed', 'backdrop', 'disabled')
        }
        if any(image.isNull() for image in self._images.values()):
            raise ValueError('Qt5 arrow glyph assets are missing or unreadable.')
        size = self._images['normal'].width() + 2 * shadow_px
        if self._images['normal'].width() != self._images['normal'].height() or size <= 0:
            raise ValueError('Qt5 standalone arrow geometry is invalid.')
        self.setFixedSize(size, size)
        self.setAutoRaise(False)
        self.setFocusPolicy(Qt.StrongFocus)

    def arrow_state(self):
        if not self.isEnabled():
            return 'disabled'
        if self.isDown():
            return 'pressed'
        if not self.window().isActiveWindow():
            return 'backdrop'
        return 'normal'

    def paintEvent(self, event):
        super().paintEvent(event)
        image = self._images[self.arrow_state()]
        x = (self.width() - image.width()) // 2
        y = (self.height() - image.height()) // 2
        painter = QPainter(self)
        painter.drawImage(x, y, image)
        painter.end()

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.EnabledChange, QEvent.Enter, QEvent.Leave,
                            QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                            QEvent.WindowActivate, QEvent.WindowDeactivate,
                            QEvent.ActivationChange):
            self.update()
        return result
