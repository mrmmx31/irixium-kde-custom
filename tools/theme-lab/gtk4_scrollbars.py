# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK4 native scrollbar CSS and symbolic bevel assets.

The native GtkScrollbar has no arrow/stepper nodes in GTK4. This adapter keeps
its range and input behavior, styling only the continuous trough and slider.
"""
import hashlib
import json
from pathlib import Path

import gtk4_css


def geometry(recipe):
    values = recipe['geometry']
    keys = ('bar_px', 'shadow_px', 'thumb_cross_px')
    for key in keys:
        if type(values.get(key)) is not int or values[key] < 1:
            raise ValueError('GTK4 scrollbar: invalid geometry: ' + key)
    if values['bar_px'] != values['thumb_cross_px'] + 2 * values['shadow_px']:
        raise ValueError('GTK4 scrollbar: bar must contain thumb and two bevel bands')
    if values['shadow_px'] < 1 or values['thumb_cross_px'] <= 2 * values['shadow_px']:
        raise ValueError('GTK4 scrollbar: thumb must contain a visible interior')
    return values['bar_px'], values['shadow_px'], values['thumb_cross_px']


def identity(recipe, palette):
    payload = {'geometry': recipe['geometry'], 'palette': palette,
               'rules': recipe['palette'], 'native_nodes': ['scrollbar', 'range', 'trough', 'slider']}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _effective_palette(art, palette, state):
    result = dict(palette)
    index = {'normal': 0, 'pressed': 0, 'backdrop': 1, 'disabled': 2}[state]
    for family in ('button', 'button-fg'):
        for name in art.ROLES[family]:
            if name not in palette:
                raise ValueError('GTK4 scrollbar missing KDE role: ' + name)
            art._rgb(palette[name])
        result[art.ROLES[family][0]] = palette[art.ROLES[family][index]]
    return result


def write_scrollbar_css(builder, recipe, palette, destination):
    bar, shadow, thumb = geometry(recipe)
    art = builder.art
    stamp = identity(recipe, palette)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    generated = {}
    for state in ('normal', 'pressed', 'backdrop', 'disabled'):
        effective = _effective_palette(art, palette, state)
        generated[state] = {}
        for part, fill, down in (('trough', 'trough', True),
                                 ('thumb', 'face', state == 'pressed')):
            extent = bar if part == 'trough' else thumb
            pixels = art.bevel(art.blank(extent, extent, fill),
                               thickness=shadow, down=down)
            face = art.evaluate(art.pixel_plan('button', fill,
                                  inactive=state == 'backdrop',
                                  disabled=state == 'disabled'), effective)
            ink = art.evaluate(art.pixel_plan('button', 'ink',
                                 inactive=state == 'backdrop',
                                 disabled=state == 'disabled'), effective)
            slices = {name: builder.png(image, 'button', effective)
                      for name, image in art.slices(pixels, shadow).items() if name}
            generated[state][part] = {'face': face, 'ink': ink, 'slices': slices}

    root = 'scrollbar.theme-lab-gtk4-scrollbar-' + stamp
    assets = {}
    css = []
    for state in ('normal', 'pressed', 'backdrop', 'disabled'):
        for part in ('trough', 'thumb'):
            entry = generated[state][part]
            css.append(f'@define-color lab_scrollbar_{part}_{state}_{stamp} {entry["face"]};')
            css.append(f'@define-color lab_scrollbar_ink_{part}_{state}_{stamp} {entry["ink"]};')
            filenames = {}
            for name, data in entry['slices'].items():
                filename = f'scrollbar-{part}-{state}-{name}-{stamp}.png'
                path = destination / filename
                path.write_bytes(data)
                filenames[name] = path
            assets[state, part] = filenames

    # GTK dimensions are logical CSS pixels. The requested cross-axis size is
    # kept from the shared measured contract; adjustment/page size owns length.
    css += [
        f'{root} {{ margin: 0; padding: 0; border: 0; min-width: 0; min-height: 0; background-image: none; box-shadow: none; border-radius: 0; }}',
        f'{root}.vertical {{ min-width: {bar}px; }}',
        f'{root}.horizontal {{ min-height: {bar}px; }}',
        f'{root} > range {{ margin: 0; padding: 0; border: 0; min-width: 0; min-height: 0; background-image: none; box-shadow: none; }}',
        f'{root} > range > trough {{ margin: 0; padding: 0; border: 0; min-width: {bar}px; min-height: {bar}px; background-image: none; box-shadow: none; border-radius: 0; }}',
        f'{root}.vertical > range > trough {{ min-width: {bar}px; }}',
        f'{root}.horizontal > range > trough {{ min-height: {bar}px; }}',
        f'{root} > range > trough > slider {{ margin: 0; padding: 0; border: 0; min-width: {thumb}px; min-height: {thumb}px; background-image: none; box-shadow: none; border-radius: 0; }}',
        f'{root}.vertical > range > trough > slider {{ min-width: {thumb}px; min-height: 0; }}',
        f'{root}.horizontal > range > trough > slider {{ min-width: 0; min-height: {thumb}px; }}',
    ]

    def state_rules(selector, state, part):
        shadow_px = shadow
        slices = assets[state, part]
        urls = [slices[name].as_uri() for name in gtk4_css.NAMES] if shadow_px else []
        css.extend(gtk4_css.state(selector, '', shadow_px, urls,
                                  '@lab_scrollbar_' + part + '_' + state + '_' + stamp,
                                  '@lab_scrollbar_ink_' + part + '_' + state + '_' + stamp))

    for part, node in (('trough', '> range > trough'),
                       ('thumb', '> range > trough > slider')):
        selector = root + ' ' + node
        state_rules(selector, 'normal', part)
        state_rules(root + ':backdrop ' + node, 'backdrop', part)
        state_rules(root + ':disabled ' + node, 'disabled', part)
        if part == 'thumb':
            state_rules(root + ':not(:disabled) > range > trough > slider:active', 'pressed', part)
            state_rules(root + '.theme-lab-forced-pressed > range > trough > slider',
                        'pressed', part)

    path = destination / 'scrollbar.css'
    path.write_text('\n'.join(css) + '\n', encoding='utf-8')
    return {'css': str(path), 'style_class': root.rsplit('.', 1)[1],
            'assets': {f'{state}_{part}': sorted(paths) for (state, part), paths in assets.items()},
            'geometry': {'bar_cross_px': bar, 'shadow_px': shadow,
                         'thumb_cross_px': thumb, 'length': 'native adjustment/page size'},
            'states': ['normal', 'pressed', 'backdrop', 'disabled'],
            'native_nodes': ['scrollbar', 'range', 'trough', 'slider'],
            'arrows': 'not available in GTK4; no substitute drawn or bound',
            'final_colors_from_kde_roles': True,
            'scope': 'GTK4 GtkScrollbar trough and slider only'}


def selected_fragment(art, recipe, palette, state):
    if state not in ('normal', 'pressed', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK4 scrollbar state not translated: ' + state)
    bar, shadow, thumb = geometry(recipe)
    stamp = identity(recipe, palette)
    root = 'scrollbar.theme-lab-gtk4-scrollbar-' + stamp
    part = 'thumb' if state == 'pressed' else 'trough'
    selector = root + (' > range > trough > slider' if part == 'thumb' else ' > range > trough')
    pseudo = {'normal': '', 'hover': '', 'pressed': ':active',
              'backdrop': ':backdrop', 'disabled': ':disabled'}[state]
    css_state = 'normal' if state == 'hover' else state
    face_token = 'trough' if part == 'trough' else 'face'
    face = art.expression(art.pixel_plan('button', face_token,
                         inactive=css_state == 'backdrop',
                         disabled=css_state == 'disabled'))
    ink = art.expression(art.pixel_plan('button', 'ink',
                        inactive=css_state == 'backdrop',
                        disabled=css_state == 'disabled'))
    lines = ['/* GTK4 GtkScrollbar / ' + state + '. Native input and adjustment are preserved. */',
             '@import url("scrollbar.css");',
             f'{root}.vertical {{ min-width: {bar}px; }}',
             f'{root}.horizontal {{ min-height: {bar}px; }}',
             f'{root}.vertical > range > trough > slider {{ min-width: {thumb}px; min-height: 0; }}',
             f'{root}.horizontal > range > trough > slider {{ min-width: 0; min-height: {thumb}px; }}',
             selector + pseudo + ' {',
             '  background-color: ' + face + ';',
             '  color: ' + ink + ';',
             '  /* relief: ' + str(shadow) + 'px; thumb length follows GtkAdjustment */',
             '}']
    return '\n'.join(lines) + '\n'
