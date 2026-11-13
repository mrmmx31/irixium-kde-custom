#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Isolated native Plasma Components/KSvg scrollbar recipe preview."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


QML = r'''
import QtQuick
import QtQuick.Window
import QtQuick.Controls as QQC2
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC

Window {
    id: root
    objectName: "themeLabPlasmaWindow"
    width: 460
    height: 380
    visible: false
    title: "PARA LSI — T07 Plasma ScrollBars — native preview"
    color: palette.window
    SystemPalette { id: palette }
    Component.onCompleted: KSvg.ImageSet.imageSetName = "__THEME_NAME__"

    Text {
        x: 18; y: 12
        text: "Plasma Components.ScrollBar / KSvg — native 1:1"
        color: palette.windowText
    }
    Rectangle {
        objectName: "plasmaReferenceViewport"
        x: 24; y: 48
        width: 380; height: 230
        color: palette.window
        border.color: palette.windowText
        border.width: 1
        Text {
            x: 10; y: 10
            color: palette.windowText
            text: "Reference viewport\n\nNative scrollbar samples at 1:1 scale.\nPosition and thumb length are synthetic."
        }
    }
    PC.ScrollBar {
        id: verticalScrollBar
        objectName: "plasmaVerticalScrollBar"
        x: 405; y: 48
        width: 15; height: 230
        orientation: Qt.Vertical
        policy: PC.ScrollBar.AlwaysOn
        size: 0.34
        position: 0.28
        active: true
    }
    PC.ScrollBar {
        id: horizontalScrollBar
        objectName: "plasmaHorizontalScrollBar"
        x: 24; y: 283
        width: 380; height: 15
        orientation: Qt.Horizontal
        policy: PC.ScrollBar.AlwaysOn
        size: 0.34
        position: 0.28
        active: true
    }
    Text {
        objectName: "plasmaThemeSnapshotLabel"
        x: 24; y: 356
        text: "Private theme snapshot: __THEME_NAME__"
        color: palette.windowText
    }
    QQC2.ToolTip {
        id: verticalHint
        objectName: "plasmaVerticalScrollBarHint"
        parent: QQC2.Overlay.overlay
        visible: verticalScrollBar.hovered
        delay: 500
        timeout: -1
        text: "15 px de largura. Arraste o indicador; a amostra não rola conteúdo real."
        width: 300
        x: 24
        y: 300

        Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
        Kirigami.Theme.inherit: false
        contentItem: Text {
            text: verticalHint.text
            font: verticalHint.font
            color: verticalHint.Kirigami.Theme.textColor
            wrapMode: Text.WordWrap
            Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
            Kirigami.Theme.inherit: false
        }
        background: Rectangle {
            Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor
            border.color: Qt.darker(Kirigami.Theme.backgroundColor, 1.08)
            border.width: 1
        }
    }
    QQC2.ToolTip {
        id: horizontalHint
        objectName: "plasmaHorizontalScrollBarHint"
        parent: QQC2.Overlay.overlay
        visible: horizontalScrollBar.hovered
        delay: 500
        timeout: -1
        text: "15 px de altura. Arraste o indicador; a amostra não rola conteúdo real."
        width: 300
        x: 24
        y: 300

        Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
        Kirigami.Theme.inherit: false
        contentItem: Text {
            text: horizontalHint.text
            font: horizontalHint.font
            color: horizontalHint.Kirigami.Theme.textColor
            wrapMode: Text.WordWrap
            Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
            Kirigami.Theme.inherit: false
        }
        background: Rectangle {
            Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor
            border.color: Qt.darker(Kirigami.Theme.backgroundColor, 1.08)
            border.width: 1
        }
    }
}
'''


def _atomic_json(path: Path, payload):
    temporary = path.with_name('.' + path.name + '.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.chmod(0o600)
    os.replace(temporary, path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--test-close-ms', type=int,
                        help=argparse.SUPPRESS)
    parser.add_argument('--embed-window', type=lambda value: int(value, 0))
    parser.add_argument('--host-pid', type=int)
    parser.add_argument('--host-bridge', type=Path)
    parser.add_argument('--host-session-root', type=Path)
    args = parser.parse_args(argv)
    if args.test_close_ms is not None and not 500 <= args.test_close_ms <= 60000:
        raise ValueError('--test-close-ms must be between 500 and 60000')

    from qt6_demo import PreviewShutdown, private_guards
    guards = private_guards()
    embedded = args.embed_window is not None
    if embedded != bool(args.host_pid and args.host_bridge and args.host_session_root):
        raise RuntimeError('Embedding requires canvas, host PID, host bridge and private session root together')
    session_root = Path(os.environ.get('IRIX_DOMAINOS_SESSION_ROOT', '/home/domainos-test')).resolve(strict=True)
    if embedded and args.host_session_root.resolve(strict=True) != session_root:
        raise RuntimeError('Embedding host and child must share the same private Theme Lab session')
    root = Path(os.environ.get('IRIX_DOMAINOS_FIXTURE_ROOT', Path(__file__).resolve().parents[3])).resolve()
    sys.path.insert(0, str(root / 'tools/theme-lab'))
    import backend
    from plasma_recipe import verify as verify_snapshot

    snapshot_path = args.snapshot.absolute()
    receipt = json.loads(backend.read_file(snapshot_path))
    model, _ = backend.project(args.project)
    verified = verify_snapshot(root, receipt, model)
    output = args.output.absolute()
    if not output.is_relative_to(session_root):
        raise RuntimeError('Preview proof must remain inside the private Theme Lab session')
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.chmod(0o700)

    os.environ['QT_QUICK_CONTROLS_STYLE'] = 'org.kde.desktop'
    from PyQt6.QtCore import QObject, Qt, QTimer, QUrl, qVersion
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtQuick import QQuickWindow

    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName('Theme Lab — native Plasma Style preview')
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda messages: warnings.extend(str(message.toString()) for message in messages))
    qml_path = output / 'plasma-style-preview.qml'
    qml_path.write_text(QML.replace('__THEME_NAME__', verified['theme_name']), encoding='utf-8')
    qml_path.chmod(0o600)
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    roots = engine.rootObjects()
    if len(roots) != 1 or not isinstance(roots[0], QQuickWindow):
        raise RuntimeError('Native Plasma ScrollBar/KSvg failed to load: ' + '; '.join(warnings))
    window = roots[0]
    bridge = None
    shutdown = PreviewShutdown(app, window)
    app.aboutToQuit.connect(shutdown.cleanup)
    if embedded:
        window.setFlags(Qt.WindowType.FramelessWindowHint)
    window.show()
    if embedded:
        lab = root / 'tools/theme-lab'
        if str(lab) not in sys.path:
            sys.path.insert(0, str(lab))
        from gtk4_host import HostBridge
        bridge = HostBridge(args.host_bridge, args.embed_window, args.host_pid)
        bridge.attach(int(window.winId()))
        shutdown.set_bridge(bridge)

        def poll_host():
            if bridge.poll() is None:
                shutdown.request()

        host_timer = QTimer(app)
        host_timer.setInterval(150)
        host_timer.timeout.connect(poll_host)
        host_timer.start()
        shutdown.set_timer(host_timer)

    def metrics(name):
        item = window.findChild(QObject, name)
        if item is None:
            return {'found': False}
        fields = ('width', 'height', 'implicitWidth', 'implicitHeight', 'leftPadding',
                  'rightPadding', 'topPadding', 'bottomPadding', 'leftInset',
                  'rightInset', 'topInset', 'bottomInset', 'visible', 'enabled',
                  'hovered', 'pressed')
        return {'found': True, 'class': item.metaObject().className(),
                **{key: item.property(key) for key in fields
                   if item.property(key) is not None}}

    def save_proof():
        bars = {name: metrics(name) for name in
                ('plasmaVerticalScrollBar', 'plasmaHorizontalScrollBar')}
        screenshot = output / 'plasma-style.png'
        saved = window.grabWindow().save(str(screenshot), 'PNG')
        report = {
            'status': 'native_preview_open', 'runtime': {'qt': qVersion(),
                         'platform': app.platformName(), 'native_qml': True,
                         'renderer': 'org.kde.plasma.components.ScrollBar + KSvg'},
            'guards': guards, 'theme_name': verified['theme_name'],
            'theme_svg': verified['svg'], 'recipe_sha256': verified['recipe_sha256'],
            'selected_scheme': verified['selected_scheme'],
            'bars': bars, 'reference_viewport': metrics('plasmaReferenceViewport'),
            'expected_geometry': verified['effective_geometry'],
            'qml_warnings': warnings, 'screenshot_saved': saved,
            'screenshot': str(screenshot) if saved else None,
            'screenshot_sha256': hashlib.sha256(screenshot.read_bytes()).hexdigest() if saved else None,
            'personal_profile_changed': False, 'theme_installed': False,
            'embedded': embedded,
            'native_origin': ('x11-reparented-plasma-quick-window' if embedded
                              else 'detached-plasma-quick-window'),
            'limitations': verified['limitations']}
        _atomic_json(output / 'RESULTADO.json', report)
        print(json.dumps(report, ensure_ascii=False), flush=True)

    QTimer.singleShot(1200, save_proof)
    if args.test_close_ms is not None:
        QTimer.singleShot(args.test_close_ms, shutdown.request)
    return app.exec()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, ImportError) as error:
        print('Private Plasma Style preview refused: ' + str(error), file=sys.stderr)
        sys.exit(2)
