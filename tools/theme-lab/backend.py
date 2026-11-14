#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private recipe generation and native-gallery controller for Theme Lab.

No theme is installed, no personal profile is written, and sampled RGB is never
used as a final control colour. GTK3 translates proposed recipes; GTK2 provides
partial native scrollbar scenes with a verified palette/RC snapshot. Qt5 and
Qt6 translate the 16 control families declared by their partial Widgets
recipes. GTK4 translates its explicit five-control subset; Kvantum and Plasma
translate horizontal and vertical scrollbars. Other families keep an honest
capability/recipe record. Missing GTK1/GTK5 runtimes are never simulated.
Native previews use a coordinated private namespace or the direct user-session
route with a private profile and preserve the gallery guards.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import configparser
import copy
import ctypes.util
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import uuid

sys.dont_write_bytecode = True
LOCAL = Path(__file__).resolve().parent
if str(LOCAL) not in sys.path:
    sys.path.insert(0, str(LOCAL))  # Also support explicit spec-based module loading.
from x11_session import verify_local_x11
ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ('motif', 'gtk1', 'gtk2', 'gtk3', 'gtk4', 'gtk5', 'qt5', 'qt6', 'kvantum', 'plasma')
CONTROLS = ('push', 'toggle', 'check', 'radio', 'entry', 'combo', 'spin', 'text',
            'scale_h', 'scale_v', 'scroll_h', 'scroll_v', 'arrow', 'progress', 'list', 'frame')
EDIT_STATES = ('normal', 'pressed', 'disabled', 'backdrop')
GEOMETRY = ('bar_px', 'shadow_px', 'arrow_px', 'thumb_cross_px', 'arrow_thumb_gap_px',
            'view_bar_gap_px', 'view_inset_px', 'control_padding_px', 'font_px')
DEFAULT_ROLES = {'face_role': 'Colors:Button/BackgroundNormal',
                 'text_role': 'Colors:Button/ForegroundNormal',
                 'view_role': 'Colors:View/BackgroundNormal',
                 'selection_role': 'Colors:Selection/BackgroundNormal'}
FACTORS = {'light': .56, 'shade': .482, 'trough': .15}
HEADER_ROLES = {'face': 'Colors:Header/BackgroundNormal',
                'text': 'Colors:Header/ForegroundNormal'}
HEADER_FALLBACK_ROLES = {'face': 'Colors:Window/BackgroundNormal',
                         'text': 'Colors:Window/ForegroundNormal'}
ROLE_FAMILIES = {'Colors:Window/BackgroundNormal': 'window', 'Colors:Window/ForegroundNormal': 'window-fg',
                 'Colors:Button/BackgroundNormal': 'button', 'Colors:Button/ForegroundNormal': 'button-fg',
                 'Colors:View/BackgroundNormal': 'view', 'Colors:View/ForegroundNormal': 'view-fg',
                 'Colors:Selection/BackgroundNormal': 'selection', 'Colors:Selection/ForegroundNormal': 'selection-fg',
                 'Colors:Tooltip/BackgroundNormal': 'tooltip', 'Colors:Tooltip/ForegroundNormal': 'tooltip-fg',
                 'Colors:Header/BackgroundNormal': 'header', 'Colors:Header/ForegroundNormal': 'header-fg'}
LIMIT = 2 * 1024 * 1024


class Unavailable(ValueError):
    pass


def read_file(path, limit=LIMIT):
    """Bounded regular-file reads; proposals and receipts cannot be links."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError('Entrada não regular ou maior que o limite: ' + str(path))
        result = stream.read(limit + 1)
        if len(result) > limit:
            raise ValueError('Entrada cresceu além do limite: ' + str(path))
        return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


SCROLL_PART_FIELDS = {
    'arrow': ('glyph_px', 'shadow_px'),
    'arrow_button': ('padding_px', 'shadow_px'),
    'trough': ('thickness_px', 'shadow_px'),
    'thumb': ('cross_px', 'shadow_px', 'gap_px'),
    'fitting': ('gap_px', 'inset_px'),
}


PART_STATE_IDS = ('normal', 'pressed', 'disabled', 'backdrop', 'hover', 'focus')
RELIEF_IDS = ('flat', 'raised', 'sunken')

def validate_scroll_parts(recipe, version):
    parts = recipe.get('scrollbar_parts', {})
    if 'scrollbar_parts' in recipe and version < 2:
        raise ValueError('Receitas por peça exigem schema_version=2.')
    if not isinstance(parts, dict) or set(parts) - set(SCROLL_PART_FIELDS):
        raise ValueError('Peça de barra desconhecida ou inválida.')
    for piece, parameters in parts.items():
        if not isinstance(parameters, dict) or set(parameters) - (set(SCROLL_PART_FIELDS[piece]) | {'state_relief'}):
            raise ValueError('Parâmetro de peça desconhecido: ' + piece)
        relief = parameters.get('state_relief', {})
        if (type(relief) is not dict or set(relief) - set(PART_STATE_IDS)
                or any(type(value) is not str or value not in RELIEF_IDS for value in relief.values())):
            raise ValueError('Estado/relevo de peça desconhecido ou inválido: ' + piece)
        if any(type(value) is not int or not 0 <= value <= 128
               for key, value in parameters.items() if key != 'state_relief'):
            raise ValueError('Medida de peça inteira entre 0 e 128 esperada: ' + piece)
    return parts


def require_scroll_parts_adapter(recipe, family='gtk3'):
    if family not in ('gtk3','gtk2','motif') and any(recipe.get('length_anchor', [])):
        raise Unavailable('Âncora preservada; posicionamento nativo ainda pendente.')
    if family == 'gtk2':
        from gtk2_recipe import paint_contract
        try:
            paint_contract(recipe)
        except ValueError as error:
            raise Unavailable('GTK2: tradução nativa indisponível: ' + str(error)) from error
        return
    parts = recipe.get('scrollbar_parts', {})
    active = {name: values for name, values in parts.items() if values}
    if not active:
        return
    if family != 'gtk3' or set(active) - {'arrow', 'arrow_button', 'trough', 'thumb', 'fitting'}:
        raise Unavailable('A receita por peça foi preservada; sua tradução nativa ainda não está implementada.')
    for piece, values in active.items():
        relief = values.get('state_relief', {})
        allowed = (set(PART_STATE_IDS) if piece == 'arrow_button' else
                   {'normal', 'pressed', 'disabled', 'backdrop', 'hover'} if piece in ('arrow','thumb') else
                   {'normal', 'disabled', 'backdrop'} if piece in ('trough','fitting') else set())
        if set(relief) - allowed:
            raise Unavailable('Receita de relevo por estado preservada; tradução pendente para esta peça/estado.')
    arrow = active.get('arrow', {})
    size = arrow.get('glyph_px', recipe['geometry']['arrow_px'])
    shadow = arrow.get('shadow_px', recipe['geometry']['shadow_px'])
    if size < 3 or not size % 2 or size > recipe['geometry']['arrow_px'] or shadow * 2 >= size:
        raise ValueError('Seta: tamanho ímpar de 3 até o espaço reservado; relevo menor que metade do tamanho.')
    if 'arrow_button' in active:
        button = active['arrow_button']
        padding = button.get('padding_px', 0)
        border = button.get('shadow_px', recipe['geometry']['shadow_px'])
        outer = recipe['geometry']['arrow_px'] + 2 * recipe['geometry']['shadow_px']
        if 2 * (padding + border) + size > outer:
            raise ValueError('Botão isolado: moldura e espaço interno devem caber sem cobrir a seta nem aumentar o botão.')
    if 'trough' in active:
        trough = active['trough']
        thickness = trough.get('thickness_px', recipe['geometry']['bar_px'])
        border = trough.get('shadow_px', recipe['geometry']['shadow_px'])
        reserved = max(recipe['geometry']['arrow_px'], recipe['geometry']['thumb_cross_px'])
        if thickness < reserved + 2 * border:
            raise ValueError('Trilho: espessura deve acomodar seta e cursor sem cortar suas alocações.')
    if 'thumb' in active:
        thumb, trough = active['thumb'], active.get('trough', {})
        cross = thumb.get('cross_px', recipe['geometry']['thumb_cross_px'])
        border = thumb.get('shadow_px', recipe['geometry']['shadow_px'])
        inner = trough.get('thickness_px', recipe['geometry']['bar_px']) - 2 * trough.get('shadow_px', recipe['geometry']['shadow_px'])
        if cross <= 2 * border or cross > inner or (inner - cross) % 2:
            raise ValueError('Cursor: largura deve caber no trilho com margens inteiras simétricas e relevo menor que metade.')


@contextmanager
def piece_assets(builder, recipe, geometry):
    """Independent arrow and trough masks; preserve the shared viewport mask."""
    require_scroll_parts_adapter(recipe)
    parts = recipe.get('scrollbar_parts', {}).get('arrow', {})
    trough = recipe.get('scrollbar_parts', {}).get('trough', {})
    thumb = recipe.get('scrollbar_parts', {}).get('thumb', {})
    fitting = recipe.get('scrollbar_parts', {}).get('fitting', {})
    if not parts and not trough and not thumb and not fitting:
        yield
        return
    original = builder.gtk3_assets
    proposed = dict(geometry, arrow_px=parts.get('glyph_px', geometry['arrow_px']),
                    shadow_px=parts.get('shadow_px', geometry['shadow_px']))
    def assets(*, geometry=None):
        result = original(geometry=geometry)
        if trough:
            pixels, family, _ = result['gtk3-trough-frame']
            border = trough.get('shadow_px', geometry['shadow_px'])
            # The original frame remains available to GtkViewport. A separate
            # sampling canvas accommodates large proposed borders without
            # pretending its extent is a native minimum scrollbar length.
            extent = max(len(pixels), 2 * border + 1)
            frame = builder.art.bevel(builder.art.blank(extent, extent, 'face'),
                                      thickness=border, down=True)
            result['gtk3-lab-trough-frame'] = frame, family, border
            # Enclosing contents node has no native hover/active state.
            # State masks change semantic border tokens only, never geometry.
            for edit_state, relief in trough.get('state_relief', {}).items():
                adjusted = builder.art.bevel(builder.art.blank(extent, extent, 'face'),
                                             thickness=border, down=relief=='sunken')
                if relief=='flat':
                    adjusted = [['face' for token in row] for row in adjusted]
                result['gtk3-lab-trough-'+edit_state] = adjusted, family, border
        if fitting:
            pixels, family, _ = result['gtk3-trough-frame']
            border = fitting.get('inset_px', geometry['view_inset_px'])
            extent = max(len(pixels), 2 * border + 1)
            frame = builder.art.bevel(builder.art.blank(extent, extent, 'face'),
                                      thickness=border, down=True)
            result['gtk3-lab-view-frame'] = frame, family, border
            source=Path(__file__).with_name('fitting_states.py')
            spec=importlib.util.spec_from_file_location('theme_lab_fitting_masks',source)
            states=importlib.util.module_from_spec(spec);spec.loader.exec_module(states)
            states.masks(builder,fitting,result,border)
        if thumb:
            pixels, family, _ = result['gtk3-thumb-frame']
            border = thumb.get('shadow_px', geometry['shadow_px'])
            extent = max(len(pixels), 2 * border + 1)
            frame = builder.art.bevel(builder.art.blank(extent, extent, 'face'),
                                      thickness=border, down=False)
            result['gtk3-thumb-frame'] = frame, family, border
            source=Path(__file__).with_name('thumb_states.py')
            spec=importlib.util.spec_from_file_location('theme_lab_thumb_masks',source)
            states=importlib.util.module_from_spec(spec);spec.loader.exec_module(states)
            states.masks(builder,thumb,result,border)
        for state in builder.art.STATES if parts else ():
            for direction in ('up', 'down', 'left', 'right'):
                key = 'gtk3-stepper-' + direction + '-' + state
                pixels, family, border = result[key]
                glyph = builder.gtk3_arrow(state, direction, geometry=proposed)
                canvas = builder.art.blank(len(pixels[0]), len(pixels))
                offset_x = (len(pixels[0]) - len(glyph[0])) // 2
                offset_y = (len(pixels) - len(glyph)) // 2
                for y, row in enumerate(glyph):
                    for x, token in enumerate(row):
                        canvas[y + offset_y][x + offset_x] = token
                result[key] = canvas, family, border
        # New sparse state masks preserve silhouette and reserved allocation.
        # Only semantic light/dark/face tokens change; palette remains dynamic.
        for edit_state, relief in parts.get('state_relief', {}).items():
            for direction in ('up', 'down', 'left', 'right'):
                base, family, border = result['gtk3-stepper-' + direction + '-normal']
                swaps = {'light':'dark', 'dark':'light'} if relief == 'sunken' else {}
                pixels = [[('face' if relief == 'flat' and token else swaps.get(token, token))
                           for token in row] for row in base]
                result['gtk3-lab-stepper-' + direction + '-' + edit_state] = pixels, family, border
        return result
    builder.gtk3_assets = assets
    try:
        yield
    finally:
        builder.gtk3_assets = original


def project(path):
    payload = read_file(path)
    result = json.loads(payload)
    if not isinstance(result, dict) or type(result.get('schema_version')) is not int or result.get('schema_version') not in (1, 2, 3) or result.get('kind') != 'theme_lab_project':
        raise ValueError('Projeto Theme Lab schema_version=1, 2 ou 3 esperado.')
    if result.get('selected_family') not in FAMILIES:
        raise ValueError('Família selecionada inválida.')
    result.setdefault('separate_preview', False)
    if type(result['separate_preview']) is not bool:
        raise ValueError('separate_preview deve ser booleano.')
    result.setdefault('color_scheme', '')
    if not portable_scheme(result['color_scheme']):
        raise ValueError('Use um ID portátil de esquema, sem caminhos.')
    recipes = result.get('recipes')
    if not isinstance(recipes, dict) or set(recipes) != set(FAMILIES):
        raise ValueError('As dez receitas precisam estar presentes no projeto.')
    for family, recipe in recipes.items():
        if not isinstance(recipe, dict):
            raise ValueError('Receita inválida: ' + family)
        validate_scroll_parts(recipe, result['schema_version'])
        if 'length_anchor' in recipe:
            anchors=recipe['length_anchor']
            if result['schema_version']<2:
                raise ValueError('Âncoras exigem schema_version=2.')
            if (not isinstance(anchors,list) or len(anchors)!=16 or
                    any(type(v) is not int or v not in (0,1) or (v and i not in (10,11)) for i,v in enumerate(anchors))):
                raise ValueError('length_anchor: 16 inteiros 0/1; extremidade somente nas barras.')
        geometry, palette = recipe.get('geometry'), recipe.get('palette')
        if not isinstance(geometry, dict) or any(type(geometry.get(key)) is not int or not 0 <= geometry[key] <= 128 for key in GEOMETRY[:-1]):
            raise ValueError('Geometria inteira entre 0 e 128 esperada: ' + family)
        if type(geometry.get('font_px')) is not int or not 6 <= geometry['font_px'] <= 48:
            raise ValueError('Fonte entre 6 e 48 pixels esperada: ' + family)
        if not isinstance(palette, dict):
            raise ValueError('Regras de paleta ausentes: ' + family)
        for key in DEFAULT_ROLES:
            if not isinstance(palette.get(key), str) or not re.fullmatch(r'Colors:[A-Za-z0-9_]+/[A-Za-z0-9_]+', palette[key]):
                raise ValueError('Nome de papel KDE inválido: ' + str(palette.get(key)))
        for key in FACTORS:
            value = palette.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Fator de iluminação entre 0 e 1 esperado: ' + key)
        control_palettes=recipe.get('control_palettes',{})
        if result['schema_version']<3 and control_palettes:
            raise ValueError('Papéis por controle exigem schema_version=3.')
        if not isinstance(control_palettes,dict) or not set(control_palettes).issubset(CONTROLS):
            raise ValueError('control_palettes aceita somente IDs do catálogo.')
        for control_id,override in control_palettes.items():
            if not isinstance(override,dict):
                raise ValueError('Sobrescrita de papel inválida: '+control_id)
            for key in DEFAULT_ROLES:
                if not isinstance(override.get(key),str) or not re.fullmatch(r'Colors:[A-Za-z0-9_]+/[A-Za-z0-9_]+',override[key]):
                    raise ValueError('Papel KDE inválido em '+control_id+': '+key)
            for key in FACTORS:
                value=override.get(key)
                if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:
                    raise ValueError('Fator KDE inválido em '+control_id+': '+key)
        if not isinstance(recipe.get('notes', ''), str):
            raise ValueError('Nota da receita precisa ser texto.')
        for key, default, upper in (('visible_categories', 31, 31), ('visible_controls', 65535, 65535),
                                    ('selected_control', 0, 15), ('edit_state', 0, 3), ('selected_scroll_part', 0, 4)):
            recipe.setdefault(key, default)
            if type(recipe[key]) is not int or not 0 <= recipe[key] <= upper:
                raise ValueError('Seleção ou estado inválido: ' + key)
        recipe.setdefault('positions', [[16 + (i % 4)*160, 16 + (i // 4)*80] for i in range(16)])
        positions = recipe['positions']
        if (not isinstance(positions, list) or len(positions) != 16 or
                any(not isinstance(pair, list) or len(pair) != 2 or
                    any(type(value) is not int or not 0 <= value <= 2048 for value in pair)
                    for pair in positions)):
            raise ValueError('positions deve conter os 16 pares entre 0 e 2048 pixels.')
        recipe.setdefault('sizes', [[0, 0] for _ in range(16)])
        if (not isinstance(recipe['sizes'], list) or len(recipe['sizes']) != 16 or
                any(not isinstance(pair, list) or len(pair) != 2 or
                    any(type(value) is not int or not 0 <= value <= 2048 for value in pair)
                    for pair in recipe['sizes'])):
            raise ValueError('sizes deve conter 16 pares de dimensões entre 0 e 2048 (0 = automático).')
    return result, sha(payload)


def portable_scheme(identifier):
    """Match the C model's portable ID, never accept a pathname as selection."""
    return (isinstance(identifier, str) and len(identifier) < 128 and
            (identifier == '' or (not identifier.startswith(('.', ' ')) and
             not identifier.endswith(' ') and '..' not in identifier and
             re.fullmatch(r'[A-Za-z0-9 _.\-]+', identifier) is not None)))


def kdeglobals_path(explicit=None):
    if explicit:
        return Path(explicit).absolute()
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    return config / 'kdeglobals'


def read_kde(path):
    try:
        payload = read_file(path)
    except OSError as error:
        raise Unavailable('Papéis KDE indisponíveis: ' + str(path)) from error
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read_string(payload.decode('utf-8'))
    return config, {'path': str(path), 'sha256': sha(payload), 'kind': 'current_kdeglobals_roles'}


def schemes(root=ROOT, kdeglobals=None):
    """Catalogue named scheme definitions in XDG order; no GUI or profile edit."""
    user = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    sources = [(user / 'color-schemes', 'xdg_user_color_scheme')]
    sources += [(Path(value) / 'color-schemes', 'xdg_system_color_scheme')
                for value in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if value]
    sources.append((Path(root) / 'colors', 'repository_color_scheme'))
    items = {'': {'id': '', 'name': 'Atual do KDE', 'path': str(kdeglobals_path(kdeglobals)),
                  'origin': 'current_kdeglobals_roles'}}
    skipped, visited = [], set()
    for directory, kind in sources:
        if not directory.is_absolute() or directory in visited:
            continue
        visited.add(directory)
        for path in sorted(directory.glob('*.colors'))[:4096]:
            identifier = path.stem
            if not portable_scheme(identifier) or not identifier or identifier in items:
                continue
            try:
                config, origin = read_kde(path)
                if not config.has_section('Colors:Button'):
                    raise Unavailable('Definição sem Colors:Button.')
                label = config.get('General', 'Name', fallback=identifier)
                if '\x00' in label:
                    raise ValueError('Nome do esquema contém NUL.')
                items[identifier] = {'id': identifier, 'name': label[:256], 'path': str(path),
                                     'origin': kind, 'sha256': origin['sha256']}
            except (OSError, ValueError, configparser.Error) as error:
                skipped.append({'path': str(path), 'reason': str(error)})
    return {'status': 'ok', 'schemes': [items['']] + sorted(
            (item for key, item in items.items() if key), key=lambda item: (item['name'].casefold(), item['id'])),
            'skipped': skipped, 'selection_scope': 'Lab controls and child preview only',
            'host_changed': False, 'private_kde_profile_changed': False}


def selected_palette(model, kdeglobals, root=ROOT):
    identifier = model.get('color_scheme', '') if model else ''
    if not portable_scheme(identifier):
        raise ValueError('Use um ID portátil de esquema, sem caminhos.')
    if not identifier:
        config, origin = read_kde(kdeglobals)
        origin['scheme_id'] = ''
        return config, origin
    item = next((item for item in schemes(root, kdeglobals)['schemes'] if item['id'] == identifier), None)
    if item is None:
        raise Unavailable('Esquema instalado não encontrado: ' + identifier)
    config, origin = read_kde(Path(item['path']))
    if origin['sha256'] != item['sha256']:
        raise Unavailable('O esquema mudou durante a leitura; execute novamente.')
    origin.update(kind=item['origin'], scheme_id=identifier, scheme_name=item['name'])
    return config, origin


def rgb_role(config, name):
    section, key = name.split('/', 1)
    value = config.get(section, key, fallback=None)
    if value is None:
        raise Unavailable('Papel KDE ausente: ' + name + '. O toolkit conserva sua paleta nativa.')
    fields = value.split(',')
    if len(fields) not in (3, 4) or not all(re.fullmatch(r'\d{1,3}', v.strip()) for v in fields):
        raise ValueError('RGB KDE inválido: ' + name)
    values = [int(v) for v in fields]
    if any(not 0 <= v <= 255 for v in values):
        raise ValueError('Canal KDE fora do intervalo: ' + name)
    return tuple(values[:3])


def header_role_pair(config):
    """Keep background/foreground from one semantic KDE role family."""
    header_available = all(
        config.get(*role.split('/', 1), fallback=None) is not None
        for role in HEADER_ROLES.values())
    roles = HEADER_ROLES if header_available else HEADER_FALLBACK_ROLES
    return (rgb_role(config, roles['face']), rgb_role(config, roles['text']),
            roles['face'], roles['text'])


def palette_values(model, kdeglobals, root=ROOT, family=None):
    if family is not None and family not in FAMILIES:
        raise ValueError('Família inválida para a paleta de referência.')
    selected = family or (model['selected_family'] if model else None)
    rules = model['recipes'][selected]['palette'] if model else dict(DEFAULT_ROLES, **FACTORS)
    config, origin = selected_palette(model, kdeglobals, root)
    base = [rgb_role(config, rules[key]) for key in DEFAULT_ROLES]
    face = base[0]
    light = tuple(round(value + (255 - value) * rules['light']) for value in face)
    shadow = tuple(round(value * (1 - rules['shade'])) for value in face)
    values = base + [light, shadow]
    header_face, header_text, header_face_role, header_text_role = \
        header_role_pair(config)
    header_selection = rgb_role(config, 'Colors:Selection/BackgroundNormal')
    header_light = tuple(round(value + (255 - value) * rules['light'])
                         for value in header_face)
    header_shadow = tuple(round(value * (1 - rules['shade']))
                          for value in header_face)
    header_values = [header_face, header_text, header_face, header_selection,
                     header_light, header_shadow]
    return {'status': 'ok', 'available': True, 'rgb16': [[channel * 257 for channel in color] for color in values],
            'rgb8': [list(color) for color in values], 'order': ['face', 'text', 'view', 'selection', 'light', 'shadow'],
            'header_rgb16': [[channel * 257 for channel in color]
                             for color in header_values],
            'header_rgb8': [list(color) for color in header_values],
            'header_order': ['face', 'text', 'view', 'selection', 'light', 'shadow'],
            'header_roles': {'face': header_face_role, 'text': header_text_role},
            'header_focus_role': 'Colors:Selection/BackgroundNormal',
            'origin': origin, 'roles': {key: rules[key] for key in DEFAULT_ROLES},
            'factors': {key: rules[key] for key in FACTORS}, 'picked_used': False,
            'selection_scope': 'Lab controls only; no global KDE scheme selected',
            'effective_gtk_states_exported': False, 'host_changed': False,
            'private_kde_profile_changed': False}


def python_probe(code):
    interpreter = '/usr/bin/python3' if Path('/usr/bin/python3').is_file() else sys.executable
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    try:
        result = subprocess.run([interpreter, '-B', '-c', code], capture_output=True, text=True, env=environment, timeout=10)
    except subprocess.TimeoutExpired:
        return {'available': False, 'probe_status': 'timeout',
                'reason': 'Consulta do runtime excedeu 10 s; disponibilidade não confirmada.'}
    except OSError as error:
        return {'available': False, 'probe_status': 'error', 'reason': str(error)}
    if result.returncode:
        return {'available': False, 'reason': result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'Importação indisponível.'}
    try:
        record = json.loads(result.stdout)
        if not isinstance(record, dict) or not isinstance(record.get('available'), bool):
            raise ValueError('Resposta sem disponibilidade booleana.')
        return record
    except (ValueError, TypeError) as error:
        return {'available': False, 'probe_status': 'invalid_response',
                'reason': 'Resposta inválida da consulta do runtime: ' + str(error)}


def package_version(name):
    if not shutil.which('dpkg-query'):
        return None
    try:
        result = subprocess.run(['dpkg-query', '-W', '-f=${Version}', name], capture_output=True, text=True, timeout=3)
    except (subprocess.TimeoutExpired, OSError):
        # Package metadata is optional; never invent a version or abort the
        # independent runtime checks when the package database is busy.
        return None
    return (result.stdout.strip() or None) if result.returncode == 0 else None


def probe(root):
    # Each child checks imports/libraries only, without initializing a GUI.
    # Bound concurrency and retain every result; never reuse stale availability.
    with ThreadPoolExecutor(max_workers=6) as executor:
        return _probe_inventory(root, executor)


def gtk4_probe(root):
    # The repository's GTK4 gallery uses the installed C ABI; absence of its
    # GIR package does not mean that the runtime or native gallery is absent.
    gtk4_gallery = root / 'plasma/tests/galerias-nativas/gtk4_demo.py'
    if gtk4_gallery.is_file():
        try:
            check = subprocess.run(['/usr/bin/python3', '-B', str(gtk4_gallery), '--verificar'],
                                   capture_output=True, text=True, timeout=10)
            if check.returncode == 0:
                result = dict(json.loads(check.stdout), available=True, binding='C_ABI')
            else:
                result = {'available': False, 'reason': check.stderr.strip().splitlines()[-1] if check.stderr.strip() else 'Galeria C ABI indisponível.'}
        except subprocess.TimeoutExpired:
            result = {'available': False, 'probe_status': 'timeout',
                                'reason': 'Consulta da galeria GTK4 excedeu 10 s; disponibilidade não confirmada.'}
        except (OSError, ValueError, TypeError) as error:
            result = {'available': False, 'probe_status': 'error', 'reason': str(error)}
    else:
        result = {'available': False, 'reason': 'Galeria GTK4 C ABI ausente.'}
    return result


def _probe_inventory(root, executor):
    families = {}
    gtk4_future = executor.submit(gtk4_probe, root)
    qt_futures = {family: executor.submit(python_probe,
        f'from {module}.QtCore import qVersion\nimport json\nprint(json.dumps({{"available":True,"version":qVersion(),"application_initialized":False}}))')
        for family, module in (("qt5", "PyQt5"), ("qt6", "PyQt6"))}
    quick_future = executor.submit(python_probe,
        'from PyQt6.QtCore import qVersion\nfrom PyQt6.QtQml import QQmlApplicationEngine\nimport json\nprint(json.dumps({"available":True,"version":qVersion(),"application_initialized":False}))')
    gtk_futures = {}
    for family, version, library in (('gtk2', '2.0', 'libgtk-x11-2.0.so.0'), ('gtk3', '3.0', 'libgtk-3.so.0')):
        code = ('import ctypes as C,gi,json\n'
                f'assert {version!r} in gi.Repository.get_default().enumerate_versions("Gtk"), "GIR Gtk {version} indisponível"\n'
                f'library=C.CDLL({library!r})\n'
                'values=[]\n'
                'for kind in ("major","minor","micro"):\n')
        if family == 'gtk2':
            code += ' values.append(C.c_uint.in_dll(library,"gtk_"+kind+"_version").value)\n'
        else:
            code += ' function=getattr(library,"gtk_get_"+kind+"_version");function.restype=C.c_uint;values.append(function())\n'
        code += 'result={"available":True,"version":".".join(map(str,values)),"gtk_initialized":False}\n'
        if family == 'gtk2':
            code += (f'import sys\nsys.path.insert(0,{str(root / "tools/theme-lab")!r})\n'
                     'from gtk2_press_bridge import Gtk2PressBridge\n'
                     'try:\n'
                     f' bridge=Gtk2PressBridge({str(root)!r})\n'
                     ' result["control_states"]={name:["normal","pressed","disabled","backdrop"] for name in ("push","arrow")}\n'
                     ' result["pressure_reason"]="Pressão visual: GtkButton de comando/seta isolada, runtime 2.24.33 verificado."\n'
                     'except (OSError,ValueError,AttributeError) as error:\n'
                     ' result["control_states"]={name:["normal","disabled","backdrop"] for name in ("push","arrow")}\n'
                     ' result["pressure_reason"]=str(error)\n')
        code += 'print(json.dumps(result))\n'
        gtk_futures[family] = executor.submit(python_probe, code)
    for family, future in gtk_futures.items():
        families[family] = future.result()
    families['gtk4'] = gtk4_future.result()
    for family, future in qt_futures.items():
        families[family] = future.result()
    motif = ctypes.util.find_library('Xm')
    families['motif'] = {'available': bool(motif), 'library': motif, 'version': package_version('libxm4'),
                         'reason': 'Motif instalado não comprova a versão histórica da referência.' if motif else 'Biblioteca Motif não encontrada.'}
    gtk1 = ctypes.util.find_library('gtk-1.2')
    families['gtk1'] = {'available': False, 'library_detected': gtk1,
                       'reason': 'Sem galeria nativa GTK1 e tradução implementada.' if gtk1 else 'GTK1 não instalado; sem galeria nativa.'}
    families['gtk5'] = {'available': False, 'reason': 'Nenhum runtime ou galeria GTK5 disponível; não é simulado.'}
    plugins = list(Path('/usr/lib').glob('*/qt6/plugins/styles/libkvantum.so'))
    families['kvantum'] = {'available': bool(plugins) and families['qt6']['available'],
                           'version': package_version('qt6-style-kvantum'), 'plugins': [str(p) for p in plugins],
                           'reason': 'Galeria Qt6 real com estilo Kvantum disponível para adaptação de barras.'}
    quick = quick_future.result()
    try:
        from plasma_recipe import component_source
        plasma_source = component_source()
    except (OSError, ImportError):
        plasma_source = None
    plasma_available = bool(quick.get('available') and plasma_source)
    families['plasma'] = {
        **quick, 'available': plasma_available, 'native_gallery': plasma_available,
        'preview_kind': 'native_plasma_components_ksvg',
        'renderer_source': str(plasma_source) if plasma_source else None,
        'reason': ('Plasma Components.ScrollBar/KSvg disponíveis para prévia nativa.'
                   if plasma_available else
                   'QML Plasma Components.ScrollBar/KSvg ou QtQuick6 indisponível; não substituir por galeria Qt Quick genérica.')}
    for family in FAMILIES:
        item = families[family]
        item['adapter'] = ('gtk3_private_recipe' if family == 'gtk3' else
                           'gtk2_private_recipe' if family == 'gtk2' else
                           'gtk4_private_partial_recipe' if family == 'gtk4' else
                           'qt5_private_widgets_partial_recipe' if family == 'qt5' else
                           'qt6_private_widgets_partial_recipe' if family == 'qt6' else
                           'kvantum_private_svg_recipe' if family == 'kvantum' else
                           'plasma_private_desktoptheme_recipe' if family == 'plasma' else 'not_implemented')
        if family == 'gtk4':
            item['translated_controls'] = ['push', 'toggle', 'check',
                                           'scroll_h', 'scroll_v']
        elif family == 'qt5':
            item['translated_controls'] = ['push', 'toggle', 'check', 'radio', 'entry',
                                           'text', 'combo', 'spin', 'scale_h', 'scale_v',
                                           'arrow', 'progress', 'list', 'frame',
                                           'scroll_h', 'scroll_v']
        elif family == 'qt6':
            item['translated_controls'] = ['push', 'toggle', 'check', 'radio', 'entry',
                                           'text', 'combo', 'spin', 'scale_h', 'scale_v',
                                           'arrow', 'progress', 'list', 'frame',
                                           'scroll_h', 'scroll_v']
        elif family in ('kvantum', 'plasma'):
            item['translated_controls'] = ['scroll_h', 'scroll_v']
        item['recipe_applied'] = False
        item['native_gallery'] = (root / 'plasma/tests/galerias-nativas' /
            {'gtk2': 'gtk2_demo.py', 'gtk3': 'gtk3_demo.py', 'gtk4': 'gtk4_demo.py', 'qt5': 'qt5_demo.py',
             'qt6': 'qt6_demo.py', 'kvantum': 'qt6_demo.py', 'plasma': 'qtquick_demo.py'}.get(family, '__absent__')).is_file()
    return {'status': 'ok', 'families': {family: families[family] for family in FAMILIES},
            'gui_started': False, 'scope': 'Installed libraries/imports; no historical fidelity or visual test claimed.'}


def private_namespace(root):
    if os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') != 'bwrap':
        raise Unavailable('Abra pelo lançador privado: a prévia exige o namespace bwrap coordenado.')
    gallery = root / 'plasma/tests/galerias-nativas'
    sys.path.insert(0, str(gallery))
    from qt6_demo import private_guards
    from demo_env import require_private_session
    try:
        proof = private_guards()
        require_private_session()
    except RuntimeError as error:
        raise Unavailable('Abra pelo lançador privado: ' + str(error)) from error
    return proof


def embedded_user_preview_guard(root, project, rc_file, events_directory,
                                session_root, embed_window, *, family='gtk2',
                                capture_mode=False, capture_output=None):
    """Allow a narrowly-scoped GTK2/GTK3/GTK4 child or paint capture.

    XEmbed must share the host X server. The manual editor's GTK2 sample is a
    Gtk.OffscreenWindow and also needs the host GTK2 runtime, but it never maps
    a top-level window. Keep both exceptions narrower than the gallery bwrap
    route and constrain all project/output files to the private lab directory.
    """
    if family not in ('gtk2', 'gtk3', 'gtk4'):
        raise Unavailable('A sessão normal aceita somente as prévias GTK2/GTK3/GTK4 explicitamente suportadas.')
    if os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') == 'bwrap':
        raise Unavailable('Use a guarda da sessão bwrap para a prévia privada.')
    if capture_mode:
        if embed_window is not None or capture_output is None:
            raise Unavailable('A captura da sessão normal deve ser somente offscreen.')
    elif embed_window is None or type(embed_window) is not int or not 1 <= embed_window <= 0xffffffff:
        raise Unavailable('A exceção da sessão normal vale somente para XEmbed ou captura offscreen do Theme Lab.')

    home = Path.home().resolve()
    session_root = Path(session_root).absolute()
    allowed_root = home / 'tempia' / 'domainos-theme-work'
    try:
        if (session_root.is_symlink() or session_root.resolve(strict=True) != session_root or
                not session_root.is_relative_to(allowed_root) or
                not session_root.is_dir() or session_root.stat().st_uid != os.getuid() or
                stat.S_IMODE(session_root.stat().st_mode) != 0o700):
            raise ValueError
    except (OSError, RuntimeError, ValueError):
        raise Unavailable('A prévia XEmbed exige uma sessão própria, modo 0700, em ~/tempia/domainos-theme-work/.')

    def private_child(value, *, directory=False, may_not_exist=False):
        path = Path(value).absolute()
        try:
            if path.is_symlink() or path.resolve(strict=not may_not_exist) != path or not path.is_relative_to(session_root):
                raise ValueError
            relative = path.relative_to(session_root)
            current = session_root
            for part in relative.parts:
                current = current / part
                if current.exists() or current.is_symlink():
                    info = current.lstat()
                    if stat.S_ISLNK(info.st_mode) or info.st_uid != os.getuid():
                        raise ValueError
            if not may_not_exist:
                info = path.lstat()
                if directory and not stat.S_ISDIR(info.st_mode):
                    raise ValueError
                if not directory and not stat.S_ISREG(info.st_mode):
                    raise ValueError
            return path
        except (OSError, RuntimeError, ValueError):
            raise Unavailable('Projeto, receita e eventos da prévia devem permanecer dentro da sessão privada do Theme Lab.')

    project = private_child(project)
    rc_path = Path(rc_file).absolute()
    rc_file = private_child(rc_path, directory=rc_path.is_dir())
    events_directory = private_child(events_directory, directory=True, may_not_exist=True)
    if capture_mode:
        capture_output = private_child(capture_output, may_not_exist=True)
        if (capture_output.parent != events_directory or
                not re.fullmatch(r'paint-sample-[0-9a-f]{32}\.png', capture_output.name)):
            raise Unavailable('Saída da captura deve ser um PNG único dentro dos eventos privados.')

    display = os.environ.get('DISPLAY', '')
    if os.environ.get('GDK_BACKEND', 'x11') not in ('x11', 'X11'):
        raise Unavailable('Prévia acoplada exige um DISPLAY X11 local da sessão do Theme Lab.')
    try:
        x11 = verify_local_x11(display=display,
            authority=os.environ.get('XAUTHORITY', str(home / '.Xauthority')))
    except ValueError as error:
        raise Unavailable(str(error)) from error

    return {'verified': True,
            'mode': ('explicit_user_session_offscreen_capture' if capture_mode
                     else 'explicit_user_session_xembed'),
            'uid': os.getuid(), 'project': str(project), 'recipe': str(rc_file),
            'events': str(events_directory), 'session_root': str(session_root),
            'display': display, 'xauthority': x11['xauthority'],
            'x11_transport': x11['transport'], 'x11_peer': x11['peer'],
            'personal_profile_written': False,
            'scope': (f'Somente captura {family.upper()} offscreen; não mapeia janela.'
                      if capture_mode else
                      f'Somente a cena {family.upper()} acoplada do Theme Lab por XEmbed.')}


def private_output(path, root):
    path = Path(path).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Saída privada não pode atravessar links ou ..')
    tempia_root = Path.home() / 'tempia'
    in_tempia = path.is_relative_to(tempia_root) and path != tempia_root
    in_lab = (path.is_relative_to(root) and path != root
              and path.relative_to(root).parts[0].startswith('.qa-'))
    in_namespace = (os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') == 'bwrap'
                    and path.is_relative_to(Path('/home/domainos-test')) and path != Path('/home/domainos-test'))
    direct_root = Path(os.environ.get('IRIX_DOMAINOS_SESSION_ROOT', '/')).absolute()
    actual_home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    allowed_direct = actual_home / 'tempia/domainos-theme-work'
    try:
        direct_info = direct_root.lstat()
        direct_root_valid = (os.environ.get('IRIX_DOMAINOS_DIRECT_PREVIEW') == '1' and
            direct_root != allowed_direct and direct_root.is_relative_to(allowed_direct) and
            stat.S_ISDIR(direct_info.st_mode) and not stat.S_ISLNK(direct_info.st_mode) and
            direct_info.st_uid == os.getuid() and stat.S_IMODE(direct_info.st_mode) == 0o700)
    except OSError:
        direct_root_valid = False
    in_direct = (direct_root_valid and path.is_relative_to(direct_root) and path != direct_root)
    if not (in_tempia or in_lab or in_namespace or in_direct):
        raise ValueError('Escolha saída privada em ~/tempia, em .qa-* do projeto ou no HOME do namespace.')
    if in_namespace:
        private_namespace(root)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ValueError('A saída precisa ser diretório do usuário com permissão 0700.')
    return path


def load_builder(root):
    source = root / 'gtk/tools/build_kde_domainos.py'
    sys.path.insert(0, str(source.parent))
    sys.path.insert(0, str(root / 'tools'))
    spec = importlib.util.spec_from_file_location('theme_lab_private_gtk3_builder', source)
    if not spec or not spec.loader:
        raise Unavailable('Gerador GTK3 não encontrado.')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def exported_roles(path, art):
    """Read native effective state roles, never infer Disabled from normal RGB."""
    payload = read_file(path, 256 * 1024)
    pattern = r'^\s*@define-color\s+(?:irix_kde_)?([A-Za-z_][A-Za-z0-9_]*)\s+(#[0-9A-Fa-f]{6})\s*;\s*$'
    colors = dict((name, value.lower()) for name, value in re.findall(pattern, payload.decode(), re.M))
    aliases = {}
    for family, names in art.ROLES.items():
        for state, name in enumerate(names):
            if name in colors:
                continue
            if family in ('header', 'title', 'header-fg', 'title-fg'):
                fallback = art.ROLES['window-fg' if family.endswith('-fg') else 'window'][state]
                if fallback in colors:
                    colors[name] = colors[fallback]
                    aliases[name] = fallback
            if name not in colors:
                raise Unavailable('Exportação GTK sem papel de estado efetivo: ' + name)
    return colors, {'path': str(path), 'sha256': sha(payload), 'kind': 'effective_kde_gtk_export', 'role_fallbacks': aliases}


def native_roles(root, path, art, expected_hash):
    """Read a selected file through KDE's own state algorithms, in a child."""
    helper = root / 'tools/theme-lab/build/theme-lab-colors'
    source = root / 'tools/theme-lab/src/native_colors.cpp'
    if not helper.is_file() or not os.access(helper, os.X_OK):
        raise Unavailable('Leitor nativo KDE não compilado: tools/theme-lab/build/theme-lab-colors')
    helper_hash, source_hash = sha(read_file(helper, 16 * LIMIT)), sha(read_file(source))
    if sha(read_file(path)) != expected_hash:
        raise Unavailable('O esquema mudou antes da leitura nativa; aplique novamente.')
    environment = dict(os.environ)
    for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'DBUS_SYSTEM_BUS_ADDRESS',
                'QT_STYLE_OVERRIDE', 'QT_QPA_PLATFORMTHEME', 'QT_PLUGIN_PATH', 'KDE_COLOR_SCHEME_PATH'):
        environment.pop(key, None)
    try:
        child = subprocess.run([str(helper), '--config', str(path)], env=environment,
                               capture_output=True, text=True, timeout=15)
        if len(child.stdout.encode()) > 256 * 1024:
            raise Unavailable('Resposta do leitor nativo excedeu o limite.')
        result = json.loads(child.stdout)
    except (subprocess.SubprocessError, ValueError) as error:
        raise Unavailable('Leitura nativa KDE falhou: ' + str(error)) from error
    if child.returncode or result.get('status') != 'ok':
        raise Unavailable('Leitura nativa KDE indisponível: ' + str(result.get('reason', child.stderr.strip())))
    colors, origin = result.get('colors'), result.get('origin')
    required = {name for names in art.ROLES.values() for name in names}
    if (not isinstance(colors, dict) or not required <= colors.keys() or
            any(not isinstance(value, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', value) for value in colors.values())):
        raise Unavailable('Leitor nativo não forneceu todos os papéis GTK3 válidos.')
    if (not isinstance(origin, dict) or origin.get('path') != str(path) or
            origin.get('sha256') != expected_hash or result.get('gui_started') is not False or
            result.get('config_written') is not False):
        raise Unavailable('Proveniência do leitor nativo não corresponde à entrada selecionada.')
    if (sha(read_file(path)) != expected_hash or sha(read_file(helper, 16 * LIMIT)) != helper_hash
            or sha(read_file(source)) != source_hash):
        raise Unavailable('Entrada ou leitor nativo mudou durante a leitura; aplique novamente.')
    origin.update(helper={'path': str(helper), 'sha256': helper_hash},
                  helper_source={'path': str(source), 'sha256': source_hash},
                  snapshot_sha256=sha(json.dumps(colors, sort_keys=True, separators=(',', ':')).encode()),
                  role_fallbacks={}, selection_scope='Child GTK3 recipe only; no host/profile scheme change')
    return {name: value.lower() for name, value in colors.items()}, origin


def palette_inputs_current(receipt):
    """A selected scheme and its reader are inputs, not the current GTK export."""
    inputs = receipt.get('palette_inputs')
    if inputs is None:  # Compatibility with already written V1 receipts.
        inputs = [receipt['kdeglobals'], receipt['palette']]
    try:
        return all(sha(read_file(Path(item['path']), 16 * LIMIT)) == item['sha256'] for item in inputs)
    except OSError:
        return False


def generation_sources_current(receipt, root):
    """Reject cached generations whose GTK2 source inputs are stale or unsafe."""
    sources = receipt.get('sources')
    if not isinstance(sources, dict) or not sources:
        return False
    base = Path(root).resolve()
    try:
        for name, expected in sources.items():
            relative = Path(name) if isinstance(name, str) else None
            if (relative is None or relative.is_absolute() or not relative.parts or
                    any(part in ('.', '..') for part in relative.parts) or
                    not isinstance(expected, str) or
                    not re.fullmatch(r'[0-9a-f]{64}', expected)):
                return False
            source = (base / relative).resolve(strict=True)
            if not source.is_relative_to(base) or sha(read_file(source)) != expected:
                return False
        return True
    except (OSError, ValueError, RuntimeError):
        return False


@contextmanager
def recipe_rules(builder, rules):
    """In-memory, scoped translation; canonical generators/contracts stay intact."""
    art = builder.art
    original_plan, original_roles = art.pixel_plan, art.ROLES
    mapped = copy.deepcopy(original_roles)
    for target, key in (('button', 'face_role'), ('button-fg', 'text_role'), ('view', 'view_role'), ('selection', 'selection_role')):
        mapped[target] = original_roles[ROLE_FAMILIES[rules[key]]]
    for target, key in (('view-fg', 'view_role'), ('selection-fg', 'selection_role')):
        source = ROLE_FAMILIES[rules[key]]
        mapped[target] = original_roles[source if source.endswith('-fg') else source + '-fg']
    art.ROLES = mapped
    def plan(family, token, *, inactive=False, disabled=False):
        result = original_plan(family, token, inactive=inactive, disabled=disabled)
        key = {'light': 'light', 'dark': 'shade', 'trough': 'trough'}.get(token)
        if key:
            result['mix'] = rules[key]
        return result
    art.pixel_plan = plan
    try:
        yield
    finally:
        art.pixel_plan, art.ROLES = original_plan, original_roles


def mask_metadata(builder, geometry, recipe=None):
    """Same symbolic slices as masks(), without writing any SVG or manifest."""
    entries = {}
    with piece_assets(builder, recipe or {}, geometry):
        assets = builder.art.assets() | builder.gtk3_assets(geometry=geometry)
    for name, (pixels, family, border) in assets.items():
        if border and not name.startswith('gtk3-'):
            continue
        width, height = len(pixels[0]), len(pixels)
        slices = []
        for region in builder.adaptive_assets._regions(width, height, border):
            x0, y0, x1, y1 = region['box']
            colors = sorted({token for row in pixels[y0:y1] for token in row[x0:x1] if token})
            layers = [{'file': name + ('-' + region['part'] if border else '') +
                       '-' + str(first//3) + '-symbolic.svg', 'colors': colors[first:first+3]}
                      for first in range(0, len(colors), 3)]
            slices.append(dict(region, layers=layers))
        entries[name] = {'width': width, 'height': height, 'border': border,
                         'family': family, 'slices': slices}
    return {'assets': entries}


def gtk3_sources(builder, manifest, recipe, geometry):
    """Shared by actual generation and the read-only control code viewer."""
    with recipe_rules(builder, recipe['palette']):
        common = re.sub(r'^@define-color[^\n]*\n', '', builder.common_css(manifest), flags=re.M)
        overrides = builder.gtk3_css(manifest, geometry=geometry)
        overrides += builder.rule('*', {'font-size': str(recipe['geometry']['font_px']) + 'px'})
        overrides += builder.rule('button, .button, entry, spinbutton',
                                  {'padding': str(recipe['geometry']['control_padding_px']) + 'px'})
        fitting = recipe.get('scrollbar_parts', {}).get('fitting', {})
        if fitting:
            gap = fitting.get('gap_px', geometry['view_bar_gap_px'])
            border = fitting.get('inset_px', geometry['view_inset_px'])
            overrides += builder.rule('scrolledwindow', {'-GtkScrolledWindow-scrollbar-spacing': str(gap)})
            for state, suffix in ((0, ''), (1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
                expression = builder.state_css('view', state)
                properties = builder.adaptive_assets.expression(
                    'gtk3-lab-view-frame', expression, prefix='adaptive/', manifest=manifest)
                properties.update({'background-color': expression('face'), 'border-color': 'transparent',
                                   'border-width': str(border) + 'px'})
                overrides += builder.rule('scrolledwindow > viewport' + suffix, properties)
        trough = recipe.get('scrollbar_parts', {}).get('trough', {})
        if trough:
            border = trough.get('shadow_px', geometry['shadow_px'])
            inner = trough.get('thickness_px', geometry['bar_px']) - 2 * border
            overrides += builder.rule('scrollbar.vertical trough', {'min-width': str(inner) + 'px'})
            overrides += builder.rule('scrollbar.horizontal trough', {'min-height': str(inner) + 'px'})
            for state, suffix in ((0, ''), (1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
                expression = builder.state_css('button', state)
                properties = builder.adaptive_assets.expression(
                    'gtk3-lab-trough-frame', expression, prefix='adaptive/', manifest=manifest)
                properties.update({'background-color': expression('trough'), 'border-color': 'transparent',
                                   'border-width': str(border) + 'px'})
                overrides += builder.rule('scrollbar' + suffix + ' contents', properties)
            contexts={'normal':((0,':not(:disabled):not(:backdrop)'),),
                      'disabled':((2,':disabled:not(:backdrop)'),(3,':disabled:backdrop')),
                      'backdrop':((1,':not(:disabled):backdrop'),)}
            for edit_state in trough.get('state_relief', {}):
                for palette_state,suffix in contexts[edit_state]:
                    expression=builder.state_css('button',palette_state)
                    properties=builder.adaptive_assets.expression(
                        'gtk3-lab-trough-'+edit_state,expression,prefix='adaptive/',manifest=manifest)
                    overrides += builder.rule('scrollbar'+suffix+' contents',properties)
        thumb = recipe.get('scrollbar_parts', {}).get('thumb', {})
        if thumb:
            border = thumb.get('shadow_px', geometry['shadow_px'])
            cross = thumb.get('cross_px', geometry['thumb_cross_px'])
            available = trough.get('thickness_px', geometry['bar_px']) - 2 * trough.get('shadow_px', geometry['shadow_px'])
            margin = (available - cross) // 2
            # Preserve the existing outer short-thumb floor. Its actual length
            # remains controlled by GtkRange/page size, not a historical value.
            minimum = geometry['bar_px'] + geometry['arrow_thumb_gap_px'] + 2 * geometry['shadow_px'] - 2 * border
            overrides += builder.rule('scrollbar slider', {'border-width': str(border) + 'px'})
            overrides += builder.rule('scrollbar.vertical slider', {
                'min-width': str(cross - 2 * border) + 'px', 'min-height': str(minimum) + 'px',
                'margin-left': str(margin) + 'px', 'margin-right': str(margin) + 'px'})
            overrides += builder.rule('scrollbar.horizontal slider', {
                'min-height': str(cross - 2 * border) + 'px', 'min-width': str(minimum) + 'px',
                'margin-top': str(margin) + 'px', 'margin-bottom': str(margin) + 'px'})
            gap = thumb.get('gap_px', geometry['arrow_thumb_gap_px'])
            for orientation, direction, edge in (('vertical', 'up', 'bottom'), ('vertical', 'down', 'top'),
                                                  ('horizontal', 'up', 'right'), ('horizontal', 'down', 'left')):
                overrides += builder.rule('scrollbar.' + orientation + ' button.' + direction,
                                          {'margin-' + edge: str(gap) + 'px'})
            for state, suffix in ((0, ''), (1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
                expression = builder.state_css('button', state)
                properties = builder.adaptive_assets.expression('gtk3-thumb-frame', expression, prefix='adaptive/', manifest=manifest)
                properties.update({'background-color': expression('face'), 'border-color': 'transparent',
                                   'border-width': str(border) + 'px'})
                overrides += builder.rule('scrollbar' + suffix + ' slider', properties)
        # The lab's standalone arrow is a real, compact GtkButton. Reuse the
        # generated triangle at its intrinsic pixel size; do not enlarge the
        # default GtkArrow renderer or change a canonical toolkit selector.
        # Its colours belong to the recipe's standalone Button family. Sharing
        # triangle geometry does not establish the scrollbar container's
        # colour context or visual equivalence with the VM's Trash Can.
        button = recipe.get('scrollbar_parts', {}).get('arrow_button', {})
        border = button.get('shadow_px', geometry['shadow_px'])
        padding = button.get('padding_px', 0)
        outer = geometry['arrow_px'] + 2 * geometry['shadow_px']
        inner = outer - 2 * (border + padding)
        for state, suffix in ((0, ''), (1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
            expression = builder.state_css('button', state)
            for pressed in (False, True):
                mode = 'disabled' if state & 2 else 'pressed' if pressed else 'normal'
                properties = builder.adaptive_assets.expression(
                    'gtk3-stepper-down-' + mode, expression, prefix='adaptive/', manifest=manifest)
                properties.update({'min-width': str(inner) + 'px',
                                   'min-height': str(inner) + 'px',
                                   'padding': str(padding) + 'px' if padding else '0', 'margin': '0',
                                   'border-width': str(border) + 'px',
                                   'background-origin': 'border-box', 'background-clip': 'border-box',
                                   'border-style': 'solid', 'border-image-source': 'none',
                                   'color': expression('ink'), 'background-color': expression('face')})
                overrides += builder.rule('button.theme-lab-arrow' + (':active' if pressed else '') + suffix,
                                          properties)
        relief = recipe.get('scrollbar_parts', {}).get('arrow', {}).get('state_relief', {})
        for edit_state in relief:
            # Exact native CSS states: no call to set the whole GtkRange state.
            # Normal excludes hover/focus/backdrop/disabled; those stay native.
            flags = {
                'normal':':not(:active):not(:hover):not(:focus):not(:disabled):not(:backdrop)',
                'pressed':':active:not(:disabled)',
                'disabled':':disabled',
                'backdrop':':not(:active):not(:hover):not(:focus):not(:disabled)',
                'hover':':hover:not(:active):not(:focus):not(:disabled)',
            }[edit_state]
            contexts = {
                'normal':((0, ':not(:disabled):not(:backdrop)'),),
                'pressed':((0, ':not(:disabled)'), (1, ':not(:disabled):backdrop')),
                'disabled':((2, ':disabled:not(:backdrop)'), (3, ':disabled:backdrop')),
                'backdrop':((1, ':not(:disabled):backdrop'),),
                'hover':((0, ':not(:disabled):not(:backdrop)'), (1, ':not(:disabled):backdrop')),
            }[edit_state]
            for palette_state, parent_suffix in contexts:
                expression = builder.state_css('button', palette_state)
                for orientation, css_direction, direction in (
                        ('vertical','up','up'), ('vertical','down','down'),
                        ('horizontal','up','left'), ('horizontal','down','right')):
                    properties = builder.adaptive_assets.expression(
                        'gtk3-lab-stepper-' + direction + '-' + edit_state,
                        expression, prefix='adaptive/', manifest=manifest)
                    properties['background-color'] = expression('trough')
                    selector = ('scrollbar.' + orientation + parent_suffix +
                                ' button.' + css_direction + flags)
                    overrides += builder.rule(selector, properties)
                properties = builder.adaptive_assets.expression(
                    'gtk3-lab-stepper-down-' + edit_state, expression,
                    prefix='adaptive/', manifest=manifest)
                properties['background-color'] = expression('face')
                overrides += builder.rule('button.theme-lab-arrow' + parent_suffix + flags, properties)
        source = Path(__file__).with_name('arrow_button_states.py')
        spec = importlib.util.spec_from_file_location('theme_lab_arrow_button_states', source)
        states = importlib.util.module_from_spec(spec);spec.loader.exec_module(states)
        overrides += states.css(builder, recipe)
        source=Path(__file__).with_name('thumb_states.py')
        spec=importlib.util.spec_from_file_location('theme_lab_thumb_states',source)
        states=importlib.util.module_from_spec(spec);spec.loader.exec_module(states)
        overrides += states.css(builder,recipe,manifest)
        source=Path(__file__).with_name('fitting_states.py')
        spec=importlib.util.spec_from_file_location('theme_lab_fitting_states',source)
        states=importlib.util.module_from_spec(spec);spec.loader.exec_module(states)
        overrides += states.css(builder,recipe,manifest)
    return common, overrides


def control_selector(selector, control):
    if control == 'arrow':
        return selector.startswith('button.theme-lab-arrow')
    if control == 'push':
        return bool(re.match(r'^(?:button|\.button):not\(\.toggle\):not\(\.combo\):not\(\.up\):not\(\.down\):not\(\.theme-lab-arrow\)(?=[:. >]|$)', selector))
    if control == 'toggle':
        return bool(re.match(r'^(?:button|\.button)\.toggle(?=[:. >]|$)', selector))
    if control == 'combo':
        return bool(re.match(r'^combobox(?=[:. >]|$)', selector))
    if control == 'spin':
        return bool(re.match(r'^spinbutton(?=[:. >]|$)', selector))
    if 'theme-lab-arrow' in selector:
        return False
    roots = {'check': 'check', 'radio': 'radio', 'entry': 'entry',
             'text': 'textview', 'scale_h': 'scale', 'scale_v': 'scale',
             'scroll_h': r'(?:scrollbar|scrolledwindow)', 'scroll_v': r'(?:scrollbar|scrolledwindow)',
             'progress': 'progressbar',
             'list': 'treeview', 'frame': 'frame'}
    if not re.match(r'^' + roots[control] + r'(?=[:. >]|$)', selector):
        return False
    if control in ('scale_h', 'scroll_h') and '.vertical' in selector:
        return False
    if control in ('scale_v', 'scroll_v') and '.horizontal' in selector:
        return False
    return True


def gtk3_control_palette_selector(selector, control):
    """Scope shared GtkButton CSS nodes to one native control class.

    GTK3 uses one `button` CSS node for several controls. The class/context
    path distinguishes GtkToggleButton, GtkComboBox, GtkSpinButton and the
    Theme Lab's standalone GtkArrow sample. A plain push button excludes those
    classes and the range stepper classes. This avoids exporting one control's
    semantic palette into another control's child button.
    """
    match = re.match(r'^(button|\.button)(.*)$', selector)
    if control == 'arrow' and selector.startswith('button.theme-lab-arrow'):
        return selector
    if control in ('push', 'toggle', 'combo', 'spin', 'arrow') and match:
        root, tail = match.groups()
        if any(token in tail for token in ('.toggle', '.combo', '.up', '.down', '.theme-lab-arrow')):
            if control == 'toggle' and '.toggle' in tail and not any(
                    token in tail for token in ('.combo', '.up', '.down', '.theme-lab-arrow')):
                return selector
            if control == 'combo' and '.combo' in tail and not any(
                    token in tail for token in ('.toggle', '.up', '.down', '.theme-lab-arrow')):
                return 'combobox > box > ' + selector
            if control == 'spin' and ('.up' in tail or '.down' in tail) and not any(
                    token in tail for token in ('.toggle', '.combo', '.theme-lab-arrow')):
                return 'spinbutton > ' + selector
            return None
        if any(token in tail for token in ('.flat', '.default')) and control in ('combo', 'spin', 'arrow'):
            return None
        if ':checked' in tail and control != 'toggle':
            return None
        if control == 'push':
            return root + ':not(.toggle):not(.combo):not(.up):not(.down):not(.theme-lab-arrow)' + tail
        if control == 'toggle':
            return root + '.toggle' + tail
        if control == 'combo':
            return 'combobox > box > button.combo' + tail
        if control == 'spin':
            return 'spinbutton > button' + tail
        if control == 'arrow':
            return 'button.theme-lab-arrow' + tail
    if control_selector(selector, control):
        return selector
    return None


def state_selector(selector, state):
    if state == 'focus' and ':not(:focus)' in selector:
        return False
    if state == 'hover' and ':not(:hover)' in selector:
        return False
    if state == 'pressed' and ':not(:active)' in selector:
        return False
    if state == 'backdrop' and ':not(:backdrop)' in selector:
        return False
    # Endpoint-disabled children remain a normal/backdrop parent's colour
    # dependency. Do not classify :not(:disabled) as a disabled parent.
    tested = re.sub(r':not\([^)]*\)', '', selector)
    boundary = ':not(:disabled)' in selector and ' button.' in selector and ':disabled' in tested
    disabled, backdrop = ':disabled' in tested, ':backdrop' in tested
    if boundary:
        return state in ('normal', 'pressed', 'backdrop') and backdrop == (state == 'backdrop')
    if disabled:
        return state == 'disabled' and not backdrop
    if backdrop:
        return state == 'backdrop'
    if ':hover' in tested:
        return state == 'hover'
    if ':focus' in tested:
        return state == 'focus'
    active = ':active' in tested or ':checked' in tested or ':indeterminate' in tested
    return not active or state == 'pressed'


def gtk3_css_rule_blocks(source):
    """Return one CSS block per selector for the deliberately simple GTK3 output."""
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
    for selector_group, properties in re.findall(r'([^{}]+)\{([^{}]*)\}', source):
        for selector in selector_group.strip().split(','):
            selector = selector.strip()
            if selector:
                yield selector, properties


def gtk3_palette_selector(selector, control):
    """Specialize orientation-neutral GTK CSS nodes for a directional widget."""
    if control in ('scale_h', 'scale_v'):
        if not selector.startswith('scale'):
            return selector
        if '.horizontal' in selector or '.vertical' in selector:
            return selector
        orientation = 'horizontal' if control == 'scale_h' else 'vertical'
        return 'scale.' + orientation + selector[len('scale'):]
    if control in ('scroll_h', 'scroll_v'):
        if selector.startswith('scrolledwindow'):
            # This node is the enclosing content container, not either bar.
            return None
        if not selector.startswith('scrollbar'):
            return selector
        if '.horizontal' in selector or '.vertical' in selector:
            return selector
        orientation = 'horizontal' if control == 'scroll_h' else 'vertical'
        return 'scrollbar.' + orientation + selector[len('scrollbar'):]
    return selector


def gtk3_control_palette_overrides(builder, manifest, recipe, geometry):
    """Compile semantic overrides only when GTK3 selectors isolate their controls.

    GTK3 themes style CSS nodes, not Theme Lab object IDs. Some controls share
    a node (for example GtkButton, combo buttons and spin buttons); differing
    palettes for those controls cannot be represented faithfully by a broad
    selector. Refuse that export instead of leaking one control's colors into
    another.
    """
    overrides = recipe.get('control_palettes', {})
    if not overrides:
        return '', {'status': 'none', 'controls': [], 'selectors': []}
    base = recipe['palette']
    rules_by_control = {}
    for control, palette in overrides.items():
        if palette == base:
            continue
        for key in DEFAULT_ROLES:
            if palette.get(key) not in ROLE_FAMILIES:
                raise Unavailable('GTK3 sem tradução de papel KDE para ' + control + ': ' + str(palette.get(key)))
        tailored = copy.deepcopy(recipe)
        tailored['palette'] = palette
        common, css = gtk3_sources(builder, manifest, tailored, geometry)
        selected = []
        for selector, properties in gtk3_css_rule_blocks(common + css):
            target = gtk3_control_palette_selector(selector, control)
            if target is not None:
                target = gtk3_palette_selector(target, control)
                if target is not None:
                    selected.append((target, properties))
        if not selected:
            raise Unavailable('GTK3 não emite seletores nativos para o controle ' + control)
        for selector, _properties in selected:
            owners = [other for other in CONTROLS if control_selector(selector, other)]
            different = [other for other in owners
                         if overrides.get(other, base) != palette]
            if different:
                names = ', '.join([control] + different)
                raise Unavailable('GTK3 compartilha o seletor "' + selector + '" entre ' + names +
                                   '; papéis/fatores distintos não podem ser isolados sem afetar outro controle.')
        rules_by_control[control] = selected
    emitted, selectors = [], []
    seen = set()
    for control, blocks in rules_by_control.items():
        for selector, properties in blocks:
            key = (selector, properties)
            if key in seen:
                continue
            seen.add(key)
            emitted.append(selector + ' {' + properties + '}\n')
            selectors.append(selector)
    return ''.join(emitted), {'status': 'applied', 'controls': sorted(rules_by_control),
                              'selectors': selectors,
                              'color_source': 'selected KDE semantic roles and illumination factors'}


def snippet(root, model, family=None, control=None, recipe_state=None, kdeglobals=None):
    """One selected control, named-role expressions and no final sampled RGB."""
    family = family or model['selected_family']
    recipe = model['recipes'][family]
    require_scroll_parts_adapter(recipe, family)
    index = CONTROLS.index(control) if control else recipe.get('selected_control', 0)
    control, state = CONTROLS[index], EDIT_STATES[recipe.get('edit_state', 0)]
    if recipe_state is not None:
        button_piece = family == 'gtk3' and recipe.get('selected_scroll_part',0) == 1
        if family=='gtk3' and recipe.get('selected_scroll_part',0)==2 and recipe_state not in ('normal','disabled','backdrop'):
            raise Unavailable('Moldura contínua GTK3 contents: pressão/hover removidos pelo GtkRange; barra padrão sem foco. Estado não traduzido: '+recipe_state)
        if family=='gtk3' and recipe.get('selected_scroll_part',0)==4 and recipe_state not in ('normal','disabled','backdrop'):
            raise Unavailable('Encaixe GtkViewport não interativo. Estado não traduzido: '+recipe_state)
        if button_piece and control in ('scroll_h','scroll_v','arrow'):
            index=CONTROLS.index('arrow');control='arrow'
        if recipe_state not in EDIT_STATES + ('hover',) and not (button_piece and control == 'arrow' and recipe_state == 'focus'):
            raise Unavailable('Trecho deste estado da peça ainda não traduzido: ' + str(recipe_state))
        state = recipe_state
    palette_control=control
    control_palette=recipe.get('control_palettes',{}).get(palette_control)
    if control_palette is not None:
        recipe=copy.deepcopy(recipe)
        recipe['palette']=control_palette
    positions = recipe.get('positions', [[16 + (i % 4)*160, 16 + (i // 4)*80] for i in range(16)])
    result = {'status': 'ok', 'family': family, 'control': control, 'selected_control': index,
              'state': state, 'position': positions[index], 'color_scheme': model.get('color_scheme', ''),
              'recipe_applied': False, 'picked_used': False, 'host_changed': False,
              'scrollbar_parts': recipe.get('scrollbar_parts', {}),
              'arrow_button_scope': 'Standalone GtkButton only; GtkRange internal buttons remain unchanged',
              'scope': 'Only the selected control; code inspection is not a native visual test.'}
    result['palette_control']=palette_control
    result['palette_source']='control_override' if control_palette is not None else 'family_default'
    result['palette_rules']=copy.deepcopy(recipe['palette'])
    result['size_request'] = recipe.get('sizes', [[0, 0] for _ in range(16)])[index]
    if family == 'gtk2' and control in ('scroll_h', 'scroll_v'):
        from gtk2_rc_fragments import selected_fragment
        result.pop('arrow_button_scope', None)
        result.update(language='gtkrc', source_kind='translated_native_fragment',
                      source=selected_fragment(recipe, control, state),
                      painting_dependencies='Verified KDE-derived RC and PNG snapshot; no final RGB in this fragment',
                      scope='Selected GTK2 scrollbar piece and required native geometry; not a complete theme')
    elif family == 'gtk2' and control == 'push':
        from gtk2_buttons import selected_fragment
        result.pop('arrow_button_scope', None)
        result.update(language='gtkrc', source_kind='translated_native_fragment',
                      source=selected_fragment(recipe, state),
                      painting_dependencies='Verified KDE-derived button RC and PNG snapshot',
                      scope='Selected GTK2 push button; not a complete theme')
    elif family == 'gtk2' and control == 'toggle':
        from gtk2_toggles import selected_fragment
        result.pop('arrow_button_scope',None)
        result.update(language='gtkrc',source_kind='translated_native_fragment',
                      source=selected_fragment(recipe,state),
                      painting_dependencies='Verified KDE-derived toggle RC and PNG snapshot',
                      scope='Selected GTK2 toggle; native selection independent of hover, not a complete theme')
    elif family == 'gtk2' and control in ('radio','check'):
        from gtk2_indicators import indicator_fragment
        result.pop('arrow_button_scope',None)
        result.update(language='gtkrc',source_kind='translated_native_fragment',
                      source=indicator_fragment(recipe,state,control),
                      painting_dependencies='Verified KDE-derived indicator RC and PNG snapshot',
                      scope='Selected GTK2 indicator; native interaction verified separately')
    elif family == 'gtk2' and control in ('progress', 'entry', 'text', 'combo', 'spin', 'scale_h', 'scale_v', 'arrow', 'list', 'frame'):
        if kdeglobals is None:
            raise Unavailable('Trecho GTK2 exige origem explícita dos papéis KDE.')
        if control == 'frame':
            from gtk2_frames import selected_fragment
        elif control == 'list':
            from gtk2_lists import selected_fragment
        elif control == 'arrow':
            from gtk2_arrows import selected_fragment
        elif control in ('scale_h','scale_v'):
            from gtk2_scales import selected_fragment
        elif control == 'spin':
            from gtk2_spins import selected_fragment
        elif control == 'combo':
            from gtk2_combos import selected_fragment
        elif control == 'text':
            from gtk2_text import selected_fragment
        elif control == 'entry':
            from gtk2_entries import selected_fragment
        else:
            from gtk2_progress import selected_fragment
        builder = load_builder(root)
        _, selected = selected_palette(model, kdeglobals, root)
        colors, _ = native_roles(root, Path(selected['path']), builder.art, selected['sha256'])
        with recipe_rules(builder,recipe['palette']):
            fragment = selected_fragment(recipe,state,builder,colors)
        result.pop('arrow_button_scope',None)
        result.update(language='gtkrc',source_kind='translated_native_fragment',
                      source=fragment,
                      painting_dependencies='Verified KDE-derived '+control+' RC and PNG snapshot',
                      scope='Selected GTK2 '+control+'; native verification separate')
    elif family == 'gtk4' and control in ('scroll_h', 'scroll_v'):
        if kdeglobals is None:
            raise Unavailable('Trecho GTK4 scrollbar exige origem explícita dos papéis KDE.')
        from gtk4_scrollbars import selected_fragment
        builder=load_builder(root)
        _,selected=selected_palette(model,kdeglobals,root)
        colors,_=native_roles(root,Path(selected['path']),builder.art,selected['sha256'])
        with recipe_rules(builder,recipe['palette']):
            fragment=selected_fragment(builder.art,recipe,colors,state)
        result.pop('arrow_button_scope',None)
        result.update(language='css',source_kind='translated_native_fragment',
                      source=fragment,
                      painting_dependencies='GTK4 native trough/slider CSS and KDE-role-derived relief assets from a verified private snapshot',
                      scope='Selected GTK4 '+control+'; native arrows intentionally unavailable, runtime integration is private')
    elif family == 'gtk4' and control in ('push','toggle','check'):
        if kdeglobals is None:
            raise Unavailable('Trecho GTK4 exige origem explícita dos papéis KDE.')
        if control=='toggle':
            from gtk4_toggles import selected_fragment
        elif control=='check':
            from gtk4_checks import selected_fragment
        else:
            from gtk4_buttons import selected_fragment
        builder=load_builder(root)
        _,selected=selected_palette(model,kdeglobals,root)
        colors,_=native_roles(root,Path(selected['path']),builder.art,selected['sha256'])
        with recipe_rules(builder,recipe['palette']):
            fragment=selected_fragment(builder,recipe,colors,state)
        result.pop('arrow_button_scope',None)
        result.update(language='css',source_kind='translated_native_fragment',source=fragment,
                      painting_dependencies='Verified KDE role definitions and generation-qualified GTK4 PNG slices',
                      scope='Selected GTK4 '+control+'; no final sampled RGB, native verification separate')
    elif family != 'gtk3':
        payload = {'family': family, 'control': control, 'state': state, 'position': positions[index],
                   'size_request': result['size_request'],
                   'geometry': recipe['geometry'], 'palette_rules': recipe['palette'],
                   'implementation': 'not_implemented'}
        result.update(status='not_implemented', language='json', source_kind='proposed_recipe',
                      reason='Receita do controle registrada; tradutor desta família ainda não implementado.',
                      source=json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        builder = load_builder(root)
        for key in DEFAULT_ROLES:
            if recipe['palette'][key] not in ROLE_FAMILIES:
                raise Unavailable('GTK3 sem tradução de estado para o papel: ' + recipe['palette'][key])
        geometry = dict(builder.gtk3_scrollbar_rules()['geometry'],
                        **{key: recipe['geometry'][key] for key in GEOMETRY[:7]})
        manifest = mask_metadata(builder, geometry, recipe)
        common, overrides = gtk3_sources(builder, manifest, recipe, geometry)
        source = re.sub(r'/\*.*?\*/', '', common + overrides, flags=re.S)
        blocks = []
        for selectors, properties in re.findall(r'([^{}]+)\{([^{}]*)\}', source):
            kept = []
            for item in selectors.strip().split(','):
                item=item.strip()
                if not state_selector(item, state):
                    continue
                target=gtk3_control_palette_selector(item, control)
                if target is not None:
                    kept.append(target)
            if kept:
                blocks.append(', '.join(kept) + ' {' + properties + '}\n')
        arrow_scope = (' * Seta independente: GtkButton; face: ' + recipe['palette']['face_role'] +
                       '; texto: ' + recipe['palette']['text_role'] + '.\n'
                       ' * Reutiliza geometria; não valida a composição/paleta da barra de rolagem ou do Trash Can.\n'
                       if control == 'arrow' else '')
        piece_scope = ''
        if control == 'arrow' and recipe.get('scrollbar_parts', {}).get('arrow'):
            part = recipe['scrollbar_parts']['arrow']
            piece_scope = (' * Triângulo proposto: ' + str(part.get('glyph_px', geometry['arrow_px'])) +
                           'px; relevo: ' + str(part.get('shadow_px', geometry['shadow_px'])) +
                           'px. Espaço reservado mantido: ' + str(geometry['arrow_px']) + 'px.\n')
        if control == 'arrow' and recipe.get('scrollbar_parts', {}).get('arrow_button'):
            button = recipe['scrollbar_parts']['arrow_button']
            piece_scope += (' * Botão isolado: moldura ' + str(button.get('shadow_px', geometry['shadow_px'])) +
                            'px; espaço interno ' + str(button.get('padding_px', 0)) +
                            'px. Não se aplica aos nós internos GtkRange.\n')
        if control in ('scroll_h', 'scroll_v') and recipe.get('scrollbar_parts', {}).get('trough'):
            trough = recipe['scrollbar_parts']['trough']
            piece_scope += (' * Trilho independente: espessura proposta ' +
                            str(trough.get('thickness_px', geometry['bar_px'])) +
                            'px; relevo ' + str(trough.get('shadow_px', geometry['shadow_px'])) +
                            'px. Moldura da área de conteúdo preservada.\n'
                            ' * Alocações efetivas dependem do GtkRange; medir na prévia nativa.\n')
        if control in ('scroll_h', 'scroll_v') and recipe.get('scrollbar_parts', {}).get('thumb'):
            thumb = recipe['scrollbar_parts']['thumb']
            piece_scope += (' * Cursor independente: espessura ' +
                            str(thumb.get('cross_px', geometry['thumb_cross_px'])) +
                            'px; relevo ' + str(thumb.get('shadow_px', geometry['shadow_px'])) +
                            'px; distância ' + str(thumb.get('gap_px', geometry['arrow_thumb_gap_px'])) +
                            'px. Comprimento calculado pelo GtkRange.\n')
        if control in ('scroll_h', 'scroll_v') and recipe.get('scrollbar_parts', {}).get('fitting'):
            fitting = recipe['scrollbar_parts']['fitting']
            piece_scope += (' * Encaixe independente: distância conteúdo–barra ' +
                            str(fitting.get('gap_px', geometry['view_bar_gap_px'])) +
                            'px; moldura do GtkViewport ' +
                            str(fitting.get('inset_px', geometry['view_inset_px'])) +
                            'px. Não cria moldura equivalente em GtkTreeView.\n')
        result.update(language='css', source_kind='gtk3_generated_css_subset',
                      source='/* GTK3: ' + control + ' / ' + state + '\n'
                             ' * Paleta: papéis KDE; amostra da pipeta não aplicada.\n'
                             ' * Sufixo _breeze é alias do exportador; os valores vêm do esquema KDE escolhido.\n'
                             + arrow_scope + piece_scope +
                             ' * Herda de * no tema gerado: font-size: ' +
                             str(recipe['geometry']['font_px']) + 'px.\n'
                             ' * Máscaras adaptive/ são emitidas somente por --generate. */\n' + ''.join(blocks),
                      resource_dependencies='Symbolic masks generated privately by --generate',
                      global_dependencies={'font_px': recipe['geometry']['font_px'],
                                           'stepper_properties': control in ('scroll_h', 'scroll_v')},
                      effective_states_exported=False)
    if family == 'gtk3':
        width, height = result['size_request']
        result['source'] += ('\n/* Montagem nativa: set_size_request(' + str(width or -1) + ', ' + str(height or -1) +
                             '); 0 na receita preserva o tamanho automático.\n'
                             ' * O toolkit pode impor um tamanho mínimo ao conteúdo. */\n')
    result['text'] = result['source']
    return result


def generate_gtk3(root, folder, model, kdeglobals):
    builder = load_builder(root)
    contract = copy.deepcopy(builder.gtk3_scrollbar_rules())
    recipe = model['recipes']['gtk3']
    require_scroll_parts_adapter(recipe)
    for key in DEFAULT_ROLES:
        if recipe['palette'][key] not in ROLE_FAMILIES:
            raise Unavailable('GTK3 sem tradução de estado para o papel: ' + recipe['palette'][key])
    geometry = dict(contract['geometry'], **{key: recipe['geometry'][key] for key in GEOMETRY[:7]})
    contract['geometry'] = geometry
    contract['geometry']['origin'] = 'Theme Lab proposed recipe; not a new historical measurement'
    write_json(folder / 'GTK3-PROPOSED-CONTRACT.json', contract)
    builder.gtk3_scrollbar_rules(folder / 'GTK3-PROPOSED-CONTRACT.json')
    current, selected_origin = selected_palette(model, kdeglobals, root)
    alternate = bool(model.get('color_scheme', ''))
    if alternate:
        colors, color_origin = native_roles(root, Path(selected_origin['path']), builder.art, selected_origin['sha256'])
        palette_inputs = [selected_origin, color_origin['helper'], color_origin['helper_source']]
        kde_origin = None
        write_json(folder / 'GTK3-NATIVE-COLORS.json', {'colors': colors, 'origin': color_origin})
    else:
        gtk_export = kdeglobals.parent / 'gtk-3.0/colors.css'
        if gtk_export.is_symlink():
            raise Unavailable('Exportação de cores GTK3 não pode ser um link simbólico.')
        if gtk_export.is_file():
            colors, color_origin = exported_roles(gtk_export, builder.art)
            kde_origin = selected_origin
            palette_inputs = [selected_origin, color_origin]
        else:
            # Isolated Theme Lab profiles do not run kde-gtk-config's exporter.
            # Resolve the selected KDE roles through the native KDE reader
            # instead of failing the whole generation or borrowing host colors.
            colors, color_origin = native_roles(
                root, Path(selected_origin['path']), builder.art, selected_origin['sha256'])
            kde_origin = selected_origin
            palette_inputs = [selected_origin, color_origin['helper'], color_origin['helper_source']]
            write_json(folder / 'GTK3-NATIVE-COLORS.json', {'colors': colors, 'origin': color_origin})
    # Detect an old exporter snapshot after a scheme change; allow only the
    # documented one-channel RGB8 rounding difference in native exports.
    for role, family in ROLE_FAMILIES.items():
        section = role.split('/', 1)[0]
        key = role.split('/', 1)[1]
        # Named schemes may omit an individual role while retaining its
        # section. KColorScheme has toolkit-defined defaults for that case;
        # validate only explicit values against the native reader, and keep
        # absent roles sourced from the reader's effective palette.
        if not current.has_option(section, key):
            continue
        rgb = rgb_role(current, role)
        exported = builder.art._rgb(colors[builder.art.ROLES[family][0]])
        if any(abs(a - b) > 1 for a, b in zip(rgb, exported)):
            raise Unavailable('Exportação GTK ainda não corresponde à origem de paleta selecionada: ' + role)
    name = 'ThemeLab-GTK3-' + folder.name.rsplit('-', 1)[-1]
    theme = folder / 'data/themes' / name
    common = theme / 'common'; common.mkdir(parents=True, mode=0o700)
    with recipe_rules(builder, recipe['palette']):
        with piece_assets(builder, recipe, geometry):
            manifest = builder.masks(common / 'adaptive', geometry=geometry)
    css, overrides = gtk3_sources(builder, manifest, recipe, geometry)
    control_css, control_palette_export = gtk3_control_palette_overrides(
        builder, manifest, recipe, geometry)
    overrides += control_css
    definitions = ''.join('@define-color ' + key + ' ' + value + ';\n' for key, value in sorted(colors.items()))
    (common / 'gtk.css').write_text(definitions + css, encoding='utf-8')
    (common / 'gtk-3.0-overrides.css').write_text(overrides, encoding='utf-8')
    write_json(common / 'CONTROL-PALETTE-EXPORT.json', control_palette_export)
    (theme / 'gtk-3.0').mkdir(mode=0o700)
    (theme / 'gtk-3.0/gtk.css').write_text('@import url("../common/gtk.css");\n@import url("../common/gtk-3.0-overrides.css");\n', encoding='utf-8')
    (theme / 'gtk-3.0/gtk-dark.css').write_text('@import url("gtk.css");\n', encoding='utf-8')
    (theme / 'index.theme').write_text('[Desktop Entry]\nType=X-GNOME-Metatheme\nName=' + name + '\n\n[X-GNOME-Metatheme]\nGtkTheme=' + name + '\n', encoding='utf-8')
    shutil.copyfile(root / 'decorations/domainos/LICENSE', theme / 'LICENSE')
    sources = [root / 'gtk/tools/build_kde_domainos.py', root / 'tools/domainos_motif_art.py',
               root / 'gtk/tools/adaptive_assets.py', root / 'tools/domainos_scrollbar_rules.json']
    origin = {'status': 'generated', 'family': 'gtk3', 'theme': name, 'theme_path': str(theme),
              'recipe_applied': True, 'historical_fidelity_claimed': False, 'scope': 'Private generated GTK3 recipe only',
              'reason': 'Receita GTK3 privada gerada; somente esta prévia filha usa GTK_THEME e XDG_DATA_DIRS dedicados.',
              'recipe': recipe, 'palette': color_origin, 'kdeglobals': kde_origin,
              'selected_scheme': selected_origin, 'palette_inputs': palette_inputs,
              'backend_sha256': sha(read_file(Path(__file__))),
              'source_consistency': 'Normal roles compared with selected source within RGB8 rounding 1; effective states come from native KColorScheme unless the current GTKConfig export exists. No normal-RGB approximation.',
              'states': ['normal', 'pressed', 'backdrop', 'insensitive', 'insensitive_backdrop'],
              'control_palette_export': control_palette_export,
              'sources': {str(p.relative_to(root)): sha(read_file(p)) for p in sources},
              'limitations': ['Populated GtkTreeView main frame remains the canonical GTK3 limitation.',
                              'Palette is an effective-role snapshot; apply again when its selected source changes.',
                              'Measured historical reference and proposed geometry remain separate.'],
              'picked_used': False}
    if not palette_inputs_current(origin):
        raise Unavailable('A paleta mudou durante a geração; aplique novamente.')
    write_json(theme / 'ORIGEM.json', origin)
    write_json(theme / 'MANIFEST.json', {'schema': 1, 'files': {str(p.relative_to(theme)): sha(p.read_bytes()) for p in sorted(theme.rglob('*')) if p.is_file()}})
    return origin


def generate(root, output, model, project_hash, kdeglobals, family_scope=None):
    output = private_output(output, root)
    revisions = private_output(output / 'revisions', root)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12]
    folder = revisions / stamp; folder.mkdir(mode=0o700)
    capabilities = probe(root)
    result = {'status': 'ok', 'project_sha256': project_hash, 'generation_dir': str(folder),
              'families': {}, 'host_changed': False, 'repository_changed': False, 'picked_used': False}
    write_json(folder / 'PROJECT.json', model)
    for family in FAMILIES:
        if family_scope is not None and family not in family_scope:
            continue
        capability = capabilities['families'][family]
        receipt = {'family': family, 'capability': capability, 'recipe': model['recipes'][family],
                   'native_measured': model.get('native_measured'), 'recipe_applied': False,
                   'status': 'not_implemented', 'reason': 'Receita registrada; tradução desta família ainda não implementada.'}
        if not capability['available']:
            receipt.update(status='unavailable', reason=capability.get('reason', 'Runtime indisponível.'))
        elif family == 'gtk2':
            try:
                from gtk2_generation import generate_scrollbar_snapshot
                api = SimpleNamespace(**{name: globals()[name] for name in (
                    'Unavailable', 'load_builder', 'DEFAULT_ROLES', 'ROLE_FAMILIES',
                    'selected_palette', 'native_roles', 'rgb_role', 'recipe_rules',
                    'sha', 'read_file', 'palette_inputs_current', 'write_json')})
                receipt.update(generate_scrollbar_snapshot(api, root, folder, model, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        elif family == 'gtk3':
            try:
                receipt.update(generate_gtk3(root, folder, model, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        elif family == 'gtk4':
            try:
                from gtk4_route import generate as generate_gtk4
                receipt.update(generate_gtk4(root, folder, model, project_hash, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        elif family == 'qt5':
            try:
                from qt5_scrollbar_route import generate as generate_qt5
                receipt.update(generate_qt5(root, folder, model, project_hash, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        elif family == 'qt6':
            try:
                from qt6_scrollbar_route import generate as generate_qt6
                receipt.update(generate_qt6(root, folder, model, project_hash, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        elif family == 'kvantum':
            try:
                from kvantum_route import generate as generate_kvantum
                receipt.update(generate_kvantum(root, folder, model, project_hash, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        elif family == 'plasma':
            try:
                from plasma_route import generate as generate_plasma
                receipt.update(generate_plasma(root, folder, model, project_hash, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        write_json(folder / (family + '-RECEIPT.json'), receipt)
        result['families'][family] = receipt
    selected_family = model['selected_family']
    if selected_family in result['families']:
        selected = result['families'][selected_family]
        if selected.get('status') == 'unavailable':
            result.update(status='unavailable', reason=selected.get(
                'reason', 'Runtime ou adaptador nativo indisponível.'))
        elif selected_family == 'gtk3' and not selected.get('recipe_applied'):
            result.update(status='unavailable', reason=selected.get('reason',
                          'GTK3 indisponível.'))
        elif selected_family in ('gtk2', 'gtk4', 'qt5', 'qt6', 'kvantum', 'plasma'):
            result.update(status=selected['status'], reason=selected.get('reason',
                          'Proposta parcial gerada; somente controles declarados no recibo são traduzidos.'))
    write_json(folder / 'RESULTADO.json', result)
    write_json(output / 'latest.json', {'generation_dir': str(folder), 'project_sha256': project_hash})
    return result


def scene_generation(root, output, applied, applied_hash):
    """Read only a generation bound to the normalized saved scene."""
    from proposal_export import model_digest
    index = output / 'latest.json'
    if not index.exists():
        return None
    record = json.loads(read_file(index))
    folder = Path(record.get('generation_dir', ''))
    if not folder.is_absolute() or not folder.is_relative_to(output / 'revisions'):
        raise ValueError('Geração base aponta para fora das revisões privadas.')
    private_output(folder, root)
    result = json.loads(read_file(folder / 'RESULTADO.json'))
    saved, _ = project(folder / 'PROJECT.json')
    if (record.get('project_sha256') != applied_hash or
            result.get('project_sha256') != applied_hash or
            model_digest(saved) != model_digest(applied) or
            result.get('generation_dir') != str(folder)):
        return None
    return result


def scene_palette_scope(root, output, applied, applied_hash):
    """Compare current inputs with the saved scene's generation, never exports."""
    translated = ('gtk2', 'gtk3', 'qt6')
    unknown = {family: {'status': 'unknown', 'reason':
               'Sem geração verificável da cena salva; regenerar a proposta.'}
               for family in translated}
    result = scene_generation(root, output, applied, applied_hash)
    if result is None:
        return list(translated), unknown
    affected, audit = [], {}
    for family in translated:
        receipt = result.get('families', {}).get(family, {})
        inputs = receipt.get('palette_inputs')
        if not isinstance(inputs, list) or not inputs or any(
                not isinstance(item, dict) or not isinstance(item.get('path'), str) or
                not isinstance(item.get('sha256'), str) for item in inputs):
            audit[family] = unknown[family]
            affected.append(family)
        elif palette_inputs_current(receipt):
            audit[family] = {'status': 'unchanged', 'inputs': inputs}
        else:
            audit[family] = {'status': 'changed', 'inputs': inputs,
                             'reason': 'Uma origem de paleta ou leitor mudou/desapareceu.'}
            affected.append(family)
    return affected, audit


def export_proposal(root, output, model, project_hash, kdeglobals, applied_path):
    from proposal_export import differences, affected_families, model_digest, replay_delta, review_text
    from artifact_delta import receipt_inventory, package_files
    if applied_path is None:
        raise ValueError('--applied-project obrigatório para comparar a proposta.')
    applied, applied_hash = project(applied_path)
    output = private_output(output, root)
    baseline = scene_generation(root, output, applied, applied_hash)
    external, palette_audit = scene_palette_scope(root, output, applied, applied_hash)
    families = sorted(set(affected_families(applied, model)) | set(external))
    result = generate(root, output / 'exports', model, project_hash, kdeglobals,
                      family_scope=families)
    for family, audit in palette_audit.items():
        if family not in families and audit['status'] == 'unchanged' and not palette_inputs_current(
                {'palette_inputs': audit['inputs']}):
            raise Unavailable('A paleta mudou durante a exportação; execute novamente.')
    comparison = {
        'schema': 1, 'kind': 'theme_lab_proposal_comparison',
        'proposal_sha256': project_hash, 'scene_snapshot_sha256': applied_hash,
        'changes': differences(applied, model),
        'scene_palette_comparison': palette_audit,
        'installed': False, 'live_preview_verified': False,
        'limitations': [
            'Comparação com a cena salva; não comprova pintura ou execução da prévia.',
            'Sem geração base verificável, a família exporta snapshot explícito; não inferir delta mínimo.'],
    }
    folder = Path(result['generation_dir'])
    write_json(folder / 'SCENE.json', applied)
    write_json(folder / 'COMPARISON.json', comparison)
    delta = {'schema': 1, 'kind': 'theme_lab_project_delta',
             'base_model_sha256': model_digest(applied),
             'proposal_model_sha256': model_digest(model),
             'changes': comparison['changes'], 'affected_families': families,
             'scene_palette_comparison': palette_audit,
             'rule_sources': {}}
    for family, receipt in result['families'].items():
        delta['rule_sources'][family] = receipt.get('sources', {})
    # The shared contract is provenance even when the family has no translator.
    contract = root / 'tools/domainos_scrollbar_rules.json'
    delta['shared_contract'] = {'path': 'tools/domainos_scrollbar_rules.json',
                                'sha256': sha(read_file(contract))}
    replay_delta(applied, delta)
    write_json(folder / 'DELTA.json', delta)
    package = folder / 'PACKAGE'
    package.mkdir(mode=0o700)
    packages = {}
    dependencies = {'schema': 1, 'kind': 'theme_lab_export_dependencies', 'families': {},
                    'installed': False, 'palette_policy':
                    'Snapshot dos papéis KDE; regenerar depois de mudar a origem efetiva.'}
    for family, receipt in result['families'].items():
        dependencies['families'][family] = {key: receipt[key] for key in (
            'engine', 'selected_scheme', 'palette_inputs', 'sources', 'limitations') if key in receipt}
        _, files = receipt_inventory(folder, receipt, read_file)
        if files is None:
            packages[family] = {'status': 'no_generated_files', 'reason': receipt.get('reason')}
            continue
        previous = None
        if baseline is not None:
            _, previous = receipt_inventory(Path(baseline['generation_dir']),
                baseline.get('families', {}).get(family, {}), read_file)
        manifest = package_files(previous, files, package / family)
        packages[family] = {'status': manifest['mode'],
                            'payload_files': len(manifest['payload']),
                            'reused_files': len(manifest['reuse']),
                            'removed_files': len(manifest['removed'])}
    write_json(package / 'DELTA.json', delta)
    write_json(package / 'COMPARISON.json', comparison)
    write_json(package / 'DEPENDENCIES.json', dependencies)
    result['artifact_packages'] = packages
    result['package_directory'] = str(package)
    result['affected_families'] = families
    result['comparison'] = comparison
    result['export_directory'] = str(folder)
    result['review_text'] = review_text(result)
    write_json(folder / 'RESULTADO.json', result)
    return result


def import_project_delta(root, output, model, project_hash, delta_path):
    from proposal_export import validate_delta, replay_delta, model_digest
    if delta_path is None:
        raise ValueError('--delta obrigatório para importar uma proposta.')
    payload = read_file(delta_path)
    delta = json.loads(payload)
    validate_delta(delta)
    candidate = replay_delta(model, delta)
    output = private_output(output, root)
    imports = private_output(output / 'imports', root)
    with tempfile.TemporaryDirectory(prefix='.validate-', dir=imports) as staging:
        staged = Path(staging) / 'PROJECT.json'
        write_json(staged, candidate)
        validated, _ = project(staged)
        if model_digest(validated) != delta['proposal_model_sha256']:
            raise ValueError('A proposta depende de defaults ausentes; reexporte o projeto validado.')
        folder = imports / ('revision-' + uuid.uuid4().hex)
        folder.mkdir(mode=0o700)
        project_path = folder / 'PROJECT.json'
        write_json(project_path, validated)
    result = {'status': 'ok', 'project_path': str(project_path),
              'base_project_sha256': project_hash, 'delta_sha256': sha(payload),
              'proposal_model_sha256': model_digest(validated),
              'host_changed': False, 'installed': False, 'preview_applied': False,
              'reason': 'Projeto reconstruído em pasta privada. Importe PROJECT.json na interface; Aplicar continua separado.'}
    write_json(folder / 'IMPORT.json', result)
    return result


def preview(root, output, model, project_hash, kdeglobals, family,
            private_test_close_ms=None, gtk2_trace_input=False, *,
            embed_window=None, host_pid=None, host_bridge=None,
            host_session_root=None):
    require_scroll_parts_adapter(model["recipes"][family], family)
    direct_family = family in ('qt5', 'qt6', 'kvantum', 'plasma')
    direct = direct_family and os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') != 'bwrap'
    if direct:
        output = private_output(output, root)
        from direct_preview_route import guard as direct_preview_guard
        try:
            guards = direct_preview_guard(root, output, family,
                embed_window=embed_window, host_pid=host_pid,
                host_bridge=host_bridge, host_session_root=host_session_root)
        except ValueError as error:
            raise Unavailable('Prévia nativa direta recusada: ' + str(error)) from error
    else:
        guards = private_namespace(root)  # Must pass BEFORE any GUI toolkit import.
        output = private_output(output, root)
    if family == 'gtk4':
        # Validate the renderer selected for this recipe. A button-only
        # preflight also rejects the already-supported GTK4 scrollbar route.
        from gtk4_route import renderer
        renderer(model)
    if family == 'gtk2':
        from native_scene_gtk2 import scene_records
        from gtk2_session import NativeSession
        bridge = NativeSession.pressure_bridge(root, model)
        scene_records(model, allow_button_pressed=bridge is not None)
    latest = output / 'latest.json'
    result = None
    if latest.is_file():
        record = json.loads(read_file(latest))
        folder = Path(record.get('generation_dir', ''))
        if not folder.is_relative_to(output / 'revisions'):
            raise ValueError('Recibo aponta para fora da saída privada.')
        private_output(folder, root)
        if record.get('project_sha256') == project_hash:
            result = json.loads(read_file(folder / 'RESULTADO.json'))
            # The index alone cannot prove that a cached receipt and its
            # serialized scene still belong to the current project.
            if (result.get('project_sha256') != project_hash or
                    result.get('generation_dir') != str(folder) or
                    json.loads(read_file(folder / 'PROJECT.json')) != model):
                result = None
        if result is not None:
            selected = result.get('families', {}).get(family, {})
            if (family in ('qt5', 'qt6', 'kvantum', 'plasma') and
                    selected.get('status') != 'partially_generated'):
                # An earlier unsupported/missing-runtime receipt is not a
                # snapshot and therefore has no route fields to verify.
                # Regenerate after capability or adapter changes.
                result = None
            if family == 'gtk2':
                from native_scene_gtk2 import scene_records
                controls = selected.get('translated_controls', [])
                if not isinstance(controls, list) or any(row['id'] not in controls for row in scene_records(model, allow_button_pressed=bridge is not None)):
                    result = None
                if result is not None and not generation_sources_current(selected, root):
                    result = None
            if ((family == 'gtk3' and selected.get('recipe_applied')) or
                    (family in ('gtk2','gtk4') and selected.get('status') == 'partially_generated')):
                if not palette_inputs_current(selected):
                    result = None
            if family == 'gtk4' and result is not None:
                from gtk4_route import verify as verify_gtk4
                verify_gtk4(root, selected, model)
            if family == 'qt5' and result is not None:
                from qt5_scrollbar_route import verify as verify_qt5
                verify_qt5(root, selected, model)
            if family == 'qt6' and result is not None:
                from qt6_scrollbar_route import verify as verify_qt6
                verify_qt6(root, selected, model)
            if family == 'kvantum' and result is not None:
                from kvantum_route import verify as verify_kvantum
                verify_kvantum(root, selected, model)
            if family == 'plasma' and result is not None:
                from plasma_route import verify as verify_plasma
                verify_plasma(root, selected, model)
    if result is None:
        # A native preview belongs to one selected family. Generating every
        # adapter here can make an unrelated runtime (for example Kvantum)
        # block a GTK2 preview and needlessly scans all toolkit capabilities.
        result = generate(root, output, model, project_hash, kdeglobals,
                          family_scope=[family])
    receipt = result['families'][family]
    capability = receipt['capability']
    if not capability['available'] or not capability['native_gallery']:
        raise Unavailable('Sem galeria nativa utilizável para ' + family + ': ' + capability.get('reason', ''))
    if family == 'gtk3' and not receipt.get('recipe_applied'):
        raise Unavailable('A receita GTK3 não foi gerada: ' + receipt.get('reason', ''))
    if family == 'gtk2' and receipt.get('status') != 'partially_generated':
        raise Unavailable('A receita parcial GTK2 não foi gerada: ' + receipt.get('reason', ''))
    if family == 'gtk4' and receipt.get('status') != 'partially_generated':
        raise Unavailable('A receita parcial GTK4 não foi gerada: ' + receipt.get('reason', ''))
    if family == 'qt5' and receipt.get('status') != 'partially_generated':
        raise Unavailable('A receita parcial Qt5 não foi gerada: ' + receipt.get('reason', ''))
    if family == 'qt6' and receipt.get('status') != 'partially_generated':
        raise Unavailable('A receita parcial Qt6 não foi gerada: ' + receipt.get('reason', ''))
    if family == 'kvantum' and receipt.get('status') != 'partially_generated':
        raise Unavailable('A receita Kvantum não foi gerada: ' + receipt.get('reason', ''))
    if family == 'plasma' and receipt.get('status') != 'partially_generated':
        raise Unavailable('A receita Plasma não foi gerada: ' + receipt.get('reason', ''))
    gallery = root / 'plasma/tests/galerias-nativas' / {'gtk2': 'gtk2_demo.py', 'gtk3': 'gtk3_demo.py', 'gtk4': 'gtk4_demo.py',
                 'qt5': 'qt5_demo.py', 'qt6': 'qt6_demo.py', 'kvantum': 'qt6_demo.py',
                 'plasma': 'plasma_style_demo.py'}[family]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if direct:
        from direct_preview_route import (environment as direct_preview_environment,
                                          seed_kde_profile)
        environment.update(direct_preview_environment(guards))
        if family in ('qt5', 'qt6'):
            guards['kde_profile'] = seed_kde_profile(guards, kdeglobals, receipt)
    if family == 'gtk3':
        environment['GTK_THEME'] = receipt['theme']
        environment['GTK_OVERLAY_SCROLLING'] = '0'
        environment['XDG_DATA_DIRS'] = str(Path(receipt['theme_path']).parents[1]) + ':' + environment.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share')
    command = ['/usr/bin/python3', '-B', str(gallery)]
    if family == 'gtk2':
        gallery = root / 'tools/theme-lab/preview_gtk2.py'
        events = private_output(Path(result['generation_dir']) / 'gtk2-preview-events', root)
        command = ['/usr/bin/python3', '-B', str(gallery), '--root', str(root),
                   '--project', str(Path(result['generation_dir']) / 'PROJECT.json'),
                   '--rc', receipt['rc'], '--events-dir', str(events)]
        if gtk2_trace_input:
            command.append('--trace-input')
    if family == 'gtk4':
        from gtk4_route import command as gtk4_command
        gallery = root / 'tools/theme-lab/preview_gtk4.py'
        events = private_output(Path(result['generation_dir']) / 'gtk4-preview-events', root)
        command = gtk4_command(root, receipt, model, events, kdeglobals)
    if family == 'qt5':
        from qt5_scrollbar_route import command as qt5_command
        command = qt5_command(root, receipt, model, private_test_close_ms,
            embed_window=embed_window, host_pid=host_pid, host_bridge=host_bridge,
            host_session_root=host_session_root)
    if family == 'qt6':
        from qt6_scrollbar_route import command as qt6_command
        command = qt6_command(root, receipt, model, private_test_close_ms,
            embed_window=embed_window, host_pid=host_pid, host_bridge=host_bridge,
            host_session_root=host_session_root)
    if family == 'kvantum':
        from kvantum_route import command as kvantum_command, environment as kvantum_environment
        direct_output = Path(guards['profile']['home']) / 'qtwidgets-proof' if direct else None
        command = kvantum_command(root, receipt, model,
            Path(receipt['snapshot']) / 'PROJECT.json', output=direct_output,
            embed_window=embed_window, host_pid=host_pid, host_bridge=host_bridge,
            host_session_root=host_session_root, test_close_ms=private_test_close_ms)
        environment.update(kvantum_environment(root, receipt, model))
    if family == 'plasma':
        from plasma_route import command as plasma_command, environment as plasma_environment
        direct_output = Path(guards['profile']['home']) / 'plasma-native-preview' if direct else None
        command = plasma_command(root, receipt, model,
            Path(receipt['snapshot']) / 'PROJECT.json', output=direct_output,
            embed_window=embed_window, host_pid=host_pid, host_bridge=host_bridge,
            host_session_root=host_session_root)
        environment.update(plasma_environment(root, receipt, model))
    folder = Path(result['generation_dir'])
    proof = {'status': 'starting', 'family': family,
             'recipe_applied': family in ('gtk3','plasma'),
             'theme_mode': 'private_recipe' if family == 'gtk3' else 'current_theme', 'guards': guards,
             'gallery': str(gallery), 'argv': command, 'namespace_created': False,
             'existing_coordinated_namespace': not direct,
             'direct_private_profile': direct, 'embedded': embed_window is not None,
             'project_sha256': project_hash,
             'selection': 'GTK_THEME child environment' if family == 'gtk3' else 'Existing private profile selection',
             'limitation': 'GTK_THEME selects painting; a gallery theme-name label can still report the XSettings name.' if family == 'gtk3' else 'Proposed recipe is not translated/applied for this family.'}
    if family == 'gtk2':
        proof.update(theme_mode='private_partial_recipe', recipe_scope='translated_controls',
                     translated_controls=receipt['translated_controls'],
                     preview_project_sha256=sha(read_file(folder / 'PROJECT.json')),
                     selection='Verified private GTK2 RC and PNG snapshot',
                     limitation='Only controls listed in translated_controls receive this recipe. The GTK2 theme remains partial; launch alone is not proof of rendering or historical fidelity.')
    if family == 'gtk4':
        proof.update(theme_mode='private_partial_recipe',
                     recipe_scope=', '.join(receipt['translated_controls']),
                     translated_controls=receipt['translated_controls'],
                     preview_project_sha256=receipt['preview_project_sha256'],
                     selection='Verified private GTK4 CSS and PNG snapshot',
                     limitation='Only controls listed in translated_controls receive this partial recipe. GTK4 does not expose native scrollbar stepper arrows; launch is not proof of rendering or historical fidelity.')
    if family == 'qt5':
        proof.update(theme_mode='private_partial_recipe',
                     recipe_scope=', '.join(receipt['translated_controls']),
                     translated_controls=receipt['translated_controls'],
                     preview_project_sha256=receipt['preview_project_sha256'],
                     selection='Verified Qt5 Widgets QSS and KDE-role-derived assets',
                     limitation='All 16 controls in the lab catalog have declared Qt5 Widgets translations; Qt retains native interaction and value semantics. Launch and pixel tests do not prove historical SR10.4 fidelity or human visual approval.')
    if family == 'qt6':
        proof.update(theme_mode='private_partial_recipe',
                     recipe_scope=', '.join(receipt['translated_controls']),
                     translated_controls=receipt['translated_controls'],
                     preview_project_sha256=receipt['preview_project_sha256'],
                     selection='Verified Qt6 Widgets QSS and KDE-role-derived assets',
                     limitation='Only controls listed in translated_controls receive this partial recipe; Qt retains native interaction and value semantics. Launch is not proof of historical fidelity.')
    if family == 'kvantum':
        proof.update(theme_mode='private_real_kvantum_recipe', recipe_scope='scroll_h/scroll_v',
                     translated_controls=receipt['translated_controls'],
                     recipe_sha256=receipt['recipe_sha256'],
                     selection='Generated SVG/config loaded by the real Kvantum QStyle',
                     limitation='Only the declared scrollbar controls use this generated theme. The native Qt preview must confirm Kvantum loaded; launch alone is not proof of historical fidelity.')
    if family == 'plasma':
        proof.update(theme_mode='private_plasma_desktoptheme_recipe', recipe_scope='scroll_h/scroll_v',
                     translated_controls=receipt['translated_controls'],
                     recipe_sha256=receipt['recipe_sha256'],
                     selection='Private desktop theme selected through plasmarc and KSvg.ImageSet',
                     limitation='Uses direct real Plasma Components.ScrollBar + KSvg at 1:1. Plasma has no native stepper arrows or separate 4px viewport gap; launch is not proof of historical fidelity.')
    log_path = folder / (family + '-preview-' + uuid.uuid4().hex[:8] + '.log')
    with log_path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
        proof.update(status='launched', pid=process.pid, log=str(log_path))
        write_json(folder / (family + '-PREVIEW.json'), proof)
        print(json.dumps(proof, ensure_ascii=False), flush=True)
        try:
            code = process.wait()
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(3)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
    proof.update(status='closed' if code == 0 else 'failed', exit_code=code)
    write_json(folder / (family + '-PREVIEW.json'), proof)
    return proof


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for command in ('probe', 'palette', 'schemes', 'snippet', 'generate', 'export', 'import-delta', 'inspect-files', 'reconstruct-files', 'preview'):
        mode.add_argument('--' + command, action='store_true')
    parser.add_argument('--project', type=Path)
    parser.add_argument('--applied-project', type=Path)
    parser.add_argument('--delta', type=Path)
    parser.add_argument('--file-delta', type=Path)
    parser.add_argument('--base-directory', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--kdeglobals', type=Path)
    parser.add_argument('--family', choices=FAMILIES)
    parser.add_argument('--control', choices=CONTROLS,
                        help='Controle do trecho; omitido usa recipe.selected_control.')
    parser.add_argument('--recipe-state', choices=EDIT_STATES + ('hover', 'focus'),
                        help='Estado inspecionado no trecho; não altera receita nem prévia.')
    parser.add_argument('--private-test-close-ms', type=int,
                        help='Fecha automaticamente somente uma prévia Qt5/Qt6/Kvantum privada; uso do teste nativo.')
    parser.add_argument('--gtk2-trace-input', action='store_true',
                        help='Ativa rastreamento de sinais de entrada somente na prévia privada GTK2.')
    parser.add_argument('--embed-window', type=lambda value: int(value, 0),
                        help='Canvas X11 marcado do Theme Lab para acoplar Qt/Plasma nativos.')
    parser.add_argument('--host-pid', type=int)
    parser.add_argument('--host-bridge', type=Path)
    parser.add_argument('--host-session-root', type=Path)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        model, project_hash = project(args.project) if args.project else (None, None)
        kdeglobals = kdeglobals_path(args.kdeglobals)
        if args.probe:
            result = probe(root)
        elif args.schemes:
            result = schemes(root, kdeglobals)
        elif args.palette:
            result = palette_values(model, kdeglobals, root, args.family)
        elif args.snippet:
            if model is None:
                raise ValueError('--project obrigatório para mostrar o trecho selecionado.')
            result = snippet(root, model, args.family, args.control, args.recipe_state, kdeglobals)
        elif args.inspect_files:
            from artifact_reconstruction import inspect_files
            result = inspect_files(args.file_delta, read_file)
        elif args.reconstruct_files:
            from artifact_reconstruction import reconstruct
            result = reconstruct(args.file_delta, args.base_directory, args.output,
                                 read_file, write_json)
        else:
            if model is None or args.output is None:
                raise ValueError('--project e --output obrigatórios para gerar/abrir prévia.')
            if args.import_delta:
                result = import_project_delta(root, args.output, model, project_hash, args.delta)
            elif args.export:
                result = export_proposal(root, args.output, model, project_hash,
                                         kdeglobals, args.applied_project)
            elif args.generate:
                result = generate(root, args.output, model, project_hash, kdeglobals)
            else:
                if not args.family:
                    raise ValueError('--family obrigatório para abrir prévia.')
                if args.private_test_close_ms is not None and (
                        args.family not in ('qt5', 'qt6', 'kvantum') or
                        not 1500 <= args.private_test_close_ms <= 120000):
                    raise ValueError('--private-test-close-ms é exclusivo de Qt5/Qt6/Kvantum e deve estar entre 1500 e 120000.')
                if args.gtk2_trace_input and args.family != 'gtk2':
                    raise ValueError('--gtk2-trace-input é exclusivo da prévia GTK2.')
                result = preview(root, args.output, model, project_hash, kdeglobals,
                                 args.family, args.private_test_close_ms,
                                 args.gtk2_trace_input,
                                 embed_window=args.embed_window,
                                 host_pid=args.host_pid,
                                 host_bridge=args.host_bridge,
                                 host_session_root=args.host_session_root)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0 if result.get('status') not in ('unavailable', 'failed', 'error') else 2
    except (OSError, ValueError, RuntimeError, ImportError, configparser.Error, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'unavailable' if isinstance(error, Unavailable) else 'error',
                          'available': False, 'reason': str(error), 'host_changed': False}, ensure_ascii=False), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
