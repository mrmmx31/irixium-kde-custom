#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise check state transitions on a real Qt6 QCheckBox."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QCheckBox


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
    check = QCheckBox('Checked')
    check.setObjectName('domainosRecipeCheckBox')
    check.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    check.resize(120, 26)
    states = []
    check.toggled.connect(states.append)
    check.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    check.show()
    app.processEvents()
    unchecked = check.grab().toImage()

    QTest.mousePress(check, Qt.MouseButton.LeftButton,
                     pos=check.rect().center())
    app.processEvents()
    pressed = check.grab().toImage()
    QTest.mouseRelease(check, Qt.MouseButton.LeftButton,
                       pos=check.rect().center())
    app.processEvents()
    checked = check.grab().toImage()

    QTest.mouseClick(check, Qt.MouseButton.LeftButton,
                     pos=check.rect().center())
    app.processEvents()
    released = check.grab().toImage()

    check.setChecked(True)
    app.processEvents()
    checked_before_disable = check.grab().toImage()
    check.setEnabled(False)
    app.processEvents()
    disabled_checked = check.grab().toImage()

    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    unchecked.save(str(args.output / 'qt6-check-unchecked.png'), 'PNG')
    pressed.save(str(args.output / 'qt6-check-pressed.png'), 'PNG')
    checked.save(str(args.output / 'qt6-check-checked.png'), 'PNG')
    disabled_checked.save(str(args.output / 'qt6-check-disabled-checked.png'), 'PNG')
    proof = {
        'status': 'passed', 'qtMajor': 6,
        'widgetClass': check.metaObject().className(),
        'objectName': check.objectName(), 'checkable': check.isCheckable(),
        'size': [check.width(), check.height()], 'toggleStates': states,
        'pressedPixelChanges': changed_pixels(unchecked, pressed),
        'checkedPixelChanges': changed_pixels(unchecked, checked),
        'uncheckReleasePixelChanges': changed_pixels(unchecked, released),
        'disabledPixelChanges': changed_pixels(checked_before_disable, disabled_checked),
        'screenshots': {
            'unchecked': str(args.output / 'qt6-check-unchecked.png'),
            'pressed': str(args.output / 'qt6-check-pressed.png'),
            'checked': str(args.output / 'qt6-check-checked.png'),
            'disabledChecked': str(args.output / 'qt6-check-disabled-checked.png')},
    }
    assert proof['widgetClass'] == 'QCheckBox'
    assert proof['checkable'] is True
    assert proof['pressedPixelChanges'] > 0
    assert proof['checkedPixelChanges'] > 0
    assert proof['uncheckReleasePixelChanges'] == 0
    assert proof['disabledPixelChanges'] > 0
    assert states == [True, False, True]
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))
    check.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
