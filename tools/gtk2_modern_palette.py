#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render Irixium's plain GTK2 RC with native KDE colors, without writes.

The Modern source has no engine or pixmaps. Its caller journals this small,
immutable RC bundle through the same transaction used for Classic palettes.
GTK2 has no separate Backdrop state and requires native RC reparsing in an
already running process; generating a file alone does not provide that reload.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from gtk2_palette import PreparedPalette, exported_palette
from theme_transaction import Failure, no_links

FALLBACK = {
    'theme_bg_color_breeze': '#c1c1c1', 'theme_fg_color_breeze': '#000000',
    'theme_base_color_breeze': '#c1c1c1', 'theme_text_color_breeze': '#000000',
    'theme_selected_bg_color_breeze': '#648bb3', 'theme_selected_fg_color_breeze': '#ffffff',
    'theme_button_background_normal_breeze': '#c1c1c1', 'theme_button_foreground_normal_breeze': '#000000',
    'theme_button_background_insensitive_breeze': '#919191', 'theme_button_foreground_insensitive_breeze': '#606060',
    'insensitive_bg_color_breeze': '#919191', 'insensitive_fg_color_breeze': '#606060',
    'insensitive_base_color_breeze': '#c1c1c1', 'insensitive_base_fg_color_breeze': '#606060',
    'insensitive_selected_bg_color_breeze': '#648bb3', 'insensitive_selected_fg_color_breeze': '#606060',
    'tooltip_background_breeze': '#d0cfb2', 'tooltip_text_breeze': '#000000',
    'error_color_breeze': '#ff0000', 'link_color_breeze': '#0000cd', 'link_visited_color_breeze': '#660066',
}


def gtk2_rc(original: str, palette: dict[str, str] | None = None) -> str:
    """Preserve Modern's RC declarations; replace only its color assignments."""
    values = FALLBACK if palette is None else palette
    if 'style "irixium-default"' not in original or re.search(r'\bengine\s|\binclude\s|(?:overlay_)?file\s*=', original):
        raise Failure('A origem não é o RC plano Irixium reconhecido.')
    text = original.replace('"irixium-default"', '"irixium-kde-default"')

    def assignment(match):
        field, state = match[1], match[2]
        if state == 'SELECTED':
            name = 'theme_selected_bg_color_breeze' if field in ('bg', 'base') else 'theme_selected_fg_color_breeze'
        elif state == 'INSENSITIVE':
            name = {'bg': 'insensitive_bg_color_breeze', 'fg': 'insensitive_fg_color_breeze',
                    'base': 'insensitive_base_color_breeze', 'text': 'insensitive_base_fg_color_breeze'}[field]
        else:
            name = {'bg': 'theme_bg_color_breeze', 'fg': 'theme_fg_color_breeze',
                    'base': 'theme_base_color_breeze', 'text': 'theme_text_color_breeze'}[field]
        value = values.get(name)
        if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
            raise Failure('Papel de cor GTK2 Modern ausente ou inválido: ' + name)
        return field + '[' + state + '] = "' + value.lower() + '"'

    text = re.sub(r'(bg|fg|base|text)\[(NORMAL|PRELIGHT|ACTIVE|SELECTED|INSENSITIVE)\]\s*=\s*"#[0-9a-fA-F]{6}"', assignment, text)
    pairs = {'theme_bg_color': 'theme_bg_color_breeze', 'theme_fg_color': 'theme_fg_color_breeze',
             'theme_base_color': 'theme_base_color_breeze', 'theme_text_color': 'theme_text_color_breeze',
             'theme_selected_bg_color': 'theme_selected_bg_color_breeze', 'theme_selected_fg_color': 'theme_selected_fg_color_breeze',
             'theme_tooltip_bg_color': 'tooltip_background_breeze', 'theme_tooltip_fg_color': 'tooltip_text_breeze'}
    text = re.sub(r'gtk-color-scheme\s*=\s*"(?:[^"\\]|\\.)*"',
                  lambda _: 'gtk-color-scheme = ' + json.dumps('\n'.join(name+':'+values[role] for name, role in pairs.items())), text, flags=re.S)
    extra = ['\nstyle "irixium-kde-button" = "irixium-kde-default" {']
    for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
        disabled = state == 'INSENSITIVE'
        bg = values['theme_button_background_insensitive_breeze' if disabled else 'theme_button_background_normal_breeze']
        fg = values['theme_button_foreground_insensitive_breeze' if disabled else 'theme_button_foreground_normal_breeze']
        if state == 'SELECTED':
            bg, fg = values['theme_selected_bg_color_breeze'], values['theme_selected_fg_color_breeze']
        extra += [f'  bg[{state}] = "{bg}"', f'  fg[{state}] = "{fg}"']
    extra += ['}', 'class "GtkButton" style : rc "irixium-kde-button"',
              'widget_class "*<GtkButton>*" style : rc "irixium-kde-button"',
              'style "irixium-kde-tooltip" = "irixium-kde-default" {',
              '  bg[NORMAL] = "'+values['tooltip_background_breeze']+'"',
              '  fg[NORMAL] = "'+values['tooltip_text_breeze']+'"', '}',
              'widget "gtk-tooltip*" style : rc "irixium-kde-tooltip"']
    extra += ['style "irixium-kde-header" = "irixium-kde-default" {',
              '  bg[NORMAL] = "'+values.get('theme_header_background_breeze', values['theme_bg_color_breeze'])+'"',
              '  fg[NORMAL] = "'+values.get('theme_header_foreground_breeze', values['theme_fg_color_breeze'])+'"',
              '  bg[PRELIGHT] = "'+values['theme_selected_bg_color_breeze']+'"',
              '  bg[ACTIVE] = "'+values['theme_selected_bg_color_breeze']+'"',
              '  fg[PRELIGHT] = "'+values['theme_selected_fg_color_breeze']+'"',
              '  fg[ACTIVE] = "'+values['theme_selected_fg_color_breeze']+'"',
              '}', 'class "GtkMenuBar" style : rc "irixium-kde-header"',
              'style "irixium-kde-menu-selection" = "irixium-kde-default" {',
              '  bg[PRELIGHT] = "'+values['theme_selected_bg_color_breeze']+'"',
              '  fg[PRELIGHT] = "'+values['theme_selected_fg_color_breeze']+'"',
              '  bg[ACTIVE] = "'+values['theme_selected_bg_color_breeze']+'"',
              '  fg[ACTIVE] = "'+values['theme_selected_fg_color_breeze']+'"', '}',
              'widget_class "*<GtkMenuItem>*" style : rc "irixium-kde-menu-selection"',
              'widget "*GtkMenuItem*" style : rc "irixium-kde-menu-selection"',
              'widget "*GtkMenuBar*" style : rc "irixium-kde-header"']
    text = re.sub(r'((?:class|widget|widget_class) .* style) "', r'\1 : rc "', text)
    return '# Generated Irixium KDE color roles; original metrics, no engine or assets.\n' + text.rstrip() + '\n' + '\n'.join(extra) + '\n'


def prepare_modern(theme: Path, colors: bytes, destination: Path) -> PreparedPalette:
    """Return an immutable RC/manifest bundle; caller owns all actual writes."""
    theme, destination = Path(theme), Path(destination)
    no_links(theme); no_links(destination)
    rc = theme/'gtk-2.0/gtkrc'; no_links(rc)
    raw = rc.read_bytes()
    if len(raw) > 256*1024:
        raise Failure('RC Irixium inesperadamente grande.')
    palette = exported_palette(colors)
    try:
        original = raw.decode('utf-8')
    except UnicodeError as exc:
        raise Failure('RC Irixium não é UTF-8.') from exc
    rendered = gtk2_rc(original, palette).encode()
    identity = {'format': 1, 'theme': 'Irixium', 'source_rc_sha256': hashlib.sha256(raw).hexdigest(),
                'roles': palette, 'rendered_rc_sha256': hashlib.sha256(rendered).hexdigest(),
                'limits': ['plain native GTK2 RC; no engine or assets', 'GTK2 has no separate backdrop state',
                           'existing processes require native RC reparsing']}
    token = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    directory = destination/token; gtkrc = directory/'gtkrc'
    manifest = dict(identity, id=token, asset_count=0, generated={'gtkrc': hashlib.sha256(rendered).hexdigest()})
    files = {gtkrc: rendered, directory/'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()}
    return PreparedPalette(directory, gtkrc, files, manifest)
