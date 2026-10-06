#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt mouse events for both packages; native popups/closing stay KWin's responsibility."""
def main():
    from pathlib import Path
    from PyQt6.QtCore import QPoint, QUrl, Qt
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQuick import QQuickView
    from PyQt6.QtTest import QTest

    ROOT=Path(__file__).resolve().parents[2]
    app=QGuiApplication([])
    for folder,point in [('classic-rewrite-rc1',QPoint(20,20)),('modern-rewrite-rc1',QPoint(26,17))]:
        v=QQuickView();v.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        warnings=[];v.engine().warnings.connect(lambda errors:warnings.extend(e.toString() for e in errors))
        v.resize(800,400);v.setSource(QUrl.fromLocalFile(str(ROOT/folder/'package/contents/ui/Surface.qml')))
        assert v.status()!=QQuickView.Status.Error,[e.toString() for e in v.errors()]
        root=v.rootObject();calls=[]
        root.menuRequested.connect(lambda button:calls.append('menu'))
        root.closeRequested.connect(lambda:calls.append('close'))
        v.show();QTest.qWait(100)
        interval=app.styleHints().mouseDoubleClickInterval()
        QTest.mouseClick(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
        assert calls==[],(folder,calls)
        QTest.qWait(interval+100)
        assert calls==['menu'],(folder,calls)
        calls.clear()
        QTest.mouseClick(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
        QTest.mouseDClick(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point,10)
        QTest.mouseRelease(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
        assert calls==['close'],(folder,calls)
        QTest.qWait(interval+100)
        assert calls==['close'],(folder,calls)
        calls.clear()
        QTest.mouseClick(v,Qt.MouseButton.RightButton,Qt.KeyboardModifier.NoModifier,point)
        assert calls==['menu'],(folder,calls)
        assert not warnings,warnings
        print(folder+': clique simples no intervalo Qt, duplo clique fecha sem menu posterior, direito imediato; sem avisos QML.')
        v.close();v.deleteLater();app.processEvents()


if __name__ == "__main__":
    main()
