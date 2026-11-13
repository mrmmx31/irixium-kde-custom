#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a real Qt6 QPushButton with KDE-role-derived recipe states."""
import argparse
import json
from pathlib import Path
import re

from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication, QPushButton


def changed_pixels(left, right):
    a = left.convertToFormat(QImage.Format.Format_RGBA8888)
    b = right.convertToFormat(QImage.Format.Format_RGBA8888)
    if a.size() != b.size():
        return -1
    return sum(a.pixel(x, y) != b.pixel(x, y)
               for y in range(a.height()) for x in range(a.width()))


def qss_color(stylesheet, selector, property_name):
    match = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', stylesheet, re.S)
    if not match:
        raise AssertionError(f'Missing QSS selector: {selector}')
    value = re.search(re.escape(property_name) + r'\s*:\s*(#[0-9a-fA-F]{6})',
                      match.group(1))
    if not value:
        raise AssertionError(f'Missing {property_name} in {selector}')
    return value.group(1).lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stylesheet = args.stylesheet.read_text(encoding='utf-8')
    app = QApplication([])
    button = QPushButton('Press')
    button.setObjectName('domainosRecipePushButton')
    button.resize(180, 38)
    clicks = []
    button.clicked.connect(lambda: clicks.append(True))
    button.setStyleSheet(stylesheet)
    button.show()
    app.processEvents()
    normal = button.grab().toImage()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    normal.save(str(args.output / 'qt6-push-normal.png'), 'PNG')
    expected_normal = qss_color(
        stylesheet, 'QPushButton#domainosRecipePushButton', 'background-color')
    normal_sample = normal.pixelColor(button.width() - 4,
                                      button.height() // 2).name().lower()

    QTest.mousePress(button, Qt.MouseButton.LeftButton,
                     pos=button.rect().center())
    app.processEvents()
    pressed = button.grab().toImage()
    pressed.save(str(args.output / 'qt6-push-pressed.png'), 'PNG')
    QTest.mouseRelease(button, Qt.MouseButton.LeftButton,
                       pos=button.rect().center())
    app.processEvents()
    released = button.grab().toImage()

    button.setEnabled(False)
    app.processEvents()
    disabled = button.grab().toImage()
    disabled.save(str(args.output / 'qt6-push-disabled.png'), 'PNG')
    expected_disabled = qss_color(
        stylesheet, 'QPushButton#domainosRecipePushButton:disabled',
        'background-color')
    disabled_sample = disabled.pixelColor(button.width() - 4,
                                          button.height() // 2).name().lower()
    proof = {
        'status': 'passed', 'qtMajor': 6,
        'widgetClass': button.metaObject().className(),
        'objectName': button.objectName(),
        'size': [button.width(), button.height()],
        'pressedPixelChanges': changed_pixels(normal, pressed),
        'releasePixelChanges': changed_pixels(normal, released),
        'disabledPixelChanges': changed_pixels(released, disabled),
        'normalFace': {'expectedKdeRoleDerived': expected_normal,
                       'actualPixel': normal_sample},
        'disabledFace': {'expectedKdeRoleDerived': expected_disabled,
                         'actualPixel': disabled_sample},
        'clickCount': len(clicks),
        'screenshots': {
            'normal': str(args.output / 'qt6-push-normal.png'),
            'pressed': str(args.output / 'qt6-push-pressed.png'),
            'disabled': str(args.output / 'qt6-push-disabled.png')},
    }
    assert proof['widgetClass'] == 'QPushButton'
    assert proof['pressedPixelChanges'] > 0
    assert proof['releasePixelChanges'] == 0
    assert proof['disabledPixelChanges'] > 0
    assert proof['normalFace']['actualPixel'] == expected_normal
    assert proof['disabledFace']['actualPixel'] == expected_disabled
    assert proof['clickCount'] == 1
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))
    button.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
