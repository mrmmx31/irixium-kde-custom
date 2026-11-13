# SPDX-License-Identifier: GPL-3.0-or-later
"""Timed hover matrix for mapped controls in the real GTK4 demo gallery."""
import ctypes as C
import importlib.util
import json
import os
import subprocess
import sys
import time

assert os.environ.get('T07_PRIVATE_PROBE') == '1'
root = __import__('pathlib').Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'plasma/tests/galerias-nativas'))
spec = importlib.util.spec_from_file_location(
    'gtk4_gallery', root / 'plasma/tests/galerias-nativas/gtk4_demo.py')
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)
g, P, I = gallery, gallery.P, gallery.I
x11 = C.CDLL('libX11.so.6')
x11.XOpenDisplay.restype = P
x11.XOpenDisplay.argtypes = [C.c_char_p]
xdisplay = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
assert xdisplay, 'could not open the private X display for geometry measurements'
x11.XDefaultRootWindow.restype = C.c_ulong
x11.XDefaultRootWindow.argtypes = [P]
x11.XDefaultScreen.restype = I
x11.XDefaultScreen.argtypes = [P]
x11.XDisplayWidth.restype = I
x11.XDisplayWidth.argtypes = [P, I]
x11.XDisplayHeight.restype = I
x11.XDisplayHeight.argtypes = [P, I]
x11.XGetGeometry.restype = I
x11.XGetGeometry.argtypes = [P, C.c_ulong, C.POINTER(C.c_ulong),
                              C.POINTER(I), C.POINTER(I), C.POINTER(C.c_uint),
                              C.POINTER(C.c_uint), C.POINTER(C.c_uint),
                              C.POINTER(C.c_uint)]
x11.XTranslateCoordinates.restype = I
x11.XTranslateCoordinates.argtypes = [P, C.c_ulong, C.c_ulong, I, I,
                                      C.POINTER(I), C.POINTER(I),
                                      C.POINTER(C.c_ulong)]
x11.XCloseDisplay.restype = I
x11.XCloseDisplay.argtypes = [P]
root_window = x11.XDefaultRootWindow(xdisplay)
screen_number = x11.XDefaultScreen(xdisplay)
screen_width = x11.XDisplayWidth(xdisplay, screen_number)
screen_height = x11.XDisplayHeight(xdisplay, screen_number)
active = g.api('gtk_application_get_active_window', P, P)
tops = g.api('gtk_window_get_toplevels', P)
length = g.bind(g.gio, 'g_list_model_get_n_items', g.U, P)
item = g.bind(g.gio, 'g_list_model_get_item', P, P, g.U)
mapped = g.api('gtk_widget_get_mapped', I, P)
native_widget = g.api('gtk_widget_get_native', P, P)
surface = g.api('gtk_native_get_surface', P, P)
xid = g.api('gdk_x11_surface_get_xid', C.c_ulong, P)
css_name = g.api('gtk_widget_get_css_name', g.S, P)
tooltip_text = g.api('gtk_widget_get_tooltip_text', g.S, P)
notebook_set_page = g.api('gtk_notebook_set_current_page', None, P, I)
parent_widget = g.api('gtk_widget_get_parent', P, P)
scrollbar_adjustment = g.api('gtk_scrollbar_get_adjustment', P, P)
adjustment_value = g.api('gtk_adjustment_get_value', C.c_double, P)
type_name = g.type_name
class Rect(C.Structure):
    _fields_ = [('x', C.c_float), ('y', C.c_float),
                ('width', C.c_float), ('height', C.c_float)]
# Reuse the gallery's void-pointer binding. ctypes returns the same _FuncPtr
# for a shared library symbol; rebinding argtypes here would corrupt the
# gallery's distinct Bounds structure declaration.
bounds = g.compute_bounds
timer = g.bind(g.glib, 'g_timeout_add', g.U, g.U, P, P)
TICK = C.CFUNCTYPE(I, P)
state = {'phase': 'wait', 'start': time.monotonic(), 'page': 0,
         'targets': [], 'index': 0, 'cases': [], 'initial_cold_delay_ms': None}
errors = []

def descendants(node):
    yield node
    child = g.first_child(node)
    while child:
        yield from descendants(child)
        child = g.next_sibling(child)

def geometry(widget):
    native = surface(widget)
    assert native
    window = int(xid(native))
    geometry_root, x, y = C.c_ulong(), I(), I()
    width, height, border, depth = C.c_uint(), C.c_uint(), C.c_uint(), C.c_uint()
    if not x11.XGetGeometry(xdisplay, window, C.byref(geometry_root),
                            C.byref(x), C.byref(y), C.byref(width), C.byref(height),
                            C.byref(border), C.byref(depth)):
        raise RuntimeError('XGetGeometry failed for GTK4 popup')
    absolute_x, absolute_y, child = I(), I(), C.c_ulong()
    if not x11.XTranslateCoordinates(xdisplay, window, root_window, 0, 0,
                                     C.byref(absolute_x), C.byref(absolute_y),
                                     C.byref(child)):
        raise RuntimeError('XTranslateCoordinates failed for GTK4 popup')
    return (absolute_x.value, absolute_y.value, width.value, height.value)

def rect(widget):
    native = native_widget(widget)
    area = Rect()
    assert native and bounds(widget, native, C.byref(area))
    x, y, _, _ = geometry(native)
    return (x + int(area.x), y + int(area.y),
            int(area.width), int(area.height))

def tooltip_rects():
    result = []
    seen_surfaces = set()
    model = tops()
    for n in range(length(model)):
        top = item(model, n)
        try:
            for node in descendants(top):
                if not mapped(node):
                    continue
                kind = type_name(node)
                is_hint_popover = (kind.startswith(b'GtkPopover') and
                                   bool(g.object_data(node,b'theme-lab-delayed-hint')))
                if css_name(node) != b'tooltip' and not is_hint_popover:
                    continue
                native = native_widget(node)
                popup_surface = surface(native) if native else None
                if not popup_surface:
                    continue
                surface_id = int(xid(popup_surface))
                if surface_id in seen_surfaces:
                    continue
                seen_surfaces.add(surface_id)
                result.append(geometry(native))
        finally:
            g.unref(top)
    return result

def move(x, y):
    subprocess.run(['xdotool', 'mousemove', str(x), str(y)],
                   check=True, capture_output=True, timeout=2)

def targets(window):
    found = []
    seen = set()
    for node in descendants(window):
        text = tooltip_text(node)
        if not mapped(node) or not text or int(node) in seen:
            continue
        seen.add(int(node))
        area = rect(node)
        ancestor = parent_widget(node)
        while ancestor:
            if type_name(ancestor) == b'GtkScrolledWindow':
                clip = rect(ancestor)
                left, top = max(area[0], clip[0]), max(area[1], clip[1])
                right = min(area[0] + area[2], clip[0] + clip[2])
                bottom = min(area[1] + area[3], clip[1] + clip[3])
                area = (left, top, max(0, right - left), max(0, bottom - top))
                break
            ancestor = parent_widget(ancestor)
        if area[2] <= 0 or area[3] <= 0:
            continue
        found.append((node, text.decode('utf-8'), area))
    control_type=os.environ.get('T07_MATRIX_CONTROL_TYPE')
    if control_type:
        found=[row for row in found if type_name(row[0]).decode()==control_type]
    text_filter=os.environ.get('T07_MATRIX_TOOLTIP_CONTAINS')
    if text_filter:
        found=[row for row in found if text_filter in row[1]]
    limit=int(os.environ.get('T07_MATRIX_LIMIT_PER_PAGE','0'))
    if limit>0:
        found=found[:limit]
    return found

def begin_target(now):
    if state['index'] >= len(state['targets']):
        if state['page'] == 0:
            notebooks = [w for w in descendants(state['window'])
                         if type_name(w) == b'GtkNotebook']
            assert notebooks, 'gallery notebook not found'
            state['page'] = 1
            notebook_set_page(notebooks[0], 1)
            state['phase'] = 'page_switch'
            state['start'] = now
            return
        state['phase'] = 'done'
        return
    target, text, area = state['targets'][state['index']]
    # Interaction evidence is per widget. A successful click on page 0 must
    # not silently skip the same check for page 1.
    state.update(target=target, expected=text, owner=area,
                 phase='cold', start=now, scroll_click_tested=False,
                 scroll_click_point=None, scroll_value_before=None,
                 scroll_value_after=None, scroll_click_responded=None)
    move(0, 0)

def fail_target(reason, now):
    target, text, area = state['targets'][state['index']]
    placements = []
    for hint in g.hint_popovers:
        if int(hint.owner) != int(target):
            continue
        anchor_rect = rect(hint.anchor) if hint.anchor and mapped(hint.anchor) else None
        popup_rect = geometry(native_widget(hint.popover)) if hint.popover and mapped(hint.popover) else None
        placements.append({'strategy': hint.position_strategy,
                           'layout_diagnostics': hint.layout_diagnostics,
                           'anchor_rect_px': list(anchor_rect) if anchor_rect else None,
                           'popover_rect_px': list(popup_rect) if popup_rect else None})
    state['cases'].append({'page': state['page'],
        'control_type': type_name(target).decode(), 'tooltip_text': text,
        'control_rect_px': list(area),
        'screen_px': [screen_width, screen_height],
        'placement_diagnostics': placements,
        'native_tooltip_enabled': bool(g.widget_has_tooltip(target)),
        'custom_popovers': [{'controller_active': bool(h.controller_added),
            'timer_active': bool(h.timer), 'helper_visible': bool(h.visible),
            'popover_mapped': bool(mapped(h.popover)),
            'anchor_mapped': bool(mapped(h.anchor)),
            'popover_css_name': css_name(h.popover).decode('ascii'),
            'marker_present': bool(g.object_data(h.popover,b'theme-lab-delayed-hint'))}
            for h in g.hint_popovers],
        'overlaps_large_owner_region': state.get('overlaps_owner', False),
        'status': 'failed', 'reason': reason})
    state['index'] += 1
    begin_target(now)

@TICK
def tick(_):
    try:
        now = time.monotonic()
        phase = state['phase']
        elapsed = now - state['start']
        if phase == 'wait':
            window = active(g.application)
            if not window or elapsed < .8:
                return 1
            assert g.display_name(g.widget_display(window)).decode() == os.environ['DISPLAY']
            state['window'] = window
            assert g.hint_popovers, 'no custom scrollbar popover attached after gallery layout'
            assert not g.hint_retry_pending, 'scrollbar hint anchors did not settle before hover'
            state['targets'] = targets(window)
            assert state['targets'], 'no mapped GTK4 controls with native hints'
            state['initial_count'] = len(state['targets'])
            begin_target(now)
        elif phase == 'page_switch' and elapsed > .5:
            state['targets'] = targets(state['window'])
            assert state['targets'], 'text/scrolling page has no mapped hints'
            state['index'] = 0
            state['second_page_count'] = len(state['targets'])
            begin_target(now)
        elif phase == 'cold' and elapsed > .7:
            x, y, w, h = state['owner']
            move(x + w // 2, y + h // 2)
            state.update(phase='hover', start=now)
        elif phase == 'hover':
            visible_tips = tooltip_rects()
            if state['index'] == 0 and state['page'] == 0 and elapsed < .2:
                assert not visible_tips, 'first tooltip appeared before cold delay'
            if visible_tips:
                assert len(visible_tips) == 1, visible_tips
                x, y, w, h = visible_tips[0]
                a, b, c, d = state['owner']
                overlaps_owner = not (x + w <= a or a + c <= x or
                                      y + h <= b or b + d <= y)
                pointer = (a + c // 2, b + d // 2)
                if x <= pointer[0] < x + w and y <= pointer[1] < y + h:
                    fail_target('tooltip covers hover point: tip=%r' % (visible_tips[0],), now)
                    return 1
                if overlaps_owner:
                    fail_target('tooltip overlaps its owner: tip=%r owner=%r' %
                                (visible_tips[0], state['owner']), now)
                    return 1
                sw, sh = screen_width, screen_height
                if not (x >= 0 and y >= 0 and x + w <= sw and y + h <= sh):
                    fail_target('tooltip exceeds screen: tip=%r' % (visible_tips[0],), now)
                    return 1
                state['initial_tip'] = visible_tips[0]
                state['settle_positions'] = [visible_tips[0]]
                state['overlaps_owner'] = overlaps_owner
                state.update(phase='settle', start=now)
            elif elapsed > 3:
                fail_target('tooltip did not appear after pointer entered mapped widget', now)
                return 1
        elif phase == 'settle':
            observed = tooltip_rects()
            assert len(observed) == 1, ('tooltip count changed during initial layout: '
                                        + repr(observed))
            if observed[0] not in state['settle_positions']:
                state['settle_positions'].append(observed[0])
            x, y, w, h = observed[0]
            a, b, c, d = state['owner']
            pointer = (a + c // 2, b + d // 2)
            if x <= pointer[0] < x + w and y <= pointer[1] < y + h:
                fail_target('tooltip moved over hover point during initial layout', now)
                return 1
            overlaps_owner = not (x + w <= a or a + c <= x or
                                  y + h <= b or b + d <= y)
            if overlaps_owner:
                fail_target('tooltip overlaps its owner after layout: tip=%r owner=%r' %
                            (observed[0], state['owner']), now)
                return 1
            if len(state['settle_positions']) > 3:
                fail_target('tooltip position kept oscillating during initial layout', now)
                return 1
            if elapsed > .2:
                state['tip'] = observed[0]
                state.update(phase='stable', start=now)
        elif phase == 'stable':
            observed = tooltip_rects()
            if observed != [state['tip']]:
                fail_target('tooltip moved or oscillated after initial layout: '
                            'expected=%r observed=%r' % (state['tip'], observed), now)
                return 1
            x, y, w, h = observed[0]
            a, b, c, d = state['owner']
            state['overlaps_owner'] = not (x + w <= a or a + c <= x or
                                           y + h <= b or b + d <= y)
            if state['overlaps_owner']:
                fail_target('stable tooltip overlaps hovered control: '
                            'tip=%r owner=%r' % (observed[0], state['owner']), now)
                return 1
            if elapsed > .4:
                if (not state.get('scroll_click_tested') and
                        state['expected'].startswith('Barra vertical:')):
                    adjustment = scrollbar_adjustment(state['target'])
                    assert adjustment, 'GtkScrollbar did not expose its GtkAdjustment'
                    state['scroll_value_before'] = adjustment_value(adjustment)
                    x, y, w, h = state['owner']
                    fraction = float(os.environ.get(
                        'T07_MATRIX_SCROLL_CLICK_FRACTION', '0.75'))
                    assert 0.0 < fraction < 1.0, 'scroll click fraction must be between 0 and 1'
                    click_point = (x + w // 2, y + max(1, min(h - 1, round(h * fraction))))
                    move(*click_point)
                    subprocess.run(['xdotool', 'click', '1'], check=True,
                                   capture_output=True, timeout=2)
                    state['scroll_adjustment'] = adjustment
                    state['scroll_click_tested'] = True
                    state['scroll_click_point'] = click_point
                    state.update(phase='scroll_click', start=now)
                else:
                    move(0, 0)
                    state.update(phase='leave', start=now)
        elif phase == 'scroll_click' and elapsed > .2:
            after = adjustment_value(state['scroll_adjustment'])
            if after == state['scroll_value_before']:
                fail_target('scrollbar did not respond to click while its hint was open', now)
                return 1
            state['scroll_value_after'] = after
            state['scroll_click_responded'] = True
            move(0, 0)
            state.update(phase='leave', start=now)
        elif phase == 'leave' and elapsed > .7:
            if tooltip_rects():
                fail_target('tooltip remained after pointer leave', now)
                return 1
            helper = next((h for h in g.hint_popovers
                           if int(h.owner) == int(state['target'])), None)
            ancestor_restored = (helper is None or
                (not helper.ancestor_suppressed and all(
                    bool(g.widget_has_tooltip(ancestor)) == original
                    for ancestor, original in helper.ancestor_tooltips)))
            if not ancestor_restored:
                fail_target('ancestor tooltip was not restored after pointer leave', now)
                return 1
            x, y, w, h = state['owner']
            state['cases'].append({'page': state['page'],
                'control_type': type_name(state['target']).decode(),
                'tooltip_text': state['expected'],
                'control_rect_px': [x, y, w, h],
                'initial_tooltip_rect_px': list(state['initial_tip']),
                'tooltip_rect_px': list(state['tip']),
                'initial_layout_positions_px': [list(p) for p in state['settle_positions']],
                'overlaps_large_owner_region': state.get('overlaps_owner', False),
                'ancestor_tooltip_restored_after_leave': ancestor_restored,
                'scrollbar_click_responded_with_hint_open': (
                    state.get('scroll_click_responded') if helper else None),
                'scrollbar_click_point_px': (list(state['scroll_click_point'])
                    if state.get('scroll_click_point') else None),
                'scroll_value_before_click': state.get('scroll_value_before') if helper else None,
                'scroll_value_after_click': state.get('scroll_value_after') if helper else None,
                'stable_ms': 400, 'closed_after_leave': True, 'status': 'passed'})
            state['index'] += 1
            begin_target(now)
        elif phase == 'done':
            passed = sum(case['status'] == 'passed' for case in state['cases'])
            failed = len(state['cases']) - passed
            small_nonoverlap = all(
                not case.get('overlaps_large_owner_region', False) for case in state['cases']
                if case['control_rect_px'][2] * case['control_rect_px'][3] < 80000)
            cleanup = []
            overlay_children_before = 0
            child = g.first_child(g.hint_layer)
            while child:
                overlay_children_before += 1
                child = g.next_sibling(child)
            for hint in g.hint_popovers:
                owner = hint.owner
                hint.close()
                hint.close()
                cleanup.append({
                    'native_tooltip_restored': bool(g.widget_has_tooltip(owner)),
                    'closed_idempotently': hint.closed,
                })
            overlay_children_after = 0
            child = g.first_child(g.hint_layer)
            while child:
                overlay_children_after += 1
                child = g.next_sibling(child)
            anchors_removed = overlay_children_before == len(cleanup) and overlay_children_after == 0
            assert cleanup and anchors_removed and all(
                row['native_tooltip_restored'] and row['closed_idempotently']
                for row in cleanup), (cleanup, overlay_children_before, overlay_children_after)
            state['result'] = {'status': 'partial' if failed or not small_nonoverlap else 'passed',
                'initial_cold_delay_ms': 500,
                'mapped_targets_first_page': state['initial_count'],
                'mapped_targets_second_page': state['second_page_count'],
                'passed_targets': passed, 'failed_targets': failed,
                'within_screen': True, 'never_covers_hover_point': True,
                'small_control_nonoverlap': small_nonoverlap,
                'stable_ms': 400, 'closed_after_leave': True,
                'cleanup': {'hints': cleanup,
                            'overlay_anchors_before': overlay_children_before,
                            'overlay_anchors_after': overlay_children_after,
                            'anchors_removed': anchors_removed},
                'cases': state['cases'],
                'scope': 'Mapped native hint-bearing widgets on both pages of the GTK4 gallery; cold delay checked on first target, active-session tooltip cycles on remaining targets; custom popover cleanup restores native tooltip state and removes anchors.',
                'selected_control_type': os.environ.get('T07_MATRIX_CONTROL_TYPE'),
                'selected_tooltip_text': os.environ.get('T07_MATRIX_TOOLTIP_CONTAINS'),
                'target_limit_per_page': int(os.environ.get('T07_MATRIX_LIMIT_PER_PAGE','0'))}
            g.app_quit(g.application)
            return 0
        return 1
    except Exception as error:
        errors.append(str(error))
        g.app_quit(g.application)
        return 0

@g.CALLBACK
def start_probe(_application, _data):
    timer(100, C.cast(tick, P), None)

g.signal(g.application, 'activate', start_probe)
g.app_run(g.application, 0, None)
x11.XCloseDisplay(xdisplay)
assert not errors, errors
assert state.get('result', {}).get('status') in ('passed', 'partial')
print(json.dumps({'hover_matrix': state['result']}, ensure_ascii=False), flush=True)
