#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 recipe translation; pure functions, no toolkit or profile access.

This first stage emits native range geometry. Painting, state roles and scene
integration remain separate gates; this alone is not a completed adapter.
"""
import hashlib
import json


def scrollbar_properties(recipe):
    geometry = recipe['geometry']
    parts = recipe.get('scrollbar_parts', {})

    def measure(piece, field, inherited):
        value = parts.get(piece, {}).get(field, geometry[inherited])
        if type(value) is not int or not 0 <= value <= 128:
            raise ValueError('GTK2: integer geometry in 0..128 required: ' + field)
        return value

    thickness = measure('trough', 'thickness_px', 'bar_px')
    border = measure('trough', 'shadow_px', 'shadow_px')
    cross = measure('thumb', 'cross_px', 'thumb_cross_px')
    arrow = measure('arrow', 'glyph_px', 'arrow_px')
    gap = measure('thumb', 'gap_px', 'arrow_thumb_gap_px')
    if cross < 1 or arrow < 3 or arrow % 2 != 1:
        raise ValueError('GTK2: positive cursor and odd arrow >=3 required')
    if thickness != cross + 2 * border or arrow > cross:
        raise ValueError('GTK2: native range thickness must equal cursor + two borders')
    # GtkRange's stepper allocation follows the native GTK range geometry.
    # Keep the full SR10.4 cell artwork separate from the cross-axis thumb size;
    # the Pixbuf engine's reconstructed draw rectangle is narrower than its
    # stepper expose clip and uses centered, non-stretched overlay rendering.
    if arrow + gap > 128:
        raise ValueError('GTK2: arrow plus gap exceeds native recipe bound')
    return {'slider-width': cross, 'stepper-size': thickness,
            'trough-border': border, 'stepper-spacing': 0,
            'trough-under-steppers': False,
            'has-backward-stepper': True, 'has-forward-stepper': True,
            'has-secondary-backward-stepper': False,
            'has-secondary-forward-stepper': False}


def scrollbar_rc(recipe, style_id=None):
    properties = scrollbar_properties(recipe)
    suffix = '-' + style_id if style_id else ''
    geometry_style = 'theme-lab-gtk2-scroll-geometry' + suffix
    lines = ['# Theme Lab GTK2 proposed native geometry; no palette override.',
             'style "' + geometry_style + '" {']
    for name, value in properties.items():
        owner = 'GtkScrollbar' if name.startswith('has-') else 'GtkRange'
        lines.append('  ' + owner + '::' + name + ' = ' +
                     ('1' if value is True else '0' if value is False else str(value)))
    lines.extend(['}', 'class "GtkScrollbar" style : highest "' + geometry_style + '"', ''])
    return '\n'.join(lines)


def paint_contract(recipe):
    """Validate and resolve the exact geometry used by native pixmap generation."""
    properties = scrollbar_properties(recipe)
    geometry = dict(recipe['geometry'])
    parts = recipe.get('scrollbar_parts', {})
    if parts.get('fitting'):
        raise ValueError('GTK2: content fitting painting remains pending')
    if parts.get('arrow_button'):
        from gtk2_arrows import validate_geometry
        validate_geometry(recipe)
    for piece in ('arrow', 'thumb', 'trough'):
        overrides = parts.get(piece, {}).get('state_relief', {})
        allowed = {'normal', 'disabled', 'backdrop'} | (set() if piece == 'trough' else {'pressed'})
        if not isinstance(overrides, dict) or set(overrides) - allowed or any(
                value not in ('flat', 'raised', 'sunken') for value in overrides.values()):
            raise ValueError('GTK2: unsupported piece relief/state: ' + piece)
    glyph = parts.get('arrow', {}).get('glyph_px', geometry['arrow_px'])
    gap = parts.get('thumb', {}).get('gap_px', geometry['arrow_thumb_gap_px'])
    arrow_shadow = parts.get('arrow', {}).get('shadow_px', geometry['shadow_px'])
    thumb_shadow = parts.get('thumb', {}).get('shadow_px', geometry['shadow_px'])
    for value, size in ((arrow_shadow, glyph), (thumb_shadow, properties['slider-width'])):
        if type(value) is not int or value < 0 or 2 * value >= size:
            raise ValueError('GTK2: piece shadow must fit within its native allocation')
    geometry.update(arrow_px=glyph, shadow_px=arrow_shadow)
    return properties, geometry, glyph, gap, arrow_shadow, thumb_shadow


def paint_scrollbars(builder, recipe, palette, destination):
    """Write effective KDE-derived native pixmaps and their GTK2 engine contract."""
    from pathlib import Path
    properties, geometry, glyph, gap, arrow_shadow, thumb_shadow = paint_contract(recipe)
    parts = recipe.get("scrollbar_parts", {})
    # GTK2 caches RC styles by their names. Theme Lab reparses snapshots in the
    # same GTK process when the user changes a palette or a recipe; reusing a
    # fixed style name can leave the old pixmap colors attached to new widgets.
    # Give each effective recipe/palette its own deterministic native style ID.
    style_payload = {'geometry': recipe.get('geometry', {}),
                     'palette_recipe': recipe.get('palette', {}),
                     'scrollbar_parts': parts,
                     'effective_palette': palette}
    style_id = hashlib.sha256(json.dumps(
        style_payload, sort_keys=True, separators=(',', ':'), default=str
    ).encode('utf-8')).hexdigest()[:16]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    art = builder.art
    # Exact effective KDE role variants must be provided by the native reader.
    for family in ('button', 'button-fg'):
        for name in art.ROLES[family]:
            if name not in palette:
                raise ValueError('GTK2 missing effective state role: ' + name)
    from gtk2_canvas import canvas_rc
    canvas_style = canvas_rc(art, palette)
    files = {}
    for state in ('normal', 'pressed', 'disabled', 'backdrop'):
        state_palette = dict(palette)
        index = 2 if state == 'disabled' else 1 if state == 'backdrop' else 0
        for names in art.ROLES.values():
            if names[index] in palette: state_palette[names[0]] = palette[names[index]]
        assets = {}
        for direction in ('up', 'down', 'left', 'right'):
            relief = parts.get('arrow', {}).get('state_relief', {}).get(state)
            cell = properties['slider-width'] + 2 * properties['trough-border']
            cell_shadow = properties['trough-border']
            # The measured 15/2/11 case uses the complete SR10.4 semantic
            # cell. Other recipe sizes retain a role-derived bevel and a
            # nearest-neighbour glyph inside the same native allocation.
            if cell == glyph + 2 * cell_shadow:
                pixels = art.kvantum_scrollbar_stepper(
                    state, direction, bar_px=cell, shadow_px=cell_shadow,
                    arrow_px=glyph)
            else:
                pixels = art.blank(cell, cell, 'trough')
                art.bevel(pixels, thickness=cell_shadow, down=True)
                source = art.kvantum_scrollbar_triangle(state, direction)
                size = len(source)
                offset = (cell - glyph) // 2
                for y in range(glyph):
                    for x in range(glyph):
                        token = source[min(size - 1, y * size // glyph)][min(size - 1, x * size // glyph)]
                        if token is not None:
                            pixels[offset + y][offset + x] = token
            if relief:
                # Explicit piece relief overrides GTK's pressed default, but
                # only the triangular mask changes; the full cell junction
                # and its KDE-derived border stay intact.
                source = art.kvantum_scrollbar_triangle('normal', direction)
                size = len(source)
                offset = (cell - glyph) // 2
                swaps = {'light': 'dark', 'dark': 'light'} if relief == 'sunken' else {}
                for y in range(glyph):
                    for x in range(glyph):
                        token = source[min(size - 1, y * size // glyph)][min(size - 1, x * size // glyph)]
                        if token is not None:
                            pixels[offset + y][offset + x] = (
                                'face' if relief == 'flat' else swaps.get(token, token))
            assets['arrow-' + direction] = (pixels, 0)
        extent = 2 * (properties['stepper-size'] + properties['stepper-spacing'])
        junctions = art.gtk2_stepper_trough_junctions()
        for name, down in (('trough', True), ('thumb', False)):
            border = properties['trough-border'] if name == 'trough' else thumb_shadow
            edit_state = 'normal' if name == 'trough' and state == 'pressed' else state
            relief = parts.get(name, {}).get('state_relief', {}).get(edit_state)
            pixels = art.bevel(art.blank(extent, extent, 'face'),
                               thickness=border, down=relief == 'sunken' if relief else down)
            if relief == 'flat': pixels = art.blank(extent, extent, 'face')
            assets[name] = (pixels, border)
            if name == 'trough' and (properties['stepper-size'], border) == (15, 2):
                for orientation in ('horizontal', 'vertical'):
                    width, height = ((extent, properties['stepper-size'])
                                     if orientation == 'horizontal' else
                                     (properties['stepper-size'], extent))
                    oriented = art.bevel(art.blank(width, height, 'face'),
                                         thickness=border,
                                         down=relief == 'sunken' if relief else down)
                    if relief == 'flat':
                        oriented = art.blank(width, height, 'face')
                    # The source VUE trough has a measured 15px cross-axis
                    # profile through its stretched body. Use the same
                    # role-derived profile as the installed GTK2 adapter.
                    cross_profile = junctions.get(
                        'gtk2_adaptation_cross_axis_profile',
                        junctions['normal_cross_axis_profile'])
                    if relief == 'flat':
                        cross_profile = tuple('face' for _ in cross_profile)
                    elif relief == 'raised':
                        cross_profile = tuple(
                            {'dark': 'light', 'light': 'dark'}.get(token, token)
                            for token in cross_profile)
                    if orientation == 'horizontal':
                        for x in range(5, width - 5):
                            for y, token in enumerate(cross_profile):
                                oriented[y][x] = token
                    else:
                        for y in range(5, height - 5):
                            for x, token in enumerate(cross_profile):
                                oriented[y][x] = token
                    if orientation == 'horizontal':
                        for y, row in enumerate(junctions['horizontal_start_rows']):
                            oriented[y][:5] = row
                        for y, row in enumerate(junctions['horizontal_end_rows']):
                            oriented[y][-5:] = row
                        cap_border = (5, 5, 2, 2)
                    else:
                        for y, row in enumerate(junctions['vertical_start_rows']):
                            oriented[y][:] = row
                        for y, row in enumerate(junctions['vertical_end_rows']):
                            oriented[-5 + y][:] = row
                        cap_border = (2, 2, 5, 5)
                    assets['trough-' + orientation] = (oriented, cap_border)
        for name, (pixels, border) in assets.items():
            filename = name + '-' + state + '.png'
            (destination / filename).write_bytes(builder.png(pixels, 'button', state_palette))
            files[(name, state)] = (filename, border)

    def style(name, disabled_parent=False, inactive=False, geometry_style=None):
        result = ['style "' + name + '" = "' +
                  (geometry_style or 'theme-lab-gtk2-scroll-geometry') + '" {']
        role_index = 2 if disabled_parent else 1 if inactive else 0
        face = art._rgb(palette[art.ROLES['button'][role_index]])
        face = '#%02x%02x%02x' % face
        for gtk_state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            result.append('  bg[' + gtk_state + '] = "' + face + '"')
        if 'pressed' in parts.get('thumb', {}).get('state_relief', {}):
            result.append('  GtkRange::activate-slider = 1')
        result.append('  engine "pixmap" {')
        for gtk_state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            state = ('disabled' if disabled_parent else 'backdrop' if inactive else
                     'pressed' if gtk_state == 'ACTIVE' else 'normal')
            from gtk2_rc_fragments import image_rules
            result.extend(image_rules(files, gtk_state, state))
        return result + ['  }', '}']

    geometry_style = 'theme-lab-gtk2-scroll-geometry-' + style_id
    paint_style = 'theme-lab-gtk2-scroll-paint-' + style_id
    insensitive_style = 'theme-lab-gtk2-scroll-insensitive-' + style_id
    backdrop_style = 'theme-lab-gtk2-scroll-backdrop-' + style_id
    lines = [canvas_style, scrollbar_rc(recipe, style_id)]
    lines += style(paint_style, geometry_style=geometry_style)
    lines += style(insensitive_style, disabled_parent=True, geometry_style=geometry_style)
    lines += style(backdrop_style, inactive=True, geometry_style=geometry_style)
    lines += ['class "GtkScrollbar" style : highest "' + paint_style + '"',
              'widget "*themeLabInsensitiveScroll" style : highest "' + insensitive_style + '"',
              'widget "*themeLabBackdropScroll" style : highest "' + backdrop_style + '"', '']
    rc = destination / 'gtkrc'
    rc.write_text('\n'.join(lines), encoding='utf-8')
    return {'rc': str(rc), 'geometry_properties': properties,
            'scrollbar_style_id': style_id,
            'assets': [item[0] for item in files.values()],
            'scope': 'Private GTK2 scrollbar paint only; no scene integration or visual approval',
            'whole_insensitive_requires_widget_name': 'themeLabInsensitiveScroll',
            'backdrop_requires_widget_name': 'themeLabBackdropScroll'}
