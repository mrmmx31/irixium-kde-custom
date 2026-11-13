#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real GTK2 press/release and blocked-range proof, owned Xvfb only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from test_gtk2_paint_native import ROOT, verify_arrow_masks
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend
from gtk2_recipe import paint_scrollbars


def run(fixtures, output):
    output.mkdir(parents=True, exist_ok=True)
    recipe = json.loads((fixtures / 'recipe.json').read_text())
    recipe_file = output / 'recipe.json'
    recipe_file.write_text(json.dumps(recipe))
    sources = {'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
               'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
               'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
               'TestYellow': fixtures / 'TestYellow.colors'}
    builder = backend.load_builder(ROOT)
    results = []
    for scheme, source in sources.items():
        colors, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        assets = output / scheme / 'assets'
        with backend.recipe_rules(builder, recipe['palette']):
            generated = paint_scrollbars(builder, recipe, colors, assets)
            for state in ('normal', 'endpoint', 'disabled'):
                folder = output / scheme / state
                command = ['xvfb-run', '-a', '/usr/bin/python3', '-B',
                           str(ROOT / 'tools/theme-lab/tests/probe_gtk2_runtime.py'),
                           '--recipe', str(recipe_file), '--paint-rc', generated['rc'], '--cycles', str(folder)]
                if state == 'endpoint': command += ['--endpoint-cycles']
                if state == 'disabled': command += ['--insensitive']
                environment = dict(os.environ, GTK_MODULES='', GTK2_RC_FILES='/dev/null', I167_PRIVATE_PROBE='1')
                child = subprocess.run(command, env=environment, text=True, capture_output=True, timeout=25)
                folder.mkdir(parents=True, exist_ok=True)
                (folder / 'stderr.log').write_text(child.stderr)
                (folder / 'native.json').write_text(child.stdout)
                if child.returncode or child.stderr: raise RuntimeError(child.stderr or child.stdout)
                native = json.loads(child.stdout)
                face = builder.art._rgb(colors[builder.art.ROLES['button'][2 if state == 'disabled' else 0]])
                for cycle in native['cycles']:
                    pressed = cycle['direction'] if not cycle['blocked'] else None
                    held = verify_arrow_masks(assets, state, native, face, recipe,
                                              capture=cycle['held_capture'], pressed_direction=pressed)
                    released = verify_arrow_masks(assets, state, native, face, recipe,
                                                  capture=cycle['released_capture'])
                    results.append({'scheme': scheme, 'state': state, 'cycle': cycle,
                                    'held_mask_deltas': held, 'released_mask_deltas': released,
                                    'palette_origin': origin})
    report = {'status': 'passed', 'cycles': results,
              'scope': 'GTK2 native four-direction input/value, pressed relief, release and blocked input in four role palettes',
              'personal_input_sent': False, 'historical_all_states_claimed': False}
    (output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'status': 'passed', 'cycles': len(results), 'directional_masks': len(results) * 8}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.fixtures.resolve(), args.output.resolve())
