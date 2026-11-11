# SPDX-License-Identifier: GPL-3.0-or-later
"""GtkRange slider relief only; geometry and enclosing frame remain independent.

Default scrollbar has no focus. Disabled outranks interaction, pressed outranks
hover; backdrop supplies the palette context without suppressing interaction.
"""
FLAGS={
    'normal':':not(:active):not(:hover):not(:disabled)',
    'pressed':':active:not(:disabled)',
    'disabled':':disabled',
    'backdrop':':not(:active):not(:hover):not(:disabled)',
    'hover':':hover:not(:active):not(:disabled)',
}
CONTEXTS={
    'normal':((0,':not(:disabled):not(:backdrop)'),),
    'pressed':((0,':not(:disabled):not(:backdrop)'),(1,':not(:disabled):backdrop')),
    'disabled':((2,':disabled:not(:backdrop)'),(3,':disabled:backdrop')),
    'backdrop':((1,':not(:disabled):backdrop'),),
    'hover':((0,':not(:disabled):not(:backdrop)'),(1,':not(:disabled):backdrop')),
}


def masks(builder,recipe,result,border):
    base,family,_=result['gtk3-thumb-frame']
    extent=max(len(base),2*border+1)
    for state,relief in recipe.get('state_relief',{}).items():
        frame=builder.art.bevel(builder.art.blank(extent,extent,'face'),
                                thickness=border,down=relief=='sunken')
        if relief=='flat':frame=[['face' for token in row] for row in frame]
        result['gtk3-lab-thumb-'+state]=frame,family,border


def css(builder,recipe,manifest):
    result=''
    for state in recipe.get('scrollbar_parts',{}).get('thumb',{}).get('state_relief',{}):
        for palette_state,parent in CONTEXTS[state]:
            expression=builder.state_css('button',palette_state)
            properties=builder.adaptive_assets.expression('gtk3-lab-thumb-'+state,
                expression,prefix='adaptive/',manifest=manifest)
            result+=builder.rule('scrollbar'+parent+' slider'+FLAGS[state],properties)
    return result
