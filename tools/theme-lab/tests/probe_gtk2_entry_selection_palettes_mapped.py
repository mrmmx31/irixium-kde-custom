#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare the live VUE reverse-video rule across GTK2 KDE schemes."""
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
    'I167_SELECTION_PALETTES_OUTPUT',
    TEMP_ROOT / 'i167-entry-selection-inverse-r115'))
output.mkdir(parents=True, exist_ok=True)
builder = backend.load_builder(REPO)
recipe = model()['recipes']['gtk2']
schemes = {
    'DomainOS': REPO / 'colors/DomainOS-SR10.4.colors',
    'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
    'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
}
text = 'DomainOS SR10.4 selection'
rows = []

for name, scheme_path in schemes.items():
    palette, origin = backend.native_roles(
        REPO, scheme_path, builder.art, backend.sha(scheme_path.read_bytes()))
    generated_dir = output / name / 'generated'
    with backend.recipe_rules(builder, recipe['palette']):
        generated = paint_entry(builder, recipe, palette, generated_dir)
    Gtk.rc_parse(generated['rc'])

    title = 'I167 GTK2 mapped selection ' + name
    window = Gtk.Window()
    window.set_title(title)
    window.set_default_size(360, 90)
    fixed = Gtk.Fixed()
    window.add(fixed)
    entry = Gtk.Entry()
    entry.set_name('themeLabEntry_' + generated['style_id'])
    entry.set_size_request(320, 44)
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
        ['xdotool', 'search', '--name', '^' + title + '$'],
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
        raise AssertionError((name, 'X focus mismatch', server_focus, window_id))
    if not entry.is_focus() or not window.get_property('has-toplevel-focus'):
        raise AssertionError((name, 'GTK did not receive mapped X focus'))

    baseline = subprocess.check_output(
        ['import', '-window', window_id, 'png:-'], timeout=5)
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'],
                   check=True, timeout=5)
    drain_events()
    bounds = entry.get_selection_bounds()
    if len(bounds) == 3:
        bounds = bounds[1:] if bounds[0] else ()
    if bounds != (0, len(text)):
        raise AssertionError((name, 'incorrect selection range', bounds))
    selected = subprocess.check_output(
        ['import', '-window', window_id, 'png:-'], timeout=5)
    focus_after = entry.is_focus() and window.get_property('has-toplevel-focus')

    base_image = Image.open(io.BytesIO(baseline)).convert('RGB')
    selected_image = Image.open(io.BytesIO(selected)).convert('RGB')
    if base_image.size != selected_image.size:
        raise AssertionError((name, 'capture dimensions changed'))
    selected_background_rgb = builder.art._rgb(
        palette[builder.art.ROLES['view-fg'][0]])
    selected_text_rgb = builder.art._rgb(
        palette[builder.art.ROLES['view'][0]])
    before = sum(pixel == selected_background_rgb for pixel in base_image.getdata())
    after = sum(pixel == selected_background_rgb for pixel in selected_image.getdata())
    selected_text_pixels = sum(pixel == selected_text_rgb for pixel in selected_image.getdata())
    changed = sum(a != b for a, b in zip(base_image.getdata(), selected_image.getdata()))
    if after <= before or selected_text_pixels <= 0 or changed <= 0 or not focus_after:
        raise AssertionError((name, 'inverse view roles/focus did not persist', before, after, changed))

    folder = output / name
    folder.mkdir(parents=True, exist_ok=True)
    baseline_path = folder / 'unselected-mapped.png'
    selected_path = folder / 'selected-mapped.png'
    base_image.save(baseline_path)
    selected_image.save(selected_path)
    rows.append({
        'scheme': name,
        'scheme_path': str(scheme_path),
        'scheme_sha256': origin['sha256'],
        'xid': int(window_id),
        'xdotool_focused_xid': int(server_focus),
        'gtk_entry_is_focus': True,
        'gtk_toplevel_has_focus': True,
        'selection_bounds': list(bounds),
        'entry_selected_background_view_text_rgb': selected_background_rgb,
        'entry_selected_text_view_background_rgb': selected_text_rgb,
        'exact_role_pixels_before': before,
        'exact_role_pixels_after': after,
        'added_role_pixels': after - before,
        'selected_text_role_pixels_after': selected_text_pixels,
        'changed_pixels': changed,
        'captures': {'unselected': str(baseline_path), 'selected': str(selected_path)},
    })
    window.destroy()
    drain_events()

if len({tuple(row['entry_selected_background_view_text_rgb']) for row in rows}) < 2:
    raise AssertionError('real schemes did not exercise different inverted view roles')
if len({tuple(row['entry_selected_text_view_background_rgb']) for row in rows}) < 2:
    raise AssertionError('real schemes did not exercise different inverted text roles')
result = {
    'status': 'passed',
    'gtk': '2.24.33',
    'control': 'real GtkEntry with mapped X11 focus and Ctrl+A',
    'schemes': rows,
    'limits': [
        'This verifies GtkEntry reverse-video mapping through KDE view roles in three schemes, using the live SR10.4 VUE selected state as the design rule.',
        'The VUE pixels do not identify the compiled Xt resource that supplies the original colors.',
        'Xvfb has no window manager, so KWin integration and human approval remain untested.',
        'No final RGB is added to the product; each expected color is read from the selected scheme roles.',
    ],
}
(output / 'RESULTADO.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'schemes': [
    {'name': row['scheme'], 'inverse_background_rgb': row['entry_selected_background_view_text_rgb'],
     'pixels_added': row['added_role_pixels']} for row in rows]}, ensure_ascii=False, indent=2))
