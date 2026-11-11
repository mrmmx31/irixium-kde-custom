# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Qt6 tool button with a KDE-role arrow glyph from the recipe."""
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QToolButton


class RecipeArrowButton(QToolButton):
    """Keep QToolButton input semantics and paint the generated arrow pixels."""

    def __init__(self, asset_dir, shadow_px=2, parent=None):
        super().__init__(parent)
        self._images = {
            state: QImage(str(Path(asset_dir) / f'standalone-arrow-down-{state}.png'))
            for state in ('normal', 'pressed', 'backdrop', 'disabled')
        }
        if any(image.isNull() for image in self._images.values()):
            raise ValueError('Qt6 arrow glyph assets are missing or unreadable.')
        glyph_size = self._images['normal'].width()
        if glyph_size != self._images['normal'].height() or shadow_px < 0:
            raise ValueError('Qt6 standalone arrow geometry is invalid.')
        self.setFixedSize(glyph_size + 2 * shadow_px,
                          glyph_size + 2 * shadow_px)
        self.setAutoRaise(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def arrow_state(self):
        if not self.isEnabled():
            return 'disabled'
        if self.isDown():
            return 'pressed'
        if self.property('domainosBackdrop') is True:
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
        if event.type() in (
                QEvent.Type.EnabledChange,
                QEvent.Type.Enter,
                QEvent.Type.Leave,
                QEvent.Type.MouseButtonPress,
                QEvent.Type.MouseButtonRelease,
                QEvent.Type.WindowActivate,
                QEvent.Type.WindowDeactivate,
                QEvent.Type.ActivationChange,
                QEvent.Type.DynamicPropertyChange):
            self.update()
        return result
