# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK2 indicator-less toggle proposal; persistent face matches Motif.

GTK 2.24.33 gtktogglebutton.c passes shadow IN/OUT from GtkButton.depressed
to _gtk_button_paint. gtkbutton.c actually paints detail button, ignoring the
main_detail argument in this release. The pixmap engine cannot distinguish the
persistent ACTIVE toggle from an armed ACTIVE button; keep both faces flat and
retain native focus feedback. No historical metric claim or install.
"""
from pathlib import Path
from gtk2_buttons import geometry


def toggle_geometry_lines(recipe):
    shadow, padding, font = geometry(recipe)
    # The local Motif indicator-less toggle is text-centered in a shallow
    # 56x21 sample. GTK2's natural box adds vertical requisition that the Motif
    # sample does not; use the horizontal inset to keep the label centered.
    return ['  xthickness = ' + str(shadow * 2), '  ythickness = 0',
            '  GtkButton::inner-border = { ' + ', '.join([str(padding)] * 4) + ' }',
            '  font_name = "' + str(font) + 'px"']


def image_rule(state, depressed, filename, shadow):
    # Motif's indicator-less toggle returns to a flat face after focus leaves.
    # GTK2's pixmap engine cannot distinguish persistent ACTIVE from armed
    # ACTIVE, so keep both states flat and leave focus feedback native.
    border = '0, 0, 0, 0'
    return ('    image { function = BOX detail = "button" state = ' + state +
            ' shadow = ' + ('IN' if depressed else 'OUT') + ' file = "' + filename +
            '" border = { ' + border + ' } stretch = TRUE }')


def paint_toggle(builder, recipe, palette, destination):
    shadow, _, _ = geometry(recipe)
    art = builder.art
    for role in ('window', 'window-fg'):
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 toggle missing effective role: ' + name)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    files = {}
    for variant, index in (('normal', 0), ('disabled', 2), ('backdrop', 1)):
        effective = dict(palette)
        for names in art.ROLES.values():
            if names[index] in palette: effective[names[0]] = palette[names[index]]
        for depressed in (False, True):
            pixels = art.blank(1, 1, 'face')
            filename = 'toggle-' + variant + ('-selected' if depressed else '') + '.png'
            (destination / filename).write_bytes(builder.png(pixels, 'window', effective))
            files[variant, depressed] = filename
    lines = ['# Private GTK2 toggle proposal; effective KDE palette, native shadow selector.']
    for name, backdrop in (('theme-lab-gtk2-toggle', False), ('theme-lab-gtk2-toggle-backdrop', True)):
        lines += ['style "' + name + '" {'] + toggle_geometry_lines(recipe)
        for gtk_state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if gtk_state == 'INSENSITIVE' else 1 if backdrop else 0
            for field, role in (('bg', 'window'), ('fg', 'window-fg')):
                rgb = art._rgb(palette[art.ROLES[role][index]])
                lines.append('  ' + field + '[' + gtk_state + '] = "#%02x%02x%02x"' % rgb)
        lines.append('  engine "pixmap" {')
        for gtk_state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            variant = 'disabled' if gtk_state == 'INSENSITIVE' else 'backdrop' if backdrop else 'normal'
            for depressed in (False, True):
                lines.append(image_rule(gtk_state, depressed, files[variant, depressed], shadow))
        lines += ['  }', '}']
    for widget, style in (('themeLabToggle', 'theme-lab-gtk2-toggle'),
                          ('themeLabBackdropToggle', 'theme-lab-gtk2-toggle-backdrop')):
        lines += ['widget "*' + widget + '" style : highest "' + style + '"',
                  'widget "*' + widget + '.*" style : highest "' + style + '"']
    rc = destination / 'toggle.gtkrc'
    rc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'rc': str(rc), 'assets': list(files.values()), 'translated_control': 'toggle',
            'scope': 'Indicator-less toggle: flat persistent face; native focus feedback retained',
            'unsupported': ['inconsistent', 'focus', 'default indicator', 'automatic backdrop',
                            'separate persistent selection from armed press in GTK2 pixmap engine']}


def selected_fragment(recipe, state):
    if state not in ('normal','pressed','disabled','backdrop','hover'):
        raise ValueError('GTK2 toggle: state not translated: '+state)
    shadow, _, _ = geometry(recipe)
    gtk_state={'normal':'NORMAL','pressed':'ACTIVE','disabled':'INSENSITIVE',
               'backdrop':'NORMAL','hover':'PRELIGHT'}[state]
    variant='disabled' if state=='disabled' else 'backdrop' if state=='backdrop' else 'normal'
    # Selection is native state, but the local Motif sample has no persistent
    # selected relief after focus leaves.
    return '\n'.join(['# Selected GtkToggleButton; palette/selection come from verified native RC.',
        'style "theme-lab-gtk2-toggle-fragment" {']+toggle_geometry_lines(recipe)+
        ['  engine "pixmap" {']+[image_rule(gtk_state,selected,'toggle-'+variant+
        ('-selected' if selected else '')+'.png',shadow) for selected in (False,True)]+
        ['  }','}','# Inspection fragment; not a complete theme or palette installation.',''])
