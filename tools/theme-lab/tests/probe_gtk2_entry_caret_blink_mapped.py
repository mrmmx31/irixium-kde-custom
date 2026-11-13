#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure a real GTK2 Entry caret blink with mapped X11 focus."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image, ImageChops

if os.environ.get('T04_PRIVATE_ENTRY') != '1':
    raise SystemExit('set T04_PRIVATE_ENTRY=1 for this isolated GTK2 probe')

TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
ROOT = Path(__file__).resolve().parents[3]
TESTS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(TESTS)]

from test_backend import ROOT as REPO, backend, model
from gtk2_entries import paint_entry

import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk

if not Gtk.init_check([])[0]:
    raise SystemExit('GTK2 caret probe requires an isolated X display')

output = Path(os.environ.get(
    'I167_CARET_BLINK_OUTPUT', TEMP_ROOT / 'i167-entry-caret-blink-r69'))
output.mkdir(parents=True, exist_ok=True)
builder = backend.load_builder(REPO)
recipe = model()['recipes']['gtk2']
palette_path = REPO / 'colors/DomainOS-SR10.4.colors'
palette, palette_origin = backend.native_roles(
    REPO, palette_path, builder.art, backend.sha(palette_path.read_bytes()))
with backend.recipe_rules(builder, recipe['palette']):
    generated = paint_entry(builder, recipe, palette, output / 'generated')
Gtk.rc_parse(generated['rc'])

settings = Gtk.Settings.get_default()
settings_before = {
    name: settings.get_property(name)
    for name in ('gtk-cursor-blink', 'gtk-cursor-blink-time',
                 'gtk-cursor-blink-timeout')
}
# Make the blink observable only in this probe process; never change the user
# session or schema. A bounded 30-second timeout exceeds the measurement.
settings.set_property('gtk-cursor-blink', True)
settings.set_property('gtk-cursor-blink-timeout', 30)
effective_settings = {
    name: settings.get_property(name)
    for name in ('gtk-cursor-blink', 'gtk-cursor-blink-time',
                 'gtk-cursor-blink-timeout')
}

window = Gtk.Window()
window.set_title('I167 GTK2 mapped caret blink')
window.set_default_size(338, 34)
entry = Gtk.Entry()
entry.set_name('themeLabEntry_' + generated['style_id'])
entry.set_size_request(338, -1)
entry.set_text('.a')
window.add(entry)
window.show_all()
entry.set_position(2)

def drain_events():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)

drain_events()
window.set_focus(None)
drain_events()
window.set_focus(entry)
entry.grab_focus()
drain_events()
window_id = subprocess.check_output(
    ['xdotool', 'search', '--name', '^I167 GTK2 mapped caret blink$'],
    text=True, timeout=5).split()[0]
subprocess.run(['xdotool', 'windowmap', window_id,
                'windowraise', window_id,
                'windowfocus', '--sync', window_id],
               check=True, timeout=5)
server_focus = subprocess.check_output(
    ['xdotool', 'getwindowfocus'], text=True, timeout=5).strip()
if server_focus != window_id:
    raise AssertionError(('X focus mismatch', server_focus, window_id))
# A real pointer click starts/restarts GtkEntry's cursor phase, as a user's
# click does. The caret is then placed at the end of the same two-character
# text used by the offscreen geometry probe R61.
subprocess.run(['xdotool', 'mousemove', '--window', window_id,
                '33', '17', 'click', '1'], check=True, timeout=5)
drain_events()
entry.set_position(2)
drain_events()
if not entry.is_focus() or not window.get_property('has-toplevel-focus'):
    raise AssertionError('GtkEntry did not receive mapped X11 focus')

started = time.monotonic()
deadline = started + 4.2
previous = None
previous_change = None
transitions = []
while time.monotonic() < deadline:
    drain_events()
    png = subprocess.check_output(
        ['import', '-window', window_id, 'png:-'], timeout=5)
    frame = Image.open(io.BytesIO(png)).convert('RGB')
    relative_ms = round((time.monotonic() - started) * 1000)
    if previous is not None:
        changed = ImageChops.difference(previous, frame).crop(
            (5, 5, max(6, frame.width - 5), max(6, frame.height - 5)))
        bbox = changed.getbbox()
        if bbox:
            count = sum(pixel != (0, 0, 0) for pixel in changed.getdata())
            rect = [bbox[0] + 5, bbox[1] + 5,
                    bbox[2] + 5, bbox[3] + 5]
            image_path = output / (
                'transition-%02d-%dms.png' % (len(transitions) + 1,
                                                relative_ms))
            frame.save(image_path)
            transitions.append({
                't_ms': relative_ms,
                'since_previous_change_ms': (
                    round((time.monotonic() - previous_change) * 1000)
                    if previous_change else None),
                'changed_pixels': count,
                'bbox_xyxy': rect,
                'image': image_path.name,
            })
            previous_change = time.monotonic()
    else:
        frame.save(output / 'initial.png')
    previous = frame
    time.sleep(0.05)

entry_focus = entry.is_focus()
toplevel_focus = window.get_property('has-toplevel-focus')
entry_allocation = entry.get_allocation()
font = entry.get_pango_context().get_font_description().to_string()
window.destroy()
drain_events()

caret_transitions = [
    row for row in transitions
    if row['bbox_xyxy'][2] - row['bbox_xyxy'][0] == 1
    and 10 <= row['bbox_xyxy'][3] - row['bbox_xyxy'][1] <= 24
]
if len(caret_transitions) < 4:
    raise AssertionError('caret transitions not found: ' + repr(transitions))
intervals = [row['since_previous_change_ms']
             for row in caret_transitions[1:]]
geometries = sorted({(row['bbox_xyxy'][2] - row['bbox_xyxy'][0],
                     row['bbox_xyxy'][3] - row['bbox_xyxy'][1])
                    for row in caret_transitions})
if len(geometries) != 1:
    raise AssertionError('caret geometry changed between phases: ' + repr(geometries))
if not all(300 <= value <= 1000 for value in intervals):
    raise AssertionError('unexpected caret intervals: ' + repr(intervals))
result = {
    'status': 'passed',
    'gtk': '2.24.33',
    'palette': 'DomainOS-SR10.4',
    'palette_origin': palette_origin,
    'mapped_x11_focus': {
        'xid': int(window_id),
        'xdotool_focused_xid': int(server_focus),
        'gtk_entry_is_focus': entry_focus,
        'gtk_toplevel_has_focus': toplevel_focus,
    },
    'entry': {
        'requested_window_px': [338, 34],
        'allocation_px': [entry_allocation.width, entry_allocation.height],
        'font': font,
        'text': '.a',
        'caret_stem_px': list(geometries[0]),
    },
    'settings_before_probe': settings_before,
    'settings_effective_in_probe_process': effective_settings,
    'transitions': transitions,
    'caret_transition_intervals_ms': intervals,
    'expected_from_gtk_source': {
        'gtk_cursor_blink_time_ms': effective_settings['gtk-cursor-blink-time'],
        'visible_phase_fraction': '2/3',
        'hidden_phase_fraction': '1/3',
        'expected_visible_ms': round(effective_settings['gtk-cursor-blink-time'] * 2 / 3),
        'expected_hidden_ms': round(effective_settings['gtk-cursor-blink-time'] / 3),
    },
    'limits': [
        'Measured in isolated Xvfb without a window manager; not KWin integration.',
        'XImage capture sampling adds delay, so observed intervals are approximate.',
        'The period is GTK2 behavior; no SR10.4/VUE caret-blink period was found in available defaults.',
        'GtkEntry caret color/shape follows the GTK2 recipe; the temporary blink settings never leave this process.',
    ],
}
(output / 'RESULTADO.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'status': result['status'],
    'gtk_settings': effective_settings,
    'caret_transitions': len(caret_transitions),
    'intervals_ms': intervals,
    'caret_bbox': caret_transitions[0]['bbox_xyxy'],
}, ensure_ascii=False, indent=2))
