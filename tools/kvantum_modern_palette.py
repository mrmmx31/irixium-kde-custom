#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure, conservative palette adapter for the original Irixium Kvantum art.

The recognized upstream input is never rewritten on disk. Only paint literals
change in its XML bytes; geometry, opacity, references, metadata and all original
IDs stay intact. Two added, separately named copies resolve existing shared-art
conflicts: ToolTip versus Menu and HeaderSection versus TabFrame. The generated
configuration refers to those copies only for the conflicting contexts.

The caller owns paths, journaling, native style notifications and rollback. A
new upstream revision needs a fresh audit, rather than a blanket RGB replacement.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import re
import xml.etree.ElementTree as ET

SOURCE_SVG_SHA256 = '0da336caf24d7c6a63476d12950b6181ff536533d55f03b59aed0574f2e6ea32'
SOURCE_CONFIG_SHA256 = '44867332bb1bee48931204a30687681d155004db41ed41bebc069ca99dd7cc6e'
RECIPE = 'irixium-kvantum-semantic-1'
_SVG = 'http://www.w3.org/2000/svg'
_XLINK = 'http://www.w3.org/1999/xlink'
_PAINT = re.compile(r'(?P<prefix>(?:^|;)\s*(?:fill|stroke)\s*:\s*)(?P<color>#[0-9a-fA-F]{6})(?=\s*(?:;|$))')
_ATTRIBUTE = re.compile(r'(?P<name>[\w:.-]+)\s*=\s*(?P<quote>[\"\'])(?P<value>.*?)(?P=quote)', re.S)
_TOKENS = re.compile(r'<(?:[^>\"\']|\"[^\"]*\"|\'[^\']*\')*>', re.S)
_STATE = re.compile(r'^(.+?)-(normal|focused|pressed|toggled|disabled)(?:-|$)')
_HEX = re.compile(r'#[0-9a-fA-F]{6}\Z')
_ORPHANS = frozenset(('path784', 'path2', 'path700', 'path704', 'path66', 'path64', 'path65'))
_SPECIAL = frozenset(('tbar-handle', 'tbar-separator', 'marrow-separator',
                      'header-separator', 'button-default-indicator', 'dock-close', 'dock-restore'))
_FAMILIES = frozenset(('window', 'common', 'ledit', 'tbtn', 'bbb', 'checkbox',
    'checkbox-checked', 'checkbox-tristate', 'radio', 'radio-checked',
    'arrow-right', 'arrow-left', 'arrow-up', 'arrow-down', 'cind', 'trough',
    'trough-tick', 'sgrip', 'gbox', 'iview', 'tree-plus', 'tree-minus', 'tab',
    'tab-separator', 'tab-close', 'floating-tab', 'floating-tab-separator',
    'scrollslide', 'scrolly', 'tbb', 'tbf', 'mbord', 'mbi', 'slind', 'pbc',
    'sarrow-up', 'sarrow-down', 'sarrow-left', 'sarrow-right', 'splitter-grip',
    'marrow-tearoff', 'marrow-right', 'marrow-left', 'dbar', 'mubar', 'menii',
    'menit', 'sparrow-up', 'sparrow-down', 'sparrow-plus', 'sparrow-minus'))
REQUIRED = ('theme_bg_color_breeze', 'theme_fg_color_breeze',
    'theme_base_color_breeze', 'theme_text_color_breeze',
    'theme_selected_bg_color_breeze', 'theme_selected_fg_color_breeze',
    'theme_button_background_normal_breeze', 'theme_button_foreground_normal_breeze',
    'theme_button_background_insensitive_breeze', 'theme_button_foreground_insensitive_breeze',
    'insensitive_bg_color_breeze', 'insensitive_fg_color_breeze',
    'insensitive_base_color_breeze', 'insensitive_base_fg_color_breeze',
    'insensitive_selected_bg_color_breeze', 'insensitive_selected_fg_color_breeze',
    'tooltip_background_breeze', 'tooltip_text_breeze',
    'error_color_breeze', 'warning_color_breeze')


def _sha(contents):
    return hashlib.sha256(contents).hexdigest()


def _rgb(color):
    if not isinstance(color, str) or not _HEX.fullmatch(color):
        raise ValueError('Invalid exported KDE color: ' + repr(color))
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _role(palette, role):
    # KDE's exporter uses Window when the optional Header color set is absent.
    optional = {'theme_header_background_breeze': 'theme_bg_color_breeze',
                'theme_header_foreground_breeze': 'theme_fg_color_breeze'}
    return _rgb(palette.get(role, palette.get(optional.get(role, ''), '')))


def _tone(palette, role, source, anchor):
    """Keep a band's distance from its original face toward black or white.

    For the few chromatic original faces, luminance is the audited shade axis;
    this changes hue to the selected native role while keeping the same band
    order. It does not introduce or move any pixels, paths or gradients.
    """
    rgb, base = _rgb(source), _rgb(anchor)
    value = sum(w * c for w, c in zip((.2126, .7152, .0722), rgb))
    face = sum(w * c for w, c in zip((.2126, .7152, .0722), base))
    if value < face:
        amount, endpoint = (face - value) / face, 0
    elif value > face:
        amount, endpoint = (value - face) / (255 - face), 255
    else:
        amount, endpoint = 0.0, 0
    result = tuple(round(c * (1 - amount) + endpoint * amount) for c in _role(palette, role))
    return '#%02x%02x%02x' % result


def _context(element, parents):
    current = element
    while current is not None:
        name = current.get('id', '')
        match = _STATE.match(name)
        if match:
            if match[1] not in _FAMILIES:
                raise ValueError('Unclassified Irixium SVG family: ' + name)
            return match[1], match[2], name
        if name in _SPECIAL:
            return name, 'normal', name
        if name in _ORPHANS:
            return 'unreferenced-editor-path', 'normal', name
        current = parents.get(current)
    raise ValueError('Paint without an audited Irixium SVG context: ' + element.get('id', '?'))


def _paint(palette, family, state, source, element, override=None):
    disabled = state == 'disabled'
    button = 'theme_button_background_insensitive_breeze' if disabled else 'theme_button_background_normal_breeze'
    ink = 'theme_button_foreground_insensitive_breeze' if disabled else 'theme_button_foreground_normal_breeze'
    window = 'insensitive_bg_color_breeze' if disabled else 'theme_bg_color_breeze'
    view = 'insensitive_base_color_breeze' if disabled else 'theme_base_color_breeze'
    selection = 'insensitive_selected_bg_color_breeze' if disabled else 'theme_selected_bg_color_breeze'
    if override:
        return _tone(palette, override, source, '#c1c1c1')
    if family == 'unreferenced-editor-path':
        return source
    if family == 'window':
        return _tone(palette, window, source, '#c1c1c1')
    if family == 'common':
        role, anchor = (view, '#8daaa9') if source == '#8daaa9' else (window, '#c1c1c1')
    elif family == 'ledit':
        role, anchor = ((view, '#be9292') if source in ('#be9292', '#553434', '#8b6a6a')
                        else (window, '#c1c1c1'))
    elif family == 'iview':
        # Original normal borders are bright green, not an extra configurable
        # status indicator. They belong to the same unselected View surface.
        if state == 'normal':
            return '#%02x%02x%02x' % _role(palette, view)
        role, anchor = selection, '#78a0a0' if state != 'focused' else '#8cafaf'
    elif family in ('tbtn', 'bbb', 'scrollslide'):
        role, anchor = (selection, '#87aaca') if family == 'bbb' and state == 'toggled' else (button, '#999999')
    elif family in ('scrolly', 'trough'):
        role, anchor = window, '#c1c1c1'
    elif family.startswith(('checkbox', 'radio')):
        if source in ('#e80000', '#e00a0a'):
            return '#%02x%02x%02x' % _role(palette, 'error_color_breeze')
        if source == '#f0f043':
            return '#%02x%02x%02x' % _role(palette, 'warning_color_breeze')
        role, anchor = button, '#999999'
    elif family == 'cind':
        # This indicator has a two-tone glyph, unlike the one-color generic
        # arrows. Keep its lighter band instead of collapsing both into ink.
        return _tone(palette, ink, source, '#252525')
    elif family.startswith(('arrow-', 'sparrow-', 'tree-')):
        role = ('insensitive_base_fg_color_breeze' if disabled else 'theme_text_color_breeze') if family.startswith('tree-') else ink
        # Group-level cyan attributes in plus/minus are overridden by all
        # rendered descendants. Keep them themed as foreground as well.
        return '#%02x%02x%02x' % _role(palette, role)
    elif family.startswith('sarrow-'):
        # In this family paths are the arrow; rectangles draw the original
        # 18px bevel. Do not confuse the glyph with similarly dark band colors.
        if element.tag == '{'+_SVG+'}path':
            return '#%02x%02x%02x' % _role(palette, ink)
        role, anchor = button, '#999999'
    elif family in ('sgrip', 'slind'):
        if source in ('#000000', '#2e2e2e'):
            return '#%02x%02x%02x' % _role(palette, ink)
        role, anchor = button, '#999999'
    elif family in ('tab-close', 'dock-close', 'dock-restore', 'button-default-indicator', 'trough-tick'):
        if source in ('#000000', '#00ffff'):
            role = 'theme_header_foreground_breeze' if family.startswith('dock-') else ink
            return '#%02x%02x%02x' % _role(palette, role)
        role, anchor = button, '#999999'
    elif family.startswith('marrow-') or family == 'marrow-separator':
        if family == 'marrow-tearoff' or family == 'marrow-separator':
            role, anchor = window, '#c1c1c1'
        else:
            role = 'theme_selected_fg_color_breeze' if state == 'focused' else 'theme_fg_color_breeze'
            return '#%02x%02x%02x' % _role(palette, role)
    elif family in ('mubar', 'mbi', 'tbar-handle', 'tbar-separator'):
        role, anchor = 'theme_header_background_breeze', '#c1c1c1'
    elif family in ('menit', 'menii'):
        role, anchor = selection, '#e0e0e0' if family == 'menit' else '#999999'
    elif family == 'dbar':
        role, anchor = 'theme_header_background_breeze', '#a59f80'
    elif family == 'pbc':
        role, anchor = selection, '#808080' if disabled else '#699997'
    elif family == 'header-separator':
        role, anchor = button, '#999999'
    elif family in ('gbox', 'tbb', 'mbord', 'tbf', 'tab', 'tab-separator',
                    'floating-tab', 'floating-tab-separator', 'splitter-grip'):
        role, anchor = window, '#c1c1c1'
    else:
        raise ValueError('Missing Irixium semantic plan: ' + family)
    return _tone(palette, role, source, anchor)


def _xml_records(text, root):
    """Associate XML nodes with exact source spans without serializing them."""
    nodes, records, stack, index = list(root.iter()), {}, [], 0
    for token in _TOKENS.finditer(text):
        raw = token.group()
        if raw.startswith(('<?', '<!')):
            continue
        if raw.startswith('</'):
            if not stack:
                raise ValueError('Malformed SVG closing tag')
            node = stack.pop()
            records[node]['end'] = token.end()
            records[node]['close_start'] = token.start()
        else:
            if index >= len(nodes):
                raise ValueError('Unsupported SVG XML structure')
            node = nodes[index]; index += 1
            records[node] = {'start': token.start(), 'open_end': token.end(), 'raw': raw}
            if raw.rstrip().endswith('/>'):
                records[node]['end'] = token.end()
            else:
                stack.append(node)
    if stack or index != len(nodes):
        raise ValueError('SVG XML token/node mismatch')
    return records


def _replace_tag(raw, element, family, state, palette, override, count):
    def replace_attribute(match):
        name, value = match['name'], match['value']
        if name == 'style':
            def paint(match):
                count[family] += 1
                return match['prefix'] + _paint(palette, family, state, match['color'].lower(), element, override)
            new = _PAINT.sub(paint, value)
        elif name in ('fill', 'stroke') and _HEX.fullmatch(value):
            count[family] += 1
            new = _paint(palette, family, state, value.lower(), element, override)
        else:
            return match.group()
        start, end = match.span('value')
        # These offsets are relative to raw, while this callback returns only
        # the matched attribute text.
        offset = match.start()
        return match.group()[:start-offset] + new + match.group()[end-offset:]
    return _ATTRIBUTE.sub(replace_attribute, raw)


def _geometry(element):
    """Comparable XML shape; paint-only changes are excluded, nothing else."""
    attrs = dict(element.attrib)
    attrs.pop('id', None)
    if '{'+_XLINK+'}href' in attrs:
        # Alias reference identity is checked separately against its ID map.
        attrs['{'+_XLINK+'}href'] = '<local-reference>'
    for name in ('fill', 'stroke'):
        if name in attrs and _HEX.fullmatch(attrs[name]):
            attrs[name] = '<paint>'
    if 'style' in attrs:
        attrs['style'] = _PAINT.sub(lambda m: m['prefix']+'<paint>', attrs['style'])
    return (element.tag, sorted(attrs.items()), element.text,
            tuple(_geometry(child) for child in element))


def render(svgbytes: bytes, kvconfigbytes: bytes, palette: dict[str, str], *, native_qt_palette: dict):
    """Return a complete in-memory Modern variant; no files or settings change."""
    from kvantum_palette_config import adapt_config
    if not isinstance(svgbytes, bytes) or not isinstance(kvconfigbytes, bytes):
        raise ValueError('Kvantum source inputs must be bytes')
    if _sha(svgbytes) != SOURCE_SVG_SHA256 or _sha(kvconfigbytes) != SOURCE_CONFIG_SHA256:
        raise ValueError('Unrecognized Irixium source revision; semantic audit required')
    for name in REQUIRED:
        _rgb(palette.get(name))
    for name in ('theme_header_background_breeze', 'theme_header_foreground_breeze'):
        _role(palette, name)
    text = svgbytes.decode('utf-8')
    if '<!DOCTYPE' in text or '<!ENTITY' in text:
        raise ValueError('SVG external declarations are unsupported')
    root = ET.fromstring(text)
    parents = {child: parent for parent in root.iter() for child in parent}
    ids = {node.get('id'): node for node in root.iter() if node.get('id')}
    if len(ids) != len([node for node in root.iter() if node.get('id')]):
        raise ValueError('Duplicate source SVG IDs')
    references = {node.get('{'+_XLINK+'}href', '').removeprefix('#')
                  for node in root.iter() if node.tag == '{'+_SVG+'}use'}
    if references & _ORPHANS:
        raise ValueError('Editor-only paths are now referenced; semantic audit required')
    if not references <= ids.keys():
        raise ValueError('Unresolved source SVG use reference')
    records, replacements, count, preserved = _xml_records(text, root), [], Counter(), []
    for node, record in records.items():
        raw = record['raw']
        if not _PAINT.search(node.get('style', '')) and not any(_HEX.fullmatch(node.get(n, '')) for n in ('fill', 'stroke')):
            continue
        family, state, context = _context(node, parents)
        if family == 'unreferenced-editor-path':
            preserved.append(context); continue
        updated = _replace_tag(raw, node, family, state, palette, None, count)
        replacements.append((record['start'], record['open_end'], updated))
    aliases, alias_reports = [], []
    for original, alias, role, section in (
        ('mbord', 'irix-kde-tooltip', 'tooltip_background_breeze', 'ToolTip'),
        ('tbb', 'irix-kde-header', 'theme_button_background_normal_breeze', 'HeaderSection')):
        originals = [node for node in ids.values()
                     if node.get('id', '').startswith(original+'-') and parents.get(node) is ids['layer1']]
        alias_ids = {node.get('id'): (node.get('id').replace(original+'-', alias+'-', 1)
                     if node.get('id').startswith(original+'-') else alias+'-copy-'+node.get('id'))
                     for group in originals for node in group.iter() if node.get('id')}
        for group in originals:
            record = records[group]
            raw = text[record['start']:record['end']]
            group_changes = []
            for node in group.iter():
                rec = records[node]
                tag = _replace_tag(rec['raw'], node, original, 'normal', palette, role, count)
                def identifiers(match):
                    value = match['value']
                    if match['name'] == 'id':
                        new = alias_ids[value]
                    elif match['name'] in ('xlink:href', 'href') and value.startswith('#'):
                        if value[1:] not in alias_ids:
                            raise ValueError('Alias uses art outside its audited context')
                        new = '#'+alias_ids[value[1:]]
                    else:
                        return match.group()
                    return match.group().replace(value, new, 1)
                tag = _ATTRIBUTE.sub(identifiers, tag)
                group_changes.append((rec['start']-record['start'], rec['open_end']-record['start'], tag))
            for start, end, tag in sorted(group_changes, reverse=True):
                raw = raw[:start]+tag+raw[end:]
            aliases.append(raw)
        alias_reports.append({'sourceFamily': original, 'family': alias, 'role': role,
            'configurationSection': section, 'groups': len(originals), 'ids': len(alias_ids)})
    insert = records[ids['layer1']]['close_start']
    replacements.append((insert, insert, '\n    <!-- Generated KDE role aliases; canonical geometry is unchanged. -->\n    '+'\n    '.join(aliases)+'\n  '))
    for start, end, raw in sorted(replacements, reverse=True):
        text = text[:start]+raw+text[end:]
    output_svg = text.encode('utf-8')
    outroot = ET.fromstring(output_svg)
    output_ids = {node.get('id'): node for node in outroot.iter() if node.get('id')}
    if not ids.keys() <= output_ids.keys():
        raise ValueError('Original SVG identity was lost')
    for name, node in ids.items():
        if _geometry(node) != _geometry(output_ids[name]) and name not in ('svg8', 'layer1'):
            raise ValueError('Original SVG geometry changed: '+name)
        old = node.get('{'+_XLINK+'}href')
        if old != output_ids[name].get('{'+_XLINK+'}href'):
            raise ValueError('Original SVG reference changed: '+name)
    for alias in alias_reports:
        for name, node in ids.items():
            if name.startswith(alias['sourceFamily']+'-') and parents.get(node) is ids['layer1']:
                target = name.replace(alias['sourceFamily']+'-', alias['family']+'-', 1)
                if _geometry(node) != _geometry(output_ids[target]):
                    raise ValueError('Alias SVG geometry changed: '+target)
    output_config, config_report = adapt_config(kvconfigbytes, native_qt_palette=native_qt_palette)
    config_text, section, result = output_config.decode('utf-8'), None, []
    aliases_by_section = {item['configurationSection']: item for item in alias_reports}
    context_changes = []
    for line in config_text.splitlines(keepends=True):
        if line.startswith('['):
            section = line.strip()[1:-1]
        match = re.fullmatch(r'(\s*(?:interior|frame)\.element\s*=\s*)(\w+)(\r?\n|)', line)
        if match and section in aliases_by_section:
            alias = aliases_by_section[section]
            if match[2] != alias['sourceFamily']:
                raise ValueError('Unexpected conflicting config context')
            line = match[1]+alias['family']+match[3]
            context_changes.append(section+'/'+match[1].strip().rstrip('=').strip())
        result.append(line)
    output_config = ''.join(result).encode('utf-8')
    report = {'recipe': RECIPE, 'sourceSvgSha256': _sha(svgbytes),
        'sourceConfigSha256': _sha(kvconfigbytes), 'outputSvgSha256': _sha(output_svg),
        'outputConfigSha256': _sha(output_config), 'originalIdsPreserved': len(ids),
        'originalReferencesPreserved': sum(node.tag == '{'+_SVG+'}use' for node in root.iter()),
        'originalReferenceTargetsPreserved': len(references), 'paintCount': sum(count.values()),
        'paintByFamily': dict(sorted(count.items())), 'aliases': alias_reports,
        'configContextChanges': context_changes, 'configColors': config_report,
        'preservedUnreferencedEditorPaths': sorted(preserved),
        'limitations': ['The canonical SVG has no explicit inactive state; native QPalette owns inactive/disabled text.',
            'Canonical SizeGrip references resize-grip, absent in the original SVG; this adapter adds no new artwork.']}
    return output_svg, output_config, report
