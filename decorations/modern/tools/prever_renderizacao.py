#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the actual Surface/ModernButton with KSvg, without KWin or installation.

Default: interactive preview. --testar: real QML loading, referenced states,
pointer input and screenshots in a NEW --saida directory. No KDE settings write.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--testar', action='store_true')
    parser.add_argument('--saida', type=Path)
    args = parser.parse_args()
    if args.testar and args.saida is None:
        parser.error('--testar exige --saida em pasta nova, fora do clone.')
    try:
        from PyQt6.QtCore import QObject, QPoint, QUrl, Qt
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtQuick import QQuickView
        from PyQt6.QtTest import QTest
        binding = 'PyQt6'
    except ImportError:
        try:
            from PySide6.QtCore import QObject, QPoint, QUrl, Qt
            from PySide6.QtGui import QGuiApplication
            from PySide6.QtQuick import QQuickView
            from PySide6.QtTest import QTest
            binding = 'PySide6'
        except ImportError:
            print('Não executado: precisa de PyQt6/PySide6 QtQuick e do módulo QML org.kde.ksvg.', file=sys.stderr)
            return 77
    if args.saida:
        args.saida = args.saida.expanduser().absolute()
        if args.saida.exists() or ROOT.parent in args.saida.parents:
            parser.error('A saída deve ser nova e ficar fora do clone.')
    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName('IrixiumModernRenderPreview')
    view = QQuickView()
    view.setTitle('Irixium Moderno — galeria de renderização')
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setSource(QUrl.fromLocalFile(str(ROOT / 'tests/render-preview.qml')))
    if view.status() == QQuickView.Status.Error:
        for error in view.errors(): print(error.toString(), file=sys.stderr)
        return 1
    view.show()
    if not args.testar:
        return app.exec()
    QTest.qWait(400)
    results = []
    def check(name, condition): results.append({'check': name, 'passed': bool(condition)})
    root = view.rootObject()
    active = root.findChild(QObject, 'previewActive')
    check('active frame present', active is not None)
    for name in ('previewActive', 'previewInactive', 'previewMaximized', 'previewDisabled'):
        surface = root.findChild(QObject, name)
        check(name + ' frame artwork exists', surface is not None and surface.property('artworkValid'))
        if not surface: continue
        check(name + ' no close button', surface.findChild(QObject, 'irixiumModernClose') is None)
        for suffix in ('Menu', 'Minimize', 'Maximize'):
            button = surface.findChild(QObject, 'irixiumModern' + suffix)
            check(name + ' ' + suffix + ' selected asset exists', button is not None and button.property('artworkValid'))
            if button and suffix != 'Menu':
                element = button.property('renderedElement')
                check(name + ' ' + suffix + ' not full atlas', bool(element) and str(element).endswith('-center'))
    if active:
        button = active.findChild(QObject, 'irixiumModernMinimize')
        if button:
            # The local demo frame is at (16,40); button coordinates are relative to it.
            point = QPoint(16 + int(button.property('x')) + 11, 40 + int(button.property('y')) + 11)
            QTest.mouseMove(view, point); QTest.qWait(80)
            check('hover chooses hover layer', button.property('renderedElement') == 'hover-center')
            QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
            check('pressed layer before release', button.property('renderedElement') == 'pressed-center')
            QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
            check('released removes pressed state', not button.property('pressed'))
        menu = active.findChild(QObject, 'irixiumModernMenu')
        if menu:
            point = QPoint(16 + int(menu.property('x')) + 11, 40 + int(menu.property('y')) + 11)
            old = root.property('calls')
            QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
            check('left menu waits for double-click', root.property('calls') == old)
            QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
            check('menu release still waits', root.property('calls') == old)
            QTest.qWait(app.styleHints().mouseDoubleClickInterval() + 100)
            check('single menu click emits once after native interval', root.property('calls') == old + 1)
    # Move the pointer away from button hover before the comparison image.
    QTest.mouseMove(view, QPoint(440, 120)); QTest.qWait(120)
    if args.saida:
        args.saida.mkdir(parents=True)
        image = view.grabWindow()
        check('screenshot saved', not image.isNull() and image.save(str(args.saida / 'renderizacao.png')))
    check('no QML warnings', not warnings)
    report = {'binding': binding, 'platform': app.platformName(), 'scope': 'Actual QML + KSvg in a standalone preview; not a KWin integration test',
              'checks': results, 'warnings': warnings,
              'status': 'passed' if all(x['passed'] for x in results) else 'failed'}
    if args.saida:
        (args.saida / 'renderizacao.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    view.close()
    return 0 if report['status'] == 'passed' else 1

if __name__ == '__main__':
    try: sys.exit(main())
    except (OSError, ValueError, TypeError) as e:
        print('ERRO:', e, file=sys.stderr); sys.exit(1)
