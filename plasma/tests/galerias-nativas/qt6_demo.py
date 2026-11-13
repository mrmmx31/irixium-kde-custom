#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt5/Qt6 Widgets/Kvantum controls in an owned private preview.

No stylesheet, setStyle, setPalette, forced font or synthetic theme is used.
The launcher owns either a bwrap profile or a Theme Lab direct private profile.
This process never writes to the user's personal HOME/XDG directories.
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


class PreviewShutdown:
    """Idempotent teardown for native windows that may be X11-reparented.

    After reparenting, ``window.close()`` alone does not reliably make Qt see
    the window as its last top-level.  Keep cleanup independent from that Qt
    heuristic and explicitly leave the event loop.
    """

    def __init__(self, app, window):
        self.app = app
        self.window = window
        self.timer = None
        self.bridge = None
        self.requested = False

    def set_timer(self, timer):
        self.timer = timer

    def set_bridge(self, bridge):
        self.bridge = bridge

    def cleanup(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        if self.bridge is not None:
            self.bridge.close()
            self.bridge = None

    def request(self):
        if self.requested:
            return False
        self.requested = True
        self.cleanup()
        self.window.close()
        self.app.quit()
        return True


def fixture_root():
    return Path(os.environ.get('IRIX_DOMAINOS_FIXTURE_ROOT', '/fixture/root')).resolve()


def private_home():
    return Path(os.environ.get('HOME', '/home/domainos-test')).resolve()


def private_guards():
    if os.environ.get('IRIX_DOMAINOS_DIRECT_PREVIEW') == '1':
        from demo_env import require_private_session
        require_private_session()
        root = fixture_root()
        if not (root / 'tools/theme-lab/backend.py').is_file():
            raise RuntimeError('Theme Lab fixture root is unavailable')
        return {'verified': True, 'uid': os.getuid(),
                'mode': 'explicit_user_session_direct',
                'sessionRoot': os.environ['IRIX_DOMAINOS_SESSION_ROOT'],
                'privateHome': str(private_home()), 'fixtureRoot': str(root),
                'personalHomeExposed': False, 'personalProfileWritten': False,
                'systemBusSocketExposed': False,
                'procStatusPresent': Path('/proc/self/status').is_file(),
                'cwd': str(Path.cwd())}
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


def main(argv=None, default_qt_major=6):
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('--qt-major', type=int, choices=(5, 6), default=default_qt_major)
    arguments.add_argument('--output', type=Path)
    arguments.add_argument('--guard-only', action='store_true')
    arguments.add_argument('--theme-lab-scrollbar-snapshot', type=Path)
    arguments.add_argument('--theme-lab-qt5-scrollbar-snapshot', type=Path)
    arguments.add_argument('--theme-lab-kvantum-snapshot', type=Path)
    arguments.add_argument('--theme-lab-kvantum-root', type=Path, default=Path('/fixture/root'))
    arguments.add_argument('--theme-lab-project', type=Path)
    arguments.add_argument('--theme-lab-test-close-ms', type=int)
    arguments.add_argument('--embed-window', type=lambda value: int(value, 0))
    arguments.add_argument('--host-pid', type=int)
    arguments.add_argument('--host-bridge', type=Path)
    arguments.add_argument('--host-session-root', type=Path)
    args = arguments.parse_args(argv)
    guards = private_guards()  # Must run BEFORE importing/initializing Qt.
    embedded = args.embed_window is not None
    if embedded != bool(args.host_pid and args.host_bridge and args.host_session_root):
        raise RuntimeError('Embedding requires canvas, host PID, host bridge and private session root together')
    if embedded and args.host_session_root.resolve(strict=True) != Path(
            os.environ['IRIX_DOMAINOS_SESSION_ROOT']).resolve(strict=True):
        raise RuntimeError('Embedding host and child must share the same private Theme Lab session')
    proof_name = 'qtwidgets-proof' if args.qt_major == 6 else 'qt5widgets-proof'
    home = private_home()
    output = (args.output or home / proof_name).absolute()
    if not output.is_relative_to(Path(os.environ.get('IRIX_DOMAINOS_SESSION_ROOT', home)).resolve()):
        raise RuntimeError('Proof output must remain inside the private Theme Lab session')
    if args.guard_only:
        print(json.dumps(guards, sort_keys=True))
        return 0
    scrollbar_recipe = None
    qt5_scrollbar_recipe = None
    qt6_push_recipe = False
    qt6_toggle_recipe = False
    qt6_check_recipe = False
    qt6_radio_recipe = False
    qt6_entry_recipe = False
    qt6_text_recipe = False
    qt6_combo_recipe = False
    qt6_spin_recipe = False
    qt6_scale_recipe = False
    qt6_scale_v_recipe = False
    qt6_arrow_recipe = False
    qt6_progress_recipe = False
    qt6_list_recipe = False
    qt6_scale_backdrop_tracker = None
    qt6_arrow_backdrop_tracker = None
    qt6_list_backdrop_tracker = None
    qt6_frame_backdrop_tracker = None
    qt5_arrow_button_class = None
    qt6_arrow_button_class = None
    qt6_progress_bar_class = None
    qt5_progress_bar_class = None
    kvantum_recipe = None
    if args.theme_lab_scrollbar_snapshot is not None:
        if args.qt_major != 6 or args.theme_lab_project is None:
            raise RuntimeError('The DomainOS scrollbar snapshot requires Qt6 and its saved project.')
        lab = fixture_root() / 'tools/theme-lab'
        sys.path.insert(0, str(lab))
        import backend as theme_backend
        from qt6_scrollbar_recipe import verify as verify_qt6_scrollbar
        from qt6_arrow_widget import RecipeArrowButton as Qt6RecipeArrowButton
        from qt6_progress_widget import RecipeProgressBar as Qt6RecipeProgressBar
        qt6_arrow_button_class = Qt6RecipeArrowButton
        qt6_progress_bar_class = Qt6RecipeProgressBar
        model, _digest = theme_backend.project(args.theme_lab_project)
        snapshot = args.theme_lab_scrollbar_snapshot.absolute()
        proposal = json.loads(theme_backend.read_file(snapshot / 'QT6-SCROLLBAR-PROPOSAL.json'))
        scrollbar_recipe = verify_qt6_scrollbar(fixture_root(), proposal, model)
        qt6_push_recipe = 'push' in scrollbar_recipe.get('translated_controls', [])
        qt6_toggle_recipe = 'toggle' in scrollbar_recipe.get('translated_controls', [])
        qt6_check_recipe = 'check' in scrollbar_recipe.get('translated_controls', [])
        qt6_radio_recipe = 'radio' in scrollbar_recipe.get('translated_controls', [])
        qt6_entry_recipe = 'entry' in scrollbar_recipe.get('translated_controls', [])
        qt6_text_recipe = 'text' in scrollbar_recipe.get('translated_controls', [])
        qt6_combo_recipe = 'combo' in scrollbar_recipe.get('translated_controls', [])
        qt6_spin_recipe = 'spin' in scrollbar_recipe.get('translated_controls', [])
        qt6_scale_recipe = 'scale_h' in scrollbar_recipe.get('translated_controls', [])
        qt6_scale_v_recipe = 'scale_v' in scrollbar_recipe.get('translated_controls', [])
        qt6_arrow_recipe = 'arrow' in scrollbar_recipe.get('translated_controls', [])
        qt6_progress_recipe = 'progress' in scrollbar_recipe.get('translated_controls', [])
        qt6_list_recipe = 'list' in scrollbar_recipe.get('translated_controls', [])
        qt6_frame_recipe = 'frame' in scrollbar_recipe.get('translated_controls', [])
    else:
        qt6_frame_recipe = False
    if args.theme_lab_qt5_scrollbar_snapshot is not None:
        if args.qt_major != 5 or args.theme_lab_project is None:
            raise RuntimeError('The DomainOS scrollbar snapshot requires Qt5 and its saved project.')
        lab = fixture_root() / 'tools/theme-lab'
        sys.path.insert(0, str(lab))
        import backend as theme_backend
        from qt5_scrollbar_recipe import verify as verify_qt_scrollbar
        from qt5_arrow_widget import RecipeArrowButton
        from qt5_progress_widget import RecipeProgressBar
        qt5_arrow_button_class = RecipeArrowButton
        qt5_progress_bar_class = RecipeProgressBar
        model, _digest = theme_backend.project(args.theme_lab_project)
        snapshot = args.theme_lab_qt5_scrollbar_snapshot.absolute()
        proposal = json.loads(theme_backend.read_file(snapshot / 'QT5-SCROLLBAR-PROPOSAL.json'))
        qt5_scrollbar_recipe = verify_qt_scrollbar(fixture_root(), proposal, model)
    if args.theme_lab_kvantum_snapshot is not None:
        if args.qt_major != 6 or args.theme_lab_project is None:
            raise RuntimeError('The Kvantum recipe requires Qt6 and its saved project.')
        root = args.theme_lab_kvantum_root.absolute()
        lab = root / 'tools/theme-lab'
        sys.path.insert(0, str(lab))
        import backend as theme_backend
        from kvantum_route import verify as verify_kvantum
        model, _digest = theme_backend.project(args.theme_lab_project)
        proposal = json.loads(theme_backend.read_file(args.theme_lab_kvantum_snapshot))
        kvantum_recipe = verify_kvantum(root, proposal, model)
        selected_theme = selection()['Kvantum/kvantum.kvconfig']['General']['theme']
        if selected_theme != kvantum_recipe['theme_name']:
            raise RuntimeError('The private Kvantum selector does not match its generated recipe.')
    if (args.theme_lab_test_close_ms is not None and scrollbar_recipe is None and
            qt5_scrollbar_recipe is None and kvantum_recipe is None):
        raise RuntimeError('The test close timer requires a verified private scrollbar recipe.')
    output.mkdir(parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    if args.qt_major == 6:
        from PyQt6.QtCore import QEvent, QObject, Qt, QItemSelectionModel, QT_VERSION_STR, PYQT_VERSION_STR, QTimer, qVersion
        from PyQt6.QtGui import QAction, QPalette
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QButtonGroup,
            QGroupBox, QPushButton, QCheckBox, QRadioButton, QComboBox, QSpinBox,
            QDoubleSpinBox, QLineEdit, QTextEdit, QSlider, QProgressBar, QTabWidget,
            QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
            QScrollArea, QToolButton, QFrame, QAbstractItemView, QTreeWidget,
            QTreeWidgetItem)
    else:
        from PyQt5.QtCore import Qt, QItemSelectionModel, QT_VERSION_STR, PYQT_VERSION_STR, QTimer, qVersion
        from PyQt5.QtGui import QPalette
        from PyQt5.QtWidgets import (
            QAction, QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QFormLayout, QGroupBox, QButtonGroup, QPushButton, QCheckBox, QRadioButton, QComboBox,
            QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit, QSlider, QProgressBar,
            QTabWidget, QLabel, QFileDialog, QMessageBox, QTableWidget,
            QTableWidgetItem, QScrollArea, QToolButton, QFrame,
            QAbstractItemView, QTreeWidget, QTreeWidgetItem)
    app = QApplication(sys.argv[:1])
    app.setApplicationName('DomainOS Theme Preview — Qt Widgets' if args.qt_major == 6
                           else 'DomainOS Theme Preview — Qt5 Widgets')
    app.setDesktopFileName('org.irixclassic.preview.qtwidgets' if args.qt_major == 6
                           else 'org.irixclassic.preview.qt5widgets')
    if kvantum_recipe:
        style_class = app.style().metaObject().className().lower()
        loaded = any('kvantum' in line.lower() for line in Path('/proc/self/maps').read_text().splitlines())
        if 'kvantum' not in style_class or not loaded:
            raise RuntimeError('Kvantum QStyle or generated theme was not loaded by the native Qt application.')
    window = QMainWindow()
    window.setObjectName('privateQtWidgetsWindow' if args.qt_major == 6
                         else 'privateQt5WidgetsWindow')
    if embedded:
        frameless = (Qt.WindowType.FramelessWindowHint if args.qt_major == 6
                     else Qt.FramelessWindowHint)
        window.setWindowFlag(frameless, True)
    global_theme = selection()['kdeglobals']['KDE']['LookAndFeelPackage']
    theme_title = ('DomainOS SR10.4' if global_theme == 'org.magpie.irixclassic.domainos.desktop'
                   else 'IRIX Classic')
    window.setWindowTitle(theme_title + f' — Qt{args.qt_major} Widgets / Kvantum')
    window.resize(500, 490)
    window.move(520 if kvantum_recipe else 20, 80)
    central = QWidget()
    outer = QVBoxLayout(central)
    tabs = QTabWidget()
    outer.addWidget(tabs)
    status = QLabel('Real Qt controls; theme and palette come from the private KDE profile.')
    status.setObjectName('qtGalleryStatus')
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
    qt5_push_recipe = bool(qt5_scrollbar_recipe and
                           'push' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_toggle_recipe = bool(qt5_scrollbar_recipe and
                             'toggle' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_check_recipe = bool(qt5_scrollbar_recipe and
                            'check' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_radio_recipe = bool(qt5_scrollbar_recipe and
                            'radio' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_entry_recipe = bool(qt5_scrollbar_recipe and
                            'entry' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_text_recipe = bool(qt5_scrollbar_recipe and
                           'text' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_combo_recipe = bool(qt5_scrollbar_recipe and
                            'combo' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_spin_recipe = bool(qt5_scrollbar_recipe and
                           'spin' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_scale_recipe = bool(qt5_scrollbar_recipe and
                            {'scale_h', 'scale_v'}.intersection(qt5_scrollbar_recipe.get('translated_controls', [])))
    qt5_arrow_recipe = bool(qt5_scrollbar_recipe and
                            'arrow' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_progress_recipe = bool(qt5_scrollbar_recipe and
                               'progress' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_list_recipe = bool(qt5_scrollbar_recipe and
                           'list' in qt5_scrollbar_recipe.get('translated_controls', []))
    qt5_frame_recipe = bool(qt5_scrollbar_recipe and
                            'frame' in qt5_scrollbar_recipe.get('translated_controls', []))
    button.setObjectName('domainosRecipePushButton' if (qt5_push_recipe or qt6_push_recipe) else
                         'themePushButton' if args.qt_major == 6 else 'qt5ThemePushButton')
    button.clicked.connect(lambda: status.setText('Push button clicked'))
    toggle_button = QPushButton('Toggle')
    toggle_button.setCheckable(True)
    toggle_button.setObjectName('domainosRecipeToggleButton' if (qt5_toggle_recipe or qt6_toggle_recipe) else
                                'themeToggleButton' if args.qt_major == 6 else 'qt5ThemeToggleButton')
    toggle_button.toggled.connect(lambda checked: status.setText(
        'Toggle selected' if checked else 'Toggle released'))
    check = QCheckBox('Checked')
    check.setChecked(True)
    check.setObjectName('domainosRecipeCheckBox' if (qt5_check_recipe or qt6_check_recipe) else
                        'themeCheckBox' if args.qt_major == 6 else 'qt5ThemeCheckBox')
    radio = QRadioButton('Radio')
    radio.setChecked(True)
    radio.setObjectName('domainosRecipeRadioButton' if (qt5_radio_recipe or qt6_radio_recipe) else
                        'themeRadioButton' if args.qt_major == 6 else 'qt5ThemeRadioButton')
    radio_peer = QRadioButton('Radio B') if (qt5_radio_recipe or qt6_radio_recipe) else None
    radio_group = QButtonGroup(group) if (qt5_radio_recipe or qt6_radio_recipe) else None
    if radio_peer is not None:
        radio_peer.setObjectName('domainosRecipeRadioPeer')
        radio_group.setExclusive(True)
        radio_group.addButton(radio)
        radio_group.addButton(radio_peer)
    tool = QToolButton()
    tool.setText('Tool')
    tool.setCheckable(True)
    recipe_arrow = None
    if qt5_arrow_recipe or qt6_arrow_recipe:
        active_arrow_class = qt6_arrow_button_class if qt6_arrow_recipe else qt5_arrow_button_class
        active_arrow_recipe_data = scrollbar_recipe if qt6_arrow_recipe else qt5_scrollbar_recipe
        recipe_arrow = active_arrow_class(
            active_arrow_recipe_data['asset_dir'],
            active_arrow_recipe_data['geometry']['shadow_px'])
        recipe_arrow.setObjectName('domainosRecipeArrow')
        recipe_arrow.setToolTip('Seta isolada; tamanho em pixels da receita. Cliques e foco permanecem nativos do Qt.')
        recipe_arrow.clicked.connect(lambda: status.setText('Arrow button clicked'))
        if qt6_arrow_recipe:
            from qt6_scale_widget import WindowBackdropTracker
            qt6_arrow_backdrop_tracker = WindowBackdropTracker(window, recipe_arrow)
            window.installEventFilter(qt6_arrow_backdrop_tracker)
    controls_widgets = [button, toggle_button, check, radio]
    if radio_peer is not None:
        controls_widgets.append(radio_peer)
    controls_widgets.append(tool)
    if recipe_arrow is not None:
        controls_widgets.append(recipe_arrow)
    for widget in controls_widgets:
        group_layout.addWidget(widget)
    controls_layout.addWidget(group)
    form = QFormLayout()
    combo = QComboBox()
    combo.addItems(['Classic', 'DomainOS SR10.4', 'A long selectable menu option'])
    combo.setObjectName('domainosRecipeCombo' if (qt5_combo_recipe or qt6_combo_recipe) else
                        'themeCombo' if args.qt_major == 6 else 'qt5ThemeCombo')
    if qt5_combo_recipe or qt6_combo_recipe:
        combo.view().setObjectName('domainosRecipeComboPopup')
    form.addRow('Combo:', combo)
    numeric = QWidget()
    numeric_layout = QHBoxLayout(numeric)
    numeric_layout.setContentsMargins(0, 0, 0, 0)
    spin = QSpinBox()
    spin.setRange(-99, 999)
    spin.setValue(42)
    spin.setObjectName('domainosRecipeSpinBox' if (qt5_spin_recipe or qt6_spin_recipe)
                       else 'themeSpinBox' if args.qt_major == 6 else 'qt5ThemeSpinBox')
    decimal = QDoubleSpinBox()
    decimal.setValue(10.4)
    decimal.setObjectName('domainosRecipeDoubleSpinBox' if (qt5_spin_recipe or qt6_spin_recipe)
                          else 'themeDoubleSpinBox' if args.qt_major == 6 else 'qt5ThemeDoubleSpinBox')
    numeric_layout.addWidget(spin)
    numeric_layout.addWidget(decimal)
    form.addRow('Spin boxes:', numeric)
    text = QLineEdit('Editable text')
    text.setObjectName('domainosRecipeEntry' if (qt5_entry_recipe or qt6_entry_recipe) else
                       'themeLineEdit' if args.qt_major == 6 else 'qt5ThemeLineEdit')
    form.addRow('Text:', text)
    scale_row = QWidget()
    scale_layout = QHBoxLayout(scale_row)
    scale_layout.setContentsMargins(0, 0, 0, 0)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(43)
    slider.setObjectName('domainosRecipeScaleHorizontal' if (qt5_scale_recipe or qt6_scale_recipe) else
                         'themeScaleHorizontal' if args.qt_major == 6 else 'qt5ThemeScaleHorizontal')
    if qt6_scale_recipe:
        from qt6_scale_widget import WindowBackdropTracker
        qt6_scale_backdrop_tracker = WindowBackdropTracker(window, slider)
        window.installEventFilter(qt6_scale_backdrop_tracker)
    vertical_slider = QSlider(Qt.Orientation.Vertical)
    vertical_slider.setRange(0, 100)
    vertical_slider.setValue(38)
    vertical_slider.setMinimumHeight(80)
    vertical_slider.setObjectName('domainosRecipeScaleVertical' if (qt5_scale_recipe or qt6_scale_v_recipe) else
                                  'themeScaleVertical' if args.qt_major == 6 else 'qt5ThemeScaleVertical')
    if qt6_scale_v_recipe:
        from qt6_scale_widget import WindowBackdropTracker
        qt6_scale_v_backdrop_tracker = WindowBackdropTracker(window, vertical_slider)
        window.installEventFilter(qt6_scale_v_backdrop_tracker)
    else:
        qt6_scale_v_backdrop_tracker = None
    scale_layout.addWidget(slider, 1)
    scale_layout.addWidget(vertical_slider)
    form.addRow('Slider:', scale_row)
    progress = (qt6_progress_bar_class() if qt6_progress_recipe else
                qt5_progress_bar_class() if qt5_progress_recipe else QProgressBar())
    progress.setValue(43)
    if qt5_progress_recipe or qt6_progress_recipe:
        progress.setObjectName('domainosRecipeProgress')
        progress.setFocusPolicy(Qt.StrongFocus if args.qt_major == 5 else Qt.FocusPolicy.StrongFocus)
    if qt6_progress_recipe:
        window.installEventFilter(progress)
    slider.valueChanged.connect(progress.setValue)
    form.addRow('Progress:', progress)
    controls_layout.addLayout(form)
    editor = QTextEdit('Multiline editor\nSelect text, open menus and hold buttons to inspect the actual relief.')
    editor.setObjectName('domainosRecipeText' if (qt5_text_recipe or qt6_text_recipe) else
                         'themeTextEdit' if args.qt_major == 6 else 'qt5ThemeTextEdit')
    if qt6_text_recipe:
        from qt6_scale_widget import WindowBackdropTracker
        qt6_text_backdrop_tracker = WindowBackdropTracker(window, editor)
        window.installEventFilter(qt6_text_backdrop_tracker)
    else:
        qt6_text_backdrop_tracker = None
    controls_layout.addWidget(editor)
    tabs.addTab(controls, 'Controls')

    table = QTableWidget(40, 3)
    table.setHorizontalHeaderLabels(['Item', 'State', 'Value'])
    for row in range(40):
        for column, value in enumerate((f'Object {row + 1}', 'Available', str(row * 3))):
            table.setItem(row, column, QTableWidgetItem(value))
    table.setSortingEnabled(True)
    tabs.addTab(table, 'Table')
    listing = None
    if qt5_list_recipe or qt6_list_recipe:
        listing = QTreeWidget()
        listing.setObjectName('domainosRecipeList')
        listing.setHeaderHidden(True)
        listing.setRootIsDecorated(False)
        listing.setItemsExpandable(False)
        listing.setUniformRowHeights(True)
        if args.qt_major == 6:
            listing.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            listing.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        else:
            listing.setSelectionMode(QAbstractItemView.SingleSelection)
            listing.setSelectionBehavior(QAbstractItemView.SelectRows)
        scroll_always_on = (Qt.ScrollBarPolicy.ScrollBarAlwaysOn if args.qt_major == 6
                            else Qt.ScrollBarAlwaysOn)
        listing.setVerticalScrollBarPolicy(scroll_always_on)
        listing.setHorizontalScrollBarPolicy(scroll_always_on)
        for index in range(40):
            item = QTreeWidgetItem(
                [f'Item {index + 1:02d} — selectable row — long content for horizontal scrolling'])
            listing.addTopLevelItem(item)
        listing.setColumnWidth(0, 620)
        listing.setCurrentItem(listing.topLevelItem(0))
        listing.topLevelItem(0).setSelected(True)
        listing.verticalScrollBar().setObjectName('domainosScrollBarVertical')
        listing.horizontalScrollBar().setObjectName('domainosScrollBarHorizontal')
        listing.setToolTip('Lista Qt real: selecione uma linha; use as barras para percorrer o conteúdo.')
        if qt6_list_recipe:
            from qt6_scale_widget import WindowBackdropTracker
            qt6_list_backdrop_tracker = WindowBackdropTracker(window, listing)
            window.installEventFilter(qt6_list_backdrop_tracker)
        listing.currentItemChanged.connect(
            lambda current, _previous: status.setText(
                'List row selected' if current is not None else 'No list row selected'))
        tabs.addTab(listing, 'List')
    framed = None
    if qt5_frame_recipe or qt6_frame_recipe:
        frame_recipe = scrollbar_recipe if qt6_frame_recipe else qt5_scrollbar_recipe
        framed = QFrame()
        framed.setObjectName('domainosRecipeFrame')
        if args.qt_major == 6:
            framed.setFrameShape(QFrame.Shape.Panel)
            framed.setFrameShadow(QFrame.Shadow.Sunken)
        else:
            framed.setFrameShape(QFrame.Panel)
            framed.setFrameShadow(QFrame.Sunken)
        framed.setLineWidth(frame_recipe['geometry']['shadow_px'])
        frame_layout = QVBoxLayout(framed)
        frame_layout.addWidget(QLabel('Conteúdo'))
        framed.setToolTip('Moldura QFrame real; relevo e cores vêm dos papéis KDE ativos.')
        if qt6_frame_recipe:
            from qt6_scale_widget import WindowBackdropTracker
            qt6_frame_backdrop_tracker = WindowBackdropTracker(window, framed)
            window.installEventFilter(qt6_frame_backdrop_tracker)
        tabs.addTab(framed, 'Frame')
    scroll = QScrollArea()
    scroll.setObjectName('domainosKvantumScrollArea' if kvantum_recipe else
                         'domainosScrollArea' if scrollbar_recipe else 'nativeScrollArea')
    scroll.setWidgetResizable(True)
    long_content = QWidget()
    long_layout = QVBoxLayout(long_content)
    for index in range(24):
        long_layout.addWidget(QPushButton(f'Scrollable button {index + 1}'))
    qt6_scroll_controls = bool(scrollbar_recipe and
                               {'scroll_h', 'scroll_v'}.intersection(
                                   scrollbar_recipe.get('translated_controls', [])))
    if qt6_scroll_controls or qt5_scrollbar_recipe or kvantum_recipe:
        # Force both native axes to exist so the 1:1 preview includes their
        # junction. The per-widget viewport-margin adapter makes the complete
        # viewport-to-bar distance four pixels, including the frame inset,
        # while leaving Kvantum's painting and palette intact.
        long_content.setMinimumSize(650, 620)
    if qt6_scroll_controls or qt5_scrollbar_recipe:
        selected_scrollbar_recipe = scrollbar_recipe if qt6_scroll_controls else qt5_scrollbar_recipe
        scroll.setFrameShape(QFrame.Shape.Box if args.qt_major == 6 else QFrame.Box)
        scroll.verticalScrollBar().setObjectName('domainosScrollBarVertical')
        scroll.horizontalScrollBar().setObjectName('domainosScrollBarHorizontal')
    scroll.setWidget(long_content)
    if qt6_scroll_controls:
        from qt6_scrollbar_widgets import install_scrollbar_painters
        install_scrollbar_painters(scroll, scrollbar_recipe['asset_dir'])
    if qt5_scrollbar_recipe:
        from qt5_scrollbar_widgets import install_scrollbar_painters
        install_scrollbar_painters(scroll, qt5_scrollbar_recipe['asset_dir'])
    tabs.addTab(scroll, 'Scroll')
    if qt6_scroll_controls or qt5_scrollbar_recipe or kvantum_recipe:
        # The scrollbar recipe preview must show the controls being measured;
        # hidden tabs report valid allocations but are not a visual preview.
        tabs.setCurrentWidget(scroll)
    elif qt5_list_recipe or qt6_list_recipe:
        tabs.setCurrentWidget(listing)
    scrollbar_spacing_adapters = []
    if qt6_scroll_controls or qt5_scrollbar_recipe:
        from qt_scrollbar_spacing import install_on_scroll_areas
        selected_scrollbar_recipe = scrollbar_recipe if qt6_scroll_controls else qt5_scrollbar_recipe
        scrollbar_spacing_adapters = install_on_scroll_areas(
            window, selected_scrollbar_recipe['geometry']['view_bar_gap_px'], args.qt_major)
    if scrollbar_recipe:
        qss_path = Path(scrollbar_recipe['css'])
        stylesheet = qss_path.read_text(encoding='utf-8')
        window.setStyleSheet(stylesheet)
        if qt6_scroll_controls:
            record['qt6ScrollbarRecipe'] = {
                'applied': True, 'scope': scrollbar_recipe['scope'],
                'projectSha256': scrollbar_recipe['project_sha256'],
                'recipeSha256': scrollbar_recipe['recipe_sha256'],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'geometry': scrollbar_recipe['geometry'],
                'states': scrollbar_recipe['states'],
                'scrollSpacingAdapters': scrollbar_spacing_adapters,
                'source': str(qss_path), 'limitations': scrollbar_recipe['limitations']}
        if qt6_push_recipe:
            record['qt6PushButtonRecipe'] = {
                'applied': True,
                'scope': 'one real QPushButton identified by its object name in this private Qt6 gallery window',
                'objectName': button.objectName(),
                'source': str(qss_path),
                'states': scrollbar_recipe['states'],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'sizeHint': [button.sizeHint().width(), button.sizeHint().height()],
                'limitations': ['The Qt6 stylesheet paints a real Qt button; this does not prove SR10.4 fidelity.']}
        if qt6_toggle_recipe:
            record['qt6ToggleButtonRecipe'] = {
                'applied': True,
                'scope': 'one real checkable QPushButton identified by its object name in this private Qt6 gallery window',
                'objectName': toggle_button.objectName(),
                'checkable': toggle_button.isCheckable(),
                'initiallyChecked': toggle_button.isChecked(),
                'source': str(qss_path),
                'states': ['released', 'checked-relief-locked', 'disabled'],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'sizeHint': [toggle_button.sizeHint().width(), toggle_button.sizeHint().height()],
                'limitations': ['The Qt6 stylesheet paints a real checkable Qt button; this does not prove SR10.4 fidelity.']}
        if qt6_check_recipe:
            record['qt6CheckBoxRecipe'] = {
                'applied': True,
                'scope': 'one real QCheckBox indicator identified by its object name in this private Qt6 gallery window',
                'objectName': check.objectName(),
                'checkable': check.isCheckable(),
                'initiallyChecked': check.isChecked(),
                'source': str(qss_path),
                'states': ['unchecked', 'checked', 'pressed', 'backdrop', 'disabled'],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'sizeHint': [check.sizeHint().width(), check.sizeHint().height()],
                'limitations': ['The Qt6 stylesheet paints a real QCheckBox indicator; this does not prove SR10.4 fidelity.']}
        if qt6_radio_recipe:
            record['qt6RadioButtonRecipe'] = {
                'applied': True,
                'scope': 'real exclusive QRadioButton pair identified by object names in this private Qt6 gallery window',
                'objectName': radio.objectName(),
                'checkable': radio.isCheckable(),
                'initiallyChecked': radio.isChecked(),
                'exclusiveGroup': radio_group.exclusive(),
                'peerObjectName': radio_peer.objectName(),
                'peerInitiallyChecked': radio_peer.isChecked(),
                'source': str(qss_path),
                'states': ['unchecked', 'checked', 'pressed', 'backdrop', 'disabled'],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'sizeHint': [radio.sizeHint().width(), radio.sizeHint().height()],
                'limitations': ['The Qt6 stylesheet paints real QRadioButton indicators; this does not prove SR10.4 fidelity.']}
        if qt6_entry_recipe:
            record['qt6EntryRecipe'] = {
                'applied': True,
                'scope': 'one real QLineEdit; Qt retains native editing, cursor, selection, undo/redo and clipboard shortcuts',
                'objectName': text.objectName(),
                'states': ['normal', 'focused', 'backdrop', 'disabled'],
                'source': str(qss_path),
                'sizeHint': [text.sizeHint().width(), text.sizeHint().height()],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'limitations': ['QSS state mapping does not establish historical SR10.4 fidelity.']}
        if qt6_text_recipe:
            record['qt6TextRecipe'] = {
                'applied': True,
                'scope': 'one real QTextEdit; Qt retains multiline UTF-8 editing, undo/redo, keyboard, selection and clipboard semantics',
                'objectName': editor.objectName(),
                'states': ['normal', 'focused', 'backdrop', 'disabled'],
                'backdropSelector': '[domainosBackdrop="true"]',
                'backdropTracksTopLevelActivation': qt6_text_backdrop_tracker is not None,
                'source': str(qss_path),
                'sizeHint': [editor.sizeHint().width(), editor.sizeHint().height()],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'limitations': ['QSS state mapping does not establish historical SR10.4 fidelity or full controller integration.']}
        if qt6_arrow_recipe:
            record['qt6ArrowRecipe'] = {
                'applied': True,
                'scope': 'one real QToolButton with recipe-owned KDE-role arrow pixels; Qt6 retains native click/focus semantics',
                'objectName': recipe_arrow.objectName(),
                'widgetClass': recipe_arrow.metaObject().className(),
                'glyphSize': scrollbar_recipe['geometry']['arrow_cell_px'],
                'size': [recipe_arrow.width(), recipe_arrow.height()],
                'states': ['normal', 'pressed while held', 'backdrop', 'disabled', 'focused'],
                'backdropSelector': '[domainosBackdrop="true"]',
                'backdropTracksTopLevelActivation': qt6_arrow_backdrop_tracker is not None,
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'limitations': ['This native-widget recipe is not a claim of historical SR10.4 fidelity.']}
        if qt6_progress_recipe:
            record['qt6ProgressRecipe'] = {
                'applied': True,
                'scope': 'one real QProgressBar; Qt retains range, fill fraction, text and value semantics',
                'objectName': progress.objectName(),
                'widgetClass': progress.metaObject().className(),
                'range': [progress.minimum(), progress.maximum()],
                'value': progress.value(),
                'text': progress.text(),
                'states': ['normal', 'backdrop', 'disabled', 'focused'],
                'textColorSource': 'KDE view ink role derived from the selected color scheme',
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'sizeHint': [progress.sizeHint().width(), progress.sizeHint().height()],
                'limitations': ['This real-widget recipe is not a claim of historical SR10.4 fidelity.']}
        if qt6_list_recipe:
            record['qt6ListRecipe'] = {
                'applied': True,
                'scope': 'real QTreeWidget/QTreeView with Qt6-native selection, keyboard/mouse input and internal scrollbars',
                'objectName': listing.objectName(),
                'widgetClass': listing.metaObject().className(),
                'rowCount': listing.topLevelItemCount(),
                'selectedRow': listing.indexOfTopLevelItem(listing.currentItem()),
                'selectionMode': 'single row',
                'states': ['normal', 'selected', 'focused', 'backdrop', 'disabled'],
                'backdropSelector': '[domainosBackdrop="true"]',
                'backdropTracksTopLevelActivation': qt6_list_backdrop_tracker is not None,
                'source': str(qss_path),
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'limitations': ['The QTreeView is a real Qt6 control; matching SR10.4 visual evidence is not implied.'],
                'nativeScrollbars': {}}
            for axis, widget in (('vertical', listing.verticalScrollBar()),
                                 ('horizontal', listing.horizontalScrollBar())):
                record['qt6ListRecipe']['nativeScrollbars'][axis] = {
                    'visible': widget.isVisible(), 'maximum': widget.maximum(),
                    'sizeHint': [widget.sizeHint().width(), widget.sizeHint().height()],
                    'objectName': widget.objectName(),
                    'widgetClass': widget.metaObject().className()}
        if qt6_combo_recipe:
            record['qt6ComboRecipe'] = {
                'applied': True,
                'scope': 'one real QComboBox and native QAbstractItemView popup; Qt retains selection and keyboard/mouse behavior',
                'objectName': combo.objectName(),
                'popupObjectName': combo.view().objectName(),
                'initialIndex': combo.currentIndex(),
                'items': combo.count(),
                'source': str(qss_path),
                'states': ['normal', 'popup-open', 'backdrop', 'disabled'],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'sizeHint': [combo.sizeHint().width(), combo.sizeHint().height()],
                'limitations': ['The native Qt popup is styled through QAbstractItemView; this does not establish historical SR10.4 fidelity.']}
        if qt6_spin_recipe:
            record['qt6SpinRecipe'] = {
                'applied': True,
                'scope': 'real QSpinBox and QDoubleSpinBox; Qt retains numeric range, stepping, text editing and keyboard semantics',
                'widgets': [
                    {'class': spin.metaObject().className(), 'objectName': spin.objectName(),
                     'value': spin.value(), 'range': [spin.minimum(), spin.maximum()],
                     'sizeHint': [spin.sizeHint().width(), spin.sizeHint().height()]},
                    {'class': decimal.metaObject().className(), 'objectName': decimal.objectName(),
                     'value': decimal.value(), 'range': [decimal.minimum(), decimal.maximum()],
                     'sizeHint': [decimal.sizeHint().width(), decimal.sizeHint().height()]},
                ],
                'source': str(qss_path),
                'states': ['normal', 'pressed', 'backdrop', 'disabled'],
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'limitations': ['QSS state mapping does not establish historical SR10.4 fidelity.']}
        if qt6_scale_recipe:
            record['qt6ScaleRecipe'] = {
                'applied': True,
                'scope': 'one real horizontal QSlider; Qt retains range, mouse and keyboard semantics',
                'widgetClass': slider.metaObject().className(),
                'objectName': slider.objectName(),
                'orientation': 'horizontal',
                'value': slider.value(),
                'sizeHint': [slider.sizeHint().width(), slider.sizeHint().height()],
                'source': str(qss_path),
                'states': ['normal', 'focused', 'backdrop', 'disabled'],
                'backdropSelector': '[domainosBackdrop="true"]',
                'backdropTracksTopLevelActivation': qt6_scale_backdrop_tracker is not None,
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'limitations': ['The QSS uses Qt subcontrols; this does not establish historical SR10.4 fidelity.']}
        if qt6_scale_v_recipe:
            record['qt6ScaleVRecipe'] = {
                'applied': True,
                'scope': 'one real vertical QSlider; Qt retains range, mouse and keyboard semantics',
                'widgetClass': vertical_slider.metaObject().className(),
                'objectName': vertical_slider.objectName(),
                'orientation': 'vertical',
                'value': vertical_slider.value(),
                'sizeHint': [vertical_slider.sizeHint().width(), vertical_slider.sizeHint().height()],
                'source': str(qss_path),
                'states': ['normal', 'focused', 'backdrop', 'disabled'],
                'backdropSelector': '[domainosBackdrop="true"]',
                'backdropTracksTopLevelActivation': qt6_scale_v_backdrop_tracker is not None,
                'selectedScheme': scrollbar_recipe['selected_scheme'],
                'paletteInputs': scrollbar_recipe['palette_inputs'],
                'limitations': ['The QSS uses Qt subcontrols; this does not establish historical SR10.4 fidelity.']}
    if qt5_scrollbar_recipe:
        qss_path = Path(qt5_scrollbar_recipe['css'])
        stylesheet = qss_path.read_text(encoding='utf-8')
        window.setStyleSheet(stylesheet)
        record['qt5ScrollbarRecipe'] = {
            'applied': True, 'scope': qt5_scrollbar_recipe['scope'],
            'projectSha256': qt5_scrollbar_recipe['project_sha256'],
            'recipeSha256': qt5_scrollbar_recipe['recipe_sha256'],
            'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
            'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
            'geometry': qt5_scrollbar_recipe['geometry'],
            'states': qt5_scrollbar_recipe['states'],
            'scrollSpacingAdapters': scrollbar_spacing_adapters,
            'source': str(qss_path), 'limitations': qt5_scrollbar_recipe['limitations']}
        if qt5_push_recipe:
            record['qt5PushButtonRecipe'] = {
                'applied': True,
                'scope': 'one real QPushButton identified by its object name in this private gallery window',
                'objectName': button.objectName(),
                'source': str(qss_path),
                'states': qt5_scrollbar_recipe['states'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'sizeHint': [button.sizeHint().width(), button.sizeHint().height()],
                'limitations': ['The Qt5 stylesheet paints a real Qt button; this does not prove SR10.4 fidelity.']}
        if qt5_toggle_recipe:
            record['qt5ToggleButtonRecipe'] = {
                'applied': True,
                'scope': 'one real checkable QPushButton identified by its object name in this private gallery window',
                'objectName': toggle_button.objectName(),
                'checkable': toggle_button.isCheckable(),
                'initiallyChecked': toggle_button.isChecked(),
                'source': str(qss_path),
                'states': ['released', 'checked-relief-locked', 'disabled'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'sizeHint': [toggle_button.sizeHint().width(), toggle_button.sizeHint().height()],
                'limitations': ['This records the native checkable QPushButton and QSS scope; it does not prove SR10.4 fidelity.']}
        if qt5_check_recipe:
            record['qt5CheckBoxRecipe'] = {
                'applied': True,
                'scope': 'one real QCheckBox identified by its object name in this private gallery window',
                'objectName': check.objectName(),
                'checkable': check.isCheckable(),
                'initiallyChecked': check.isChecked(),
                'source': str(qss_path),
                'states': ['unchecked', 'checked', 'pressed', 'backdrop', 'disabled'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'sizeHint': [check.sizeHint().width(), check.sizeHint().height()],
                'limitations': ['The Qt5 stylesheet paints the indicator of a real QCheckBox; this does not prove SR10.4 fidelity.']}
        if qt5_radio_recipe:
            record['qt5RadioButtonRecipe'] = {
                'applied': True,
                'scope': 'real exclusive QRadioButton pair identified by object names in this private gallery window',
                'objectName': radio.objectName(),
                'checkable': True,
                'initiallyChecked': radio.isChecked(),
                'exclusiveGroup': radio_group.exclusive(),
                'peerObjectName': radio_peer.objectName(),
                'peerInitiallyChecked': radio_peer.isChecked(),
                'source': str(qss_path),
                'states': ['unchecked', 'checked', 'pressed', 'backdrop', 'disabled'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'sizeHint': [radio.sizeHint().width(), radio.sizeHint().height()],
                'limitations': ['The Qt5 stylesheet paints the indicator of a real QRadioButton; this does not prove SR10.4 fidelity.']}
        if qt5_entry_recipe:
            record['qt5EntryRecipe'] = {
                'applied': True,
                'scope': 'one real QLineEdit; native editing, cursor, selection and input remain owned by Qt',
                'objectName': text.objectName(),
                'states': ['normal', 'focused', 'backdrop', 'disabled'],
                'source': str(qss_path),
                'sizeHint': [text.sizeHint().width(), text.sizeHint().height()],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'limitations': ['QSS state mapping does not establish historical SR10.4 fidelity or full controller integration.']}
        if qt5_text_recipe:
            record['qt5TextRecipe'] = {
                'applied': True,
                'scope': 'one real QTextEdit; Qt retains multiline editing, keyboard, selection and clipboard semantics',
                'objectName': editor.objectName(),
                'states': ['normal', 'focused', 'backdrop', 'disabled'],
                'source': str(qss_path),
                'sizeHint': [editor.sizeHint().width(), editor.sizeHint().height()],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'limitations': ['QSS state mapping does not establish historical SR10.4 fidelity or full controller integration.']}
        if qt5_combo_recipe:
            record['qt5ComboRecipe'] = {
                'applied': True,
                'scope': 'one real QComboBox; Qt retains its native popup, selection and keyboard/mouse behavior',
                'objectName': combo.objectName(),
                'popupObjectName': combo.view().objectName(),
                'initialIndex': combo.currentIndex(),
                'items': combo.count(),
                'source': str(qss_path),
                'states': ['normal', 'popup-open', 'backdrop', 'disabled'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'sizeHint': [combo.sizeHint().width(), combo.sizeHint().height()],
                'limitations': ['The native Qt popup is styled through QAbstractItemView; this does not establish historical SR10.4 fidelity or full controller integration.']}
        if qt5_spin_recipe:
            record['qt5SpinRecipe'] = {
                'applied': True,
                'scope': 'real QSpinBox and QDoubleSpinBox; Qt retains numeric range, stepping and keyboard semantics',
                'widgets': [
                    {'class': spin.metaObject().className(), 'objectName': spin.objectName(),
                     'value': spin.value(), 'sizeHint': [spin.sizeHint().width(), spin.sizeHint().height()]},
                    {'class': decimal.metaObject().className(), 'objectName': decimal.objectName(),
                     'value': decimal.value(), 'sizeHint': [decimal.sizeHint().width(), decimal.sizeHint().height()]},
                ],
                'source': str(qss_path),
                'states': ['normal', 'pressed', 'backdrop', 'disabled', 'minimum/maximum stepper off'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'limitations': ['The real Qt spin buttons and arrows use QSS subcontrols; this does not establish historical SR10.4 fidelity.']}
        if qt5_scale_recipe:
            record['qt5ScaleRecipe'] = {
                'applied': True,
                'scope': 'real horizontal and vertical QSlider controls; Qt retains range, mouse and keyboard semantics',
                'widgets': [
                    {'class': slider.metaObject().className(), 'objectName': slider.objectName(),
                     'orientation': 'horizontal', 'value': slider.value(),
                     'sizeHint': [slider.sizeHint().width(), slider.sizeHint().height()]},
                    {'class': vertical_slider.metaObject().className(),
                     'objectName': vertical_slider.objectName(), 'orientation': 'vertical',
                     'value': vertical_slider.value(),
                     'sizeHint': [vertical_slider.sizeHint().width(), vertical_slider.sizeHint().height()]},
                ],
                'source': str(qss_path),
                'states': ['normal', 'focused', 'pressed', 'backdrop', 'disabled'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'limitations': ['The QSS uses Qt subcontrols; this does not establish historical SR10.4 fidelity.']}
        if qt5_arrow_recipe:
            record['qt5ArrowRecipe'] = {
                'applied': True,
                'scope': 'one real QToolButton with a recipe-owned state glyph; native Qt5 click/focus semantics retained',
                'objectName': recipe_arrow.objectName(),
                'widgetClass': recipe_arrow.metaObject().className(),
                'states': ['normal', 'pressed while held', 'backdrop', 'disabled', 'focused'],
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'size': [recipe_arrow.width(), recipe_arrow.height()],
                'limitations': ['This real-widget recipe is not a claim of historical SR10.4 fidelity.']}
        if qt5_progress_recipe:
            record['qt5ProgressRecipe'] = {
                'applied': True,
                'scope': 'one real QProgressBar; Qt retains progress range, value, fill fraction and text formatting',
                'objectName': progress.objectName(),
                'widgetClass': progress.metaObject().className(),
                'orientation': 'horizontal',
                'range': [progress.minimum(), progress.maximum()],
                'value': progress.value(),
                'text': progress.text(),
                'states': ['normal', 'backdrop', 'disabled', 'focused'],
                'textColorSource': 'Qt palette Text role; the QSS only sets KDE-role-derived track/fill surfaces and relief',
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'limitations': ['The value shown is static gallery sample data, not task telemetry or historical fidelity.']}
        if qt5_list_recipe:
            record['qt5ListRecipe'] = {
                'applied': True,
                'scope': 'real QTreeWidget/QTreeView with native selection and internal scrollbars',
                'objectName': listing.objectName(),
                'widgetClass': listing.metaObject().className(),
                'rowCount': listing.topLevelItemCount(),
                'selectedRow': listing.indexOfTopLevelItem(listing.currentItem()),
                'selectionMode': 'single row',
                'states': ['normal', 'selected', 'focused', 'backdrop', 'disabled'],
                'source': str(qt5_scrollbar_recipe['css']),
                'selectedScheme': qt5_scrollbar_recipe['selected_scheme'],
                'paletteInputs': qt5_scrollbar_recipe['palette_inputs'],
                'limitations': ['The QTreeView is a real Qt control; this does not prove historical SR10.4 fidelity.']}
            for axis, widget in (('vertical', listing.verticalScrollBar()),
                                 ('horizontal', listing.horizontalScrollBar())):
                record['qt5ListRecipe'].setdefault('nativeScrollbars', {})[axis] = {
                    'visible': widget.isVisible(), 'maximum': widget.maximum(),
                    'sizeHint': [widget.sizeHint().width(), widget.sizeHint().height()],
                    'objectName': widget.objectName(),
                    'widgetClass': widget.metaObject().className()}
    if qt5_frame_recipe or qt6_frame_recipe:
        frame_key = 'qt6FrameRecipe' if qt6_frame_recipe else 'qt5FrameRecipe'
        record[frame_key] = {
            'applied': True,
            'scope': 'one real QFrame with native Panel/Sunken semantics; KDE-role-derived surface and bevel',
            'objectName': framed.objectName(),
            'widgetClass': framed.metaObject().className(),
            'frameShape': int(framed.frameShape()),
            'frameShadow': int(framed.frameShadow()),
            'lineWidth': framed.lineWidth(),
            'sizeHint': [framed.sizeHint().width(), framed.sizeHint().height()],
            'source': str(frame_recipe['css']),
            'selectedScheme': frame_recipe['selected_scheme'],
            'paletteInputs': frame_recipe['palette_inputs'],
            'states': ['normal', 'backdrop', 'disabled'],
            'backdropSelector': '[domainosBackdrop="true"]' if qt6_frame_recipe else ':!active',
            'backdropTracksTopLevelActivation': bool(qt6_frame_recipe),
            'limitations': ['A real QFrame recipe does not establish historical SR10.4 fidelity.']}
    if kvantum_recipe:
        record['kvantumScrollbarRecipe'] = {
            'applied': True, 'scope': kvantum_recipe['scope'],
            'projectSha256': kvantum_recipe['project_sha256'],
            'recipeSha256': kvantum_recipe['recipe_sha256'],
            'contract': kvantum_recipe['contract'],
            'themeName': kvantum_recipe['theme_name'],
            'geometry': kvantum_recipe['geometry'],
            'configGeometry': kvantum_recipe['config_geometry'],
            'paletteRolesApplied': kvantum_recipe['palette_roles_applied'],
            'paletteInputs': kvantum_recipe['palette_inputs'],
            'limitations': kvantum_recipe['limitations'],
            'nativeMetrics': {}}
    dialogs = QWidget()
    dialogs_layout = QVBoxLayout(dialogs)
    instructions = QLabel('Dialogs and System Settings run inside the same private namespace, HOME, display and session bus.')
    instructions.setWordWrap(True)
    dialogs_layout.addWidget(instructions)
    file_button = QPushButton('Open QFileDialog')
    settings_button = QPushButton('Open private System Settings')
    capture_button = QPushButton('Save this window screenshot and JSON')
    file_button.setToolTip('Abre o seletor de arquivos no perfil privado; a galeria registra apenas seleção ou cancelamento.')
    settings_button.setToolTip('Abre as Configurações do Sistema dentro do ambiente privado; não modifica o perfil pessoal.')
    capture_button.setToolTip('Salva a captura desta janela e a prova JSON no perfil privado; não instala o tema.')
    dialogs_layout.addWidget(file_button)
    dialogs_layout.addWidget(settings_button)
    dialogs_layout.addWidget(capture_button)
    dialogs_layout.addStretch(1)
    tabs.addTab(dialogs, 'Dialogs')

    def save_proof(screenshot=False):
        if scrollbar_spacing_adapters:
            from qt_scrollbar_spacing import finalize_on_scroll_areas
            finalize_on_scroll_areas(window)
            record['scrollSpacingSkippedWidgets'] = getattr(
                window, '_domainos_scroll_spacing_skipped', [])
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
                      qtMajor=args.qt_major, qtRuntimeVersion=qVersion(),
                      platform=app.platformName(), platformTheme=os.environ.get('QT_QPA_PLATFORMTHEME'),
                      style={'objectName': app.style().objectName(), 'className': app.style().metaObject().className()},
                      font=app.font().toString(), selections=selection(), loadedKvantum=loaded,
                      palette={group: {role: palette.color(value, getattr(QPalette.ColorRole, role)).name()
                                       for role in roles} for group, value in groups.items()},
                      window={'width': window.width(), 'height': window.height(),
                              'x': window.x(), 'y': window.y()},
                      apiLimits=['Qt Widgets has no native switch control; QCheckBox is the standard boolean widget.'])
        if scrollbar_recipe:
            for axis, widget in (('vertical', scroll.verticalScrollBar()),
                                 ('horizontal', scroll.horizontalScrollBar())):
                record['qt6ScrollbarRecipe'].setdefault('nativeMetrics', {})[axis] = {
                    'allocation': [widget.width(), widget.height()],
                    'sizeHint': [widget.sizeHint().width(), widget.sizeHint().height()],
                    'minimumSizeHint': [widget.minimumSizeHint().width(), widget.minimumSizeHint().height()],
                    'visible': widget.isVisible(), 'value': widget.value(),
                    'minimum': widget.minimum(), 'maximum': widget.maximum(),
                    'pageStep': widget.pageStep(), 'singleStep': widget.singleStep(),
                    'objectName': widget.objectName(), 'widgetClass': widget.metaObject().className()}
        if qt5_scrollbar_recipe:
            for axis, widget in (('vertical', scroll.verticalScrollBar()),
                                 ('horizontal', scroll.horizontalScrollBar())):
                record['qt5ScrollbarRecipe'].setdefault('nativeMetrics', {})[axis] = {
                    'allocation': [widget.width(), widget.height()],
                    'sizeHint': [widget.sizeHint().width(), widget.sizeHint().height()],
                    'minimumSizeHint': [widget.minimumSizeHint().width(), widget.minimumSizeHint().height()],
                    'visible': widget.isVisible(), 'value': widget.value(),
                    'minimum': widget.minimum(), 'maximum': widget.maximum(),
                    'pageStep': widget.pageStep(), 'singleStep': widget.singleStep(),
                    'objectName': widget.objectName(), 'widgetClass': widget.metaObject().className()}
        if kvantum_recipe:
            for axis, widget in (('vertical', scroll.verticalScrollBar()),
                                 ('horizontal', scroll.horizontalScrollBar())):
                record['kvantumScrollbarRecipe']['nativeMetrics'][axis] = {
                    'allocation': [widget.width(), widget.height()],
                    'sizeHint': [widget.sizeHint().width(), widget.sizeHint().height()],
                    'minimumSizeHint': [widget.minimumSizeHint().width(), widget.minimumSizeHint().height()],
                    'visible': widget.isVisible(), 'value': widget.value(),
                    'minimum': widget.minimum(), 'maximum': widget.maximum(),
                    'pageStep': widget.pageStep(), 'singleStep': widget.singleStep(),
                    'objectName': widget.objectName(), 'widgetClass': widget.metaObject().className()}
        if screenshot and window.isVisible():
            image_path = output / 'qtwidgets.png'
            record['screenshotSaved'] = window.grab().save(str(image_path), 'PNG')
            record['screenshot'] = str(image_path)
            if qt5_push_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                push_path = output / 'qt5-pushbutton.png'
                record['pushButtonScreenshotSaved'] = window.grab().save(str(push_path), 'PNG')
                record['pushButtonScreenshot'] = str(push_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_toggle_recipe:
                prior_tab = tabs.currentWidget()
                prior_checked = toggle_button.isChecked()
                tabs.setCurrentWidget(controls)
                toggle_button.setChecked(True)
                app.processEvents()
                toggle_path = output / 'qt5-togglebutton-checked.png'
                record['toggleButtonScreenshotSaved'] = window.grab().save(str(toggle_path), 'PNG')
                record['toggleButtonCheckedScreenshot'] = str(toggle_path)
                toggle_button.setChecked(prior_checked)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_toggle_recipe:
                prior_tab = tabs.currentWidget()
                prior_checked = toggle_button.isChecked()
                tabs.setCurrentWidget(controls)
                toggle_button.setChecked(True)
                app.processEvents()
                toggle_path = output / 'qt6-togglebutton-checked.png'
                record['toggleButtonScreenshotSaved'] = window.grab().save(str(toggle_path), 'PNG')
                record['toggleButtonCheckedScreenshot'] = str(toggle_path)
                toggle_button.setChecked(prior_checked)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_check_recipe:
                prior_tab = tabs.currentWidget()
                prior_checked = check.isChecked()
                tabs.setCurrentWidget(controls)
                check.setChecked(True)
                app.processEvents()
                checked_path = output / 'qt6-checkbox-checked.png'
                record['checkBoxCheckedScreenshotSaved'] = window.grab().save(str(checked_path), 'PNG')
                record['checkBoxCheckedScreenshot'] = str(checked_path)
                check.setChecked(False)
                app.processEvents()
                unchecked_path = output / 'qt6-checkbox-unchecked.png'
                record['checkBoxUncheckedScreenshotSaved'] = window.grab().save(str(unchecked_path), 'PNG')
                record['checkBoxUncheckedScreenshot'] = str(unchecked_path)
                check.setChecked(prior_checked)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_check_recipe:
                prior_tab = tabs.currentWidget()
                prior_checked = check.isChecked()
                tabs.setCurrentWidget(controls)
                check.setChecked(True)
                app.processEvents()
                checked_path = output / 'qt5-checkbox-checked.png'
                record['checkBoxCheckedScreenshotSaved'] = window.grab().save(str(checked_path), 'PNG')
                record['checkBoxCheckedScreenshot'] = str(checked_path)
                check.setChecked(False)
                app.processEvents()
                unchecked_path = output / 'qt5-checkbox-unchecked.png'
                record['checkBoxUncheckedScreenshotSaved'] = window.grab().save(str(unchecked_path), 'PNG')
                record['checkBoxUncheckedScreenshot'] = str(unchecked_path)
                check.setChecked(prior_checked)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_radio_recipe:
                prior_tab = tabs.currentWidget()
                prior_checked = radio.isChecked()
                tabs.setCurrentWidget(controls)
                radio.setChecked(True)
                app.processEvents()
                checked_path = output / 'qt5-radiobutton-checked.png'
                record['radioButtonCheckedScreenshotSaved'] = window.grab().save(str(checked_path), 'PNG')
                record['radioButtonCheckedScreenshot'] = str(checked_path)
                radio_peer.setChecked(True)
                app.processEvents()
                unchecked_path = output / 'qt5-radiobutton-unchecked.png'
                record['radioButtonUncheckedScreenshotSaved'] = window.grab().save(str(unchecked_path), 'PNG')
                record['radioButtonUncheckedScreenshot'] = str(unchecked_path)
                radio.setChecked(prior_checked)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_radio_recipe:
                prior_tab = tabs.currentWidget()
                prior_checked = radio.isChecked()
                prior_peer_checked = radio_peer.isChecked()
                tabs.setCurrentWidget(controls)
                radio.setChecked(True)
                app.processEvents()
                checked_path = output / 'qt6-radiobutton-checked.png'
                record['radioButtonCheckedScreenshotSaved'] = window.grab().save(str(checked_path), 'PNG')
                record['radioButtonCheckedScreenshot'] = str(checked_path)
                radio_peer.setChecked(True)
                app.processEvents()
                unchecked_path = output / 'qt6-radiobutton-unchecked.png'
                record['radioButtonUncheckedScreenshotSaved'] = window.grab().save(str(unchecked_path), 'PNG')
                record['radioButtonUncheckedScreenshot'] = str(unchecked_path)
                radio.setChecked(prior_checked)
                radio_peer.setChecked(prior_peer_checked)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_entry_recipe:
                entry_path = output / 'qt5-entry.png'
                record['entryScreenshotSaved'] = text.grab().save(str(entry_path), 'PNG')
                record['entryScreenshot'] = str(entry_path)
            if qt6_entry_recipe:
                entry_path = output / 'qt6-entry.png'
                record['qt6EntryScreenshotSaved'] = text.grab().save(str(entry_path), 'PNG')
                record['qt6EntryScreenshot'] = str(entry_path)
            if qt5_text_recipe:
                text_path = output / 'qt5-textedit.png'
                record['textEditScreenshotSaved'] = editor.grab().save(str(text_path), 'PNG')
                record['textEditScreenshot'] = str(text_path)
            if qt6_text_recipe:
                text_path = output / 'qt6-textedit.png'
                record['qt6TextScreenshotSaved'] = editor.grab().save(str(text_path), 'PNG')
                record['qt6TextScreenshot'] = str(text_path)
            if qt5_combo_recipe or qt6_combo_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                prefix = 'qt6' if qt6_combo_recipe else 'qt5'
                combo_path = output / f'{prefix}-combo.png'
                record[f'{prefix}ComboScreenshotSaved'] = combo.grab().save(str(combo_path), 'PNG')
                record[f'{prefix}ComboScreenshot'] = str(combo_path)
                prior_index = combo.currentIndex()
                combo.showPopup()
                app.processEvents()
                popup = combo.view()
                selected = popup.model().index(1, 0)
                popup.setCurrentIndex(selected)
                selection_flag = (QItemSelectionModel.SelectionFlag.ClearAndSelect
                                  if args.qt_major == 6 else QItemSelectionModel.ClearAndSelect)
                popup.selectionModel().select(selected, selection_flag)
                app.processEvents()
                popup_path = output / f'{prefix}-combo-popup-selection.png'
                record[f'{prefix}ComboPopupSelectionScreenshotSaved'] = popup.viewport().grab().save(
                    str(popup_path), 'PNG')
                record[f'{prefix}ComboPopupSelectionScreenshot'] = str(popup_path)
                record[f'{prefix}ComboPopupSelection'] = {
                    'visible': popup.isVisible(),
                    'selectedIndex': selected.row(),
                    'selected': popup.selectionModel().isSelected(selected),
                    'rowRect': popup.visualRect(selected).getRect()}
                combo.hidePopup()
                combo.setCurrentIndex(prior_index)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_spin_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                spin_path = output / 'qt6-spinboxes.png'
                record['qt6SpinScreenshotSaved'] = window.grab().save(str(spin_path), 'PNG')
                record['qt6SpinScreenshot'] = str(spin_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_scale_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                scale_path = output / 'qt6-scale-horizontal.png'
                record['qt6ScaleScreenshotSaved'] = slider.grab().save(str(scale_path), 'PNG')
                record['qt6ScaleScreenshot'] = str(scale_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_scale_v_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                scale_path = output / 'qt6-scale-vertical.png'
                record['qt6ScaleVScreenshotSaved'] = vertical_slider.grab().save(str(scale_path), 'PNG')
                record['qt6ScaleVScreenshot'] = str(scale_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_spin_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                spin_path = output / 'qt5-spinboxes.png'
                record['spinScreenshotSaved'] = window.grab().save(str(spin_path), 'PNG')
                record['spinScreenshot'] = str(spin_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_scale_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                scale_path = output / 'qt5-scales.png'
                record['scaleScreenshotSaved'] = scale_row.grab().save(str(scale_path), 'PNG')
                record['scaleScreenshot'] = str(scale_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_arrow_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                arrow_path = output / 'qt5-arrow-button.png'
                record['qt5ArrowScreenshotSaved'] = window.grab().save(str(arrow_path), 'PNG')
                record['qt5ArrowScreenshot'] = str(arrow_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_arrow_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                arrow_path = output / 'qt6-arrow-button.png'
                record['qt6ArrowScreenshotSaved'] = window.grab().save(str(arrow_path), 'PNG')
                record['qt6ArrowScreenshot'] = str(arrow_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt6_progress_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                progress_path = output / 'qt6-progress.png'
                record['qt6ProgressScreenshotSaved'] = window.grab().save(str(progress_path), 'PNG')
                record['qt6ProgressScreenshot'] = str(progress_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_progress_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(controls)
                app.processEvents()
                progress_path = output / 'qt5-progress.png'
                record['qt5ProgressScreenshotSaved'] = window.grab().save(str(progress_path), 'PNG')
                record['qt5ProgressScreenshot'] = str(progress_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_list_recipe or qt6_list_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(listing)
                app.processEvents()
                list_record = record['qt6ListRecipe'] if qt6_list_recipe else record['qt5ListRecipe']
                list_record['selectedRow'] = listing.indexOfTopLevelItem(listing.currentItem())
                for axis, widget in (('vertical', listing.verticalScrollBar()),
                                     ('horizontal', listing.horizontalScrollBar())):
                    list_record['nativeScrollbars'][axis].update({
                        'visible': widget.isVisible(), 'maximum': widget.maximum(),
                        'allocation': [widget.width(), widget.height()]})
                list_path = output / ('qt6-list.png' if qt6_list_recipe else 'qt5-list.png')
                screenshot_key = 'qt6ListScreenshot' if qt6_list_recipe else 'qt5ListScreenshot'
                record[screenshot_key + 'Saved'] = window.grab().save(str(list_path), 'PNG')
                record[screenshot_key] = str(list_path)
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
            if qt5_frame_recipe or qt6_frame_recipe:
                prior_tab = tabs.currentWidget()
                tabs.setCurrentWidget(framed)
                app.processEvents()
                frame_prefix = 'qt6' if qt6_frame_recipe else 'qt5'
                frame_path = output / (frame_prefix + '-frame.png')
                frame_key = frame_prefix + 'FrameRecipe'
                record[frame_prefix + 'FrameScreenshotSaved'] = window.grab().save(str(frame_path), 'PNG')
                record[frame_prefix + 'FrameScreenshot'] = str(frame_path)
                record[frame_key]['sizeHint'] = [
                    framed.sizeHint().width(), framed.sizeHint().height()]
                tabs.setCurrentWidget(prior_tab)
                app.processEvents()
        target = output / 'RESULTADO.json'
        target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
        target.chmod(0o600)

    def open_file():
        private_guards()
        actions.append({'action': 'QFileDialog', 'request': 'open'})
        dialog = QFileDialog(window, 'Private theme file dialog', str(home))
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        record['fileDialogHintCoverage'] = add_dialog_hints(dialog, QWidget, QAction)
        # Preserve the platform's native-dialog choice; external portal controls
        # cannot be assigned QWidget hints by this process.
        accepted = dialog.exec()
        chosen = dialog.selectedFiles() if accepted else []
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
                                   close_fds=True, cwd=str(home))
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
    file_action.setToolTip(file_button.toolTip())
    file_action.triggered.connect(open_file)
    menu.addAction(file_action)
    settings_action = QAction('Private System Settings...', window)
    settings_action.setToolTip(settings_button.toolTip())
    settings_action.triggered.connect(open_settings)
    menu.addAction(settings_action)
    menu.addSeparator()
    checked_action = QAction('Checkable native QAction', window)
    checked_action.setCheckable(True)
    checked_action.setChecked(True)
    checked_action.setToolTip('Opção alternável do menu nativo: marque ou desmarque para observar a seleção.')
    menu.addAction(checked_action)
    disabled_action = QAction('Disabled native QAction', window)
    disabled_action.setEnabled(False)
    disabled_action.setToolTip('Ação desabilitada da amostra: apresenta o estado sem executar uma operação.')
    menu.addAction(disabled_action)
    submenu = menu.addMenu('Submenu')
    submenu_hint = (
        'Abre as opções adicionais desta amostra. A explicação aparece na linha de estado após 500 ms; não altera o tema.'
        if args.qt_major == 6 else
        'Abre as opções adicionais desta amostra. A dica nativa aparece fora do menu; não altera o tema.')
    submenu.menuAction().setToolTip(submenu_hint)
    submenu_action = submenu.addAction('Submenu item')
    submenu_action.setToolTip(
        'Executa a ação demonstrativa do submenu e informa o resultado na linha de estado; não altera o tema.')
    submenu_action.triggered.connect(lambda: status.setText('Native submenu action clicked'))
    menu.addSeparator()
    close_action = menu.addAction('Close')
    close_action.setToolTip(
        'Fecha somente esta galeria privada; não altera arquivos nem configurações do perfil pessoal.')
    close_action.triggered.connect(lambda: shutdown.request())
    help_menu = window.menuBar().addMenu('&Help')
    menu.menuAction().setToolTip(
        'Abre ações da galeria: seletor de arquivos, controles de estado da amostra e fechamento.')
    def show_about():
        dialog = QMessageBox(window)
        dialog.setWindowTitle('Private Qt Widgets demo')
        dialog.setText('Real Qt Widgets rendered by the selected private KDE/Kvantum style.')
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        record['aboutDialogHintCoverage'] = add_dialog_hints(dialog, QWidget, QAction)
        dialog.exec()

    about_action = help_menu.addAction('About this private demo')
    about_action.setToolTip(
        'Abre as informações desta demonstração; fechar o diálogo retorna à galeria sem alterar o tema ou o projeto.')
    about_action.triggered.connect(show_about)
    help_menu.menuAction().setToolTip(
        'Abre o menu de ajuda com informações sobre esta demonstração privada.')
    from qt_widget_hints import add_gallery_hints, add_dialog_hints
    record['hintCoverage']=add_gallery_hints(
        window,QWidget,QAction,status_widget=status if args.qt_major==6 else None)
    bridge = None
    shutdown = PreviewShutdown(app, window)
    app.aboutToQuit.connect(lambda: save_proof(False))
    app.aboutToQuit.connect(shutdown.cleanup)
    window.show()
    if embedded:
        lab = fixture_root() / 'tools/theme-lab'
        if str(lab) not in sys.path:
            sys.path.insert(0, str(lab))
        from gtk4_host import HostBridge
        bridge = HostBridge(args.host_bridge, args.embed_window, args.host_pid)
        bridge.attach(int(window.winId()))
        shutdown.set_bridge(bridge)
        record.update(embedded=True, embedWindow=args.embed_window,
                      hostPid=args.host_pid, nativeOrigin='x11-reparented-qt-window')

        def poll_host():
            if bridge.poll() is None:
                shutdown.request()

        host_timer = QTimer(app)
        host_timer.setInterval(150)
        host_timer.timeout.connect(poll_host)
        host_timer.start()
        shutdown.set_timer(host_timer)
    else:
        record.update(embedded=False, nativeOrigin='detached-qt-window')
    # QA snapshot only. No timer controls interactive actions or production UI.
    QTimer.singleShot(1000, lambda: save_proof(True))
    if args.theme_lab_test_close_ms is not None:
        QTimer.singleShot(max(1500, args.theme_lab_test_close_ms), shutdown.request)
    return app.exec()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, ImportError) as error:
        print('Private Qt Widgets demo refused: ' + str(error), file=sys.stderr)
        sys.exit(2)
