#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-widget Qt adapter for the measured Domain/OS viewport-to-bar gap.

Qt/Kvantum does not expose the needed spacing setting. This adapter measures
the real widget after layout and adds only the missing viewport margin on that
QAbstractScrollArea. The selected QStyle, palette, bar extent, painting and
interaction remain untouched.
"""


def _qt_api(qt_major):
    if qt_major == 6:
        from PyQt6.QtCore import QEvent, QPoint, QObject, QTimer
        from PyQt6.QtWidgets import QApplication, QStyle
    elif qt_major == 5:
        from PyQt5.QtCore import QEvent, QPoint, QObject, QTimer
        from PyQt5.QtWidgets import QApplication, QStyle
    else:
        raise ValueError('Qt major must be 5 or 6')
    return QApplication, QStyle, QEvent, QPoint, QObject, QTimer


def _gap(widget, bar, horizontal, point_type):
    viewport = widget.viewport()
    viewport_origin = viewport.mapTo(widget, point_type(0, 0))
    bar_origin = bar.mapTo(widget, point_type(0, 0))
    if horizontal:
        return bar_origin.y() - (viewport_origin.y() + viewport.height())
    return bar_origin.x() - (viewport_origin.x() + viewport.width())


def finalize_scrollbar_spacing(widget):
    """Measure a shown area and reserve only the residual margin."""
    info = getattr(widget, '_domainos_scroll_spacing_info', None)
    if info is None:
        raise RuntimeError('scrollbar spacing adapter is not installed')
    if info.get('finalized'):
        return info

    QApplication, _, _, QPoint, _, _ = _qt_api(info['qtMajor'])
    measurements = []
    vertical = widget.verticalScrollBar()
    horizontal = widget.horizontalScrollBar()
    if vertical.isVisible():
        measurements.append(('vertical', _gap(widget, vertical, False, QPoint)))
    if horizontal.isVisible():
        measurements.append(('horizontal', _gap(widget, horizontal, True, QPoint)))
    if not measurements:
        info['finalizePending'] = 'no visible scrollbar axis yet'
        return info
    if len({gap for _, gap in measurements}) != 1:
        raise RuntimeError(f'Qt scrollbar axes have asymmetric baseline gaps: {measurements}')

    baseline = measurements[0][1]
    addition = info['targetGapPx'] - baseline
    margins = widget.viewportMargins()
    right, bottom = margins.right(), margins.bottom()
    if right != bottom:
        raise RuntimeError(f'existing explicit viewport margins are asymmetric: {right}, {bottom}')
    if right + addition < 0:
        raise RuntimeError(f'existing frame already exceeds target and cannot be reduced safely: {measurements}')

    info['finalizing'] = True
    widget.setViewportMargins(margins.left(), margins.top(), right + addition, bottom + addition)
    widget.updateGeometry()
    layout = widget.layout()
    if layout is not None:
        layout.activate()
    QApplication.processEvents()
    final_gaps = []
    if vertical.isVisible():
        final_gaps.append(('vertical', _gap(widget, vertical, False, QPoint)))
    if horizontal.isVisible():
        final_gaps.append(('horizontal', _gap(widget, horizontal, True, QPoint)))
    if any(gap != info['targetGapPx'] for _, gap in final_gaps):
        info['finalizing'] = False
        raise RuntimeError(
            f'Qt did not lay out the requested {info["targetGapPx"]}px gap for '
            f'{widget.metaObject().className()}#{widget.objectName()}: '
            f'baseline={measurements}, margins={widget.viewportMargins()}, final={final_gaps}, '
            f'viewport={widget.viewport().geometry().getRect()}, '
            f'vbar={vertical.geometry().getRect()}, hbar={horizontal.geometry().getRect()}')

    info['measuredBaselineGapsPx'] = dict(measurements)
    info['frameAndStyleContributionPx'] = baseline - right
    info['addedViewportMarginPx'] = addition
    info['finalViewportMarginsPx'] = [margins.left(), margins.top(), right + addition, bottom + addition]
    info['measuredFinalGapsPx'] = dict(final_gaps)
    info['finalizePending'] = None
    info['finalizing'] = False
    info['finalized'] = True
    return info


def install_scrollbar_spacing(widget, gap_px, qt_major, explicit_margins=(0, 0, 0, 0)):
    """Install a geometry-only adapter; final measurement runs on Show."""
    QApplication, QStyle, QEvent, _, QObject, QTimer = _qt_api(qt_major)
    margins = tuple(int(value) for value in explicit_margins)
    if len(margins) != 4 or any(value < 0 for value in margins):
        raise ValueError('explicit_margins must contain four non-negative pixel values')
    left, top, right, bottom = margins
    if left or top or right != bottom:
        raise ValueError('explicit gap margins must be symmetric on right/bottom')
    if int(gap_px) < 0:
        raise ValueError('target gap must be non-negative')
    if widget.property('domainosScrollSpacingInstalled'):
        raise RuntimeError('scrollbar spacing is already installed on this widget')

    style = widget.style()
    metric = (QStyle.PixelMetric.PM_ScrollView_ScrollBarSpacing if qt_major == 6
              else QStyle.PM_ScrollView_ScrollBarSpacing)
    base_metric = int(style.pixelMetric(metric, None, widget))
    if margins != (0, 0, 0, 0):
        widget.setViewportMargins(*margins)

    info = {
        'widgetClass': widget.metaObject().className(),
        'styleKey': style.objectName(),
        'styleClass': style.metaObject().className(),
        'metric': 'PM_ScrollView_ScrollBarSpacing',
        'baseStyleMetricPx': base_metric,
        'targetGapPx': int(gap_px),
        'explicitViewportMarginsPx': list(margins),
        'addedViewportMarginPx': None,
        'finalViewportMarginsPx': None,
        'measuredBaselineGapsPx': None,
        'measuredFinalGapsPx': None,
        'finalized': False,
        'finalizePending': 'waiting for shown, laid-out scrollbar geometry',
        'scope': 'one QAbstractScrollArea; no style or palette mutation',
        'qtMajor': qt_major,
    }
    widget._domainos_scroll_spacing_info = info
    widget.setProperty('domainosScrollSpacingInstalled', True)

    class _FinalizeOnShow(QObject):
        def eventFilter(self, watched, event):
            show_type = QEvent.Type.Show if qt_major == 6 else QEvent.Show
            resize_type = QEvent.Type.Resize if qt_major == 6 else QEvent.Resize
            if event.type() in (show_type, resize_type):
                def try_finalize():
                    try:
                        finalize_scrollbar_spacing(widget)
                    except Exception as error:
                        info['finalizeError'] = str(error)
                        info['finalizePending'] = 'geometry is unsupported or not stable yet'
                QTimer.singleShot(0, try_finalize)
            return False

    finalizer = _FinalizeOnShow(widget)
    widget.installEventFilter(finalizer)
    widget._domainos_scroll_spacing_finalizer = finalizer
    return info


def install_on_scroll_areas(root, gap_px, qt_major):
    if qt_major == 6:
        from PyQt6.QtWidgets import QAbstractScrollArea, QPlainTextEdit, QScrollArea, QTextEdit
    elif qt_major == 5:
        from PyQt5.QtWidgets import QAbstractScrollArea, QPlainTextEdit, QScrollArea, QTextEdit
    else:
        raise ValueError('Qt major must be 5 or 6')
    widgets = root.findChildren(QAbstractScrollArea)
    supported = (QScrollArea, QPlainTextEdit, QTextEdit)
    candidates = [widget for widget in widgets if isinstance(widget, supported)]
    skipped = [
        {'widgetClass': widget.metaObject().className(), 'objectName': widget.objectName(),
         'reason': 'viewport/bar geometry needs a separate adapter for this view class'}
        for widget in widgets if widget not in candidates
    ]
    adapters = [install_scrollbar_spacing(widget, gap_px, qt_major)
                for widget in candidates]
    root._domainos_scroll_spacing_widgets = candidates
    root._domainos_scroll_spacing_skipped = skipped
    return adapters


def finalize_on_scroll_areas(root):
    """Finalize visible areas; hidden areas finalize on their own Show event."""
    if root is None:
        return []
    results = []
    for widget in getattr(root, '_domainos_scroll_spacing_widgets', []):
        if not (widget.verticalScrollBar().isVisible()
                or widget.horizontalScrollBar().isVisible()):
            continue
        info = widget._domainos_scroll_spacing_info
        try:
            results.append(finalize_scrollbar_spacing(widget))
        except Exception as error:
            info['finalizeError'] = str(error)
            info['finalizePending'] = 'geometry is unsupported or not stable yet'
            results.append(info)
    return results
