#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt mouse events for both packages; native popups/closing stay KWin's responsibility."""
def main():
    from pathlib import Path
    from PyQt6.QtCore import QPoint, QPointF, QEvent, QUrl, Qt
    from PyQt6.QtGui import QGuiApplication, QMouseEvent
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
        # Focus is independent of button availability. Cover a window that
        # remains inactive and focus changes between the two native clicks.
        for first_active, second_active in ((True, True), (False, False),
                                            (False, True), (True, False)):
            calls.clear()
            root.setProperty('activeWindow', first_active)
            QTest.mouseClick(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
            root.setProperty('activeWindow', second_active)
            # Deliver only the second native press, classified by Qt as double.
            # QTest.mouseDClick synthesizes a full sequence of its own, which
            # would hide a lost first click when testing focus transitions.
            QTest.qWait(10)
            QTest.mousePress(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
            event=QMouseEvent(QEvent.Type.MouseButtonDblClick, QPointF(point),
                             QPointF(v.mapToGlobal(point)), Qt.MouseButton.LeftButton,
                             Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QGuiApplication.sendEvent(v,event)
            QTest.mouseRelease(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
            scenario=(folder, first_active, second_active, calls)
            assert calls==['close'],scenario
            assert root.property('activeWindow')==second_active,scenario
            QTest.qWait(interval+100)
            assert calls==['close'],scenario
        calls.clear()
        QTest.mouseClick(v,Qt.MouseButton.RightButton,Qt.KeyboardModifier.NoModifier,point)
        assert calls==['menu'],(folder,calls)
        assert not warnings,warnings
        print(folder+': clique simples no intervalo Qt; duplo clique fecha ativa/inativa e durante mudanças de foco, sem menu posterior; direito imediato; sem avisos QML.')
        v.close();v.deleteLater();app.processEvents()


if __name__ == "__main__":
    main()
