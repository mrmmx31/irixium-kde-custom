#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt mouse events for both packages; native popups/closing stay KWin's responsibility."""
def main():
    import os
    from pathlib import Path
    from PyQt6.QtCore import QPoint, QPointF, QRectF, QEvent, QUrl, Qt
    from PyQt6.QtGui import QGuiApplication, QMouseEvent
    from PyQt6.QtQuick import QQuickItem, QQuickView
    from PyQt6.QtTest import QTest

    ROOT=Path(__file__).resolve().parents[3]
    app=QGuiApplication([])
    evidence=Path(os.environ['IRIX_INPUT_EVIDENCE']) if os.environ.get('IRIX_INPUT_EVIDENCE') else None
    if evidence: evidence.mkdir(parents=True,exist_ok=True)
    for folder,point in [('decorations/classic',QPoint(20,20)),('decorations/modern',QPoint(26,17))]:
        v=QQuickView();v.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        warnings=[];v.engine().warnings.connect(lambda errors:warnings.extend(e.toString() for e in errors))
        v.resize(800,400);v.setSource(QUrl.fromLocalFile(str(ROOT/folder/'package/contents/ui/Surface.qml')))
        assert v.status()!=QQuickView.Status.Error,[e.toString() for e in v.errors()]
        root=v.rootObject();calls=[]
        root.menuRequested.connect(lambda button:calls.append('menu'))
        root.closeRequested.connect(lambda:calls.append('close'))
        root.minimizeRequested.connect(lambda:calls.append('minimize'))
        root.maximizeRequested.connect(lambda button:calls.append('maximize'))
        v.show();QTest.qWait(100)
        interval=app.styleHints().mouseDoubleClickInterval()
        modern=Path(folder).name=='modern'
        prefix='irixiumModern' if modern else 'irix'
        pressure='pressed' if modern else 'down'
        menu=root.findChild(QQuickItem,prefix+'Menu')
        if modern: assert root.findChild(QQuickItem,'irixiumModernClose') is None
        for suffix in ('Minimize','Maximize'):
            button=root.findChild(QQuickItem,prefix+suffix)
            assert button is not None,(folder,suffix)
            pos=QPoint(int(button.x()+button.width()/2),int(button.y()+button.height()/2))
            calls.clear()
            QTest.mouseMove(v,pos);QTest.qWait(30)
            before=v.grabWindow()
            QTest.mousePress(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,pos)
            assert button.property(pressure),(folder,suffix,'no pressed state')
            assert calls==[],(folder,suffix,'action before relief',calls)
            QTest.qWait(30)  # Test-only: let the native renderer produce the held frame.
            pressed=v.grabWindow()
            rect=button.mapRectToScene(QRectF(0,0,button.width(),button.height())).toRect()
            assert before.copy(rect)!=pressed.copy(rect),(folder,suffix,'no visual relief')
            if evidence:
                before.save(str(evidence/(folder.replace('/','-')+'-'+suffix+'-normal.png')))
                pressed.save(str(evidence/(folder.replace('/','-')+'-'+suffix+'-pressionado.png')))
            QTest.mouseRelease(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,pos)
            assert calls==[suffix.lower()],(folder,suffix,calls)
            assert not button.property(pressure),(folder,suffix,'stuck relief')
        calls.clear()
        QTest.mousePress(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
        assert menu.property(pressure) and calls==[],(folder,'menu relief')
        QTest.qWait(30)
        if evidence:v.grabWindow().save(str(evidence/(folder.replace('/','-')+'-Menu-pressionado.png')))
        QTest.mouseRelease(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
        QTest.qWait(interval+100)
        assert calls==['menu'],(folder,calls)
        calls.clear()
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
            assert calls==[] and menu.property(pressure),(folder,'second press relief',calls)
            QTest.qWait(30)
            if evidence:v.grabWindow().save(str(evidence/(folder.replace('/','-')+'-Duplo-pressionado.png')))
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
        print(folder+': clique simples no intervalo Qt; duplo clique fecha ativa/inativa e durante mudanças de foco, sem menu posterior; ações na soltura com relevo visível; direito sem espera adicional; sem avisos QML.')
        v.close();v.deleteLater();app.processEvents()


if __name__ == "__main__":
    main()
