# SPDX-License-Identifier: GPL-3.0-or-later
"""Private native GtkProgressBar recipe, effective KDE roles only."""
from pathlib import Path
import hashlib
import json
from gtk2_buttons import geometry


def geometry_lines(recipe):
    shadow, _, font = geometry(recipe)
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            '  font_name = "' + str(font) + 'px"']


def image_rule(state, detail, filename, shadow):
    return ('    image { function = BOX detail = "' + detail + '" state = ' + state +
            ' file = "' + filename + '" border = { ' + ', '.join([str(shadow)] * 4) +
            ' } stretch = TRUE }')


def paint_progress(builder, recipe, palette, destination):
    shadow, _, _ = geometry(recipe)
    art = builder.art
    for role in ('view', 'view-fg', 'selection', 'selection-fg'):
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 progress missing effective role: ' + name)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    images = snapshot_images(builder, recipe, palette)
    assets = []
    for name, payload in images.values():
        (destination / name).write_bytes(payload)
        assets.append(name)
    role_inputs = {name: palette[name] for role in ('view','view-fg','selection','selection-fg') for name in art.ROLES[role]}
    style_id = hashlib.sha256(json.dumps([sorted(assets), geometry_lines(recipe), role_inputs], sort_keys=True).encode()).hexdigest()[:16]
    lines = ['# Native GtkProgressBar; private KDE role snapshot, no historical metric claim.']
    for name, backdrop in (('theme-lab-gtk2-progress', 0),
                            ('theme-lab-gtk2-progress-backdrop', 1),
                            ('theme-lab-gtk2-progress-disabled', 2)):
        lines += ['style "' + name + '-' + style_id + '" {'] + geometry_lines(recipe)
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if state == 'INSENSITIVE' else backdrop
            for field, role in (('bg', 'view'), ('fg', 'view-fg'),
                                 ('base', 'selection'), ('text', 'selection-fg')):
                rgb = art._rgb(palette[art.ROLES[role][index]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines.append('  engine "pixmap" {')
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            variant = 'disabled' if state == 'INSENSITIVE' or backdrop == 2 else 'backdrop' if backdrop == 1 else 'normal'
            for detail in ('trough', 'bar'):
                lines.append(image_rule(state, detail, images[variant, detail][0], shadow))
        lines += ['  }', '}']
    for widget, style in (('themeLabProgress', 'theme-lab-gtk2-progress'),
                          ('themeLabBackdropProgress', 'theme-lab-gtk2-progress-backdrop'),
                          ('themeLabInsensitiveProgress', 'theme-lab-gtk2-progress-disabled')):
        lines.append('widget "*' + widget + '_' + style_id + '" style : highest "' + style + '-' + style_id + '"')
    for widget, variant in (('themeLabProgressValue', 0),
                            ('themeLabBackdropProgressValue', 1),
                            ('themeLabInsensitiveProgressValue', 2)):
        style = widget + '-' + style_id
        foreground = art._rgb(palette[art.ROLES['view-fg'][variant]])
        lines += ['style "' + style + '" {',
                  '  fg[NORMAL] = "#%02x%02x%02x"' % foreground,
                  '  fg[INSENSITIVE] = "#%02x%02x%02x"' % foreground,
                  '  font_name = "' + str(geometry(recipe)[2]) + 'px"',
                  '}',
                  'widget "*' + widget + '_' + style_id + '" style : highest "' + style + '"']
    rc = destination / 'progress.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': assets, 'translated_control': 'progress', 'style_id': style_id}


def snapshot_images(builder, recipe, palette):
    """Content-address images so a reused GTK2 engine cannot retain old pixels."""
    shadow, _, _ = geometry(recipe)
    art = builder.art
    images = {}
    for variant, index in (('normal', 0), ('disabled', 2), ('backdrop', 1)):
        effective = dict(palette)
        for names in art.ROLES.values():
            if names[index] in palette: effective[names[0]] = palette[names[index]]
        for detail, role in (('trough', 'view'), ('bar', 'selection')):
            pixels = art.bevel(art.blank(2 * shadow + 1, 2 * shadow + 1, 'face'),
                               thickness=shadow, down=detail == 'trough')
            payload = builder.png(pixels, role, effective)
            name = 'progress-' + variant + '-' + detail + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png'
            images[variant, detail] = name, payload
    return images


def selected_fragment(recipe, state, builder, palette):
    if state not in ('normal', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 progress: unsupported forced state: ' + state)
    shadow, _, _ = geometry(recipe)
    gtk_state = 'INSENSITIVE' if state == 'disabled' else 'PRELIGHT' if state == 'hover' else 'NORMAL'
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    images = snapshot_images(builder, recipe, palette)
    return '\n'.join(['# Selected GtkProgressBar; effective palette supplied by generated private RC.',
        'style "theme-lab-gtk2-progress-fragment" {'] + geometry_lines(recipe) +
        ['  engine "pixmap" {'] + [image_rule(gtk_state, detail,
        images[variant, detail][0], shadow)
        for gtk_state in (('NORMAL', 'PRELIGHT', 'INSENSITIVE') if state == 'disabled' else (gtk_state,))
        for detail in ('trough', 'bar')] +
        ['  }', '}', '# Sample value is not task telemetry.', ''])
