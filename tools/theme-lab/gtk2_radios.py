# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 OPTION indicator proposal; native grouping belongs to GtkRadioButton.

Diamond silhouette extends the shared Motif-inspired art by recipe dimensions;
this does not establish historical SR10.4 indicator dimensions or behavior.
"""
from gtk2_indicators import paint_indicator, indicator_pixels, indicator_geometry


def paint_radio(builder, recipe, palette, destination):
    return paint_indicator(builder, recipe, palette, destination, 'radio')


def selected_fragment(recipe, state):
    from gtk2_indicators import indicator_fragment
    return indicator_fragment(recipe,state,'radio')
