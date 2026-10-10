#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native QtQuick5/6 KDE controls in the coordinated private Xephyr namespace.

The QML and artificial text data are written only inside the disposable HOME.
Controls inherit the KDE platform palette/font. No custom painting or CSS is used.
"""
from pathlib import Path
import argparse
import importlib
import importlib.util
import json
import os
import sys

from qt6_demo import private_guards, selection


QML_SOURCE = r'''
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    objectName: "privateQtQuick__MAJOR__Window"
    width: 660
    height: 560
    visible: true
    title: "DomainOS SR10.4 — QtQuick__MAJOR__ / KDE"
    property int selectedRow: -1
    signal actionRecorded(string action, string detail)
    function log(action, detail) {
        statusLabel.text = action + ": " + detail
        actionRecorded(action, String(detail))
    }
    readonly property string nativePalettes: JSON.stringify({
        normalButton: {button: String(pressButton.palette.button),
                       buttonText: String(pressButton.palette.buttonText),
                       window: String(pressButton.palette.window),
                       highlight: String(pressButton.palette.highlight)},
        disabledButton: {button: String(disabledButton.palette.button),
                         buttonText: String(disabledButton.palette.buttonText),
                         window: String(disabledButton.palette.window),
                         highlight: String(disabledButton.palette.highlight)}
    })
    readonly property string nativeFont: pressButton.font.family + ";" + pressButton.font.pointSize
    menuBar: MenuBar {
        Menu {
            title: "Native menu"
            Action { text: "Record activation"; onTriggered: window.log("menu", "activated") }
            Action { text: "Checkable action"; checkable: true; checked: true }
            Action { text: "Unavailable action"; enabled: false }
            MenuSeparator {}
            Menu { title: "Submenu"; Action { text: "Native submenu item" } }
            Action { text: "Close only this gallery"; onTriggered: window.close() }
        }
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        Label {
            text: "REAL QtQuick__MAJOR__ controls | " + runtimeDescription
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
        TabBar {
            id: pages
            objectName: "qtquick__MAJOR___tabs"
            Layout.fillWidth: true
            TabButton { text: "Controls" }
            TabButton { text: "Table" }
            TabButton { text: "Scroll" }
        }
        StackLayout {
            currentIndex: pages.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                GroupBox {
                    title: "Native buttons and selection"
                    Layout.fillWidth: true
                    RowLayout {
                        Button {
                            id: pressButton
                            objectName: "qtquick__MAJOR___pressButton"
                            text: "Press and release"
                            onClicked: window.log("button", "clicked")
                        }
                        Button { text: "Latched"; checkable: true; checked: true }
                        Button {
                            id: disabledButton
                            objectName: "qtquick__MAJOR___disabledButton"
                            text: "Disabled"
                            enabled: false
                        }
                    }
                }
                RowLayout {
                    CheckBox { text: "Off" }
                    CheckBox { text: "Checked"; checked: true }
                    CheckBox { text: "Mixed"; tristate: true; checkState: Qt.PartiallyChecked }
                    CheckBox { text: "Disabled"; checked: true; enabled: false }
                }
                RowLayout {
                    RadioButton { text: "Radio A"; checked: true }
                    RadioButton { text: "Radio B" }
                    Switch {
                        objectName: "qtquick__MAJOR___switch"
                        text: "Native switch"
                        onToggled: window.log("switch", checked)
                    }
                    Switch { text: "Disabled"; checked: true; enabled: false }
                }
                GridLayout {
                    columns: 2
                    Layout.fillWidth: true
                    Label { text: "Combo" }
                    ComboBox {
                        objectName: "qtquick__MAJOR___combo"
                        model: ["First option", "Second option", "Third option"]
                        Layout.fillWidth: true
                        onActivated: window.log("combo", currentText)
                    }
                    Label { text: "Disabled combo" }
                    ComboBox { model: ["Unavailable"]; enabled: false; Layout.fillWidth: true }
                    Label { text: "Spin box" }
                    SpinBox {
                        objectName: "qtquick__MAJOR___spin"
                        from: -99; to: 999; value: 42; editable: true
                        onValueModified: window.log("spin", value)
                    }
                    Label { text: "Disabled spin" }
                    SpinBox { value: 42; enabled: false }
                    Label { text: "Text" }
                    TextField { text: "Editable native TextField"; Layout.fillWidth: true }
                    Label { text: "Disabled text" }
                    TextField { text: "Unavailable"; enabled: false; Layout.fillWidth: true }
                }
                RowLayout {
                    Label { text: "Slider" }
                    Slider {
                        id: slider
                        objectName: "qtquick__MAJOR___slider"
                        from: 0; to: 100; value: 43
                        Layout.fillWidth: true
                        onMoved: window.log("slider", value)
                    }
                    Slider { value: 0.43; enabled: false }
                }
                ProgressBar { from: 0; to: 100; value: slider.value; Layout.fillWidth: true }
                Item { Layout.fillHeight: true }
            }
            Frame {
                ColumnLayout {
                    anchors.fill: parent
                    RowLayout {
                        Repeater {
                            model: ["Item", "State", "Value"]
                            Label { text: modelData; Layout.fillWidth: true }
                        }
                    }
                    TableView {
                        id: table
                        objectName: "qtquick__MAJOR___table"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: galleryTableModel
                        columnSpacing: 1
                        rowSpacing: 1
                        delegate: ItemDelegate {
                            implicitWidth: 230
                            implicitHeight: 32
                            text: display
                            highlighted: row === window.selectedRow
                            onClicked: {
                                window.selectedRow = row
                                window.log("table cell", row + "," + column)
                            }
                        }
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AlwaysOn }
                        ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AlwaysOn }
                    }
                }
            }
            ScrollView {
                objectName: "qtquick__MAJOR___scrollView"
                clip: true
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOn
                TextArea {
                    objectName: "qtquick__MAJOR___textArea"
                    text: artificialText
                    wrapMode: TextEdit.NoWrap
                    selectByMouse: true
                }
            }
        }
        RowLayout {
            Label {
                id: statusLabel
                text: "Artificial data only; controls inherit the private KDE scheme."
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Button { text: "Save window proof"; onClicked: window.log("capture", "requested") }
        }
    }
}
'''


def binding_inventory(major):
    """Locate binding modules without initializing Qt or contacting a display."""
    required = ('QtCore', 'QtGui', 'QtWidgets', 'QtQml', 'QtQuick')
    modules = {}
    for name in required:
        qualified = f'PyQt{major}.{name}'
        try:
            found = importlib.util.find_spec(qualified)
        except (ImportError, ValueError):
            found = None
        modules[qualified] = found.origin if found else None
    return {'toolkit': f'QtQuick{major}', 'qtMajor': major,
            'status': 'ready' if all(modules.values()) else 'unavailable',
            'modules': modules, 'gui_started': False, 'qt_initialized': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qt-major', type=int, choices=(5, 6), default=6)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--guard-only', action='store_true')
    parser.add_argument('--verificar-only', action='store_true', help='Inspect bindings only; never initialize Qt')
    args = parser.parse_args(argv)
    if args.verificar_only:
        inventory = binding_inventory(args.qt_major)
        print(json.dumps(inventory, sort_keys=True))
        return 0 if inventory['status'] == 'ready' else 3
    guards = private_guards()  # Before all Qt imports/application initialization.
    output = (args.output or Path('/home/domainos-test') / f'qtquick{args.qt_major}-proof').resolve()
    if not output.is_relative_to(Path('/home/domainos-test')):
        raise RuntimeError('Proof output must remain inside fake HOME')
    if args.guard_only:
        print(json.dumps(guards, sort_keys=True))
        return 0
    inventory = binding_inventory(args.qt_major)
    if inventory['status'] != 'ready':
        raise RuntimeError(f'QtQuick{args.qt_major} bindings unavailable: ' +
                           ', '.join(name for name, path in inventory['modules'].items() if not path))
    # Native Controls style selection is process-local and precedes Qt initialization.
    # It is not a QApplication style/palette override or custom component drawing.
    os.environ['QT_QUICK_CONTROLS_STYLE'] = 'org.kde.desktop'
    if args.qt_major == 6:
        from PyQt6.QtCore import (Qt, QObject, QModelIndex, QAbstractTableModel,
                                 QTimer, QUrl, QT_VERSION_STR, PYQT_VERSION_STR, qVersion)
        from PyQt6.QtGui import QPalette
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickWindow
    else:
        from PyQt5.QtCore import (Qt, QObject, QModelIndex, QAbstractTableModel,
                                 QTimer, QUrl, QT_VERSION_STR, PYQT_VERSION_STR, qVersion)
        from PyQt5.QtGui import QPalette
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtQml import QQmlApplicationEngine
        from PyQt5.QtQuick import QQuickWindow
    try:
        quick_style_api = importlib.import_module(f'PyQt{args.qt_major}.QtQuickControls2').QQuickStyle
    except ImportError:
        quick_style_api = None  # Optional diagnostic binding, not a rendering dependency.
    display_role = int(Qt.ItemDataRole.DisplayRole)

    class ArtificialTable(QAbstractTableModel):
        def rowCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else 60

        def columnCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else 3

        def data(self, index, role=display_role):
            if index.isValid() and role == display_role:
                return (f'Object {index.row() + 1}', 'Available', str(index.row() * 3))[index.column()]
            return None

        def roleNames(self):
            return {display_role: b'display'}

    app = QApplication(sys.argv[:1])
    app.setApplicationName(f'DomainOS Theme Preview — QtQuick{args.qt_major}')
    app.setDesktopFileName(f'org.irixclassic.preview.qtquick{args.qt_major}')
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o700)
    data_path = output / 'artificial-scroll-text.txt'
    data_path.write_text(('Native QtQuick ScrollView and TextArea: artificial content only. ' * 4 + '\n') * 45)
    data_path.chmod(0o600)
    qml_path = output / 'gallery.qml'
    qml_path.write_text(QML_SOURCE.replace('__MAJOR__', str(args.qt_major)))
    qml_path.chmod(0o600)
    record = {'scope': 'Owned bwrap/Xephyr preview only; native KDE QtQuick controls',
              'guards': guards, 'qtMajor': args.qt_major, 'qtVersion': QT_VERSION_STR,
              'qtRuntimeVersion': qVersion(), 'pyqtVersion': PYQT_VERSION_STR,
              'qmlSource': str(qml_path), 'dataSource': str(data_path),
              'actions': [], 'qmlWarnings': [], 'customDrawing': False,
              'paletteOverride': False, 'fontOverride': False}
    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda messages: record['qmlWarnings'].extend(str(message.toString()) for message in messages))
    model = ArtificialTable(engine)
    engine.rootContext().setContextProperty('galleryTableModel', model)
    engine.rootContext().setContextProperty('artificialText', data_path.read_text())
    engine.rootContext().setContextProperty('runtimeDescription', f'Qt {qVersion()} | org.kde.desktop')
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    roots = engine.rootObjects()
    if len(roots) != 1 or not isinstance(roots[0], QQuickWindow):
        raise RuntimeError('Native QtQuick gallery failed to load: ' + '; '.join(record['qmlWarnings']))
    window = roots[0]

    def qml_sources():
        sources = set()
        for node in (window, *window.findChildren(QObject)):
            context = engine.contextForObject(node)
            if context and not context.baseUrl().isEmpty():
                sources.add(context.baseUrl().toString())
        return sorted(sources)

    def save_proof(screenshot=False):
        palette = app.palette()
        groups = {'active': QPalette.ColorGroup.Active, 'inactive': QPalette.ColorGroup.Inactive,
                  'disabled': QPalette.ColorGroup.Disabled}
        roles = ('Window', 'WindowText', 'Base', 'Text', 'Button', 'ButtonText', 'Highlight', 'HighlightedText')
        sources = qml_sources()
        record.update(platform=app.platformName(), platformTheme=os.environ.get('QT_QPA_PLATFORMTHEME'),
                      quickStyle={'requested': os.environ['QT_QUICK_CONTROLS_STYLE'],
                                  'name': quick_style_api.name() if quick_style_api else None,
                                  'nameApiAvailable': quick_style_api is not None,
                                  'kdeDesktopQmlObserved': any('/org/kde/desktop/' in path or
                                                              '/org.kde.desktop/' in path for path in sources)},
                      loadedQmlContexts=sources,
                      widgetStyle={'objectName': app.style().objectName(), 'className': app.style().metaObject().className()},
                      font=app.font().toString(), nativeControlFont=window.property('nativeFont'),
                      selections=selection(),
                      palette={group: {role: palette.color(value, getattr(QPalette.ColorRole, role)).name()
                                       for role in roles} for group, value in groups.items()},
                      nativeControlPalettes=json.loads(window.property('nativePalettes')),
                      window={'objectName': window.objectName(), 'width': window.width(), 'height': window.height(),
                              'x': window.x(), 'y': window.y()},
                      apiLimits=['QtQuick ScrollBar has no native Motif arrow buttons.',
                                 'TableView uses native ItemDelegate cells, not historical TreeView geometry.'])
        if screenshot and window.isVisible():
            path = output / f'qtquick{args.qt_major}.png'
            record['screenshotSaved'] = window.grabWindow().save(str(path), 'PNG')
            record['screenshot'] = str(path)
        target = output / 'RESULTADO.json'
        target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
        target.chmod(0o600)

    def action_recorded(action, detail):
        record['actions'].append({'action': action, 'detail': detail})
        save_proof(action == 'capture')

    window.actionRecorded.connect(action_recorded)
    app.aboutToQuit.connect(lambda: save_proof(False))
    save_proof(False)
    # QA snapshot of this private window only; it never delays an interactive action.
    QTimer.singleShot(1000, lambda: save_proof(True))
    return app.exec()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, ImportError) as error:
        print('Private QtQuick demo refused: ' + str(error), file=sys.stderr)
        sys.exit(2)
