#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a real Qt6 QTextEdit, its editing actions and KDE-role palette."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QTextEdit, QWidget, QVBoxLayout

from qt6_scale_widget import WindowBackdropTracker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    app = QApplication([])
    host = QWidget()
    layout = QVBoxLayout(host)
    editor = QTextEdit()
    editor.setObjectName('domainosRecipeText')
    peer = QTextEdit()
    peer.setObjectName('peerEditor')
    layout.addWidget(editor)
    layout.addWidget(peer)
    original = 'Primeira linha: ação — 東京\nSegunda linha\nTerceira linha'
    editor.setPlainText(original)
    tracker = WindowBackdropTracker(host, editor)
    host.installEventFilter(tracker)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.resize(520, 350)
    host.show()
    host.activateWindow()
    app.setActiveWindow(host)
    app.processEvents()

    editor.setFocus()
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClicks(editor, ' primeiro')
    QTest.keyClick(editor, Qt.Key.Key_Return)
    QTest.keyClicks(editor, ' segundo')
    app.processEvents()
    edited = editor.toPlainText()

    def key_until(target, key, modifiers, limit=16):
        count = 0
        while editor.toPlainText() != target and count < limit:
            QTest.keyClick(editor, key, modifiers)
            app.processEvents()
            count += 1
        return count

    undo_steps = key_until(original, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    multi_step_undo = undo_steps >= 2 and editor.toPlainText() == original
    redo_y_steps = key_until(edited, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    redo_y = redo_y_steps >= 2 and editor.toPlainText() == edited
    key_until(original, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    redo_shift_steps = key_until(
        edited, Qt.Key.Key_Z,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    redo_shift_z = redo_shift_steps >= 2 and editor.toPlainText() == edited

    editor.selectAll()
    QTest.keyClick(editor, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    app.processEvents()
    clipboard_text = app.clipboard().text()
    peer.setFocus()
    app.processEvents()
    QTest.keyClick(peer, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    app.processEvents()
    copied = peer.toPlainText()

    editor.setFocus()
    editor.selectAll()
    QTest.keyClick(editor, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)
    cut_empty = editor.toPlainText() == ''
    QTest.keyClick(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    pasted = editor.toPlainText()
    QTest.keyClick(editor, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    selected_all = editor.textCursor().hasSelection() and editor.textCursor().selectedText().replace('\u2029', '\n') == pasted

    menu = editor.createStandardContextMenu()
    action_names = {action.text().split('\t', 1)[0].replace('&', '').replace('…', '').strip().lower()
                    for action in menu.actions() if not action.isSeparator()}
    expected_actions = {'undo', 'redo', 'cut', 'copy', 'paste', 'select all'}
    native_actions = expected_actions.issubset(action_names)
    menu.deleteLater()

    editor.setPlainText(edited)
    app.processEvents()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    normal_path = args.output / 'qt6-text-normal.png'
    normal_saved = editor.grab().save(str(normal_path), 'PNG')
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowDeactivate))
    app.processEvents()
    backdrop_path = args.output / 'qt6-text-backdrop.png'
    backdrop_saved = editor.grab().save(str(backdrop_path), 'PNG')
    backdrop_applied = tracker.backdrop and editor.property('domainosBackdrop') is True
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowActivate))
    app.processEvents()
    editor.setEnabled(False)
    app.processEvents()
    disabled_path = args.output / 'qt6-text-disabled.png'
    disabled_saved = editor.grab().save(str(disabled_path), 'PNG')

    proof = {
        'status': 'passed', 'widgetClass': editor.metaObject().className(),
        'objectName': editor.objectName(), 'utf8Original': original,
        'nativeEditWorked': edited != original,
        'undoSteps': undo_steps, 'redoCtrlYSteps': redo_y_steps,
        'redoCtrlShiftZSteps': redo_shift_steps,
        'multiStepUndoWorked': multi_step_undo,
        'redoCtrlYWorked': redo_y,
        'redoCtrlShiftZWorked': redo_shift_z,
        'copyWorked': clipboard_text == edited and copied == edited, 'cutWorked': cut_empty,
        'pasteWorked': pasted == edited, 'selectAllWorked': selected_all,
        'nativeEditActionsPresent': native_actions,
        'contextActions': sorted(action_names),
        'backdropPropertyApplied': backdrop_applied,
        'normalScreenshotSaved': normal_saved,
        'backdropScreenshotSaved': backdrop_saved,
        'disabledScreenshotSaved': disabled_saved,
        'screenshots': {'normal': str(normal_path), 'backdrop': str(backdrop_path),
                        'disabled': str(disabled_path)},
    }
    required = ('nativeEditWorked', 'multiStepUndoWorked', 'redoCtrlYWorked',
                'redoCtrlShiftZWorked', 'copyWorked', 'cutWorked', 'pasteWorked',
                'selectAllWorked', 'nativeEditActionsPresent', 'backdropPropertyApplied',
                'normalScreenshotSaved', 'backdropScreenshotSaved', 'disabledScreenshotSaved')
    assert proof['widgetClass'] == 'QTextEdit'
    for key in required:
        assert proof[key], (key, proof)
    host.close()
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
