# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate an isolated real-Kvantum theme from the Theme Lab recipe."""
from __future__ import annotations

import configparser
import hashlib
import json
from pathlib import Path

import backend
from scene_contract import scene


STATES = ('normal', 'pressed', 'backdrop', 'disabled')
SUPPORTED = {'scroll_h', 'scroll_v'}


def contract(root):
    path = root / 'tools/domainos_scrollbar_rules.json'
    data = json.loads(backend.read_file(path))
    geometry = data.get('geometry', {})
    required = ('bar_px', 'shadow_px', 'arrow_px', 'thumb_cross_px')
    if (data.get('schema_version') != 1 or geometry.get('unit') != 'native_pixel' or
            geometry.get('origin') != 'measurement_vm' or
            any(type(geometry.get(key)) is not int for key in required) or
            geometry['bar_px'] != geometry['arrow_px'] + 2 * geometry['shadow_px'] or
            geometry['thumb_cross_px'] != geometry['arrow_px']):
        raise ValueError('Kvantum requires the validated SR10.4 scrollbar contract')
    return data, backend.sha(backend.read_file(path))


def _geometry(recipe, rules):
    result = dict(rules['geometry'])
    result.update(recipe['geometry'])
    for key in ('bar_px', 'shadow_px', 'arrow_px', 'thumb_cross_px',
                'arrow_thumb_gap_px', 'view_bar_gap_px', 'view_inset_px'):
        if type(result.get(key)) is not int or not 0 <= result[key] <= 128:
            raise ValueError('Kvantum metric must be an integer pixel value: ' + key)
    if (result['bar_px'] != result['arrow_px'] + 2 * result['shadow_px'] or
            result['arrow_px'] < 3 or result['arrow_px'] % 2 == 0 or
            result['thumb_cross_px'] != result['arrow_px']):
        raise ValueError('Kvantum needs an odd arrow and bar = arrow + 2 × relief')
    return result


def _write_ini(parser, target):
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8', newline='\n') as stream:
        parser.write(stream, space_around_delimiters=False)
    target.chmod(0o600)


def generate(root, folder, model, project_hash, kdeglobals):
    recipe = model['recipes']['kvantum']
    parts = {key: value for key, value in recipe.get('scrollbar_parts', {}).items() if value}
    if parts:
        raise backend.Unavailable('Kvantum traduz a receita geométrica comum; sobrescritas por peça ainda não estão integradas.')
    records = scene(model, 'kvantum')
    requested = {row['id'] for row in records}
    ids = requested & SUPPORTED
    if not ids:
        raise backend.Unavailable('Kvantum requer scroll_h ou scroll_v visível; os demais controles permanecem salvos, mas ainda não são traduzidos.')
    skipped = sorted(requested - SUPPORTED)

    rules, contract_hash = contract(root)
    geometry = _geometry(recipe, rules)
    builder = backend.load_builder(root)
    selected_config, selected = backend.selected_palette(model, kdeglobals, root)
    colors, color_origin = backend.native_roles(root, Path(selected['path']),
                                                builder.art, selected['sha256'])
    folder = backend.private_output(Path(folder), root)

    palette_input = folder / 'kvantum-palette-input'
    _write_ini(selected_config, palette_input / 'kdeglobals')
    from kvantum_native_palette import read as read_qt_palette
    qt_native = read_qt_palette(palette_input)

    metrics = {key: geometry[key] for key in ('bar_px', 'shadow_px', 'arrow_px')}
    with backend.recipe_rules(builder, recipe['palette']):
        svg = builder.art.svg(colors, scrollbar_geometry=metrics)
    config_source = builder.art.kvconfig(geometry['bar_px'], geometry['shadow_px'])
    from kvantum_palette_config import adapt_config
    kvconfig, config_report = adapt_config(config_source, native_qt_palette=qt_native['palette'])

    name = 'ThemeLab-DomainOS'
    preview_data = folder / 'kvantum-preview-data'
    preview_config = folder / 'kvantum-preview-config'
    # Kvantum resolves named themes from XDG_CONFIG_HOME/Kvantum/<theme>
    # (or the documented ~/.themes and XDG_DATA_HOME/themes layouts); placing
    # this under XDG_DATA_HOME/Kvantum silently falls back to another theme.
    theme_dir = backend.private_output(preview_config / 'Kvantum' / name, root)
    svg_path = theme_dir / (name + '.svg')
    config_path = theme_dir / (name + '.kvconfig')
    svg_path.write_bytes(svg)
    config_path.write_bytes(kvconfig)
    selector = preview_config / 'Kvantum' / 'kvantum.kvconfig'
    selector.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    selector.write_text('[General]\ntheme=' + name + '\n', encoding='utf-8')
    selector.chmod(0o600)

    native_config_path = preview_config / 'kdeglobals'
    kde = configparser.ConfigParser(interpolation=None, strict=False)
    kde.optionxform = str
    kde.read(palette_input / 'kdeglobals', encoding='utf-8')
    if not kde.has_section('KDE'):
        kde.add_section('KDE')
    kde.set('KDE', 'widgetStyle', 'kvantum')
    if selected.get('scheme_id'):
        if not kde.has_section('General'):
            kde.add_section('General')
        kde.set('General', 'ColorScheme', selected['scheme_id'])
    _write_ini(kde, native_config_path)

    recipe_hash = backend.sha(json.dumps(recipe, sort_keys=True).encode())
    with backend.recipe_rules(builder, recipe['palette']):
        role_values = {}
        for family, tokens in (('face', ('face',)), ('relief', ('light', 'dark', 'trough'))):
            for token in tokens:
                role_values[family + '.' + token] = builder.art.evaluate(
                    builder.art.pixel_plan('button', token), colors)
    artifacts = {}
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'KVANTUM-RECIPE.json':
            artifacts[str(path.relative_to(folder))] = backend.sha(backend.read_file(path))
    palette_inputs = [selected, color_origin['helper'], color_origin['helper_source']]
    receipt = {
        'schema_version': 1, 'family': 'kvantum', 'status': 'partially_generated',
        'reason': 'Tema Kvantum real gerado para barras de rolagem; demais controles não são traduzidos nesta etapa.',
        'recipe_applied': True, 'translated_controls': sorted(ids),
        'untranslated_visible_controls': skipped,
        'scope': 'Real Kvantum QStyle; isolated SVG/config generated from Theme Lab recipe and KDE roles',
        'project_sha256': project_hash, 'recipe_sha256': recipe_hash,
        'project_path': str(folder / 'PROJECT.json'),
        'contract': {'path': 'tools/domainos_scrollbar_rules.json', 'sha256': contract_hash,
                     'reference': 'Domain/OS SR10.4 with HP VUE 2.01'},
        'theme_name': name, 'theme_dir': str(theme_dir), 'svg': str(svg_path),
        'kvconfig': str(config_path), 'selector': str(selector),
        'preview_config': str(preview_config), 'preview_data': str(preview_data),
        'geometry': {key: geometry[key] for key in ('bar_px', 'shadow_px', 'arrow_px',
            'thumb_cross_px', 'arrow_thumb_gap_px', 'view_bar_gap_px', 'view_inset_px')},
        'config_geometry': {'scroll_width': geometry['bar_px'],
                            'indicator_size': geometry['bar_px']},
        'palette_roles_applied': True, 'palette_role_values': role_values,
        'selected_scheme': selected, 'palette': color_origin,
        'qt_palette': {'qt_version': qt_native.get('qt_version'),
                       'source_signature': qt_native.get('source_signature'),
                       'checks': qt_native.get('checks'), 'adaptation': config_report},
        'palette_inputs': palette_inputs, 'artifacts': artifacts,
        'host_changed': False, 'repository_changed': False, 'picked_used': False,
        'limitations': [
            ('Controles visíveis ainda não traduzidos e omitidos desta prévia: ' + ', '.join(skipped) + '.'
             if skipped else 'Todos os controles visíveis desta cena pertencem ao escopo Kvantum traduzido.'),
            'Kvantum owns native scrollbar range, page size, wheel and drag behavior.',
            'The shared contract supplies 15/2/11 and the recipe controls geometry; Kvantum settings expose scroll_width and indicator size but not the 4px viewport/bar gap or arrow/thumb gap as independent metrics.',
            'The generated SVG contains KDE-role-derived colors for this private preview; it is a snapshot and must be regenerated when the selected scheme changes.',
            'The product theme companion separately regenerates local color variants on KDE scheme changes; this preview does not write the user profile.',
            'Disabled and hover historical Motif states remain unverified; a successful render is not user approval.'
        ]}
    if not backend.palette_inputs_current(receipt):
        raise backend.Unavailable('A paleta KDE mudou durante a geração Kvantum; gere novamente.')
    backend.write_json(folder / 'KVANTUM-RECIPE.json', receipt)
    return receipt


def verify(root, receipt, model):
    folder = Path(receipt['kvconfig']).parents[3]
    folder = backend.private_output(folder.absolute(), root)
    saved = json.loads(backend.read_file(folder / 'KVANTUM-RECIPE.json'))
    recipe_hash = backend.sha(json.dumps(model['recipes']['kvantum'], sort_keys=True).encode())
    if (saved.get('family') != 'kvantum' or saved.get('project_sha256') != receipt.get('project_sha256') or
            saved.get('recipe_sha256') != recipe_hash or
            saved.get('translated_controls') != receipt.get('translated_controls')):
        raise ValueError('Kvantum snapshot/recipe identity mismatch')
    for relative, digest in saved.get('artifacts', {}).items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Kvantum artifact outside private snapshot')
        target = folder / path
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError('Kvantum artifact traverses a link')
        if backend.sha(backend.read_file(target)) != digest:
            raise ValueError('Kvantum artifact hash mismatch: ' + relative)
    if not backend.palette_inputs_current(saved):
        raise ValueError('Kvantum palette inputs are stale')
    return saved


def environment(root, receipt, model):
    verify(root, receipt, model)
    config = Path(receipt['preview_config'])
    data = Path(receipt['preview_data'])
    return {
        'XDG_CONFIG_HOME': str(config), 'XDG_DATA_HOME': str(data),
        'XDG_CONFIG_DIRS': '/etc/xdg', 'XDG_DATA_DIRS': '/usr/local/share:/usr/share',
        'QT_STYLE_OVERRIDE': 'kvantum', 'QT_QPA_PLATFORMTHEME': 'kde',
        'XDG_CURRENT_DESKTOP': 'KDE', 'KDE_SESSION_VERSION': '6'
    }


def command(root, receipt, model, project_file):
    verify(root, receipt, model)
    return ['/usr/bin/python3', '-B', str(root / 'plasma/tests/galerias-nativas/qt6_demo.py'),
            '--qt-major', '6', '--theme-lab-kvantum-snapshot', str(Path(receipt['kvconfig']).parents[3] / 'KVANTUM-RECIPE.json'),
            '--theme-lab-project', str(project_file)]
