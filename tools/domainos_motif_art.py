# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Original integer Motif control primitives for the SR10.4 adaptation.

Only measured geometry and color relationships are reconstructed. This module
contains no HP bitmap, font, screenshot or extracted software. Semantic pixels
are shared by the SVG, GTK symbolic masks and native GTK2 pixmaps so the three
toolkits keep the same bevels and arrow shape.
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET

NAME = 'DomainOS-SR10-4'
STATES = ('normal', 'focused', 'pressed', 'toggled', 'disabled')
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

ROLES = {
    'window': ('theme_bg_color_breeze', 'theme_unfocused_bg_color_breeze', 'insensitive_bg_color_breeze', 'insensitive_unfocused_bg_color_breeze'),
    'window-fg': ('theme_fg_color_breeze', 'theme_unfocused_fg_color_breeze', 'insensitive_fg_color_breeze', 'insensitive_unfocused_fg_color_breeze'),
    'button': ('theme_button_background_normal_breeze', 'theme_button_background_backdrop_breeze', 'theme_button_background_insensitive_breeze', 'theme_button_background_backdrop_insensitive_breeze'),
    'button-fg': ('theme_button_foreground_normal_breeze', 'theme_button_foreground_backdrop_breeze', 'theme_button_foreground_insensitive_breeze', 'theme_button_foreground_backdrop_insensitive_breeze'),
    'view': ('theme_base_color_breeze', 'theme_unfocused_base_color_breeze', 'insensitive_base_color_breeze', 'theme_unfocused_view_bg_color_breeze'),
    'view-fg': ('theme_text_color_breeze', 'theme_unfocused_text_color_breeze', 'insensitive_base_fg_color_breeze', 'theme_unfocused_view_text_color_breeze'),
    'selection': ('theme_selected_bg_color_breeze', 'theme_unfocused_selected_bg_color_breeze', 'insensitive_selected_bg_color_breeze', 'insensitive_unfocused_selected_bg_color_breeze'),
    'selection-fg': ('theme_selected_fg_color_breeze', 'theme_unfocused_selected_fg_color_breeze', 'insensitive_selected_fg_color_breeze', 'insensitive_unfocused_selected_fg_color_breeze'),
    'header': ('theme_header_background_breeze', 'theme_header_background_backdrop_breeze', 'theme_header_background_backdrop_breeze', 'theme_header_background_backdrop_breeze'),
    'header-fg': ('theme_header_foreground_breeze', 'theme_header_foreground_backdrop_breeze', 'theme_header_foreground_insensitive_breeze', 'theme_header_foreground_insensitive_backdrop_breeze'),
    'title': ('theme_titlebar_background_breeze', 'theme_titlebar_background_backdrop_breeze', 'theme_titlebar_background_backdrop_breeze', 'theme_titlebar_background_backdrop_breeze'),
    'title-fg': ('theme_titlebar_foreground_breeze', 'theme_titlebar_foreground_backdrop_breeze', 'theme_titlebar_foreground_insensitive_breeze', 'theme_titlebar_foreground_insensitive_backdrop_breeze'),
    'tooltip': ('tooltip_background_breeze',) * 4,
    'tooltip-fg': ('tooltip_text_breeze',) * 4,
    'focus': ('theme_button_decoration_focus_breeze', 'theme_button_decoration_focus_backdrop_breeze', 'theme_button_decoration_focus_insensitive_breeze', 'theme_button_decoration_focus_backdrop_insensitive_breeze'),
}
DEFAULT = {}
for kind, names in ROLES.items():
    value = ('#ffffff' if kind.endswith('-fg') else '#fe8282' if kind in ('title', 'focus')
             else '#3297c7' if kind in ('header', 'selection') else '#6688b5' if kind == 'view' else '#78a0d5')
    for index, name in enumerate(names):
        DEFAULT.setdefault(name, '#7acac5' if kind == 'title' and index else value)


def _rgb(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise ValueError('Missing native DomainOS color role: ' + str(value))
    return tuple(int(value[n:n+2], 16) for n in (1, 3, 5))


def tone(value, amount, endpoint):
    source, target = _rgb(value), _rgb(endpoint)
    return '#%02x%02x%02x' % tuple(round(a*(1-amount)+b*amount) for a, b in zip(source, target))


def role(family, *, inactive=False, disabled=False):
    return ROLES[family][int(inactive) + 2*int(disabled)]


def pixel_plan(family, token, *, inactive=False, disabled=False):
    """Three-dimensional Motif light/shadow are relative to the chosen face."""
    key = family
    if token == 'ink': key += '-fg'
    elif token == 'focus': key = 'focus'
    elif token == 'default': key = 'title'
    # Native SR10.4 inset views retain the enclosing primary color set's
    # shadows even though their interior uses its darker select color. The
    # KDE View face/text remain independent; only their bevel follows Window.
    elif family == 'view' and token in ('light', 'dark'): key = 'window'
    result = {'role': role(key, inactive=inactive, disabled=disabled), 'mix': 0.0, 'endpoint': '#000000'}
    # Calibrated relative levels, not fixed runtime RGBs or a scheme-name
    # exception. They reproduce the native primary/secondary relief at the
    # reference palette and continue to follow every exported KDE face.
    secondary = family in ('header', 'selection')
    if token == 'light': result.update(mix=.55 if secondary else .56, endpoint='#ffffff')
    elif token == 'dark': result.update(mix=.502 if secondary else .482, endpoint='#000000')
    elif token == 'trough': result.update(mix=.15, endpoint='#000000')
    elif token not in ('face', 'ink', 'focus', 'default'):
        raise ValueError('Unknown Motif pixel token: ' + token)
    return result


def evaluate(plan, palette):
    value = palette.get(plan['role'])
    _rgb(value)
    return tone(value, plan['mix'], plan['endpoint']) if plan['mix'] else value.lower()


def expression(plan):
    value = '@' + plan['role']
    return value if not plan['mix'] else f"mix({value}, {plan['endpoint']}, {plan['mix']:.6g})"


def blank(width, height, token=None):
    return [[token for _ in range(width)] for _ in range(height)]


def rect(image, x, y, width, height, token):
    for yy in range(max(0, y), min(len(image), y+height)):
        for xx in range(max(0, x), min(len(image[0]), x+width)):
            image[yy][xx] = token


def bevel(image, thickness=2, down=False):
    height, width = len(image), len(image[0])
    upper, lower = ('dark', 'light') if down else ('light', 'dark')
    for n in range(thickness):
        rect(image, n, n, width-2*n, 1, upper)
        rect(image, n, n, 1, height-2*n, upper)
        rect(image, n+1, height-n-1, width-2*n-1, 1, lower)
        rect(image, width-n-1, n+1, 1, height-2*n-1, lower)
    return image


def surface(state='normal', *, width=24, height=24, down=False, flat=False):
    image = blank(width, height, 'face')
    return image if flat else bevel(image, down=down or state in ('pressed', 'toggled'))


def triangle(state='normal', direction='up', *, size=12):
    """Raised twelve-pixel triangle; no solid IRIX arrow or black outline.

    Its two-pixel illuminated left slope, shadowed right slope and horizontal
    base reconstruct the measured VUE scrollbar triangle. Pressure reverses
    the relief at the same coordinates rather than shifting the widget.
    """
    if direction not in ('up', 'down', 'left', 'right') or size != 12:
        raise ValueError('DomainOS arrows require a 12px intrinsic cell')
    image = blank(size, size)
    upper, lower = ('dark', 'light') if state in ('pressed', 'toggled') else ('light', 'dark')
    for y in range(11):
        left = 5-y//2
        right = 5+(y+1)//2
        for x in range(max(0, left), min(size, right+1)):
            image[y][x] = upper if x < left+2 else lower if x > right-2 else 'face'
    rect(image, 0, 10, 11, 1, lower)
    rect(image, 0, 11, 12, 1, lower)
    if direction == 'down': image = [list(reversed(row)) for row in reversed(image)]
    elif direction == 'left': image = [list(row) for row in zip(*image)]
    elif direction == 'right': image = [list(reversed(row)) for row in zip(*image)]
    return image


def stepper(state='normal', direction='up'):
    image = surface(state, width=16, height=16, down=True)
    # The trough extends under a free-standing Motif triangle; it is not a
    # raised square command button around a flat IRIX chevron.
    for y in range(2, 14):
        for x in range(2, 14): image[y][x] = 'trough'
    arrow = triangle(state, direction)
    for y, row in enumerate(arrow):
        for x, token in enumerate(row):
            if token is not None: image[y+2][x+2] = token
    return image


def toggle(kind, state='normal', selected=False, mixed=False):
    image = blank(14, 14)
    down = selected or mixed or state == 'pressed'
    fill = 'trough' if down else 'face'
    if kind == 'check':
        small = bevel(blank(12, 12, fill), down=down)
        for y, row in enumerate(small):
            for x, token in enumerate(row): image[y+1][x+1] = token
        # Motif uses a sunken square with select-color interior for its set
        # state; no red check mark. Its radio follows the same color policy.
        if mixed: rect(image, 4, 6, 6, 2, 'ink')
    elif kind == 'radio':
        upper, lower = ('dark', 'light') if down else ('light', 'dark')
        for y in range(1, 13):
            for x in range(1, 13):
                distance = abs(x-6.5)+abs(y-6.5)
                if distance <= 6:
                    image[y][x] = (upper if x+y < 13 else lower) if distance >= 4 else fill
    else: raise ValueError('Unknown Motif selection control')
    return image


def assets():
    """Original PNG/symbolic asset plans, independent of any installed theme."""
    result = {}
    for state in STATES:
        for kind, family, down, flat in (
            ('command', 'button', False, False), ('input', 'view', True, False),
            ('inset', 'window', True, False), ('menupanel', 'header', False, False),
            ('menustrip', 'header', False, False), ('menurow', 'header', False, state in ('normal', 'disabled')),
            ('scroll-trough', 'button', True, False), ('scroll-thumb', 'button', False, False),
            ('range-thumb', 'button', False, False), ('meter-fill', 'selection', False, False),
            ('tab', 'window', False, False)):
            image = surface(state, down=down, flat=flat)
            if kind == 'scroll-trough':
                for y in range(2, 22):
                    for x in range(2, 22): image[y][x] = 'trough'
            result[kind+'-'+state] = (image, family, 2)
        for direction in ('up', 'down', 'left', 'right'):
            result['arrow-'+direction+'-'+state] = (triangle(state, direction), 'button', 0)
            result['stepper-'+direction+'-'+state] = (stepper(state, direction), 'button', 0)
        for kind in ('check', 'radio'):
            for selected in (False, True):
                result[kind+('-on-' if selected else '-off-')+state] = (toggle(kind, state, selected), 'button', 0)
        result['check-mixed-'+state] = (toggle('check', state, mixed=True), 'button', 0)
    return result


def slices(image, border):
    height, width = len(image), len(image[0])
    if not border: return {'': image}
    n = border
    bounds = {'': (n, n, width-n, height-n), 'top': (n, 0, width-n, n),
              'bottom': (n, height-n, width-n, height), 'left': (0, n, n, height-n),
              'right': (width-n, n, width, height-n), 'topleft': (0, 0, n, n),
              'topright': (width-n, 0, width, n), 'bottomleft': (0, height-n, n, height),
              'bottomright': (width-n, height-n, width, height)}
    return {name: [row[x0:x1] for row in image[y0:y1]] for name, (x0, y0, x1, y1) in bounds.items()}


def svg(palette=None):
    palette = DEFAULT if palette is None else palette
    root = ET.Element('{'+NS+'}svg', {'version': '1.1', 'width': '768', 'height': '8192',
        'viewBox': '0 0 768 8192', 'shape-rendering': 'crispEdges'})
    ET.SubElement(root, '{'+NS+'}title').text = 'DomainOS SR10.4 — original Motif control reconstruction'
    ET.SubElement(root, '{'+NS+'}desc').text = 'GPL-3.0-or-later; integer semantic artwork; no HP code, fonts or bitmaps.'
    count = 0
    def add(identifier, pixels, family, *, inactive=False, disabled=False):
        nonlocal count
        x, y = (count % 16)*48, (count//16)*40
        count += 1
        group = ET.SubElement(root, '{'+NS+'}g', {'id': identifier, 'transform': f'translate({x},{y})'})
        height, width = len(pixels), len(pixels[0])
        ET.SubElement(group, '{'+NS+'}rect', {'x': '0', 'y': '0', 'width': str(width), 'height': str(height), 'fill': '#000000', 'fill-opacity': '0'})
        # Merge equal runs vertically. Separate one-pixel strips can acquire
        # translucent seams when QSvgRenderer stretches a solid frame interior.
        # A single rectangle keeps the same integer art without those seams.
        active, rectangles = {}, []
        for yy, row in enumerate(pixels):
            current, xx = {}, 0
            while xx < width:
                token, start = row[xx], xx
                while xx < width and row[xx] == token: xx += 1
                if token is None: continue
                key = (start, xx-start, token)
                current[key] = active.pop(key, [start, yy, xx-start, 0, token])
                current[key][3] += 1
            rectangles.extend(active.values())
            active = current
        rectangles.extend(active.values())
        for xx, yy, ww, hh, token in sorted(rectangles, key=lambda box: (box[1], box[0])):
            color = evaluate(pixel_plan(family, token, inactive=inactive, disabled=disabled), palette)
            ET.SubElement(group, '{'+NS+'}rect', {'x': str(xx), 'y': str(yy), 'width': str(ww), 'height': str(hh), 'fill': color})
    for name, (pixels, family, border) in assets().items():
        disabled = name.endswith('-disabled')
        for inactive in (False, True):
            prefix = 'dm-'+name+('-inactive' if inactive else '')
            for part, image in slices(pixels, border).items():
                add(prefix+('-'+part if part else ''), image, family, inactive=inactive, disabled=disabled)
    # Kvantum's native selection protocol names its interior *-checked-normal
    # and *-tristate-normal; it does not use GTK's on/off filename convention.
    for state in STATES:
        for inactive in (False, True):
            suffix = '-'+state+('-inactive' if inactive else '')
            # ComboBox and TreeExpander request their own native aliases.
            for name, direction in (('arrow', 'down'), ('arrow-down-down', 'down'),
                                    ('arrow-plus', 'right'), ('arrow-minus', 'down')):
                add('dm-'+name+suffix, triangle(state, direction), 'button', inactive=inactive, disabled=state == 'disabled')
            # Explicit transparent artwork suppresses the base theme's grip.
            add('dm-empty'+suffix, blank(1, 1), 'button', inactive=inactive, disabled=state == 'disabled')
            for kind in ('check', 'radio'):
                for selected in (False, True):
                    name = 'dm-'+kind+('-checked' if selected else '')+'-'+state+('-inactive' if inactive else '')
                    add(name, toggle(kind, state, selected), 'button', inactive=inactive, disabled=state == 'disabled')
            add('dm-check-tristate-'+state+('-inactive' if inactive else ''), toggle('check', state, mixed=True), 'button', inactive=inactive, disabled=state == 'disabled')
    # Plain windows, MDI titlebars, selected rows and keyboard focus markers.
    for state in STATES:
        for inactive in (False, True):
            suffix = '-'+state+('-inactive' if inactive else '')
            for kind, family in (('window', 'window'), ('view', 'view'), ('row', 'selection'), ('title', 'title'), ('tooltip', 'tooltip')):
                for part, image in slices(surface(state, flat=kind in ('window', 'row')), 2).items():
                    add('dm-'+kind+suffix+('-'+part if part else ''), image, family, inactive=inactive, disabled=state == 'disabled')
            focus = blank(16, 16)
            for i in range(0, 16, 2):
                focus[0][i] = focus[15][i] = focus[i][0] = focus[i][15] = 'focus'
            for part, image in slices(focus, 1).items():
                add('dm-focus'+suffix+('-'+part if part else ''), image, 'button', inactive=inactive, disabled=state == 'disabled')
            ring = blank(24, 24)
            for n in range(2):
                rect(ring, n, n, 24-2*n, 1, 'default'); rect(ring, n, n, 1, 24-2*n, 'default')
                rect(ring, n, 23-n, 24-2*n, 1, 'default'); rect(ring, 23-n, n, 1, 24-2*n, 'default')
            for part, image in slices(ring, 2).items():
                add('dm-default'+suffix+('-'+part if part else ''), image, 'button', inactive=inactive, disabled=state == 'disabled')
    # The default command overlay is requested without a normal state suffix.
    for inactive in (False, True):
        for part, image in slices(ring, 2).items():
            add('dm-command-default'+('-inactive' if inactive else '')+('-'+part if part else ''), image, 'button', inactive=inactive)
    ET.indent(root)
    return (ET.tostring(root, encoding='unicode', xml_declaration=False)+'\n').encode()


def kvconfig():
    general = '''# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
# New Motif/VUE SR10.4 adaptation; no extracted HP theme resources.
[%General]
author=mrmmx31
comment=DomainOS SR10.4 — integer Motif bevels and three-dimensional arrows
respect_DE=true
animate_states=false
button_contents_shift=false
composite=false
blurring=false
popup_blurring=false
translucent_windows=false
menu_shadow_depth=0
tooltip_shadow_depth=0
reduce_menu_opacity=0
reduce_window_opacity=0
alt_mnemonic=true
menubar_mouse_tracking=true
scrollable_menu=true
scroll_arrows=true
scrollbar_in_view=false
transient_scrollbar=false
transient_groove=false
scroll_width=16
scroll_min_extent=20
splitter_width=5
slider_width=14
slider_handle_width=16
slider_handle_length=24
check_size=14
layout_margin=6
layout_spacing=6
small_icon_size=16
button_icon_size=16
toolbar_icon_size=16
large_icon_size=32
toolbar_item_spacing=2
toolbar_interior_spacing=0
submenu_delay=250
submenu_overlap=1
combo_as_lineedit=false
combo_menu=true
combo_focus_rect=true
no_inactiveness=false
tooltip_delay=-1
menu_separator_height=6
[GeneralColors]
window.color=#78a0d5
window.text.color=#ffffff
base.color=#6688b5
alt.base.color=#78a0d5
button.color=#78a0d5
button.text.color=#ffffff
light.color=#c4d5ed
dark.color=#3e536e
text.color=#ffffff
disabled.text.color=#c4d5ed
highlight.color=#3297c7
highlight.text.color=#ffffff
tooltip.base.color=#78a0d5
tooltip.text.color=#ffffff
[Hacks]
kinetic_scrolling=false
normal_default_pushbutton=false
no_selection_tint=true
'''
    sections = []
    def panel(name, element, *, frame=2, minimum=0, extra='', interior=True):
        sections.append(f'[{name}]\nframe={str(bool(frame)).lower()}\nframe.element=dm-{element}\n'
                        + ''.join(f'frame.{side}={frame}\n' for side in ('top', 'bottom', 'left', 'right'))
                        + f'interior={str(interior).lower()}\ninterior.element=dm-{element}\n'
                        + 'text.shadow=false\ntext.italic=false\ntext.margin=true\n'
                        + 'text.margin.top=4\ntext.margin.bottom=4\ntext.margin.left=6\ntext.margin.right=6\n'
                        + (f'min_height={minimum}\n' if minimum else '')+extra)
    panel('Window', 'window', frame=0)
    sections.append('[Dialog]\ninherits=Window\n')
    panel('PanelButtonCommand', 'command', minimum=24, extra='focusFrame=true\ndefaultFrame=true\n')
    sections.append('[PanelButtonTool]\ninherits=PanelButtonCommand\n')
    panel('ToolbarButton', 'command', minimum=20)
    panel('GenericFrame', 'inset', interior=False)
    panel('LineEdit', 'input', minimum=22)
    panel('ComboBox', 'command', minimum=22, extra='indicator.element=dm-arrow\nindicator.size=12\n')
    sections.append('[DropDownButton]\ninherits=ComboBox\n[SpinBox]\ninherits=LineEdit\n[IndicatorArrow]\nindicator.element=dm-arrow\nindicator.size=12\n[IndicatorSpinBox]\ninherits=PanelButtonCommand\nindicator.element=dm-arrow\nindicator.size=12\n')
    panel('CheckBox', 'check', frame=0, minimum=18)
    panel('RadioButton', 'radio', frame=0, minimum=18)
    panel('Menu', 'menupanel')
    panel('MenuItem', 'menurow', minimum=20, extra='indicator.element=dm-arrow\nindicator.size=12\n')
    panel('MenuBar', 'menustrip')
    panel('MenuBarItem', 'menurow', minimum=20)
    panel('Toolbar', 'menustrip')
    panel('Tab', 'tab', minimum=22)
    panel('TabFrame', 'inset')
    panel('TabBarFrame', 'window', frame=0)
    panel('ToolboxTab', 'tab')
    panel('Dock', 'inset')
    panel('DockTitle', 'menustrip')
    panel('HeaderSection', 'command', extra='indicator.element=dm-arrow\nindicator.size=12\n')
    sections.append('[TreeExpander]\nindicator.element=dm-arrow\nindicator.size=12\n')
    panel('GroupBox', 'inset', interior=False)
    panel('ItemView', 'row', frame=0, minimum=18)
    sections.append('[Scrollbar]\nframe=false\ninterior=false\nindicator.element=dm-stepper\nindicator.size=16\n')
    panel('ScrollbarGroove', 'scroll-trough')
    panel('ScrollbarSlider', 'scroll-thumb', extra='indicator.element=dm-empty\nindicator.size=1\n')
    panel('Splitter', 'command', extra='indicator.element=dm-empty\nindicator.size=1\n')
    panel('Slider', 'scroll-trough')
    panel('SliderCursor', 'range-thumb', extra='indicator.element=dm-empty\nindicator.size=1\n')
    panel('Progressbar', 'scroll-trough')
    panel('ProgressbarContents', 'meter-fill')
    panel('ToolTip', 'tooltip')
    panel('Focus', 'focus', frame=1, interior=False, extra='frame.patternsize=2\n')
    panel('DefaultButton', 'default', frame=2, interior=False)
    panel('SizeGrip', 'command')
    panel('TitleBar', 'title', extra='indicator.element=dm-arrow\nindicator.size=12\n')
    return (general+'\n'+'\n'.join(sections)).encode()


def geometry_sha(contents):
    root = ET.fromstring(contents)
    structure = [(node.tag, sorted((key, value) for key, value in node.attrib.items() if key not in ('fill',))) for node in root.iter()]
    return hashlib.sha256(json.dumps(structure, separators=(',', ':')).encode()).hexdigest()
