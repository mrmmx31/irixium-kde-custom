#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real GTK2 all-control scene in disposable Xvfb; no personal display input."""
import configparser
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageChops

if os.environ.get('I167_PRIVATE_ALL_CONTROLS') != '1':
    raise SystemExit('Run only through the private GTK2 Xvfb test harness.')
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/theme-lab/tests'))
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
from test_backend import backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from native_scene_gtk2 import scene_records
from scene_contract import CONTROLS
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk

assert os.environ.get('DISPLAY')
Gtk.init([])
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
output.chmod(0o700)
sources = {
    'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
    'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
    'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
}
yellow = configparser.ConfigParser(interpolation=None)
yellow.optionxform = str
yellow.read(sources['DomainOS'])
yellow['General']['Name'] = 'Artificial yellow test'
for section in ('Colors:Window', 'Colors:Button', 'Colors:View'):
    yellow[section]['BackgroundNormal'] = '236,216,112'
    yellow[section]['BackgroundAlternate'] = '216,196,92'
    yellow[section]['ForegroundNormal'] = '32,28,12'
yellow['Colors:Selection']['BackgroundNormal'] = '88,72,24'
yellow['Colors:Selection']['ForegroundNormal'] = '255,248,216'
sources['TestYellow'] = output / 'TestYellow.colors'
with sources['TestYellow'].open('w', encoding='utf-8') as stream:
    yellow.write(stream)

def drain(seconds=.12):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(.001)

base = model()
base['selected_family'] = 'gtk2'
recipe = base['recipes']['gtk2']
recipe.update(visible_categories=31, visible_controls=(1 << len(CONTROLS)) - 1,
              selected_control=0, edit_state=0)
recipe['positions'] = [[16 + (index % 2) * 540,
                        16 + (index // 2) * 110] for index in range(len(CONTROLS))]
recipe['sizes'] = [[0, 0] for _ in CONTROLS]
original = copy.deepcopy(base)
results = []
for scheme, source in sources.items():
    folder = output / scheme
    folder.mkdir(exist_ok=True)
    folder.chmod(0o700)
    snapshot = generate_scrollbar_snapshot(backend, ROOT, folder, base, source)
    assert set(snapshot['translated_controls']) == set(CONTROLS), snapshot['translated_controls']
    assert backend.palette_inputs_current(snapshot)
    for origin in ('separate', 'coupled'):
        host = None
        xid = None
        if origin == 'coupled':
            host = Gtk.Window()
            host.set_default_size(1100, 1000)
            socket = Gtk.Socket()
            socket.set_size_request(1100, 1000)
            host.add(socket)
            host.show_all()
            drain()
            xid = socket.get_id()
        project = folder / (origin + '-PROJECT.json')
        backend.write_json(project, base)
        digest = hashlib.sha256(project.read_bytes()).hexdigest()
        session = NativeSession(backend, Gtk, Gdk, ROOT, snapshot['rc'], base,
                                digest, None, embed_window=xid)
        scene = session.scene
        scene.fixed.set_size_request(1100, 1000)
        if host is not None:
            host.resize(1100, 1000)
        scene.window.resize(1100, 1000)
        scene.window.show_all()
        drain(.35)
        window_width, window_height = scene.window.get_size()
        assert window_width >= 1100 and window_height >= 1000, (origin, window_width, window_height)
        records = scene_records(base)
        metrics = scene.metrics()
        assert len(records) == len(metrics) == len(CONTROLS)
        assert [row['id'] for row in metrics] == list(CONTROLS)
        assert all(widget.get_mapped() and widget.is_drawable()
                   for widget in scene.widgets.values())
        for row, record in zip(metrics, records):
            assert row['origin'] == origin, row
            assert row['allocation'][0:2] == [record['x'], record['y']], row
            assert row['allocation'][2] > 1 and row['allocation'][3] > 1, row
            assert row['coordinate_space'] == 'gtk_logical_px', row
            assert record['x'] + row['allocation'][2] <= window_width, row
            assert record['y'] + row['allocation'][3] <= window_height, row
        assert origin == 'separate' or scene.window.get_embedded()
        png = folder / f'{origin}-all-controls.png'
        subprocess.run(['import', '-window', 'root', str(png)], check=True, timeout=10)
        # GtkRC styles are cached by name. Compare actual native pixels to this
        # snapshot's role-derived assets while all four schemas are loaded in
        # the same GTK process; this catches stale colors after a live reload.
        screenshot = Image.open(png).convert('RGB')
        assets = folder / 'gtk2-scrollbars'
        by_id = {row['id']: row for row in metrics}
        scrollbar_checks = []
        for control, directions in (('scroll_h', ('left', 'right')),
                                    ('scroll_v', ('up', 'down'))):
            row = by_id[control]
            x, y, width, height = row['allocation']
            boxes = ((x, y, x + 15, y + 15), (x + width - 15, y + height - 15,
                                               x + width, y + height))
            for direction, box in zip(directions, boxes):
                actual = screenshot.crop(box)
                expected = Image.open(assets / f'arrow-{direction}-normal.png').convert('RGB')
                difference = ImageChops.difference(actual, expected)
                if difference.getbbox() is not None:
                    raise AssertionError(f'{scheme}/{origin}/{control}/{direction}: rendered cell differs from current palette asset')
                scrollbar_checks.append({'control': control, 'direction': direction,
                                         'pixels_equal': 225, 'pixels_total': 225})
        results.append({'scheme': scheme, 'origin': origin,
                        'controls': [row['id'] for row in metrics],
                        'sizes': {row['id']: row['allocation'][2:] for row in metrics},
                        'all_mapped': True, 'within_viewport': True,
                        'window_size': [window_width, window_height],
                        'palette_inputs_current': True,
                        'scrollbar_cells_match_current_palette_assets': scrollbar_checks,
                        'capture': png.relative_to(output).as_posix()})
        scene.gestures.close()
        scene.window.destroy()
        if host is not None:
            host.destroy()
        drain()
assert base == original
report = {
    'status': 'passed', 'native_toolkit': 'GTK2 2.24',
    'controls': list(CONTROLS), 'control_count': len(CONTROLS),
    'schemes': list(sources), 'origins': ['separate', 'coupled'],
    'native_scenes': results,
    'scope': 'All catalog Gtk2 control types generated and mounted together as real widgets in separate Window and XEmbed Plug scenes; every allocation is mapped, visible within the viewport and coordinate checked. Does not claim per-control visual fidelity, all states, controller-C integration, or historical approval.',
    'model_unchanged': True, 'personal_display_input_sent': False,
    'theme_installed': False,
}
(output / 'ALL-CONTROLS-RESULTADO.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'passed', 'control_count': len(CONTROLS),
                  'schemes': len(sources), 'native_scenes': len(results)}))
