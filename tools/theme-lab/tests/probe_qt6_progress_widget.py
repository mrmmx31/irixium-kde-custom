#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise a native Qt6 progress bar and its palette state transitions."""
import argparse
import json
from pathlib import Path

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget

from qt6_progress_widget import RecipeProgressBar


def image_difference(left, right):
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
    progress = RecipeProgressBar()
    progress.setObjectName('domainosRecipeProgress')
    progress.setRange(0, 100)
    progress.setValue(43)
    progress.setFormat('%p%')
    layout.addWidget(progress)
    peer = QLineEdit()
    layout.addWidget(peer)
    host.installEventFilter(progress)
    host.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    host.resize(420, 90)
    host.show()
    host.activateWindow()
    app.setActiveWindow(host)
    app.processEvents()
    peer.setFocus()
    app.processEvents()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)

    def capture(state):
        path = args.output / f'qt6-progress-{state}.png'
        saved = progress.grab().save(str(path), 'PNG')
        return path, saved

    initial_text = progress.text()
    normal, normal_saved = capture('normal')
    progress.setValue(70)
    app.processEvents()
    changed_text = progress.text()
    changed, changed_saved = capture('changed')
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowDeactivate))
    app.processEvents()
    backdrop, backdrop_saved = capture('backdrop')
    backdrop_applied = progress.property('domainosState') == 'backdrop'
    QApplication.sendEvent(host, QEvent(QEvent.Type.WindowActivate))
    app.processEvents()
    progress.setEnabled(False)
    app.processEvents()
    disabled, disabled_saved = capture('disabled')
    disabled_applied = progress.property('domainosState') == 'disabled'

    from PyQt6.QtGui import QImage
    images = {name: QImage(str(path)) for name, path in (
        ('normal', normal), ('changed', changed), ('backdrop', backdrop),
        ('disabled', disabled))}
    proof = {
        'status': 'passed', 'widgetClass': progress.metaObject().className(),
        'objectName': progress.objectName(), 'range': [progress.minimum(), progress.maximum()],
        'initialValue': 43, 'changedValue': progress.value(),
        'initialText': initial_text, 'changedText': changed_text,
        'nativeValueAndTextWorked': initial_text == '43%' and changed_text == '70%',
        'fillValueChangedPixels': image_difference(images['normal'], images['changed']),
        'backdropApplied': backdrop_applied, 'disabledApplied': disabled_applied,
        'screenshotsSaved': all((normal_saved, changed_saved, backdrop_saved, disabled_saved)),
        'screenshots': {'normal': str(normal), 'changed': str(changed),
                        'backdrop': str(backdrop), 'disabled': str(disabled)},
    }
    if not (proof['nativeValueAndTextWorked'] and proof['fillValueChangedPixels'] > 0
            and proof['backdropApplied'] and proof['disabledApplied']
            and proof['screenshotsSaved']):
        proof['status'] = 'failed'
    print(json.dumps(proof, ensure_ascii=False), flush=True)
    return 0 if proof['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
