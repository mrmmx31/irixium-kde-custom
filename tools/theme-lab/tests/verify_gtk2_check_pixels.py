# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify saved native CHECK pixels without replaying input."""
import io
import json
from pathlib import Path
import sys
from PIL import Image
from test_backend import backend, ROOT


def verify(folder):
    folder = Path(folder); builder = backend.load_builder(ROOT); rows = []
    for directory in sorted(p for p in folder.iterdir() if p.is_dir()):
        recipe = json.loads((directory / 'recipe.json').read_text())
        native = json.loads((directory / 'native.json').read_text())
        colors = json.loads((directory / 'colors.json').read_text())['colors']
        x, y, width, height = native['allocation']; props = native['style_properties']
        size = props['indicator-size']
        ix = x + props['indicator-spacing'] + native['border_width']
        if not props['interior-focus']: ix += props['focus-line-width'] + props['focus-padding']
        iy = y + (height - size) // 2
        selected_states = ('selected-hover', 'selected', 'disabled-selected', 'selected-pressed', 'backdrop-selected')
        for state in ('normal','hover','pressed','selected-hover','selected','disabled-selected',
                      'disabled','selected-pressed','released','backdrop','backdrop-selected'):
            index = 2 if state.startswith('disabled') else 1 if state.startswith('backdrop') else 0
            effective = dict(colors)
            for names in builder.art.ROLES.values(): effective[names[0]] = colors[names[index]]
            screenshot = Image.open(directory / (state + '.png')).convert('RGB')
            # Parent remains enabled/active in this fixture; explicit backdrop
            # selects the child's style, not the native window's focus state.
            canvas = builder.art._rgb(colors[builder.art.ROLES['window'][0]])
            assert all(screenshot.getpixel((cx,cy)) == canvas
                       for cx in range(5,13) for cy in range(5,13))
            actual = screenshot.crop((ix, iy, ix + size, iy + size))
            selected = state in selected_states
            with backend.recipe_rules(builder, recipe['palette']):
                pixels = builder.art.bevel(builder.art.blank(size,size,'trough' if selected else 'face'),
                                          thickness=recipe['geometry']['shadow_px'], down=selected)
                expected = Image.open(io.BytesIO(builder.png(pixels,'button',effective))).convert('RGB')
            delta = sum(a != b for a,b in zip(actual.getdata(),expected.getdata()))
            assert delta == 0, (directory.name, state, delta)
            fg = builder.art._rgb(effective[builder.art.ROLES['window-fg'][0]])
            glyphs = sum(p == fg for p in screenshot.crop((ix+size+1,y+5,x+width-5,y+height-5)).getdata())
            assert glyphs > 0, (directory.name,state,'window foreground not found')
            rows.append({'palette':directory.name,'state':state,'indicator_pixels':size*size,
                         'indicator_differences':delta,'text_role_pixels':glyphs,
                         'parent_canvas_role_pixels':64})
        assert list(Image.open(directory/'normal.png').getdata()) == list(Image.open(directory/'released.png').getdata())
    result = {'status':'passed_scoped_pixels','rows':rows,'focus_excluded':True,'historical_fidelity_claimed':False}
    (folder/'verified-pixels.json').write_text(json.dumps(result,indent=2))
    return result


if __name__ == '__main__':
    r=verify(sys.argv[1]);print(json.dumps({'status':r['status'],'captures':len(r['rows']),
        'indicator_pixels':sum(x['indicator_pixels'] for x in r['rows'])}))
