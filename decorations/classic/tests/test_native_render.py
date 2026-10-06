#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual Qt Quick frame versus the preserved pixel painter. Run in a private D-Bus session."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    from PyQt6.QtCore import QUrl, Qt
    from PyQt6.QtGui import QColor, QGuiApplication, QImage, QPainter, QSurfaceFormat
    from PyQt6.QtQuick import QQuickView
    from PyQt6.QtTest import QTest
    root = Path(__file__).resolve().parents[1]
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(fmt)
    app = QGuiApplication([])
    view = QQuickView()
    view.setColor(QColor('#ff00ff'))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    warnings = []
    view.engine().warnings.connect(lambda items: warnings.extend(e.toString() for e in items))
    view.setSource(QUrl.fromLocalFile(str(root/'package/contents/ui/Surface.qml')))
    if view.status() == QQuickView.Status.Error:
        raise RuntimeError([e.toString() for e in view.errors()])
    surface = view.rootObject()
    view.resize(591,240)
    view.show()
    cases = [(w,h,s,active,maximized) for w,h in [(591,240),(590,199),(100,80),(99,36)]
             for s in (1,2,3) for active,maximized in [(True,False),(False,False),(True,True)]]
    for w,h,s,active,maximized in cases:
        surface.setProperty('pixelScale', s)
        surface.setProperty('activeWindow', active)
        surface.setProperty('maximizedWindow', maximized)
        view.resize(w*s,h*s)
        QTest.qWait(50)
        actual = view.grabWindow().convertToFormat(QImage.Format.Format_RGBA8888)
        commands = json.loads(subprocess.check_output(['node',str(root/'tests/render.js'),str(w*s),str(h*s),str(s),
                           'active' if active else 'inactive','max' if maximized else 'normal'],text=True))
        expected = QImage(w*s,h*s,QImage.Format.Format_RGBA8888)
        expected.fill(QColor('#ff00ff'))
        painter = QPainter(expected)
        for x,y,width,height,color in commands['rectangles']:
            painter.fillRect(x,y,width,height,QColor(color))
        painter.end()
        def raw(image):
            ptr = image.constBits(); ptr.setsize(image.sizeInBytes()); return bytes(ptr)
        if raw(actual) != raw(expected):
            folder = Path(tempfile.mkdtemp(prefix='irix-pixel-diff-'))
            actual.save(str(folder/'actual.png')); expected.save(str(folder/'expected.png'))
            raise AssertionError(f'Pixels divergentes em {(w,h,s,active,maximized)}: {folder}')
    if warnings:
        raise AssertionError(warnings)
    print(f'{len(cases)} renderizações Qt Quick idênticas ao painter original; sem avisos QML.')
    view.close()


if __name__ == '__main__':
    main()
