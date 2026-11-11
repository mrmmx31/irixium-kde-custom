# SPDX-License-Identifier: GPL-3.0-or-later
"""Inspect the production gallery inside its real, required private guards."""
import argparse
import json
from pathlib import Path
import sys
import subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'plasma/tests/galerias-nativas'))
from qt6_demo import main, private_guards
private_guards()  # No guard replacement; must pass before importing Qt.
parser=argparse.ArgumentParser();parser.add_argument('--major',type=int,choices=(5,6),required=True)
args=parser.parse_args()
if args.major==6:
    from PyQt6 import QtWidgets as W
    from PyQt6.QtGui import QAction
    from PyQt6.QtCore import QTimer, QPoint, Qt
    from PyQt6.QtTest import QTest
else:
    from PyQt5 import QtWidgets as W
    from PyQt5.QtWidgets import QAction
    from PyQt5.QtCore import QTimer, QPoint, Qt
    from PyQt5.QtTest import QTest
native_exec=W.QApplication.exec


def inspect_exec(app):
    assert app.platformName()=='xcb'
    window=next(w for w in app.topLevelWidgets() if isinstance(w,W.QMainWindow))
    widgets=window.findChildren(W.QWidget)
    buttons=[w for w in widgets if isinstance(w,W.QAbstractButton)]
    assert len(buttons)>=30 and all(w.toolTip() for w in buttons)
    assert all(m.toolTipsVisible() for m in window.findChildren(W.QMenu))
    actions=[a for a in window.findChildren(QAction) if not a.isSeparator()]
    assert actions and all(a.toolTip().strip() for a in actions), 'menu action without a hint'
    spin=window.findChild(W.QSpinBox)
    decimal=window.findChild(W.QDoubleSpinBox)
    combo=window.findChild(W.QComboBox)
    integer_spins=window.findChildren(W.QSpinBox)
    decimal_spins=window.findChildren(W.QDoubleSpinBox)
    combos=window.findChildren(W.QComboBox)
    sliders=window.findChildren(W.QSlider)
    assert decimal and combo and integer_spins and decimal_spins and combos and len(sliders)>=2
    assert '-99' in spin.toolTip() and '999' in spin.toolTip() and 'sem unidade' in spin.toolTip()
    assert 'sem unidade' in decimal.toolTip() and 'passo' in decimal.toolTip()
    assert 'lista' in combo.toolTip() and 'tema do desktop' in combo.toolTip()
    assert all('sem unidade' in w.toolTip() and 'mínimo' in w.toolTip() and 'passo' in w.toolTip()
               for w in integer_spins+decimal_spins)
    assert all('lista' in w.toolTip() for w in combos)
    assert all('sem unidade' in slider.toolTip() and 'passo' in slider.toolTip()
               for slider in sliders)
    line_name='themeLineEdit' if args.major==6 else 'qt5ThemeLineEdit'
    line_edit=window.findChild(W.QLineEdit,line_name)
    text_edit=window.findChild(W.QTextEdit)
    line_edits=window.findChildren(W.QLineEdit)
    text_edits=window.findChildren(W.QTextEdit)+window.findChildren(W.QPlainTextEdit)
    assert line_edit and 'Undo/Redo' in line_edit.toolTip() and 'clipboard' in line_edit.toolTip()
    assert text_edit and 'Undo/Redo' in text_edit.toolTip() and 'clipboard' in text_edit.toolTip()
    assert all(w.toolTip() for w in line_edits+text_edits)
    scrollbars=window.findChildren(W.QScrollBar)
    assert scrollbars and all('Barra ' in bar.toolTip() for bar in scrollbars)
    table=window.findChild(W.QTableWidget)
    assert 'Cabeçalho' in table.horizontalHeader().toolTip()
    name='themePushButton' if args.major==6 else 'qt5ThemePushButton'
    button=window.findChild(W.QPushButton,name)
    button.click()
    assert any(label.text()=='Push button clicked' for label in window.findChildren(W.QLabel))
    dialog_results=[]
    def inspect_dialog(expected):
        def inspect():
            dialog=app.activeModalWidget()
            assert isinstance(dialog,expected), 'expected native Qt modal dialog'
            controls=dialog.findChildren(W.QAbstractButton)
            assert controls and all(c.toolTip() for c in controls)
            editors=dialog.findChildren(W.QLineEdit)
            assert all(e.toolTip() for e in editors)
            for box in dialog.findChildren(W.QDialogButtonBox):
                for child in box.buttons():
                    role=box.buttonRole(child)
                    value=role.value if hasattr(role,'value') else int(role)
                    if value==0:assert 'Confirma' in child.toolTip() or 'Fecha' in child.toolTip()
                    if value==1:assert 'Cancela' in child.toolTip()
            if expected is W.QFileDialog:
                assert 'Nome do arquivo' in dialog.findChild(W.QLineEdit,'fileNameEdit').toolTip()
            dialog_results.append({'type':expected.__name__,'buttons':len(controls),
                                   'line_editors':len(editors),'hints_present':True})
            dialog.reject()
        return inspect
    # Real production callbacks enter native modal event loops. Cancel only;
    # no files are opened and no personal/application configuration is touched.
    QTimer.singleShot(500,inspect_dialog(W.QFileDialog))
    next(b for b in buttons if b.text()=='Open QFileDialog').click()
    assert any(label.text()=='Private file dialog completed' for label in window.findChildren(W.QLabel))
    QTimer.singleShot(500,inspect_dialog(W.QMessageBox))
    next(a for a in window.findChildren(__import__(
        'PyQt6.QtGui' if args.major==6 else 'PyQt5.QtWidgets',fromlist=['QAction']).QAction)
         if a.text()=='About this private demo').trigger()
    assert len(dialog_results)==2
    QTest.qWait(250)
    # Xvfb has no window manager: give only this private window X input focus.
    subprocess.run(['xdotool','windowfocus',str(int(window.winId()))],check=True)
    QTest.qWait(100)
    assert window.isActiveWindow(), 'private fixture did not acquire input focus'
    subprocess.run(['xdotool','mousemove','0','0'],check=True)
    QTest.qWait(700)
    origin=button.mapToGlobal(QPoint(0,0))
    control=(origin.x(),origin.y(),button.width(),button.height())
    subprocess.run(['xdotool','mousemove',str(origin.x()+button.width()//2),
                    str(origin.y()+button.height()//2)],check=True)
    QTest.qWait(100)
    assert not W.QToolTip.isVisible(), 'tooltip appears without cold hover delay'
    for _ in range(20):
        QTest.qWait(100)
        if W.QToolTip.isVisible():break
    assert W.QToolTip.isVisible(), 'native tooltip never appeared'
    assert W.QToolTip.text()==button.toolTip()
    tips=[w for w in app.topLevelWidgets() if w.isVisible() and w.inherits('QTipLabel')]
    assert len(tips)==1
    tip=tips[0];rect=tip.frameGeometry()
    assert not rect.intersects(button.rect().translated(origin)), 'tooltip covers control'
    assert app.primaryScreen().availableGeometry().contains(rect), 'tooltip outside screen'
    QTest.qWait(400)
    assert W.QToolTip.isVisible() and tip.frameGeometry()==rect, 'tooltip oscillation'
    subprocess.run(['xdotool','mousemove','0','0'],check=True)
    QTest.qWait(700)
    assert not W.QToolTip.isVisible(), 'tooltip remains after leaving'
    button.click()
    assert any(label.text()=='Push button clicked' for label in window.findChildren(W.QLabel))
    def hover_control(widget, name):
        origin=widget.mapToGlobal(QPoint(0,0))
        center=QPoint(origin.x()+widget.width()//2,origin.y()+widget.height()//2)
        W.QToolTip.hideText()
        subprocess.run(['xdotool','mousemove','0','0'],check=True)
        QTest.qWait(700)
        assert not W.QToolTip.isVisible(), f'{name} prior hint did not close before hover'
        subprocess.run(['xdotool','mousemove',str(center.x()),str(center.y())],check=True)
        for _ in range(25):
            QTest.qWait(100)
            if W.QToolTip.isVisible():break
        assert W.QToolTip.isVisible(), f'{name} native hint did not appear'
        assert W.QToolTip.text()==widget.toolTip(), f'{name} hint text mismatch'
        labels=[w for w in app.topLevelWidgets() if w.isVisible() and w.inherits('QTipLabel')]
        assert len(labels)==1, f'{name} produced {len(labels)} visible native tips'
        rect=labels[0].frameGeometry()
        control_rect=widget.rect().translated(origin)
        assert not rect.intersects(control_rect), (
            f'{name} hint covers its control: tooltip={rect.getRect()} control={control_rect.getRect()}')
        assert app.primaryScreen().availableGeometry().contains(rect), f'{name} hint leaves the screen'
        QTest.qWait(400)
        assert W.QToolTip.isVisible() and labels[0].frameGeometry()==rect, f'{name} hint oscillated'
        subprocess.run(['xdotool','mousemove','0','0'],check=True)
        QTest.qWait(700)
        assert not W.QToolTip.isVisible(), f'{name} hint remained after pointer leave'
        return {'text':widget.toolTip(),'no_overlap':True,'inside_screen':True,
                'stable_ms':400,'closed_after_leave':True,
                'control':[control_rect.x(),control_rect.y(),control_rect.width(),control_rect.height()],
                'tooltip':[rect.x(),rect.y(),rect.width(),rect.height()]}
    additional_hover={
        'combo':hover_control(combo,'combo'),
        'integer_spin':hover_control(spin,'integer spin'),
        'decimal_spin':hover_control(decimal,'decimal spin'),
        'horizontal_slider':hover_control(next(s for s in sliders if s.orientation()==
            (Qt.Orientation.Horizontal if args.major==6 else Qt.Horizontal)),'horizontal slider'),
        'vertical_slider':hover_control(next(s for s in sliders if s.orientation()==
            (Qt.Orientation.Vertical if args.major==6 else Qt.Vertical)),'vertical slider'),
    }
    def hover_menu_action(menu, action, index):
        W.QToolTip.hideText()
        menu.hide()
        subprocess.run(['xdotool','mousemove','0','0'],check=True)
        QTest.qWait(700)
        assert not W.QToolTip.isVisible(), f'menu action {index} prior hint did not close'
        menu.popup(window.mapToGlobal(QPoint(8,40)))
        QTest.qWait(150)
        local=menu.actionGeometry(action)
        origin=menu.mapToGlobal(local.topLeft())
        row=local.translated(origin-local.topLeft())
        center=row.center()
        subprocess.run(['xdotool','mousemove',str(center.x()),str(center.y())],check=True)
        for _ in range(30):
            QTest.qWait(100)
            if W.QToolTip.isVisible():break
        assert W.QToolTip.isVisible(), f'menu action {index} hint did not appear'
        assert W.QToolTip.text()==action.toolTip(), f'menu action {index} hint text mismatch'
        tips=[w for w in app.topLevelWidgets() if w.isVisible() and w.inherits('QTipLabel')]
        assert len(tips)==1, f'menu action {index} produced {len(tips)} tips'
        tip=tips[0].frameGeometry()
        menu_rect=menu.frameGeometry()
        assert not tip.intersects(row), f'menu action {index} hint covers its row'
        assert not tip.intersects(menu_rect), f'menu action {index} hint covers another menu option'
        assert app.primaryScreen().availableGeometry().contains(tip), (
            f'menu action {index} hint outside screen')
        QTest.qWait(400)
        assert W.QToolTip.isVisible() and tips[0].frameGeometry()==tip, (
            f'menu action {index} hint oscillated')
        subprocess.run(['xdotool','mousemove','0','0'],check=True)
        QTest.qWait(700)
        assert not W.QToolTip.isVisible(), f'menu action {index} hint remained after leave'
        menu.hide()
        return {'text':action.text(),'hint':action.toolTip(),'stable_ms':400,
                'no_overlap':True,'no_menu_overlap':True,'inside_screen':True,'closed_after_leave':True,
                'menu':[menu_rect.x(),menu_rect.y(),menu_rect.width(),menu_rect.height()],
                'action':[row.x(),row.y(),row.width(),row.height()],
                'tooltip':[tip.x(),tip.y(),tip.width(),tip.height()]}

    def hover_submenu_parent(menu, action, index):
        status=window.findChild(W.QLabel,'qtGalleryStatus')
        assert status is not None and window._domainos_submenu_help_strip
        W.QToolTip.hideText();menu.hide()
        subprocess.run(['xdotool','mousemove','0','0'],check=True)
        QTest.qWait(700)
        baseline=status.text()
        menu.popup(window.mapToGlobal(QPoint(8,40)))
        QTest.qWait(150)
        local=menu.actionGeometry(action)
        origin=menu.mapToGlobal(local.topLeft())
        row=local.translated(origin-local.topLeft())
        center=row.center()
        subprocess.run(['xdotool','mousemove',str(center.x()),str(center.y())],check=True)
        QTest.qWait(250)
        assert status.text()==baseline, f'submenu action {index} help appeared before its delay'
        QTest.qWait(350)
        expected=action.statusTip() or action.toolTip()
        assert status.text()==expected, f'submenu action {index} delayed status hint missing'
        assert not W.QToolTip.isVisible(), f'submenu action {index} spawned an overlapping native tooltip'
        child=action.menu()
        assert child is not None
        if not child.isVisible():
            child.popup(QPoint(menu.geometry().right(),row.y()))
            QTest.qWait(250)
        assert child.isVisible(), f'submenu action {index} child menu did not open'
        status_rect=status.rect().translated(status.mapToGlobal(QPoint(0,0)))
        assert not status_rect.intersects(row), 'status help covers the submenu opener'
        QTest.qWait(400)
        assert status.text()==expected and not W.QToolTip.isVisible(), (
            f'submenu action {index} status hint was unstable while child menu stayed open')
        app.primaryScreen().grabWindow(0).save('/home/domainos-test/qtwidgets-proof/submenu-help-strip.png')
        child_actions=[a for a in child.actions() if not a.isSeparator()]
        if child_actions:
            child_row=child.actionGeometry(child_actions[0])
            child_center=child.mapToGlobal(child_row.center())
            subprocess.run(['xdotool','mousemove',str(child_center.x()),str(child_center.y())],check=True)
            QTest.qWait(900)
            assert status.text()==baseline, 'parent help remained after moving into a child action'
            assert W.QToolTip.isVisible() and W.QToolTip.text()==child_actions[0].toolTip(), (
                'child action native hint did not replace the parent context')
        subprocess.run(['xdotool','mousemove','0','0'],check=True)
        QTest.qWait(700)
        assert not W.QToolTip.isVisible()
        child.hide();menu.hide()
        return {'text':action.text(),'hint':expected,'route':'delayed status label',
                'delay_ms':500,'stable_ms':400,'submenu_open':True,
                'no_overlap':True,'native_parent_tooltip_suppressed':True,
                'child_hint_replaces_parent':True,'closed_after_leave':True,
                'action':[row.x(),row.y(),row.width(),row.height()],
                'status':[status_rect.x(),status_rect.y(),status_rect.width(),status_rect.height()]}

    menu_rows=[]
    for menu in window.findChildren(W.QMenu):
        for action in menu.actions():
            if not action.isSeparator():
                menu_rows.append((menu,action))
    menu_action_hovers=[]
    for index,(menu,action) in enumerate(menu_rows,1):
        if args.major==6 and action.menu() is not None:
            menu_action_hovers.append(hover_submenu_parent(menu,action,index))
        else:
            menu_action_hovers.append(hover_menu_action(menu,action,index))
    def hover_menu_corner(menu, action, corner):
        W.QToolTip.hideText()
        menu.hide()
        screen=app.primaryScreen().availableGeometry()
        menu.adjustSize()
        size=menu.sizeHint()
        x=screen.left() if corner.endswith('left') else screen.right()-size.width()+1
        y=screen.top() if corner.startswith('top') else screen.bottom()-size.height()+1
        safe=screen.center()
        subprocess.run(['xdotool','mousemove',str(safe.x()),str(safe.y())],check=True)
        QTest.qWait(700)
        assert not W.QToolTip.isVisible(), f'{corner} menu prior hint did not close'
        menu.popup(QPoint(x,y))
        QTest.qWait(150)
        # Force the actual QMenu surface to the screen corner, then measure the
        # final frame used by the tooltip positioner, not the requested anchor.
        menu.move(x,y)
        QTest.qWait(100)
        menu_rect=menu.frameGeometry()
        assert screen.contains(menu_rect), f'{corner} menu escaped screen: {menu_rect.getRect()}'
        row_local=menu.actionGeometry(action)
        origin=menu.mapToGlobal(row_local.topLeft())
        row=row_local.translated(origin-row_local.topLeft())
        center=row.center()
        subprocess.run(['xdotool','mousemove',str(center.x()),str(center.y())],check=True)
        for _ in range(30):
            QTest.qWait(100)
            if W.QToolTip.isVisible():break
        assert W.QToolTip.isVisible(), f'{corner} menu hint did not appear'
        assert W.QToolTip.text()==action.toolTip(), f'{corner} menu hint text mismatch'
        tips=[w for w in app.topLevelWidgets() if w.isVisible() and w.inherits('QTipLabel')]
        assert len(tips)==1, f'{corner} menu produced {len(tips)} tips'
        tip=tips[0].frameGeometry()
        assert not tip.intersects(row), f'{corner} menu hint covers its hovered row'
        assert not tip.intersects(menu_rect), f'{corner} menu hint covers another option'
        assert screen.contains(tip), f'{corner} menu hint escaped screen: {tip.getRect()}'
        QTest.qWait(400)
        assert W.QToolTip.isVisible() and tips[0].frameGeometry()==tip, (
            f'{corner} menu hint oscillated')
        subprocess.run(['xdotool','mousemove',str(safe.x()),str(safe.y())],check=True)
        QTest.qWait(700)
        assert not W.QToolTip.isVisible(), f'{corner} menu hint remained after leave'
        menu.hide()
        return {'corner':corner,'menu':[menu_rect.x(),menu_rect.y(),menu_rect.width(),menu_rect.height()],
                'action':[row.x(),row.y(),row.width(),row.height()],
                'tooltip':[tip.x(),tip.y(),tip.width(),tip.height()],
                'outside_whole_menu':True,'inside_screen':True,'stable_ms':400,
                'closed_after_leave':True}

    edge_menu=next((menu,action) for menu,action in menu_rows
                   if action.isEnabled() and action.menu() is None)
    edge_menu_hovers=[hover_menu_corner(edge_menu[0],edge_menu[1],corner)
                      for corner in ('top-left','top-right','bottom-left','bottom-right')]
    menu_hover={'rows_tested':len(menu_action_hovers),
                'all_rows_passed':True,'actions':menu_action_hovers,
                'edge_positions':edge_menu_hovers}
    proof=Path('/home/domainos-test')/('qtwidgets-proof' if args.major==6 else 'qt5widgets-proof')
    (proof/'HINTS-QA.json').write_text(json.dumps({'status':'passed','qt_major':args.major,
        'guarded_production_main':True,'buttons_with_hint':len(buttons),
        'typed_hint_coverage':{'combo':combo.toolTip(),'integer_spin':spin.toolTip(),
            'decimal_spin':decimal.toolTip(),'sliders':[s.toolTip() for s in sliders],
            'counts':{'combos':len(combos),'integer_spins':len(integer_spins),
                'decimal_spins':len(decimal_spins),'sliders':len(sliders),
                'line_edits':len(line_edits),'text_edits':len(text_edits)},
            'menu_actions':[{'text':a.text(),'hint':a.toolTip()} for a in actions],
            'line_edit':line_edit.toolTip(),'text_edit':text_edit.toolTip(),
            'scrollbars':[s.toolTip() for s in scrollbars]},
        'dynamic_dialogs':dialog_results,
        'hover':{'cold_delay_checked_ms':100,'stable_ms':400,'closed_after_leave':True,
                 'control':control,'tooltip':[rect.x(),rect.y(),rect.width(),rect.height()],
                 'no_overlap':True,'inside_screen':True},
        'additional_native_hovers':additional_hover,
        'menu_action_hover':menu_hover,
        'scope':'production gallery resource coverage and native push/combo/integer+decimal spin/horizontal+vertical slider hovers; every visible menu row action hovered; not every layout or Kvantum fidelity'}))
    QTimer.singleShot(1300,app.quit)
    return native_exec()


W.QApplication.exec=inspect_exec
raise SystemExit(main(['--qt-major',str(args.major)]))
