# SPDX-License-Identifier: GPL-3.0-or-later
"""Native pixmap statements shared by generation and selected-code inspection."""


def image_rules(files, gtk_state, state, orientations=('HORIZONTAL', 'VERTICAL'),
                pieces=('trough', 'thumb', 'arrow'), directions=('up', 'down', 'left', 'right')):
    lines = []
    for orientation in orientations:
        for function, detail, asset in (('BOX', 'trough', 'trough'), ('SLIDER', 'slider', 'thumb')):
            if asset not in pieces:
                continue
            # GtkRange paints the trough ACTIVE continuously: not a press.
            asset_state = 'normal' if asset == 'trough' and state == 'pressed' else state
            oriented = (asset + '-' + orientation.lower(), asset_state)
            filename, border = files[oriented] if asset == 'trough' and oriented in files else files[(asset, asset_state)]
            edges = border if isinstance(border, tuple) else (border,) * 4
            lines.append('    image { function = ' + function + ' detail = "' + detail +
                         '" state = ' + gtk_state + ' orientation = ' + orientation +
                         ' file = "' + filename + '" border = { ' +
                         ', '.join(str(value) for value in edges) + ' } stretch = TRUE }')
    if 'arrow' in pieces:
        for direction in directions:
            filename, _border = files[('arrow-' + direction, state)]
            lines.append('    image { function = STEPPER state = ' + gtk_state +
                         ' arrow_direction = ' + direction.upper() + ' overlay_file = "' +
                         filename + '" overlay_stretch = FALSE }')
    return lines


def selected_fragment(recipe, control, state):
    from gtk2_recipe import paint_contract, scrollbar_rc
    properties, _geometry, _glyph, _gap, _shadow, thumb_shadow = paint_contract(recipe)
    if control not in ('scroll_h', 'scroll_v'):
        raise ValueError('GTK2: trecho nativo deste controle ainda pendente.')
    if state not in ('normal', 'pressed', 'disabled', 'backdrop'):
        raise ValueError('GTK2: trecho nativo deste estado ainda pendente.')
    piece = recipe.get('selected_scroll_part', 0)
    if piece not in (0, 2, 3):
        raise ValueError('GTK2: botão isolado/encaixe ainda pendentes.')
    selected = {0: 'arrow', 2: 'trough', 3: 'thumb'}[piece]
    if selected == 'trough' and state == 'pressed':
        raise ValueError('GTK2: trilho ACTIVE não representa pressão; inspecione normal.')
    files = {(asset, status): (asset + '-' + status + '.png',
                             properties['trough-border'] if asset == 'trough' else
                             thumb_shadow if asset == 'thumb' else 0)
             for asset in ('trough', 'thumb', 'arrow-up', 'arrow-down', 'arrow-left', 'arrow-right')
             for status in ('normal', 'pressed', 'disabled', 'backdrop')}
    files.update({
        ('trough-horizontal', status): ('trough-horizontal-' + status + '.png', (5, 5, 2, 2))
        for status in ('normal', 'pressed', 'disabled', 'backdrop')
    })
    files.update({
        ('trough-vertical', status): ('trough-vertical-' + status + '.png', (2, 2, 5, 5))
        for status in ('normal', 'pressed', 'disabled', 'backdrop')
    })
    horizontal = control == 'scroll_h'
    native_state = {'normal': 'NORMAL', 'pressed': 'ACTIVE', 'disabled': 'INSENSITIVE', 'backdrop': 'NORMAL'}[state]
    lines = ['# GTK2: ' + control + ' / ' + selected + ' / ' + state,
             '# Fragmento de inspeção; paleta e PNGs dependem do snapshot KDE verificado.',
             '# Geometria compartilhada é uma dependência desta peça.',
             '# Desabilitado refere-se ao controle inteiro; seta no limite mantém a face do pai.',
             scrollbar_rc(recipe).replace('class "GtkScrollbar"', 'class "GtkHScrollbar"' if horizontal else 'class "GtkVScrollbar"'),
             'style "theme-lab-gtk2-selected-fragment" = "theme-lab-gtk2-scroll-geometry" {',
             '  engine "pixmap" {']
    lines.extend(image_rules(files, native_state, state,
                            ('HORIZONTAL' if horizontal else 'VERTICAL',), (selected,),
                            ('left', 'right') if horizontal else ('up', 'down')))
    lines += ['  }', '}', '# A vinculação de pintura e a face por estado vêm do RC gerado; este trecho não instala um tema.']
    return '\n'.join(lines) + '\n'
