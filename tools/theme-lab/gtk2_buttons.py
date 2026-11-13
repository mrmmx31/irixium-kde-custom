# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 push-button proposal: native geometry and effective KDE role images.

This module does not install a theme or assert historical widget metrics.
The recipe's shadow, padding and font are proposals, not Motif C defaults.
"""
from pathlib import Path
from io import BytesIO


# R216 measured the SR10.4 focused pushbutton's bevel as a 76x36 image body:
# a 6px nine-slice border around a 64x24 face.  The 13x13 mask records only
# light/face/shadow geometry; colors are resolved from the live KDE roles.
PUSH_IMAGE_BORDER_PX = 6
VUE_PUSH_FRAME = (
    'ddddddddddddd',
    'dfffffffffffl',
    'dfffffffffffl',
    'dfffffffffffl',
    'dffflllllfffl',
    'dffflllldfffl',
    'dfffllfddfffl',
    'dffflldddfffl',
    'dffflddddfffl',
    'dfffffffffffl',
    'dfffffffffffl',
    'dfffffffffffl',
    'dllllllllllll',
)


def push_frame_pixels(state):
    """Return the measured SR10.4 9-slice mask for one push-button state."""
    if state not in ('normal', 'pressed', 'disabled', 'backdrop'):
        raise ValueError('GTK2 button: unsupported frame state: ' + state)
    tokens = {'d': 'dark', 'f': 'face', 'l': 'light'}
    pixels = [[tokens[token] for token in row] for row in VUE_PUSH_FRAME]
    if state == 'pressed':
        # R216: exactly the 76px top edge flattens while held. The 64x24 center
        # face is shaded separately after role colors are resolved.
        pixels[0] = ['face'] * len(pixels[0])
    return pixels


def geometry(recipe):
    values = recipe['geometry']
    shadow, padding, font = (values[k] for k in ('shadow_px', 'control_padding_px', 'font_px'))
    for name, value, low, high in (('shadow_px', shadow, 0, 128),
                                   ('control_padding_px', padding, 0, 128), ('font_px', font, 6, 48)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError('GTK2 button: invalid proposed geometry: ' + name)
    return shadow, padding, font


def image_rule(state, filename, border_px):
    border = ', '.join([str(border_px)] * 4)
    return ('    image { function = BOX detail = "button" state = ' + state +
            ' file = "' + filename + '" border = { ' + border + ' } stretch = TRUE }')


def geometry_lines(recipe):
    shadow, padding, font = geometry(recipe)
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            '  GtkButton::inner-border = { ' + ', '.join([str(padding)] * 4) + ' }',
            '  font_name = "' + str(font) + 'px"']


def push_geometry_lines(recipe):
    shadow, padding, font = geometry(recipe)
    # R26 compares the actual Motif button pixels (62x21) with a native GTK2
    # button.  Keeping GTK2's vertical style extent at zero yields 63x21 while
    # the generated image still carries the measured 2px bevel.  Horizontal
    # thickness remains tied to the recipe's bevel/shadow setting.
    return ['  xthickness = ' + str(shadow), '  ythickness = 0',
            '  GtkButton::inner-border = { ' + ', '.join([str(padding)] * 4) + ' }',
            # VUE's measured focused/default Start button has a continuous
            # outer focus frame. GTK2 defaults to a dotted interior line.
            # These native GTK2 properties move the outline outside the face
            # and give it the 2px measured emphasis without fixing its color.
            '  GtkButton::focus-line-pattern = ""',
            '  GtkButton::focus-line-width = 2',
            '  GtkButton::focus-padding = 2',
            '  GtkButton::interior-focus = 0',
            '  font_name = "' + str(font) + 'px"']


def role_source(state, backdrop=False):
    """Return the KDE role family and variant used by a push-button state.

    The live SR10.4 Find Files button uses the VUE Header color set. Disabled
    controls retain Button roles because no disabled VUE push-button state has
    been measured yet.
    """
    if state == 'disabled':
        return ('button', 'button-fg', 3 if backdrop else 2)
    if state == 'backdrop' or backdrop:
        return ('header', 'header-fg', 1)
    return ('header', 'header-fg', 0)


def focus_role(backdrop=False):
    """Return KDE's dynamic focus role for GTK2's native button outline.

    GTK2 paints GtkButton focus through the widget style foreground GC. The
    child GtkLabel keeps its own foreground, so the outline can follow
    DecorationFocus without recoloring the button text.
    """
    return ('focus', 1 if backdrop else 0)


def pressed_face_color(art, palette):
    """Shade the live VUE Header face while held; retain light/shadow roles."""
    header = palette[art.ROLES['header'][0]]
    return art.tone(header, 0.15, '#000000')


def paint_button(builder, recipe, palette, destination):
    geometry(recipe)
    art = builder.art
    for role in ('header', 'header-fg', 'button', 'button-fg', 'focus'):
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 button missing effective role: ' + name)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    files = {}
    pressed_face = pressed_face_color(art, palette)
    for state in ('normal', 'pressed', 'disabled', 'backdrop'):
        effective = dict(palette)
        index = 2 if state == 'disabled' else 1 if state == 'backdrop' else 0
        for names in art.ROLES.values():
            if names[index] in palette: effective[names[0]] = palette[names[index]]
        pixels = push_frame_pixels(state)
        filename = 'push-' + state + '.png'
        family, _, _ = role_source(state)
        image = builder.png(pixels, family, effective)
        if state == 'pressed':
            # R216 shows a 15% dynamic shade in the 64x24 center face. The
            # pressed mask keeps the measured side/bottom relief unchanged.
            from PIL import Image
            image = Image.open(BytesIO(image)).convert('RGBA')
            center = PUSH_IMAGE_BORDER_PX
            image.putpixel((center, center), art._rgb(pressed_face) + (255,))
            encoded = BytesIO()
            image.save(encoded, format='PNG', optimize=True)
            image = encoded.getvalue()
        (destination / filename).write_bytes(image)
        files[state] = filename
    lines = ['# Private GTK2 button proposal; RGB resolved from verified KDE roles.']
    label_bindings = []
    for name, backdrop in (('theme-lab-gtk2-push', False), ('theme-lab-gtk2-push-backdrop', True)):
        lines += ['style "' + name + '" {'] + push_geometry_lines(recipe)
        for gtk_state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            state = 'disabled' if gtk_state == 'INSENSITIVE' else 'normal'
            face_role, text_role, index = role_source(state, backdrop=backdrop)
            face = (pressed_face if gtk_state == 'ACTIVE' and not backdrop
                    else palette[art.ROLES[face_role][index]])
            face_rgb = art._rgb(face)
            lines.append('  bg[' + gtk_state + '] = "#%02x%02x%02x"' % face_rgb)
            # The native focus painter reads the button's foreground GC; the
            # nested GtkLabel keeps its own Header foreground style.
            fg_role, fg_index = (focus_role(backdrop) if gtk_state != 'INSENSITIVE'
                                 else (text_role, index))
            fg_rgb = art._rgb(palette[art.ROLES[fg_role][fg_index]])
            lines.append('  fg[' + gtk_state + '] = "#%02x%02x%02x"' % fg_rgb)
        lines.append('  engine "pixmap" {')
        for gtk_state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            state = ('disabled' if gtk_state == 'INSENSITIVE' else
                     'backdrop' if backdrop else 'pressed' if gtk_state == 'ACTIVE' else 'normal')
            lines.append(image_rule(gtk_state, files[state], PUSH_IMAGE_BORDER_PX))
        lines += ['  }', '}']
        label_name = name + '-label'
        lines += ['style "' + label_name + '" {']
        for gtk_state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            state = 'disabled' if gtk_state == 'INSENSITIVE' else 'normal'
            _, text_role, index = role_source(state, backdrop=backdrop)
            text_rgb = art._rgb(palette[art.ROLES[text_role][index]])
            lines.append('  fg[' + gtk_state + '] = "#%02x%02x%02x"' % text_rgb)
        lines.append('}')
        label_widget = ('themeLabBackdropPush' if backdrop else 'themeLabPush') + '.GtkLabel'
        label_bindings.append('widget "*' + label_widget + '" style : highest "' + label_name + '"')
    lines += ['widget "*themeLabPush" style : highest "theme-lab-gtk2-push"',
              'widget "*themeLabPush.*" style : highest "theme-lab-gtk2-push"',
              'widget "*themeLabBackdropPush" style : highest "theme-lab-gtk2-push-backdrop"',
              'widget "*themeLabBackdropPush.*" style : highest "theme-lab-gtk2-push-backdrop"']
    lines += label_bindings + ['']
    rc = destination / 'button.gtkrc'
    rc.write_text('\n'.join(lines), encoding='utf-8')
    return {'rc': str(rc), 'assets': list(files.values()), 'translated_control': 'push',
            'color_roles': {'enabled': 'KDE Header active/inactive roles',
                            'disabled': 'KDE Button disabled roles'},
            'scope': 'Private standalone push-button proposal; scene integration separate',
            'hover_policy': 'Native PRELIGHT uses normal effective roles',
            'press_policy': 'R216 SR10.4 mask: 6px nine-slice bevel, 64x24 center face shaded 15% dynamically from KDE HeaderBackground while the measured 76px top edge flattens; side and bottom relief stay unchanged',
            'focus_policy': 'Solid 2px outer GTK2 focus outline, 2px padding, dynamic KDE DecorationFocus; preview label retains its matching text role'}


def selected_fragment(recipe, state):
    if state not in ('normal', 'pressed', 'disabled', 'backdrop', 'hover'):
        raise ValueError('GTK2 button: state not translated: ' + state)
    geometry(recipe)
    gtk_state = {'normal':'NORMAL', 'hover':'PRELIGHT', 'pressed':'ACTIVE',
                 'disabled':'INSENSITIVE', 'backdrop':'NORMAL'}[state]
    image_state = 'normal' if state == 'hover' else state
    return '\n'.join(['# Selected GtkButton only; palette/text bindings come from verified generated RC.',
        'style "theme-lab-gtk2-push-fragment" {'] + push_geometry_lines(recipe) +
        ['  engine "pixmap" {', image_rule(gtk_state, 'push-' + image_state + '.png', PUSH_IMAGE_BORDER_PX),
         '  }', '}', '# Inspection fragment; not a complete theme or palette installation.', ''])
