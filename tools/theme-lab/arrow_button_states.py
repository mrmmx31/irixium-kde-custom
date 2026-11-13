# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone GtkButton relief contract; never applies to GtkRange steppers.

Disabled overrides interaction. Pressed overrides hover/focus; hover overrides
focus. Backdrop changes palette context and has its own idle relief. An absent
override retains native border drawing. Geometry and glyph remain independent.
"""
FLAGS = {
    'normal': ':not(:active):not(:hover):not(:focus):not(:disabled)',
    'pressed': ':active:not(:disabled)',
    'disabled': ':disabled',
    'backdrop': ':not(:active):not(:hover):not(:focus):not(:disabled)',
    'hover': ':hover:not(:active):not(:disabled)',
    'focus': ':focus:not(:hover):not(:active):not(:disabled)',
}
CONTEXTS = {
    'normal': ((0, ':not(:backdrop)'),),
    'pressed': ((0, ':not(:backdrop)'), (1, ':backdrop')),
    'disabled': ((2, ':not(:backdrop)'), (3, ':backdrop')),
    'backdrop': ((1, ':backdrop'),),
    'hover': ((0, ':not(:backdrop)'), (1, ':backdrop')),
    'focus': ((0, ':not(:backdrop)'), (1, ':backdrop')),
}

def css(builder, recipe):
    result = ''
    overrides = recipe.get('scrollbar_parts', {}).get('arrow_button', {}).get('state_relief', {})
    for state, relief in overrides.items():
        for palette_state, context in CONTEXTS[state]:
            expression = builder.state_css('button', palette_state)
            face, light, shade = (expression(token) for token in ('face', 'light', 'dark'))
            edges = ((face,) * 4 if relief == 'flat' else
                     (light, shade, shade, light) if relief == 'raised' else
                     (shade, light, light, shade))
            result += builder.rule('button.theme-lab-arrow' + context + FLAGS[state], {
                'border-color': ' '.join(edges),
            })
    return result
