# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK4 CheckButton assets and CSS derived from the shared KDE role recipe."""
from pathlib import Path
from gtk2_indicators import indicator_geometry, indicator_pixels
from gtk4_buttons import identity


def write_check_css(builder, recipe, palette, destination):
    glyph, shadow, spacing, font = indicator_geometry(recipe)
    art = builder.art
    for role in ('button', 'button-fg', 'window', 'window-fg'):
        for key in art.ROLES[role]:
            if key not in palette:
                raise ValueError('GTK4 check missing effective KDE role: ' + key)
            art._rgb(palette[key])
    stamp = identity(recipe, palette)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    files = {}
    for variant, index in (('normal', 0), ('backdrop', 1), ('disabled', 2)):
        effective = dict(palette)
        for names in art.ROLES.values():
            if names[index] in palette:
                effective[names[0]] = palette[names[index]]
        for selected in (False, True):
            pixels = indicator_pixels(art, glyph, shadow, selected, 'check')
            filename = f'check-{variant}-{"checked" if selected else "unchecked"}-{stamp}.png'
            path = destination / filename
            path.write_bytes(builder.png(pixels, 'button', effective))
            files[variant, selected] = path

    selector = 'checkbutton.theme-lab-gtk4-check-' + stamp
    lines = [
        selector + ' { background-image: none; background-color: transparent;',
        '  border: none; border-radius: 0; box-shadow: none; padding: 0;',
        f'  color: {art.expression(art.pixel_plan("window", "ink"))}; font-size: {font}px;',
        '}',
    ]
    for variant, pseudo in (('normal', ''), ('backdrop', ':backdrop'), ('disabled', ':disabled')):
        # Use the exact window foreground role for each root state.
        fg = art.expression(art.pixel_plan('window', 'ink',
                    inactive=variant == 'backdrop', disabled=variant == 'disabled'))
        lines += [selector + pseudo + ' { color: ' + fg + '; }']
        child = selector + pseudo + ' check'
        lines += [child + ' {', f'  min-width: {glyph}px; min-height: {glyph}px;',
                  '  padding: 0; border: none; border-radius: 0;',
                  f'  margin: 0 {spacing}px 0 0;',
                  '  background-color: transparent; box-shadow: none;',
                  '  background-position: center; background-repeat: no-repeat;',
                  f'  background-size: {glyph}px {glyph}px;',
                  '  background-image: url("' + files[variant, False].as_uri() + '");', '}']
        lines += [child + ':checked {',
                  '  background-image: url("' + files[variant, True].as_uri() + '");', '}']
    lines += [selector + ':dir(rtl) check { margin: 0 0 0 ' + str(spacing) + 'px; }']
    css = destination / 'check.css'
    css.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'css': str(css), 'style_class': 'theme-lab-gtk4-check-' + stamp,
            'glyph_px': glyph, 'indicator_spacing_px': spacing,
            'selected_values': {'false': str(files['normal', False]),
                                'true': str(files['normal', True])},
            'palette_source': 'KDE role aliases; no final static colors',
            'translated_control': 'check',
            'scope': 'Private native GtkCheckButton indicator and input; no historical approval'}


def selected_fragment(builder, recipe, palette, state):
    if state not in ('normal', 'pressed', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK4 check state not translated: ' + state)
    stamp = identity(recipe, palette)
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    selector = 'checkbutton.theme-lab-gtk4-check-' + stamp
    pseudo = {'normal': '', 'pressed': ':active', 'disabled': ':disabled',
              'backdrop': ':backdrop', 'hover': ':hover'}[state]
    geometry_text = ('/* GTK4 GtkCheckButton / ' + state +
        '. Native checkbutton remains interactive; KDE role colors are in check.css. */\n')
    css = ['@import url("check.css");',
           selector + pseudo + ' check {',
           '  background-image: url("check-' + variant + '-unchecked-' + stamp + '.png");', '}',
           selector + pseudo + ' check:checked {',
           '  background-image: url("check-' + variant + '-checked-' + stamp + '.png");', '}']
    return geometry_text + '\n'.join(css) + '\n'
