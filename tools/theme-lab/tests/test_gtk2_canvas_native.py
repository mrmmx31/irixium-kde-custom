#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Four current KDE palettes, both GTK2 native origins, canvas state pixels."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from test_gtk2_paint_native import ROOT, verify_arrow_masks

sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend
from gtk2_generation import generate_scrollbar_snapshot

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fixtures', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.fixtures = args.fixtures.resolve()
args.output = args.output.absolute()
args.output.mkdir(parents=True, exist_ok=True)
recipe = json.loads((args.fixtures / 'recipe.json').read_text())
recipe.update(visible_controls=(1 << 10) | (1 << 11), selected_control=10,
              positions=[[41, 57] for _ in range(16)], sizes=[[0, 0] for _ in range(16)])
recipe['positions'][11] = [311, 103]
recipe['sizes'][10], recipe['sizes'][11] = [240, 15], [15, 270]
model = {'recipes': {'gtk2': recipe}, 'color_scheme': ''}
original = copy.deepcopy(model)
sources = {'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
           'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
           'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
           'TestYellow': args.fixtures / 'TestYellow.colors'}
builder = backend.load_builder(ROOT)
rows = []
for name, source in sources.items():
    folder = backend.private_output(args.output / name, ROOT)
    receipt = generate_scrollbar_snapshot(backend, ROOT, folder, model, source)
    colors = json.loads((folder / 'GTK2-NATIVE-COLORS.json').read_text())['colors']
    expected = {state: builder.art._rgb(colors[builder.art.ROLES['window'][index]])
                for state, index in [('normal', 0), ('insensitive', 2)]}
    (folder / 'expected.json').write_text(json.dumps(expected))
    project = folder / 'PROJECT.json'; project.write_text(json.dumps(model))
    for origin in ('coupled', 'separate'):
        output = backend.private_output(folder / origin, ROOT)
        command = ['xvfb-run', '-a', '/usr/bin/python3', '-B',
                   str(ROOT / 'tools/theme-lab/tests/probe_gtk2_canvas.py'), '--project', str(project),
                   '--rc', receipt['rc'], '--expected', str(folder / 'expected.json'), '--output', str(output)]
        if origin == 'coupled': command.append('--embedded')
        child = subprocess.run(command, env=dict(os.environ, I167_PRIVATE_PROBE='1',
                               GTK_MODULES='', GTK2_RC_FILES='/dev/null'), text=True,
                               capture_output=True, timeout=15)
        (output / 'native.json').write_text(child.stdout)
        (output / 'stderr.log').write_text(child.stderr)
        if child.returncode or child.stderr: raise RuntimeError(child.stderr or child.stdout)
        native = json.loads(child.stdout)
        widgets = [{'type': 'GtkHScrollbar' if item['index'] == 10 else 'GtkVScrollbar',
                    'allocation': item['allocation']} for item in native['metrics']]
        with backend.recipe_rules(builder, recipe['palette']):
            face = builder.art._rgb(colors[builder.art.ROLES['button'][0]])
            for state in ('normal', 'restored'):
                verify_arrow_masks(folder / 'gtk2-scrollbars', 'normal', {'widgets': widgets},
                                   face, recipe, capture=output / (state + '.png'))
        rows.append(dict(native, palette=name, native_arrow_masks_unchanged=8))
    # Canvas style must leave the previously verified 24 scrollbar PNGs identical.
    for asset in receipt['assets']:
        assert (folder / 'gtk2-scrollbars' / asset).read_bytes() == (args.fixtures / name / asset).read_bytes()
assert model == original
(args.output / 'results.json').write_text(json.dumps({'status': 'passed', 'rows': rows,
    'model_unchanged': True, 'verified_bar_assets_unchanged': 96}, indent=2))
print(json.dumps({'status': 'passed', 'origins': 8, 'canvas_captures': 24,
                  'verified_bar_assets_unchanged': 96}))
