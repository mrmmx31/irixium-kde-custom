#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise checked/pressed states on a real Qt6 checkable QPushButton."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton


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
    button = QPushButton('Toggle')
    button.setObjectName('domainosRecipeToggleButton')
    button.setCheckable(True)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.resize(180, 38)
    states = []
    button.toggled.connect(states.append)
    button.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    button.show()
    app.processEvents()
    normal = button.grab().toImage()

    QTest.mousePress(button, Qt.MouseButton.LeftButton,
                     pos=button.rect().center())
    app.processEvents()
    pressed = button.grab().toImage()
    QTest.mouseRelease(button, Qt.MouseButton.LeftButton,
                       pos=button.rect().center())
    app.processEvents()
    checked = button.grab().toImage()

    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    normal.save(str(args.output / 'qt6-toggle-normal.png'), 'PNG')
    pressed.save(str(args.output / 'qt6-toggle-pressed.png'), 'PNG')
    checked.save(str(args.output / 'qt6-toggle-checked.png'), 'PNG')

    QTest.mousePress(button, Qt.MouseButton.LeftButton,
                     pos=button.rect().center())
    app.processEvents()
    checked_pressed = button.grab().toImage()
    QTest.mouseRelease(button, Qt.MouseButton.LeftButton,
                       pos=button.rect().center())
    app.processEvents()
    unchecked = button.grab().toImage()

    button.setChecked(True)
    app.processEvents()
    checked_before_disable = button.grab().toImage()
    button.setEnabled(False)
    app.processEvents()
    disabled_checked = button.grab().toImage()
    disabled_path = args.output / 'qt6-toggle-checked-disabled.png'
    disabled_checked.save(str(disabled_path), 'PNG')

    proof = {
        'status': 'passed', 'qtMajor': 6,
        'widgetClass': button.metaObject().className(),
        'objectName': button.objectName(), 'checkable': button.isCheckable(),
        'size': [button.width(), button.height()], 'toggleStates': states,
        'pressedPixelChanges': changed_pixels(normal, pressed),
        'checkedPixelChanges': changed_pixels(normal, checked),
        'checkedPressedPixelChanges': changed_pixels(checked, checked_pressed),
        'uncheckReleasePixelChanges': changed_pixels(normal, unchecked),
        'disabledPixelChanges': changed_pixels(checked_before_disable, disabled_checked),
        'screenshots': {
            'normal': str(args.output / 'qt6-toggle-normal.png'),
            'pressed': str(args.output / 'qt6-toggle-pressed.png'),
            'checked': str(args.output / 'qt6-toggle-checked.png'),
            'disabledChecked': str(disabled_path)},
    }
    assert proof['widgetClass'] == 'QPushButton'
    assert proof['checkable'] is True
    assert proof['pressedPixelChanges'] > 0
    assert proof['checkedPixelChanges'] > 0
    assert proof['checkedPressedPixelChanges'] == 0
    assert proof['uncheckReleasePixelChanges'] == 0
    assert proof['disabledPixelChanges'] > 0
    assert states == [True, False, True]
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))
    button.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
