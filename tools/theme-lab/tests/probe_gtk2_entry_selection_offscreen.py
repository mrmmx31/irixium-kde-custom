# SPDX-License-Identifier: GPL-3.0-or-later
"""Check GTK2 Entry selection painting without mapping a host window.

The synthetic GDK focus event enables GTK2's selection renderer in an
OffscreenWindow. This verifies role translation only; it does not prove that
the X server delivers real focus events or that SR10.4 uses the same selection.
"""
import configparser
import json
import os
from pathlib import Path
import sys
import tempfile
from PIL import Image

if os.environ.get('T04_PRIVATE_ENTRY') != '1':
    raise SystemExit('set T04_PRIVATE_ENTRY=1 to enable this isolated GTK2 probe')

TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_backend import ROOT as REPO, backend, model
from gtk2_entries import paint_entry

import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gdk, Gtk

if not Gtk.init_check([])[0]:
    raise SystemExit('GTK2 selection probe needs an existing X display')

builder = backend.load_builder(REPO)
recipe = model()['recipes']['gtk2']
sources = {
    'DomainOS': REPO / 'colors/DomainOS-SR10.4.colors',
    'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
    'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
}

yellow = configparser.ConfigParser(interpolation=None)
yellow.optionxform = str
yellow.read(sources['DomainOS'])
yellow['General']['Name'] = 'Artificial yellow selection test'
yellow['Colors:Selection']['BackgroundNormal'] = '88,72,24'
yellow['Colors:Selection']['ForegroundNormal'] = '255,248,216'
sources['TestYellow'] = TEMP_ROOT / 'i167-entry-selection-TestYellow.colors'
with sources['TestYellow'].open('w', encoding='utf-8') as stream:
    yellow.write(stream)

output = Path(os.environ.get(
    'I167_SELECTION_OUTPUT', TEMP_ROOT / 'i167-entry-selection-r60'))
output.mkdir(parents=True, exist_ok=True)
rows = []
text = 'DomainOS SR10.4 selection'

with tempfile.TemporaryDirectory(dir=TEMP_ROOT,
                                 prefix='i167-entry-selection-r60-') as temporary:
    for name, source in sources.items():
        palette, origin = backend.native_roles(
            REPO, source, builder.art, backend.sha(source.read_bytes()))
        generated_dir = Path(temporary) / name
        with backend.recipe_rules(builder, recipe['palette']):
            generated = paint_entry(builder, recipe, palette, generated_dir)
        Gtk.rc_parse(generated['rc'])

        window = Gtk.OffscreenWindow()
        window.set_default_size(360, 90)
        entry = Gtk.Entry()
        entry.set_name('themeLabEntry_' + generated['style_id'])
        entry.set_size_request(320, 44)
        entry.set_text(text)
        window.add(entry)
        window.show_all()
        while Gtk.events_pending():
            Gtk.main_iteration()
        baseline_path = output / (name + '-unselected.png')
        window.get_pixbuf().savev(str(baseline_path), 'png', [], [])

        entry.select_region(0, -1)
        event = Gdk.Event.new(Gdk.EventType.FOCUS_CHANGE)
        event.focus_change.window = entry.get_window()
        event.focus_change.in_ = True
        event.focus_change.send_event = True
        Gtk.Widget.send_focus_change(entry, event)
        while Gtk.events_pending():
            Gtk.main_iteration()
        window.queue_draw()
        while Gtk.events_pending():
            Gtk.main_iteration()

        if not entry.has_focus():
            raise AssertionError(name + ': synthetic focus did not activate Entry')
        if entry.get_selection_bounds() != (0, len(text)):
            raise AssertionError(name + ': selected range changed')

        image_path = output / (name + '.png')
        pixbuf = window.get_pixbuf()
        pixbuf.savev(str(image_path), 'png', [], [])
        selected_bg = builder.art._rgb(
            palette[builder.art.ROLES['selection'][0]])
        selected_fg = builder.art._rgb(
            palette[builder.art.ROLES['selection-fg'][0]])
        image = Image.open(image_path).convert('RGB')
        baseline = Image.open(baseline_path).convert('RGB')
        background_pixels = sum(pixel == selected_bg for pixel in image.getdata())
        baseline_background_pixels = sum(
            pixel == selected_bg for pixel in baseline.getdata())
        changed_pixels = sum(
            before != after for before, after in zip(baseline.getdata(), image.getdata()))
        selected_role_pixels_added = background_pixels - baseline_background_pixels
        if selected_role_pixels_added <= 0:
            raise AssertionError(name + ': selection role did not increase in selected render')
        if changed_pixels == 0:
            raise AssertionError(name + ': selection produced no rendered pixel changes')

        rows.append({
            'scheme': name,
            'selection_background_role_rgb': selected_bg,
            'selection_foreground_role_rgb': selected_fg,
            'exact_background_role_pixels': background_pixels,
            'baseline_background_role_pixels': baseline_background_pixels,
            'added_background_role_pixels': selected_role_pixels_added,
            'changed_pixels_including_focus_frame': changed_pixels,
            'selected_bounds': list(entry.get_selection_bounds()),
            'focus_activation': 'synthetic GDK_FOCUS_CHANGE',
            'png': str(image_path),
            'palette_origin': {
                'kind': origin['kind'],
                'path': origin['path'],
                'sha256': origin['sha256'],
                'helper_sha256': origin['helper']['sha256'],
            },
        })
        window.destroy()
        while Gtk.events_pending():
            Gtk.main_iteration()

result = {
    'status': 'passed',
    'control': 'GTK2 2.x GtkEntry in GtkOffscreenWindow',
    'method': 'select_region plus synthetic GDK focus-in; no host window mapped',
    'rows': rows,
    'limit': 'Role translation/rendering only; does not prove real X focus delivery or historical SR10.4 selection appearance.',
}
(output / 'RESULTADO.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': result['status'], 'rows': rows}, ensure_ascii=False))
