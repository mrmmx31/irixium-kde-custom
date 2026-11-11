#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure the per-widget Qt scroll gap in real Qt5/Qt6 widgets on Xephyr."""
import argparse
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--qt-major', type=int, choices=(5, 6), required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()

if args.qt_major == 5:
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtGui import QImage, QPalette
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
        QPlainTextEdit, QScrollArea, QStyle, QStyleOptionSlider,
        QVBoxLayout, QWidget)
else:
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtGui import QImage, QPalette
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
        QPlainTextEdit, QScrollArea, QStyle, QStyleOptionSlider,
        QVBoxLayout, QWidget)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'plasma/tests/galerias-nativas'))
from qt_scrollbar_spacing import install_scrollbar_spacing, finalize_scrollbar_spacing


def point_in(widget, target):
    p = widget.mapTo(target, QPoint(0, 0))
    return [p.x(), p.y(), widget.width(), widget.height()]


def palette_snapshot(widget):
    palette = widget.palette()
    groups = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive,
              QPalette.ColorGroup.Disabled) if args.qt_major == 6 else (
              QPalette.Active, QPalette.Inactive, QPalette.Disabled)
    roles = ('Window', 'WindowText', 'Base', 'Text', 'Button', 'ButtonText',
             'Highlight', 'HighlightedText')
    result = {}
    for group_name, group in zip(('active', 'inactive', 'disabled'), groups):
        result[group_name] = {}
        for name in roles:
            role = getattr(QPalette.ColorRole, name) if args.qt_major == 6 else getattr(QPalette, name)
            result[group_name][name] = palette.color(group, role).name()
    return result


def arrow_rect(bar, subcontrol):
    option = QStyleOptionSlider()
    option.initFrom(bar)
    option.orientation = bar.orientation()
    option.minimum, option.maximum = bar.minimum(), bar.maximum()
    option.sliderPosition, option.sliderValue = bar.sliderPosition(), bar.value()
    option.pageStep, option.singleStep = bar.pageStep(), bar.singleStep()
    rect = bar.style().subControlRect(QStyle.ComplexControl.CC_ScrollBar,
                                      option, subcontrol, bar)
    if rect.isEmpty() or not bar.rect().contains(rect):
        raise AssertionError('native scrollbar arrow subcontrol has no in-bar geometry')
    return rect


def image(widget):
    fmt = QImage.Format.Format_ARGB32 if args.qt_major == 6 else QImage.Format_ARGB32
    return widget.grab().toImage().convertToFormat(fmt)


def compare_arrows(base, adapted, orientation, name):
    if base.size() != adapted.size():
        raise AssertionError(f'{name}: proxy changed scrollbar allocation size')
    base.setValue(base.maximum() // 2)
    adapted.setValue(adapted.maximum() // 2)
    QApplication.processEvents()
    initial_value = adapted.value()
    subline = (QStyle.SC_ScrollBarSubLine if args.qt_major == 5 else
               QStyle.SubControl.SC_ScrollBarSubLine)
    base_line = arrow_rect(base, subline)
    line = arrow_rect(adapted, subline)
    if base_line != line:
        raise AssertionError(f'{name}: spacing proxy changed the native arrow cell geometry')
    normal_base, normal = image(base), image(adapted)
    normal_arrow_diff = sum(normal_base.pixel(x, y) != normal.pixel(x, y)
                            for y in range(line.top(), line.bottom() + 1)
                            for x in range(line.left(), line.right() + 1))
    if normal_arrow_diff:
        raise AssertionError(f'{name}: native arrow pixels changed under proxy: {normal_arrow_diff}')
    if orientation == 'vertical':
        point = line.center()
    else:
        point = line.center()
    QTest.mousePress(adapted, Qt.LeftButton if args.qt_major == 5 else Qt.MouseButton.LeftButton,
                     pos=point)
    QApplication.processEvents()
    held = image(adapted)
    QTest.mouseRelease(adapted, Qt.LeftButton if args.qt_major == 5 else Qt.MouseButton.LeftButton,
                       pos=point)
    adapted.setValue(initial_value)
    QApplication.processEvents()
    released = image(adapted)
    changed_held = sum(normal.pixel(x, y) != held.pixel(x, y)
                       for y in range(line.top(), line.bottom() + 1)
                       for x in range(line.left(), line.right() + 1))
    changed_release = sum(normal.pixel(x, y) != released.pixel(x, y)
                          for y in range(line.top(), line.bottom() + 1)
                          for x in range(line.left(), line.right() + 1))
    if changed_held <= 0 or changed_release != 0:
        raise AssertionError(f'{name}: native pressed/released arrow state did not return exactly')
    return {'normalPixelsEqualToBase': True, 'pressChangedPixelsInArrow': changed_held,
            'releasedPixelsDifferentFromNormal': changed_release,
            'arrowRect': [line.x(), line.y(), line.width(), line.height()]}


app = QApplication(sys.argv[:1])
base_style = app.style()
window = QWidget()
window.setWindowTitle(f'Qt{args.qt_major} DomainOS viewport spacing probe')
grid = QGridLayout(window)
areas = {}
plain_edits = {}
contents = '\n'.join(f'Linha {n:03d} — ' + ('texto longo ' * 16) for n in range(60))

for column, variant in enumerate(('base', 'proxy')):
    area_box = QGroupBox('QScrollArea — ' + variant)
    area_layout = QVBoxLayout(area_box)
    area = QScrollArea()
    area.setObjectName('area-' + variant)
    area.setFrameShape(QFrame.Shape.Box if args.qt_major == 6 else QFrame.Box)
    area.setLineWidth(2)
    area.setWidgetResizable(False)
    content = QWidget()
    content.setMinimumSize(700, 560)
    area.setWidget(content)
    if variant == 'proxy':
        area_info = install_scrollbar_spacing(area, 4, args.qt_major)
    else:
        area_info = {'targetGapPx': 4, 'proxyResidualPx': 0,
                     'explicitViewportMarginsPx': [0, 0, 0, 0]}
    area_layout.addWidget(area)
    grid.addWidget(area_box, 0, column)
    areas[variant] = (area, area_info)

    edit_box = QGroupBox('QPlainTextEdit — ' + variant)
    edit_layout = QVBoxLayout(edit_box)
    edit = QPlainTextEdit()
    edit.setObjectName('plain-' + variant)
    edit.setPlainText(contents)
    edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap if args.qt_major == 6 else QPlainTextEdit.NoWrap)
    if variant == 'proxy':
        # The QFrame contributes two pixels. Two explicit pixels complete the
        # four-pixel target, so the proxy must contribute zero here.
        edit_info = install_scrollbar_spacing(edit, 4, args.qt_major, (0, 0, 2, 2))
    else:
        edit_info = {'targetGapPx': 4, 'proxyResidualPx': 0,
                     'explicitViewportMarginsPx': [0, 0, 0, 0]}
    edit_layout.addWidget(edit)
    grid.addWidget(edit_box, 1, column)
    plain_edits[variant] = (edit, edit_info)

window.resize(1000, 700)
window.show()
app.processEvents()
for collection in (areas, plain_edits):
    finalize_scrollbar_spacing(collection['proxy'][0])

if base_style.objectName() != 'kvantum':
    raise AssertionError(f'expected active KDE/Kvantum style, got {base_style.metaObject().className()} ({base_style.objectName()})')

def measure(widget):
    viewport = point_in(widget.viewport(), widget)
    vertical = point_in(widget.verticalScrollBar(), widget)
    horizontal = point_in(widget.horizontalScrollBar(), widget)
    return {
        'viewport': viewport, 'verticalScrollbar': vertical,
        'horizontalScrollbar': horizontal,
        'rightGapPx': vertical[0] - (viewport[0] + viewport[2]),
        'bottomGapPx': horizontal[1] - (viewport[1] + viewport[3]),
        'verticalVisible': widget.verticalScrollBar().isVisible(),
        'horizontalVisible': widget.horizontalScrollBar().isVisible(),
    }

results = {'qtMajor': args.qt_major, 'qtStyle': base_style.metaObject().className(),
           'qtStyleKey': base_style.objectName(), 'applicationStyleUnchanged': app.style() is base_style,
           'areas': {}, 'plainTextEdits': {}}
for collection, output in ((areas, results['areas']), (plain_edits, results['plainTextEdits'])):
    for variant, (widget, adapter) in collection.items():
        value = measure(widget)
        value['adapter'] = adapter
        value['styleMetricPx'] = widget.style().pixelMetric(
            QStyle.PixelMetric.PM_ScrollView_ScrollBarSpacing if args.qt_major == 6 else
            QStyle.PM_ScrollView_ScrollBarSpacing, None, widget)
        value['scrollbarExtentPx'] = widget.style().pixelMetric(
            QStyle.PixelMetric.PM_ScrollBarExtent if args.qt_major == 6 else
            QStyle.PM_ScrollBarExtent, None, widget)
        value['paletteRoles'] = palette_snapshot(widget)
        if not value['verticalVisible'] or not value['horizontalVisible']:
            raise AssertionError(f'{variant}: both real axes must be visible')
        output[variant] = value

for collection in (results['areas'], results['plainTextEdits']):
    baseline, adapted = collection['base'], collection['proxy']
    if adapted['rightGapPx'] != 4 or adapted['bottomGapPx'] != 4:
        raise AssertionError('viewport-to-scrollbar distance is not exactly four pixels on both axes')
    if (adapted['adapter']['frameAndStyleContributionPx']
            + adapted['adapter']['explicitViewportMarginsPx'][2]
            + adapted['adapter']['addedViewportMarginPx'] != 4):
        raise AssertionError('measured frame, explicit margin and adapter margin do not sum to four pixels')
    if adapted['paletteRoles'] != baseline['paletteRoles']:
        raise AssertionError('proxy changed KDE palette roles')
    if adapted['scrollbarExtentPx'] != baseline['scrollbarExtentPx']:
        raise AssertionError('proxy changed native scrollbar extent')
    if adapted['styleMetricPx'] != adapted['adapter']['baseStyleMetricPx']:
        raise AssertionError('per-widget adapter changed the active Qt spacing metric')

for orientation, base_attr, adapted_attr in (
    ('vertical', 'verticalScrollBar', 'verticalScrollBar'),
    ('horizontal', 'horizontalScrollBar', 'horizontalScrollBar')):
    for group in ('areas', 'plainTextEdits'):
        base_widget = (areas if group == 'areas' else plain_edits)['base'][0]
        adapted_widget = (areas if group == 'areas' else plain_edits)['proxy'][0]
        results[group]['proxy'][orientation + 'ArrowStates'] = compare_arrows(
            getattr(base_widget, base_attr)(), getattr(adapted_widget, adapted_attr)(),
            orientation, f'{group}/{orientation}')

args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
results['screenshot'] = str(args.output / f'qt{args.qt_major}-spacing.png')
if not window.grab().save(results['screenshot'], 'PNG'):
    raise RuntimeError('failed to save the Xephyr proof image')
(args.output / 'RESULTADO.json').write_text(json.dumps(results, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(results, indent=2, ensure_ascii=False))
window.close()
app.quit()
