#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify saved custom-relief captures of the natural GTK2 geometry fixture.

Edge samples apply only to the explicitly checked15px/21px-minimum fixture;
they are not an implementation of GtkRange's general slider layout.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from PIL import Image
from test_gtk2_paint_native import ROOT, verify_arrow_masks
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work', type=Path, required=True)
args = parser.parse_args()
folder = args.work.resolve()
recipe = json.loads((folder / 'recipe.json').read_text())
native = json.loads((folder / 'native.json').read_text())
horizontal = next(row for row in native['widgets'] if row['type'] == 'GtkHScrollbar')
assert horizontal['natural_request'] == [49, 15]
assert horizontal['properties']['min-slider-length'] == 21
assert recipe['scrollbar_parts']['trough']['state_relief']['normal'] == 'raised'
assert recipe['scrollbar_parts']['thumb']['state_relief']['normal'] == 'sunken'
builder = backend.load_builder(ROOT)
source = ROOT / 'colors/DomainOS-SR10.4.colors'
colors, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
results = []
with backend.recipe_rules(builder, recipe['palette']):
    face = builder.art._rgb(colors[builder.art.ROLES['button'][0]])
    light, dark = (builder.art._rgb(builder.art.evaluate(builder.art.pixel_plan('button', token), colors))
                   for token in ('light', 'dark'))
    for cycle in native['cycles']:
        held = verify_arrow_masks(folder / 'assets', 'normal', native, face, recipe,
                                  capture=cycle['held_capture'], pressed_direction=cycle['direction'])
        release = verify_arrow_masks(folder / 'assets', 'normal', native, face, recipe,
                                     capture=cycle['released_capture'])
        image = Image.open(cycle['released_capture']).convert('RGB')
        x, y, _, _ = horizontal['allocation']
        assert image.getpixel((x + 4, y)) == light
        assert image.getpixel((x + 18, y + 2)) == dark
        results.append({'cycle': cycle, 'held': held, 'release': release,
                        'raised_trough_top_verified': True, 'sunken_thumb_top_verified': True})
(folder / 'verified.json').write_text(json.dumps({'rows': results, 'palette_origin': origin}, indent=2))
print('4 custom cycles/32 arrow masks; fixture trough/thumb edges verified')
