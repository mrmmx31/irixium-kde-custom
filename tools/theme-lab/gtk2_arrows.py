# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone GtkButton + GtkArrow foundation, not GtkRange steppers.

Native GTK2 owns input and allocation; masks derive only from verified KDE
roles. Recipe dimensions/reliefs are proposals, not historical defaults.
"""
import hashlib
import json
from pathlib import Path
from gtk2_buttons import geometry, image_rule

DIRECTIONS = ('up', 'down', 'left', 'right')


def validate_geometry(recipe):
    default_shadow, _, _ = geometry(recipe)
    parts = recipe.get('scrollbar_parts', {})
    glyph = parts.get('arrow', {}).get('glyph_px', recipe['geometry']['arrow_px'])
    glyph_shadow = parts.get('arrow', {}).get('shadow_px', default_shadow)
    shadow = parts.get('arrow_button', {}).get('shadow_px', default_shadow)
    padding = parts.get('arrow_button', {}).get('padding_px', 0)
    for field, value in (('shadow_px',shadow),('padding_px',padding),('glyph_shadow',glyph_shadow)):
        if type(value) is not int or not 0 <= value <= 128:
            raise ValueError('GTK2 isolated arrow: invalid ' + field)
    if type(glyph) is not int or not 3 <= glyph <= 127 or glyph % 2 != 1:
        raise ValueError('GTK2 isolated arrow: arrow_px requires odd integer 3..127')
    if type(recipe['geometry']['arrow_px']) is not int or glyph > recipe['geometry']['arrow_px'] or 2 * glyph_shadow >= glyph:
        raise ValueError('GTK2 isolated arrow: shadow must fit reserved glyph')
    outer = recipe['geometry']['arrow_px'] + 2 * default_shadow
    if 2 * (padding + shadow) + glyph > outer:
        raise ValueError('GTK2 isolated arrow: button border/padding must fit reserved extent')
    glyph_reliefs = parts.get('arrow', {}).get('state_relief', {})
    if not isinstance(glyph_reliefs, dict) or set(glyph_reliefs) - {'normal','pressed','disabled','backdrop'} or any(v not in ('raised','sunken','flat') for v in glyph_reliefs.values()):
        raise ValueError('GTK2 isolated arrow: unsupported glyph relief/state')
    overrides = recipe.get('scrollbar_parts', {}).get('arrow_button', {}).get('state_relief', {})
    if not isinstance(overrides, dict) or set(overrides) - {'normal','pressed','disabled','backdrop','hover'} or any(v not in ('raised','sunken','flat') for v in overrides.values()):
        raise ValueError('GTK2 isolated arrow: unsupported button relief/state')
    return shadow, overrides


def glyph_geometry(recipe):
    validate_geometry(recipe)
    result = dict(recipe['geometry'])
    parts = recipe.get('scrollbar_parts', {}).get('arrow', {})
    result['arrow_px'] = parts.get('glyph_px', result['arrow_px'])
    result['shadow_px'] = parts.get('shadow_px', result['shadow_px'])
    return result


def geometry_lines(recipe):
    shadow, _ = validate_geometry(recipe)
    padding = recipe.get('scrollbar_parts', {}).get('arrow_button', {}).get('padding_px', 0)
    font = geometry(recipe)[2]
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            '  GtkButton::inner-border = { ' + ', '.join([str(padding)]*4) + ' }',
            # XmArrowButton in the local Motif reference uses highlightThickness=0.
            # GTK2 otherwise reserves 3 px on each axis for its focus indicator,
            # inflating the 11 px glyph + 2 px bevel from 15x15 to 21x21.
            # Keep keyboard activation; remove only the extra visual allocation.
            '  GtkButton::focus-line-width = 0',
            '  GtkButton::focus-padding = 0',
            '  font_name = "' + str(font) + 'px"']


def snapshot_images(builder, recipe, palette):
    shadow, overrides = validate_geometry(recipe)
    images = {}
    for context, index in (('normal',0), ('backdrop',1), ('disabled',2)):
        effective = dict(palette)
        for names in builder.art.ROLES.values():
            if names[index] in palette:
                effective[names[0]] = palette[names[index]]
        for interaction in ('idle','pressed','hover'):
            state = 'disabled' if context == 'disabled' else 'pressed' if interaction == 'pressed' else 'hover' if interaction == 'hover' else context
            relief = overrides.get(state, 'sunken' if state == 'pressed' else 'raised')
            pixels = builder.art.blank(2*shadow+1, 2*shadow+1, 'face')
            if relief != 'flat':
                pixels = builder.art.bevel(pixels, thickness=shadow, down=relief=='sunken')
            parts = {'panel': pixels}
            for direction in DIRECTIONS:
                glyph_state = 'pressed' if state=='pressed' else context
                arrow = builder.gtk3_arrow(glyph_state, direction, geometry=glyph_geometry(recipe))
                glyph_relief = recipe.get('scrollbar_parts', {}).get('arrow', {}).get('state_relief', {}).get(glyph_state)
                if glyph_relief:
                    arrow = builder.gtk3_arrow('normal', direction, geometry=glyph_geometry(recipe))
                    swaps = {'light':'dark','dark':'light'} if glyph_relief=='sunken' else {}
                    arrow = [[None if token is None else 'face' if glyph_relief=='flat' else swaps.get(token,token) for token in row] for row in arrow]
                parts[direction] = arrow
            for part, pixels in parts.items():
                payload = builder.png(pixels, 'button', effective)
                name = 'isolated-arrow-' + part + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png'
                images[context, interaction, part] = name, payload
    return images


def paint_rules(recipe, images, context, states):
    shadow, _ = validate_geometry(recipe)
    lines = []
    for state in states:
        variant = 'disabled' if state=='INSENSITIVE' else context
        interaction = 'pressed' if state=='ACTIVE' else 'hover' if state=='PRELIGHT' else 'idle'
        lines.append(image_rule(state, images[variant,interaction,'panel'][0], shadow))
        for direction in DIRECTIONS:
            lines.append('    image { function = ARROW detail = "arrow" state = ' + state +
                ' arrow_direction = ' + direction.upper() + ' overlay_file = "' + images[variant,interaction,direction][0] +
                '" overlay_stretch = FALSE }')
    return lines


def paint_arrow(builder, recipe, palette, destination):
    for role in ('button','button-fg'):
        for name in builder.art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 isolated arrow missing effective role: ' + name)
    images = snapshot_images(builder, recipe, palette)
    inputs = {name:palette[name] for role in ('button','button-fg') for name in builder.art.ROLES[role]}
    assets = sorted(set(name for name, _ in images.values()))
    style_id = hashlib.sha256(json.dumps([geometry_lines(recipe),recipe['geometry']['arrow_px'],
        validate_geometry(recipe)[1], sorted(inputs.items()), assets], sort_keys=True).encode()).hexdigest()[:16]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name,payload in images.values():
        (destination/name).write_bytes(payload)
    states = ('NORMAL','PRELIGHT','ACTIVE','SELECTED','INSENSITIVE')
    lines = ['# Standalone GTK2 arrow button; independent from range steppers.']
    for prefix,context,index in (('themeLabArrow','normal',0),('themeLabBackdropArrow','backdrop',1),('themeLabInsensitiveArrow','disabled',2)):
        style = prefix + '-' + style_id
        lines += ['style "' + style + '" {'] + geometry_lines(recipe)
        for state in states:
            effective = 2 if state=='INSENSITIVE' else index
            for field,role in (('bg','button'),('fg','button-fg')):
                rgb = builder.art._rgb(palette[builder.art.ROLES[role][effective]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines += ['  engine "pixmap" {'] + paint_rules(recipe,images,context,states) + ['  }','}']
        for suffix in ('', '.*'):
            lines.append('widget "*' + prefix + '_' + style_id + suffix + '" style : highest "' + style + '"')
    rc = destination/'isolated-arrow.gtkrc'
    rc.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return {'rc':str(rc),'assets':assets,'translated_control':'arrow','style_id':style_id}


def selected_fragment(recipe,state,builder,palette):
    if state not in ('normal','pressed','disabled','backdrop','hover'):
        raise ValueError('GTK2 isolated arrow: unsupported forced state: ' + state)
    context = 'disabled' if state=='disabled' else 'backdrop' if state=='backdrop' else 'normal'
    native = 'INSENSITIVE' if state=='disabled' else 'ACTIVE' if state=='pressed' else 'PRELIGHT' if state=='hover' else 'NORMAL'
    return '\n'.join(['# Standalone button and directional child; not a scrollbar stepper.',
        'style "theme-lab-gtk2-isolated-arrow-fragment" {'] + geometry_lines(recipe) + ['  engine "pixmap" {'] +
        paint_rules(recipe,snapshot_images(builder,recipe,palette),context,(native,)) + ['  }','}',''])
