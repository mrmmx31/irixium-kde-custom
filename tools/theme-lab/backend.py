#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private recipe generation and native-gallery controller for Theme Lab.

No theme is installed, no personal profile is written, and sampled RGB is never
used as a final control colour. Only GTK3 currently translates a proposed recipe.
Other families keep an honest capability/recipe record and, when available, use
the existing native gallery with its current theme. GUI launch requires the
already coordinated bwrap/Xephyr namespace and preserves the gallery guards.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
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
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True
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


def project(path):
    payload = read_file(path)
    result = json.loads(payload)
    if not isinstance(result, dict) or result.get('schema_version') != 1 or result.get('kind') != 'theme_lab_project':
        raise ValueError('Projeto Theme Lab schema_version=1 esperado.')
    if result.get('selected_family') not in FAMILIES:
        raise ValueError('Família selecionada inválida.')
    result.setdefault('color_scheme', '')
    if not portable_scheme(result['color_scheme']):
        raise ValueError('Use um ID portátil de esquema, sem caminhos.')
    recipes = result.get('recipes')
    if not isinstance(recipes, dict) or set(recipes) != set(FAMILIES):
        raise ValueError('As dez receitas precisam estar presentes no projeto.')
    for family, recipe in recipes.items():
        if not isinstance(recipe, dict):
            raise ValueError('Receita inválida: ' + family)
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
        if not isinstance(recipe.get('notes', ''), str):
            raise ValueError('Nota da receita precisa ser texto.')
        for key, default, upper in (('visible_categories', 31, 31), ('visible_controls', 65535, 65535),
                                    ('selected_control', 0, 15), ('edit_state', 0, 3)):
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
    return {'status': 'ok', 'available': True, 'rgb16': [[channel * 257 for channel in color] for color in values],
            'rgb8': [list(color) for color in values], 'order': ['face', 'text', 'view', 'selection', 'light', 'shadow'],
            'origin': origin, 'roles': {key: rules[key] for key in DEFAULT_ROLES},
            'factors': {key: rules[key] for key in FACTORS}, 'picked_used': False,
            'selection_scope': 'Lab controls only; no global KDE scheme selected',
            'effective_gtk_states_exported': False, 'host_changed': False,
            'private_kde_profile_changed': False}


def python_probe(code):
    interpreter = '/usr/bin/python3' if Path('/usr/bin/python3').is_file() else sys.executable
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([interpreter, '-B', '-c', code], capture_output=True, text=True, env=environment, timeout=10)
    if result.returncode:
        return {'available': False, 'reason': result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'Importação indisponível.'}
    return json.loads(result.stdout)


def package_version(name):
    if not shutil.which('dpkg-query'):
        return None
    result = subprocess.run(['dpkg-query', '-W', '-f=${Version}', name], capture_output=True, text=True, timeout=3)
    return (result.stdout.strip() or None) if result.returncode == 0 else None


def probe(root):
    families = {}
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
        code += 'print(json.dumps({"available":True,"version":".".join(map(str,values)),"gtk_initialized":False}))\n'
        families[family] = python_probe(code)
    # The repository's GTK4 gallery uses the installed C ABI; absence of its
    # GIR package does not mean that the runtime or native gallery is absent.
    gtk4_gallery = root / 'plasma/tests/galerias-nativas/gtk4_demo.py'
    if gtk4_gallery.is_file():
        check = subprocess.run(['/usr/bin/python3', '-B', str(gtk4_gallery), '--verificar'],
                               capture_output=True, text=True, timeout=10)
        if check.returncode == 0:
            families['gtk4'] = dict(json.loads(check.stdout), available=True, binding='C_ABI')
        else:
            families['gtk4'] = {'available': False, 'reason': check.stderr.strip().splitlines()[-1] if check.stderr.strip() else 'Galeria C ABI indisponível.'}
    else:
        families['gtk4'] = {'available': False, 'reason': 'Galeria GTK4 C ABI ausente.'}
    for family, module in (('qt5', 'PyQt5'), ('qt6', 'PyQt6')):
        families[family] = python_probe(f'from {module}.QtCore import qVersion\nimport json\nprint(json.dumps({{"available":True,"version":qVersion(),"application_initialized":False}}))')
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
                           'reason': 'Galeria Qt6 real; adaptar receita Kvantum permanece pendente.'}
    quick = python_probe('from PyQt6.QtCore import qVersion\nfrom PyQt6.QtQml import QQmlApplicationEngine\nimport json\nprint(json.dumps({"available":True,"version":qVersion(),"application_initialized":False}))')
    families['plasma'] = dict(quick, plasmashell=shutil.which('plasmashell'),
                             preview_kind='qtquick6_current_theme',
                             reason='Qt Quick6/KDE real; esta galeria não aplica nem valida os SVGs do Plasma Style.')
    if not families['plasma']['plasmashell']:
        families['plasma'].update(available=False, reason='Plasma não instalado; disponibilidade Qt Quick isolada não equivale a Plasma Style.')
    for family in FAMILIES:
        item = families[family]
        item['adapter'] = 'gtk3_private_recipe' if family == 'gtk3' else 'not_implemented'
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


def private_output(path, root):
    path = Path(path).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Saída privada não pode atravessar links ou ..')
    in_tmp = path.is_relative_to(Path(tempfile.gettempdir())) and path != Path(tempfile.gettempdir())
    in_lab = (path.is_relative_to(root) and path != root
              and path.relative_to(root).parts[0].startswith('.qa-'))
    in_namespace = (os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') == 'bwrap'
                    and path.is_relative_to(Path('/home/domainos-test')) and path != Path('/home/domainos-test'))
    if not (in_tmp or in_lab or in_namespace):
        raise ValueError('Escolha saída privada em /tmp, em .qa-* do projeto ou no HOME do namespace.')
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


def mask_metadata(builder, geometry):
    """Same symbolic slices as masks(), without writing any SVG or manifest."""
    entries = {}
    for name, (pixels, family, border) in (builder.art.assets() | builder.gtk3_assets(geometry=geometry)).items():
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
        # The lab's standalone arrow is a real, compact GtkButton. Reuse the
        # generated triangle at its intrinsic pixel size; do not enlarge the
        # default GtkArrow renderer or change a canonical toolkit selector.
        # Its colours belong to the recipe's standalone Button family. Sharing
        # triangle geometry does not establish the scrollbar container's
        # colour context or visual equivalence with the VM's Trash Can.
        for state, suffix in ((0, ''), (1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
            expression = builder.state_css('button', state)
            for pressed in (False, True):
                mode = 'disabled' if state & 2 else 'pressed' if pressed else 'normal'
                properties = builder.adaptive_assets.expression(
                    'gtk3-stepper-down-' + mode, expression, prefix='adaptive/', manifest=manifest)
                properties.update({'min-width': str(geometry['arrow_px']) + 'px',
                                   'min-height': str(geometry['arrow_px']) + 'px',
                                   'padding': '0', 'margin': '0',
                                   'border-width': str(geometry['shadow_px']) + 'px',
                                   'border-style': 'solid', 'border-image-source': 'none',
                                   'color': expression('ink'), 'background-color': expression('face')})
                overrides += builder.rule('button.theme-lab-arrow' + (':active' if pressed else '') + suffix,
                                          properties)
    return common, overrides


def control_selector(selector, control):
    if control == 'arrow':
        return (selector.startswith('button.theme-lab-arrow') or
                bool(re.fullmatch(r'button(?::(?:active|backdrop|disabled))*', selector)))
    if 'theme-lab-arrow' in selector:
        return False
    roots = {'push': r'(?:button|\.button)', 'toggle': r'(?:button|\.button)',
             'check': 'check', 'radio': 'radio', 'entry': 'entry',
             'combo': r'(?:combobox|button|\.button)', 'spin': r'(?:spinbutton|button|\.button)',
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


def state_selector(selector, state):
    # Endpoint-disabled children remain a normal/backdrop parent's colour
    # dependency. Do not classify :not(:disabled) as a disabled parent.
    boundary = ':not(:disabled)' in selector and ' button.' in selector
    tested = re.sub(r':not\([^)]*\)', '', selector)
    disabled, backdrop = ':disabled' in tested, ':backdrop' in tested
    if boundary:
        return state in ('normal', 'pressed', 'backdrop') and backdrop == (state == 'backdrop')
    if disabled:
        return state == 'disabled' and not backdrop
    if backdrop:
        return state == 'backdrop'
    active = ':active' in tested or ':checked' in tested or ':indeterminate' in tested
    return not active or state == 'pressed'


def snippet(root, model, family=None, control=None):
    """One selected control, named-role expressions and no final sampled RGB."""
    family = family or model['selected_family']
    recipe = model['recipes'][family]
    index = CONTROLS.index(control) if control else recipe.get('selected_control', 0)
    control, state = CONTROLS[index], EDIT_STATES[recipe.get('edit_state', 0)]
    positions = recipe.get('positions', [[16 + (i % 4)*160, 16 + (i // 4)*80] for i in range(16)])
    result = {'status': 'ok', 'family': family, 'control': control, 'selected_control': index,
              'state': state, 'position': positions[index], 'color_scheme': model.get('color_scheme', ''),
              'recipe_applied': False, 'picked_used': False, 'host_changed': False,
              'scope': 'Only the selected control; code inspection is not a native visual test.'}
    result['size_request'] = recipe.get('sizes', [[0, 0] for _ in range(16)])[index]
    if family != 'gtk3':
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
        manifest = mask_metadata(builder, geometry)
        common, overrides = gtk3_sources(builder, manifest, recipe, geometry)
        source = re.sub(r'/\*.*?\*/', '', common + overrides, flags=re.S)
        blocks = []
        for selectors, properties in re.findall(r'([^{}]+)\{([^{}]*)\}', source):
            kept = [item.strip() for item in selectors.strip().split(',')
                    if control_selector(item.strip(), control) and state_selector(item.strip(), state)]
            if kept:
                blocks.append(', '.join(kept) + ' {' + properties + '}\n')
        arrow_scope = (' * Seta independente: GtkButton; face: ' + recipe['palette']['face_role'] +
                       '; texto: ' + recipe['palette']['text_role'] + '.\n'
                       ' * Reutiliza geometria; não valida a composição/paleta da barra de rolagem ou do Trash Can.\n'
                       if control == 'arrow' else '')
        result.update(language='css', source_kind='gtk3_generated_css_subset',
                      source='/* GTK3: ' + control + ' / ' + state + '\n'
                             ' * Paleta: papéis KDE; amostra da pipeta não aplicada.\n'
                             + arrow_scope +
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
        colors, color_origin = exported_roles(kdeglobals.parent / 'gtk-3.0/colors.css', builder.art)
        kde_origin = selected_origin
        palette_inputs = [selected_origin, color_origin]
    # Detect an old exporter snapshot after a scheme change; allow only the
    # documented one-channel RGB8 rounding difference in native exports.
    for role, family in ROLE_FAMILIES.items():
        section = role.split('/', 1)[0]
        if not current.has_section(section):
            continue
        rgb = rgb_role(current, role)
        exported = builder.art._rgb(colors[builder.art.ROLES[family][0]])
        if any(abs(a - b) > 1 for a, b in zip(rgb, exported)):
            raise Unavailable('Exportação GTK ainda não corresponde à origem de paleta selecionada: ' + role)
    name = 'ThemeLab-GTK3-' + folder.name.rsplit('-', 1)[-1]
    theme = folder / 'data/themes' / name
    common = theme / 'common'; common.mkdir(parents=True, mode=0o700)
    with recipe_rules(builder, recipe['palette']):
        manifest = builder.masks(common / 'adaptive', geometry=geometry)
    css, overrides = gtk3_sources(builder, manifest, recipe, geometry)
    definitions = ''.join('@define-color ' + key + ' ' + value + ';\n' for key, value in sorted(colors.items()))
    (common / 'gtk.css').write_text(definitions + css, encoding='utf-8')
    (common / 'gtk-3.0-overrides.css').write_text(overrides, encoding='utf-8')
    (theme / 'gtk-3.0').mkdir(mode=0o700)
    (theme / 'gtk-3.0/gtk.css').write_text('@import url("../common/gtk.css");\n@import url("../common/gtk-3.0-overrides.css");\n', encoding='utf-8')
    (theme / 'gtk-3.0/gtk-dark.css').write_text('@import url("gtk.css");\n', encoding='utf-8')
    (theme / 'index.theme').write_text('[Desktop Entry]\nType=X-GNOME-Metatheme\nName=' + name + '\n\n[X-GNOME-Metatheme]\nGtkTheme=' + name + '\n', encoding='utf-8')
    shutil.copyfile(root / 'decorations/domainos/LICENSE', theme / 'LICENSE')
    sources = [root / 'gtk/tools/build_kde_domainos.py', root / 'tools/domainos_motif_art.py',
               root / 'gtk/tools/adaptive_assets.py', root / 'tools/domainos_scrollbar_rules.json']
    origin = {'status': 'generated', 'family': 'gtk3', 'theme': name, 'theme_path': str(theme),
              'recipe_applied': True, 'historical_fidelity_claimed': False, 'scope': 'Private generated GTK3 recipe only',
              'recipe': recipe, 'palette': color_origin, 'kdeglobals': kde_origin,
              'selected_scheme': selected_origin, 'palette_inputs': palette_inputs,
              'backend_sha256': sha(read_file(Path(__file__))),
              'source_consistency': 'Normal roles compared with selected source within RGB8 rounding 1; states supplied by native KColorScheme reader for selected scheme, or current GTKConfig export. No normal-RGB approximation.',
              'states': ['normal', 'pressed', 'backdrop', 'insensitive', 'insensitive_backdrop'],
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


def generate(root, output, model, project_hash, kdeglobals):
    output = private_output(output, root)
    revisions = private_output(output / 'revisions', root)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12]
    folder = revisions / stamp; folder.mkdir(mode=0o700)
    capabilities = probe(root)
    result = {'status': 'ok', 'project_sha256': project_hash, 'generation_dir': str(folder),
              'families': {}, 'host_changed': False, 'repository_changed': False, 'picked_used': False}
    write_json(folder / 'PROJECT.json', model)
    for family in FAMILIES:
        capability = capabilities['families'][family]
        receipt = {'family': family, 'capability': capability, 'recipe': model['recipes'][family],
                   'native_measured': model.get('native_measured'), 'recipe_applied': False,
                   'status': 'not_implemented', 'reason': 'Receita registrada; tradução desta família ainda não implementada.'}
        if not capability['available']:
            receipt.update(status='unavailable', reason=capability.get('reason', 'Runtime indisponível.'))
        elif family == 'gtk3':
            try:
                receipt.update(generate_gtk3(root, folder, model, kdeglobals))
            except (OSError, ValueError, ImportError) as error:
                receipt.update(status='unavailable', reason=str(error))
        write_json(folder / (family + '-RECEIPT.json'), receipt)
        result['families'][family] = receipt
    if model['selected_family'] == 'gtk3' and not result['families']['gtk3']['recipe_applied']:
        result.update(status='unavailable', reason=result['families']['gtk3'].get('reason', 'GTK3 indisponível.'))
    write_json(folder / 'RESULTADO.json', result)
    write_json(output / 'latest.json', {'generation_dir': str(folder), 'project_sha256': project_hash})
    return result


def preview(root, output, model, project_hash, kdeglobals, family):
    guards = private_namespace(root)  # Must pass BEFORE any GUI toolkit import.
    output = private_output(output, root)
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
            gtk3 = result.get('families', {}).get('gtk3', {})
            if family == 'gtk3' and gtk3.get('recipe_applied'):
                if not palette_inputs_current(gtk3):
                    result = None
    if result is None:
        result = generate(root, output, model, project_hash, kdeglobals)
    receipt = result['families'][family]
    capability = receipt['capability']
    if not capability['available'] or not capability['native_gallery']:
        raise Unavailable('Sem galeria nativa utilizável para ' + family + ': ' + capability.get('reason', ''))
    if family == 'gtk3' and not receipt.get('recipe_applied'):
        raise Unavailable('A receita GTK3 não foi gerada: ' + receipt.get('reason', ''))
    gallery = root / 'plasma/tests/galerias-nativas' / {'gtk2': 'gtk2_demo.py', 'gtk3': 'gtk3_demo.py', 'gtk4': 'gtk4_demo.py',
                 'qt5': 'qt5_demo.py', 'qt6': 'qt6_demo.py', 'kvantum': 'qt6_demo.py', 'plasma': 'qtquick_demo.py'}[family]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if family == 'gtk3':
        environment['GTK_THEME'] = receipt['theme']
        environment['GTK_OVERLAY_SCROLLING'] = '0'
        environment['XDG_DATA_DIRS'] = str(Path(receipt['theme_path']).parents[1]) + ':' + environment.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share')
    command = ['/usr/bin/python3', '-B', str(gallery)]
    if family == 'plasma':
        command += ['--qt-major', '6']
    folder = Path(result['generation_dir'])
    proof = {'status': 'starting', 'family': family, 'recipe_applied': family == 'gtk3',
             'theme_mode': 'private_recipe' if family == 'gtk3' else 'current_theme', 'guards': guards,
             'gallery': str(gallery), 'argv': command, 'namespace_created': False,
             'existing_coordinated_namespace': True, 'project_sha256': project_hash,
             'selection': 'GTK_THEME child environment' if family == 'gtk3' else 'Existing private profile selection',
             'limitation': 'GTK_THEME selects painting; a gallery theme-name label can still report the XSettings name.' if family == 'gtk3' else 'Proposed recipe is not translated/applied for this family.'}
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
    for command in ('probe', 'palette', 'schemes', 'snippet', 'generate', 'preview'):
        mode.add_argument('--' + command, action='store_true')
    parser.add_argument('--project', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--kdeglobals', type=Path)
    parser.add_argument('--family', choices=FAMILIES)
    parser.add_argument('--control', choices=CONTROLS,
                        help='Controle do trecho; omitido usa recipe.selected_control.')
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
            result = snippet(root, model, args.family, args.control)
        else:
            if model is None or args.output is None:
                raise ValueError('--project e --output obrigatórios para gerar/abrir prévia.')
            if args.generate:
                result = generate(root, args.output, model, project_hash, kdeglobals)
            else:
                if not args.family:
                    raise ValueError('--family obrigatório para abrir prévia.')
                result = preview(root, args.output, model, project_hash, kdeglobals, args.family)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0 if result.get('status') not in ('unavailable', 'failed', 'error') else 2
    except (OSError, ValueError, RuntimeError, ImportError, configparser.Error, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'unavailable' if isinstance(error, Unavailable) else 'error',
                          'available': False, 'reason': str(error), 'host_changed': False}, ensure_ascii=False), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
