#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a real Qt5 QFrame with generated KDE-role border and surface."""
import argparse
import json
from pathlib import Path
import re

from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout


def changed_pixels(left, right):
    a = left.convertToFormat(QImage.Format_RGBA8888)
    b = right.convertToFormat(QImage.Format_RGBA8888)
    if a.size() != b.size():
        return -1
    return sum(a.pixel(x, y) != b.pixel(x, y)
               for y in range(a.height()) for x in range(a.width()))


def css_color(stylesheet, selector, property_name):
    match = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', stylesheet, re.S)
    if not match:
        raise AssertionError(f'Missing QSS block: {selector}')
    value = re.search(re.escape(property_name) + r'\s*:\s*(#[0-9a-fA-F]{6})', match.group(1))
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
    frame = QFrame()
    frame.setObjectName('domainosRecipeFrame')
    frame.setFrameShape(QFrame.Panel)
    frame.setFrameShadow(QFrame.Sunken)
    frame.setLineWidth(2)
    layout = QVBoxLayout(frame)
    layout.addWidget(QLabel('Conteúdo'))
    frame.setStyleSheet(stylesheet)
    frame.resize(220, 96)
    frame.show()
    frame.activateWindow()
    app.processEvents()
    normal = frame.grab().toImage()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    normal.save(str(args.output / 'qt5-frame-normal.png'), 'PNG')
    normal_expected = css_color(stylesheet, 'QFrame#domainosRecipeFrame', 'background-color')
    normal_actual = normal.pixelColor(frame.width() // 2, frame.height() // 2).name().lower()
    frame.setEnabled(False)
    app.processEvents()
    disabled = frame.grab().toImage()
    disabled.save(str(args.output / 'qt5-frame-disabled.png'), 'PNG')
    disabled_expected = css_color(stylesheet, 'QFrame#domainosRecipeFrame:disabled', 'background-color')
    disabled_actual = disabled.pixelColor(frame.width() // 2, frame.height() // 2).name().lower()
    result = {
        'status': 'passed', 'qtMajor': 5,
        'widgetClass': frame.metaObject().className(),
        'frameShape': int(frame.frameShape()), 'frameShadow': int(frame.frameShadow()),
        'lineWidth': frame.lineWidth(), 'size': [frame.width(), frame.height()],
        'normalFace': {'expectedKdeRoleDerived': normal_expected, 'actualPixel': normal_actual},
        'disabledFace': {'expectedKdeRoleDerived': disabled_expected, 'actualPixel': disabled_actual},
        'disabledPixelChanges': changed_pixels(normal, disabled),
        'screenshots': {'normal': str(args.output / 'qt5-frame-normal.png'),
                        'disabled': str(args.output / 'qt5-frame-disabled.png')},
    }
    assert result['widgetClass'] == 'QFrame'
    assert frame.frameShape() == QFrame.Panel and frame.frameShadow() == QFrame.Sunken
    assert result['normalFace']['actualPixel'] == normal_expected
    assert result['disabledFace']['actualPixel'] == disabled_expected
    assert result['disabledPixelChanges'] > 0
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    frame.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
