#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify GTK2 Entry selection painting after real mapped X11 focus."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image

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
    raise SystemExit('GTK2 selection probe requires an isolated X display')

output = Path(os.environ.get(
    'I167_SELECTION_MAPPED_OUTPUT', TEMP_ROOT / 'i167-entry-selection-mapped-r70'))
output.mkdir(parents=True, exist_ok=True)
builder = backend.load_builder(REPO)
recipe = model()['recipes']['gtk2']
palette_path = REPO / 'colors/DomainOS-SR10.4.colors'
palette, palette_origin = backend.native_roles(
    REPO, palette_path, builder.art, backend.sha(palette_path.read_bytes()))
with backend.recipe_rules(builder, recipe['palette']):
    generated = paint_entry(builder, recipe, palette, output / 'generated')
Gtk.rc_parse(generated['rc'])

window = Gtk.Window()
window.set_title('I167 GTK2 mapped selection')
window.set_default_size(360, 90)
fixed = Gtk.Fixed()
window.add(fixed)
entry = Gtk.Entry()
entry.set_name('themeLabEntry_' + generated['style_id'])
entry.set_size_request(320, 44)
text = 'DomainOS SR10.4 selection'
entry.set_text(text)
fixed.put(entry, 16, 16)
window.show_all()

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
    ['xdotool', 'search', '--name', '^I167 GTK2 mapped selection$'],
    text=True, timeout=5).split()[0]
subprocess.run(['xdotool', 'windowmap', window_id,
                'windowraise', window_id,
                'windowfocus', '--sync', window_id],
               check=True, timeout=5)
subprocess.run(['xdotool', 'mousemove', '--window', window_id,
                '32', '36', 'click', '1'], check=True, timeout=5)
drain_events()
server_focus = subprocess.check_output(
    ['xdotool', 'getwindowfocus'], text=True, timeout=5).strip()
if server_focus != window_id:
    raise AssertionError(('X focus mismatch', server_focus, window_id))
if not entry.is_focus() or not window.get_property('has-toplevel-focus'):
    raise AssertionError('GtkEntry did not retain mapped X11 focus')
baseline = subprocess.check_output(
    ['import', '-window', window_id, 'png:-'], timeout=5)
subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'],
               check=True, timeout=5)
drain_events()
bounds = entry.get_selection_bounds()
if len(bounds) == 3:
    bounds = bounds[1:] if bounds[0] else ()
if bounds != (0, len(text)):
    raise AssertionError(('Ctrl+A selected unexpected range', bounds, len(text)))
selected = subprocess.check_output(
    ['import', '-window', window_id, 'png:-'], timeout=5)
focus_after = entry.is_focus() and window.get_property('has-toplevel-focus')

base_image = Image.open(io.BytesIO(baseline)).convert('RGB')
selected_image = Image.open(io.BytesIO(selected)).convert('RGB')
if base_image.size != selected_image.size:
    raise AssertionError('mapped captures have different sizes')
selection_rgb = builder.art._rgb(
    palette[builder.art.ROLES['selection'][0]])
selection_fg_rgb = builder.art._rgb(
    palette[builder.art.ROLES['selection-fg'][0]])
baseline_pixels = sum(pixel == selection_rgb for pixel in base_image.getdata())
selected_pixels = sum(pixel == selection_rgb for pixel in selected_image.getdata())
added = selected_pixels - baseline_pixels
changed = sum(a != b for a, b in zip(base_image.getdata(), selected_image.getdata()))
if added <= 0 or changed <= 0:
    raise AssertionError(('selection role did not paint', baseline_pixels,
                          selected_pixels, changed))

baseline_path = output / 'unselected-mapped.png'
selected_path = output / 'selected-mapped.png'
base_image.save(baseline_path)
selected_image.save(selected_path)
window.destroy()
drain_events()
result = {
    'status': 'passed',
    'gtk': '2.24.33',
    'control': 'real GtkEntry in mapped X11 GtkWindow',
    'palette': 'DomainOS-SR10.4',
    'palette_sha256': palette_origin['sha256'],
    'mapped_x11_focus': {
        'xid': int(window_id),
        'xdotool_focused_xid': int(server_focus),
        'gtk_entry_is_focus': True,
        'gtk_toplevel_has_focus': True,
        'focus_retained_after_selection': focus_after,
    },
    'selection': {
        'input_method': 'xdotool Ctrl+A key event',
        'utf8_text': text,
        'bounds': list(bounds),
        'selection_background_role_rgb': selection_rgb,
        'selection_foreground_role_rgb': selection_fg_rgb,
        'exact_background_pixels_before': baseline_pixels,
        'exact_background_pixels_selected': selected_pixels,
        'added_background_role_pixels': added,
        'changed_pixels': changed,
    },
    'captures': {
        'unselected': str(baseline_path),
        'selected': str(selected_path),
    },
    'limits': [
        'This proves GTK2 selection role painting after real mapped focus, not historical SR10.4 selection color or geometry.',
        'The available VUE capture does not establish a native selected-text highlight for pixel comparison.',
        'Xvfb without a window manager; no KWin integration or human approval is claimed.',
        'No product RGB was added; colors come from current KDE schema roles.',
    ],
}
(output / 'RESULTADO.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'selection': result['selection'],
                  'focus': result['mapped_x11_focus']}, ensure_ascii=False, indent=2))
