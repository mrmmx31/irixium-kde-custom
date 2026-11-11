#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a real Qt6 combo and its popup without replacing Qt interaction."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QComboBox


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    app = QApplication([])
    combo = QComboBox()
    combo.setObjectName('domainosRecipeCombo')
    combo.addItems(['Classic', 'DomainOS SR10.4', 'A long selectable menu option'])
    combo.view().setObjectName('domainosRecipeComboPopup')
    combo.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    combo.resize(280, combo.sizeHint().height())
    combo.show()
    app.processEvents()
    before = combo.currentIndex()
    combo.setFocus()
    QTest.keyClick(combo, Qt.Key.Key_Down)
    QTest.keyClick(combo, Qt.Key.Key_Return)
    app.processEvents()
    keyboard_index = combo.currentIndex()
    combo.setCurrentIndex(0)
    combo.showPopup()
    app.processEvents()
    popup = combo.view()
    target = popup.model().index(1, 0)
    popup.setCurrentIndex(target)
    rect = popup.visualRect(target)
    QTest.mouseClick(popup.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    app.processEvents()
    pointer_index = combo.currentIndex()
    popup_visible_after_choice = popup.isVisible()
    combo.setCurrentIndex(0)
    app.processEvents()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    closed_path = args.output / 'qt6-combo-closed.png'
    closed_image = combo.grab().toImage()
    closed_saved = closed_image.save(str(closed_path), 'PNG')
    middle = closed_image.width() // 2
    center_content_uniform = all(
        closed_image.pixel(x, y) == closed_image.pixel(middle, y)
        for y in range(closed_image.height())
        for x in range(max(1, middle - 8), min(closed_image.width() - 1, middle + 9)))
    combo.showPopup()
    app.processEvents()
    popup_path = args.output / 'qt6-combo-popup.png'
    popup_saved = popup.viewport().grab().save(str(popup_path), 'PNG')
    popup.hide()
    proof = {
        'status': 'passed',
        'widgetClass': combo.metaObject().className(),
        'popupClass': popup.metaObject().className(),
        'objectName': combo.objectName(),
        'popupObjectName': popup.objectName(),
        'count': combo.count(),
        'initialIndex': before,
        'keyboardSelectionIndex': keyboard_index,
        'pointerSelectionIndex': pointer_index,
        'popupClosedAfterPointerSelection': not popup_visible_after_choice,
        'centerContentUniform': center_content_uniform,
        'closedScreenshotSaved': closed_saved,
        'popupScreenshotSaved': popup_saved,
        'screenshots': {'closed': str(closed_path), 'popup': str(popup_path)},
    }
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))
    assert proof['widgetClass'] == 'QComboBox'
    assert proof['popupObjectName'] == 'domainosRecipeComboPopup'
    assert proof['count'] == 3
    assert proof['keyboardSelectionIndex'] == 1
    assert proof['pointerSelectionIndex'] == 1
    assert proof['popupClosedAfterPointerSelection']
    assert proof['centerContentUniform']
    assert proof['closedScreenshotSaved'] and proof['popupScreenshotSaved']
    combo.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
