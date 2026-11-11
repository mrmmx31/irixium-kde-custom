#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise one real Qt6 slider using a generated KDE-role recipe."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt, QPoint
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QSlider, QWidget, QVBoxLayout

from qt6_scale_widget import WindowBackdropTracker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--orientation', choices=('horizontal', 'vertical'), default='horizontal')
    args = parser.parse_args()
    app = QApplication([])
    host = QWidget()
    layout = QVBoxLayout(host)
    orientation = Qt.Orientation.Horizontal if args.orientation == 'horizontal' else Qt.Orientation.Vertical
    slider = QSlider(orientation)
    slider.setObjectName('domainosRecipeScaleHorizontal' if args.orientation == 'horizontal'
                         else 'domainosRecipeScaleVertical')
    slider.setRange(0, 100)
    slider.setSingleStep(5)
    slider.setPageStep(20)
    slider.setValue(43)
    if args.orientation == 'horizontal':
        slider.setMinimumWidth(260)
    else:
        slider.setMinimumHeight(260)
    layout.addWidget(slider)
    backdrop_tracker = WindowBackdropTracker(host, slider)
    host.installEventFilter(backdrop_tracker)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.show()
    host.activateWindow()
    app.setActiveWindow(host)
    app.processEvents()

    from PyQt6.QtWidgets import QStyle, QStyleOptionSlider
    option = QStyleOptionSlider()
    slider.initStyleOption(option)
    groove = slider.style().subControlRect(QStyle.ComplexControl.CC_Slider, option,
                                           QStyle.SubControl.SC_SliderGroove, slider)
    handle = slider.style().subControlRect(QStyle.ComplexControl.CC_Slider, option,
                                           QStyle.SubControl.SC_SliderHandle, slider)
    assert groove.isValid() and slider.rect().contains(groove), groove
    assert handle.isValid() and slider.rect().contains(handle), handle

    initial = slider.value()
    target = (QPoint(groove.right() - 2, groove.center().y()) if args.orientation == 'horizontal'
              else QPoint(groove.center().x(), groove.top() + 2))
    QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=target)
    app.processEvents()
    mouse_value = slider.value()
    before_key = slider.value()
    QTest.keyClick(slider, Qt.Key.Key_Left if args.orientation == 'horizontal' else Qt.Key.Key_Down)
    app.processEvents()
    key_value = slider.value()
    slider.setValue(43)
    app.processEvents()
    normal_image = host.grab()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    prefix = 'qt6-scale-' + args.orientation
    normal_path = args.output / f'{prefix}.png'
    normal_saved = slider.grab().save(str(normal_path), 'PNG')

    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowDeactivate))
    app.processEvents()
    backdrop_path = args.output / f'{prefix}-backdrop.png'
    backdrop_saved = slider.grab().save(str(backdrop_path), 'PNG')
    backdrop_applied = backdrop_tracker.backdrop and slider.property('domainosBackdrop') is True
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowActivate))
    app.processEvents()

    slider.setFocus()
    QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=handle.center())
    app.processEvents()
    pressed = slider.isSliderDown()
    QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=handle.center())
    app.processEvents()
    released = not slider.isSliderDown()

    slider.setEnabled(False)
    app.processEvents()
    disabled_path = args.output / f'{prefix}-disabled.png'
    disabled_saved = slider.grab().save(str(disabled_path), 'PNG')
    proof = {
        'status': 'passed',
        'widgetClass': slider.metaObject().className(),
        'objectName': slider.objectName(),
        'orientation': 'horizontal' if slider.orientation() == Qt.Orientation.Horizontal else 'vertical',
        'range': [slider.minimum(), slider.maximum()],
        'initialValue': initial,
        'valueAfterMouse': mouse_value,
        'valueBeforeKey': before_key,
        'valueAfterKey': key_value,
        'mouseChangedValue': mouse_value != initial,
        'keyboardChangedValue': key_value != before_key,
        'pressedWhileHeld': pressed,
        'releasedAfterPointerUp': released,
        'backdropPropertyApplied': backdrop_applied,
        'grooveRect': list(groove.getRect()),
        'handleRect': list(handle.getRect()),
        'normalScreenshotSaved': normal_saved,
        'disabledScreenshotSaved': disabled_saved,
        'backdropScreenshotSaved': backdrop_saved,
        'screenshots': {'normal': str(normal_path), 'backdrop': str(backdrop_path),
                        'disabled': str(disabled_path)},
    }
    assert proof['widgetClass'] == 'QSlider'
    assert proof['orientation'] == args.orientation
    assert proof['mouseChangedValue'] and proof['keyboardChangedValue']
    assert proof['pressedWhileHeld'] and proof['releasedAfterPointerUp']
    assert proof['backdropPropertyApplied'] and backdrop_saved
    assert normal_saved and disabled_saved
    host.close()
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
