#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private generation provenance and compatibility with verified GTK2 masks."""
import argparse
import copy
import json
from pathlib import Path
import sys
from unittest.mock import patch
from test_gtk2_paint_native import ROOT
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend
from gtk2_generation import generate_scrollbar_snapshot


def run(fixtures, output):
    output.mkdir(parents=True, exist_ok=True)
    recipe = json.loads((fixtures / 'recipe.json').read_text())
    model = {'recipes': {'gtk2': recipe}, 'color_scheme': ''}
    original = copy.deepcopy(model)
    sources = {'DomainOS': ROOT / 'colors/DomainOS-SR10.4.colors',
               'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
               'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors'),
               'TestYellow': fixtures / 'TestYellow.colors'}
    rows = []
    for scheme, source in sources.items():
        folder = output / scheme
        folder.mkdir(exist_ok=True)
        receipt = generate_scrollbar_snapshot(backend, ROOT, folder, model, source)
        assert receipt['status'] == 'partially_generated'
        assert not receipt['recipe_applied'] and not receipt['scene_integrated']
        assert not receipt['host_changed'] and not receipt['picked_used']
        assert backend.palette_inputs_current(receipt)
        assert receipt['selected_scheme']['path'] == str(source)
        matches = []
        for name in receipt['assets']:
            candidate = folder / 'gtk2-scrollbars' / name
            verified = fixtures / scheme / name
            assert candidate.read_bytes() == verified.read_bytes(), (scheme, name)
            matches.append(name)
        rows.append({'scheme': scheme, 'identical_verified_assets': matches,
                     'provenance_current': True, 'receipt': receipt})
    assert model == original
    bad = copy.deepcopy(model)
    bad['recipes']['gtk2']['scrollbar_parts'] = {'fitting': {'gap_px': 8}}
    before = copy.deepcopy(bad)
    rejected = output / 'unsupported'
    rejected.mkdir(exist_ok=True)
    try:
        generate_scrollbar_snapshot(backend, ROOT, rejected, bad, sources['DomainOS'])
    except ValueError as error:
        assert 'pending' in str(error)
    else:
        raise AssertionError('Unsupported fitting silently accepted')
    assert bad == before
    assert not (rejected / 'GTK2-SCROLLBAR-PROPOSAL.json').exists()
    complete_geometry = dict(recipe['geometry'], view_bar_gap_px=4, view_inset_px=2,
                             control_padding_px=4, font_px=13)
    full_model = {'selected_family': 'gtk2', 'color_scheme': '',
                  'recipes': {family: dict(copy.deepcopy(recipe), geometry=complete_geometry.copy())
                              for family in backend.FAMILIES}}
    capability_fixture = {'families': {family: {'available': family == 'gtk2'}
                                      for family in backend.FAMILIES}}
    with patch.object(backend, 'probe', return_value=capability_fixture):
        pipeline = backend.generate(ROOT, output / 'pipeline', full_model, 'fixture', sources['DomainOS'])
    assert pipeline['status'] == 'partially_generated'
    assert pipeline['families']['gtk2']['translated_controls'] == ['push', 'toggle', 'scroll_h', 'scroll_v']
    assert not pipeline['families']['gtk2']['recipe_applied']
    report = {'status': 'passed', 'rows': rows, 'unsupported_recipe_preserved': True,
              'scene_not_claimed': True, 'model_unchanged': True,
              'generation_dispatch_verified_with_isolated_capability_fixture': True}
    (output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'status': 'passed', 'schemes': len(rows),
                      'verified_png_matches': sum(len(row['identical_verified_assets']) for row in rows)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.fixtures.resolve(), args.output.resolve())
