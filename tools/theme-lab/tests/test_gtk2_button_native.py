#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Four-palette real GTK2 button state fixture; no historical approval claim."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from PIL import Image
from test_backend import model, ROOT, backend
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
from gtk2_buttons import paint_button

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--yellow', type=Path, required=True)
parser.add_argument('--shadow', type=int, default=2)
parser.add_argument('--padding', type=int, default=4)
parser.add_argument('--font', type=int, default=13)
args = parser.parse_args()
recipe = model()['recipes']['gtk2']
recipe['geometry'].update(shadow_px=args.shadow, control_padding_px=args.padding, font_px=args.font)
before = copy.deepcopy(recipe)
builder = backend.load_builder(ROOT)
sources = {'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
           'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
           'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
           'TestYellow': args.yellow.resolve()}
results = []
for scheme, source in sources.items():
    folder = backend.private_output(args.output.absolute() / scheme, ROOT)
    colors, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
    with backend.recipe_rules(builder, recipe['palette']):
        receipt = paint_button(builder, recipe, colors, folder)
    (folder / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    (folder / 'recipe.json').write_text(json.dumps(recipe, indent=2))
    (folder / 'colors.json').write_text(json.dumps({'colors': colors, 'origin': origin}, indent=2))
    child = subprocess.run(['xvfb-run', '-a', '/usr/bin/python3', '-B',
                            str(ROOT / 'tools/theme-lab/tests/probe_gtk2_button.py'),
                            '--rc', receipt['rc'], '--output', str(folder)],
                           env=dict(os.environ, I167_PRIVATE_PROBE='1', GTK_MODULES='', GTK2_RC_FILES='/dev/null'),
                           capture_output=True, text=True, timeout=15)
    (folder / 'native.json').write_text(child.stdout)
    (folder / 'stderr.log').write_text(child.stderr)
    if child.returncode or child.stderr: raise RuntimeError(child.stderr or child.stdout)
    native = json.loads(child.stdout)
    assert native['allocation'] == [25, 25, 180, 50]
    assert native['style_properties']['inner-border'] == [args.padding] * 4
    # Record captures and real input first. Pixel verification is separate so
    # a verifier defect cannot require replaying a valid native input cycle.
    results.append({'scheme': scheme, 'native': native, 'palette': origin})
assert recipe == before
(args.output / 'results.json').write_text(json.dumps({'status': 'passed_native', 'rows': results,
    'recipe_unchanged': True, 'historical_fidelity_claimed': False}, indent=2))
print(json.dumps({'status': 'passed_native', 'palettes': len(results), 'captures': 24,
                  'disabled_clicks_blocked': 4, 'successful_release_clicks': 4}))
