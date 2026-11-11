#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a real Qt6 QFrame with KDE-role surface and relief states."""
import argparse
import json
from pathlib import Path
import re

from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout


def changed_pixels(left, right):
    a = left.convertToFormat(QImage.Format.Format_RGBA8888)
    b = right.convertToFormat(QImage.Format.Format_RGBA8888)
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


def repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.repaint()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stylesheet = args.stylesheet.read_text(encoding='utf-8')
    app = QApplication([])
    frame = QFrame()
    frame.setObjectName('domainosRecipeFrame')
    frame.setFrameShape(QFrame.Shape.Panel)
    frame.setFrameShadow(QFrame.Shadow.Sunken)
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
    normal.save(str(args.output / 'qt6-frame-normal.png'), 'PNG')
    normal_expected = css_color(stylesheet, 'QFrame#domainosRecipeFrame', 'background-color')
    normal_actual = normal.pixelColor(12, 12).name().lower()

    frame.setProperty('domainosBackdrop', True)
    repolish(frame)
    app.processEvents()
    backdrop = frame.grab().toImage()
    backdrop.save(str(args.output / 'qt6-frame-backdrop.png'), 'PNG')
    backdrop_expected = css_color(
        stylesheet, 'QFrame#domainosRecipeFrame[domainosBackdrop="true"]', 'background-color')
    backdrop_actual = backdrop.pixelColor(12, 12).name().lower()

    frame.setProperty('domainosBackdrop', False)
    frame.setEnabled(False)
    repolish(frame)
    app.processEvents()
    disabled = frame.grab().toImage()
    disabled.save(str(args.output / 'qt6-frame-disabled.png'), 'PNG')
    disabled_expected = css_color(
        stylesheet, 'QFrame#domainosRecipeFrame:disabled', 'background-color')
    disabled_actual = disabled.pixelColor(12, 12).name().lower()

    result = {
        'status': 'passed', 'qtMajor': 6,
        'widgetClass': frame.metaObject().className(),
        'frameShape': frame.frameShape().value,
        'frameShadow': frame.frameShadow().value,
        'lineWidth': frame.lineWidth(), 'size': [frame.width(), frame.height()],
        'normalFace': {'expectedKdeRoleDerived': normal_expected, 'actualPixel': normal_actual},
        'backdropFace': {'expectedKdeRoleDerived': backdrop_expected, 'actualPixel': backdrop_actual},
        'disabledFace': {'expectedKdeRoleDerived': disabled_expected, 'actualPixel': disabled_actual},
        'statePixelChanges': {'backdrop': changed_pixels(normal, backdrop),
                              'disabled': changed_pixels(normal, disabled)},
        'screenshots': {'normal': str(args.output / 'qt6-frame-normal.png'),
                        'backdrop': str(args.output / 'qt6-frame-backdrop.png'),
                        'disabled': str(args.output / 'qt6-frame-disabled.png')},
    }
    assert result['widgetClass'] == 'QFrame'
    assert frame.frameShape() == QFrame.Shape.Panel and frame.frameShadow() == QFrame.Shadow.Sunken
    assert result['normalFace']['actualPixel'] == normal_expected
    assert result['backdropFace']['actualPixel'] == backdrop_expected
    assert result['disabledFace']['actualPixel'] == disabled_expected
    assert result['statePixelChanges']['disabled'] > 0
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    frame.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
