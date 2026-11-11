# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt6 Widgets scrollbar recipe rendered from KDE roles and the shared contract."""
from __future__ import annotations

import json
from pathlib import Path

import backend


STATES = ('normal', 'pressed', 'backdrop', 'disabled')
DIRECTIONS = {
    'up': ('sub-line', 'vertical'),
    'down': ('add-line', 'vertical'),
    'left': ('sub-line', 'horizontal'),
    'right': ('add-line', 'horizontal'),
}


def contract():
    """Load the one source of scrollbar geometry; do not copy local defaults."""
    source = backend.ROOT / 'tools/domainos_scrollbar_rules.json'
    rules = json.loads(backend.read_file(source))
    geometry = rules['geometry']
    if (rules.get('schema_version') != 1 or geometry.get('unit') != 'native_pixel' or
            geometry.get('bar_px') != geometry.get('arrow_px') + 2 * geometry.get('shadow_px') or
            geometry.get('thumb_cross_px') != geometry.get('arrow_px')):
        raise ValueError('Qt6 scrollbar shared contract is invalid')
    return rules


def _rgb8(value):
    return [int(value[n:n+2], 16) for n in (1, 3, 5)]


def _png(pixels, art, palette, *, inactive=False, disabled=False):
    from PIL import Image
    image = Image.new('RGBA', (len(pixels[0]), len(pixels)))
    for y, row in enumerate(pixels):
        for x, token in enumerate(row):
            if token is None:
                continue
            color = art.evaluate(art.pixel_plan('button', token,
                                 inactive=inactive, disabled=disabled), palette)
            image.putpixel((x, y), tuple(_rgb8(color)) + (255,))
    from io import BytesIO
    stream = BytesIO()
    image.save(stream, format='PNG', optimize=True)
    return stream.getvalue()


def _translated_colors(builder, recipe, palette, state, family, tokens):
    with backend.recipe_rules(builder, recipe['palette']):
        return {token: builder.art.evaluate(builder.art.pixel_plan(
                    family, token, inactive=state == 'backdrop',
                    disabled=state == 'disabled'), palette)
                for token in tokens}


def _selector(axis, name, pseudo=''):
    return f'QScrollBar#domainosScrollBar{name}:{axis}{pseudo}'


def _line_selector(axis, name, subcontrol, parent_state='', part_state=''):
    """Qt QSS puts orientation after the subcontrol selector."""
    return (f'QScrollBar#domainosScrollBar{name}{parent_state}::'
            f'{subcontrol}:{axis}{part_state}')


def _stepper_pixels(art, state, direction, geometry):
    """Return a pixel-exact cell at the recipe's current native dimensions.

    The measured 15/2/11 cell stays byte-for-byte sourced from the shared
    DomainOS art. Other odd glyph sizes are nearest-neighbour resized before
    being framed, so Qt never smooth-scales a bitmap to fit the subcontrol.
    """
    bar = geometry['bar_px']
    shadow = geometry['shadow_px']
    arrow = geometry['arrow_px']
    if (bar, shadow, arrow) == (15, 2, 11):
        return art.kvantum_scrollbar_stepper(state, direction)
    if (type(bar) is not int or type(shadow) is not int or type(arrow) is not int or
            bar != arrow + 2 * shadow or arrow < 3 or not arrow & 1 or shadow < 0):
        raise ValueError('Qt6 scrollbar geometry requires an odd arrow, nonnegative relief, and bar = arrow + 2 × relief.')

    source = art.kvantum_scrollbar_triangle(state, direction)
    source_size = len(source)
    glyph = [[source[min(source_size - 1, (y * source_size) // arrow)]
                    [min(source_size - 1, (x * source_size) // arrow)]
              for x in range(arrow)] for y in range(arrow)]
    cell = art.blank(bar, bar, 'trough')
    art.bevel(cell, thickness=shadow, down=True)
    for y, row in enumerate(glyph):
        for x, token in enumerate(row):
            if token is not None:
                cell[y + shadow][x + shadow] = token
    return cell


def generate(root, folder, model, project_hash, kdeglobals, family='qt6'):
    """Generate a private Qt5/Qt6 stylesheet and role-derived arrow cells."""
    if family not in ('qt5', 'qt6'):
        raise ValueError('Qt scrollbar recipe family must be qt5 or qt6.')
    rules = contract()
    recipe = model['recipes'][family]
    active = {key: value for key, value in recipe.get('scrollbar_parts', {}).items() if value}
    if active:
        raise backend.Unavailable(
            f'{family.upper()} translates the shared scrollbar geometry; custom per-piece overrides remain pending.')
    from scene_contract import scene
    records = scene(model, family)
    ids = {row['id'] for row in records}
    supported = {'scroll_h', 'scroll_v'} | {
        'push', 'toggle', 'check', 'radio', 'entry', 'text', 'combo', 'spin',
        'scale_h', 'scale_v', 'arrow', 'progress', 'list', 'frame'}
    scroll_ids = ids.intersection({'scroll_h', 'scroll_v'})
    if not ids or ids - supported:
        names = ', '.join(sorted(supported))
        raise backend.Unavailable(f'{family.upper()} partial recipe accepts only visible {names} controls.')

    builder = backend.load_builder(root)
    _config, selected = backend.selected_palette(model, kdeglobals, root)
    palette, origin = backend.native_roles(root, Path(selected['path']), builder.art,
                                           selected['sha256'])
    origin = dict(origin)
    origin['selection_scope'] = (f'Qt{family[-1]} private partial Widgets recipe only; '
                                 'no host/profile scheme change')
    folder = backend.private_output(Path(folder), root)
    asset_dir = backend.private_output(folder / f'{family}-scrollbar-assets', root)
    geometry = dict(rules['geometry'])
    geometry.update(recipe['geometry'])
    geometry['view_bar_gap_px'] = recipe['geometry']['view_bar_gap_px']
    bar, shadow, thumb = geometry['bar_px'], geometry['shadow_px'], geometry['thumb_cross_px']

    qss = []
    if scroll_ids:
        assets = {}
        for state in STATES:
            inactive, disabled = state == 'backdrop', state == 'disabled'
            assets[state] = {}
            for direction in DIRECTIONS:
                with backend.recipe_rules(builder, recipe['palette']):
                    pixels = _stepper_pixels(builder.art, state, direction, geometry)
                    payload = _png(pixels, builder.art, palette,
                                   inactive=inactive, disabled=disabled)
                name = f'arrow-{direction}-{state}.png'
                path = asset_dir / name
                path.write_bytes(payload)
                assets[state][direction] = path

    if scroll_ids:
        for state in ('normal', 'backdrop', 'disabled'):
            colors = _translated_colors(builder, recipe, palette, state, 'button',
                                        ('face', 'light', 'dark', 'trough'))
            pseudo = {'normal': '', 'pressed': ':pressed',
                      'backdrop': ':!active', 'disabled': ':disabled'}[state]
            for axis in ('vertical', 'horizontal'):
                transverse = 'width' if axis == 'vertical' else 'height'
                cross_first = 'left' if axis == 'vertical' else 'top'
                cross_last = 'right' if axis == 'vertical' else 'bottom'
                qss.extend([
                    f'{_selector(axis, "Vertical" if axis == "vertical" else "Horizontal", pseudo)} {{',
                    f'  {transverse}: {bar}px;',
                    f'  background-color: {colors["trough"]};',
                    f'  border-{cross_first}: {shadow}px solid {colors["dark"]};',
                    f'  border-{cross_last}: {shadow}px solid {colors["light"]};',
                    '  margin: 0px;',
                    '}',
                    f'{_selector(axis, "Vertical" if axis == "vertical" else "Horizontal", pseudo)}::handle {{',
                    f'  {transverse}: {thumb}px;',
                    f'  min-{"height" if axis == "vertical" else "width"}: {thumb}px;',
                    f'  background-color: {colors["face"]};',
                    f'  border-top: {shadow}px solid {colors["light"]};',
                    f'  border-left: {shadow}px solid {colors["light"]};',
                    f'  border-bottom: {shadow}px solid {colors["dark"]};',
                    f'  border-right: {shadow}px solid {colors["dark"]};',
                    f'  margin: {geometry["arrow_thumb_gap_px"]}px;',
                    '}',
                    f'{_selector(axis, "Vertical" if axis == "vertical" else "Horizontal", pseudo)}::add-page,',
                    f'{_selector(axis, "Vertical" if axis == "vertical" else "Horizontal", pseudo)}::sub-page {{',
                    f'  background-color: {colors["trough"]}; border: none;',
                    '}',
                ])
        for direction, (subcontrol, axis) in DIRECTIONS.items():
            axis_name = 'Vertical' if axis == 'vertical' else 'Horizontal'
            position = ({'up': 'top', 'down': 'bottom', 'left': 'left', 'right': 'right'}[direction])
            cross_size = bar
            along_size = bar
            for state in STATES:
                colors = _translated_colors(builder, recipe, palette, state, 'button',
                                            ('face', 'light', 'dark', 'trough'))
                # Qt Style Sheets treats background-image as a filesystem path;
                # unlike QML/GTK CSS it does not load file:// URLs here.
                url = str(assets[state][direction].resolve())
                parent_state = ':!active' if state == 'backdrop' else ':disabled' if state == 'disabled' else ''
                part_state = ':pressed' if state == 'pressed' else ''
                selector = _line_selector(axis, axis_name, subcontrol,
                                          parent_state, part_state)
                disabled_selector = _line_selector(axis, axis_name, subcontrol,
                                                   parent_state, ':disabled')
                declarations = [
                    f'  width: {cross_size}px; height: {along_size}px;',
                    '  subcontrol-origin: margin;',
                    f'  subcontrol-position: {position};',
                    f'  background-image: url("{url}");',
                    '  background-repeat: no-repeat; background-position: center;',
                    f'  background-color: {colors["trough"]}; border: none; padding: 0px; margin: 0px;',
                ]
                qss.extend([
                    selector + ' {',
                    *declarations,
                    '}',
                    disabled_selector + ' {',
                    *declarations,
                    '}',
                ])
            arrow_name = {'up': 'up-arrow', 'down': 'down-arrow',
                          'left': 'left-arrow', 'right': 'right-arrow'}[direction]
            qss.extend([
                _line_selector(axis, axis_name, arrow_name, parent_state) + ' {',
                '  width: 0px; height: 0px; image: none; border: none; padding: 0px; margin: 0px;',
                '}',
            ])
        view_colors = _translated_colors(builder, recipe, palette, 'normal', 'window',
                                         ('light', 'dark'))
        view_face = _translated_colors(builder, recipe, palette, 'normal', 'view', ('face',))['face']
        qss.extend([
            'QScrollArea#domainosScrollArea {',
            f'  border-top: {geometry["view_inset_px"]}px solid {view_colors["dark"]};',
            f'  border-left: {geometry["view_inset_px"]}px solid {view_colors["dark"]};',
            f'  border-bottom: {geometry["view_inset_px"]}px solid {view_colors["light"]};',
            f'  border-right: {geometry["view_inset_px"]}px solid {view_colors["light"]};',
            '}',
            f'QAbstractScrollArea#domainosScrollArea {{',
            f'  background-color: {view_face};',
            '}',
        ])
    if family in ('qt5', 'qt6') and 'check' in ids:
        check_colors = _translated_colors(builder, recipe, palette, 'normal', 'button',
                                          ('trough', 'ink'))
        selector = 'QCheckBox#domainosRecipeCheckBox'
        qss.extend([
            selector + ' {',
            f'  color: {check_colors["ink"]};',
            '  spacing: 4px;',
            '}',
            selector + '::indicator {',
            f'  width: {len(builder.art.toggle("check"))}px;',
            f'  height: {len(builder.art.toggle("check"))}px;',
            f'  background-color: {check_colors["trough"]};',
            '  border: none; padding: 0px; margin: 0px;',
            '}',
        ])
        for state in STATES:
            inactive, disabled = state == 'backdrop', state == 'disabled'
            state_name = 'normal' if state == 'backdrop' else state
            state_art = 'pressed' if state == 'pressed' else state_name
            for checked in (False, True):
                pixels = builder.art.toggle('check', state_art, selected=checked)
                payload = _png(pixels, builder.art, palette,
                               inactive=inactive, disabled=disabled)
                name = f'check-{"on" if checked else "off"}-{state}.png'
                path = asset_dir / name
                path.write_bytes(payload)
                pseudo = {'normal': '', 'pressed': ':pressed',
                          'backdrop': ':!active', 'disabled': ':disabled'}[state]
                checked_pseudo = ':checked' if checked else ':unchecked'
                url = str(path.resolve())
                qss.extend([
                    selector + '::indicator' + pseudo + checked_pseudo + ' {',
                    f'  image: url("{url}");',
                    f'  background-color: {check_colors["trough"]};',
                    '}',
                ])
    if family in ('qt5', 'qt6') and 'radio' in ids:
        radio_colors = _translated_colors(builder, recipe, palette, 'normal', 'button',
                                          ('trough', 'ink'))
        selectors = ['QRadioButton#domainosRecipeRadioButton::indicator',
                     'QRadioButton#domainosRecipeRadioPeer::indicator']
        selector = ', '.join(selectors)
        qss.extend([
            'QRadioButton#domainosRecipeRadioButton, QRadioButton#domainosRecipeRadioPeer {',
            f'  color: {radio_colors["ink"]};',
            '  spacing: 4px;',
            '}',
            selector + ' {',
            f'  width: {len(builder.art.toggle("radio"))}px;',
            f'  height: {len(builder.art.toggle("radio"))}px;',
            f'  background-color: {radio_colors["trough"]};',
            '  border: none; padding: 0px; margin: 0px;',
            '}',
        ])
        for state in STATES:
            inactive, disabled = state == 'backdrop', state == 'disabled'
            state_name = 'normal' if state == 'backdrop' else state
            state_art = 'pressed' if state == 'pressed' else state_name
            for checked in (False, True):
                pixels = builder.art.toggle('radio', state_art, selected=checked)
                payload = _png(pixels, builder.art, palette,
                               inactive=inactive, disabled=disabled)
                name = f'radio-{"on" if checked else "off"}-{state}.png'
                path = asset_dir / name
                path.write_bytes(payload)
                pseudo = {'normal': '', 'pressed': ':pressed',
                          'backdrop': ':!active', 'disabled': ':disabled'}[state]
                checked_pseudo = ':checked' if checked else ':!checked'
                url = str(path.resolve())
                qss.extend([
                    ', '.join(item + pseudo + checked_pseudo for item in selectors) + ' {',
                    f'  image: url("{url}");',
                    f'  background-color: {radio_colors["trough"]};',
                    '}',
                ])
    if family in ('qt5', 'qt6') and 'entry' in ids:
        selector = 'QLineEdit#domainosRecipeEntry'
        padding = geometry['control_padding_px']
        for state in ('normal', 'backdrop', 'disabled'):
            view = _translated_colors(builder, recipe, palette, state, 'view', ('face', 'ink'))
            relief = _translated_colors(builder, recipe, palette, state, 'window', ('light', 'dark'))
            selection = _translated_colors(builder, recipe, palette, state, 'selection', ('face', 'ink'))
            pseudo = {'normal': '', 'backdrop': ':!active', 'disabled': ':disabled'}[state]
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {view["ink"]};',
                f'  background-color: {view["face"]};',
                f'  selection-background-color: {selection["face"]};',
                f'  selection-color: {selection["ink"]};',
                f'  border-top: {shadow}px solid {relief["dark"]};',
                f'  border-left: {shadow}px solid {relief["dark"]};',
                f'  border-bottom: {shadow}px solid {relief["light"]};',
                f'  border-right: {shadow}px solid {relief["light"]};',
                '  border-radius: 0px;',
                f'  padding: {padding}px;',
                '}',
            ])
        focus = _translated_colors(builder, recipe, palette, 'normal', 'focus',
                                   ('light', 'dark'))
        qss.extend([
            selector + ':focus {',
            f'  border-top: {shadow}px solid {focus["dark"]};',
            f'  border-left: {shadow}px solid {focus["dark"]};',
            f'  border-bottom: {shadow}px solid {focus["light"]};',
            f'  border-right: {shadow}px solid {focus["light"]};',
            '}',
        ])
    if family in ('qt5', 'qt6') and 'text' in ids:
        selector = 'QTextEdit#domainosRecipeText'
        padding = geometry['control_padding_px']
        for state in ('normal', 'backdrop', 'disabled'):
            view = _translated_colors(builder, recipe, palette, state, 'view', ('face', 'ink'))
            relief = _translated_colors(builder, recipe, palette, state, 'window', ('light', 'dark'))
            selection = _translated_colors(builder, recipe, palette, state, 'selection', ('face', 'ink'))
            if state == 'normal':
                pseudo = ''
            elif state == 'disabled':
                pseudo = ':disabled'
            elif family == 'qt6':
                pseudo = '[domainosBackdrop="true"]'
            else:
                pseudo = ':!active'
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {view["ink"]};',
                f'  background-color: {view["face"]};',
                f'  selection-background-color: {selection["face"]};',
                f'  selection-color: {selection["ink"]};',
                f'  border-top: {shadow}px solid {relief["dark"]};',
                f'  border-left: {shadow}px solid {relief["dark"]};',
                f'  border-bottom: {shadow}px solid {relief["light"]};',
                f'  border-right: {shadow}px solid {relief["light"]};',
                '  border-radius: 0px;',
                f'  padding: {padding}px;',
                '}',
            ])
        focus = _translated_colors(builder, recipe, palette, 'normal', 'focus',
                                   ('light', 'dark'))
        qss.extend([
            selector + ':focus {',
            f'  border-top: {shadow}px solid {focus["dark"]};',
            f'  border-left: {shadow}px solid {focus["dark"]};',
            f'  border-bottom: {shadow}px solid {focus["light"]};',
            f'  border-right: {shadow}px solid {focus["light"]};',
            '}',
        ])
    if family in ('qt5', 'qt6') and 'arrow' in ids:
        selector = 'QToolButton#domainosRecipeArrow'
        glyph_size = geometry['arrow_px']
        outer_size = glyph_size + 2 * shadow
        qss_content_size = glyph_size if family == 'qt6' else outer_size
        arrow_assets = {}
        for state in STATES:
            inactive, disabled = state == 'backdrop', state == 'disabled'
            arrow_state = 'normal' if state == 'backdrop' else state
            pixels = builder.gtk3_arrow(arrow_state, 'down', geometry=geometry)
            payload = _png(pixels, builder.art, palette,
                           inactive=inactive, disabled=disabled)
            path = asset_dir / f'standalone-arrow-down-{state}.png'
            path.write_bytes(payload)
            arrow_assets[state] = path
        for state in ('normal', 'backdrop', 'disabled'):
            colors = _translated_colors(builder, recipe, palette, state,
                                        'button', ('face', 'light', 'dark', 'ink'))
            pseudo = {'normal': '', 'backdrop': '[domainosBackdrop="true"]' if family == 'qt6' else ':!active',
                      'disabled': ':disabled'}[state]
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {colors["ink"]};',
                f'  background-color: {colors["face"]};',
                f'  border-top: {shadow}px solid {colors["light"]};',
                f'  border-left: {shadow}px solid {colors["light"]};',
                f'  border-bottom: {shadow}px solid {colors["dark"]};',
                f'  border-right: {shadow}px solid {colors["dark"]};',
                '  border-radius: 0px;',
                '  padding: 0px; margin: 0px;',
                f'  min-width: {qss_content_size}px; min-height: {qss_content_size}px;',
                f'  max-width: {qss_content_size}px; max-height: {qss_content_size}px;',
                '}',
            ])
        pressed = _translated_colors(builder, recipe, palette, 'pressed',
                                    'button', ('face', 'light', 'dark', 'ink'))
        qss.extend([
            selector + ':pressed {',
            f'  color: {pressed["ink"]};',
            f'  background-color: {pressed["face"]};',
            f'  border-top: {shadow}px solid {pressed["dark"]};',
            f'  border-left: {shadow}px solid {pressed["dark"]};',
            f'  border-bottom: {shadow}px solid {pressed["light"]};',
            f'  border-right: {shadow}px solid {pressed["light"]};',
            '}',
        ])
        focus = _translated_colors(builder, recipe, palette, 'normal', 'focus',
                                   ('light', 'dark'))
        qss.extend([
            selector + ':focus {',
            f'  border-top: {shadow}px solid {focus["dark"]};',
            f'  border-left: {shadow}px solid {focus["dark"]};',
            f'  border-bottom: {shadow}px solid {focus["light"]};',
            f'  border-right: {shadow}px solid {focus["light"]};',
            '}',
        ])
    if family in ('qt5', 'qt6') and 'progress' in ids:
        selector = 'QProgressBar#domainosRecipeProgress'
        shadow = geometry['shadow_px']
        for state in ('normal', 'backdrop', 'disabled'):
            inactive, disabled = state == 'backdrop', state == 'disabled'
            trough = _translated_colors(builder, recipe, palette, state, 'view',
                                        ('face', 'light', 'dark', 'ink'))
            fill = _translated_colors(builder, recipe, palette, state, 'selection',
                                      ('face', 'light', 'dark'))
            pseudo = f'[domainosState="{state}"]'
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {trough["ink"]};',
                f'  background-color: {trough["face"]};',
                f'  border-top: {shadow}px solid {trough["dark"]};',
                f'  border-left: {shadow}px solid {trough["dark"]};',
                f'  border-bottom: {shadow}px solid {trough["light"]};',
                f'  border-right: {shadow}px solid {trough["light"]};',
                '  border-radius: 0px; padding: 0px; text-align: center;',
                '}',
                selector + pseudo + '::chunk {',
                f'  background-color: {fill["face"]};',
                f'  border-top: {shadow}px solid {fill["light"]};',
                f'  border-left: {shadow}px solid {fill["light"]};',
                f'  border-bottom: {shadow}px solid {fill["dark"]};',
                f'  border-right: {shadow}px solid {fill["dark"]};',
                '  border-radius: 0px; margin: 0px;',
                '}',
            ])
        focus = _translated_colors(builder, recipe, palette, 'normal', 'focus',
                                   ('light', 'dark'))
        qss.extend([
            selector + '[domainosState="focused"] {',
            f'  border-top: {shadow}px solid {focus["dark"]};',
            f'  border-left: {shadow}px solid {focus["dark"]};',
            f'  border-bottom: {shadow}px solid {focus["light"]};',
            f'  border-right: {shadow}px solid {focus["light"]};',
            '}',
        ])
    if family in ('qt5', 'qt6') and 'frame' in ids:
        selector = 'QFrame#domainosRecipeFrame'
        padding = geometry['control_padding_px']
        for state in ('normal', 'backdrop', 'disabled'):
            view = _translated_colors(builder, recipe, palette, state, 'view',
                                      ('face', 'ink'))
            relief = _translated_colors(builder, recipe, palette, state, 'window',
                                        ('light', 'dark'))
            pseudo = ({'normal': '', 'backdrop': ':!active', 'disabled': ':disabled'}[state]
                      if family == 'qt5' else
                      {'normal': '', 'backdrop': '[domainosBackdrop="true"]',
                       'disabled': ':disabled'}[state])
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {view["ink"]};',
                f'  background-color: {view["face"]};',
                f'  border-top: {shadow}px solid {relief["dark"]};',
                f'  border-left: {shadow}px solid {relief["dark"]};',
                f'  border-bottom: {shadow}px solid {relief["light"]};',
                f'  border-right: {shadow}px solid {relief["light"]};',
                '  border-radius: 0px;',
                f'  padding: {padding}px;',
                '}',
            ])
    if family == 'qt5' and 'list' in ids:
        selector = 'QTreeWidget#domainosRecipeList'
        padding = geometry['control_padding_px']
        for state in ('normal', 'backdrop', 'disabled'):
            view = _translated_colors(builder, recipe, palette, state, 'view',
                                      ('face', 'ink'))
            selection = _translated_colors(builder, recipe, palette, state,
                                           'selection', ('face', 'ink'))
            relief = _translated_colors(builder, recipe, palette, state, 'window',
                                        ('light', 'dark'))
            pseudo = {'normal': '', 'backdrop': ':!active',
                      'disabled': ':disabled'}[state]
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {view["ink"]};',
                f'  background-color: {view["face"]};',
                f'  selection-background-color: {selection["face"]};',
                f'  selection-color: {selection["ink"]};',
                f'  border-top: {shadow}px solid {relief["dark"]};',
                f'  border-left: {shadow}px solid {relief["dark"]};',
                f'  border-bottom: {shadow}px solid {relief["light"]};',
                f'  border-right: {shadow}px solid {relief["light"]};',
                '  border-radius: 0px; outline: none;',
                f'  padding: {padding}px;',
                '}',
                selector + pseudo + '::item {',
                f'  color: {view["ink"]};',
                f'  background-color: {view["face"]};',
                '  border: none; border-radius: 0px;',
                f'  padding: {padding}px;',
                '}',
                selector + pseudo + '::item:selected {',
                f'  background-color: {selection["face"]};',
                f'  color: {selection["ink"]};',
                '}',
            ])
        focus = _translated_colors(builder, recipe, palette, 'normal', 'focus',
                                   ('light', 'dark'))
        qss.extend([
            selector + ':focus {',
            f'  border-top: {shadow}px solid {focus["dark"]};',
            f'  border-left: {shadow}px solid {focus["dark"]};',
            f'  border-bottom: {shadow}px solid {focus["light"]};',
            f'  border-right: {shadow}px solid {focus["light"]};',
            '}',
        ])
    if (family == 'qt5' and ids.intersection({'scale_h', 'scale_v'})) or (family == 'qt6' and ids.intersection({'scale_h', 'scale_v'})):
        scale_cross = geometry['thumb_cross_px'] + 2 * shadow
        groove_cross = 2 * shadow + 3
        scale_specs = (
            ('scale_h', 'QSlider#domainosRecipeScaleHorizontal', 'horizontal'),
            ('scale_v', 'QSlider#domainosRecipeScaleVertical', 'vertical'),
        )
        for control, selector, orientation in scale_specs:
            if control not in ids:
                continue
            if family == 'qt6':
                # QSS dimensions describe the handle's content box; its two
                # relief borders add to the painted height. Reserve that full
                # cross-axis space so Qt does not clip the real handle.
                qss.extend([
                    selector + ' {',
                    f'  min-{"height" if orientation == "horizontal" else "width"}: {scale_cross + 2 * shadow}px;',
                    '}',
                ])
            for state in ('normal', 'backdrop', 'disabled'):
                trough = _translated_colors(builder, recipe, palette, state,
                                            'button', ('face', 'light', 'dark'))
                if state == 'normal':
                    state_selector = ''
                elif state == 'disabled':
                    state_selector = ':disabled'
                elif family == 'qt6':
                    # QSS :!active matches an idle QSlider as well, so it
                    # overrides the normal rule even while the window is
                    # active. Use a property synchronized from window events.
                    state_selector = '[domainosBackdrop="true"]'
                else:
                    # This Qt6-specific correction must not alter Qt5's
                    # separate, already-tested selector mapping.
                    state_selector = ':!active'
                orient = ':' + orientation
                if family == 'qt6':
                    groove_selector = selector + state_selector + '::groove' + orient
                    handle_selector = selector + state_selector + '::handle' + orient
                else:
                    # Keep Qt5's established ordering: QSS subcontrol first,
                    # then orientation and state.
                    pseudo = {'normal': '', 'backdrop': ':!active',
                              'disabled': ':disabled'}[state]
                    groove_selector = selector + '::groove' + orient + pseudo
                    handle_selector = selector + '::handle' + orient + pseudo
                qss.extend([
                    groove_selector + ' {',
                    f'  {"height" if orientation == "horizontal" else "width"}: {groove_cross}px;',
                    f'  background-color: {trough["face"]};',
                    f'  border-top: {shadow}px solid {trough["dark"]};',
                    f'  border-left: {shadow}px solid {trough["dark"]};',
                    f'  border-bottom: {shadow}px solid {trough["light"]};',
                    f'  border-right: {shadow}px solid {trough["light"]};',
                    '  border-radius: 0px;',
                    '}',
                ])
                handle = _translated_colors(builder, recipe, palette, state,
                                           'button', ('face', 'light', 'dark'))
                upper, lower = handle['light'], handle['dark']
                qss.extend([
                    handle_selector + ' {',
                    f'  {"width" if orientation == "horizontal" else "height"}: {scale_cross}px;',
                    f'  {"height" if orientation == "horizontal" else "width"}: {scale_cross}px;',
                    f'  background-color: {handle["face"]};',
                    f'  border-top: {shadow}px solid {upper};',
                    f'  border-left: {shadow}px solid {upper};',
                    f'  border-bottom: {shadow}px solid {lower};',
                    f'  border-right: {shadow}px solid {lower};',
                    '  border-radius: 0px;',
                    f'  margin: {-(scale_cross - groove_cross) // 2}px 0px;' if orientation == 'horizontal' else
                    f'  margin: 0px {-(scale_cross - groove_cross) // 2}px;',
                ])
                qss.append('}')
            focus = _translated_colors(builder, recipe, palette, 'normal', 'focus',
                                       ('light', 'dark'))
            qss.extend([
                selector + '::handle' + ':' + orientation + ':focus {',
                f'  border-top: {shadow}px solid {focus["dark"]};',
                f'  border-left: {shadow}px solid {focus["dark"]};',
                f'  border-bottom: {shadow}px solid {focus["light"]};',
                f'  border-right: {shadow}px solid {focus["light"]};',
                '}',
            ])
    if family in ('qt5', 'qt6') and 'combo' in ids:
        selector = 'QComboBox#domainosRecipeCombo'
        popup = 'QAbstractItemView#domainosRecipeComboPopup'
        padding = geometry['control_padding_px']
        arrow_size = geometry['arrow_px']
        drop_width = arrow_size + 2 * shadow
        combo_padding = (f'{padding}px {drop_width + padding}px {padding}px {padding}px'
                         if family == 'qt6' else f'{padding}px')
        combo_assets = {}
        for state in STATES:
            inactive, disabled = state == 'backdrop', state == 'disabled'
            arrow_state = 'normal' if state == 'backdrop' else state
            pixels = builder.gtk3_arrow(arrow_state, 'down', geometry=geometry)
            payload = _png(pixels, builder.art, palette,
                           inactive=inactive, disabled=disabled)
            path = asset_dir / f'combo-arrow-down-{state}.png'
            path.write_bytes(payload)
            combo_assets[state] = path

        for state in ('normal', 'backdrop', 'disabled'):
            colors = _translated_colors(builder, recipe, palette, state, 'button',
                                        ('face', 'light', 'dark', 'ink'))
            pseudo = {'normal': '', 'backdrop': ':!active', 'disabled': ':disabled'}[state]
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {colors["ink"]};',
                f'  background-color: {colors["face"]};',
                f'  border-top: {shadow}px solid {colors["light"]};',
                f'  border-left: {shadow}px solid {colors["light"]};',
                f'  border-bottom: {shadow}px solid {colors["dark"]};',
                f'  border-right: {shadow}px solid {colors["dark"]};',
                '  border-radius: 0px;',
                f'  padding: {combo_padding};',
                '}',
            ])
            separator = colors['light'] if state == 'pressed' else colors['dark']
            qss.extend([
                selector + '::drop-down' + pseudo + ' {',
                f'  width: {drop_width}px;',
                f'  background-color: {colors["face"]};',
                '  subcontrol-origin: padding;',
                '  subcontrol-position: top right;',
                f'  border-left: {shadow}px solid {separator};',
                '  padding: 0px; margin: 0px;',
                '}',
            ])
            if family == 'qt6':
                qss.extend([
                    selector + '::drop-down' + pseudo + ' {',
                    f'  border-top: {shadow}px solid {colors["light"]};',
                    f'  border-right: {shadow}px solid {colors["dark"]};',
                    f'  border-bottom: {shadow}px solid {colors["dark"]};',
                    '}',
                ])
            else:
                qss.extend([
                    selector + '::drop-down' + pseudo + ' {',
                    '  border-top: none; border-right: none; border-bottom: none;',
                    '}',
                ])
            url = str(combo_assets[state].resolve())
            if family == 'qt6':
                qss.extend([selector + '::down-arrow' + pseudo + ' {',
                            f'  image: url("{url}");', '}'])
            else:
                qss.extend([
                    selector + '::down-arrow' + pseudo + ' {',
                    f'  width: {arrow_size}px; height: {arrow_size}px;',
                    '  subcontrol-origin: padding; subcontrol-position: center;',
                    f'  image: url("{url}");',
                    '  border: none; padding: 0px; margin: 0px;',
                    '}',
                ])

        opened = _translated_colors(builder, recipe, palette, 'pressed', 'button',
                                    ('face', 'light', 'dark', 'ink'))
        qss.extend([
            selector + ':on {',
            f'  color: {opened["ink"]};',
            f'  background-color: {opened["face"]};',
            f'  border-top: {shadow}px solid {opened["dark"]};',
            f'  border-left: {shadow}px solid {opened["dark"]};',
            f'  border-bottom: {shadow}px solid {opened["light"]};',
            f'  border-right: {shadow}px solid {opened["light"]};',
            '}',
        ])
        if family == 'qt6':
            qss.extend([
                selector + ':on::drop-down {',
                f'  border-top: {shadow}px solid {opened["dark"]};',
                f'  border-left: {shadow}px solid {opened["light"]};',
                f'  border-right: {shadow}px solid {opened["light"]};',
                f'  border-bottom: {shadow}px solid {opened["light"]};',
                '}',
            ])
        else:
            qss.extend([
                selector + ':on::drop-down {',
                f'  border-left: {shadow}px solid {opened["light"]};',
                '}',
            ])
        arrow_on_selector = (selector + '::down-arrow:on' if family == 'qt6'
                             else selector + ':on::down-arrow')
        qss.append(arrow_on_selector + ' {')
        if family == 'qt5':
            qss.extend([
                '  subcontrol-origin: padding; subcontrol-position: center;',
                f'  width: {arrow_size}px; height: {arrow_size}px;',
            ])
        qss.extend([f'  image: url("{combo_assets["pressed"].resolve()}");', '}'])

        view = _translated_colors(builder, recipe, palette, 'normal', 'view', ('face', 'ink'))
        selection_colors = _translated_colors(builder, recipe, palette, 'normal', 'selection', ('face', 'ink'))
        relief = _translated_colors(builder, recipe, palette, 'normal', 'window', ('light', 'dark'))
        qss.extend([
            popup + ' {',
            f'  color: {view["ink"]};',
            f'  background-color: {view["face"]};',
            f'  selection-background-color: {selection_colors["face"]};',
            f'  selection-color: {selection_colors["ink"]};',
            f'  border-top: {shadow}px solid {relief["dark"]};',
            f'  border-left: {shadow}px solid {relief["dark"]};',
            f'  border-bottom: {shadow}px solid {relief["light"]};',
            f'  border-right: {shadow}px solid {relief["light"]};',
            '  outline: none;',
            '}',
            popup + '::item {',
            f'  padding: {padding}px;',
            '}',
            popup + '::item:selected {',
            f'  color: {selection_colors["ink"]};',
            f'  background-color: {selection_colors["face"]};',
            '}',
        ])
    if family in ('qt5', 'qt6') and 'spin' in ids:
        spin_selectors = (
            'QSpinBox#domainosRecipeSpinBox',
            'QDoubleSpinBox#domainosRecipeDoubleSpinBox',
        )
        spin_arrow_size = geometry['arrow_px']
        spin_button_width = spin_arrow_size + 2 * shadow
        spin_assets = {}
        for state in STATES:
            inactive, disabled = state == 'backdrop', state == 'disabled'
            arrow_state = 'normal' if state == 'backdrop' else state
            for direction in ('up', 'down'):
                pixels = builder.gtk3_arrow(arrow_state, direction, geometry=geometry)
                payload = _png(pixels, builder.art, palette,
                               inactive=inactive, disabled=disabled)
                path = asset_dir / f'spin-arrow-{direction}-{state}.png'
                path.write_bytes(payload)
                spin_assets[(direction, state)] = path

        for selector in spin_selectors:
            for state in ('normal', 'backdrop', 'disabled'):
                colors = _translated_colors(builder, recipe, palette, state, 'view',
                                            ('face', 'ink', 'light', 'dark'))
                pseudo = {'normal': '', 'backdrop': ':!active',
                          'disabled': ':disabled'}[state]
                qss.extend([
                    selector + pseudo + ' {',
                    f'  color: {colors["ink"]};',
                    f'  background-color: {colors["face"]};',
                    f'  border-top: {shadow}px solid {colors["dark"]};',
                    f'  border-left: {shadow}px solid {colors["dark"]};',
                    f'  border-bottom: {shadow}px solid {colors["light"]};',
                    f'  border-right: {shadow}px solid {colors["light"]};',
                    '  border-radius: 0px;',
                    f'  padding: {geometry["control_padding_px"]}px;',
                    '}'])
            for direction in ('up', 'down'):
                button_selector = selector + f'::{direction}-button'
                for state in ('normal', 'backdrop', 'disabled'):
                    colors = _translated_colors(builder, recipe, palette, state,
                                                'button', ('face', 'light', 'dark'))
                    pseudo = {'normal': '', 'backdrop': ':!active',
                              'disabled': ':disabled'}[state]
                    placement = 'top right' if direction == 'up' else 'bottom right'
                    qss.extend([
                        button_selector + pseudo + ' {',
                        '  subcontrol-origin: border;',
                        f'  subcontrol-position: {placement};',
                        f'  width: {spin_button_width}px;',
                        f'  background-color: {colors["face"]};',
                        f'  border-top: {shadow}px solid {colors["light"]};',
                        f'  border-left: {shadow}px solid {colors["light"]};',
                        f'  border-bottom: {shadow}px solid {colors["dark"]};',
                        f'  border-right: {shadow}px solid {colors["dark"]};',
                        '}'])
                pressed = _translated_colors(builder, recipe, palette, 'pressed',
                                             'button', ('face', 'light', 'dark'))
                qss.extend([
                    button_selector + ':pressed {',
                    f'  background-color: {pressed["face"]};',
                    f'  border-top: {shadow}px solid {pressed["dark"]};',
                    f'  border-left: {shadow}px solid {pressed["dark"]};',
                    f'  border-bottom: {shadow}px solid {pressed["light"]};',
                    f'  border-right: {shadow}px solid {pressed["light"]};',
                    '}'])

                arrow_selector = selector + f'::{direction}-arrow'
                for state in STATES:
                    pseudo = {'normal': '', 'pressed': ':pressed',
                              'backdrop': ':!active', 'disabled': ':disabled'}[state]
                    path = spin_assets[(direction, state)]
                    qss.extend([
                        arrow_selector + pseudo + ' {',
                        f'  width: {spin_arrow_size}px; height: {spin_arrow_size}px;',
                        '  subcontrol-origin: padding; subcontrol-position: center;',
                        f'  image: url("{path.resolve()}");',
                        '  border: none; padding: 0px; margin: 0px;',
                        '}'])
                disabled_path = spin_assets[(direction, 'disabled')]
                qss.extend([
                    arrow_selector + ':off {',
                    f'  image: url("{disabled_path.resolve()}");',
                    '}'])

    if family == 'qt6' and 'list' in ids:
        selector = 'QTreeWidget#domainosRecipeList'
        padding = geometry['control_padding_px']
        for state in ('normal', 'backdrop', 'disabled'):
            view = _translated_colors(builder, recipe, palette, state, 'view',
                                      ('face', 'ink'))
            selection = _translated_colors(builder, recipe, palette, state,
                                            'selection', ('face', 'ink'))
            relief = _translated_colors(builder, recipe, palette, state, 'window',
                                        ('light', 'dark'))
            if state == 'normal':
                pseudo = ''
            elif state == 'disabled':
                pseudo = ':disabled'
            else:
                pseudo = '[domainosBackdrop="true"]'
            qss.extend([
                selector + pseudo + ' {',
                f'  color: {view["ink"]};',
                f'  background-color: {view["face"]};',
                f'  selection-background-color: {selection["face"]};',
                f'  selection-color: {selection["ink"]};',
                f'  border-top: {shadow}px solid {relief["dark"]};',
                f'  border-left: {shadow}px solid {relief["dark"]};',
                f'  border-bottom: {shadow}px solid {relief["light"]};',
                f'  border-right: {shadow}px solid {relief["light"]};',
                '  border-radius: 0px; outline: none;',
                f'  padding: {padding}px;',
                '}',
                selector + pseudo + '::item {',
                f'  color: {view["ink"]};',
                f'  background-color: {view["face"]};',
                '  border: none; border-radius: 0px;',
                f'  padding: {padding}px;',
                '}',
                selector + pseudo + '::item:selected {',
                f'  background-color: {selection["face"]};',
                f'  color: {selection["ink"]};',
                '}',
            ])
        focus = _translated_colors(builder, recipe, palette, 'normal', 'focus',
                                   ('light', 'dark'))
        qss.extend([
            selector + ':focus {',
            f'  border-top: {shadow}px solid {focus["dark"]};',
            f'  border-left: {shadow}px solid {focus["dark"]};',
            f'  border-bottom: {shadow}px solid {focus["light"]};',
            f'  border-right: {shadow}px solid {focus["light"]};',
            '}',
        ])

    if family in ('qt5', 'qt6') and ids.intersection({'push', 'toggle'}):
        state_selectors = {
            'normal': '', 'pressed': ':pressed',
            'backdrop': ':!active', 'disabled': ':disabled',
        }
        button_controls = []
        if 'push' in ids:
            button_controls.append(('push', 'QPushButton#domainosRecipePushButton', False))
        if 'toggle' in ids:
            button_controls.append(('toggle', 'QPushButton#domainosRecipeToggleButton', True))
        for _control, selector, checkable in button_controls:
            for state in STATES:
                colors = _translated_colors(builder, recipe, palette, state, 'button',
                                            ('face', 'light', 'dark', 'ink'))
                upper = colors['dark'] if state == 'pressed' else colors['light']
                lower = colors['light'] if state == 'pressed' else colors['dark']
                qss.extend([
                    selector + state_selectors[state] + ' {',
                    f'  color: {colors["ink"]};',
                    f'  background-color: {colors["face"]};',
                    f'  border-top: {shadow}px solid {upper};',
                    f'  border-left: {shadow}px solid {upper};',
                    f'  border-bottom: {shadow}px solid {lower};',
                    f'  border-right: {shadow}px solid {lower};',
                    '  border-radius: 0px;',
                    '}',
                ])
                if checkable:
                    qss.extend([
                        selector + ':checked' + state_selectors[state] + ' {',
                        f'  color: {colors["ink"]};',
                        f'  background-color: {colors["face"]};',
                        f'  border-top: {shadow}px solid {colors["dark"]};',
                        f'  border-left: {shadow}px solid {colors["dark"]};',
                        f'  border-bottom: {shadow}px solid {colors["light"]};',
                        f'  border-right: {shadow}px solid {colors["light"]};',
                        '  border-radius: 0px;',
                        '}',
                    ])
    css_path = folder / f'{family}-scrollbar.qss'
    css_path.write_text('\n'.join(qss) + '\n', encoding='utf-8')
    backend.write_json(folder / f'{family.upper()}-NATIVE-COLORS.json', {'colors': palette, 'origin': origin})
    recipe_hash = backend.sha(json.dumps(recipe, sort_keys=True).encode())
    artifacts = {str(path.relative_to(folder)): backend.sha(backend.read_file(path))
                 for path in sorted(folder.rglob('*')) if path.is_file()}
    receipt = {
        'schema_version': 1, 'family': family, 'status': 'partially_generated',
        'reason': f'Receita parcial aplicada aos controles Qt{family[-1]} visíveis declarados; os demais controles continuam pendentes.',
        'recipe_applied': False, 'translated_controls': sorted(ids),
        'scope': f'Qt{family[-1]} Widgets partial QSS snapshot; visible controls'
                 + (' and QPushButton controls' if family in ('qt5', 'qt6') and ids.intersection({'push', 'toggle'}) else '')
                 + (' and QCheckBox indicators' if family == 'qt5' and 'check' in ids else '')
                 + (' and QRadioButton indicators' if family == 'qt5' and 'radio' in ids else '')
                 + (' and QLineEdit controls' if family in ('qt5', 'qt6') and 'entry' in ids else '')
                 + (' and QComboBox/dropdown controls' if family in ('qt5', 'qt6') and 'combo' in ids else '')
                 + (' and QSpinBox/QDoubleSpinBox controls' if family in ('qt5', 'qt6') and 'spin' in ids else '')
                 + (' and QTextEdit controls' if family in ('qt5', 'qt6') and 'text' in ids else '')
                 + (' and QSlider controls' if ids.intersection({'scale_h', 'scale_v'}) else '')
                 + (' and QToolButton arrow controls' if family in ('qt5', 'qt6') and 'arrow' in ids else '')
                 + (' and native QProgressBar controls with explicit QSS states' if family in ('qt5', 'qt6') and 'progress' in ids else '')
                 + (' and QTreeView list, selection, focus and disabled states' if family in ('qt5', 'qt6') and 'list' in ids else '')
                 + (' and QFrame panel/sunken bevel states' if family in ('qt5', 'qt6') and 'frame' in ids else '')
                 + (' and QSpinBox/QDoubleSpinBox controls' if family == 'qt5' and 'spin' in ids else ''),
        'project_sha256': project_hash, 'recipe_sha256': recipe_hash,
        'css': str(css_path), 'asset_dir': str(asset_dir), 'geometry': {
            'bar_cross_px': bar, 'shadow_px': shadow, 'arrow_cell_px': geometry['arrow_px'],
            'thumb_cross_px': thumb, 'arrow_thumb_gap_px': geometry['arrow_thumb_gap_px'],
            'view_bar_gap_px': geometry['view_bar_gap_px'],
            'view_inset_px': geometry['view_inset_px'],
            'length': 'Qt native range/page step'},
        'states': list(STATES), 'palette_roles_applied': True,
        'selected_scheme': selected, 'palette': origin,
        'palette_inputs': [selected, origin['helper'], origin['helper_source']],
        'artifacts': artifacts, 'host_changed': False, 'picked_used': False,
        'limitations': [
            f'Qt{family[-1]} still owns scrollbar range, page step, wheel and drag input when scrollbars are visible.',
            'This partial recipe does not translate controls omitted from translated_controls.',
            'KDE palette roles are resolved into this private snapshot; regenerate after changing the selected scheme.',
            'Qt QScrollBar does not expose 4px viewport-to-bar spacing as a style metric; the gallery reserves it in QAbstractScrollArea when scrollbars are visible.',
            'The QSS adapter does not establish all historical Motif states or visual equivalence.'
        ]}
    if not backend.palette_inputs_current(receipt):
        raise backend.Unavailable('Qt6 KDE palette changed during scrollbar generation.')
    backend.write_json(folder / f'{family.upper()}-SCROLLBAR-PROPOSAL.json', receipt)
    return receipt


def verify(root, receipt, model, family='qt6'):
    if family not in ('qt5', 'qt6'):
        raise ValueError('Qt scrollbar recipe family must be qt5 or qt6.')
    folder = Path(receipt['css']).parent
    folder = backend.private_output(folder.absolute(), root)
    receipt_path = folder / f'{family.upper()}-SCROLLBAR-PROPOSAL.json'
    saved = json.loads(backend.read_file(receipt_path))
    recipe_hash = backend.sha(json.dumps(model['recipes'][family], sort_keys=True).encode())
    if (saved.get('family') != family or saved.get('project_sha256') != receipt.get('project_sha256') or
            saved.get('recipe_sha256') != recipe_hash or saved.get('translated_controls') != receipt.get('translated_controls')):
            raise ValueError(f'{family.upper()} scrollbar snapshot/recipe identity mismatch')
    assets = saved.get('artifacts')
    if not isinstance(assets, dict) or not assets:
        raise ValueError(f'{family.upper()} scrollbar artifact manifest missing')
    for relative, digest in assets.items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError(f'{family.upper()} scrollbar artifact outside snapshot')
        target = folder / path
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError(f'{family.upper()} scrollbar artifact traverses a link')
        if backend.sha(backend.read_file(target)) != digest:
            raise ValueError(f'{family.upper()} scrollbar artifact hash mismatch: ' + relative)
    css = Path(saved.get('css', ''))
    if not css.is_absolute() or not css.is_relative_to(folder) or str(css.relative_to(folder)) not in assets:
        raise ValueError(f'{family.upper()} stylesheet is not a verified snapshot artifact')
    if not backend.palette_inputs_current(saved):
        raise ValueError(f'{family.upper()} scrollbar palette inputs are stale')
    return saved
