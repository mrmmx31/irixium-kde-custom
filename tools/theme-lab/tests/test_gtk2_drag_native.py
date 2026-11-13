#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK2 thumb drag and independent held/released relief, private Xvfb."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from PIL import Image
from test_gtk2_paint_native import ROOT
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend
from gtk2_recipe import paint_scrollbars


def run(fixtures, output):
    output.mkdir(parents=True, exist_ok=True)
    recipe = json.loads((fixtures / 'recipe.json').read_text())
    recipe['scrollbar_parts'] = {'thumb': {'state_relief': {'normal': 'sunken', 'pressed': 'flat'}}}
    recipe_file = output / 'recipe.json'
    recipe_file.write_text(json.dumps(recipe))
    builder = backend.load_builder(ROOT)
    reports = []
    sources = {'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
               'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
               'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
               'TestYellow': fixtures / 'TestYellow.colors'}
    for name, source in sources.items():
        colors, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        folder = output / name
        with backend.recipe_rules(builder, recipe['palette']):
            generated = paint_scrollbars(builder, recipe, colors, folder / 'assets')
            environment = dict(os.environ, GTK_MODULES='', GTK2_RC_FILES='/dev/null', I167_PRIVATE_PROBE='1')
            child = subprocess.run(['xvfb-run', '-a', '/usr/bin/python3', '-B',
                                    str(ROOT / 'tools/theme-lab/tests/probe_gtk2_runtime.py'),
                                    '--recipe', str(recipe_file), '--paint-rc', generated['rc'],
                                    '--drag-cycles', str(folder / 'captures')],
                                   env=environment, text=True, capture_output=True, timeout=25)
            (folder / 'stderr.log').write_text(child.stderr)
            (folder / 'native.json').write_text(child.stdout)
            if child.returncode or child.stderr:
                raise RuntimeError(child.stderr or child.stdout)
            native = json.loads(child.stdout)
            face = tuple(builder.art._rgb(colors[builder.art.ROLES['button'][0]]))
            dark = tuple(builder.art._rgb(builder.art.evaluate(builder.art.pixel_plan('button', 'dark'), colors)))
            for drag in native['drags']:
                horizontal = drag['orientation'] == 'horizontal'
                widget = native['widgets'][0 if horizontal else 1]
                x, y, width, height = widget['allocation']
                assert (width if horizontal else height) == 200
                start, end = drag['held_range']
                assert drag['released_range'] == [start, end]
                # Sample the central top/left bevel away from corner joins;
                # positions come from GtkRange itself, not guessed thumb size.
                point = (x + (start + end) // 2, y + 2) if horizontal else (x + 2, y + (start + end) // 2)
                held = Image.open(drag['held_capture']).convert('RGB')
                released = Image.open(drag['released_capture']).convert('RGB')
                assert held.getpixel(point) == face, (name, drag['orientation'], 'held', held.getpixel(point), face)
                assert released.getpixel(point) == dark, (name, drag['orientation'], 'released', released.getpixel(point), dark)
                reports.append({'scheme': name, 'drag': drag, 'sample_point': point,
                                'held_flat_verified': True, 'released_sunken_verified': True,
                                'palette_origin': origin})
    (output / 'results.json').write_text(json.dumps({'status': 'passed', 'drags': reports,
        'scope': 'Two native orientations, real adjustment and thumb relief in four KDE palettes; private fixture only'}, indent=2))
    print(json.dumps({'status': 'passed', 'native_drags': len(reports)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.fixtures.resolve(), args.output.resolve())
