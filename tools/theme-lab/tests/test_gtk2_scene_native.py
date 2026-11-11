#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 layout and XEmbed, both native origins in four KDE palettes."""
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
from scene_contract import scene


def run(fixtures, output):
    output.mkdir(parents=True, exist_ok=True)
    recipe = json.loads((fixtures / 'recipe.json').read_text())
    recipe.update(visible_controls=(1 << 10) | (1 << 11), selected_control=10,
                  positions=[[16, 16] for _ in range(16)], sizes=[[0, 0] for _ in range(16)])
    recipe['positions'][10], recipe['positions'][11] = [41, 57], [311, 103]
    recipe['sizes'][10], recipe['sizes'][11] = [240, 15], [15, 270]
    model = {'recipes': {'gtk2': recipe}, 'color_scheme': ''}
    original = copy.deepcopy(model)
    assert [item['id'] for item in scene(model, 'gtk2')] == ['scroll_h', 'scroll_v']
    sources = {'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
               'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
               'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
               'TestYellow': fixtures / 'TestYellow.colors'}
    results = []
    for scheme, source in sources.items():
        folder = output / scheme
        folder.mkdir(exist_ok=True)
        receipt = generate_scrollbar_snapshot(backend, ROOT, folder, model, source)
        for state in (0, 2, 3):
            for embedded in (False, True):
                proposal = copy.deepcopy(model)
                proposal['recipes']['gtk2']['edit_state'] = state
                target = folder / ('state%d-%s' % (state, 'coupled' if embedded else 'separate'))
                target.mkdir(exist_ok=True)
                project = target / 'PROJECT.json'
                project.write_text(json.dumps(proposal))
                command = ['xvfb-run', '-a', '/usr/bin/python3', '-B',
                           str(ROOT / 'tools/theme-lab/tests/probe_gtk2_scene.py'),
                           '--project', str(project), '--rc', receipt['rc'], '--output', str(target)]
                if embedded: command.append('--embedded')
                child = subprocess.run(command, env=dict(os.environ, GTK_MODULES='', GTK2_RC_FILES='/dev/null',
                                       I167_PRIVATE_PROBE='1'), text=True, capture_output=True, timeout=25)
                (target / 'stderr.log').write_text(child.stderr)
                (target / 'native.json').write_text(child.stdout)
                if child.returncode or child.stderr: raise RuntimeError(child.stderr or child.stdout)
                native = json.loads(child.stdout)
                horizontal = native['metrics'][0]
                assert horizontal['sensitive'] == (state != 2)
                if state == 3: assert horizontal['widget_name'] == 'themeLabBackdropScroll'
                results.append({'scheme': scheme, 'editor_state': state, 'native': native})
    assert model == original
    (output / 'results.json').write_text(json.dumps({'status': 'passed', 'scenes': results,
        'model_unchanged': True, 'full_lab_scene_integration_claimed': False}, indent=2))
    print(json.dumps({'status': 'passed', 'native_scenes': len(results), 'native_widgets_measured': 2 * len(results)}))


def verify_saved(output):
    """Verify the already captured native scenes, without sending more input."""
    report = json.loads((output / 'results.json').read_text())
    builder = backend.load_builder(ROOT)
    masks = []
    for row in report['scenes']:
        folder = output / row['scheme']
        native = row['native']
        target = folder / ('state%d-%s' % (row['editor_state'], 'coupled' if native['embedded'] else 'separate'))
        model = json.loads((target / 'PROJECT.json').read_text())
        recipe = model['recipes']['gtk2']
        colors = json.loads((folder / 'GTK2-NATIVE-COLORS.json').read_text())['colors']
        with backend.recipe_rules(builder, recipe['palette']):
            for item in native['metrics']:
                state = ('disabled' if row['editor_state'] == 2 else 'backdrop' if row['editor_state'] == 3 else 'normal') if item['index'] == 10 else 'normal'
                index = 2 if state == 'disabled' else 1 if state == 'backdrop' else 0
                face = builder.art._rgb(colors[builder.art.ROLES['button'][index]])
                widget = {'type': 'GtkHScrollbar' if item['index'] == 10 else 'GtkVScrollbar',
                          'allocation': item['allocation']}
                deltas = verify_arrow_masks(folder / 'gtk2-scrollbars', state,
                         {'widgets': [widget]}, face, recipe, capture=target / 'native.png')
                # Full 15px stepper cells add three native pixels at each end
                # relative to the former 12px arrow-only allocation.
                assert item['native_request_before_custom_size'] == ([55, 15] if item['index'] == 10 else [15, 55])
                masks.append({'scheme': row['scheme'], 'origin': item['origin'],
                              'state': state, 'control': item['id'], 'mask_deltas': deltas})
    (output / 'masks.json').write_text(json.dumps({'status': 'passed', 'masks': masks,
         'native_capture_reused': True, 'scope': 'Scrollbar scene arrow masks only'}, indent=2))
    print(json.dumps({'status': 'passed', 'scene_arrow_masks': sum(len(row['mask_deltas']) for row in masks)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if not args.verify_only:
        if not args.fixtures: parser.error('--fixtures required for native run')
        run(args.fixtures.resolve(), args.output.resolve())
    verify_saved(args.output.resolve())
