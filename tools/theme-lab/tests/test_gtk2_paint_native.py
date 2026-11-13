#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real pixmap-engine role/geometry test in isolated Xvfb, not visual approval."""
import argparse
import configparser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend
from gtk2_recipe import paint_scrollbars, scrollbar_properties


def verify_arrow_source_pixels(folder, state, builder, palette, geometry):
    """Check each complete stepper cell against the shared SR10.4 pixel map."""
    art = builder.art
    for direction in ('up', 'down', 'left', 'right'):
        expected = art.kvantum_scrollbar_stepper(
            state, direction, bar_px=geometry['bar_px'],
            shadow_px=geometry['shadow_px'], arrow_px=geometry['arrow_px'])
        expected_rgb = [[art._rgb(art.evaluate(art.pixel_plan('button', token), palette))
                         for token in row] for row in expected]
        image = Image.open(folder / ('arrow-' + direction + '-' + state + '.png')).convert('RGB')
        assert image.size == (geometry['bar_px'], geometry['bar_px']), (state, direction, image.size)
        actual_rgb = [list(image.crop((0, y, image.width, y + 1)).getdata())
                      for y in range(image.height)]
        assert actual_rgb == expected_rgb, (state, direction, 'not equal to the SR10.4 pixel map')


def verify_arrow_masks(folder, state, native, face, recipe, capture=None, pressed_direction=None):
    screen = Image.open(capture or folder / (state + '.png')).convert('RGBA')
    mask_state = state if state in ('disabled', 'backdrop') else 'normal'
    properties = scrollbar_properties(recipe)
    border, cross, longitudinal = (properties[key] for key in ('trough-border', 'slider-width', 'stepper-size'))
    thickness = cross + 2 * border
    deltas = {}
    for widget in native['widgets']:
        x, y, width, height = widget['allocation']
        boxes = ([('left', x, y, longitudinal, thickness),
                  ('right', x + width - longitudinal, y, longitudinal, thickness)]
                 if widget['type'] == 'GtkHScrollbar' else
                 [('up', x, y, thickness, longitudinal),
                  ('down', x, y + height - longitudinal, thickness, longitudinal)])
        for direction, bx, by, bw, bh in boxes:
            glyph_state = 'pressed' if direction == pressed_direction else mask_state
            expected = Image.open(folder / ('arrow-' + direction + '-' + glyph_state + '.png')).convert('RGBA')
            assert expected.size == (bw, bh), (direction, expected.size, (bw, bh))
            actual = screen.crop((bx, by, bx + bw, by + bh))
            deltas[direction] = sum(a != b for a, b in zip(actual.getdata(), expected.getdata()))
            assert deltas[direction] == 0, (state, direction, deltas[direction])
    return deltas


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    yellow = configparser.ConfigParser(interpolation=None, strict=False)
    yellow.optionxform = str
    yellow.read('/usr/share/color-schemes/BreezeLight.colors')
    for section in yellow.sections():
        if section.startswith('Colors:'):
            yellow[section]['BackgroundNormal'] = '236,216,112'
            yellow[section]['ForegroundNormal'] = '32,28,12'
    yellow_path = output / 'TestYellow.colors'
    with yellow_path.open('w') as stream: yellow.write(stream)
    fixtures = {'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
                'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
                'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
                'TestYellow': yellow_path}
    recipe = {'geometry': {'bar_px': 15, 'shadow_px': 2, 'arrow_px': 11,
                           'thumb_cross_px': 11, 'arrow_thumb_gap_px': 1},
              'palette': dict(backend.DEFAULT_ROLES, **backend.FACTORS)}
    recipe_path = output / 'recipe.json'
    recipe_path.write_text(json.dumps(recipe))
    builder = backend.load_builder(ROOT)
    results = []
    for name, source in fixtures.items():
        colors, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        folder = output / name
        with backend.recipe_rules(builder, recipe['palette']):
            generated = paint_scrollbars(builder, recipe, colors, folder)
            for state in ('normal', 'endpoint', 'disabled', 'backdrop'):
                state_index = 2 if state == 'disabled' else 1 if state == 'backdrop' else 0
                effective = dict(colors)
                for roles in builder.art.ROLES.values(): effective[roles[0]] = colors[roles[state_index]]
                glyph_state = 'normal' if state == 'endpoint' else state
                verify_arrow_source_pixels(folder, glyph_state, builder, effective,
                                           recipe['geometry'])
                expected = {tuple(builder.art._rgb(builder.art.evaluate(builder.art.pixel_plan('button', token), effective)))
                            for token in ('face', 'light', 'dark', 'trough')}
                capture = folder / (state + '.png')
                # Reuse an explicitly supplied private X server. This avoids
                # nesting a fresh xvfb-run inside managed display sandboxes.
                display_wrapper = [] if os.environ.get('DISPLAY') else ['xvfb-run', '-a']
                command = display_wrapper + ['/usr/bin/python3', '-B',
                           str(ROOT / 'tools/theme-lab/tests/probe_gtk2_runtime.py'),
                           '--recipe', str(recipe_path), '--paint-rc', generated['rc'], '--capture', str(capture)]
                if state == 'endpoint': command += ['--value', '0']
                if state == 'disabled': command += ['--insensitive']
                if state == 'backdrop': command += ['--backdrop']
                environment = dict(os.environ, GTK_MODULES='', GTK2_RC_FILES='/dev/null', I167_PRIVATE_PROBE='1')
                child = subprocess.run(command, env=environment, text=True, capture_output=True, timeout=20)
                (folder / (state + '.stderr')).write_text(child.stderr)
                (folder / (state + '.json')).write_text(child.stdout)
                if child.returncode or child.stderr: raise RuntimeError(child.stderr or child.stdout)
                native = json.loads(child.stdout)
                image = Image.open(capture).convert('RGB')
                for widget in native['widgets']:
                    x, y, width, height = widget['allocation']
                    actual = set(image.crop((x, y, x + width, y + height)).getdata())
                    assert actual == expected, (name, state, widget['type'], actual, expected)
                face = builder.art._rgb(effective[builder.art.ROLES['button'][0]])
                deltas = verify_arrow_masks(folder, state, native, face, recipe)
                results.append({'scheme': name, 'state': state, 'terminal': child.returncode,
                                'palette_origin': origin, 'native': native,
                                'actual_colors_match_only_current_role_face_light_shadow': True,
                                'directional_glyph_pixel_deltas': deltas})
    report = {'status': 'passed', 'scope': 'GTK2 real engine full range palette and allocation; not pressed glyph fidelity or full adapter',
              'rows': results, 'host_profile_changed': False, 'historical_fidelity_claimed': False}
    (output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'status': report['status'], 'native_cases': len(results), 'output': str(output)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output: run(args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='gtk2-paint-') as directory: run(Path(directory))
