#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a real Qt6 tree/list, selection, scrollbars and palette states."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QAbstractItemView, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout

from qt6_scale_widget import WindowBackdropTracker


def changed_pixels(left, right):
    if left.size() != right.size():
        return max(left.width() * left.height(), right.width() * right.height())
    return sum(left.pixel(x, y) != right.pixel(x, y)
               for y in range(left.height()) for x in range(left.width()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    app = QApplication([])
    host = QWidget()
    layout = QVBoxLayout(host)
    listing = QTreeWidget()
    listing.setObjectName('domainosRecipeList')
    listing.setHeaderHidden(True)
    listing.setRootIsDecorated(False)
    listing.setItemsExpandable(False)
    listing.setUniformRowHeights(True)
    listing.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    listing.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    listing.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    listing.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    for index in range(40):
        listing.addTopLevelItem(QTreeWidgetItem([
            f'Item {index + 1:02d} — selectable row — long content for horizontal scrolling']))
    listing.setColumnWidth(0, 620)
    listing.verticalScrollBar().setObjectName('domainosScrollBarVertical')
    listing.horizontalScrollBar().setObjectName('domainosScrollBarHorizontal')
    layout.addWidget(listing)
    tracker = WindowBackdropTracker(host, listing)
    host.installEventFilter(tracker)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.resize(440, 300)
    host.show()
    host.activateWindow()
    app.setActiveWindow(host)
    listing.setCurrentItem(listing.topLevelItem(0))
    listing.topLevelItem(0).setSelected(True)
    listing.setFocus()
    app.processEvents()

    initial_index = listing.indexOfTopLevelItem(listing.currentItem())
    target = listing.topLevelItem(2)
    QTest.mouseClick(listing.viewport(), Qt.MouseButton.LeftButton,
                     pos=listing.visualItemRect(target).center())
    app.processEvents()
    after_mouse = listing.indexOfTopLevelItem(listing.currentItem())
    QTest.keyClick(listing, Qt.Key.Key_Down)
    app.processEvents()
    after_key = listing.indexOfTopLevelItem(listing.currentItem())
    selected_item_flag = listing.currentItem().isSelected()
    selected_rows = len(listing.selectionModel().selectedRows())
    selected = listing.grab().toImage()
    listing.clearSelection()
    listing.setCurrentItem(None)
    app.processEvents()
    unselected = listing.grab().toImage()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)

    def save(image, state):
        path = args.output / f'qt6-list-{state}.png'
        return path, image.save(str(path), 'PNG')

    selected_path, selected_saved = save(selected, 'selected')
    unselected_path, unselected_saved = save(unselected, 'unselected')
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowDeactivate))
    app.processEvents()
    backdrop_path, backdrop_saved = save(listing.grab().toImage(), 'backdrop')
    backdrop_applied = tracker.backdrop and listing.property('domainosBackdrop') is True
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowActivate))
    app.processEvents()
    listing.setEnabled(False)
    app.processEvents()
    disabled_path, disabled_saved = save(listing.grab().toImage(), 'disabled')

    vertical, horizontal = listing.verticalScrollBar(), listing.horizontalScrollBar()
    result = {
        'status': 'passed', 'widgetClass': listing.metaObject().className(),
        'objectName': listing.objectName(), 'rowCount': listing.topLevelItemCount(),
        'selectionMode': 'single row', 'initialSelectedRow': initial_index,
        'selectedAfterMouse': after_mouse, 'selectedAfterKeyboard': after_key,
        'selectedItem': selected_item_flag, 'selectedRows': selected_rows,
        'backdropApplied': backdrop_applied, 'disabled': not listing.isEnabled(),
        'selectionChangesPixels': changed_pixels(selected, unselected),
        'verticalScrollbar': {'visible': vertical.isVisible(), 'maximum': vertical.maximum(),
                              'objectName': vertical.objectName()},
        'horizontalScrollbar': {'visible': horizontal.isVisible(), 'maximum': horizontal.maximum(),
                                'objectName': horizontal.objectName()},
        'screenshotsSaved': all((selected_saved, unselected_saved,
                                 backdrop_saved, disabled_saved)),
        'screenshots': {'selected': str(selected_path), 'unselected': str(unselected_path),
                        'backdrop': str(backdrop_path), 'disabled': str(disabled_path)},
    }
    result['status'] = 'passed' if (
        initial_index == 0 and after_mouse == 2 and after_key == 3
        and selected_item_flag and selected_rows == 1
        and result['selectionChangesPixels'] > 0 and backdrop_applied
        and result['disabled'] and result['screenshotsSaved']
        and vertical.isVisible() and vertical.maximum() > 0
        and horizontal.isVisible() and horizontal.maximum() > 0
    ) else 'failed'
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
