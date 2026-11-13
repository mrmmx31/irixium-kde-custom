# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GtkTreeView list and enclosure, with effective KDE role snapshots.

The enclosure alone paints a sunken border. Cells keep native flat selection;
no engine shadow rule is attached to the TreeView itself.
"""
import hashlib
import json
from pathlib import Path
from gtk2_buttons import geometry
from gtk2_entries import snapshot_images
from gtk2_text import image_rule


def geometry_lines(recipe):
    shadow, _, font = geometry(recipe)
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            # XmList's ordinary single-column rows have no extra inter-item
            # gutter. Do not reuse the generic button/input padding here.
            '  GtkTreeView::horizontal-separator = 0',
            '  GtkTreeView::vertical-separator = 0',
            '  font_name = "' + str(font) + 'px"']


def paint_list(builder, recipe, palette, destination):
    shadow, _, _ = geometry(recipe)
    art = builder.art
    roles = ('view', 'view-fg', 'selection', 'selection-fg')
    for role in roles:
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 list missing effective role: ' + name)
    images = snapshot_images(builder, recipe, palette)
    inputs = {name: palette[name] for role in roles for name in art.ROLES[role]}
    identity = hashlib.sha256(json.dumps([geometry_lines(recipe), sorted(inputs.items()),
                    sorted(name for name, _ in images.values())], sort_keys=True).encode()).hexdigest()[:16]
    lines = ['# GtkTreeView cells remain flat; sunken shadow belongs to enclosure.']
    for prefix, variant in (('themeLabList', 'normal'),
                            ('themeLabBackdropList', 'backdrop'),
                            ('themeLabInsensitiveList', 'disabled')):
        style = prefix + '-' + identity
        lines += ['style "' + style + '" {'] + geometry_lines(recipe)
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if variant == 'disabled' or state == 'INSENSITIVE' else 1 if variant == 'backdrop' else 0
            for field in ('base', 'bg', 'text', 'fg'):
                # GtkTreeView uses ACTIVE for selected rows without keyboard focus.
                selected = state in ('SELECTED', 'ACTIVE')
                role = ('selection-fg' if selected else 'view-fg') if field in ('text', 'fg') else ('selection' if selected else 'view')
                rgb = art._rgb(palette[art.ROLES[role][index]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines += ['}', 'widget "*' + prefix + 'View_' + identity + '" style : highest "' + style + '"',
                  'style "' + style + '-enclosure" = "' + style + '" {', '  engine "pixmap" {']
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            image = images['disabled' if state == 'INSENSITIVE' else variant][0]
            lines.append(image_rule(state, image, shadow))
        lines += ['  }', '}', 'widget "*' + prefix + 'Enclosure_' + identity + '" style : highest "' + style + '-enclosure"']
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in images.values():
        (destination / name).write_bytes(payload)
    rc = destination / 'list.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': [name for name, _ in images.values()],
            'translated_control': 'list', 'style_id': identity,
            'padding_scope': 'GtkTreeView cell separators; not outer scrollbar spacing'}


def selected_fragment(recipe, state, builder, palette):
    if state not in ('normal', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 list: unsupported forced state: ' + state)
    shadow, _, _ = geometry(recipe)
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    image = snapshot_images(builder, recipe, palette)[variant][0]
    native_state = 'INSENSITIVE' if state == 'disabled' else 'PRELIGHT' if state == 'hover' else 'NORMAL'
    return '\n'.join(['# List cell geometry; flat native selection uses KDE roles.',
                     'style "theme-lab-gtk2-list-fragment" {'] + geometry_lines(recipe) +
                     ['}', '# Only the scrolling enclosure receives the sunken mask.',
                      'style "theme-lab-gtk2-list-enclosure-fragment" {', '  engine "pixmap" {',
                      image_rule(native_state, image, shadow), '  }', '}', ''])
