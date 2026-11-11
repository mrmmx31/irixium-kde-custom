#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise generated QSS and arrow paint on real PyQt5 scrollbars."""
import argparse
from collections import Counter
import json
import os
import re
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stylesheet', type=Path, required=True)
parser.add_argument('--assets', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
    raise SystemExit('This widget probe requires the offscreen Qt platform.')

from PyQt5.QtCore import QPoint, Qt, QItemSelectionModel
from PyQt5.QtGui import QColor, QImage, QPainter
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QLineEdit, QProgressBar, QRadioButton, QScrollArea, QSlider, QSpinBox, QStyle, QStyleOptionButton, QStyleOptionComboBox, QStyleOptionSlider, QStyleOptionSpinBox, QTextEdit, QVBoxLayout, QWidget, QPushButton
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'plasma/tests/galerias-nativas'))
from qt5_scrollbar_widgets import install_scrollbar_painters
from qt_scrollbar_spacing import install_scrollbar_spacing
from qt5_arrow_widget import RecipeArrowButton
from qt5_progress_widget import RecipeProgressBar


def difference(first, second, rect):
    return sum(first.pixel(x, y) != second.pixel(x, y)
               for y in range(rect.top(), rect.bottom() + 1)
               for x in range(rect.left(), rect.right() + 1))


def assert_standalone_arrow_asset(widget, asset_path, state):
    expected = QImage(str(asset_path)).convertToFormat(QImage.Format_ARGB32)
    actual = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    x = (actual.width() - expected.width()) // 2
    y = (actual.height() - expected.height()) // 2
    if x < 0 or y < 0:
        raise AssertionError(f'Qt5 standalone arrow {state} asset exceeds its QToolButton.')
    differences = sum(expected.pixelColor(ix, iy).alpha() > 0 and
                      actual.pixel(x + ix, y + iy) != expected.pixel(ix, iy)
                      for iy in range(expected.height()) for ix in range(expected.width()))
    if differences:
        actual.save(str(args.output / f'standalone-arrow-{state}-actual.png'), 'PNG')
        expected.save(str(args.output / f'standalone-arrow-{state}-expected.png'), 'PNG')
        raise AssertionError(f'Qt5 standalone arrow {state} asset differs in {differences} opaque pixels.')
    return {'pixelDifferences': differences, 'state': state,
            'glyphSize': [expected.width(), expected.height()]}


def exercise_standalone_arrow(stylesheet):
    window = QWidget()
    layout = QHBoxLayout(window)
    button = RecipeArrowButton(args.assets, shadow_px=2)
    button.setObjectName('domainosRecipeArrow')
    button.setStyleSheet(stylesheet.read_text(encoding='utf-8'))
    layout.addWidget(button)
    window.resize(button.sizeHint().width() + 12, button.sizeHint().height() + 12)
    window.show()
    window.activateWindow()
    QApplication.processEvents()
    clicked = []
    button.clicked.connect(lambda: clicked.append(True))
    state = button.arrow_state()
    normal = assert_standalone_arrow_asset(
        button, args.assets / f'standalone-arrow-down-{state}.png', state)
    point = button.rect().center()
    QTest.mousePress(button, Qt.LeftButton, pos=point)
    QApplication.processEvents()
    held = button.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    pressed = assert_standalone_arrow_asset(
        button, args.assets / 'standalone-arrow-down-pressed.png', 'pressed')
    QTest.mouseRelease(button, Qt.LeftButton, pos=point)
    QApplication.processEvents()
    released_state = button.arrow_state()
    released = assert_standalone_arrow_asset(
        button, args.assets / f'standalone-arrow-down-{released_state}.png', released_state)
    QTest.mouseClick(button, Qt.LeftButton, pos=point)
    QApplication.processEvents()
    button.setEnabled(False)
    QApplication.processEvents()
    disabled = assert_standalone_arrow_asset(
        button, args.assets / 'standalone-arrow-down-disabled.png', 'disabled')
    screenshot = args.output / 'qt5-standalone-arrow.png'
    saved = window.grab().save(str(screenshot), 'PNG')
    result = {'widgetClass': button.metaObject().className(),
              'objectName': button.objectName(), 'normalState': state,
              'releasedState': released_state, 'pressedState': button.arrow_state() if button.isDown() else 'pressed',
              'isDownAfterRelease': button.isDown(), 'clickCount': len(clicked),
              'normalAsset': normal, 'pressedAsset': pressed,
              'releasedAsset': released, 'disabledAsset': disabled,
              'disabled': not button.isEnabled(), 'screenshotSaved': saved,
              'screenshot': str(screenshot), 'heldImageCaptured': not held.isNull()}
    if (button.isEnabled() or button.isDown() or len(clicked) != 2 or not saved or
            not result['heldImageCaptured']):
        window.close()
        raise AssertionError('Qt5 standalone QToolButton did not preserve click/press/disable behavior.')
    window.close()
    QApplication.processEvents()
    return result


def exercise_progress(stylesheet):
    window = QWidget()
    layout = QVBoxLayout(window)
    progress = RecipeProgressBar()
    progress.setObjectName('domainosRecipeProgress')
    progress.setRange(0, 100)
    progress.setValue(43)
    progress.setFormat('%p%')
    progress.setTextVisible(True)
    progress.setFocusPolicy(Qt.StrongFocus)
    layout.addWidget(progress)
    window.setStyleSheet(stylesheet.read_text(encoding='utf-8'))
    window.resize(320, max(50, progress.sizeHint().height() + 16))
    window.show()
    window.activateWindow()
    QApplication.processEvents()
    initial = progress.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    initial_value, initial_text = progress.value(), progress.text()
    progress.setValue(70)
    QApplication.processEvents()
    changed = progress.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    fill_changes = difference(initial, changed, progress.rect())
    changed_value, changed_text = progress.value(), progress.text()
    normal_path = args.output / 'qt5-progress-normal.png'
    normal_saved = changed.save(str(normal_path), 'PNG')
    progress.setEnabled(False)
    QApplication.processEvents()
    disabled = progress.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    disabled_changes = difference(changed, disabled, progress.rect())
    disabled_path = args.output / 'qt5-progress-disabled.png'
    disabled_saved = disabled.save(str(disabled_path), 'PNG')
    result = {'widgetClass': progress.metaObject().className(),
              'objectName': progress.objectName(), 'orientation': 'horizontal',
              'recipeState': progress.property('domainosState'),
              'initialValue': initial_value, 'initialText': initial_text,
              'valueAfterChange': changed_value, 'textAfterChange': changed_text,
              'fillValueChangedPixels': fill_changes,
              'disabled': not progress.isEnabled(),
              'disabledStateChangedPixels': disabled_changes,
              'normalScreenshotSaved': normal_saved,
              'disabledScreenshotSaved': disabled_saved,
              'normalScreenshot': str(normal_path),
              'disabledScreenshot': str(disabled_path),
              'size': [progress.width(), progress.height()]}
    if (progress.isEnabled() or initial_value != 43 or initial_text != '43%' or
            changed_value != 70 or changed_text != '70%' or fill_changes <= 0 or
            disabled_changes <= 0 or not normal_saved or not disabled_saved):
        window.close()
        raise AssertionError('Qt5 QProgressBar recipe did not preserve native value/text or visible state changes: '
                             + json.dumps(result, ensure_ascii=False))
    window.close()
    QApplication.processEvents()
    return result


def line_rect(widget, subcontrol):
    option = QStyleOptionSlider()
    widget.initStyleOption(option)
    rect = widget.style().subControlRect(QStyle.CC_ScrollBar, option, subcontrol, widget)
    if rect.isEmpty() or not widget.rect().contains(rect):
        raise AssertionError(f'Qt5 line subcontrol has no in-bar allocation: {rect}')
    return rect


def check_indicator_rect(widget):
    option = QStyleOptionButton()
    widget.initStyleOption(option)
    rect = widget.style().subElementRect(QStyle.SE_CheckBoxIndicator, option, widget)
    if rect.isEmpty() or not widget.rect().contains(rect):
        raise AssertionError(f'Qt5 checkbox indicator has no in-widget allocation: {rect}')
    return rect


def radio_indicator_rect(widget):
    option = QStyleOptionButton()
    widget.initStyleOption(option)
    rect = widget.style().subElementRect(QStyle.SE_RadioButtonIndicator, option, widget)
    if rect.isEmpty() or not widget.rect().contains(rect):
        raise AssertionError(f'Qt5 radio indicator has no in-widget allocation: {rect}')
    return rect


def combo_arrow_rect(widget):
    option = QStyleOptionComboBox()
    widget.initStyleOption(option)
    rect = widget.style().subControlRect(QStyle.CC_ComboBox, option,
                                         QStyle.SC_ComboBoxArrow, widget)
    if rect.isEmpty() or not widget.rect().contains(rect):
        raise AssertionError(f'Qt5 combo arrow has no in-widget allocation: {rect}')
    return rect


def combo_face_pixel(widget, image):
    from PyQt5.QtWidgets import QStyleOptionComboBox
    option = QStyleOptionComboBox()
    widget.initStyleOption(option)
    rect = widget.style().subControlRect(QStyle.CC_ComboBox, option,
                                         QStyle.SC_ComboBoxEditField, widget)
    if rect.isEmpty():
        raise AssertionError(f'Qt5 combo edit field has no face allocation: {rect}')
    colors = Counter(image.pixelColor(x, y).name().lower()
                     for y in range(rect.top(), rect.bottom() + 1)
                     for x in range(rect.left(), rect.right() + 1))
    return colors.most_common(1)[0][0]


def spin_button_rect(widget, subcontrol):
    option = QStyleOptionSpinBox()
    widget.initStyleOption(option)
    rect = widget.style().subControlRect(QStyle.CC_SpinBox, option, subcontrol, widget)
    if rect.isEmpty() or not widget.rect().contains(rect):
        raise AssertionError(f'Qt5 spin button has no in-widget allocation: {rect}')
    return rect


def assert_spin_arrow_asset(widget, asset_path, subcontrol, state):
    rect = spin_button_rect(widget, subcontrol)
    actual = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    expected = QImage(str(asset_path)).convertToFormat(QImage.Format_ARGB32)
    if expected.width() > rect.width() or expected.height() > rect.height():
        raise AssertionError(f'Qt5 spin {state} arrow {expected.size()} exceeds button {rect.size()}')
    x = rect.x() + (rect.width() - expected.width()) // 2
    y = rect.y() + (rect.height() - expected.height()) // 2
    differences = sum(
        expected.pixelColor(ix, iy).alpha() > 0 and
        actual.pixel(x + ix, y + iy) != expected.pixel(ix, iy)
        for iy in range(expected.height()) for ix in range(expected.width()))
    if differences:
        actual.copy(x, y, expected.width(), expected.height()).save(
            str(args.output / f'spin-arrow-{state}-actual.png'), 'PNG')
        expected.save(str(args.output / f'spin-arrow-{state}-expected.png'), 'PNG')
        raise AssertionError(
            f'Qt5 spin {state} arrow asset differs by {differences} pixels; '
            f'button={rect.getRect()} asset=({x},{y},{expected.width()},{expected.height()})')
    return {'rect': [x, y, expected.width(), expected.height()], 'pixelDifferences': differences}


def exercise_text_edit(stylesheet):
    editor = QTextEdit('Native Qt5 multiline text')
    editor.setObjectName('domainosRecipeText')
    editor.resize(480, 120)
    editor.setStyleSheet(stylesheet.read_text(encoding='utf-8'))
    editor.show()
    QApplication.processEvents()
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key_End)
    QTest.keyClick(editor, Qt.Key_X)
    QApplication.processEvents()
    native_edit = editor.toPlainText().endswith('x')
    editor.selectAll()
    QApplication.processEvents()
    cursor = editor.textCursor()
    selection = cursor.hasSelection() and cursor.selectedText() == editor.toPlainText()

    def css_color(selector, property_name):
        source = stylesheet.read_text(encoding='utf-8')
        block = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', source)
        match = re.search(re.escape(property_name) + r':\s*(#[0-9a-fA-F]{6})',
                           block.group(1) if block else '')
        if not match:
            raise AssertionError(f'Qt5 text stylesheet lacks {property_name} in {selector}')
        return match.group(1).lower()

    normal_image = editor.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    point = QPoint(max(1, editor.width() - 8), max(1, editor.height() - 8))
    normal_pixel = normal_image.pixelColor(point).name().lower()
    expected_normal = css_color('QTextEdit#domainosRecipeText', 'background-color')
    selection_background = css_color('QTextEdit#domainosRecipeText', 'selection-background-color')
    selection_foreground = css_color('QTextEdit#domainosRecipeText', 'selection-color')
    editor.setEnabled(False)
    QApplication.processEvents()
    disabled_image = editor.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    expected_disabled = css_color('QTextEdit#domainosRecipeText:disabled', 'background-color')
    disabled_pixel = disabled_image.pixelColor(point).name().lower()
    proof = {
        'widgetClass': editor.metaObject().className(), 'objectName': editor.objectName(),
        'nativeEditWorked': native_edit, 'selectionWorked': selection,
        'selectedText': cursor.selectedText(), 'selectionBackground': selection_background,
        'selectionForeground': selection_foreground, 'disabled': not editor.isEnabled(),
        'normalFacePixel': normal_pixel, 'expectedNormalFace': expected_normal,
        'disabledFacePixel': disabled_pixel, 'expectedDisabledFace': expected_disabled,
        'sizeHint': [editor.sizeHint().width(), editor.sizeHint().height()]}
    editor.close()
    QApplication.processEvents()
    if (not native_edit or not selection or editor.isEnabled() or
            normal_pixel != expected_normal or disabled_pixel != expected_disabled):
        raise AssertionError(
            'Qt5 QTextEdit recipe did not preserve native editing/selection/disabled behavior or KDE-role face colors: '
            f'normal={normal_pixel}/{expected_normal}, disabled={disabled_pixel}/{expected_disabled}.')
    return proof


def exercise_scales(stylesheet, output):
    host = QWidget()
    layout = QHBoxLayout(host)
    layout.setContentsMargins(16, 16, 16, 16)
    horizontal = QSlider(Qt.Horizontal)
    horizontal.setObjectName('domainosRecipeScaleHorizontal')
    vertical = QSlider(Qt.Vertical)
    vertical.setObjectName('domainosRecipeScaleVertical')
    for slider in (horizontal, vertical):
        slider.setRange(0, 100)
        slider.setSingleStep(5)
        slider.setPageStep(20)
        slider.setValue(25)
        slider.setMinimumWidth(240 if slider is horizontal else 32)
    vertical.setMinimumHeight(120)
    layout.addWidget(horizontal, 1)
    layout.addWidget(vertical)
    host.resize(380, 180)
    host.setStyleSheet(stylesheet.read_text(encoding='utf-8'))
    host.show()
    QApplication.processEvents()
    proof = {}
    for name, slider, subcontrol, point_fn, key in (
            ('horizontal', horizontal, QStyle.SC_SliderGroove,
             lambda rect: QPoint(max(rect.left(), rect.right() - 3), rect.center().y()), Qt.Key_Right),
            ('vertical', vertical, QStyle.SC_SliderGroove,
             lambda rect: QPoint(rect.center().x(), min(rect.bottom(), rect.top() + 3)), Qt.Key_Up)):
        initial = slider.value()
        option = QStyleOptionSlider()
        slider.initStyleOption(option)
        groove = slider.style().subControlRect(QStyle.CC_Slider, option, subcontrol, slider)
        if groove.isEmpty() or not slider.rect().contains(groove):
            raise AssertionError(f'Qt5 {name} slider has no native groove allocation: {groove}')
        QTest.mouseClick(slider, Qt.LeftButton, pos=point_fn(groove))
        QApplication.processEvents()
        after_mouse = slider.value()
        slider.setValue(40)
        before_key = slider.value()
        QTest.keyClick(slider, key)
        QApplication.processEvents()
        after_key = slider.value()
        slider.setEnabled(False)
        QApplication.processEvents()
        proof[name] = {
            'widgetClass': slider.metaObject().className(), 'objectName': slider.objectName(),
            'orientation': 'horizontal' if slider.orientation() == Qt.Horizontal else 'vertical',
            'grooveRect': list(groove.getRect()), 'initialValue': initial,
            'valueAfterMouse': after_mouse, 'valueBeforeKey': before_key,
            'valueAfterKey': after_key, 'disabled': not slider.isEnabled(),
            'sizeHint': [slider.sizeHint().width(), slider.sizeHint().height()]}
        if (after_mouse == initial or after_key == before_key or slider.isEnabled()):
            raise AssertionError(f'Qt5 {name} QSlider lost mouse, keyboard or disabled behavior: {proof[name]}')
    screenshot = output / 'qt5-scales.png'
    proof['screenshotSaved'] = host.grab().save(str(screenshot), 'PNG')
    proof['screenshot'] = str(screenshot)
    host.close()
    QApplication.processEvents()
    if not proof['screenshotSaved']:
        raise AssertionError('Qt5 scale screenshot could not be saved.')
    return proof


def assert_combo_arrow_asset(widget, asset_path, background, state):
    from PyQt5.QtGui import QColor
    rect = combo_arrow_rect(widget)
    actual = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    expected = QImage(str(asset_path)).convertToFormat(QImage.Format_ARGB32)
    if expected.width() > rect.width() or expected.height() > rect.height():
        raise AssertionError(f'Qt5 combo arrow asset {expected.size()} exceeds native arrow allocation {rect.size()}')
    stylesheet = Path(args.stylesheet).read_text(encoding='utf-8')
    drop_down = re.search(r'QComboBox#domainosRecipeCombo::drop-down\s*\{([^}]*)\}', stylesheet)
    divider = re.search(r'border-left:\s*(\d+)px', drop_down.group(1) if drop_down else '')
    if not divider:
        raise AssertionError('Qt5 combo dropdown has no generated relief divider width')
    divider_px = int(divider.group(1))
    x = rect.x() + divider_px + (rect.width() - divider_px - expected.width()) // 2
    y = rect.y() + (rect.height() - expected.height()) // 2
    composited = QImage(expected.size(), QImage.Format_ARGB32)
    composited.fill(QColor(background))
    painter = QPainter(composited)
    painter.drawImage(0, 0, expected)
    painter.end()
    differences = sum(actual.pixel(x + ix, y + iy) != composited.pixel(ix, iy)
                      for iy in range(expected.height()) for ix in range(expected.width()))
    if differences:
        actual.save(str(args.output / f'combo-arrow-{state}-widget.png'), 'PNG')
        actual.copy(x, y, expected.width(), expected.height()).save(
            str(args.output / f'combo-arrow-{state}-actual.png'), 'PNG')
        composited.save(str(args.output / f'combo-arrow-{state}-expected.png'), 'PNG')
        raise AssertionError(f'Qt5 combo {state} arrow differs from its generated KDE-role asset by {differences} pixels; subcontrol={rect.getRect()} divider={divider_px}px asset_origin=({x},{y})')
    for other_y in range(0, widget.height() - expected.height() + 1):
        for other_x in range(0, max(0, rect.left() - expected.width())):
            duplicate = all(actual.pixel(other_x + ix, other_y + iy) == composited.pixel(ix, iy)
                            for iy in range(expected.height()) for ix in range(expected.width()))
            if duplicate:
                raise AssertionError(f'Qt5 combo {state} arrow asset also appears outside the dropdown at ({other_x},{other_y})')
    return {'rect': [x, y, expected.width(), expected.height()], 'pixelDifferences': differences}


def assert_indicator_asset(widget, asset_path, state):
    rect = check_indicator_rect(widget)
    actual = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    expected = QImage(str(asset_path)).convertToFormat(QImage.Format_ARGB32)
    if expected.size() != rect.size():
        raise AssertionError(f'Qt5 checkbox {state} indicator size {rect.size()} differs from generated asset {expected.size()}')
    stylesheet = Path(args.stylesheet).read_text(encoding='utf-8')
    block = re.search(r'QCheckBox#domainosRecipeCheckBox::indicator\s*\{([^}]*)\}', stylesheet)
    background = re.search(r'background-color:\s*(#[0-9a-fA-F]{6})', block.group(1) if block else '')
    if not background:
        raise AssertionError('Qt5 checkbox indicator has no generated KDE-role background')
    composited = QImage(expected.size(), QImage.Format_ARGB32)
    composited.fill(QColor(background.group(1)))
    painter = QPainter(composited)
    painter.drawImage(0, 0, expected)
    painter.end()
    differences = sum(actual.pixel(rect.x() + x, rect.y() + y) != composited.pixel(x, y)
                      for y in range(rect.height()) for x in range(rect.width()))
    if differences:
        actual.copy(rect).save(str(args.output / f'checkbox-{state}-actual.png'), 'PNG')
        composited.save(str(args.output / f'checkbox-{state}-expected.png'), 'PNG')
        raise AssertionError(f'Qt5 checkbox {state} indicator differs from its generated KDE-role asset by {differences} pixels')
    return {'rect': [rect.x(), rect.y(), rect.width(), rect.height()], 'pixelDifferences': differences}


def assert_radio_asset(widget, asset_path, state):
    rect = radio_indicator_rect(widget)
    actual = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    expected = QImage(str(asset_path)).convertToFormat(QImage.Format_ARGB32)
    if expected.size() != rect.size():
        raise AssertionError(f'Qt5 radio {state} indicator size {rect.size()} differs from generated asset {expected.size()}')
    stylesheet = Path(args.stylesheet).read_text(encoding='utf-8')
    block = re.search(r'QRadioButton#domainosRecipeRadioButton::indicator[^\{]*\{([^}]*)\}', stylesheet)
    background = re.search(r'background-color:\s*(#[0-9a-fA-F]{6})', block.group(1) if block else '')
    if not background:
        raise AssertionError('Qt5 radio indicator has no generated KDE-role background')
    composited = QImage(expected.size(), QImage.Format_ARGB32)
    composited.fill(QColor(background.group(1)))
    painter = QPainter(composited)
    painter.drawImage(0, 0, expected)
    painter.end()
    differences = sum(actual.pixel(rect.x() + x, rect.y() + y) != composited.pixel(x, y)
                      for y in range(rect.height()) for x in range(rect.width()))
    if differences:
        actual.copy(rect).save(str(args.output / f'radio-{state}-actual.png'), 'PNG')
        composited.save(str(args.output / f'radio-{state}-expected.png'), 'PNG')
        raise AssertionError(f'Qt5 radio {state} indicator differs from its generated KDE-role asset by {differences} pixels')
    return {'rect': [rect.x(), rect.y(), rect.width(), rect.height()], 'pixelDifferences': differences}


def main():
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    app = QApplication(sys.argv[:1])
    app.setStyle('Fusion')
    text_proof = exercise_text_edit(args.stylesheet)
    scale_proof = exercise_scales(args.stylesheet, args.output)
    window = QWidget()
    layout = QVBoxLayout(window)
    push = QPushButton('Native Qt5 recipe push')
    push.setObjectName('domainosRecipePushButton')
    layout.addWidget(push)
    check = QCheckBox('Native Qt5 recipe checkbox')
    check.setObjectName('domainosRecipeCheckBox')
    check.setChecked(False)
    layout.addWidget(check)
    radio_group = QWidget()
    radio_layout = QVBoxLayout(radio_group)
    radio = QRadioButton('Native Qt5 radio A')
    radio.setObjectName('domainosRecipeRadioButton')
    radio_peer = QRadioButton('Native Qt5 radio B')
    radio_peer.setObjectName('domainosRecipeRadioPeer')
    radio_group_buttons = QButtonGroup(radio_group)
    radio_group_buttons.setExclusive(True)
    radio_group_buttons.addButton(radio)
    radio_group_buttons.addButton(radio_peer)
    radio.setChecked(True)
    radio_layout.addWidget(radio)
    radio_layout.addWidget(radio_peer)
    layout.addWidget(radio_group)
    entry = QLineEdit('Native Qt5 entry')
    entry.setObjectName('domainosRecipeEntry')
    layout.addWidget(entry)
    combo = QComboBox()
    combo.setObjectName('domainosRecipeCombo')
    combo.addItems(['Classic', 'DomainOS SR10.4', 'A long selectable menu option'])
    combo.view().setObjectName('domainosRecipeComboPopup')
    layout.addWidget(combo)
    spin = QSpinBox()
    spin.setObjectName('domainosRecipeSpinBox')
    spin.setRange(0, 100)
    spin.setValue(42)
    layout.addWidget(spin)
    decimal_spin = QDoubleSpinBox()
    decimal_spin.setObjectName('domainosRecipeDoubleSpinBox')
    decimal_spin.setDecimals(1)
    decimal_spin.setSingleStep(0.1)
    decimal_spin.setRange(0.0, 20.0)
    decimal_spin.setValue(10.4)
    layout.addWidget(decimal_spin)
    toggle = QPushButton('')
    toggle.setObjectName('domainosRecipeToggleButton')
    toggle.setCheckable(True)
    layout.addWidget(toggle)
    area = QScrollArea()
    area.setObjectName('domainosScrollArea')
    area.setWindowTitle('Qt5 DomainOS scrollbar native widget probe')
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Box)
    content = QWidget()
    content.setMinimumSize(650, 620)
    content_layout = QVBoxLayout(content)
    for index in range(24):
        content_layout.addWidget(QPushButton(f'Native Qt5 content {index + 1}'))
    area.setWidget(content)
    install_scrollbar_painters(area, args.assets)
    spacing_adapter = install_scrollbar_spacing(area, 4, 5)
    vertical, horizontal = area.verticalScrollBar(), area.horizontalScrollBar()
    window.setStyleSheet(args.stylesheet.read_text(encoding='utf-8'))
    layout.addWidget(area)
    window.resize(520, 430)
    window.show()
    app.processEvents()
    result = {'status': 'running', 'qtMajor': 5, 'style': app.style().metaObject().className(),
              'axes': {}, 'textEdit': text_proof, 'scales': scale_proof,
              'scope': 'real PyQt5 QTextEdit/QScrollArea/QScrollBar; per-widget measured viewport margin plus generated QSS',
              'scrollSpacingAdapter': spacing_adapter}

    click_count = []
    push.clicked.connect(lambda: click_count.append(True))
    push_normal = push.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    point = push.rect().center()
    QTest.mousePress(push, Qt.LeftButton, pos=point)
    app.processEvents()
    push_held = push.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    push_held_changes = difference(push_normal, push_held, push.rect())
    QTest.mouseRelease(push, Qt.LeftButton, pos=point)
    app.processEvents()
    push_released = push.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    push_release_changes = difference(push_normal, push_released, push.rect())
    result['pushButton'] = {
        'widgetClass': push.metaObject().className(), 'objectName': push.objectName(),
        'sizeHint': [push.sizeHint().width(), push.sizeHint().height()],
        'allocation': [push.width(), push.height()],
        'heldReliefPixelChanges': push_held_changes,
        'releasePixelChanges': push_release_changes,
        'clickCount': len(click_count)}
    if push_held_changes <= 0 or push_release_changes != 0 or len(click_count) != 1:
        raise AssertionError('Qt5 recipe push state/click did not survive press-release.')

    check_unchecked = check.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    check_off_pixels = assert_indicator_asset(check, args.assets / 'check-off-normal.png', 'unchecked')
    QTest.mouseClick(check, Qt.LeftButton, pos=check.rect().center())
    app.processEvents()
    check_checked = check.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    check_checked_changes = difference(check_unchecked, check_checked, check.rect())
    checked_after_click = check.isChecked()
    check_on_pixels = assert_indicator_asset(check, args.assets / 'check-on-normal.png', 'checked')
    QTest.mouseClick(check, Qt.LeftButton, pos=check.rect().center())
    app.processEvents()
    check_released = check.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    check_restored_changes = difference(check_unchecked, check_released, check.rect())
    result['checkBox'] = {
        'widgetClass': check.metaObject().className(), 'objectName': check.objectName(),
        'checkedAfterClick': checked_after_click,
        'checkedPixelChanges': check_checked_changes,
        'uncheckedAsset': check_off_pixels,
        'checkedAsset': check_on_pixels,
        'uncheckedAfterSecondClick': not check.isChecked(),
        'restoredPixelChanges': check_restored_changes}
    if (not checked_after_click or check_checked_changes <= 0 or check.isChecked() or
            check_restored_changes != 0):
        raise AssertionError('Qt5 recipe checkbox did not toggle and restore the exact unchecked pixels.')

    radio_unselected = assert_radio_asset(radio_peer, args.assets / 'radio-off-normal.png', 'unchecked')
    radio_selected = assert_radio_asset(radio, args.assets / 'radio-on-normal.png', 'checked')
    radio_before = radio.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    QTest.mouseClick(radio_peer, Qt.LeftButton, pos=radio_peer.rect().center())
    app.processEvents()
    radio_after = radio.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    peer_after = radio_peer.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    radio_changes = difference(radio_before, radio_after, radio.rect())
    peer_on = assert_radio_asset(radio_peer, args.assets / 'radio-on-normal.png', 'checked')
    radio_off = assert_radio_asset(radio, args.assets / 'radio-off-normal.png', 'unchecked')
    if radio.isChecked() or not radio_peer.isChecked() or radio_changes <= 0:
        raise AssertionError('QRadioButton group did not transfer selection to the clicked peer.')
    transferred = not radio.isChecked() and radio_peer.isChecked()
    QTest.mouseClick(radio, Qt.LeftButton, pos=radio.rect().center())
    app.processEvents()
    if not radio.isChecked() or radio_peer.isChecked():
        raise AssertionError('QRadioButton group did not restore exclusive selection after the second click.')
    result['radioButtons'] = {
        'widgetClass': radio.metaObject().className(),
        'exclusiveGroup': radio_group_buttons.exclusive(),
        'selectedAfterPeerClick': transferred,
        'selectionPixelChanges': radio_changes,
        'initialUncheckedAsset': radio_unselected,
        'initialCheckedAsset': radio_selected,
        'peerCheckedAsset': peer_on,
        'radioUncheckedAsset': radio_off,
        'returnedToFirst': radio.isChecked() and not radio_peer.isChecked()}

    stylesheet = Path(args.stylesheet).read_text(encoding='utf-8')
    def css_color(selector, property_name):
        block = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', stylesheet)
        match = re.search(re.escape(property_name) + r':\s*(#[0-9a-fA-F]{6})', block.group(1) if block else '')
        if not match:
            raise AssertionError(f'Qt5 entry stylesheet lacks {property_name} in {selector}')
        return match.group(1).lower()

    entry_normal = entry.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    entry_point = QPoint(max(1, entry.width() - 8), max(1, entry.height() // 2))
    expected_normal_face = css_color('QLineEdit#domainosRecipeEntry', 'background-color')
    normal_face_pixel = entry_normal.pixelColor(entry_point).name().lower()
    entry.setFocus()
    app.processEvents()
    entry_focused = entry.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    focus_changes = difference(entry_normal, entry_focused, entry.rect())
    focused = entry.hasFocus()
    QTest.keyClick(entry, Qt.Key_End)
    QTest.keyClick(entry, Qt.Key_X)
    app.processEvents()
    native_edit_worked = entry.text().endswith('x')
    entry.selectAll()
    app.processEvents()
    selection_worked = entry.hasSelectedText() and entry.selectedText() == entry.text()
    selection_background = css_color('QLineEdit#domainosRecipeEntry', 'selection-background-color')
    selection_foreground = css_color('QLineEdit#domainosRecipeEntry', 'selection-color')
    entry.setEnabled(False)
    app.processEvents()
    entry_disabled = entry.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    expected_disabled_face = css_color('QLineEdit#domainosRecipeEntry:disabled', 'background-color')
    disabled_face_pixel = entry_disabled.pixelColor(entry_point).name().lower()
    result['entry'] = {
        'widgetClass': entry.metaObject().className(), 'objectName': entry.objectName(),
        'focused': focused, 'focusPixelChanges': focus_changes,
        'nativeEditWorked': native_edit_worked, 'selectionWorked': selection_worked,
        'selectionBackground': selection_background, 'selectionForeground': selection_foreground,
        'disabled': not entry.isEnabled(),
        'normalFacePixel': normal_face_pixel, 'expectedNormalFace': expected_normal_face,
        'disabledFacePixel': disabled_face_pixel, 'expectedDisabledFace': expected_disabled_face}
    if (not focused or focus_changes <= 0 or not native_edit_worked or not selection_worked or
            entry.isEnabled() or normal_face_pixel != expected_normal_face or
            disabled_face_pixel != expected_disabled_face):
        raise AssertionError('Qt5 QLineEdit recipe did not preserve native focus/edit/selection/disabled state or KDE-role face colors.')

    def combo_css_color(selector, property_name):
        block = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', stylesheet)
        match = re.search(re.escape(property_name) + r':\s*(#[0-9a-fA-F]{6})', block.group(1) if block else '')
        if not match:
            raise AssertionError(f'Qt5 combo stylesheet lacks {property_name} in {selector}')
        return match.group(1).lower()

    combo_normal_color = combo_css_color('QComboBox#domainosRecipeCombo', 'background-color')
    combo_size = [combo.sizeHint().width(), combo.sizeHint().height()]
    combo_normal_image = combo.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    combo_normal_face_pixel = combo_face_pixel(combo, combo_normal_image)
    combo_normal_arrow = assert_combo_arrow_asset(
        combo, args.assets / 'combo-arrow-down-normal.png', combo_normal_color, 'normal')
    combo.showPopup()
    app.processEvents()
    popup_opened = combo.view().isVisible()
    target = combo.view().model().index(2, 0)
    target_rect = combo.view().visualRect(target)
    if not popup_opened or target_rect.isEmpty():
        raise AssertionError('Qt5 combo popup did not expose its native third option.')
    combo.view().setCurrentIndex(target)
    combo.view().selectionModel().select(target, QItemSelectionModel.ClearAndSelect)
    app.processEvents()
    target_rect = combo.view().visualRect(target)
    popup_selection_image = combo.view().viewport().grab().toImage().convertToFormat(QImage.Format_ARGB32)
    popup_selection_image.save(str(args.output / 'qt5-combo-popup-selection.png'), 'PNG')
    popup_selection_role = combo_css_color(
        'QAbstractItemView#domainosRecipeComboPopup::item:selected', 'background-color')
    popup_image_rect = popup_selection_image.rect()
    popup_sample_rect = target_rect.intersected(popup_image_rect)
    if popup_sample_rect.isEmpty():
        popup_selection_image.save(str(args.output / 'qt5-combo-popup-selection.png'), 'PNG')
        raise AssertionError(
            'Qt5 combo popup target row is outside captured viewport: '
            f'row={target_rect}, image={popup_image_rect}.')
    popup_selection_point = QPoint(max(popup_sample_rect.left(), popup_sample_rect.right() - 2),
                                   popup_sample_rect.center().y())
    popup_selection_pixel = popup_selection_image.pixelColor(popup_selection_point).name().lower()
    QTest.mouseClick(combo.view().viewport(), Qt.LeftButton, pos=target_rect.center())
    app.processEvents()
    selected_index = combo.currentIndex()
    popup_closed_after_selection = not combo.view().isVisible()
    combo.setEnabled(False)
    app.processEvents()
    QTest.qWait(50)
    app.processEvents()
    combo_disabled = not combo.isEnabled()
    combo_disabled_color = combo_css_color('QComboBox#domainosRecipeCombo:disabled', 'background-color')
    combo_disabled_image = combo.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    combo_disabled_image.save(str(args.output / 'qt5-combo-disabled.png'), 'PNG')
    combo_disabled_face_pixel = combo_face_pixel(combo, combo_disabled_image)
    combo_disabled_arrow = assert_combo_arrow_asset(
        combo, args.assets / 'combo-arrow-down-disabled.png', combo_disabled_color, 'disabled')
    result['comboBox'] = {
        'widgetClass': combo.metaObject().className(),
        'objectName': combo.objectName(),
        'popupObjectName': combo.view().objectName(),
        'popupOpened': popup_opened,
        'nativeSelectionWorked': selected_index == 2,
        'selectedIndex': selected_index,
        'popupClosedAfterSelection': popup_closed_after_selection,
        'popupSelectionImageSize': [popup_selection_image.width(), popup_selection_image.height()],
        'popupSelectionRowRect': [target_rect.x(), target_rect.y(), target_rect.width(), target_rect.height()],
        'popupSelectionRole': popup_selection_role,
        'popupSelectionPixel': popup_selection_pixel,
        'popupSelectionPixelMatchesRole': popup_selection_pixel == popup_selection_role,
        'platform': app.platformName(),
        'disabled': combo_disabled,
        'sizeHint': combo_size,
        'normalFaceRole': combo_normal_color,
        'normalFacePixel': combo_normal_face_pixel,
        'normalArrowAsset': combo_normal_arrow,
        'disabledFaceRole': combo_disabled_color,
        'disabledFacePixel': combo_disabled_face_pixel,
        'disabledArrowAsset': combo_disabled_arrow}
    if (selected_index != 2 or not popup_closed_after_selection or not combo_disabled or
            combo_normal_face_pixel != combo_normal_color or
            combo_disabled_face_pixel != combo_disabled_color or
            (app.platformName() == 'xcb' and popup_selection_pixel != popup_selection_role)):
        raise AssertionError(
            'Qt5 QComboBox state mismatch: '
            f'selected={selected_index}, popup_closed={popup_closed_after_selection}, '
            f'disabled={combo_disabled}, normal_face={combo_normal_face_pixel}/{combo_normal_color}, '
            f'disabled_face={combo_disabled_face_pixel}/{combo_disabled_color}, '
            f'popup_selection={popup_selection_pixel}/{popup_selection_role}.')

    spin_initial = spin.value()
    spin_up_asset = assert_spin_arrow_asset(
        spin, args.assets / 'spin-arrow-up-normal.png', QStyle.SC_SpinBoxUp, 'normal-up')
    spin_down_asset = assert_spin_arrow_asset(
        spin, args.assets / 'spin-arrow-down-normal.png', QStyle.SC_SpinBoxDown, 'normal-down')
    decimal_up_asset = assert_spin_arrow_asset(
        decimal_spin, args.assets / 'spin-arrow-up-normal.png', QStyle.SC_SpinBoxUp, 'decimal-up')
    spin_up_rect = spin_button_rect(spin, QStyle.SC_SpinBoxUp)
    QTest.mouseClick(spin, Qt.LeftButton, pos=spin_up_rect.center())
    app.processEvents()
    spin_after_up = spin.value()
    spin_down_rect = spin_button_rect(spin, QStyle.SC_SpinBoxDown)
    QTest.mouseClick(spin, Qt.LeftButton, pos=spin_down_rect.center())
    app.processEvents()
    spin_after_down = spin.value()
    spin.setFocus()
    QTest.keyClick(spin, Qt.Key_Up)
    app.processEvents()
    spin_keyboard_step = spin.value()

    decimal_initial = decimal_spin.value()
    decimal_up_rect = spin_button_rect(decimal_spin, QStyle.SC_SpinBoxUp)
    QTest.mouseClick(decimal_spin, Qt.LeftButton, pos=decimal_up_rect.center())
    app.processEvents()
    decimal_after_up = decimal_spin.value()
    decimal_down_rect = spin_button_rect(decimal_spin, QStyle.SC_SpinBoxDown)
    QTest.mouseClick(decimal_spin, Qt.LeftButton, pos=decimal_down_rect.center())
    app.processEvents()
    decimal_after_down = decimal_spin.value()

    spin.setEnabled(False)
    decimal_spin.setEnabled(False)
    app.processEvents()
    spin_disabled_up_asset = assert_spin_arrow_asset(
        spin, args.assets / 'spin-arrow-up-disabled.png', QStyle.SC_SpinBoxUp, 'disabled-up')
    spin_disabled_down_asset = assert_spin_arrow_asset(
        spin, args.assets / 'spin-arrow-down-disabled.png', QStyle.SC_SpinBoxDown, 'disabled-down')
    decimal_disabled = not decimal_spin.isEnabled()
    spin_disabled = not spin.isEnabled()
    result['spinBoxes'] = {
        'integer': {
            'widgetClass': spin.metaObject().className(), 'objectName': spin.objectName(),
            'initialValue': spin_initial, 'valueAfterUp': spin_after_up,
            'valueAfterDown': spin_after_down, 'valueAfterKeyboardUp': spin_keyboard_step,
            'upArrowAsset': spin_up_asset, 'downArrowAsset': spin_down_asset,
            'disabledUpArrowAsset': spin_disabled_up_asset,
            'disabledDownArrowAsset': spin_disabled_down_asset, 'disabled': spin_disabled,
            'sizeHint': [spin.sizeHint().width(), spin.sizeHint().height()]},
        'decimal': {
            'widgetClass': decimal_spin.metaObject().className(),
            'objectName': decimal_spin.objectName(), 'initialValue': decimal_initial,
            'valueAfterUp': decimal_after_up, 'valueAfterDown': decimal_after_down,
            'upArrowAsset': decimal_up_asset, 'disabled': decimal_disabled,
            'sizeHint': [decimal_spin.sizeHint().width(), decimal_spin.sizeHint().height()]}}
    if (spin_after_up != 43 or spin_after_down != 42 or spin_keyboard_step != 43 or
            decimal_after_up != 10.5 or decimal_after_down != 10.4 or
            not spin_disabled or not decimal_disabled):
        raise AssertionError(
            'Qt5 spin controls lost native numeric stepping, keyboard, or disabled state: '
            f'integer={spin_initial}/{spin_after_up}/{spin_after_down}/{spin_keyboard_step}, '
            f'decimal={decimal_initial}/{decimal_after_up}/{decimal_after_down}.')

    toggle_normal = toggle.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    QTest.mouseClick(toggle, Qt.LeftButton, pos=toggle.rect().center())
    app.processEvents()
    toggle_checked = toggle.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    toggle_checked_changes = difference(toggle_normal, toggle_checked, toggle.rect())
    checked_after_click = toggle.isChecked()
    QTest.mouseClick(toggle, Qt.LeftButton, pos=toggle.rect().center())
    app.processEvents()
    toggle_released = toggle.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    toggle_restored_changes = difference(toggle_normal, toggle_released, toggle.rect())
    checked_after_second_click = toggle.isChecked()
    result['toggleButton'] = {
        'widgetClass': toggle.metaObject().className(), 'objectName': toggle.objectName(),
        'checkable': toggle.isCheckable(), 'checkedAfterClick': checked_after_click,
        'checkedPixelChanges': toggle_checked_changes,
        'checkedAfterSecondClick': checked_after_second_click,
        'restoredPixelChanges': toggle_restored_changes}
    if (not toggle.isCheckable() or not checked_after_click or toggle_checked_changes <= 0 or
            checked_after_second_click or toggle_restored_changes != 0):
        raise AssertionError('Qt5 recipe toggle did not remain selected and restore on second click.')

    def exercise(axis, widget, controls):
        if not widget.isVisible() or widget.maximum() <= 0:
            raise AssertionError(f'{axis} scrollbar is not visible and scrollable')
        widget.setValue(widget.maximum() // 2)
        app.processEvents()
        cells = {}
        for direction, subcontrol, step in controls:
            rect = line_rect(widget, subcontrol)
            point = rect.center()
            QTest.mouseMove(widget, point)
            app.processEvents()
            normal = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
            before = widget.value()
            QTest.mousePress(widget, Qt.LeftButton, pos=point)
            app.processEvents()
            held = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
            changes_held = difference(normal, held, rect)
            QTest.mouseRelease(widget, Qt.LeftButton, pos=point)
            QTest.mouseMove(widget, QPoint(0, 0))
            app.processEvents()
            released = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
            changes_release = difference(normal, released, rect)
            after = widget.value()
            expected = max(0, min(widget.maximum(), before + step * widget.singleStep()))
            if changes_held <= 0:
                raise AssertionError(f'{direction} arrow did not change relief while held')
            if changes_release != 0:
                raise AssertionError(f'{direction} arrow relief did not return to normal: {changes_release} pixels')
            if after != expected:
                raise AssertionError(f'{direction} changed value to {after}, expected {expected}')
            cells[direction] = {'rect': [rect.x(), rect.y(), rect.width(), rect.height()],
                                'valueBefore': before, 'valueAfter': after,
                                'heldReliefPixelChanges': changes_held,
                                'releasePixelChanges': changes_release}
        return cells

    result['axes']['vertical'] = {'allocation': [vertical.width(), vertical.height()],
                                  'visible': vertical.isVisible(), 'maximum': vertical.maximum(),
                                  'cells': exercise('vertical', vertical,
                                      (('up', QStyle.SC_ScrollBarSubLine, -1),
                                       ('down', QStyle.SC_ScrollBarAddLine, 1)))}
    result['axes']['horizontal'] = {'allocation': [horizontal.width(), horizontal.height()],
                                    'visible': horizontal.isVisible(), 'maximum': horizontal.maximum(),
                                    'cells': exercise('horizontal', horizontal,
                                        (('left', QStyle.SC_ScrollBarSubLine, -1),
                                         ('right', QStyle.SC_ScrollBarAddLine, 1)))}
    result['standaloneArrow'] = exercise_standalone_arrow(Path(args.stylesheet))
    result['progressBar'] = exercise_progress(Path(args.stylesheet))
    if vertical.width() != 15 or horizontal.height() != 15:
        raise AssertionError(f'Qt5 allocation differs from the requested 15px cross-size: {result["axes"]}')
    result['status'] = 'passed'
    window.close()
    app.processEvents()
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


raise SystemExit(main())
