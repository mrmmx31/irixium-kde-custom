# SPDX-License-Identifier: GPL-3.0-or-later
"""Checkbox entry point; shared geometry/roles/RC live in gtk2_indicators."""
from gtk2_indicators import indicator_geometry as check_geometry, paint_indicator


def paint_check(builder, recipe, palette, destination):
    return paint_indicator(builder, recipe, palette, destination, 'check')


def selected_fragment(recipe, state):
    from gtk2_indicators import indicator_fragment
    return indicator_fragment(recipe,state,'check')
