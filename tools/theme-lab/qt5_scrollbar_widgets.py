# SPDX-License-Identifier: GPL-3.0-or-later
"""Paint recipe arrow cells on real Qt5 scrollbars while retaining native input."""
from pathlib import Path


def install_scrollbar_painters(area, asset_dir):
    from PyQt5.QtCore import QEvent, Qt
    from PyQt5.QtGui import QCursor, QPainter, QPixmap
    from PyQt5.QtWidgets import QApplication, QScrollBar, QStyle, QStyleOptionSlider

    assets = {}
    for state in ('normal', 'pressed', 'backdrop', 'disabled'):
        assets[state] = {}
        for direction in ('up', 'down', 'left', 'right'):
            path = Path(asset_dir) / f'arrow-{direction}-{state}.png'
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                raise RuntimeError(f'Qt5 scrollbar recipe image could not be loaded: {path}')
            assets[state][direction] = pixmap

    class RecipeScrollBar(QScrollBar):
        def __init__(self, orientation, parent=None):
            super().__init__(orientation, parent)
            self._recipe_assets = assets
            self.setObjectName('domainosScrollBarVertical'
                               if orientation == Qt.Vertical else 'domainosScrollBarHorizontal')
            self.setMouseTracking(True)

        def paintEvent(self, event):
            super().paintEvent(event)
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            vertical = self.orientation() == Qt.Vertical
            controls = ((QStyle.SC_ScrollBarSubLine, 'up' if vertical else 'left'),
                        (QStyle.SC_ScrollBarAddLine, 'down' if vertical else 'right'))
            cursor = self.mapFromGlobal(QCursor.pos())
            buttons = QApplication.mouseButtons()
            active = self.isActiveWindow()
            disabled = not self.isEnabled()
            painter = QPainter(self)
            for subcontrol, direction in controls:
                rect = self.style().subControlRect(QStyle.CC_ScrollBar, option,
                                                   subcontrol, self)
                if rect.isEmpty():
                    continue
                if disabled:
                    state = 'disabled'
                elif not active:
                    state = 'backdrop'
                elif buttons & Qt.LeftButton and rect.contains(cursor):
                    state = 'pressed'
                else:
                    state = 'normal'
                painter.drawPixmap(rect, self._recipe_assets[state][direction])
            painter.end()

        def event(self, event):
            result = super().event(event)
            if event.type() in (QEvent.WindowActivate, QEvent.WindowDeactivate,
                                QEvent.Enter, QEvent.Leave):
                self.update()
            return result

    area.setVerticalScrollBar(RecipeScrollBar(Qt.Vertical, area))
    area.setHorizontalScrollBar(RecipeScrollBar(Qt.Horizontal, area))
    return area.verticalScrollBar(), area.horizontalScrollBar()
