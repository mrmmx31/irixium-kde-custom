#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prove Qt6 QLineEdit retains its standard UTF-8 editing and clipboard keys."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLineEdit, QWidget, QVBoxLayout


def color(image, x, y):
    return image.pixelColor(x, y).name()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stylesheet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    app = QApplication([])
    host = QWidget()
    layout = QVBoxLayout(host)
    entry = QLineEdit('UTF-8: ação — 東京')
    entry.setObjectName('domainosRecipeEntry')
    peer = QLineEdit()
    layout.addWidget(entry)
    layout.addWidget(peer)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.show()
    app.processEvents()

    original = entry.text()
    entry.setFocus()
    entry.setCursorPosition(len(original))
    QTest.keyClicks(entry, ' + edit')
    edited = entry.text()
    QTest.keyClick(entry, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    undo_text = entry.text()
    QTest.keyClick(entry, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    redo_y_text = entry.text()
    QTest.keyClick(entry, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(entry, Qt.Key.Key_Z,
                   Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    redo_shift_z_text = entry.text()

    entry.selectAll()
    QTest.keyClick(entry, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(peer, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    copied_text = peer.text()

    entry.selectAll()
    QTest.keyClick(entry, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)
    cut_text = entry.text()
    entry.setFocus()
    QTest.keyClick(entry, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    pasted_text = entry.text()

    entry.setFocus()
    QTest.keyClick(entry, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    selected_all = entry.hasSelectedText() and entry.selectedText() == pasted_text
    face = entry.grab().toImage()
    image_path = args.output / 'qt6-entry-focused.png'
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    saved = face.save(str(image_path), 'PNG')
    face_pixel = color(face, 2, face.height() // 2)

    entry.setEnabled(False)
    app.processEvents()
    disabled = entry.grab().toImage()
    disabled_pixel = color(disabled, 2, disabled.height() // 2)

    proof = {
        'status': 'passed',
        'widgetClass': entry.metaObject().className(),
        'objectName': entry.objectName(),
        'utf8Original': original,
        'nativeEditWorked': edited == original + ' + edit',
        'undoWorked': undo_text == original,
        'redoCtrlYWorked': redo_y_text == edited,
        'redoCtrlShiftZWorked': redo_shift_z_text == edited,
        'copyWorked': copied_text == edited,
        'cutWorked': cut_text == '',
        'pasteWorked': pasted_text == edited,
        'selectAllWorked': selected_all,
        'focusedScreenshotSaved': saved,
        'focusedScreenshot': str(image_path),
        'normalFacePixel': face_pixel,
        'disabledFacePixel': disabled_pixel,
    }
    assert proof['widgetClass'] == 'QLineEdit'
    assert proof['nativeEditWorked'] and proof['undoWorked']
    assert proof['redoCtrlYWorked'] and proof['redoCtrlShiftZWorked']
    assert proof['copyWorked'] and proof['cutWorked'] and proof['pasteWorked']
    assert proof['selectAllWorked'] and proof['focusedScreenshotSaved']
    assert face.size() == disabled.size()
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True))
    host.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
