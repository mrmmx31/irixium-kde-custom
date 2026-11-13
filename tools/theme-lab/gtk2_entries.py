# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GtkEntry recipe; effective KDE roles, no historical metric claim."""
from pathlib import Path
import hashlib
import json
from gtk2_buttons import geometry


def geometry_lines(recipe):
    shadow, padding, font = geometry(recipe)
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            '  GtkEntry::state-hint = 1',
            # The SR10.4 File Finder capture shows a one-pixel insertion stem.
            # GTK2's default 0.04 aspect ratio can widen it as the entry grows;
            # zero keeps the stem at one pixel without fixing its text role.
            '  GtkWidget::cursor-aspect-ratio = 0.0',
            '  GtkEntry::inner-border = { ' + ', '.join([str(padding)] * 4) + ' }',
            '  font_name = "' + str(font) + 'px"']


def image_rule(state, filename, border):
    return ('    image { function = SHADOW detail = "entry" state = ' + state +
            ' file = "' + filename + '" border = { ' + ', '.join([str(border)] * 4) +
            ' } stretch = TRUE }')


def snapshot_images(builder, recipe, palette):
    shadow, _, _ = geometry(recipe)
    art = builder.art
    images = {}
    for variant, index in (('normal', 0), ('backdrop', 1), ('disabled', 2)):
        effective = dict(palette)
        for names in art.ROLES.values():
            if names[index] in palette:
                effective[names[0]] = palette[names[index]]
        pixels = art.bevel(art.blank(2 * shadow + 1, 2 * shadow + 1, 'face'),
                           thickness=shadow, down=True)
        payload = builder.png(pixels, 'view', effective)
        filename = 'entry-' + variant + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png'
        images[variant] = filename, payload
    # The native SR10.4 File Finder changes a two-pixel outline when keyboard
    # focus enters the field. Keep the outline transparent inside and derive
    # its color from the current KDE focus role; do not bake the captured coral
    # sample into the theme.
    focus = art.blank(5, 5)
    art.rect(focus, 0, 0, 5, 2, 'focus')
    art.rect(focus, 0, 3, 5, 2, 'focus')
    art.rect(focus, 0, 2, 2, 1, 'focus')
    art.rect(focus, 3, 2, 2, 1, 'focus')
    for variant, index in (('focus', 0), ('backdrop-focus', 1), ('disabled-focus', 2)):
        effective = dict(palette)
        focus_names = art.ROLES['focus']
        effective[focus_names[0]] = palette[focus_names[index]]
        payload = builder.png(focus, 'window', effective)
        images[variant] = ('entry-' + variant + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png', payload)
    return images


def paint_entry(builder, recipe, palette, destination):
    shadow, _, _ = geometry(recipe)
    art = builder.art
    # VUE's native text selection is reverse video. Invert the Entry's current
    # KDE view/text pair, rather than borrowing the separate list Selection
    # pair. Other widgets keep the KDE Selection roles.
    roles = ('view', 'view-fg', 'focus')
    for role in roles:
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 entry missing effective role: ' + name)
    images = snapshot_images(builder, recipe, palette)
    inputs = {name: palette[name] for role in roles for name in art.ROLES[role]}
    style_id = hashlib.sha256(json.dumps([geometry_lines(recipe), sorted(inputs.items()),
                                         sorted(name for name, _ in images.values())],
                                        sort_keys=True).encode()).hexdigest()[:16]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in images.values():
        (destination / name).write_bytes(payload)
    lines = ['# Native GtkEntry; KDE snapshot. Selection/clipboard stay native.']
    for prefix, variant in (('themeLabEntry', 'normal'),
                            ('themeLabBackdropEntry', 'backdrop'),
                            ('themeLabInsensitiveEntry', 'disabled')):
        style = prefix + '-' + style_id
        lines += ['style "' + style + '" {'] + geometry_lines(recipe)
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if variant == 'disabled' or state == 'INSENSITIVE' else 1 if variant == 'backdrop' else 0
            for field in ('base', 'bg', 'text', 'fg'):
                selected = state == 'SELECTED'
                if selected:
                    role = 'view-fg' if field in ('base', 'bg') else 'view'
                else:
                    role = 'view-fg' if field in ('text', 'fg') else 'view'
                rgb = art._rgb(palette[art.ROLES[role][index]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines.append('  engine "pixmap" {')
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            image_variant = ('disabled' if state == 'INSENSITIVE' else variant)
            if state == 'ACTIVE':
                image_variant = {'normal': 'focus', 'backdrop': 'backdrop-focus',
                                 'disabled': 'disabled-focus'}[variant]
            image = images[image_variant][0]
            lines.append(image_rule(state, image, shadow))
        lines += ['  }', '}', 'widget "*' + prefix + '_' + style_id + '" style : highest "' + style + '"']
    rc = destination / 'entry.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': [name for name, _ in images.values()],
            'translated_control': 'entry', 'style_id': style_id}


def selected_fragment(recipe, state, builder, palette):
    if state not in ('normal', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 entry: unsupported forced state: ' + state)
    shadow, _, _ = geometry(recipe)
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    images = snapshot_images(builder, recipe, palette)
    focus_variant = {'normal': 'focus', 'backdrop': 'backdrop-focus',
                     'disabled': 'disabled-focus'}[variant]
    states = ('NORMAL', 'PRELIGHT', 'INSENSITIVE') if state == 'disabled' else ('PRELIGHT',) if state == 'hover' else ('NORMAL',)
    return '\n'.join(['# Selected GtkEntry; palette bindings supplied by private generated RC.',
                      'style "theme-lab-gtk2-entry-fragment" {'] + geometry_lines(recipe) +
                     ['  engine "pixmap" {',
                      image_rule('ACTIVE', images[focus_variant][0], shadow)] +
                     [image_rule(s, images[variant][0], shadow) for s in states] +
                     ['  }', '}', '# Inspection fragment; not a complete theme.', ''])
