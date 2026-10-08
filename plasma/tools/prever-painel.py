#!/usr/bin/env python3
"""Render and exercise Classic artwork in an isolated native Plasma gallery.

This does not install, replace or activate the desktop. Model/window activation
and live-panel persistence require the separate plasmashell runtime checks.
"""
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET

PLASMA = Path(__file__).resolve().parents[1]
REPO = PLASMA.parent
ARTWORK = PLASMA / 'IrixClassic'


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capturas', type=Path, default=Path('/tmp/irix-classic-painel'))
    p.add_argument('--controles', action='store_true', help='Include native control gallery.')
    p.add_argument('--testar', action='store_true', help='Run real pointer input on gallery controls.')
    p.add_argument('--offscreen', action='store_true')
    p.add_argument('--interativo', action='store_true', help='Keep the preview window open.')
    return p.parse_args()


def check_assets():
    suffixes = ('center', 'top', 'bottom', 'left', 'right', 'topleft', 'topright', 'bottomleft', 'bottomright')
    required = {
        'tasks': ('normal', 'hover', 'focus', 'focus-hover', 'minimized', 'minimized-hover',
                  'attention', 'attention-hover', 'pressed', 'focus-pressed', 'minimized-pressed'),
        'button': ('normal', 'hover', 'pressed', 'toolbutton-hover', 'toolbutton-pressed', 'focus'),
        'pager': ('normal', 'active', 'hover'),
        'viewitem': ('normal', 'hover', 'selected', 'selected+hover'),
        'listitem': ('normal', 'hover', 'pressed'),
        'slider': ('groove', 'groove-highlight'),
        'panel-background': ('',),
        'iconbox': ('', 'heading'),
        'instrument': ('normal', 'pressed'),
        'instrument-well': ('',),
        'task-icon': ('normal', 'normal-hover', 'hover', 'focus', 'focus-hover', 'minimized', 'minimized-hover',
                      'attention', 'attention-hover', 'pressed', 'normal-pressed', 'focus-pressed',
                      'minimized-pressed', 'attention-pressed'),
    }
    result = {}
    for resource, prefixes in required.items():
        path = ARTWORK / 'widgets' / f'{resource}.svg'
        root = ET.parse(path).getroot()
        all_ids = [e.get('id') for e in root.iter() if e.get('id')]
        if len(all_ids) != len(set(all_ids)):
            raise AssertionError(f'Duplicate element IDs: {path}')
        ids = set(all_ids)
        for prefix in prefixes:
            for suffix in suffixes:
                element = f'{prefix}-{suffix}' if prefix else suffix
                if element not in ids:
                    raise AssertionError(f'Missing {resource}/{element}')
        if resource == 'slider':
            for direction in ('horizontal', 'vertical'):
                for kind in ('handle', 'hover', 'focus', 'shadow'):
                    element = f'{direction}-slider-{kind}'
                    if element not in ids:
                        raise AssertionError(f'Missing slider/{element}')
        result[resource] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'contract': 'pass'}
    clock = ARTWORK / 'widgets' / 'clock.svg'
    clock_ids = [e.get('id') for e in ET.parse(clock).getroot().iter() if e.get('id')]
    if len(clock_ids) != len(set(clock_ids)):
        raise AssertionError(f'Duplicate element IDs: {clock}')
    for element in ('ClockFace', 'Glass', 'HandCenterScrew', 'HourHand', 'MinuteHand', 'SecondHand',
                    'HourHandShadow', 'MinuteHandShadow', 'SecondHandShadow',
                    'hint-hourhand-rotation-center-offset', 'hint-minutehand-rotation-center-offset',
                    'hint-secondhand-rotation-center-offset', 'hint-hourhandshadow-rotation-center-offset',
                    'hint-minutehandshadow-rotation-center-offset', 'hint-secondhandshadow-rotation-center-offset'):
        if element not in clock_ids:
            raise AssertionError(f'Missing clock/{element}')
    result['clock'] = {'sha256': hashlib.sha256(clock.read_bytes()).hexdigest(), 'contract': 'pass'}
    return result


def isolated_profile(root: Path):
    config, data, cache, state = (root / n for n in ('config', 'data', 'cache', 'state'))
    for folder in (config, data, cache, state):
        folder.mkdir()
    target = data / 'plasma' / 'desktoptheme' / 'IrixClassic'
    shutil.copytree(ARTWORK, target)
    (config / 'plasmarc').write_text('[Theme]\nname=IrixClassic\n')
    colors = (REPO / 'colors' / 'Irixium.colors').read_text()
    (config / 'kdeglobals').write_text(colors + '\n[KDE]\nwidgetStyle=kvantum\n[Icons]\nTheme=IrixClassic-SGI\n')
    kvsrc = REPO / 'kvantum' / 'IrixClassic'
    if kvsrc.is_dir():
        shutil.copytree(kvsrc, config / 'Kvantum' / 'IrixClassic')
        (config / 'Kvantum' / 'kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
    original_data = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))
    os.environ.update(XDG_CONFIG_HOME=str(config), XDG_DATA_HOME=str(data),
                      XDG_CACHE_HOME=str(cache), XDG_STATE_HOME=str(state))
    # Reuse installed icon resources read-only; the preview theme itself is first
    # in the private XDG_DATA_HOME above. No user's configuration is read or written.
    os.environ['XDG_DATA_DIRS'] = original_data + ':' + os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share')
    os.environ['XDG_CONFIG_DIRS'] = '/etc/xdg'
    os.environ['QT_QUICK_CONTROLS_STYLE'] = 'org.kde.desktop'
    os.environ['QT_QPA_PLATFORMTHEME'] = 'generic'
    os.environ['XDG_CURRENT_DESKTOP'] = 'NONE'
    os.environ.pop('QT_STYLE_OVERRIDE', None)


def main():
    args = parse_args()
    output = args.capturas.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'native gallery artwork and control input; live task/window actions are separate',
              'task_representation': '24px icon inside a 28px square well, separate 14px caption, 8px Iconbox heading in a 64px panel',
              'right_section': 'recessed tray field, analog instrument socket, transparent pager frame above illustrative window rectangles; no real desktop model in this gallery',
              'desktop_modified': False, 'network_services_called': False, 'checks': {}, 'artwork': check_assets()}
    if args.offscreen or not (os.environ.get('WAYLAND_DISPLAY') or os.environ.get('DISPLAY')):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        os.environ['QT_QUICK_BACKEND'] = 'software'
    try:
        from PyQt6 import sip
        from PyQt6.QtCore import QObject, QPointF, QTimer, QUrl, Qt, QMetaObject, Q_ARG, Q_RETURN_ARG, qVersion
        from PyQt6.QtGui import QFont
        from PyQt6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlPropertyMap
        from PyQt6.QtQuick import QQuickItem, QQuickWindow
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication, QStyleFactory
    except ImportError as error:
        print(f'Native Qt 6 gallery unavailable: {error}', file=sys.stderr)
        return 77
    exit_code = 0
    with tempfile.TemporaryDirectory(prefix='irix-classic-panel-', dir='/tmp') as temp:
        isolated_profile(Path(temp))
        app = QApplication([sys.argv[0]])
        style = QStyleFactory.create('kvantum')
        app.setStyle(style if style is not None else 'Fusion')
        os.environ['QT_QUICK_CONTROLS_STYLE'] = 'org.kde.desktop'
        app.setFont(QFont('DejaVu Sans', 10))
        report['runtime'] = {'qt': qVersion(), 'platform': app.platformName(),
                             'widgets_style': app.style().objectName(), 'profile': 'temporary /tmp only'}
        engine = QQmlApplicationEngine()
        context = engine.rootContext()
        context.setContextProperty('artworkRoot', str(ARTWORK))
        context.setContextProperty('previewControls', args.controles or args.testar)
        engine.load(QUrl.fromLocalFile(str(PLASMA / 'tests' / 'PanelPreview.qml')))
        if not engine.rootObjects():
            print('Failed to load native Plasma gallery.', file=sys.stderr)
            return 1
        window = sip.cast(engine.rootObjects()[0], QQuickWindow)

        def item(name):
            obj = window.findChild(QObject, name)
            if obj is None:
                raise AssertionError(f'Missing control: {name}')
            return sip.cast(obj, QQuickItem)

        def settle(ms=50):
            app.processEvents()
            window.requestUpdate()
            QTest.qWait(ms)
            app.processEvents()

        def capture(name):
            settle()
            image = window.grabWindow()
            if image.isNull() or not image.save(str(output / name)):
                raise AssertionError(f'Empty capture: {name}')
            return image

        def control_image(control):
            settle()
            top = control.mapToScene(QPointF(0, 0))
            return window.grabWindow().copy(round(top.x()), round(top.y()), round(control.width()), round(control.height()))

        def point(control, x=None, y=None):
            return control.mapToScene(QPointF(control.width() / 2 if x is None else x,
                                              control.height() / 2 if y is None else y)).toPoint()

        def require(name, value):
            report['checks'][name] = bool(value)
            if not value:
                raise AssertionError(name)

        def svg_has(name, element):
            obj = window.findChild(QObject, name)
            if obj is None:
                raise AssertionError(f'Missing native SVG: {name}')
            return QMetaObject.invokeMethod(obj, 'hasElement', Qt.ConnectionType.DirectConnection,
                                           Q_RETURN_ARG(bool), Q_ARG(str, element))

        def test_applications_icon_sources():
            # Exercise the actual production compact icon blocks. No applet
            # model is created: Plasmoid icon/form-factor inputs are mocked.
            production = PLASMA / 'applets' / 'org.irixclassic.applications' / 'contents' / 'ui' / 'main.qml'
            source = production.read_text()

            def block(kind, identifier):
                marker = source.index('id: ' + identifier)
                start = source.rfind(kind + ' {', 0, marker)
                if start < 0:
                    raise AssertionError('Missing production icon block: ' + identifier)
                opening = source.index('{', start)
                depth = 0
                for position in range(opening, len(source)):
                    depth += (source[position] == '{') - (source[position] == '}')
                    if depth == 0:
                        return source[start:position + 1].replace(
                            'id: ' + identifier, 'id: ' + identifier + '\n objectName: "' + identifier + 'Smoke"' + ('\n readonly property int smokeStatus: status' if identifier == 'imageFallback' else ''), 1)
                raise AssertionError('Unbalanced production icon block: ' + identifier)

            compact_blocks = '\n'.join((block('Kirigami.Icon', 'buttonIcon'),
                                          block('Kirigami.Icon', 'buttonIconFallback'),
                                          block('Image', 'imageFallback')))
            qml = ("import QtQuick\nimport QtQuick.Layouts\n"
                   "import org.kde.kirigami as Kirigami\n"
                   'import "' + (production.parent / 'code' / 'tools.js').as_uri() + '" as Tools\n'
                   'Item { width: 100; height: 80;\n'
                   'QtObject { id: kickoff; property bool vertical: false }\n'
                   'QtObject { id: compactRoot; property bool containsMouse: true }\n'
                   'QtObject { id: compactDragArea; property bool containsDrag: false }\n'
                   + compact_blocks + '\n}')
            values = QQmlPropertyMap(engine)
            values.insert('icon', '')
            values.insert('formFactor', 2)
            context.setContextProperty('Plasmoid', values)
            component = QQmlComponent(engine)
            component.setData(qml.encode(), QUrl.fromLocalFile(str(Path(temp) / 'icon-smoke.qml')))
            smoke = component.create()
            if smoke is None:
                raise AssertionError('Production compact icon smoke failed: ' +
                                     '; '.join(e.toString() for e in component.errors()))
            fallback = smoke.findChild(QObject, 'imageFallbackSmoke')
            native_icon = smoke.findChild(QObject, 'buttonIconSmoke')
            default_icon = smoke.findChild(QObject, 'buttonIconFallbackSmoke')
            fixture = Path(temp) / 'custom-menu-icon.svg'
            fixture.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="30" height="12"><rect width="30" height="12" fill="#9ebfbf"/></svg>')
            import base64
            data_url = 'data:image/svg+xml;base64,' + base64.b64encode(fixture.read_bytes()).decode()
            try:
                for label, value in (('empty', ''), ('symbolic', 'start-here-kde-symbolic')):
                    values.insert('icon', value)
                    settle(100)
                    require('applications_' + label + '_image_source_empty', fallback.property('source').isEmpty())
                    require('applications_' + label + '_image_status_null', fallback.property('smokeStatus') == 0)
                    if label == 'symbolic':
                        require('applications_symbolic_icon_resolves', native_icon.property('valid'))
                require('applications_icon_hover_recolor_disabled', not native_icon.property('active') and not default_icon.property('active'))
                for label, value in (('absolute_filename', str(fixture)), ('file_url', fixture.as_uri()), ('data_url', data_url)):
                    values.insert('icon', value)
                    settle(100)
                    require('applications_' + label + '_image_source_set', not fallback.property('source').isEmpty())
                    require('applications_' + label + '_image_status_ready', fallback.property('smokeStatus') == 1)
                    require('applications_' + label + '_non_square_image_visible', fallback.property('visible'))
            finally:
                smoke.deleteLater()
                app.processEvents()

        def test_input():
            outside = QPointF(window.width() - 5, window.height() - 5).toPoint()
            tile = item('normalTask')
            QTest.mouseMove(window, outside)
            before = control_image(tile)
            initial = tile.property('activationCount')
            QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point(tile))
            require('task_down_on_press', tile.property('down'))
            require('task_no_action_before_release', tile.property('activationCount') == initial and not tile.property('checked'))
            held = control_image(tile)
            require('task_pressed_pixels', before != held)
            require('task_pressed_prefix', tile.property('usedPrefix') in ('normal-pressed', 'pressed'))
            QTest.qWait(180)
            require('task_feedback_while_held', tile.property('down') and held == control_image(tile))
            capture('painel-pressionado.png')
            QTest.mouseMove(window, outside)
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=outside)
            require('task_release_outside_cancels', tile.property('activationCount') == initial and not tile.property('checked'))
            QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point(tile))
            require('task_release_inside_activates', tile.property('activationCount') == initial + 1 and tile.property('checked'))
            QTest.mouseMove(window, outside)
            active = item('activeTask')
            before = control_image(active)
            QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point(active))
            require('active_task_down', active.property('down'))
            require('active_task_press_distinct', before != control_image(active))
            require('active_task_pressed_prefix', active.property('usedPrefix') == 'focus-pressed')
            capture('painel-ativo-pressionado.png')
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=outside)
            require('active_task_cancel_preserves_state', active.property('checked'))
            QTest.mouseMove(window, outside)
            minimized = item('minimizedTask')
            before = control_image(minimized)
            QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point(minimized))
            require('minimized_task_pressed_prefix', minimized.property('usedPrefix') == 'minimized-pressed')
            require('minimized_task_press_distinct', before != control_image(minimized))
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=outside)

            wifi = item('wifiSwitch')
            QTest.mouseMove(window, outside)
            before = control_image(wifi)
            QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point(wifi, 8))
            require('native_switch_down', wifi.property('down'))
            require('native_switch_no_toggle_before_release', not wifi.property('checked'))
            require('native_switch_pressed_pixels', before != control_image(wifi))
            capture('controles-pressionados.png')
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=point(wifi, 8))
            require('native_switch_turns_on', wifi.property('checked'))
            QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point(wifi, 8))
            require('native_switch_turns_off', not wifi.property('checked'))

            for name, vertical in (('horizontalSlider', False), ('verticalSlider', True)):
                slider = item(name)
                handle = sip.cast(slider.property('handle'), QQuickItem)
                initial = slider.property('value')
                QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point(handle))
                require(name + '_pressed', slider.property('pressed'))
                target = point(slider, slider.width() / 2 if vertical else slider.width() * .82,
                               slider.height() * .82 if vertical else slider.height() / 2)
                QTest.mouseMove(window, target)
                QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
                require(name + '_value_changes', abs(slider.property('value') - initial) > 5)
                require(name + '_released', not slider.property('pressed'))

            entry = item('listEntry')
            QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point(entry))
            require('native_list_down', entry.property('down'))
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=point(entry))
            require('native_list_selected', entry.property('highlighted'))
            QTest.mouseMove(window, outside)
            for name in ('commandButton', 'trayButton'):
                button = item(name)
                before = control_image(button)
                QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point(button))
                require(name + '_down', button.property('down'))
                require(name + '_pressed_pixels', before != control_image(button))
                QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=point(button))
            QTest.mouseMove(window, outside)
            capture('controles-verificados.png')

        def run():
            nonlocal exit_code
            try:
                image = capture('painel-normal.png')
                image.copy(0, 0, 1440, 64).save(str(output / 'barra-normal.png'))
                if args.controles or args.testar:
                    for native, elements in {
                        'nativeSwitchSvg': ('handle', 'handle-pressed', 'inactive-center', 'active-center'),
                        'nativeSliderSvg': ('horizontal-slider-handle', 'vertical-slider-handle', 'vertical-slider-hover', 'vertical-slider-focus'),
                        'nativeListSvg': ('normal-center', 'hover-center', 'pressed-center'),
                    }.items():
                        for element in elements:
                            require(native + '/' + element, svg_has(native, element))
                if args.testar:
                    test_input()
                    test_applications_icon_sources()
                report['pass'] = True
            except Exception as error:
                report['pass'] = False
                report['failure'] = str(error)
                exit_code = 1
                traceback.print_exc()
                try:
                    capture('falha.png')
                except Exception:
                    pass
            finally:
                (output / 'resultado.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
                print(json.dumps({'pass': report['pass'], 'checks': len(report['checks']), 'capturas': str(output)}, ensure_ascii=False))
                if not args.interativo:
                    app.quit()

        QTimer.singleShot(500, run)  # Test/capture settlement only; no production timer.
        app.exec()
        engine.clearComponentCache()
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
