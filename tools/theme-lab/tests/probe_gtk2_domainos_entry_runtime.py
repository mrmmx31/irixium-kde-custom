#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise selected GtkEntry colors from the complete GTK2 runtime adapter."""
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
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'tests'),
                str(Path(__file__).resolve().parent)]

from test_backend import ROOT as REPO, backend
import gtk2_domainos_palette
import domainos_motif_art as art
from test_gtk2_palette import native_export

import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk

if not Gtk.init_check([])[0]:
    raise SystemExit('GTK2 runtime selection probe requires an isolated X display')

output = Path(os.environ.get(
    'I167_RUNTIME_SELECTION_OUTPUT',
    TEMP_ROOT / 'i167-entry-selection-runtime-r115'))
output.mkdir(parents=True, exist_ok=True)
schemes = {
    'DomainOS': REPO / 'colors/DomainOS-SR10.4.colors',
    'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
    'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
}
sample_text = 'a*a'
Gtk.Settings.get_default().set_property('gtk-cursor-blink', False)
builder = backend.load_builder(REPO)


def drain_events():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def run_scheme(name, scheme_path):
    palette, origin = backend.native_roles(
        REPO, scheme_path, builder.art,
        backend.sha(scheme_path.read_bytes()))
    expected_background = builder.art._rgb(palette[builder.art.ROLES['view-fg'][0]])
    expected_foreground = builder.art._rgb(palette[builder.art.ROLES['view'][0]])
    expected_entry_face = builder.art._rgb(art.tone(
        palette[art.ROLES['header'][0]],
        1.0-gtk2_domainos_palette.ENTRY_FACE_FACTOR, '#000000'))

    generated_root = output / name / 'runtime'
    prepared = gtk2_domainos_palette.prepare_domainos(
        REPO / 'gtk/DomainOS-SR10-4', native_export(palette), generated_root)
    for path, payload in prepared.files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    Gtk.rc_parse(str(prepared.gtkrc))

    title = 'I167 GTK2 DomainOS runtime selection ' + name
    window = Gtk.Window()
    window.set_title(title)
    window.set_default_size(360, 90)
    fixed = Gtk.Fixed()
    window.add(fixed)
    entry = Gtk.Entry()
    entry.set_size_request(320, 44)
    entry.set_text(sample_text)
    entry.set_position(2)
    fixed.put(entry, 16, 16)
    window.show_all()
    drain_events()

    window_id = subprocess.check_output(
        ['xdotool', 'search', '--name', '^' + title + '$'],
        text=True, timeout=5).split()[0]
    subprocess.run(['xdotool', 'windowmap', window_id, 'windowraise', window_id,
                    'windowfocus', '--sync', window_id],
                   check=True, timeout=5)
    subprocess.run(['xdotool', 'mousemove', '--window', window_id,
                    '32', '36', 'click', '1'], check=True, timeout=5)
    drain_events()
    server_focus = subprocess.check_output(
        ['xdotool', 'getwindowfocus'], text=True, timeout=5).strip()
    if server_focus != window_id or not entry.is_focus() or not window.get_property('has-toplevel-focus'):
        raise AssertionError((name, 'mapped GTK/X focus was lost', server_focus, window_id))

    baseline = Image.open(io.BytesIO(subprocess.check_output(
        ['import', '-window', window_id, 'png:-'], timeout=5))).convert('RGB')
    allocation = entry.get_allocation()
    entry_roi = baseline.crop((allocation.x+2, allocation.y+2,
                               allocation.x+allocation.width-2,
                               allocation.y+allocation.height-2))
    entry_face_pixels = sum(pixel == expected_entry_face
                            for pixel in entry_roi.getdata())
    if entry_face_pixels < 1000:
        raise AssertionError((name, 'runtime GtkEntry face did not use the derived Header role',
                              list(expected_entry_face), entry_face_pixels))
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'shift+Left'],
                   check=True, timeout=5)
    drain_events()
    bounds = entry.get_selection_bounds()
    if len(bounds) == 3:
        bounds = bounds[1:] if bounds[0] else ()
    if bounds != (1, 2):
        raise AssertionError((name, 'incorrect selection bounds', bounds))
    selected = Image.open(io.BytesIO(subprocess.check_output(
        ['import', '-window', window_id, 'png:-'], timeout=5))).convert('RGB')
    if baseline.size != selected.size:
        raise AssertionError((name, 'capture dimensions changed'))

    pixels_before = sum(pixel == expected_background for pixel in baseline.getdata())
    pixels_after = sum(pixel == expected_background for pixel in selected.getdata())
    selected_ink_pixels = sum(pixel == expected_foreground for pixel in selected.getdata())
    changed_pixels = sum(a != b for a, b in zip(baseline.getdata(), selected.getdata()))
    if pixels_after <= pixels_before or selected_ink_pixels == 0 or changed_pixels == 0:
        raise AssertionError((name, 'runtime reverse video was not rendered',
                              pixels_before, pixels_after, selected_ink_pixels, changed_pixels))

    folder = output / name / 'runtime-capture'
    folder.mkdir(parents=True, exist_ok=True)
    baseline_path, selected_path = folder / 'unselected.png', folder / 'selected.png'
    baseline.save(baseline_path)
    selected.save(selected_path)
    window.destroy()
    drain_events()
    return {
        'scheme': name,
        'scheme_path': str(scheme_path),
        'scheme_sha256': origin['sha256'],
        'gtk_version': '2.24.33',
        'runtime_rc_sha256': backend.sha(prepared.gtkrc.read_bytes()),
        'runtime_manifest_sha256': backend.sha(
            (prepared.directory / 'manifest.json').read_bytes()),
        'expected_inverse_background_rgb': list(expected_background),
        'expected_inverse_text_rgb': list(expected_foreground),
        'expected_entry_face_rgb': list(expected_entry_face),
        'entry_face_pixels': entry_face_pixels,
        'selection_bounds': list(bounds),
        'added_background_role_pixels': pixels_after - pixels_before,
        'selected_text_role_pixels': selected_ink_pixels,
        'changed_pixels': changed_pixels,
        'captures': {'unselected': str(baseline_path), 'selected': str(selected_path)},
    }


rows = [run_scheme(name, path) for name, path in schemes.items()]
if len({tuple(row['expected_inverse_background_rgb']) for row in rows}) < 2:
    raise AssertionError('KDE schemes did not change the runtime entry background role')
if len({tuple(row['expected_inverse_text_rgb']) for row in rows}) < 2:
    raise AssertionError('KDE schemes did not change the runtime entry text role')
result = {
    'status': 'passed',
    'adapter': 'complete GTK2 DomainOS runtime RC from prepare_domainos()',
    'control': 'real mapped GtkEntry, queried GTK selected state, Ctrl+A and pixel capture',
    'schemes': rows,
    'limits': [
        'The selected VUE field provides a visual reverse-video rule, not proof of its internal Motif resource source.',
        'Xvfb has no window manager, so KWin integration and human approval remain untested.',
        'Runtime colors are generated from KDE view roles; no captured final RGB is fixed in the product.',
    ],
}
(output / 'RESULTADO.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'schemes': [
    {'name': row['scheme'], 'selected_background': row['expected_inverse_background_rgb'],
     'selected_text': row['expected_inverse_text_rgb'],
     'changed_pixels': row['changed_pixels']} for row in rows]},
    ensure_ascii=False, indent=2))
