# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared GTK2 indicator proposal. Native CHECK/OPTION selection is shadow IN/OUT.

Metrics are recipe proposals. GtkCheckButton GTK 2.24.33 draws its indicator
with active-dependent shadow; pointer press only changes GtkStateType. The
indicator uses button roles; the surrounding text/canvas uses window roles.
"""
from pathlib import Path
from gtk2_buttons import geometry
from gtk2_canvas import canvas_rc


# Symbolic raster measured from the local Motif 2.3.8 XmONE_OF_MANY sample.
# It records geometry/relief only; PNG colors still resolve through KDE roles.
# The interior margin is transparent in GTK's 15px indicator allocation.
_MOTIF_RADIO_OFF = (
    '......L......', '.....LLL.....', '....LLLLL....', '...LLLFLLL...',
    '..LLL...LLL..', '.LLL.....LLL.', 'LLL.......DDD', '.DDD.....DDD.',
    '..DDD...DDD..', '...DDD.DDD...', '....DDDDD....', '.....DDD.....',
    '......D......',
)
_MOTIF_RADIO_ON = (
    '......D......', '.....DDD.....', '....DDDDD....', '...DDDSDDD...',
    '..DDDSSSDDD..', '.DDDSSSSSDDDF', 'DDDSSSSSSSLLL', '.LLLSSSSSLLLF',
    '..LLLSSSLLL..', '...LLLSLLL...', '....LLLLL....', '.....LLL.....',
    '......L......',
)


def indicator_geometry(recipe, kind='check'):
    shadow, spacing, font = geometry(recipe)
    if kind not in ('check', 'radio'):
        raise ValueError('Unknown GTK2 indicator geometry')
    # The local Motif resource reports indicatorSize=13, but the sampled visible
    # check box is 10x10 px. Translate the painted extent, not the resource
    # allocation. Keep this independent of scrollbar arrow_px. A recipe may
    # supply a future per-control override without changing common geometry.
    key = kind + '_indicator_px'
    glyph = recipe['geometry'].get(key, 10 if kind == 'check' else 15)
    if kind == 'check':
        spacing = recipe['geometry'].get('check_indicator_spacing_px', 3)
    else:
        spacing = recipe['geometry'].get('radio_indicator_spacing_px', 2)
    if type(glyph) is not int or not 1 <= glyph <= 128 or glyph < 2 * shadow + 1:
        raise ValueError('GTK2 ' + kind + ': ' + key + ' must contain the proposed bevel')
    return glyph, shadow, spacing, font


def indicator_pixels(art, size, shadow, selected, kind):
    if kind == 'check':
        return art.bevel(art.blank(size,size,'trough' if selected else 'face'),
                         thickness=shadow, down=selected)
    if kind != 'radio': raise ValueError('Unknown GTK2 indicator')
    if size < 15 or size > 128: raise ValueError('GTK2 radio: indicator must be at least 15 px')
    visible = size - 2
    pixels = art.blank(size,size)
    source = _MOTIF_RADIO_ON if selected else _MOTIF_RADIO_OFF
    # Keep the measured 13px raster exact at its native size; nearest-neighbor
    # scaling gives a crisp pixel mask for manual larger-size experiments.
    for y in range(visible):
        sy = min(12, int((y + .5) * 13 / visible))
        for x in range(visible):
            sx = min(12, int((x + .5) * 13 / visible))
            token = source[sy][sx]
            if token != '.':
                pixels[y+1][x+1] = {'L':'light','D':'dark','F':'face','S':'trough'}[token]
    return pixels


def paint_indicator(builder, recipe, palette, destination, kind):
    if kind not in ('check','radio'): raise ValueError('Unknown GTK2 indicator')
    glyph, shadow, spacing, font = indicator_geometry(recipe, kind)
    if kind == 'radio' and glyph < 2*shadow+3:
        raise ValueError('GTK2 radio: indicator cannot contain proposed bevel/interior')
    art = builder.art
    for role in ('button', 'button-fg', 'window', 'window-fg'):
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 check missing effective role: ' + name)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    files, backgrounds = {}, {}
    for variant, index in (('normal', 0), ('disabled', 2), ('backdrop', 1)):
        effective = dict(palette)
        for names in art.ROLES.values():
            if names[index] in palette: effective[names[0]] = palette[names[index]]
        for selected in (False, True):
            pixels = indicator_pixels(art,glyph,shadow,selected,kind)
            filename = kind + '-' + variant + ('-selected' if selected else '') + '.png'
            (destination / filename).write_bytes(builder.png(pixels, 'button', effective))
            files[variant, selected] = filename
        filename = kind + '-canvas-' + variant + '.png'
        (destination / filename).write_bytes(builder.png(art.blank(1, 1, 'face'), 'window', effective))
        backgrounds[variant] = filename
    lines = ['# Private GTK2 ' + ('CHECK' if kind=='check' else 'OPTION') + ' proposal; effective KDE roles only.']
    for name, backdrop in (('theme-lab-gtk2-'+kind, False), ('theme-lab-gtk2-'+kind+'-backdrop', True)):
        lines += ['style "' + name + '" {', '  GtkCheckButton::indicator-size = ' + str(glyph),
                  '  GtkCheckButton::indicator-spacing = ' + str(spacing), '  font_name = "' + str(font) + 'px"']
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if state == 'INSENSITIVE' else 1 if backdrop else 0
            for field, role in (('bg', 'window'), ('fg', 'window-fg')):
                rgb = art._rgb(palette[art.ROLES[role][index]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines.append('  engine "pixmap" {')
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            variant = 'disabled' if state == 'INSENSITIVE' else 'backdrop' if backdrop else 'normal'
            lines.append('    image { function = FLAT_BOX detail = "checkbutton" state = ' + state +
                         ' file = "' + backgrounds[variant] + '" stretch = TRUE }')
            for selected in (False, True):
                lines.append('    image { function = ' + ('CHECK' if kind=='check' else 'OPTION') + ' detail = "' + kind + 'button" state = ' + state +
                             ' shadow = ' + ('IN' if selected else 'OUT') + ' overlay_file = "' + files[variant, selected] +
                             '" overlay_stretch = FALSE }')
        lines += ['  }', '}']
    for widget, style in (('themeLab'+kind.title(), 'theme-lab-gtk2-'+kind),
                          ('themeLabBackdrop'+kind.title(), 'theme-lab-gtk2-'+kind+'-backdrop')):
        lines += ['widget "*' + widget + '" style : highest "' + style + '"',
                  'widget "*' + widget + '.*" style : highest "' + style + '"']
    rc = destination / (kind+'.gtkrc')
    rc.write_text('\n'.join(lines) + '\n' + canvas_rc(art, palette), encoding='utf-8')
    return {'rc': str(rc), 'assets': list(files.values()) + list(backgrounds.values()),
            'translated_control': kind, 'scope': 'Standalone native '+('checkbox' if kind=='check' else 'radio')+' foundation; integration pending',
            'unsupported': ['inconsistent', 'focus', 'RTL', 'automatic backdrop']}


def indicator_fragment(recipe, state, kind):
    """Inspection fragment: both native selection shadows for one pointer state."""
    if kind not in ('check','radio'): raise ValueError('Unknown GTK2 indicator')
    states={'normal':'NORMAL','pressed':'ACTIVE','hover':'PRELIGHT',
            'disabled':'INSENSITIVE','backdrop':'NORMAL'}
    if state not in states: raise ValueError('GTK2 '+kind+': state not translated: '+state)
    glyph,shadow,spacing,font=indicator_geometry(recipe, kind)
    if kind=='radio' and glyph < 2*shadow+3: raise ValueError('GTK2 radio: indicator cannot contain proposed bevel/interior')
    variant='disabled' if state=='disabled' else 'backdrop' if state=='backdrop' else 'normal'
    lines=['# Native GTK2 indicator; KDE roles supplied by the verified RC snapshot.',
           'style "theme-lab-gtk2-'+kind+'-fragment" {',
           '  GtkCheckButton::indicator-size = '+str(glyph),
           '  GtkCheckButton::indicator-spacing = '+str(spacing),
           '  font_name = "'+str(font)+'px"','  engine "pixmap" {',
           '    image { function = FLAT_BOX detail = "checkbutton" state = '+states[state]+
           ' file = "'+kind+'-canvas-'+variant+'.png" stretch = TRUE }']
    for selected in (False,True):
        lines.append('    image { function = '+('OPTION' if kind=='radio' else 'CHECK')+' detail = "'+kind+'button" state = '+states[state]+
                     ' shadow = '+('IN' if selected else 'OUT')+' overlay_file = "'+kind+'-'+variant+
                     ('-selected' if selected else '')+'.png" overlay_stretch = FALSE }')
    return '\n'.join(lines+['  }','}','# Fragment only; selection belongs to the native GTK2 indicator.',''])
