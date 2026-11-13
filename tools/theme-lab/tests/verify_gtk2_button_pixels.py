# SPDX-License-Identifier: GPL-3.0-or-later
"""Inspect existing GTK2 button captures; no replay or personal GUI input."""
import io
import json
from pathlib import Path
import sys
from PIL import Image
from test_backend import backend, ROOT, model
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
from gtk2_buttons import role_source


def verify(folder):
    folder = Path(folder)
    builder = backend.load_builder(ROOT)
    rows = []
    for directory in sorted(p for p in folder.iterdir() if p.is_dir()):
        recipe_file = directory / 'recipe.json'
        recipe = json.loads(recipe_file.read_text()) if recipe_file.exists() else model()['recipes']['gtk2']
        native = json.loads((directory / 'native.json').read_text())
        colors = json.loads((directory / 'colors.json').read_text())['colors']
        x, y, width, height = native['allocation']
        for state in ('normal', 'hover', 'pressed', 'released', 'disabled', 'backdrop'):
            effective = dict(colors)
            index = 2 if state == 'disabled' else 1 if state == 'backdrop' else 0
            for names in builder.art.ROLES.values():
                effective[names[0]] = colors[names[index]]
            family, foreground_family, _ = role_source(
                'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal')
            actual = Image.open(directory / (state + '.png')).convert('RGB').crop((x, y, x + width, y + height))
            shadow = recipe['geometry']['shadow_px']
            with backend.recipe_rules(builder, recipe['palette']):
                pixels = builder.art.bevel(builder.art.blank(width, height, 'face'),
                                          thickness=shadow, down=state == 'pressed')
                expected = Image.open(io.BytesIO(builder.png(pixels, family, effective))).convert('RGB')
                foreground = builder.art._rgb(effective[builder.art.ROLES[foreground_family][0]])
            edges = [(bx, by) for by in range(height) for bx in range(width)
                     if bx < shadow or by < shadow or bx >= width - shadow or by >= height - shadow]
            delta = sum(actual.getpixel(p) != expected.getpixel(p) for p in edges)
            assert delta == 0, (directory.name, state, delta)
            assert all(actual.getpixel((bx, by)) == expected.getpixel((bx, by))
                       for bx in range(shadow + 2, shadow + 8) for by in range(shadow + 2, shadow + 8))
            glyph_pixels = sum(pixel == foreground for pixel in actual.crop((10, 10, width-10, height-10)).getdata())
            assert glyph_pixels > 0, (directory.name, state, 'foreground role not found')
            rows.append({'palette': directory.name, 'state': state, 'edge_pixels': len(edges),
                         'edge_differences': delta, 'face_pixels_match': 36, 'glyph_role_pixels': glyph_pixels})
        normal = Image.open(directory / 'normal.png'); released = Image.open(directory / 'released.png')
        assert list(normal.getdata()) == list(released.getdata()), directory.name
    result = {'status': 'passed_scoped_pixels', 'rows': rows, 'focus_excluded': True,
              'historical_fidelity_claimed': False}
    (folder / 'verified-pixels.json').write_text(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    result = verify(sys.argv[1])
    print(json.dumps({'status': result['status'], 'captures': len(result['rows']),
                      'edge_pixels': sum(r['edge_pixels'] for r in result['rows']),
                      'face_pixels': sum(r['face_pixels_match'] for r in result['rows'])}))
