# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic input to gallery windows; no cursor warping or control-state forcing.

Qt modules are injected to support PyQt6 and PySide6. This is test machinery,
never a desktop event filter or an installed QStyle. All observers return False.
"""
from __future__ import annotations


def interior_walk(x: int, y: int, width: int, height: int) -> list[tuple[int, int]]:
    """A short actual pointer approach within an action, ending at its centre.

Multiple distinct moves avoid depending on QCursor::pos(), which a Wayland
compositor need not allow a test to change. No private QMenu state is changed.
"""
    if width < 3 or height < 3:
        raise ValueError('Área da ação muito pequena para um percurso confiável.')
    cx, cy = x + (width - 1) // 2, y + (height - 1) // 2
    dx = min(3, (width - 1) // 2)
    return [(cx + (-dx if i % 2 == 0 else dx), cy) for i in range(10)] + [(cx, cy)]


class GalleryInput:
    def __init__(self, C, W, T, app):
        self.C, self.W, self.T, self.app = C, W, T, app
        self.records = []

    @staticmethod
    def _rect(r):
        return [r.x(), r.y(), r.width(), r.height()]

    def _ready(self, widget):
        self.app.processEvents()
        top = widget.window()
        handle = top.windowHandle()
        if not widget.isVisible() or handle is None:
            raise ValueError('Janela de ensaio não está visível ou não possui QWindow.')
        if not self.T.QTest.qWaitForWindowExposed(handle, 2000):
            raise ValueError('A janela de ensaio não ficou exposta; entrada não executada.')
        return top, handle

    def _watch(self, widget):
        C = self.C
        rows = []
        kinds = {C.QEvent.Type.MouseMove:'move', C.QEvent.Type.MouseButtonPress:'press',
                 C.QEvent.Type.MouseButtonRelease:'release'}
        class Observer(C.QObject):
            def eventFilter(self, watched, event):
                if watched is widget and event.type() in kinds:
                    pt = event.position().toPoint()
                    rows.append({'event':kinds[event.type()], 'x':pt.x(), 'y':pt.y()})
                return False
        observer = Observer()
        widget.installEventFilter(observer)
        return observer, rows

    def toggle(self, widget):
        C, W, T = self.C, self.W, self.T
        is_radio = isinstance(widget, W.QRadioButton)
        opt = W.QStyleOptionButton()
        opt.initFrom(widget)
        opt.text = widget.text()
        sub = W.QStyle.SubElement
        indicator = widget.style().subElementRect(
            sub.SE_RadioButtonIndicator if is_radio else sub.SE_CheckBoxIndicator, opt, widget)
        click_rect = widget.style().subElementRect(
            sub.SE_RadioButtonClickRect if is_radio else sub.SE_CheckBoxClickRect, opt, widget)
        point = indicator.center()
        if not indicator.isValid() or not widget.rect().contains(point) or not click_rect.contains(point):
            raise ValueError('Indicador fora da área clicável; teste não deve usar o centro do widget.')
        top, window = self._ready(widget)
        scene_point = widget.mapTo(top, point)
        observer, events = self._watch(widget)
        signals = []
        def pressed(): signals.append('pressed')
        def released(): signals.append('released')
        def clicked(_checked=False): signals.append('clicked')
        widget.pressed.connect(pressed);widget.released.connect(released);widget.clicked.connect(clicked)
        row = {'kind':'radio' if is_radio else 'checkbox', 'enabled':widget.isEnabled(),
               'widget_rect':self._rect(widget.rect()), 'indicator_rect':self._rect(indicator),
               'click_rect':self._rect(click_rect), 'point':[point.x(), point.y()],
               'before':widget.isChecked(), 'events':events, 'signals':signals}
        try:
            T.QTest.mouseMove(window, scene_point, 10);self.app.processEvents()
            T.QTest.mousePress(window,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,scene_point)
            try:
                self.app.processEvents();T.QTest.qWait(20)
                row['held_down']=widget.isDown()
            finally:
                T.QTest.mouseRelease(window,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,scene_point)
            self.app.processEvents();T.QTest.qWait(20)
            row['after']=widget.isChecked();row['released_down']=widget.isDown()
            row['valid_target']=any(e['event']=='press' and click_rect.contains(C.QPoint(e['x'],e['y'])) for e in events)
        finally:
            widget.removeEventFilter(observer)
            widget.pressed.disconnect(pressed);widget.released.disconnect(released);widget.clicked.disconnect(clicked)
        self.records.append(row)
        return row

    def menu_action(self, menu, action):
        C, T = self.C, self.T
        row={'kind':'menu', 'action_text':action.text(), 'enabled':action.isEnabled(),
             'events':[], 'stage':'readiness', 'valid_target':False,
             'visible_before':menu.isVisible(), 'window_exists_before':menu.window().windowHandle() is not None}
        self.records.append(row)
        observer=None
        try:
            top, window = self._ready(menu)
            rect = menu.actionGeometry(action).intersected(menu.rect())
            row['action_rect']=self._rect(rect)
            if not rect.isValid() or menu.actionAt(rect.center()) != action:
                raise ValueError('Ação não localizada na janela do menu; teste inconclusivo.')
            observer, events = self._watch(menu)
            row['events']=events;row['stage']='pointer_approach'
            for x,y in interior_walk(rect.x(),rect.y(),rect.width(),rect.height()):
                # QWindow overload generates a move instead of QCursor::setPos.
                T.QTest.mouseMove(window,menu.mapTo(top,C.QPoint(x,y)),5)
                self.app.processEvents()
            if not menu.isVisible():raise ValueError('Menu deixou de estar visível durante a aproximação.')
            rect=menu.actionGeometry(action).intersected(menu.rect());point=rect.center()
            if menu.actionAt(point) != action:
                raise ValueError('A ação mudou de posição durante a aproximação.')
            row['move_events_received']=sum(e['event']=='move' for e in events)
            row['active_before_press']=menu.activeAction().text() if menu.activeAction() else None
            scene_point=menu.mapTo(top,point);row['stage']='click'
            # Keep this a native event sequence, not QAction.trigger or setActiveAction.
            T.QTest.mouseClick(window,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,scene_point,20)
            self.app.processEvents();T.QTest.qWait(30)
            row['valid_target']=any(e['event']=='press' and rect.contains(C.QPoint(e['x'],e['y'])) for e in events)
            row['popup_visible_after']=menu.isVisible();row['stage']='completed'
        except (ValueError, RuntimeError) as exc:
            row['error']=str(exc);row['popup_visible_after']=menu.isVisible()
            raise
        finally:
            if observer is not None:menu.removeEventFilter(observer)
        return row
