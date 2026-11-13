# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate a private Plasma desktop-theme snapshot from the scrollbar recipe."""
from __future__ import annotations

import configparser
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import backend
from scene_contract import scene


THEME_NAME = 'ThemeLabDomainOS'
SUPPORTED = {'scroll_h', 'scroll_v'}
ROLE_CLASSES = {
    'Colors:Window/BackgroundNormal': 'Background',
    'Colors:Window/ForegroundNormal': 'Text',
    'Colors:Button/BackgroundNormal': 'ButtonBackground',
    'Colors:Button/ForegroundNormal': 'ButtonText',
    'Colors:View/BackgroundNormal': 'ViewBackground',
    'Colors:View/ForegroundNormal': 'ViewText',
    'Colors:Selection/BackgroundNormal': 'Highlight',
    'Colors:Selection/ForegroundNormal': 'HighlightedText',
}
VERTICAL_CROSS_HINTS = {
    'slider-hint-left-inset', 'slider-hint-right-inset',
    'mouseover-slider-hint-left-inset', 'mouseover-slider-hint-right-inset',
    'background-vertical-hint-left-inset', 'background-vertical-hint-right-inset',
}
HORIZONTAL_CROSS_HINTS = {
    'slider-hint-top-inset', 'slider-hint-bottom-inset',
    'mouseover-slider-hint-top-inset', 'mouseover-slider-hint-bottom-inset',
    'background-horizontal-hint-top-inset', 'background-horizontal-hint-bottom-inset',
}


def component_source():
    candidates = [Path('/usr/lib/qt6/qml/org/kde/plasma/components/ScrollBar.qml')]
    candidates.extend(sorted(Path('/usr/lib').glob('*/qt6/qml/org/kde/plasma/components/ScrollBar.qml')))
    candidates.extend(sorted(Path('/usr/local/lib').glob('*/qt6/qml/org/kde/plasma/components/ScrollBar.qml')))
    return next((path for path in candidates if path.is_file()), None)


def contract(root):
    path = root / 'tools/domainos_scrollbar_rules.json'
    payload = backend.read_file(path)
    data = json.loads(payload)
    geometry = data.get('geometry', {})
    if (data.get('schema_version') != 1 or geometry.get('unit') != 'native_pixel' or
            geometry.get('origin') != 'measurement_vm' or
            geometry.get('bar_px') != geometry.get('arrow_px') + 2 * geometry.get('shadow_px') or
            geometry.get('thumb_cross_px') != geometry.get('arrow_px')):
        raise ValueError('Plasma requires the measured Domain/OS SR10.4 scrollbar contract')
    return data, backend.sha(payload)


def _geometry(recipe, rules):
    values = dict(rules['geometry'])
    values.update(recipe.get('geometry', {}))
    bar = values.get('bar_px')
    thumb = values.get('thumb_cross_px')
    shadow = values.get('shadow_px')
    if any(type(value) is not int or value < 1 or value > 128
           for value in (bar, thumb, shadow)):
        raise ValueError('Plasma scrollbar geometry requires positive integer pixels')
    if thumb > bar or (bar - thumb) % 2:
        raise ValueError('Plasma requires a centered thumb with equal integer insets')
    if shadow * 2 > bar:
        raise ValueError('Plasma relief must fit inside the scrollbar thickness')
    return {'bar_px': bar, 'thumb_cross_px': thumb,
            'cross_inset_px': (bar - thumb) // 2, 'shadow_px': shadow,
            'arrow_px': values['arrow_px'],
            'arrow_thumb_gap_px': values['arrow_thumb_gap_px'],
            'view_bar_gap_px': values['view_bar_gap_px'],
            'view_inset_px': values['view_inset_px']}


def _role_class(value):
    try:
        return ROLE_CLASSES[value]
    except KeyError as error:
        raise backend.Unavailable('Plasma não traduz este papel KDE para KSvg: ' + str(value)) from error


def _configure_svg(payload, geometry, palette):
    root = ET.fromstring(payload)
    relief_context = []
    def visit(element, ancestors):
        identifier = element.get('id', '')
        context = ancestors + [identifier]
        if identifier == 'hint-scrollbar-size':
            element.set('width', str(geometry['thumb_cross_px']))
            element.set('height', str(geometry['thumb_cross_px']))
        if identifier in VERTICAL_CROSS_HINTS:
            element.set('width', str(geometry['cross_inset_px']))
        if identifier in HORIZONTAL_CROSS_HINTS:
            element.set('height', str(geometry['cross_inset_px']))

        classes = element.get('class', '').split()
        mapped = []
        for name in classes:
            if name == 'ColorScheme-ButtonBackground':
                name = 'ColorScheme-' + _role_class(palette['face_role'])
            elif name == 'ColorScheme-ButtonText':
                name = 'ColorScheme-' + _role_class(palette['text_role'])
            mapped.append(name)
        if classes:
            element.set('class', ' '.join(mapped))

        shade = element.get('data-scheme-shade')
        if shade in ('lighten', 'darken'):
            is_background = any(name.startswith('background-') for name in context)
            if shade == 'lighten':
                factor = float(palette['light']) / backend.FACTORS['light']
            else:
                factor = float(palette['trough'] if is_background else palette['shade']) / (
                    backend.FACTORS['trough'] if is_background else backend.FACTORS['shade'])
            original = float(element.get('opacity', '1'))
            element.set('opacity', format(min(1.0, max(0.0, original * factor)), '.8g'))
        for child in list(element):
            visit(child, context)
    visit(root, [])
    ET.indent(root, space='  ')
    # KSvg's SVG loader expects the default SVG namespace. ElementTree otherwise
    # serializes the document as ns0:svg/ns0:rect, which parses as valid XML but
    # leaves KSvg's current-color-scheme styling unresolved in the live preview.
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n' +
            ET.tostring(root, encoding='unicode') + '\n').encode('utf-8')


def _write_ini(parser, path):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        parser.write(stream, space_around_delimiters=False)
    path.chmod(0o600)


def _private_theme(root, folder, geometry, recipe, selected):
    theme_source = root / 'plasma/IrixClassicDomainOS'
    preview_data = backend.private_output(folder / 'plasma-preview-data', root)
    theme_dir = backend.private_output(
        preview_data / 'plasma/desktoptheme' / THEME_NAME, root)
    shutil.copytree(theme_source, theme_dir, dirs_exist_ok=True)
    svg_path = theme_dir / 'widgets/scrollbar.svg'
    source_svg = backend.read_file(theme_source / 'widgets/scrollbar.svg')
    rendered_svg = _configure_svg(source_svg, geometry, recipe['palette'])
    svg_path.write_bytes(rendered_svg)
    svg_path.chmod(0o600)

    metadata_path = theme_dir / 'metadata.json'
    metadata = json.loads(backend.read_file(metadata_path))
    metadata.setdefault('KPlugin', {})['Id'] = THEME_NAME
    metadata['KPlugin']['Name'] = 'Theme Lab DomainOS (private preview)'
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    metadata_path.chmod(0o600)

    preview_config = backend.private_output(folder / 'plasma-preview-config', root)
    kdeglobals = preview_config / 'kdeglobals'
    if selected.get('scheme_id'):
        if not re.fullmatch(r'[A-Za-z0-9 _.-]{1,127}', selected['scheme_id']):
            raise ValueError('KDE color scheme ID is not portable')
        if not selected['path'].endswith('.colors'):
            raise backend.Unavailable('Plasma preview needs a concrete .colors file for the selected scheme.')
        palette_dir = preview_data / 'color-schemes'
        palette_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        palette_path = palette_dir / (selected['scheme_id'] + '.colors')
        palette_path.write_bytes(backend.read_file(Path(selected['path'])))
        palette_path.chmod(0o600)
    kde = configparser.ConfigParser(interpolation=None, strict=False)
    kde.optionxform = str
    kde.read_string(backend.read_file(selected['path']).decode('utf-8'))
    if not kde.has_section('General'):
        kde.add_section('General')
    if selected.get('scheme_id'):
        kde.set('General', 'ColorScheme', selected['scheme_id'])
    if not kde.has_section('KDE'):
        kde.add_section('KDE')
    _write_ini(kde, kdeglobals)
    plasma = configparser.ConfigParser(interpolation=None, strict=False)
    plasma.optionxform = str
    plasma['Theme'] = {'name': THEME_NAME}
    _write_ini(plasma, preview_config / 'plasmarc')
    return preview_data, preview_config, theme_dir, svg_path, kdeglobals


def generate(root, folder, model, project_hash, kdeglobals):
    recipe = model['recipes']['plasma']
    custom_parts = {key: value for key, value in recipe.get('scrollbar_parts', {}).items() if value}
    if custom_parts:
        raise backend.Unavailable('Plasma scrollbar recipe currently maps shared geometry and palette roles only; piece overrides remain saved but untranslated.')
    records = scene(model, 'plasma')
    requested = {record['id'] for record in records}
    ids = requested & SUPPORTED
    if not ids:
        raise backend.Unavailable('Plasma Style requer scroll_h ou scroll_v visível; os demais controles permanecem salvos, mas ainda não são traduzidos.')
    skipped = sorted(requested - SUPPORTED)
    rules, contract_hash = contract(root)
    geometry = _geometry(recipe, rules)
    _selected_config, selected = backend.selected_palette(model, kdeglobals, root)
    folder = backend.private_output(Path(folder), root)
    preview_data, preview_config, theme_dir, svg_path, native_config = _private_theme(
        root, folder, geometry, recipe, selected)
    recipe_hash = backend.sha(json.dumps(recipe, sort_keys=True).encode())
    theme_source = root / 'plasma/IrixClassicDomainOS'
    component = component_source()
    source_paths = {
        'theme_source_metadata': theme_source / 'metadata.json',
        'theme_source_scrollbar': theme_source / 'widgets/scrollbar.svg',
        'plasma_scrollbar_component': component,
    }
    inputs = [{'path': str(selected['path']), 'sha256': selected['sha256']}]
    artifacts = {}
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'PLASMA-RECIPE.json':
            artifacts[str(path.relative_to(folder))] = backend.sha(backend.read_file(path))
    if any(path is None or not path.is_file() for path in source_paths.values()):
        raise backend.Unavailable('A fonte nativa do Plasma/KSvg necessária à prévia não está instalada.')
    sources = {key: {'path': str(path), 'sha256': backend.sha(backend.read_file(path))}
               for key, path in source_paths.items()}
    receipt = {
        'schema_version': 1, 'family': 'plasma', 'status': 'partially_generated',
        'reason': 'Tema Plasma privado gerado para scrollbar real do Plasma Components/KSvg.',
        'recipe_applied': True, 'translated_controls': sorted(ids),
        'untranslated_visible_controls': skipped,
        'scope': 'Private Plasma desktop-theme SVG snapshot; native Plasma Components.ScrollBar and KSvg 1:1 control gallery',
        'source_project_sha256': project_hash,
        'preview_project_sha256': backend.sha(backend.read_file(folder / 'PROJECT.json')),
        'recipe_sha256': recipe_hash,
        'contract': {'path': 'tools/domainos_scrollbar_rules.json', 'sha256': contract_hash,
                     'reference': 'Domain/OS SR10.4 with HP VUE 2.01'},
        'theme_name': THEME_NAME, 'theme_dir': str(theme_dir), 'svg': str(svg_path),
        'preview_data': str(preview_data), 'preview_config': str(preview_config),
        'kdeglobals': str(native_config),
        'geometry': geometry,
        'effective_geometry': {'vertical_bar_px': geometry['thumb_cross_px'] + 2 * geometry['cross_inset_px'],
                               'horizontal_bar_px': geometry['thumb_cross_px'] + 2 * geometry['cross_inset_px'],
                               'thumb_cross_px': geometry['thumb_cross_px'],
                               'cross_inset_px': geometry['cross_inset_px']},
        'palette_roles': {'face': recipe['palette']['face_role'], 'text': recipe['palette']['text_role'],
                          'shade_factors': {key: recipe['palette'][key] for key in ('light', 'shade', 'trough')}},
        'selected_scheme': selected, 'palette_inputs': inputs,
        'sources': sources, 'artifacts': artifacts,
        'host_changed': False, 'repository_changed': False, 'picked_used': False,
        'limitations': [
            ('Visible controls not yet translated and omitted from this preview: ' + ', '.join(skipped) + '.'
             if skipped else 'All visible controls in this scene belong to the translated Plasma scrollbar scope.'),
            'Plasma Components.ScrollBar is rendered directly by Plasma QML and KSvg at 1:1; the gallery does not claim ScrollView integration or the separate System Settings/QtQuick Controls scrollbar.',
            'The real Plasma component has no Motif stepper arrows; arrow_px and arrow_thumb_gap_px are not rendered.',
            'The component does not expose a theme metric for the 4px viewport/bar gap; gallery positioning only keeps the controls adjacent and does not render that gap as a recipe part.',
            'Only base scrollbar geometry and face/text KDE roles plus shade factors are mapped. Custom per-piece overrides are rejected rather than silently ignored.',
            'The theme and color scheme are private preview snapshots; regenerating the recipe is required after a KDE scheme change.',
            'Historical disabled/hover interaction remains a separate evidence question; rendering the active theme does not prove human approval.'
        ]
    }
    if not backend.palette_inputs_current(receipt):
        raise backend.Unavailable('A paleta KDE mudou durante a geração Plasma; gere novamente.')
    backend.write_json(folder / 'PLASMA-RECIPE.json', receipt)
    return receipt


def verify(root, receipt, model):
    snapshot = backend.private_output(Path(receipt['theme_dir']).parents[3], root)
    saved, digest = backend.project(snapshot / 'PROJECT.json')
    saved_receipt = json.loads(backend.read_file(snapshot / 'PLASMA-RECIPE.json'))
    recipe = model['recipes']['plasma']
    if (saved != model or digest != receipt.get('preview_project_sha256') or
            backend.sha(json.dumps(recipe, sort_keys=True).encode()) != receipt.get('recipe_sha256') or
            saved_receipt.get('theme_name') != receipt.get('theme_name') or
            saved_receipt.get('preview_project_sha256') != digest):
        raise ValueError('Plasma preview theme/recipe identity mismatch')
    for relative, expected in saved_receipt.get('artifacts', {}).items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Plasma artifact outside private snapshot')
        target = snapshot / path
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError('Plasma artifact traverses a link')
        if backend.sha(backend.read_file(target)) != expected:
            raise ValueError('Plasma artifact hash mismatch: ' + relative)
    if not backend.palette_inputs_current(saved_receipt):
        raise ValueError('Plasma palette input is stale')
    return saved_receipt


