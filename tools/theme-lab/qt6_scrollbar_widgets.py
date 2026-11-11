# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply recipe arrow cells to real Qt6 scrollbar widgets without changing input."""
from pathlib import Path


def install_scrollbar_painters(area, asset_dir):
    """Replace QScrollArea bars with QScrollBar subclasses that paint recipe cells.

    Qt owns value/range, geometry, thumb movement, wheel, and pointer input. The
    subclass overlays only the four fixed-size arrow cells after the native
    scrollbar has painted, so boundary arrows remain visible when line input is
    naturally clamped.
    """
    from PyQt6.QtCore import QEvent, Qt
    from PyQt6.QtGui import QCursor, QPainter, QPixmap
    from PyQt6.QtWidgets import QApplication, QScrollBar, QStyle, QStyleOptionSlider

    assets = {}
    for state in ('normal', 'pressed', 'backdrop', 'disabled'):
        assets[state] = {}
        for direction in ('up', 'down', 'left', 'right'):
            path = Path(asset_dir) / f'arrow-{direction}-{state}.png'
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                raise RuntimeError(f'Qt6 scrollbar recipe image could not be loaded: {path}')
            assets[state][direction] = pixmap

    class RecipeScrollBar(QScrollBar):
        def __init__(self, orientation, parent=None):
            super().__init__(orientation, parent)
            self._recipe_assets = assets
            self.setObjectName('domainosScrollBarVertical'
                               if orientation == Qt.Orientation.Vertical
                               else 'domainosScrollBarHorizontal')
            self.setMouseTracking(True)

        def paintEvent(self, event):
            super().paintEvent(event)
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            controls = (
                (QStyle.SubControl.SC_ScrollBarSubLine, 'up' if self.orientation() == Qt.Orientation.Vertical else 'left'),
                (QStyle.SubControl.SC_ScrollBarAddLine, 'down' if self.orientation() == Qt.Orientation.Vertical else 'right'),
            )
            cursor = self.mapFromGlobal(QCursor.pos())
            buttons = QApplication.mouseButtons()
            active = self.isActiveWindow()
            whole_disabled = not self.isEnabled()
            painter = QPainter(self)
            for subcontrol, direction in controls:
                rect = self.style().subControlRect(
                    QStyle.ComplexControl.CC_ScrollBar, option, subcontrol, self)
                if rect.isEmpty():
                    continue
                if whole_disabled:
                    state = 'disabled'
                elif not active:
                    state = 'backdrop'
                elif buttons & Qt.MouseButton.LeftButton and rect.contains(cursor):
                    state = 'pressed'
                else:
                    state = 'normal'
                painter.drawPixmap(rect, self._recipe_assets[state][direction])
            painter.end()

        def event(self, event):
            result = super().event(event)
            if event.type() in (QEvent.Type.WindowActivate, QEvent.Type.WindowDeactivate,
                                QEvent.Type.Enter, QEvent.Type.Leave):
                self.update()
            return result

    area.setVerticalScrollBar(RecipeScrollBar(Qt.Orientation.Vertical, area))
    area.setHorizontalScrollBar(RecipeScrollBar(Qt.Orientation.Horizontal, area))
    return area.verticalScrollBar(), area.horizontalScrollBar()
