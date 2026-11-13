# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GtkHScale/GtkVScale foundation, isolated KDE role snapshots.

Geometry defaults follow the local native Motif Theme Lab sample, not an
SR10.4 default. GtkRange owns value, orientation and interaction. Integration
into the scene is a separate gate.
"""
import hashlib
import json
from pathlib import Path
from gtk2_buttons import geometry


# Measured from the 1:1 native Motif scale in
# docs/review/theme-lab-motif-reference/01-MOTIF-REFERENCE.png: its horizontal
# thumb is about 27x8 px. These are Theme Lab defaults, not SR10.4 defaults.
# Keep scale geometry independent from scrollbar thumb metrics.
MOTIF_SCALE_SLIDER_WIDTH_PX = 8
MOTIF_SCALE_SLIDER_LENGTH_PX = 27


def geometry_lines(recipe):
    shadow, padding, font = geometry(recipe)
    dimensions = recipe['geometry']
    cross = dimensions.get('scale_slider_width_px', MOTIF_SCALE_SLIDER_WIDTH_PX)
    length = dimensions.get('scale_slider_length_px', MOTIF_SCALE_SLIDER_LENGTH_PX)
    for name, value in (('scale_slider_width_px', cross), ('scale_slider_length_px', length)):
        if type(value) is not int or not 1 <= value <= 128:
            raise ValueError('GTK2 scale: ' + name + ' requires integer 1..128')
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            '  GtkRange::slider-width = ' + str(cross),
            '  GtkRange::trough-border = ' + str(shadow),
            '  GtkScale::slider-length = ' + str(length),
            '  GtkScale::value-spacing = ' + str(padding),
            '  font_name = "' + str(font) + 'px"']


def snapshot_images(builder, recipe, palette):
    shadow, _, _ = geometry(recipe)
    geometry_lines(recipe)
    images = {}
    for variant, index in (('normal', 0), ('pressed', 0), ('backdrop', 1), ('disabled', 2)):
        effective = dict(palette)
        for names in builder.art.ROLES.values():
            if names[index] in palette:
                effective[names[0]] = palette[names[index]]
        for part in ('trough', 'slider'):
            # GTK2 draws trough ACTIVE even when idle; never treat this as press.
            pixels = builder.art.bevel(builder.art.blank(2*shadow+1, 2*shadow+1, 'face'),
                thickness=shadow, down=part == 'trough' or variant == 'pressed')
            payload = builder.png(pixels, 'button', effective)
            filename = 'scale-' + part + '-' + variant + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png'
            images[part, variant] = filename, payload
    return images


def paint_rules(recipe, images, variant, states):
    shadow, _, _ = geometry(recipe)
    border = ', '.join([str(shadow)] * 4)
    lines = []
    for state in states:
        face = 'disabled' if state == 'INSENSITIVE' else variant
        slider = 'pressed' if face == 'normal' and state == 'ACTIVE' else face
        for direction, detail in (('HORIZONTAL', 'hscale'), ('VERTICAL', 'vscale')):
            for function, part, mode in (('BOX', 'trough', face), ('SLIDER', 'slider', slider)):
                lines.append('    image { function = ' + function + ' detail = "' +
                    ('trough' if part == 'trough' else detail) + '" state = ' + state +
                    ' orientation = ' + direction + ' file = "' + images[part, mode][0] +
                    '" border = { ' + border + ' } stretch = TRUE }')
    return lines


def paint_scale(builder, recipe, palette, destination):
    for role in ('button', 'button-fg'):
        for name in builder.art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 scale missing effective role: ' + name)
    images = snapshot_images(builder, recipe, palette)
    inputs = {name: palette[name] for role in ('button', 'button-fg') for name in builder.art.ROLES[role]}
    style_id = hashlib.sha256(json.dumps([geometry_lines(recipe), sorted(inputs.items()),
        sorted(name for name, _ in images.values())], sort_keys=True).encode()).hexdigest()[:16]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in images.values():
        (destination/name).write_bytes(payload)
    states = ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE')
    lines = ['# Native GTK2 scale foundation; effective KDE roles, no installation.']
    for prefix, variant, index in (('themeLabScale', 'normal', 0),
                                  ('themeLabBackdropScale', 'backdrop', 1),
                                  ('themeLabInsensitiveScale', 'disabled', 2)):
        style = prefix + '-' + style_id
        lines += ['style "' + style + '" {'] + geometry_lines(recipe)
        for state in states:
            effective = 2 if state == 'INSENSITIVE' else index
            for field, role in (('bg', 'button'), ('fg', 'button-fg')):
                rgb = builder.art._rgb(palette[builder.art.ROLES[role][effective]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines += ['  engine "pixmap" {'] + paint_rules(recipe, images, variant, states) + ['  }', '}']
        lines.append('widget "*' + prefix + '_' + style_id + '" style : highest "' + style + '"')
    rc = destination/'scale.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': sorted(set(name for name, _ in images.values())),
            'translated_controls': ['scale_h', 'scale_v'], 'style_id': style_id}


def selected_fragment(recipe, state, builder, palette):
    if state not in ('normal', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 scale: unsupported forced state: ' + state)
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    gtk_state = 'INSENSITIVE' if state == 'disabled' else 'PRELIGHT' if state == 'hover' else 'NORMAL'
    return '\n'.join(['# Scale foundation inspection; GTK2 owns adjustment and input.',
        'style "theme-lab-gtk2-scale-fragment" {'] + geometry_lines(recipe) +
        ['  engine "pixmap" {'] + paint_rules(recipe, snapshot_images(builder, recipe, palette), variant, (gtk_state,)) + ['  }', '}', ''])
