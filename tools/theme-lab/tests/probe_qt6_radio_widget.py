#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise an exclusive pair of real Qt6 QRadioButtons."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QButtonGroup, QHBoxLayout, QRadioButton, QWidget


def changed_pixels(left, right):
    a = left.convertToFormat(QImage.Format.Format_RGBA8888)
    b = right.convertToFormat(QImage.Format.Format_RGBA8888)
    if a.size() != b.size():
        return -1
    return sum(a.pixel(x, y) != b.pixel(x, y)
               for y in range(a.height()) for x in range(a.width()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    app = QApplication([])
    host = QWidget()
    layout = QHBoxLayout(host)
    first = QRadioButton('Radio A')
    first.setObjectName('domainosRecipeRadioButton')
    second = QRadioButton('Radio B')
    second.setObjectName('domainosRecipeRadioPeer')
    group = QButtonGroup(host)
    group.setExclusive(True)
    group.addButton(first)
    group.addButton(second)
    first.setChecked(True)
    first.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    second.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    layout.addWidget(first)
    layout.addWidget(second)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.show()
    app.processEvents()
    checked_first = host.grab().toImage()
    states = [[first.isChecked(), second.isChecked()]]

    QTest.mousePress(second, Qt.MouseButton.LeftButton,
                     pos=second.rect().center())
    app.processEvents()
    pressed_second = host.grab().toImage()
    QTest.mouseRelease(second, Qt.MouseButton.LeftButton,
                       pos=second.rect().center())
    app.processEvents()
    checked_second = host.grab().toImage()
    states.append([first.isChecked(), second.isChecked()])

    QTest.mouseClick(first, Qt.MouseButton.LeftButton,
                     pos=first.rect().center())
    app.processEvents()
    returned_first = host.grab().toImage()
    states.append([first.isChecked(), second.isChecked()])

    first.setChecked(False)
    second.setChecked(True)
    app.processEvents()
    checked_before_disable = host.grab().toImage()
    second.setEnabled(False)
    app.processEvents()
    disabled_second = host.grab().toImage()

    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    checked_first.save(str(args.output / 'qt6-radio-first-checked.png'), 'PNG')
    pressed_second.save(str(args.output / 'qt6-radio-second-pressed.png'), 'PNG')
    checked_second.save(str(args.output / 'qt6-radio-second-checked.png'), 'PNG')
    disabled_second.save(str(args.output / 'qt6-radio-second-disabled.png'), 'PNG')
    proof = {
        'status': 'passed', 'qtMajor': 6,
        'widgetClasses': [first.metaObject().className(), second.metaObject().className()],
        'exclusive': group.exclusive(), 'states': states,
        'checkedStatePixelChanges': changed_pixels(checked_first, checked_second),
        'pressedPixelChanges': changed_pixels(checked_first, pressed_second),
        'exclusiveReturnPixelChanges': changed_pixels(checked_first, returned_first),
        'disabledPixelChanges': changed_pixels(checked_before_disable, disabled_second),
        'screenshots': {
            'firstChecked': str(args.output / 'qt6-radio-first-checked.png'),
            'secondPressed': str(args.output / 'qt6-radio-second-pressed.png'),
            'secondChecked': str(args.output / 'qt6-radio-second-checked.png'),
            'secondDisabled': str(args.output / 'qt6-radio-second-disabled.png')},
    }
    assert proof['widgetClasses'] == ['QRadioButton', 'QRadioButton']
    assert proof['exclusive'] is True
    assert proof['checkedStatePixelChanges'] > 0
    assert proof['pressedPixelChanges'] > 0
    assert proof['exclusiveReturnPixelChanges'] == 0
    assert proof['disabledPixelChanges'] > 0
    assert states == [[True, False], [False, True], [True, False]]
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))
    host.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
