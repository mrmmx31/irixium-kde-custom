# SPDX-License-Identifier: GPL-3.0-or-later
"""GtkViewport content enclosure relief, independent of its interactive child."""
CONTEXTS={
    'normal':((0,':not(:disabled):not(:backdrop)'),),
    'disabled':((2,':disabled:not(:backdrop)'),(3,':disabled:backdrop')),
    'backdrop':((1,':not(:disabled):backdrop'),),
}


def masks(builder,recipe,result,border):
    base,family,_=result['gtk3-lab-view-frame']
    extent=max(len(base),2*border+1)
    for state,relief in recipe.get('state_relief',{}).items():
        frame=builder.art.bevel(builder.art.blank(extent,extent,'face'),
                                thickness=border,down=relief=='sunken')
        if relief=='flat':frame=[['face' for token in row] for row in frame]
        result['gtk3-lab-fitting-'+state]=frame,family,border


def css(builder,recipe,manifest):
    result=''
    for state in recipe.get('scrollbar_parts',{}).get('fitting',{}).get('state_relief',{}):
        for palette_state,suffix in CONTEXTS[state]:
            expression=builder.state_css('view',palette_state)
            properties=builder.adaptive_assets.expression('gtk3-lab-fitting-'+state,
                expression,prefix='adaptive/',manifest=manifest)
            result+=builder.rule('scrolledwindow > viewport'+suffix,properties)
    return result
