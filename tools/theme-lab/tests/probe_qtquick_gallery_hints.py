# SPDX-License-Identifier: GPL-3.0-or-later
"""Resource plus native hover/click proof for production QtQuick controls."""
import argparse
import json
from pathlib import Path
import sys
import subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'plasma/tests/galerias-nativas'))
from qtquick_demo import main,private_guards
private_guards()
parser=argparse.ArgumentParser();parser.add_argument('--major',type=int,choices=(5,6),required=True)
args=parser.parse_args()
from importlib import import_module
W=import_module(f'PyQt{args.major}.QtWidgets')
Core=import_module(f'PyQt{args.major}.QtCore')
QTest=import_module(f'PyQt{args.major}.QtTest').QTest
native_exec=W.QApplication.exec

def inspect_exec(app):
    QTest.qWait(400)
    window=next(w for w in app.allWindows() if w.objectName()==f'privateQtQuick{args.major}Window')
    assert app.platformName()=='xcb'
    hints=json.loads(window.property('nativeHints'))
    assert len(hints)>=20
    spin=next(h for h in hints if h['name']==f'qtquick{args.major}_spin')
    assert '-99' in spin['text'] and '999' in spin['text'] and 'sem unidade' in spin['text']
    button=window.findChild(Core.QObject,f'qtquick{args.major}_pressButton')
    point=button.mapToScene(Core.QPointF(button.width()/2,button.height()/2)).toPoint()
    subprocess.run(['xdotool','windowfocus',str(int(window.winId()))],check=True,timeout=2)
    subprocess.run(['xdotool','mousemove','0','0'],check=True,timeout=2)
    QTest.qWait(700)
    tip=window.property('nativePressTip')
    assert tip is not None
    origin=button.mapToScene(Core.QPointF(0,0))
    control=Core.QRectF(origin.x(),origin.y(),button.width(),button.height())
    subprocess.run(['xdotool','mousemove',str(window.x()+point.x()),str(window.y()+point.y())],check=True,timeout=2)
    QTest.qWait(300)
    assert not tip.property('visible'),'tooltip appears without declared delay'
    for _ in range(20):
        QTest.qWait(100)
        if tip.property('visible'):break
    assert tip.property('visible'),'native attached tooltip did not appear'
    if args.major == 6:
        tooltip_palette=json.loads(window.property('nativeTooltipPalette'))
        assert tooltip_palette['popupBackground']==tooltip_palette['roleBackground'], tooltip_palette
        assert tooltip_palette['popupForeground']==tooltip_palette['roleForeground'], tooltip_palette
        assert tooltip_palette['adaptedPopups'] > 0, tooltip_palette
    def tip_rect():
        parent=tip.property('parent')
        pos=parent.mapToScene(Core.QPointF(tip.property('x'),tip.property('y')))
        return Core.QRectF(pos.x(),pos.y(),tip.property('width'),tip.property('height'))
    rect=tip_rect()
    assert not rect.intersects(control),'tooltip covers button'
    assert Core.QRectF(0,0,window.width(),window.height()).contains(rect),'tooltip outside window'
    QTest.qWait(400)
    assert tip.property('visible') and tip_rect()==rect,'tooltip oscillation'
    subprocess.run(['xdotool','mousemove','0','0'],check=True,timeout=2)
    QTest.qWait(700)
    assert not tip.property('visible'),'tooltip remains after leaving'

    role_checks=[]
    if args.major==6:
        role_palette=json.loads(window.property('nativeTooltipPalette'))
        def hover_role_target(control, label):
            assert control is not None, f'{label} control is missing'
            subprocess.run(['xdotool','mousemove','0','0'],check=True,timeout=2)
            # Let the previous attached popup finish its fade-out before
            # clearing the diagnostic. Otherwise its delayed visibleChanged
            # can be mistaken for an early hint from this target.
            QTest.qWait(750)
            window.setProperty('lastTooltipRoleSnapshot','{}')
            origin=control.mapToScene(Core.QPointF(0,0))
            point=Core.QPoint(round(window.x()+origin.x()+control.width()/2),
                              round(window.y()+origin.y()+control.height()/2))
            subprocess.run(['xdotool','mousemove',str(point.x()),str(point.y())],check=True,timeout=2)
            QTest.qWait(300)
            snapshot={}
            for _ in range(20):
                QTest.qWait(100)
                try:
                    snapshot=json.loads(window.property('lastTooltipRoleSnapshot'))
                except Exception:
                    snapshot={}
                if snapshot.get('name')==control.objectName():
                    break
            assert snapshot.get('name')==control.objectName(), (
                f'{label} did not apply its role on hover/display: {snapshot}; control={{'
                f'name={control.objectName()!r}, visible={control.property("visible")!r}, '
                f'enabled={control.property("enabled")!r}, hovered={control.property("hovered")!r}, '
                f'geometry=({origin.x()},{origin.y()},{control.width()},{control.height()}), '
                f'pointer=({point.x()},{point.y()}), '
                f'role_popup_count={window.property("tooltipRolePopupCount")}}}')
            assert snapshot.get('colorSet')=='4', f'{label} colorSet is not Tooltip: {snapshot}'
            assert snapshot.get('background')==role_palette['roleBackground'], (
                f'{label} background differs from the active Tooltip role: {snapshot}, {role_palette}')
            assert snapshot.get('foreground')==role_palette['roleForeground'], (
                f'{label} text differs from the active Tooltip role: {snapshot}, {role_palette}')
            result={'name':label,'colorSet':snapshot['colorSet'],
                    'background':snapshot['background'],'foreground':snapshot['foreground'],
                    'matched_active_kde_role':True}
            role_checks.append(result)
            subprocess.run(['xdotool','mousemove','0','0'],check=True,timeout=2)
            QTest.qWait(700)  # Allow the native popup fade-out before testing its next owner.
            return result

        tabs=window.findChild(Core.QObject,f'qtquick{args.major}_tabs')
        table_tab=window.findChild(Core.QObject,f'qtquick{args.major}_tableTab')
        table_tab_point=table_tab.mapToScene(Core.QPointF(table_tab.width()/2,
                                                          table_tab.height()/2)).toPoint()
        QTest.mouseClick(window,Core.Qt.MouseButton.LeftButton,
                         Core.Qt.KeyboardModifier.NoModifier,table_tab_point)
        assert tabs.property('currentIndex')==1, 'Table tab did not become current'
        QTest.qWait(800)
        table_cell=window.property('nativeTableCellHintControl')
        if table_cell and (not table_cell.property('visible') or table_cell.width()<=0
                           or table_cell.height()<=0):
            table_cell=None
        hover_role_target(table_cell,'TableView cell')
        hover_role_target(window.property('nativeTableVerticalBar'),
                          'TableView vertical scrollbar')
        hover_role_target(window.property('nativeTableHorizontalBar'),
                          'TableView horizontal scrollbar')
        scroll_tab=window.findChild(Core.QObject,f'qtquick{args.major}_scrollTab')
        scroll_tab_point=scroll_tab.mapToScene(Core.QPointF(scroll_tab.width()/2,
                                                            scroll_tab.height()/2)).toPoint()
        QTest.mouseClick(window,Core.Qt.MouseButton.LeftButton,
                         Core.Qt.KeyboardModifier.NoModifier,scroll_tab_point)
        assert tabs.property('currentIndex')==2, 'Scroll tab did not become current'
        QTest.qWait(800)
        hover_role_target(window.property('nativeScrollViewVerticalBar'),
                          'ScrollView vertical scrollbar')
        hover_role_target(window.property('nativeScrollViewHorizontalBar'),
                          'ScrollView horizontal scrollbar')
        controls_tab=window.findChild(Core.QObject,f'qtquick{args.major}_controlsTab')
        controls_tab_point=controls_tab.mapToScene(Core.QPointF(controls_tab.width()/2,
                                                                controls_tab.height()/2)).toPoint()
        QTest.mouseClick(window,Core.Qt.MouseButton.LeftButton,
                         Core.Qt.KeyboardModifier.NoModifier,controls_tab_point)
        assert tabs.property('currentIndex')==0, 'Controls tab did not become current'
        QTest.qWait(800)
        role_output=Path('/home/domainos-test')/'qtquick6-proof'/'TOOLTIP-ROLE-SURFACES-QA.json'
        role_output.write_text(json.dumps({'status':'passed','checks':role_checks,
            'scope':'actual TableView cell and TableView/ScrollView scrollbars; active KDE Tooltip role'}))
    QTest.mouseClick(window,Core.Qt.MouseButton.LeftButton,Core.Qt.KeyboardModifier.NoModifier,point)
    menu=window.property('nativeMenu')
    assert Core.QMetaObject.invokeMethod(menu,'open') is not False
    QTest.qWait(400)
    assert menu.property('visible'),'native menu did not open'
    first=next(item for item in menu.findChildren(Core.QObject)
               if item.inherits('QQuickMenuItem') and item.property('text')=='Record activation')
    second=next(item for item in menu.findChildren(Core.QObject)
                if item.inherits('QQuickMenuItem') and item.property('text')=='Checkable action')
    def menu_tip_visible(item):
        return bool(item.property('rowHintVisible'))

    def menu_tip_rect(item):
        value=json.loads(item.property('rowHintRect'))
        assert {'x','y','width','height'} <= value.keys(), 'native menu-row tooltip geometry is missing'
        return Core.QRectF(value['x'],value['y'],value['width'],value['height'])

    def item_rect(item):
        item_window=item.window()
        origin=item.mapToScene(Core.QPointF(0,0))
        return Core.QRectF(item_window.x()+origin.x(),item_window.y()+origin.y(),
                           item.width(),item.height())

    menu_row=item_rect(first)
    menu_window=first.window()
    menu_point=first.mapToScene(Core.QPointF(first.width()/2,first.height()/2)).toPoint()
    subprocess.run(['xdotool','mousemove','0','0'],check=True,timeout=2)
    QTest.qWait(200)
    subprocess.run(['xdotool','mousemove',str(menu_window.x()+menu_point.x()),
                    str(menu_window.y()+menu_point.y())],check=True,timeout=2)
    QTest.qWait(300)
    assert not menu_tip_visible(first),'menu-row tooltip appears before the declared delay'
    for _ in range(20):
        QTest.qWait(100)
        if menu_tip_visible(first):break
    assert menu_tip_visible(first),'native menu-row tooltip did not appear'
    menu_tip_text=str(first.property('rowHintText'))
    assert menu_tip_text=='Registra a ativação da ação de exemplo; não inicia aplicações.', (
        f'QtQuick{args.major} first menu hint mismatch: {menu_tip_text!r}; '
        f'row={first.property("text")!r}')
    if args.major == 6:
        palette=json.loads(window.property('nativeTooltipPalette'))
        row_palette=json.loads(first.property('rowHintPalette'))
        assert row_palette['background']==palette['roleBackground'], (row_palette,palette)
        assert row_palette['foreground']==palette['roleForeground'], (row_palette,palette)

    row_tip_rect=menu_tip_rect(first)
    screen=app.primaryScreen().geometry()
    assert screen.contains(row_tip_rect.toAlignedRect()),'menu-row tooltip extends beyond the screen'
    assert not row_tip_rect.intersects(menu_row),'menu-row tooltip covers its owner'
    QTest.qWait(400)
    assert menu_tip_visible(first) and menu_tip_rect(first)==row_tip_rect,'menu-row tooltip oscillated'
    assert row_tip_rect.left() >= menu_row.right()+8, \
        'menu-row tooltip covers other menu actions instead of staying beside the list'
    subprocess.run(['xdotool','mousemove','0','0'],check=True,timeout=2)
    # KDE's native tooltip uses a fade-out transition; wait for the popup to
    # finish closing, while keeping the menu itself open for the next-row test.
    for _ in range(10):
        QTest.qWait(100)
        if not menu_tip_visible(first):
            break
    assert not menu_tip_visible(first), 'menu-row tooltip remained visible after leaving its row'

    assert menu.property('visible'),'moving away unexpectedly closed the native menu'
    second_rect=item_rect(second)
    second_point=second.mapToScene(Core.QPointF(second.width()/2,second.height()/2)).toPoint()
    subprocess.run(['xdotool','mousemove',str(menu_window.x()+second_point.x()),
                    str(menu_window.y()+second_point.y())],check=True,timeout=2)
    QTest.qWait(300)
    assert not menu_tip_visible(second),'second menu-row hint appears before the declared delay'
    for _ in range(20):
        QTest.qWait(100)
        if menu_tip_visible(second):break
    assert menu_tip_visible(second),'second native menu-row hint did not appear'
    second_menu_tip_text=str(second.property('rowHintText'))
    assert second_menu_tip_text=='Marca ou desmarca esta opção do menu nativo.', (
        f'QtQuick{args.major} second menu hint mismatch: {second_menu_tip_text!r}; '
        f'row={second.property("text")!r}')
    second_tip_rect=menu_tip_rect(second)
    assert screen.contains(second_tip_rect.toAlignedRect()),'second menu-row tooltip extends beyond the screen'
    assert second_tip_rect.left() >= second_rect.right()+8, \
        'second menu-row tooltip covers other menu actions'
    QTest.qWait(400)
    assert menu_tip_visible(second) and menu_tip_rect(second)==second_tip_rect, \
        'second menu-row tooltip oscillated'
    screenshot=Path('/home/domainos-test')/f'qtquick{args.major}-proof'/'menu-row-tooltip.png'
    screenshot.parent.mkdir(parents=True,exist_ok=True)
    window.grabWindow().save(str(screenshot),'PNG')
    subprocess.run(['xdotool','mousemove','0','0'],check=True,timeout=2)
    for _ in range(10):
        QTest.qWait(100)
        if not menu_tip_visible(second):
            break
    assert menu.property('visible'),'hovering outside a row unexpectedly dismissed the menu'
    assert not menu_tip_visible(second),'second menu-row tooltip remained after leaving'

    # Keep the native menu open: pointer departure hides the hint, while an
    # explicit action click is what closes this menu in the tested style.
    # Use the actual item's own window: native menus may use a popup surface.
    menu_point=first.mapToScene(Core.QPointF(first.width()/2,first.height()/2)).toPoint()
    QTest.mouseClick(first.window(),Core.Qt.MouseButton.LeftButton,Core.Qt.KeyboardModifier.NoModifier,menu_point)
    QTest.qWait(400)
    assert not menu.property('visible'),'menu remained after action'

    output=Path('/home/domainos-test')/f'qtquick{args.major}-proof'
    (output/'HINTS-QA.json').write_text(json.dumps({'status':'passed','native_hints':len(hints),
        'spin_range_units_verified':True,'real_click_sent':True,
        'hover':{'delay_checked_ms':300,'stable_ms':400,'no_overlap':True,'closed_after_leave':True,
                 'control':[control.x(),control.y(),control.width(),control.height()],
                 'tooltip':[rect.x(),rect.y(),rect.width(),rect.height()]},
        'menu':{'opened':True,'real_first_item_click':True,'closed_after_action':True,
                'row_hint_text':menu_tip_text,
                'row_hover':{'delay_checked_ms':300,'stable_ms':400,'no_owner_overlap':True,
                             'inside_screen':True,'outside_menu_bounds':True,'closed_after_leave':True,
                             'row':[menu_row.x(),menu_row.y(),menu_row.width(),menu_row.height()],
                             'tooltip':[row_tip_rect.x(),row_tip_rect.y(),row_tip_rect.width(),row_tip_rect.height()],
                             'second_row_text':second_menu_tip_text,'switch_delay_checked_ms':250,
                             'second_row_stable_ms':400,'second_row_tooltip':
                             [second_tip_rect.x(),second_tip_rect.y(),second_tip_rect.width(),second_tip_rect.height()]}},
        'tooltip_role_hover_checks':role_checks,
        'scope':'production QtQuick KDE Controls, one push and one menu-row hover/click; not Plasma SVG or all layouts'}))
    Core.QTimer.singleShot(1100,app.quit)
    return native_exec()

W.QApplication.exec=inspect_exec
raise SystemExit(main(['--qt-major',str(args.major)]))
