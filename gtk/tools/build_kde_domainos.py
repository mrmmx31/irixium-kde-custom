#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the original SR10.4 Motif reconstruction for GTK2, GTK3 and GTK4.

The three packages are complete independent themes. Only shared build helpers
and semantic color-role infrastructure are reused; no IRIX artwork or extracted
HP bitmap/font is copied. Generation never selects a theme or edits a profile.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import domainos_motif_art as art
import adaptive_assets

LICENSE = '/* SPDX-License-Identifier: GPL-3.0-or-later */\n'
IDENTITIES = (art.NAME, art.NAME+'-KDE', art.NAME+'-KDE-Reload')
SCROLLBAR_RULES = ROOT/'tools/domainos_scrollbar_rules.json'


def gtk3_scrollbar_rules(source=SCROLLBAR_RULES):
    """Read the shared rules; never substitute local geometry defaults."""
    source = Path(source)
    try:
        contract = json.loads(source.read_text())
        geometry = contract['geometry']
        keys = ('bar_px', 'shadow_px', 'arrow_px', 'thumb_cross_px',
                'arrow_thumb_gap_px', 'view_bar_gap_px', 'view_inset_px')
        if contract['schema_version'] != 1 or geometry['unit'] != 'native_pixel':
            raise ValueError('unsupported schema or geometry unit')
        if contract['palette']['range_boundary_arrow']['color_policy'] != 'parent_scrollbar_state':
            raise ValueError('unsupported range-boundary arrow color policy')
        if any(type(geometry[key]) is not int for key in keys):
            raise ValueError('geometry dimensions must be integers')
        if any(geometry[key] <= 0 for key in keys):
            raise ValueError('geometry dimensions must be positive')
        if geometry['bar_px'] != geometry['arrow_px'] + 2*geometry['shadow_px']:
            raise ValueError('bar_px must equal arrow_px + 2 * shadow_px')
        if geometry['thumb_cross_px'] != geometry['arrow_px']:
            raise ValueError('thumb_cross_px must equal arrow_px')
        if geometry['arrow_px'] % 2 != 1 or geometry['arrow_px'] <= 2*geometry['shadow_px']:
            raise ValueError('arrow_px must be odd and exceed its two shadow bands')
        # This backend reuses one inset mask for the trough and GtkViewport.
        # Reject an incompatible contract rather than paint a mismatched frame.
        if geometry['view_inset_px'] != geometry['shadow_px']:
            raise ValueError('GTK3 shared inset mask requires view_inset_px = shadow_px')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError('Invalid DomainOS scrollbar contract '+str(source)+': '+str(exc)) from exc
    return contract


def png(pixels, family, palette, *, disabled=False):
    from PIL import Image
    image = Image.new('RGBA', (len(pixels[0]), len(pixels)))
    for y, row in enumerate(pixels):
        for x, token in enumerate(row):
            if token is None: continue
            value = art.evaluate(art.pixel_plan(family, token, disabled=disabled), palette)
            image.putpixel((x, y), tuple(int(value[n:n+2], 16) for n in (1, 3, 5))+(255,))
    output = io.BytesIO(); image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def gtk3_arrow(state='normal', direction='up', *, geometry=None):
    """An eleven-pixel Motif triangle in the shared scrollbar trough.

    The SR10.4 Trash Can has a 15px scrollbar, 2px enclosing shadows,
    11px arrows and a 1px arrow/slider interval. A direction-specific
    geometric bevel keeps the light at the upper left. Its odd intrinsic
    size leaves a centered single-pixel tip; pressing reverses the relief.
    GTK2 pixmaps and Kvantum retain their separate source contract.
    """
    if direction not in ('up', 'down', 'left', 'right'):
        raise ValueError('Unknown GTK3 Motif arrow direction')
    geometry = gtk3_scrollbar_rules()['geometry'] if geometry is None else geometry
    size, shadow = geometry['arrow_px'], geometry['shadow_px']
    shape = art.blank(size, size)
    for y in range(size):
        half = (y+1)//2
        art.rect(shape, size//2-half, y, 2*half+1, 1, 'face')
    if direction == 'down': shape = [list(reversed(row)) for row in reversed(shape)]
    elif direction == 'left': shape = [list(row) for row in zip(*shape)]
    elif direction == 'right': shape = [list(reversed(row)) for row in zip(*shape)]
    arrow = art.blank(size, size)
    light, dark = ('dark', 'light') if state in ('pressed', 'toggled') else ('light', 'dark')
    if direction in ('up', 'down'):
        for y, row in enumerate(shape):
            occupied = [x for x, token in enumerate(row) if token is not None]
            if not occupied: continue
            left, right = min(occupied), max(occupied)
            for x in occupied:
                if direction == 'up' and y >= size-shadow:
                    token = light if x < size-y else dark
                elif direction == 'down' and y < shadow:
                    token = dark if y == shadow-1 and x >= size-shadow else light
                elif direction == 'down' and x > right-shadow:
                    token = dark
                else:
                    token = light if x < left+shadow else dark if x > right-shadow else 'face'
                arrow[y][x] = token
    else:
        for x in range(size):
            occupied = [y for y in range(size) if shape[y][x] is not None]
            if not occupied: continue
            top, bottom = min(occupied), max(occupied)
            for y in occupied:
                if direction == 'left' and x >= size-shadow:
                    token = light if y < size-x else dark
                elif direction == 'right' and x < shadow:
                    token = dark if x == shadow-1 and y >= size-shadow else light
                else:
                    token = (light if y < top+shadow else dark if y > bottom-shadow else 'face') if direction == 'left' else (dark if y > bottom-shadow else light if y < top+shadow else 'face')
                arrow[y][x] = token
    return arrow


def gtk3_assets(*, geometry=None):
    geometry = gtk3_scrollbar_rules()['geometry'] if geometry is None else geometry
    result = {'gtk3-stepper-'+direction+'-'+state: (gtk3_arrow(state, direction, geometry=geometry), 'button', 0)
            for state in art.STATES for direction in ('up', 'down', 'left', 'right')}
    # Sampling extent is a backend detail; only fixed corners and one-pixel
    # repeat strips are exported, never a historical minimum thumb length.
    extent = 2*(geometry['arrow_px']+geometry['arrow_thumb_gap_px'])
    shadow = geometry['shadow_px']
    for name, inset in (('trough', True), ('thumb', False)):
        frame = art.bevel(art.blank(extent, extent, 'face'), thickness=shadow, down=inset)
        result['gtk3-'+name+'-frame'] = (frame, 'button', shadow)
    return result


def masks(destination, *, geometry=None):
    destination.mkdir(parents=True, exist_ok=True)
    entries, files = {}, {}
    for name, (pixels, family, border) in (art.assets() | gtk3_assets(geometry=geometry)).items():
        # GTK reserves the frame width; the GTK3 scrollbar's integer slices
        # paint its joins without CSS border miter antialiasing. Shared
        # controls retain their native CSS frames and intrinsic glyph masks.
        if border and not name.startswith('gtk3-'): continue
        width, height = len(pixels[0]), len(pixels)
        slices = []
        for region in adaptive_assets._regions(width, height, border):
            x0, y0, x1, y1 = region['box']
            part = [row[x0:x1] for row in pixels[y0:y1]]
            colors = sorted({token for row in part for token in row if token})
            layers = []
            for first in range(0, len(colors), 3):
                group = colors[first:first+3]
                name_svg = name+('-'+region['part'] if border else '')+'-'+str(first//3)+'-symbolic.svg'
                contents = adaptive_assets._svg(part, group).encode()
                (destination/name_svg).write_bytes(contents)
                files[name_svg] = hashlib.sha256(contents).hexdigest()
                layers.append({'file': name_svg, 'colors': group})
            slices.append({**region, 'layers': layers})
        entries[name] = {'width': width, 'height': height, 'border': border, 'family': family, 'slices': slices}
    manifest = {'schema': 1, 'algorithm': 'Original Motif semantic three-channel integer masks', 'assets': entries, 'files': files}
    # Remove only superseded, generated GTK3 masks. An eleven-pixel triangle
    # needs three channels instead of the old full stepper's fourth trough
    # channel. Leaving its obsolete layer in a rebuilt package hides stale
    # resources from the adaptive manifest.
    for path in destination.glob('gtk3-*-symbolic.svg'):
        if path.name not in files: path.unlink()
    (destination/'MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def definition_css():
    return ''.join('@define-color '+name+' '+value+';\n' for name, value in sorted(art.DEFAULT.items()))


def state_css(family, state):
    inactive, disabled = bool(state & 1), bool(state & 2)
    def expression(token):
        return art.expression(art.pixel_plan(family, token, inactive=inactive, disabled=disabled))
    return expression


def rule(selector, properties):
    return selector+' {\n'+''.join('  '+key+': '+value+';\n' for key, value in properties.items())+'}\n'


def common_css(manifest):
    output = [LICENSE, definition_css(), '''
* {
  border-radius: 0; border-style: none; border-width: 0;
  background-image: none; box-shadow: none; text-shadow: none;
  -gtk-icon-shadow: none; transition-property: none; transition-duration: 0s;
  animation-name: none; opacity: 1; outline-style: none;
}
label, image { color: inherit; }
button, .button { min-width: 16px; min-height: 18px; padding: 4px 6px; border: 2px solid; }
entry, spinbutton { min-height: 18px; padding: 2px 4px; border: 2px solid; }
textview, .view, treeview, listview, columnview, gridview { border: 0; }
menubar, toolbar { padding: 0; border: 2px solid; }
menu, popover > contents { padding: 2px; border: 2px solid; }
menuitem { min-height: 18px; padding: 2px 6px; border: 2px solid transparent; }
headerbar, .titlebar { min-height: 20px; padding: 2px; border: 2px solid; }
notebook > header > tabs > tab { min-height: 18px; padding: 4px 6px; border: 2px solid; }
notebook > stack, frame > border { border: 2px solid; }
check, radio { min-width: 14px; min-height: 14px; padding: 0; margin: 2px; border: 0; }
scrollbar { padding: 0; margin: 0; border: 0; }
scrollbar trough { min-width: 12px; min-height: 12px; border: 2px solid; }
scrollbar slider { min-width: 8px; min-height: 16px; border: 2px solid; margin: 0; padding: 0; }
scrollbar.horizontal slider { min-width: 16px; min-height: 8px; }
scale trough { min-width: 8px; min-height: 8px; border: 2px solid; }
scale slider { min-width: 12px; min-height: 20px; border: 2px solid; }
scale.vertical slider { min-width: 20px; min-height: 12px; }
progressbar trough, levelbar trough { min-height: 14px; border: 2px solid; }
progressbar progress, levelbar block.filled { min-height: 14px; border: 2px solid; }
switch { min-width: 32px; min-height: 16px; border: 2px solid; padding: 0; }
switch slider { min-width: 14px; min-height: 14px; border: 2px solid; }
separator { min-width: 2px; min-height: 2px; }
tooltip { padding: 4px 6px; border: 2px solid; }
*:focus { outline: 1px dotted; outline-offset: -4px; }
label:focus, image:focus { outline: none; }
''']
    def native(selectors, family, state, *, down=False, flat=False, token='face'):
        e = state_css(family, state)
        colors = (e('dark')+' '+e('light')+' '+e('light')+' '+e('dark')) if down else (e('light')+' '+e('dark')+' '+e('dark')+' '+e('light'))
        return rule(selectors, {'color': e('ink'), 'background-color': e(token),
            'border-color': 'transparent' if flat else colors, 'outline-color': e('focus')})
    families = (
        ('.background, window, dialog', 'window', False),
        ('button, .button', 'button', False),
        ('entry, spinbutton, textview, .view, treeview, listview, columnview, gridview', 'view', True),
        ('menubar, toolbar, menu, menuitem, popover > contents', 'header', False),
        ('headerbar, .titlebar', 'title', False),
        ('notebook > stack, notebook > header > tabs > tab, frame > border', 'window', False),
        ('scrollbar trough, scale trough, progressbar trough, levelbar trough, switch', 'button', True),
        ('scrollbar slider, scale slider, switch slider', 'button', False),
        ('progressbar progress, levelbar block.filled', 'selection', False),
        ('tooltip', 'tooltip', False),
    )
    for state, suffix in ((0, ''), (1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
        for selector, family, down in families:
            selected = ', '.join(item.strip()+suffix for item in selector.split(','))
            output.append(native(selected, family, state, down=down, token='trough' if 'scrollbar trough' in selector else 'face'))
        output.append(native('button:active'+suffix+', button:checked'+suffix+', switch:checked'+suffix+' slider', 'button', state, down=True))
        output.append(native('button.flat'+suffix, 'button', state, flat=True))
        output.append(native('selection'+suffix+', :selected'+suffix, 'selection', state, flat=True))
        output.append(native('menuitem'+suffix, 'header', state, flat=True))
        output.append(native('menuitem:hover'+suffix, 'header', state))
        output.append(native('menuitem:active'+suffix, 'header', state, down=True))
        e = state_css('button', state)
        output.append(rule('button.default'+suffix, {'box-shadow': '0 0 0 2px '+e('default')}))
        for kind in ('check', 'radio'):
            for selected, middle in ((False, ''), (True, ':checked')):
                name = kind+('-on-' if selected else '-off-')+('disabled' if state & 2 else 'normal')
                params = adaptive_assets.expression(name, lambda token: e(token), prefix='adaptive/', manifest=manifest)
                params.update({'background-color': 'transparent', '-gtk-icon-source': 'none', 'border-image-source': 'none'})
                output.append(rule(kind+middle+suffix, params))
        params = adaptive_assets.expression('check-mixed-'+('disabled' if state & 2 else 'normal'), lambda token: e(token), prefix='adaptive/', manifest=manifest)
        params.update({'background-color': 'transparent', '-gtk-icon-source': 'none', 'border-image-source': 'none'})
        output.append(rule('check:indeterminate'+suffix, params))
        for selector, direction in (('combobox arrow', 'down'), ('menuitem arrow', 'right'), ('expander arrow', 'right')):
            params = adaptive_assets.expression('arrow-'+direction+'-normal', lambda token: e(token), prefix='adaptive/', manifest=manifest)
            params.update({'min-width': '12px', 'min-height': '12px', '-gtk-icon-source': 'none'})
            output.append(rule(selector+suffix, params))
        params = adaptive_assets.expression('arrow-down-normal', lambda token: e(token), prefix='adaptive/', manifest=manifest)
        params.update({'min-width': '12px', 'min-height': '12px', '-gtk-icon-source': 'none'})
        output.append(rule('expander:checked arrow'+suffix, params))
    return ''.join(output)


def gtk3_css(manifest, *, geometry=None):
    contract = gtk3_scrollbar_rules()
    geometry = contract['geometry'] if geometry is None else geometry
    arrow, shadow = geometry['arrow_px'], geometry['shadow_px']
    thumb_inner = geometry['thumb_cross_px']-2*shadow
    # Preserve the backend's short-thumb floor without presenting it as a
    # confirmed Motif minimum; the live range/page size determines its length.
    thumb_minimum = geometry['bar_px']+geometry['arrow_thumb_gap_px']
    dimensions = {'ARROW': arrow, 'SHADOW': shadow, 'THUMB_INNER': thumb_inner,
                  'THUMB_MINIMUM': thumb_minimum, 'VIEW_INSET': geometry['view_inset_px'],
                  'ARROW_GAP': geometry['arrow_thumb_gap_px'], 'VIEW_GAP': geometry['view_bar_gap_px']}
    geometry_css = '''
* {
  -GtkScrollbar-has-backward-stepper: true;
  -GtkScrollbar-has-forward-stepper: true;
  -GtkScrollbar-has-secondary-backward-stepper: false;
  -GtkScrollbar-has-secondary-forward-stepper: false;
  -GtkScrolledWindow-scrollbar-spacing: @VIEW_GAP@;
}
scrollbar contents { border: @SHADOW@px solid transparent; padding: 0; margin: 0; }
scrollbar trough { min-width: @ARROW@px; min-height: @ARROW@px; border: none; padding: 0; margin: 0; }
scrollbar slider { min-width: @THUMB_INNER@px; min-height: @THUMB_MINIMUM@px; border: @SHADOW@px solid transparent; padding: 0; margin: 0; }
scrollbar.horizontal slider { min-width: @THUMB_MINIMUM@px; min-height: @THUMB_INNER@px; }
scrolledwindow > viewport { border: @VIEW_INSET@px solid transparent; }
scrollbar button {
  min-width: @ARROW@px; min-height: @ARROW@px; padding: 0; margin: 0;
  border: none; border-image-source: none; box-shadow: none;
  -gtk-icon-source: none; background-origin: border-box; background-clip: border-box;
}
scrollbar.vertical button.up { margin-bottom: @ARROW_GAP@px; }
scrollbar.vertical button.down { margin-top: @ARROW_GAP@px; }
scrollbar.horizontal button.up { margin-right: @ARROW_GAP@px; }
scrollbar.horizontal button.down { margin-left: @ARROW_GAP@px; }
'''
    for name, value in dimensions.items():
        geometry_css = geometry_css.replace('@'+name+'@', str(value))
    output = [LICENSE, geometry_css]
    directions = (('vertical', 'up', 'up'), ('vertical', 'down', 'down'),
                  ('horizontal', 'up', 'left'), ('horizontal', 'down', 'right'))
    for state, suffix in ((0, ''), (1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
        # GtkTextView paints its text window through a separate CSS node.
        # GtkSourceView's Classic scheme (also used by Mousepad's "none")
        # sets the root background from its line-number style. Leaving the
        # text node transparent pairs that light surface with our View ink.
        # Style the painted node explicitly; application syntax tags and
        # deliberately selected editor schemes keep their own precedence.
        v = state_css('view', state)
        output.append(rule('textview'+suffix+' text, textview'+suffix+' border', {
            'color': v('ink'), 'background-color': v('face'),
            'caret-color': v('ink'), '-gtk-secondary-caret-color': v('ink')}))
        selection = state_css('selection', state)
        output.append(rule('textview'+suffix+' text selection', {
            'color': selection('ink'), 'background-color': selection('face')}))
        e = state_css('button', state)
        params = adaptive_assets.expression('gtk3-trough-frame', e, prefix='adaptive/', manifest=manifest)
        params.update({'background-color': e('trough'), 'border-color': 'transparent'})
        output.append(rule('scrollbar'+suffix+' contents', params))
        params = adaptive_assets.expression('gtk3-thumb-frame', e, prefix='adaptive/', manifest=manifest)
        params.update({'background-color': e('face'), 'border-color': 'transparent'})
        output.append(rule('scrollbar'+suffix+' slider', params))
        v = state_css('view', state)
        params = adaptive_assets.expression('gtk3-trough-frame', v, prefix='adaptive/', manifest=manifest)
        params.update({'background-color': v('face'), 'border-color': 'transparent'})
        output.append(rule('scrolledwindow > viewport'+suffix, params))
        output.append(rule('scrolledwindow'+suffix+', scrolledwindow'+suffix+' > junction', {'background-color': state_css('window', state)('face')}))
        for orientation, cssdirection, direction in directions:
            for pressed in (False, True):
                mode = 'pressed' if pressed else 'disabled' if state & 2 else 'normal'
                e = state_css('button', state)
                params = adaptive_assets.expression('gtk3-stepper-'+direction+'-'+mode, lambda token: e(token), prefix='adaptive/', manifest=manifest)
                params.update({'min-width': str(arrow)+'px', 'min-height': str(arrow)+'px', 'padding': '0',
                    'border': 'none', 'border-image-source': 'none', '-gtk-icon-source': 'none', 'box-shadow': 'none',
                    'background-color': e('trough')})
                selector = 'scrollbar.'+orientation+' button.'+cssdirection+(':active' if pressed else '')+suffix
                output.append(rule(selector, params))
    # A GtkRange endpoint makes only its stepper insensitive. Keep that
    # child's palette continuous with the still-sensitive parent; do not
    # enable input or reuse active roles for a wholly insensitive scrollbar.
    # The contract validates this policy before any output is generated.
    for state, suffix in ((0, ':not(:backdrop)'), (1, ':backdrop')):
        e = state_css('button', state)
        for orientation, cssdirection, direction in directions:
            params = adaptive_assets.expression('gtk3-stepper-'+direction+'-normal', e,
                                               prefix='adaptive/', manifest=manifest)
            params.update({'background-color': e('trough')})
            selector = ('scrollbar.'+orientation+':not(:disabled)'+suffix+
                        ' button.'+cssdirection+':disabled')
            output.append(rule(selector, params))
    return ''.join(output)


def gtk2_rc(palette=None):
    palette = art.DEFAULT if palette is None else palette
    def value(family, token='face', disabled=False):
        return art.evaluate(art.pixel_plan(family, token, disabled=disabled), palette)
    output = ['# SPDX-License-Identifier: GPL-3.0-or-later\n# Original SR10.4 Motif reconstruction; native pixmap engine.\n',
        'gtk-enable-animations = 0\ngtk-menu-images = 1\ngtk-button-images = 1\n',
        'style "domainos-default" {\n  xthickness = 2\n  ythickness = 2\n',
        '  GtkWidget::focus-line-width = 1\n  GtkWidget::focus-padding = 1\n  GtkButton::child-displacement-x = 0\n  GtkButton::child-displacement-y = 0\n',
        '  GtkCheckButton::indicator-size = 14\n  GtkCheckMenuItem::indicator-size = 14\n',
        '  GtkRange::slider-width = 16\n  GtkRange::stepper-size = 16\n  GtkRange::trough-border = 0\n',
        '  GtkScrollbar::min-slider-length = 20\n  GtkScrollbar::has-backward-stepper = 1\n  GtkScrollbar::has-forward-stepper = 1\n']
    for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
        disabled = state == 'INSENSITIVE'
        family = 'selection' if state == 'SELECTED' else 'window'
        for field, kind, token in (('bg', family, 'face'), ('fg', family, 'ink'), ('base', 'view', 'face'), ('text', 'view', 'ink')):
            output.append(f'  {field}[{state}] = "{value(kind, token, disabled)}"\n')
    output.append('  engine "pixmap" {\n')
    def image(function, name, *, border=2, overlay=False, **attrs):
        fields = ['function = '+function]
        fields += [key+' = '+(json.dumps(value) if key == 'detail' else value) for key, value in attrs.items()]
        fields += [('overlay_file' if overlay else 'file')+' = "../common/assets/'+name+'.png"',
                   ('overlay_stretch = FALSE' if overlay else 'border = { '+', '.join([str(border)]*4)+' }  stretch = TRUE')]
        output.append('    image { '+'  '.join(fields)+' }\n')
    for gtkstate, mode in (('NORMAL', 'normal'), ('PRELIGHT', 'focused'), ('ACTIVE', 'pressed'), ('SELECTED', 'toggled'), ('INSENSITIVE', 'disabled')):
        for detail in ('button', 'buttondefault', 'togglebutton', 'optionmenu', 'spinbutton_up', 'spinbutton_down'):
            image('BOX', 'command-'+mode, state=gtkstate, detail=detail)
        image('SHADOW', 'input-'+mode, state=gtkstate, detail='entry')
        image('BOX', 'menupanel-'+mode, state=gtkstate, detail='menu')
        image('BOX', 'menustrip-'+mode, state=gtkstate, detail='menubar')
        image('BOX', 'menurow-'+mode, state=gtkstate, detail='menuitem')
        image('BOX', 'scroll-trough-'+mode, state=gtkstate, detail='trough')
        for orientation in ('VERTICAL', 'HORIZONTAL'):
            image('SLIDER', 'scroll-thumb-'+mode, state=gtkstate, detail='slider', orientation=orientation)
        for direction in ('up', 'down', 'left', 'right'):
            image('STEPPER', 'stepper-'+direction+'-'+mode, border=0, state=gtkstate,
                arrow_direction=direction.upper(), orientation='VERTICAL' if direction in ('up', 'down') else 'HORIZONTAL')
            image('ARROW', 'arrow-'+direction+'-'+mode, overlay=True, state=gtkstate, arrow_direction=direction.upper())
        for shadow, selected in (('OUT', False), ('IN', True)):
            for kind, function in (('check', 'CHECK'), ('radio', 'OPTION')):
                image(function, kind+('-on-' if selected else '-off-')+mode, overlay=True, state=gtkstate, shadow=shadow)
        image('CHECK', 'check-mixed-'+mode, overlay=True, state=gtkstate, shadow='ETCHED_IN')
        image('EXTENSION', 'tab-'+mode, state=gtkstate)
    image('SHADOW', 'inset-normal')
    output += ['  }\n}\nclass "GtkWidget" style : rc "domainos-default"\n']
    for style, family, classes in (('button', 'button', ('GtkButton',)), ('header', 'header', ('GtkMenuBar', 'GtkMenu', 'GtkMenuItem', 'GtkToolbar'))):
        output.append('style "domainos-'+style+'" = "domainos-default" {\n')
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            for field, token in (('bg', 'face'), ('fg', 'ink')):
                output.append(f'  {field}[{state}] = "{value(family, token, state == "INSENSITIVE")}"\n')
        output.append('}\n')
        output.extend('class "'+name+'" style : rc "domainos-'+style+'"\n' for name in classes)
    return ''.join(output).encode()


def build(destination, *, theme_name=art.NAME+'-KDE'):
    if theme_name not in IDENTITIES: raise ValueError('Unknown DomainOS GTK identity')
    contract = gtk3_scrollbar_rules()
    geometry = contract['geometry']
    destination = Path(destination)
    for folder in ('common/assets', 'common/adaptive', 'gtk-2.0', 'gtk-3.0', 'gtk-4.0'):
        (destination/folder).mkdir(parents=True, exist_ok=True)
    manifest = masks(destination/'common/adaptive', geometry=geometry)
    (destination/'common/gtk.css').write_text(common_css(manifest))
    (destination/'common/gtk-3.0-overrides.css').write_text(gtk3_css(manifest, geometry=geometry))
    for version in ('3.0', '4.0'):
        text = LICENSE+'@import url("../common/gtk.css");\n'
        if version == '3.0': text += '@import url("../common/gtk-3.0-overrides.css");\n'
        (destination/f'gtk-{version}/gtk.css').write_text(text)
        (destination/f'gtk-{version}/gtk-dark.css').write_text(LICENSE+'@import url("gtk.css");\n')
    (destination/'gtk-2.0/gtkrc').write_bytes(gtk2_rc())
    for name, (pixels, family, _border) in art.assets().items():
        (destination/'common/assets'/ (name+'.png')).write_bytes(png(pixels, family, art.DEFAULT, disabled=name.endswith('-disabled')))
    (destination/'index.theme').write_text('[Desktop Entry]\nType=X-GNOME-Metatheme\nName='+theme_name+'\nComment=Original DomainOS SR10.4 Motif reconstruction\nEncoding=UTF-8\n\n[X-GNOME-Metatheme]\nGtkTheme='+theme_name+'\n')
    (destination/'LICENSE').write_bytes((ROOT/'decorations/domainos/LICENSE').read_bytes())
    origin = {'license': 'GPL-3.0-or-later', 'kind': 'original_integer_control_reconstruction', 'version': 'DomainOS SR10.4',
        'reference': 'Domain_OS SR10.4 - 01 VUE desktop.png', 'reference_sha256': 'fbc724a50477f8f7871f244805c5847ca473881abf2498882d4574463fbb3d8b',
        'guest_evidence': 'HP VUE 2.01 resources and man pages read from the SR10.4 guest; Swiss 742 bold 12pt system font; primary color set 3, secondary menus set 4 with application overrides',
        'geometry': {'bevel': 2, 'gtk2_stepper': 16, 'generic_triangle': 12, 'check_radio': 14, 'scrollbar_thumb_grips': 0},
        'gtk3_scrollbar_contract': {'path': str(SCROLLBAR_RULES.relative_to(ROOT)),
                                  'sha256': hashlib.sha256(SCROLLBAR_RULES.read_bytes()).hexdigest(),
                                  'schema_version': contract['schema_version'], 'identity': contract['identity']},
        'gtk3_scrollbar_geometry': {'bar': geometry['bar_px'], 'triangle': geometry['arrow_px'],
                                   'thumb_width': geometry['thumb_cross_px'], 'enclosing_shadow': geometry['shadow_px'],
                                   'arrow_thumb_gap': geometry['arrow_thumb_gap_px'], 'view_bar_gap': geometry['view_bar_gap_px'],
                                   'view_inset': geometry['view_inset_px'], 'origin': geometry['origin']},
        'gtk3_scrollbar_relief': {'normal': contract['relief']['normal_arrow'],
                                 'pressed': contract['relief']['pressed_arrow'],
                                 'pressed_origin': contract['relief']['pressed_arrow_origin'],
                                 'pressed_source': contract['relief']['pressed_source'],
                                 'unverified_native_states': contract['relief']['unverified_native_states']},
        'color_policy': {'primary_relief': 'Light/dark derived from the current Window or Button face',
                         'secondary_relief': 'Light/dark derived from the current Header or Selection face',
                         'inset_view': 'KDE View face/text with enclosing Window color-set shadows',
                         'marked_check_radio': 'Select-color interior relative to the Button face and reversed relief'},
        'adaptations': ['KDE has one shared application palette, rather than eight per-client VUE color sets; Vuefile, Vuehelp and Vuestyle used distinct secondary sets', 'KDE list/text selection keeps the exported Selection role; native VUE XmList could use foreground/background reverse video', 'GTK3 TreeView does not paint the main CSS frame for its populated scrollable body; no per-cell shadow, widget wrapper or toolkit patch is used to imitate it', 'Modern GTK controls absent in VUE are drawn with the same square two-pixel relief', 'GTK4 has no native scrollbar arrow buttons', 'No proprietary font is distributed; application fonts remain KDE/user settings'],
        'excluded': ['SR10.4.1', 'other DomainOS versions', 'HP bitmaps, fonts, binaries or source code'], 'reference_distributed': False}
    (destination/'ORIGEM.json').write_text(json.dumps(origin, indent=2)+'\n')
    metadata = {'schema': 1, 'name': theme_name, 'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'semantic_art_sha256': hashlib.sha256((ROOT/'tools/domainos_motif_art.py').read_bytes()).hexdigest(),
        'files': {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(destination.rglob('*')) if path.is_file() and path.name != 'MANIFEST.json'}}
    metadata['files']['common/adaptive/MANIFEST.json'] = hashlib.sha256((destination/'common/adaptive/MANIFEST.json').read_bytes()).hexdigest()
    (destination/'MANIFEST.json').write_text(json.dumps(metadata, indent=2)+'\n')
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--theme-name', choices=IDENTITIES, default=art.NAME+'-KDE')
    args = parser.parse_args()
    result = build(args.output_dir or ROOT/'gtk'/args.theme_name, theme_name=args.theme_name)
    print(json.dumps({'theme': result['name'], 'files': len(result['files']), 'profile_selected': False}))


if __name__ == '__main__': main()
