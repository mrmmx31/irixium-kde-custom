#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare Classic GTK2 pixmaps from KDE's exported color roles.

This module performs no writes and selects no theme. Its caller journals the
returned files and the optional RC include through its existing transaction.
Generated assets live in an immutable, content-addressed directory under the
explicit XDG destination. No GTK engine, source artwork or user RC is replaced.
GTK2 still needs its native pixmap engine. Updating an already running process
requires native RC reparsing; generation alone does not supply that lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import re

from theme_transaction import Failure, no_links

FORMAT = 1
BEGIN = '\n# BEGIN IRIX CLASSIC KDE GTK2 PALETTE\n'
END = '# END IRIX CLASSIC KDE GTK2 PALETTE\n'
STATES = ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE')
REQUIRED = (
    'theme_bg_color_breeze', 'theme_fg_color_breeze',
    'theme_base_color_breeze', 'theme_text_color_breeze',
    'theme_selected_bg_color_breeze', 'theme_selected_fg_color_breeze',
    'theme_button_background_normal_breeze', 'theme_button_foreground_normal_breeze',
    'theme_button_background_insensitive_breeze', 'theme_button_foreground_insensitive_breeze',
    'insensitive_bg_color_breeze', 'insensitive_fg_color_breeze',
    'insensitive_base_color_breeze', 'insensitive_base_fg_color_breeze',
    'insensitive_selected_bg_color_breeze',
    'tooltip_background_breeze', 'tooltip_text_breeze',
    'error_color_breeze', 'link_color_breeze', 'link_visited_color_breeze',
)
_COLOR = re.compile(r'#[0-9a-fA-F]{6}\Z')
_ASSET = re.compile(r'(?:overlay_)?file\s*=\s*"\.\./common/assets/([a-z0-9-]+\.png)"')
_DEFINE = re.compile(r'^\s*@define-color\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(#[0-9a-fA-F]{6})\s*;\s*$', re.M)


def _hex(rgb):
    return '#%02x%02x%02x' % tuple(rgb)


def _rgb(value):
    if not isinstance(value, str) or not _COLOR.fullmatch(value):
        raise Failure('Cor GTK2 exportada inválida: ' + str(value))
    return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))


def exported_palette(contents: bytes) -> dict[str, str]:
    """Read the bounded, literal hexadecimal form emitted by KDE GTK Config.

    Do not approximate KColorScheme's Disabled/Inactive effects by reading only
    kdeglobals: those effective groups are already computed by KDE's exporter.
    """
    if len(contents) > 256 * 1024:
        raise Failure('Exportação de cores GTK inesperadamente grande.')
    try:
        text = contents.decode('utf-8')
    except UnicodeError as exc:
        raise Failure('Exportação de cores GTK não é UTF-8.') from exc
    values = dict((name, color.lower()) for name, color in _DEFINE.findall(text))
    missing = sorted(set(REQUIRED) - values.keys())
    if missing:
        raise Failure('Papéis KDE ausentes da exportação GTK: ' + ', '.join(missing))
    return values


def _role(palette, name):
    # Header is optional on older exporters; native KDE uses Window when that
    # color set is absent. All other required roles are checked before rendering.
    fallback = {'theme_header_background_breeze': 'theme_bg_color_breeze',
                'theme_header_foreground_breeze': 'theme_fg_color_breeze',
                'theme_header_foreground_insensitive_breeze': 'insensitive_fg_color_breeze',
                'theme_button_decoration_focus_breeze': 'theme_selected_bg_color_breeze'}
    return _rgb(palette.get(name, palette.get(fallback.get(name, ''), '')))


def asset_color_plan(asset: str, color: str) -> dict:
    """Return a shared semantic plan, usable for PNG or GTK3/4 SVG expressions.

    The bands stay at their existing pixels. Tone is the original distance from
    the family's face toward black/white, never a resize or a global RGB map.
    Checkbox/radio shapes use native NegativeText/LinkText instead of fixed ink.
    """
    rgb = _rgb(color)
    name = asset.removesuffix('.png')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise Failure('Nome de asset GTK2 inválido.')
    disabled = name.endswith('-disabled')
    foreground = 'theme_button_foreground_insensitive_breeze' if disabled else 'theme_button_foreground_normal_breeze'
    if name.startswith('arrow-'):
        return {'role': foreground, 'mix': 0.0, 'endpoint': '#000000'}
    if name == 'focus':
        return {'role': 'theme_button_decoration_focus_breeze', 'mix': 0.0, 'endpoint': '#000000'}
    # In the original selection builder, only the colored mark/shadow becomes
    # #858585 for Disabled; the square/diamond bevel never uses this value.
    if disabled and name.startswith(('check-', 'radio-')) and rgb == (133, 133, 133):
        return {'role': 'theme_button_foreground_insensitive_breeze', 'mix': 0.0, 'endpoint': '#000000'}
    if name.startswith(('stepper-', 'optionmark-')) and rgb == (0, 0, 0):
        return {'role': foreground, 'mix': 0.0, 'endpoint': '#000000'}
    if rgb in ((204, 0, 0), (102, 0, 0)) and name.startswith('check-'):
        return {'role': 'error_color_breeze', 'mix': 0.0 if rgb[0] == 204 else 0.5, 'endpoint': '#000000'}
    if rgb in ((0, 0, 204), (0, 0, 102)) and name.startswith('radio-'):
        return {'role': 'link_color_breeze', 'mix': 0.0 if rgb[2] == 204 else 0.5, 'endpoint': '#000000'}
    if name.startswith('input-'):
        if rgb == (182, 182, 170):
            return {'role': 'insensitive_base_color_breeze' if disabled else 'theme_base_color_breeze', 'mix': 0.0, 'endpoint': '#000000'}
        role, anchor = ('insensitive_bg_color_breeze' if disabled else 'theme_bg_color_breeze'), 193
    elif name.startswith('meter-fill-'):
        if rgb in ((113, 158, 158), (142, 170, 170)):
            return {'role': 'insensitive_selected_bg_color_breeze' if disabled else 'theme_selected_bg_color_breeze', 'mix': 0.0, 'endpoint': '#000000'}
        role, anchor = ('theme_button_background_insensitive_breeze' if disabled else 'theme_button_background_normal_breeze'), 153
    elif name.startswith('menurow-'):
        role, anchor = 'theme_selected_bg_color_breeze', 223 if name.endswith('-focused') else 179
    elif name.startswith('menustrip-'):
        role, anchor = 'theme_header_background_breeze', 193
    elif name.startswith(('command-', 'palettebutton-', 'spin-', 'option-', 'optionmark-', 'stepper-',
                          'scroll-thumb-', 'scroll-grip-', 'range-thumb-', 'range-grip-', 'check-', 'radio-')):
        role, anchor = ('theme_button_background_insensitive_breeze' if disabled else 'theme_button_background_normal_breeze'), 153
    elif name.startswith(('menupanel-', 'scroll-trough-', 'inset-', 'tab-', 'notebook-page', 'separator-')) or name == 'stipple':
        role, anchor = ('insensitive_bg_color_breeze' if disabled else 'theme_bg_color_breeze'), 193
    else:
        raise Failure('Família de asset GTK2 sem papel definido: ' + asset)
    if not (rgb[0] == rgb[1] == rgb[2]):
        raise Failure('Cor de asset GTK2 sem papel definido: ' + asset + ' ' + color)
    value = rgb[0]
    fraction = (anchor-value)/anchor if value < anchor else (value-anchor)/(255-anchor)
    return {'role': role, 'mix': fraction, 'endpoint': '#000000' if value < anchor else '#ffffff'}


def asset_color(asset: str, color: str, palette: dict[str, str]) -> str:
    plan = asset_color_plan(asset, color)
    source, endpoint = _role(palette, plan['role']), _rgb(plan['endpoint'])
    ratio = plan['mix']
    return _hex(round(a*(1-ratio) + b*ratio) for a, b in zip(source, endpoint))


def asset_css_expression(asset: str, color: str) -> str:
    """Same family plan for the native GTK3/4 symbolic SVG recolor helper."""
    plan = asset_color_plan(asset, color)
    role = '@' + plan['role']
    return role if not plan['mix'] else f"mix({role}, {plan['endpoint']}, {plan['mix']:.8f})"


def _rc_colors(text: str, palette: dict[str, str]) -> str:
    names = {name: 'irixclassic-kde-' + name.removeprefix('irixclassic-')
             for name in re.findall(r'style\s+"(irixclassic-[a-z-]+)"', text)}
    for old, new in names.items():
        text = text.replace('"'+old+'"', '"'+new+'"')
    current = 'default'
    output = []
    colorline = re.compile(r'(\s*)(bg|fg|base|text)\[(\w+)\]\s*=\s*"#[0-9a-fA-F]{6}"')
    for line in text.splitlines():
        match = re.match(r'style "irixclassic-kde-([a-z-]+)"', line)
        if match:
            current = match[1]
        match = colorline.fullmatch(line)
        if match:
            indent, field, state = match.groups()
            if state not in STATES:
                raise Failure('Estado GTK2 desconhecido.')
            if state == 'SELECTED':
                role = 'theme_selected_bg_color_breeze' if field in ('bg', 'base') else 'theme_selected_fg_color_breeze'
            elif state == 'INSENSITIVE':
                role = {'bg':'insensitive_bg_color_breeze', 'fg':'insensitive_fg_color_breeze',
                        'base':'insensitive_base_color_breeze', 'text':'insensitive_base_fg_color_breeze'}[field]
            elif current == 'tooltip':
                role = 'tooltip_background_breeze' if field in ('bg', 'base') else 'tooltip_text_breeze'
            elif current == 'menuitem' and field == 'bg' and state in ('PRELIGHT', 'ACTIVE'):
                role = 'theme_selected_bg_color_breeze'
            elif current == 'sidebar' and field == 'base':
                role = 'theme_bg_color_breeze'
            else:
                role = {'bg':'theme_bg_color_breeze', 'fg':'theme_fg_color_breeze',
                        'base':'theme_base_color_breeze', 'text':'theme_text_color_breeze'}[field]
            line = f'{indent}{field}[{state}] = "{_hex(_role(palette, role))}"'
        elif line.startswith('gtk-color-scheme ='):
            pairs = {'bg_color':'theme_bg_color_breeze', 'fg_color':'theme_fg_color_breeze',
                     'base_color':'theme_base_color_breeze', 'text_color':'theme_text_color_breeze',
                     'selected_bg_color':'theme_selected_bg_color_breeze', 'selected_fg_color':'theme_selected_fg_color_breeze',
                     'tooltip_bg_color':'tooltip_background_breeze', 'tooltip_fg_color':'tooltip_text_breeze'}
            line = 'gtk-color-scheme = ' + json.dumps('\\n'.join(k+':'+_hex(_role(palette,v)) for k,v in pairs.items()))
            # RC needs one escaped newline, not a literal slash plus newline.
            line = line.replace('\\\\n', '\\n')
        elif 'GtkWidget::link-color' in line or 'GtkWidget::visited-link-color' in line:
            role = 'link_visited_color_breeze' if 'visited-link' in line else 'link_color_breeze'
            line = re.sub(r'"#[0-9a-fA-F]{6}"', '"'+_hex(_role(palette, role))+'"', line)
        elif re.match(r'(?:class|widget|widget_class) .* style "', line):
            line = line.replace(' style "', ' style : rc "')
        output.append(line)
    # Native GtkState has no separate backdrop state. Button's normal/disabled
    # text is nevertheless a distinct KDE role, not the Window foreground.
    extra = ['\nstyle "irixclassic-kde-button" = "irixclassic-kde-default" {']
    for state in STATES:
        role = 'theme_button_foreground_insensitive_breeze' if state == 'INSENSITIVE' else 'theme_button_foreground_normal_breeze'
        extra.append(f'  fg[{state}] = "{_hex(_role(palette, role))}"')
    extra += ['}', 'class "GtkButton" style : rc "irixclassic-kde-button"',
              'widget_class "*<GtkButton>*" style : rc "irixclassic-kde-button"',
              'class "GtkOptionMenu" style : rc "irixclassic-kde-button"',
              'style "irixclassic-kde-menu-selection" = "irixclassic-kde-menuitem" {',
              '  fg[PRELIGHT] = "'+_hex(_role(palette, 'theme_selected_fg_color_breeze'))+'"',
              '  fg[ACTIVE] = "'+_hex(_role(palette, 'theme_selected_fg_color_breeze'))+'"',
              '}', 'widget_class "*<GtkMenuItem>*" style : rc "irixclassic-kde-menu-selection"']
    extra += ['style "irixclassic-kde-header" = "irixclassic-kde-menutitle" {',
              '  bg[NORMAL] = "'+_hex(_role(palette, 'theme_header_background_breeze'))+'"',
              '  fg[NORMAL] = "'+_hex(_role(palette, 'theme_header_foreground_breeze'))+'"',
              '  fg[PRELIGHT] = "'+_hex(_role(palette, 'theme_selected_fg_color_breeze'))+'"',
              '  fg[ACTIVE] = "'+_hex(_role(palette, 'theme_selected_fg_color_breeze'))+'"',
              '  fg[INSENSITIVE] = "'+_hex(_role(palette, 'theme_header_foreground_insensitive_breeze'))+'"',
              '}', 'widget_class "*<GtkMenuBar>*" style : rc "irixclassic-kde-header"']
    return '\n'.join(output+extra)+'\n'


@dataclass(frozen=True)
class PreparedPalette:
    directory: Path
    gtkrc: Path
    files: dict[Path, bytes]
    manifest: dict


def prepare(theme: Path, colors: bytes, destination: Path) -> PreparedPalette:
    """Render an immutable bundle in memory; caller decides/journals the writes.

    ``theme`` is the installed original IrixClassic directory, ``destination``
    is the caller's private XDG generated-resource root. It may contain spaces.
    The result needs no checkout path or runtime Python in a GTK application.
    """
    from PIL import Image
    theme, destination = Path(theme), Path(destination)
    no_links(theme); no_links(destination)
    palette = exported_palette(colors)
    for name in REQUIRED:
        _rgb(palette[name])
    rcfile = theme/'gtk-2.0/gtkrc'
    no_links(rcfile)
    original = rcfile.read_bytes()
    if len(original) > 256*1024:
        raise Failure('RC Classic inesperadamente grande.')
    text = original.decode('utf-8')
    if 'style "irixclassic-default"' not in text or 'engine "pixmap"' not in text:
        raise Failure('A origem não é o RC pixmap IrixClassic reconhecido.')
    names = sorted(set(_ASSET.findall(text)))
    if not names:
        raise Failure('O RC Classic não contém assets pixmap.')
    assignments = re.findall(r'(?:overlay_)?file\s*=\s*"([^"]+)"', text)
    if any(value != '../common/assets/'+Path(value).name or Path(value).name not in names
           for value in assignments) or re.search(r'^\s*include\s', text, re.M):
        raise Failure('O RC Classic contém dependência externa não reconhecida.')
    from gtk2_scrollbar_assets import adapt_scrollbars
    source_raws = {}

    def read_asset(name):
        # The helper requests only the original Classic stepper maps. All
        # other inputs must already belong to the validated source RC.
        if name not in names and not re.fullmatch(
                r'stepper-(?:up|down|left|right)-(?:normal|pressed|toggled|disabled)\.png', name):
            raise Failure('Asset da seta Classic fora da origem reconhecida: ' + name)
        path = theme/'common/assets'/name
        no_links(path)
        raw = path.read_bytes()
        if len(raw) > 256*1024:
            raise Failure('Asset Classic inesperadamente grande.')
        source_raws[name] = raw
        return raw

    try:
        scrollbars = adapt_scrollbars(text, read_asset)
    except ValueError as error:
        raise Failure('Setas de rolagem Classic não reconhecidas: ' + str(error)) from error
    text = scrollbars.text
    rendered, source_hashes, plans = {}, {}, {}
    for name in names:
        read_asset(name)
    source_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in source_raws.items()}
    for name, raw in sorted({**source_raws, **scrollbars.assets}.items()):
        with Image.open(io.BytesIO(raw)) as source:
            if source.width > 256 or source.height > 256:
                raise Failure('Dimensão de asset Classic inesperada.')
            image = source.convert('RGBA')
        pixels, plan = [], {}
        for red, green, blue, alpha in image.getdata():
            color = _hex((red, green, blue))
            if alpha:
                plan[color] = asset_color_plan(name, color)
                red, green, blue = _rgb(asset_color(name, color, palette))
            pixels.append((red, green, blue, alpha))
        image.putdata(pixels)
        buffer = io.BytesIO(); image.save(buffer, format='PNG', optimize=True)
        rendered[name] = buffer.getvalue(); plans[name] = plan
    adapted = _rc_colors(text, palette)
    # GTK2's gtk_rc_find_pixmap_in_path prepends the current RC directory even
    # for an absolute image filename. Keep these names relative to this bundle;
    # only the user RC include points to an absolute, safely quoted location.
    adapted = _ASSET.sub(lambda match: 'file = '+json.dumps('assets/'+match[1])
                        if not match[0].startswith('overlay_') else 'overlay_file = '+json.dumps('assets/'+match[1]), adapted)
    rcbytes = ('# KDE palette generated; no engine/input change.\n'+adapted).encode()
    identity = {'format':FORMAT, 'source_rc_sha256':hashlib.sha256(original).hexdigest(),
                'source_assets':source_hashes, 'roles':palette, 'plans':plans,
                'scrollbars': scrollbars.manifest,
                'rendered_rc_sha256':hashlib.sha256(rcbytes).hexdigest(),
                'rendered_assets':{name:hashlib.sha256(value).hexdigest() for name,value in rendered.items()}}
    token = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',',':')).encode()).hexdigest()
    directory = destination/token
    gtkrc = directory/'gtkrc'
    files = {directory/'assets'/name:value for name,value in rendered.items()}
    files[gtkrc] = rcbytes
    manifest = dict(identity, id=token, asset_count=len(rendered),
                    generated={str(path.relative_to(directory)):hashlib.sha256(value).hexdigest() for path,value in files.items()},
                    limits=['explicit generation; no color watcher or process reload',
                            'GTK2 GtkState has no distinct backdrop palette'])
    files[directory/'manifest.json'] = (json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    return PreparedPalette(directory, gtkrc, files, manifest)


def include_palette(original: bytes, gtkrc: Path | None) -> bytes:
    """Return RC with exactly one owned block; never edit arbitrary includes."""
    text = original.decode('utf-8')
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise Failure('Marcadores GTK2 de paleta próprios estão inconsistentes.')
    if BEGIN in text:
        start, end = text.index(BEGIN), text.index(END)
        if end < start:
            raise Failure('Marcadores GTK2 de paleta próprios invertidos.')
        stop = end+len(END)
        text = text[:start]+text[stop:]
    if gtkrc is not None:
        gtkrc = Path(gtkrc)
        no_links(gtkrc)
        if '\n' in str(gtkrc) or '\r' in str(gtkrc):
            raise Failure('Caminho RC GTK2 contém quebra de linha.')
        text += BEGIN+'include '+json.dumps(str(gtkrc),ensure_ascii=False)+'\n'+END
    return text.encode('utf-8')
