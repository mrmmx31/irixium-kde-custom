# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK4 scrollbar capability contract; creates no arrow substitute."""
import json

STEPPER_PROPERTIES = (
    'has-backward-stepper', 'has-forward-stepper',
    'has-secondary-backward-stepper', 'has-secondary-forward-stepper',
)


def contract(control, recipe):
    if control not in ('scroll_h', 'scroll_v'):
        raise ValueError('GTK4 scrollbar contract requires scroll_h or scroll_v')
    return {
        'family': 'gtk4', 'control': control, 'native_widget': 'GtkScrollbar',
        'native_css_nodes': ['scrollbar', 'range', 'trough', 'slider'],
        'native_stepper_properties': list(STEPPER_PROPERTIES),
        'native_stepper_properties_available': False,
        'reference_arrow_button': 'not_available_in_GTK4_GtkScrollbar',
        'reference_arrow_glyph': 'not_available_in_GTK4_GtkScrollbar',
        'policy': ('Keep the GTK4 native scrollbar and its native input. Do not '
                   'draw arrow buttons or bind substitute arrow interactions '
                   'without a separate user-approved design decision.'),
        'geometry_reference': dict(recipe['geometry']),
        'geometry_applied': False, 'palette_roles_applied': False,
        'status': 'capability_contract_only',
    }


def selected_contract(control, recipe):
    return json.dumps(contract(control, recipe), ensure_ascii=False, indent=2) + '\n'
