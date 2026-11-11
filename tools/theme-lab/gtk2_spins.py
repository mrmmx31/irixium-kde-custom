# SPDX-License-Identifier: GPL-3.0-or-later
"""GtkSpinButton foundation: native field, free-standing Motif relief masks.

Recipe geometry is a proposal. Native GTK2 retains arrow placement/size,
numeric validation and stepping; no SR10.4 metric equivalence is claimed.
"""
from pathlib import Path
import hashlib
import json
from gtk2_buttons import geometry
from gtk2_entries import geometry_lines, snapshot_images as entry_images, image_rule as entry_rule


def spin_geometry(recipe):
    return geometry_lines(recipe)


def spin_arrow_geometry(recipe):
    """Return an independent glyph size; the Motif sample measures 13x13.

    Scrollbar arrows have their own 11px contract. Reusing that setting here
    made the spin arrows visibly smaller than the Motif reference.
    """
    arrow = recipe.get('spin_arrow_px', 13)
    if type(arrow) is not int or not 3 <= arrow <= 127 or arrow % 2 != 1:
        raise ValueError('GTK2 spin: spin_arrow_px requires odd integer 3..127')
    result = dict(recipe['geometry'])
    result['arrow_px'] = arrow
    return result


def snapshot_images(builder, recipe, palette):
    shadow, _, _ = geometry(recipe)
    spin_geometry(recipe)
    images = {('entry', variant): item for variant, item in entry_images(builder, recipe, palette).items()}
    for variant, index in (('normal', 0), ('pressed', 0), ('backdrop', 1), ('disabled', 2)):
        effective = dict(palette)
        for names in builder.art.ROLES.values():
            if names[index] in palette:
                effective[names[0]] = palette[names[index]]
        # Motif places the two small arrows directly on the entry surface; it
        # does not wrap each one in a raised square button. Keep the GtkButton
        # child allocation native, but paint its box as the View face. The
        # bevel belongs to the arrow glyph itself and uses the enclosing
        # Window light/shadow roles through pixel_plan('view', ...).
        panel = builder.art.blank(1, 1, 'face')
        parts = {'panel': panel}
        for direction in ('up', 'down'):
            parts[direction] = builder.gtk3_arrow(variant, direction, geometry=spin_arrow_geometry(recipe))
        for part, pixels in parts.items():
            family = 'view'
            payload = builder.png(pixels, family, effective)
            name = 'spin-' + part + '-' + variant + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png'
            images[part, variant] = name, payload
    return images


def paint_rules(recipe, images, variant, states):
    shadow, _, _ = geometry(recipe)
    lines = []
    for state in states:
        face = 'disabled' if state == 'INSENSITIVE' else variant
        panel = face if face != 'normal' else 'pressed' if state == 'ACTIVE' else 'normal'
        lines.append(entry_rule(state, images['entry', face][0], shadow))
        for direction in ('up', 'down'):
            detail = 'spinbutton_' + direction
            lines.append('    image { function = BOX detail = "' + detail + '" state = ' + state +
                         ' file = "' + images['panel', panel][0] +
                         '" border = { 0, 0, 0, 0 } stretch = TRUE }')
            lines.append('    image { function = ARROW detail = "spinbutton" state = ' + state +
                         ' arrow_direction = ' + direction.upper() + ' overlay_file = "' +
                         images[direction, panel][0] + '" overlay_stretch = FALSE }')
    return lines


def paint_spin(builder, recipe, palette, destination):
    roles = ('view', 'view-fg', 'button', 'button-fg', 'selection', 'selection-fg')
    for role in roles:
        for name in builder.art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 spin missing effective role: ' + name)
    images = snapshot_images(builder, recipe, palette)
    inputs = {name: palette[name] for role in roles for name in builder.art.ROLES[role]}
    style_id = hashlib.sha256(json.dumps([spin_geometry(recipe), sorted(inputs.items()),
        spin_arrow_geometry(recipe),
        sorted(name for name, _ in images.values())], sort_keys=True).encode()).hexdigest()[:16]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in images.values():
        (destination/name).write_bytes(payload)
    states = ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE')
    lines = ['# GtkSpinButton native foundation; KDE role snapshot.']
    for prefix, variant, index in (('themeLabSpin', 'normal', 0),
                                  ('themeLabBackdropSpin', 'backdrop', 1),
                                  ('themeLabInsensitiveSpin', 'disabled', 2)):
        style = prefix + '-' + style_id
        lines += ['style "' + style + '" {'] + spin_geometry(recipe)
        for state in states:
            effective = 2 if state == 'INSENSITIVE' else index
            for field in ('bg', 'fg', 'base', 'text'):
                role = {'bg': 'button', 'fg': 'button-fg', 'base': 'view', 'text': 'view-fg'}[field]
                if state == 'SELECTED' and field in ('base', 'text'):
                    role = 'selection' if field == 'base' else 'selection-fg'
                rgb = builder.art._rgb(palette[builder.art.ROLES[role][effective]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines += ['  engine "pixmap" {'] + paint_rules(recipe, images, variant, states) + ['  }', '}']
        lines.append('widget "*' + prefix + '_' + style_id + '" style : highest "' + style + '"')
    rc = destination/'spin.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': [name for name, _ in images.values()],
            'translated_control': 'spin', 'style_id': style_id,
            'arrow_extent_scope': '13px Motif-sample glyph default, independently configurable by spin_arrow_px; native GTK2 controls panel allocation.'}


def selected_fragment(recipe, state, builder, palette):
    if state not in ('normal', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 spin: unsupported forced state: ' + state)
    images = snapshot_images(builder, recipe, palette)
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    gtk_state = 'INSENSITIVE' if state == 'disabled' else 'PRELIGHT' if state == 'hover' else 'NORMAL'
    return '\n'.join(['# GtkSpinButton inspection fragment; native input/stepper behavior retained.',
        'style "theme-lab-gtk2-spin-fragment" {'] + spin_geometry(recipe) + ['  engine "pixmap" {'] +
        paint_rules(recipe, images, variant, (gtk_state,)) + ['  }', '}', ''])
