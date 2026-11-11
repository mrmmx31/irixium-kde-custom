# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK2 combo button, symbolic arrow and scoped popup palette."""
from pathlib import Path
import hashlib
import io
import json

from PIL import Image
from gtk2_buttons import geometry, geometry_lines, image_rule

OPTION_INDICATOR_WIDTH = 14
OPTION_INDICATOR_HEIGHT = 8

# The Motif art contract gives secondary Header relief its own lighting
# ratios. GTK2's shared recipe override is for the primary controls and must
# not flatten this family distinction in the menu shell.
HEADER_RELIEF_MIX = {'light': 0.55, 'dark': 0.502}


def header_relief_plan(builder, token, *, inactive=False, disabled=False):
    plan = builder.art.pixel_plan('header', token, inactive=inactive,
                                  disabled=disabled)
    if token in HEADER_RELIEF_MIX:
        plan['mix'] = HEADER_RELIEF_MIX[token]
    return plan


def header_relief_png(builder, pixels, palette):
    image = Image.new('RGBA', (len(pixels[0]), len(pixels)))
    for y, row in enumerate(pixels):
        for x, token in enumerate(row):
            if token is None:
                continue
            value = builder.art.evaluate(header_relief_plan(builder, token),
                                         palette)
            image.putpixel((x, y), tuple(int(value[n:n+2], 16)
                                          for n in (1, 3, 5)) + (255,))
    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def combo_geometry(recipe):
    lines = geometry_lines(recipe)
    arrow = recipe['geometry']['arrow_px']
    if type(arrow) is not int or not 1 <= arrow <= 128:
        raise ValueError('GTK2 combo: arrow_px requires integer 1..128')
    return lines + ['  GtkComboBox::arrow-size = ' + str(arrow),
                    '  GtkComboBox::appears-as-list = 0']


def snapshot_images(builder, recipe, palette):
    shadow, _, _ = geometry(recipe)
    combo_geometry(recipe)
    images = {}
    for state, index in (('normal', 0), ('pressed', 0), ('backdrop', 1), ('disabled', 2)):
        effective = dict(palette)
        for names in builder.art.ROLES.values():
            if names[index] in palette:
                effective[names[0]] = palette[names[index]]
        face = builder.art.bevel(builder.art.blank(2*shadow+1, 2*shadow+1, 'face'),
                                 thickness=shadow, down=state == 'pressed')
        # The SR10.4/VUE option-menu indicator is a small rectangular relief
        # mark, not the scrollbar's triangular arrow. Its 14x8 outline was
        # measured from the archived VUE Snapshot/None option menu. Keep this
        # geometry separate from the shared scrollbar arrow contract.
        arrow = builder.art.bevel(
            builder.art.blank(OPTION_INDICATOR_WIDTH, OPTION_INDICATOR_HEIGHT, 'face'),
            thickness=2, down=state == 'pressed')
        for part, mask in (('face', face), ('arrow', arrow)):
            payload = builder.png(mask, 'button', effective)
            name = 'combo-' + part + '-' + state + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png'
            images[state, part] = name, payload
        # GTK2 theme engines can paint GtkMenuItem rows from their own pixmap
        # assets, bypassing bg[NORMAL]/bg[PRELIGHT] in the RC style. The VUE
        # menu popup uses the same surface as its menubar, so keep it on the
        # semantic Header role instead of inheriting another theme's artwork.
        popup_mask = builder.art.blank(1, 1, 'face')
        if state != 'pressed':
            popup_payload = builder.png(popup_mask, 'header', effective)
            popup_name = ('combo-popup-' + state + '-' +
                          hashlib.sha256(popup_payload).hexdigest()[:16] + '.png')
            images[state, 'popup'] = popup_name, popup_payload
            shell_mask = builder.art.bevel(
                builder.art.blank(5, 5, 'face'), thickness=2, down=False)
            shell_payload = header_relief_png(builder, shell_mask, effective)
            shell_name = ('combo-popup-shell-' + state + '-' +
                          hashlib.sha256(shell_payload).hexdigest()[:16] + '.png')
            images[state, 'popup-shell'] = shell_name, shell_payload
        if state in ('pressed', 'backdrop', 'disabled'):
            variant = 'normal' if state == 'pressed' else state
            selected_mask = builder.art.bevel(
                builder.art.blank(5, 5, 'face'), thickness=2, down=False)
            selected_payload = header_relief_png(builder, selected_mask, effective)
            selected_name = ('combo-popup-selected-' + variant + '-' +
                             hashlib.sha256(selected_payload).hexdigest()[:16] + '.png')
            images[variant, 'popup-selected'] = selected_name, selected_payload
            pressed_mask = builder.art.bevel(
                builder.art.blank(5, 5, 'face'), thickness=2, down=True)
            pressed_payload = header_relief_png(builder, pressed_mask, effective)
            pressed_name = ('combo-popup-pressed-' + variant + '-' +
                            hashlib.sha256(pressed_payload).hexdigest()[:16] + '.png')
            images[variant, 'popup-pressed'] = pressed_name, pressed_payload
    return images


def arrow_rule(state, filename):
    return ('    image { function = ARROW state = ' + state +
            ' arrow_direction = DOWN overlay_file = "' + filename + '" overlay_stretch = FALSE }')


def paint_combo(builder, recipe, palette, destination):
    roles = ('button', 'button-fg', 'header', 'header-fg')
    for role in roles:
        for name in builder.art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 combo missing effective role: ' + name)
    images = snapshot_images(builder, recipe, palette)
    inputs = {name: palette[name] for role in roles for name in builder.art.ROLES[role]}
    style_id = hashlib.sha256(json.dumps([combo_geometry(recipe), sorted(inputs.items()),
                                         sorted(name for name, _ in images.values())],
                                        sort_keys=True).encode()).hexdigest()[:16]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in images.values():
        (destination/name).write_bytes(payload)
    shadow, _, _ = geometry(recipe)
    lines = ['# Native combo; palette resolved from verified KDE roles.']
    for prefix, variant, index in (('themeLabCombo', 'normal', 0),
                                  ('themeLabBackdropCombo', 'backdrop', 1),
                                  ('themeLabInsensitiveCombo', 'disabled', 2)):
        style = prefix + '-' + style_id
        for popup in (False, True):
            name = style + ('-popup' if popup else '')
            lines += ['style "' + name + '" {'] + combo_geometry(recipe)
            for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
                effective = 2 if state == 'INSENSITIVE' else index
                for field in ('base', 'bg', 'text', 'fg'):
                    foreground = field in ('text', 'fg')
                    role = (('header-fg' if foreground else 'header') if popup else
                            ('button-fg' if foreground else 'button'))
                    rgb = builder.art._rgb(palette[builder.art.ROLES[role][effective]])
                    lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
            if not popup:
                lines.append('  engine "pixmap" {')
                for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
                    image_state = 'disabled' if state == 'INSENSITIVE' else variant if variant != 'normal' else 'pressed' if state == 'ACTIVE' else 'normal'
                    lines += [image_rule(state, images[image_state, 'face'][0], shadow),
                              arrow_rule(state, images[image_state, 'arrow'][0])]
                lines.append('  }')
            else:
                lines.append('  engine "pixmap" {')
                for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
                    disabled = state == 'INSENSITIVE'
                    selected = state in ('PRELIGHT', 'SELECTED')
                    pressed = state == 'ACTIVE'
                    surface_variant = 'disabled' if disabled else variant
                    filename = images[(surface_variant, 'popup-selected') if selected else
                                      (surface_variant, 'popup-pressed') if pressed else
                                      (surface_variant, 'popup')][0]
                    lines.append('    image { function = BOX detail = "menu" state = ' + state +
                                 ' file = "' + images[surface_variant, "popup-shell"][0] +
                                 '" border = { 2, 2, 2, 2 } stretch = TRUE }')
                    lines.append('    image { function = BOX detail = "menuitem" state = ' + state +
                                 ' file = "' + filename + '" border = { 2, 2, 2, 2 } stretch = TRUE }')
                lines.append('  }')
            lines.append('}')
            widget_name = prefix + ('Popup_' if popup else '_') + style_id
            for suffix in ('', '.*'):
                lines.append('widget "*' + widget_name + suffix + '" style : highest "' + name + '"')
        popup_window_style = style + '-popup-window'
        lines += ['style "' + popup_window_style + '" {']
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            effective = 2 if state == 'INSENSITIVE' else index
            for field, role in (('bg', 'header'), ('fg', 'header-fg')):
                rgb = builder.art._rgb(palette[builder.art.ROLES[role][effective]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines.append('}')
        popup_window_name = prefix + 'PopupWindow_' + style_id
        for suffix in ('', '.*'):
            lines.append('widget "*' + popup_window_name + suffix + '" style : highest "' +
                         popup_window_style + '"')
        # GtkMenu's child rows are created as separate widgets. Bind them
        # explicitly as well as the popup shell: GTK2 theme engines may resolve
        # their state colors from the row path rather than inheriting the
        # late-renamed GtkMenu style.
        popup_style = style + '-popup'
        lines.append('widget "*' + prefix + 'PopupItem_' + style_id +
                     '_*" style : highest "' + popup_style + '"')
    rc = destination/'combo.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': [name for name, _ in images.values()],
            'translated_control': 'combo', 'style_id': style_id}


def selected_fragment(recipe, state, builder, palette):
    if state not in ('normal', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 combo: unsupported forced state: ' + state)
    variant = 'disabled' if state == 'disabled' else 'backdrop' if state == 'backdrop' else 'normal'
    images = snapshot_images(builder, recipe, palette)
    shadow, _, _ = geometry(recipe)
    gtk_state = 'INSENSITIVE' if state == 'disabled' else 'PRELIGHT' if state == 'hover' else 'NORMAL'
    return '\n'.join(['# Selected native GTK2 combo; popup and palette bindings are generated separately.',
                      'style "theme-lab-gtk2-combo-fragment" {'] + combo_geometry(recipe) +
                     ['  engine "pixmap" {', image_rule(gtk_state, images[variant, 'face'][0], shadow),
                      arrow_rule(gtk_state, images[variant, 'arrow'][0]), '  }', '}', ''])
