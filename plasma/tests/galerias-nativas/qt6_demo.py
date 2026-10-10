#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt6 Widgets/Kvantum controls, restricted to the owned bwrap preview.

No stylesheet, setStyle, setPalette, forced font or synthetic theme is used.
The launcher owns the namespace and public theme resources. This process reads
only its fake HOME configuration and its own process metadata.
"""
from pathlib import Path
import argparse
import configparser
import json
import os
import pwd
import shutil
import subprocess
import sys


def private_guards():
    expected_home = Path('/home/domainos-test')
    failures = []
    if os.environ.get('PRIVATE_XEPHYR') != '1':
        failures.append('PRIVATE_XEPHYR=1 required')
    if os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') != 'bwrap':
        failures.append('owned bwrap namespace marker required')
    if os.environ.get('HOME') != str(expected_home):
        failures.append('fake HOME /home/domainos-test required')
    try:
        entry = pwd.getpwuid(os.getuid())
        if entry.pw_name != 'domainos-test' or entry.pw_dir != str(expected_home):
            failures.append('fake passwd entry does not match UID/HOME')
    except KeyError:
        failures.append('fake passwd entry absent')
    if os.environ.get('XDG_RUNTIME_DIR') != '/run/user/1000':
        failures.append('private /run/user/1000 required')
    for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME'):
        value = Path(os.environ.get(key, '/'))
        if not value.is_absolute() or not value.is_relative_to(expected_home):
            failures.append(key + ' must be inside fake HOME')
    if not Path('/etc/domainos-preview').is_file():
        failures.append('public namespace marker absent')
    if not Path('/home').is_dir() or set(Path('/home').iterdir()) != {expected_home}:
        failures.append('HOME directories outside the disposable profile are exposed')
    if Path('/run/dbus/system_bus_socket').exists():
        failures.append('host system bus socket is exposed')
    if not Path('/proc/self/status').is_file() or not Path('/proc/self/maps').is_file():
        failures.append('private proc is required')
    display = os.environ.get('DISPLAY', '')
    if not display.startswith(':') or not os.environ.get('XAUTHORITY'):
        failures.append('owned X display and authority required')
    if not os.environ.get('DBUS_SESSION_BUS_ADDRESS', '').startswith('unix:'):
        failures.append('private session bus required')
    if failures:
        raise RuntimeError('; '.join(failures))
    return {'verified': True, 'uid': os.getuid(), 'passwdName': entry.pw_name,
            'passwdHome': entry.pw_dir, 'namespaceMarker': '/etc/domainos-preview',
            'personalHomeExposed': False, 'systemBusSocketExposed': False,
            'procStatusPresent': True, 'cwd': str(Path.cwd())}


def selection():
    values = {}
    base = Path(os.environ['XDG_CONFIG_HOME'])
    for filename, sections in (
        ('kdeglobals', {'KDE': ['widgetStyle', 'LookAndFeelPackage'],
                        'General': ['ColorScheme', 'font'], 'Icons': ['Theme']}),
        ('Kvantum/kvantum.kvconfig', {'General': ['theme']}),
        ('plasmarc', {'Theme': ['name']}),
        ('kcminputrc', {'Mouse': ['cursorTheme', 'cursorSize']})):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        parser.read(base / filename, encoding='utf-8')
        values[filename] = {section: {key: parser.get(section, key, fallback=None)
                            for key in keys} for section, keys in sections.items()}
    return values


def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('--output', type=Path, default=Path('/home/domainos-test/qtwidgets-proof'))
    arguments.add_argument('--guard-only', action='store_true')
    args = arguments.parse_args()
    guards = private_guards()  # Must run BEFORE importing/initializing Qt.
    output = args.output.absolute()
    if not output.is_relative_to(Path('/home/domainos-test')):
        raise RuntimeError('Proof output must remain inside fake HOME')
    if args.guard_only:
        print(json.dumps(guards, sort_keys=True))
        return 0
    output.mkdir(parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    from PyQt6.QtCore import Qt, QT_VERSION_STR, PYQT_VERSION_STR, QTimer
    from PyQt6.QtGui import QAction, QPalette
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
        QGroupBox, QPushButton, QCheckBox, QRadioButton, QComboBox, QSpinBox,
        QDoubleSpinBox, QLineEdit, QTextEdit, QSlider, QProgressBar, QTabWidget,
        QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
        QScrollArea, QToolButton)
    app = QApplication(sys.argv[:1])
    app.setApplicationName('DomainOS Theme Preview — Qt Widgets')
    app.setDesktopFileName('org.irixclassic.preview.qtwidgets')
    window = QMainWindow()
    window.setObjectName('privateQtWidgetsWindow')
    window.setWindowTitle('IRIX Classic — Qt6 Widgets / Kvantum')
    window.resize(500, 490)
    window.move(20, 80)
    central = QWidget()
    outer = QVBoxLayout(central)
    tabs = QTabWidget()
    outer.addWidget(tabs)
    status = QLabel('Real Qt controls; theme and palette come from the private KDE profile.')
    status.setWordWrap(True)
    outer.addWidget(status)
    window.setCentralWidget(central)
    actions = []
    processes = []
    record = {'scope': 'Owned bwrap/Xephyr preview only; no Qt style or palette override',
              'guards': guards, 'actions': actions}

    controls = QWidget()
    controls_layout = QVBoxLayout(controls)
    group = QGroupBox('Buttons and selection')
    group_layout = QHBoxLayout(group)
    button = QPushButton('Press')
    button.setObjectName('themePushButton')
    button.clicked.connect(lambda: status.setText('Push button clicked'))
    check = QCheckBox('Checked')
    check.setChecked(True)
    radio = QRadioButton('Radio')
    radio.setChecked(True)
    tool = QToolButton()
    tool.setText('Tool')
    tool.setCheckable(True)
    for widget in (button, check, radio, tool):
        group_layout.addWidget(widget)
    controls_layout.addWidget(group)
    form = QFormLayout()
    combo = QComboBox()
    combo.addItems(['Classic', 'DomainOS SR10.4', 'A long selectable menu option'])
    form.addRow('Combo:', combo)
    numeric = QWidget()
    numeric_layout = QHBoxLayout(numeric)
    numeric_layout.setContentsMargins(0, 0, 0, 0)
    spin = QSpinBox()
    spin.setRange(-99, 999)
    spin.setValue(42)
    decimal = QDoubleSpinBox()
    decimal.setValue(10.4)
    numeric_layout.addWidget(spin)
    numeric_layout.addWidget(decimal)
    form.addRow('Spin boxes:', numeric)
    text = QLineEdit('Editable text')
    text.setObjectName('themeLineEdit')
    form.addRow('Text:', text)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(43)
    form.addRow('Slider:', slider)
    progress = QProgressBar()
    progress.setValue(43)
    slider.valueChanged.connect(progress.setValue)
    form.addRow('Progress:', progress)
    controls_layout.addLayout(form)
    editor = QTextEdit('Multiline editor\nSelect text, open menus and hold buttons to inspect the actual relief.')
    controls_layout.addWidget(editor)
    tabs.addTab(controls, 'Controls')

    table = QTableWidget(40, 3)
    table.setHorizontalHeaderLabels(['Item', 'State', 'Value'])
    for row in range(40):
        for column, value in enumerate((f'Object {row + 1}', 'Available', str(row * 3))):
            table.setItem(row, column, QTableWidgetItem(value))
    table.setSortingEnabled(True)
    tabs.addTab(table, 'Table')
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    long_content = QWidget()
    long_layout = QVBoxLayout(long_content)
    for index in range(24):
        long_layout.addWidget(QPushButton(f'Scrollable button {index + 1}'))
    scroll.setWidget(long_content)
    tabs.addTab(scroll, 'Scroll')
    dialogs = QWidget()
    dialogs_layout = QVBoxLayout(dialogs)
    instructions = QLabel('Dialogs and System Settings run inside the same private namespace, HOME, display and session bus.')
    instructions.setWordWrap(True)
    dialogs_layout.addWidget(instructions)
    file_button = QPushButton('Open QFileDialog')
    settings_button = QPushButton('Open private System Settings')
    capture_button = QPushButton('Save this window screenshot and JSON')
    dialogs_layout.addWidget(file_button)
    dialogs_layout.addWidget(settings_button)
    dialogs_layout.addWidget(capture_button)
    dialogs_layout.addStretch(1)
    tabs.addTab(dialogs, 'Dialogs')

    def save_proof(screenshot=False):
        palette = app.palette()
        groups = {'active': QPalette.ColorGroup.Active, 'inactive': QPalette.ColorGroup.Inactive,
                  'disabled': QPalette.ColorGroup.Disabled}
        roles = ['Window', 'WindowText', 'Base', 'Text', 'Button', 'ButtonText', 'Highlight', 'HighlightedText']
        loaded = []
        for line in Path('/proc/self/maps').read_text().splitlines():
            if 'kvantum' in line.lower():
                pieces = line.split(maxsplit=5)
                if len(pieces) == 6 and pieces[-1] not in loaded:
                    loaded.append(pieces[-1])
        record.update(qtVersion=QT_VERSION_STR, pyqtVersion=PYQT_VERSION_STR,
                      platform=app.platformName(), platformTheme=os.environ.get('QT_QPA_PLATFORMTHEME'),
                      style={'objectName': app.style().objectName(), 'className': app.style().metaObject().className()},
                      font=app.font().toString(), selections=selection(), loadedKvantum=loaded,
                      palette={group: {role: palette.color(value, getattr(QPalette.ColorRole, role)).name()
                                       for role in roles} for group, value in groups.items()},
                      window={'width': window.width(), 'height': window.height(),
                              'x': window.x(), 'y': window.y()},
                      apiLimits=['Qt Widgets has no native switch control; QCheckBox is the standard boolean widget.'])
        if screenshot and window.isVisible():
            image_path = output / 'qtwidgets.png'
            record['screenshotSaved'] = window.grab().save(str(image_path), 'PNG')
            record['screenshot'] = str(image_path)
        target = output / 'RESULTADO.json'
        target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
        target.chmod(0o600)

    def open_file():
        private_guards()
        actions.append({'action': 'QFileDialog', 'request': 'open'})
        chosen, _ = QFileDialog.getOpenFileName(window, 'Private theme file dialog', '/home/domainos-test')
        actions.append({'action': 'QFileDialog', 'outcome': 'selected' if chosen else 'cancelled'})
        # Only record the outcome; do not log selected private filenames.
        status.setText('Private file dialog completed')
        save_proof()

    def open_settings():
        private_guards()
        executable = shutil.which('systemsettings')
        if not executable:
            status.setText('System Settings is unavailable in this namespace')
            return
        process = subprocess.Popen([executable], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   close_fds=True, cwd='/home/domainos-test')
        processes.append(process)
        actions.append({'action': 'System Settings', 'pid': process.pid,
                        'scope': 'normal subprocess; inherited private environment'})
        status.setText('Private System Settings process requested')
        save_proof()

    file_button.clicked.connect(open_file)
    settings_button.clicked.connect(open_settings)
    capture_button.clicked.connect(lambda: save_proof(True))
    menu = window.menuBar().addMenu('&File')
    file_action = QAction('Open file dialog...', window)
    file_action.triggered.connect(open_file)
    menu.addAction(file_action)
    settings_action = QAction('Private System Settings...', window)
    settings_action.triggered.connect(open_settings)
    menu.addAction(settings_action)
    menu.addSeparator()
    checked_action = QAction('Checkable native QAction', window)
    checked_action.setCheckable(True)
    checked_action.setChecked(True)
    menu.addAction(checked_action)
    disabled_action = QAction('Disabled native QAction', window)
    disabled_action.setEnabled(False)
    menu.addAction(disabled_action)
    submenu = menu.addMenu('Submenu')
    submenu.addAction('Submenu item').triggered.connect(lambda: status.setText('Native submenu action clicked'))
    menu.addSeparator()
    menu.addAction('Close').triggered.connect(window.close)
    help_menu = window.menuBar().addMenu('&Help')
    help_menu.addAction('About this private demo').triggered.connect(lambda: QMessageBox.information(
        window, 'Private Qt Widgets demo', 'Real Qt Widgets rendered by the selected private KDE/Kvantum style.'))
    app.aboutToQuit.connect(lambda: save_proof(False))
    window.show()
    # QA snapshot only. No timer controls interactive actions or production UI.
    QTimer.singleShot(1000, lambda: save_proof(True))
    return app.exec()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError) as error:
        print('Private Qt Widgets demo refused: ' + str(error), file=sys.stderr)
        sys.exit(2)
