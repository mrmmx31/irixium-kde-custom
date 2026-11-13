#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise generated QSS on real Qt6 QScrollBars and record pixel evidence."""
import argparse
import json
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stylesheet', type=Path, required=True)
parser.add_argument('--assets', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
    raise SystemExit('This widget probe requires the offscreen Qt platform.')

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (
    QApplication, QFrame, QScrollArea, QScrollBar, QStyle, QStyleOptionSlider,
    QVBoxLayout, QWidget, QPushButton)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'plasma/tests/galerias-nativas'))
from qt6_scrollbar_widgets import install_scrollbar_painters
from qt_scrollbar_spacing import install_scrollbar_spacing


def difference(first, second, rect):
    count = 0
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            if first.pixel(x, y) != second.pixel(x, y):
                count += 1
    return count


def save(image, name):
    target = args.output / name
    if not image.save(str(target), 'PNG'):
        raise RuntimeError('Could not save probe image: ' + name)
    return str(target)


def option_for(widget):
    option = QStyleOptionSlider()
    option.initFrom(widget)
    option.orientation = widget.orientation()
    option.minimum = widget.minimum()
    option.maximum = widget.maximum()
    option.sliderPosition = widget.sliderPosition()
    option.sliderValue = widget.value()
    option.pageStep = widget.pageStep()
    option.singleStep = widget.singleStep()
    option.upsideDown = widget.invertedAppearance()
    return option


def line_rect(widget, subcontrol):
    rect = widget.style().subControlRect(QStyle.ComplexControl.CC_ScrollBar,
                                         option_for(widget), subcontrol, widget)
    if rect.isEmpty() or not widget.rect().contains(rect):
        raise AssertionError(f'Qt6 line subcontrol has no in-bar allocation: {rect}')
    return rect


def main():
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    app = QApplication(sys.argv[:1])
    app.setStyle('Fusion')
    area = QScrollArea()
    area.setObjectName('domainosScrollArea')
    area.setWindowTitle('Qt6 DomainOS scrollbar native widget probe')
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.Box)
    content = QWidget()
    content.setMinimumSize(650, 620)
    layout = QVBoxLayout(content)
    for index in range(24):
        layout.addWidget(QPushButton(f'Native Qt6 content {index + 1}'))
    area.setWidget(content)
    install_scrollbar_painters(area, args.assets)
    spacing_adapter = install_scrollbar_spacing(area, 4, 6)
    vertical = area.verticalScrollBar()
    horizontal = area.horizontalScrollBar()
    vertical.setObjectName('domainosScrollBarVertical')
    horizontal.setObjectName('domainosScrollBarHorizontal')
    area.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    area.resize(520, 390)
    result = {'status': 'running', 'qtMajor': 6, 'style': app.style().metaObject().className(),
              'axes': {}, 'scope': 'real PyQt6 QScrollArea/QScrollBar; per-widget measured viewport margin plus generated QSS',
              'scrollSpacingAdapter': spacing_adapter}

    def exercise(axis, widget, controls):
        if not widget.isVisible() or widget.maximum() <= 0:
            raise AssertionError(f'{axis} scrollbar is not visible and scrollable')
        widget.setValue(widget.maximum() // 2)
        app.processEvents()
        cells = {}
        for direction, subcontrol, step in controls:
            rect = line_rect(widget, subcontrol)
            if direction in ('up', 'left') and (rect.top() > widget.height() // 3 if axis == 'vertical'
                                                 else rect.left() > widget.width() // 3):
                raise AssertionError(f'{direction} line is not at the leading edge: {rect}')
            if direction in ('down', 'right') and (rect.bottom() < 2 * widget.height() // 3 if axis == 'vertical'
                                                    else rect.right() < 2 * widget.width() // 3):
                raise AssertionError(f'{direction} line is not at the trailing edge: {rect}')
            point = rect.center()
            QTest.mouseMove(widget, point)
            app.processEvents()
            normal = widget.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
            before = widget.value()
            QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=point)
            app.processEvents()
            held = widget.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
            changes_held = difference(normal, held, rect)
            QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=point)
            QTest.mouseMove(widget, QPoint(0, 0))
            app.processEvents()
            released = widget.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
            changes_release = difference(normal, released, rect)
            after = widget.value()
            expected = max(0, min(widget.maximum(), before + step * widget.singleStep()))
            if changes_held <= 0:
                raise AssertionError(f'{direction} arrow did not change relief while held')
            if changes_release != 0:
                raise AssertionError(f'{direction} arrow relief did not return to normal: {changes_release} pixels')
            if after != expected:
                raise AssertionError(f'{direction} changed value to {after}, expected {expected}')
            cells[direction] = {'rect': [rect.x(), rect.y(), rect.width(), rect.height()],
                                'valueBefore': before, 'valueAfter': after,
                                'heldReliefPixelChanges': changes_held,
                                'releasePixelChanges': changes_release,
                                'normal': save(normal, f'{axis}-{direction}-normal.png'),
                                'held': save(held, f'{axis}-{direction}-held.png'),
                                'released': save(released, f'{axis}-{direction}-released.png')}
        return {'allocation': [widget.width(), widget.height()],
                'minimum': widget.minimum(), 'maximum': widget.maximum(),
                'pageStep': widget.pageStep(), 'singleStep': widget.singleStep(),
                'cells': cells}

    def run():
        try:
            result['axes']['vertical'] = exercise('vertical', vertical, (
                ('up', QStyle.SubControl.SC_ScrollBarSubLine, -1),
                ('down', QStyle.SubControl.SC_ScrollBarAddLine, 1)))
            result['axes']['horizontal'] = exercise('horizontal', horizontal, (
                ('left', QStyle.SubControl.SC_ScrollBarSubLine, -1),
                ('right', QStyle.SubControl.SC_ScrollBarAddLine, 1)))
            boundary_cells = {}
            for axis, widget, boundaries in (
                    ('vertical', vertical, (('up', vertical.minimum()),
                                             ('down', vertical.maximum()))),
                    ('horizontal', horizontal, (('left', horizontal.minimum()),
                                                ('right', horizontal.maximum())))):
                for direction, position in boundaries:
                    widget.setValue(position)
                    app.processEvents()
                    image = widget.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)
                    subcontrol = (QStyle.SubControl.SC_ScrollBarSubLine
                                  if direction in ('up', 'left')
                                  else QStyle.SubControl.SC_ScrollBarAddLine)
                    rect = line_rect(widget, subcontrol)
                    expected = QImage(str(args.assets / f'arrow-{direction}-normal.png'))
                    if expected.size() != rect.size():
                        raise AssertionError(f'{direction} recipe cell {expected.size()} != native allocation {rect.size()}')
                    crop = image.copy(rect)
                    mismatch = difference(crop, expected.convertToFormat(QImage.Format.Format_ARGB32),
                                         crop.rect())
                    boundary_capture = save(image, f'{axis}-{direction}-boundary.png')
                    if mismatch:
                        raise AssertionError(f'{direction} boundary cell differs from normal recipe by {mismatch} pixels ({boundary_capture})')
                    boundary_cells[direction] = {'axis': axis, 'value': position,
                        'rect': [rect.x(), rect.y(), rect.width(), rect.height()],
                        'pixelDifferencesFromRecipe': mismatch, 'capture': boundary_capture}
            result['boundaryCells'] = boundary_cells
            result['status'] = 'passed'
            result['screenshot'] = save(area.grab().toImage(), 'qt6-scrollbar-widget.png')
        except Exception as error:
            result['status'] = 'failed'
            result['error'] = f'{type(error).__name__}: {error}'
        target = args.output / 'QT6-WIDGET-PROBE.json'
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        target.chmod(0o600)
        app.quit()

    area.show()
    QTimer.singleShot(250, run)
    exit_code = app.exec()
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if exit_code == 0 and result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
