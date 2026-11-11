#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a real Qt5 QTreeWidget with the generated KDE-role list recipe."""
import argparse
import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QAbstractItemView, QTreeWidget, QTreeWidgetItem


def changed_pixels(left, right):
    a = left.convertToFormat(QImage.Format_RGBA8888)
    b = right.convertToFormat(QImage.Format_RGBA8888)
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
    window = QTreeWidget()
    window.setObjectName('domainosRecipeList')
    window.setHeaderHidden(True)
    window.setRootIsDecorated(False)
    window.setItemsExpandable(False)
    window.setUniformRowHeights(True)
    window.setSelectionMode(QAbstractItemView.SingleSelection)
    window.setSelectionBehavior(QAbstractItemView.SelectRows)
    window.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    window.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    for index in range(40):
        window.addTopLevelItem(QTreeWidgetItem(
            [f'Item {index + 1:02d} — selectable row — long content for horizontal scrolling']))
    window.setColumnWidth(0, 620)
    window.verticalScrollBar().setObjectName('domainosScrollBarVertical')
    window.horizontalScrollBar().setObjectName('domainosScrollBarHorizontal')
    window.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    window.resize(420, 260)
    window.setCurrentItem(window.topLevelItem(0))
    window.topLevelItem(0).setSelected(True)
    window.show()
    app.processEvents()

    initial_index = window.indexOfTopLevelItem(window.currentItem())
    window.setFocus()
    app.processEvents()
    focused = window.hasFocus()
    target = window.topLevelItem(2)
    QTest.mouseClick(window.viewport(), Qt.LeftButton,
                     pos=window.visualItemRect(target).center())
    app.processEvents()
    selected_after_mouse = window.indexOfTopLevelItem(window.currentItem())
    QTest.keyClick(window, Qt.Key_Down)
    app.processEvents()
    selected_after_keyboard = window.indexOfTopLevelItem(window.currentItem())
    selected_item_flag = window.currentItem().isSelected()
    selected_rows = len(window.selectionModel().selectedRows())
    selected_image = window.grab().toImage()
    selected_capture_index = window.indexOfTopLevelItem(window.currentItem())
    selected_capture_center = window.visualItemRect(window.currentItem()).center()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    selected_image.save(str(args.output / 'qt5-list-selected.png'), 'PNG')
    window.clearSelection()
    window.setCurrentItem(None)
    app.processEvents()
    selected_after_clear = len(window.selectionModel().selectedRows())
    current_selected_after_clear = bool(window.currentItem() and
                                        window.currentItem().isSelected())
    unselected_image = window.grab().toImage()
    unselected_image.save(str(args.output / 'qt5-list-unselected.png'), 'PNG')
    window.setEnabled(False)
    app.processEvents()
    disabled_image = window.grab().toImage()
    disabled_image.save(str(args.output / 'qt5-list-disabled.png'), 'PNG')

    vertical = window.verticalScrollBar()
    horizontal = window.horizontalScrollBar()
    result = {
        'status': 'passed',
        'qtMajor': 5,
        'widgetClass': window.metaObject().className(),
        'objectName': window.objectName(),
        'rowCount': window.topLevelItemCount(),
        'selectionMode': 'single',
        'initialSelectedRow': initial_index,
        'focused': focused,
        'selectedAfterMouse': selected_after_mouse,
        'selectedAfterKeyboard': selected_after_keyboard,
        'selectedItemFlag': selected_item_flag,
        'selectedRows': selected_rows,
        'selectedCaptureIndex': selected_capture_index,
        'selectedCaptureCenter': [selected_capture_center.x(), selected_capture_center.y()],
        'selectedRowsAfterClear': selected_after_clear,
        'currentSelectedAfterClear': current_selected_after_clear,
        'verticalScrollbar': {'visible': vertical.isVisible(), 'maximum': vertical.maximum(),
                              'objectName': vertical.objectName()},
        'horizontalScrollbar': {'visible': horizontal.isVisible(), 'maximum': horizontal.maximum(),
                                'objectName': horizontal.objectName()},
        'selectionChangesPixels': changed_pixels(selected_image, unselected_image),
        'disabledChangesPixels': changed_pixels(unselected_image, disabled_image),
        'disabled': not window.isEnabled(),
        'screenshots': {
            'selected': str(args.output / 'qt5-list-selected.png'),
            'unselected': str(args.output / 'qt5-list-unselected.png'),
            'disabled': str(args.output / 'qt5-list-disabled.png')},
    }
    assert result['widgetClass'] == 'QTreeWidget'
    assert initial_index == 0 and focused
    assert selected_after_mouse == 2 and selected_after_keyboard == 3
    assert selected_item_flag and selected_rows == 1
    assert vertical.isVisible() and vertical.maximum() > 0
    assert horizontal.isVisible() and horizontal.maximum() > 0
    assert result['selectionChangesPixels'] > 0
    assert result['disabledChangesPixels'] > 0
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    window.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
