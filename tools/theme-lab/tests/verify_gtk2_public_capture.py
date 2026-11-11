# SPDX-License-Identifier: GPL-3.0-or-later
"""Check saved public-route GTK2 pixels against that generation's own roles."""
import json
from pathlib import Path
from PIL import Image
from test_gtk2_paint_native import verify_arrow_masks, ROOT
import sys
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend


def verify(output):
    output = Path(output)
    folder = next((output / 'home/out/revisions').iterdir())
    project = json.loads((folder / 'PROJECT.json').read_text())
    recipe = project['recipes']['gtk2']
    colors = json.loads((folder / 'GTK2-NATIVE-COLORS.json').read_text())['colors']
    events = [json.loads(p.read_text()) for p in (folder / 'gtk2-preview-events').glob('event-*.json')]
    # Moving the thumb may publish a second geometry event. Compare the
    # latest measurement per control, never assume exactly one emission.
    metrics_events = [r for r in events if r.get('action') == 'metrics']
    latest = {r['control_index']: r for r in sorted(metrics_events, key=lambda r: r['emitted_at'])}
    metrics = list(latest.values())
    assert len(metrics) == 2
    native = {'widgets': [{'type': 'GtkHScrollbar' if r['control_index'] == 10 else 'GtkVScrollbar',
                           'allocation': [r['position_x'], r['position_y'], r['width'], r['height']]}
                          for r in metrics]}
    builder = backend.load_builder(ROOT)
    with backend.recipe_rules(builder, recipe['palette']):
        face = builder.art._rgb(colors[builder.art.ROLES['button'][0]])
        deltas = verify_arrow_masks(folder / 'gtk2-scrollbars', 'normal', native, face,
                                   recipe, capture=output / 'preview.png')
        tokens = {builder.art._rgb(builder.art.evaluate(builder.art.pixel_plan('button', token), colors))
                  for token in ('face', 'light', 'dark', 'trough')}
    image = Image.open(output / 'preview.png').convert('RGB')
    for widget in native['widgets']:
        x, y, w, h = widget['allocation']
        assert set(image.crop((x, y, x + w, y + h)).getdata()) == tokens
    canvas = builder.art._rgb(colors[builder.art.ROLES['window'][0]])
    assert all(image.getpixel((x, y)) == canvas for x in range(300, 308) for y in range(300, 308))
    result = {'arrow_pixel_differences': deltas, 'bar_role_colors_match': True,
              'canvas_role_pixels_match': 64, 'native_metrics': metrics}
    (output / 'verified-pixels.json').write_text(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1])))
