#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the real Qt6 arrow button, held/released states and palette pixels."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qt6_arrow_widget import RecipeArrowButton
from qt6_scale_widget import WindowBackdropTracker


def masked_pixel_difference(left, right):
    if left.size() != right.size():
        return max(left.width() * left.height(), right.width() * right.height())
    differences = 0
    for y in range(left.height()):
        for x in range(left.width()):
            expected = right.pixelColor(x, y)
            if expected.alpha() == 0:
                continue
            actual = left.pixelColor(x, y)
            if (actual.red(), actual.green(), actual.blue()) != (
                    expected.red(), expected.green(), expected.blue()):
                differences += 1
    return differences


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    app = QApplication([])
    host = QWidget()
    layout = QVBoxLayout(host)
    button = RecipeArrowButton(args.assets, 2)
    button.setObjectName('domainosRecipeArrow')
    layout.addWidget(button)
    tracker = WindowBackdropTracker(host, button)
    host.installEventFilter(tracker)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.resize(90, 70)
    host.show()
    host.activateWindow()
    app.setActiveWindow(host)
    app.processEvents()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)

    def capture(state):
        path = args.output / f'qt6-arrow-{state}.png'
        saved = button.grab().save(str(path), 'PNG')
        return path, saved

    normal, normal_saved = capture('normal')
    QTest.mousePress(button, Qt.MouseButton.LeftButton, pos=button.rect().center())
    app.processEvents()
    pressed, pressed_saved = capture('pressed')
    pressed_held = button.isDown() and button.arrow_state() == 'pressed'
    QTest.mouseRelease(button, Qt.MouseButton.LeftButton, pos=button.rect().center())
    app.processEvents()
    released, released_saved = capture('released')
    click_count = []
    button.clicked.connect(lambda: click_count.append(True))
    QTest.mouseClick(button, Qt.MouseButton.LeftButton, pos=button.rect().center())
    app.processEvents()
    clicked = len(click_count) == 1

    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowDeactivate))
    app.processEvents()
    backdrop, backdrop_saved = capture('backdrop')
    backdrop_applied = tracker.backdrop and button.arrow_state() == 'backdrop'
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowActivate))
    app.processEvents()
    button.setEnabled(False)
    app.processEvents()
    disabled, disabled_saved = capture('disabled')
    disabled_applied = button.arrow_state() == 'disabled'

    from PyQt6.QtGui import QImage
    glyph = QImage(str(args.assets / 'standalone-arrow-down-normal.png'))
    held_glyph = QImage(str(args.assets / 'standalone-arrow-down-pressed.png'))
    released_glyph = QImage(str(args.assets / 'standalone-arrow-down-normal.png'))
    disabled_glyph = QImage(str(args.assets / 'standalone-arrow-down-disabled.png'))
    def centered_crop(path):
        image = QImage(str(path))
        x = (image.width() - glyph.width()) // 2
        y = (image.height() - glyph.height()) // 2
        return image.copy(x, y, glyph.width(), glyph.height())

    proof = {
        'status': 'passed', 'widgetClass': button.metaObject().className(),
        'objectName': button.objectName(), 'size': [button.width(), button.height()],
        'glyphSize': [glyph.width(), glyph.height()], 'clicked': clicked,
        'pressedWhileHeld': pressed_held, 'backdropApplied': backdrop_applied,
        'disabledApplied': disabled_applied,
        'normalAssetPixelDifferences': masked_pixel_difference(centered_crop(normal), glyph),
        'pressedAssetPixelDifferences': masked_pixel_difference(centered_crop(pressed), held_glyph),
        'releasedAssetPixelDifferences': masked_pixel_difference(centered_crop(released), released_glyph),
        'disabledAssetPixelDifferences': masked_pixel_difference(centered_crop(disabled), disabled_glyph),
        'screenshots': {'normal': str(normal), 'pressed': str(pressed),
                        'released': str(released), 'backdrop': str(backdrop),
                        'disabled': str(disabled)},
        'screenshotsSaved': all((normal_saved, pressed_saved, released_saved,
                                 backdrop_saved, disabled_saved)),
    }
    if not (proof['clicked'] and proof['pressedWhileHeld'] and proof['backdropApplied']
            and proof['disabledApplied'] and proof['screenshotsSaved']
            and all(proof[key] == 0 for key in (
                'normalAssetPixelDifferences', 'pressedAssetPixelDifferences',
                'releasedAssetPixelDifferences', 'disabledAssetPixelDifferences'))):
        proof['status'] = 'failed'
    print(json.dumps(proof, ensure_ascii=False), flush=True)
    return 0 if proof['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
