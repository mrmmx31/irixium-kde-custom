#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise real Qt6 spin boxes, stepping, text editing and clipboard keys."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDoubleSpinBox, QLineEdit, QSpinBox, QWidget, QVBoxLayout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    app = QApplication([])
    host = QWidget()
    layout = QVBoxLayout(host)
    integer = QSpinBox()
    integer.setObjectName('domainosRecipeSpinBox')
    integer.setRange(-99, 999)
    integer.setValue(42)
    decimal = QDoubleSpinBox()
    decimal.setObjectName('domainosRecipeDoubleSpinBox')
    decimal.setRange(-99, 999)
    decimal.setDecimals(2)
    decimal.setSingleStep(0.1)
    decimal.setValue(10.4)
    peer = QLineEdit()
    layout.addWidget(integer)
    layout.addWidget(decimal)
    layout.addWidget(peer)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.show()
    app.processEvents()

    integer.setFocus()
    QTest.keyClick(integer, Qt.Key.Key_Up)
    stepped_up = integer.value()
    QTest.keyClick(integer, Qt.Key.Key_Down)
    stepped_back = integer.value()
    QTest.keyClick(decimal, Qt.Key.Key_Up)
    decimal_stepped = decimal.value()

    editor = integer.lineEdit()
    editor.setFocus()
    editor.selectAll()
    QTest.keyClicks(editor, '84')
    typed = editor.text()
    QTest.keyClick(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    undo_text = editor.text()
    QTest.keyClick(editor, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    redo_y_text = editor.text()
    QTest.keyClick(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(editor, Qt.Key.Key_Z,
                   Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    redo_shift_z_text = editor.text()
    editor.selectAll()
    QTest.keyClick(editor, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(peer, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    copied_text = peer.text()
    editor.selectAll()
    QTest.keyClick(editor, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)
    cut_text = editor.text()
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    pasted_text = editor.text()
    QTest.keyClick(editor, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    selected_all = editor.hasSelectedText() and editor.selectedText() == pasted_text
    QTest.keyClick(editor, Qt.Key.Key_Return)
    committed_value = integer.value()

    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    screenshot = args.output / 'qt6-spinboxes.png'
    saved = host.grab().save(str(screenshot), 'PNG')
    integer.setEnabled(False)
    decimal.setEnabled(False)
    app.processEvents()
    disabled_saved = host.grab().save(str(args.output / 'qt6-spinboxes-disabled.png'), 'PNG')
    proof = {
        'status': 'passed',
        'widgetClasses': [integer.metaObject().className(), decimal.metaObject().className()],
        'objectNames': [integer.objectName(), decimal.objectName()],
        'keyboardStepUp': stepped_up,
        'keyboardStepDown': stepped_back,
        'doubleKeyboardStepUp': decimal_stepped,
        'utf8EditBuffer': typed,
        'undoWorked': undo_text == '42',
        'redoCtrlYWorked': redo_y_text == '84',
        'redoCtrlShiftZWorked': redo_shift_z_text == '84',
        'copyWorked': copied_text == '84',
        'cutWorked': cut_text == '',
        'pasteWorked': pasted_text == '84',
        'selectAllWorked': selected_all,
        'committedValue': committed_value,
        'normalScreenshotSaved': saved,
        'disabledScreenshotSaved': disabled_saved,
        'screenshots': {'normal': str(screenshot),
                        'disabled': str(args.output / 'qt6-spinboxes-disabled.png')},
    }
    assert proof['widgetClasses'] == ['QSpinBox', 'QDoubleSpinBox']
    assert (stepped_up, stepped_back, decimal_stepped) == (43, 42, 10.5)
    for operation in ('undoWorked', 'redoCtrlYWorked', 'redoCtrlShiftZWorked',
                      'copyWorked', 'cutWorked', 'pasteWorked', 'selectAllWorked'):
        assert proof[operation], operation
    assert committed_value == 84
    assert saved and disabled_saved
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))
    host.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
