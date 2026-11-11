# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure GTK2 GtkEntry caret geometry and role without mapping a host window."""
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
TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

from test_backend import ROOT as REPO, backend, model
from gtk2_entries import paint_entry

import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gdk, GObject, Gtk

if not Gtk.init_check([])[0]:
    raise SystemExit('GTK2 caret probe needs an existing X display')

settings = Gtk.Settings.get_default()
blink_was_enabled = settings.get_property('gtk-cursor-blink')
blink_time_ms = settings.get_property('gtk-cursor-blink-time')
settings.set_property('gtk-cursor-blink', False)

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
yellow['General']['Name'] = 'Artificial yellow caret test'
yellow['Colors:View']['ForegroundNormal'] = '32,28,12'
sources['TestYellow'] = TEMP_ROOT / 'i167-entry-caret-TestYellow.colors'
with sources['TestYellow'].open('w', encoding='utf-8') as stream:
    yellow.write(stream)

output = Path(os.environ.get('I167_CARET_OUTPUT',
                             TEMP_ROOT / 'i167-entry-caret-r61'))
output.mkdir(parents=True, exist_ok=True)
rows = []
text = '.a'

with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-entry-caret-r61-') as temporary:
    for name, source in sources.items():
        palette, origin = backend.native_roles(
            REPO, source, builder.art, backend.sha(source.read_bytes()))
        generated_dir = Path(temporary) / name
        with backend.recipe_rules(builder, recipe['palette']):
            generated = paint_entry(builder, recipe, palette, generated_dir)
        Gtk.rc_parse(generated['rc'])

        window = Gtk.OffscreenWindow()
        # Match the 338x34 SR10.4 File Name/Search Directories field measured
        # in R57; leave height natural to the GTK2 font and recipe.
        window.set_default_size(338, 34)
        entry = Gtk.Entry()
        entry.set_name('themeLabEntry_' + generated['style_id'])
        entry.set_size_request(338, -1)
        entry.set_text(text)
        window.add(entry)
        window.show_all()
        while Gtk.events_pending():
            Gtk.main_iteration()
        baseline_path = output / (name + '-unfocused.png')
        window.get_pixbuf().savev(str(baseline_path), 'png', [], [])

        entry.set_position(len(text))
        event = Gdk.Event.new(Gdk.EventType.FOCUS_CHANGE)
        event.focus_change.window = entry.get_window()
        event.focus_change.in_ = True
        event.focus_change.send_event = True
        Gtk.Widget.send_focus_change(entry, event)
        entry.set_state(Gtk.StateType.ACTIVE)
        while Gtk.events_pending():
            Gtk.main_iteration()
        window.queue_draw()
        while Gtk.events_pending():
            Gtk.main_iteration()
        if not entry.has_focus():
            raise AssertionError(name + ': synthetic focus did not activate Entry')

        aspect = GObject.Value()
        aspect.init(GObject.TYPE_FLOAT)
        entry.style_get_property('cursor-aspect-ratio', aspect)
        if aspect.get_float() != 0.0:
            raise AssertionError(name + ': one-pixel caret style was not applied')

        image_path = output / (name + '.png')
        window.get_pixbuf().savev(str(image_path), 'png', [], [])
        baseline = Image.open(baseline_path).convert('RGB')
        focused = Image.open(image_path).convert('RGB')
        text_color = builder.art._rgb(
            palette[builder.art.ROLES['view-fg'][0]])
        changed = []
        # Exclude the active frame around the outside of the GtkEntry.
        for y in range(5, focused.height - 5):
            for x in range(5, focused.width - 5):
                after = focused.getpixel((x, y))
                if after == text_color and after != baseline.getpixel((x, y)):
                    changed.append((x, y))
        if not changed:
            raise AssertionError(name + ': no caret pixels in dynamic text role')
        bbox = [min(x for x, _ in changed), min(y for _, y in changed),
                max(x for x, _ in changed) + 1, max(y for _, y in changed) + 1]
        stem_width = bbox[2] - bbox[0]
        if stem_width != 1:
            raise AssertionError(name + ': expected 1px caret stem, got ' + str(stem_width))

        rows.append({
            'scheme': name,
            'text_role_rgb': text_color,
            'cursor_aspect_ratio': aspect.get_float(),
            'entry_allocation_px': [entry.get_allocation().width,
                                    entry.get_allocation().height],
            'changed_text_role_pixels': len(changed),
            'caret_pixel_bbox': bbox,
            'stem_width_px': stem_width,
            'png': str(image_path),
            'palette_origin': {'path': origin['path'], 'sha256': origin['sha256']},
        })
        window.destroy()
        while Gtk.events_pending():
            Gtk.main_iteration()

settings.set_property('gtk-cursor-blink', blink_was_enabled)
result = {
    'status': 'passed',
    'control': 'GTK 2.24.33 GtkEntry in GtkOffscreenWindow',
    'method': 'no-blink test setting, baseline/focused pixel diff, synthetic GDK focus-in; no host window mapped',
    'gtk_cursor_blink_time_ms_before_probe': blink_time_ms,
    'rows': rows,
    'limits': [
        'The temporary no-blink setting is confined to this test process and restored afterwards.',
        'Synthetic focus proves GTK2 paint geometry and color only, not real X focus delivery.',
        'The probe verifies a 1px stem. GTK2 has no matching top/bottom caps in the native cursor painter; historical full-shape equivalence remains open.',
    ],
}
(output / 'RESULTADO.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': result['status'],
                  'rows': [{key: row[key] for key in
                            ('scheme', 'text_role_rgb', 'caret_pixel_bbox', 'stem_width_px')}
                           for row in rows]}, ensure_ascii=False))
