# SPDX-License-Identifier: GPL-3.0-or-later
"""GtkTextView in a native scrolling enclosure, using effective KDE roles."""
from pathlib import Path
import hashlib
import json
from gtk2_buttons import geometry
from gtk2_entries import snapshot_images


def geometry_lines(recipe):
    shadow, _, font = geometry(recipe)
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            '  font_name = "' + str(font) + 'px"']


def image_rule(state, filename, shadow):
    return ('    image { function = SHADOW detail = "scrolled_window" state = ' + state +
            ' file = "' + filename + '" border = { ' + ', '.join([str(shadow)] * 4) +
            ' } stretch = TRUE }')


def paint_text(builder, recipe, palette, destination):
    shadow, _, _ = geometry(recipe)
    art = builder.art
    roles = ('view', 'view-fg', 'selection', 'selection-fg')
    for role in roles:
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 text missing effective role: ' + name)
    # Reuse the symbolic sunken-field mask, not a screenshot or final colour.
    images = snapshot_images(builder, recipe, palette)
    inputs = {name: palette[name] for role in roles for name in art.ROLES[role]}
    style_id = hashlib.sha256(json.dumps([geometry_lines(recipe),
                                         sorted(inputs.items()),
                                         sorted(name for name, _ in images.values())],
                                        sort_keys=True).encode()).hexdigest()[:16]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in images.values():
        (destination / name).write_bytes(payload)
    lines = ['# Native GtkTextView; scrolling enclosure uses symbolic sunken mask.']
    for prefix, variant in (('themeLabText', 'normal'),
                            ('themeLabBackdropText', 'backdrop'),
                            ('themeLabInsensitiveText', 'disabled')):
        style = prefix + '-' + style_id
        lines += ['style "' + style + '" {'] + geometry_lines(recipe)
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if variant == 'disabled' or state == 'INSENSITIVE' else 1 if variant == 'backdrop' else 0
            for field in ('base', 'bg', 'text', 'fg'):
                selected = state == 'SELECTED'
                role = ('selection-fg' if selected else 'view-fg') if field in ('text', 'fg') else ('selection' if selected else 'view')
                rgb = art._rgb(palette[art.ROLES[role][index]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines.append('  engine "pixmap" {')
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            variant_image = 'disabled' if state == 'INSENSITIVE' else variant
            lines.append(image_rule(state, images[variant_image][0], shadow))
        lines += ['  }', '}']
        for suffix in ('Editor', 'Viewport'):
            lines.append('widget "*' + prefix + suffix + '_' + style_id + '" style : highest "' + style + '"')
    rc = destination / 'text.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': [name for name, _ in images.values()],
            'translated_control': 'text', 'style_id': style_id,
            'padding_scope': 'GTK2 RC cannot set GtkTextView instance margins; native GTK2 defaults are retained'}


def selected_fragment(recipe, state, builder, palette):
    if state not in ('normal', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 text: unsupported forced state: ' + state)
    shadow, _, _ = geometry(recipe)
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    images = snapshot_images(builder, recipe, palette)
    gtk_state = 'INSENSITIVE' if state == 'disabled' else 'PRELIGHT' if state == 'hover' else 'NORMAL'
    return '\n'.join(['# Selected native GtkTextView and scrolling enclosure.',
                      '# GTK2 theme RC does not set GtkTextView instance margins; native defaults are retained.',
                      'style "theme-lab-gtk2-text-fragment" {'] + geometry_lines(recipe) +
                     ['  engine "pixmap" {', image_rule(gtk_state, images[variant][0], shadow),
                      '  }', '}', '# Palette/text bindings supplied by private generated RC.', ''])
