#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Update modern Irixium with preflight, a private journal and explicit activation."""
from __future__ import annotations
import argparse
import configparser
import glob
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from theme_transaction import Change, Failure, Transaction, no_links, snapshot, decode, sha, edit_ini
from system_theme_writer import allowed as allowed_system

REPO = Path(__file__).resolve().parent.parent

def data_dir(name: str, default: Path) -> Path:
    path = Path(os.environ.get(name, str(default))).expanduser()
    no_links(path)
    return path

def verify_manifest(bundle: Path):
    no_links(bundle / 'MANIFEST.json')
    manifest = json.loads((bundle / 'MANIFEST.json').read_text('utf-8'))
    files = manifest.get('files', {})
    if manifest.get('version') != '1.0.0-rc1' or 'AuroraeButtonGroup.qml' not in files:
        raise Failure('Manifesto de geometria incompatível.')
    for rel, value in files.items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise Failure('Manifesto com caminho inválido.')
        path = bundle / rel; no_links(path)
        if not path.is_file() or sha(path.read_bytes()) != value:
            raise Failure('Integridade da geometria divergente: ' + rel)

def layout_module(repo: Path):
    path = repo / 'moderno/geometria/tools/layout.py'
    spec = importlib.util.spec_from_file_location('irixium_layout', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def discover(name: str, explicit: str | None = None) -> Path:
    if explicit:
        matches = [Path(explicit).expanduser().absolute() / name]
    else:
        patterns = ['/usr/lib/*/qt6/qml/org/kde/kwin/decoration/' + name,
                    '/usr/lib/qt6/qml/org/kde/kwin/decoration/' + name,
                    '/usr/lib64/qt6/qml/org/kde/kwin/decoration/' + name]
        if name == 'AuroraeButtonGroup.qml':
            patterns.append('/usr/share/kwin/aurorae/' + name)
        matches = list(dict.fromkeys(Path(p) for pattern in patterns for p in glob.glob(pattern)))
    if len(matches) != 1 or not matches[0].is_file() or not allowed_system(matches[0]):
        raise Failure(f'Não foi encontrado um único {name} do Qt 6. Use --qml-dir/--menu-dir.')
    no_links(matches[0]); return matches[0]

def system_writer(entries: list[dict]):
    launcher = shutil.which('pkexec') or shutil.which('sudo')
    python = Path('/usr/bin/python3')
    if not launcher or not python.is_file():
        raise Failure('Python 3 do sistema e pkexec ou sudo são necessários.')
    with tempfile.TemporaryDirectory(prefix='irixium-system-') as tmp:
        job = Path(tmp) / 'job.json'
        job.write_text(json.dumps(entries), encoding='utf-8')
        job.chmod(0o600)
        result = subprocess.run([launcher, str(python), str(REPO / 'tools/system_theme_writer.py'), str(job)], check=False)
    if result.returncode:
        raise Failure('Autorização cancelada ou falha na escrita do sistema; código ' + str(result.returncode))

def install_plan(repo: Path, user_theme: Path, config: Path, group: Path, menu: Path,
                 asset: Path, activate: bool, fonts: bool) -> list[Change]:
    bundle = repo / 'moderno/geometria'
    verify_manifest(bundle)
    layout = layout_module(repo)
    normalize = lambda data: b'\n'.join(line.rstrip() for line in data.splitlines() if line.strip())
    artwork = repo / 'aurorae/Irixium'
    required = ['Irixiumrc', 'decoration.svg', 'minimize.svg', 'maximize.svg',
                'restore.svg', 'close.svg', 'applications.png', 'metadata.desktop']
    for name in required:
        path = artwork / name; no_links(path)
        if not path.is_file():
            raise Failure('Arquivo obrigatório ausente: aurorae/Irixium/' + name)
    for path in artwork.rglob('*'):
        no_links(path)
        if path.is_file() and path.suffix == '.svg':
            if b'<!ENTITY' in path.read_bytes() or b'<!DOCTYPE' in path.read_bytes():
                raise Failure('SVG com entidades externas recusado.')
            ET.fromstring(path.read_bytes())
    expected_group = snapshot(group)
    if not expected_group['exists']:
        raise Failure('Componente Aurorae não encontrado.')
    known = [p.read_bytes() for p in (bundle / 'compatibilidade').glob('*.qml')]
    new_group = (bundle / 'AuroraeButtonGroup.qml').read_bytes()
    if normalize(decode(expected_group)) not in [normalize(data) for data in known + [new_group]]:
        raise Failure('O grupo Aurorae instalado tem código desconhecido; não será substituído.')
    current_rc = snapshot(user_theme / 'Irixiumrc')
    rc_bytes = decode(current_rc) if current_rc['exists'] else (artwork / 'Irixiumrc').read_bytes()
    new_rc = layout.update_layout(rc_bytes)  # preserves local colors and other keys
    changes = []
    for path in sorted(artwork.rglob('*')):
        if not path.is_file():
            continue
        target = user_theme / path.relative_to(artwork)
        old = snapshot(target)
        data = new_rc if path.name == 'Irixiumrc' else path.read_bytes()
        changes.append(Change(target, data, 0, old.get('mode', 0o644),
                              current_rc if path.name == 'Irixiumrc' else old))
    # Only the reviewed modern/geometria source is used. Never the root legacy overlay.
    changes.append(Change(group, new_group, 1, 0o644, expected_group))
    menu_bytes = (repo / 'MenuButton.qml').read_bytes()
    if b'org.kde.kwin.decoration' not in menu_bytes or b'isIrixium' not in menu_bytes:
        raise Failure('Componente de menu incompleto ou sem delimitação do tema.')
    png = (artwork / 'applications.png').read_bytes()
    if not png.startswith(b'\x89PNG\r\n\x1a\n'):
        raise Failure('Imagem de menu inválida.')
    changes.extend([Change(menu, menu_bytes, 1, 0o644, snapshot(menu)),
                    Change(asset, png, 1, 0o644, snapshot(asset))])
    if activate:
        path = config / 'kwinrc'; before = snapshot(path)
        values = {'library': 'org.kde.kwin.aurorae', 'theme': '__aurorae__svg__Irixium'}
        src = configparser.ConfigParser(interpolation=None); src.optionxform = str
        src.read_string((repo / 'kwin-decoration.conf').read_text('utf-8'))
        for key in ('BorderSize', 'ButtonsOnLeft', 'ButtonsOnRight'):
            values[key] = src['org.kde.kdecoration2'][key]
        changes.append(Change(path, edit_ini(decode(before) or b'', 'org.kde.kdecoration2', values),
                              2, before.get('mode', 0o600), before))
    if fonts:
        path = config / 'kdeglobals'; before = snapshot(path)
        values = configparser.ConfigParser(interpolation=None); values.optionxform = str
        values.read_string((repo / 'kde-fonts.conf').read_text('utf-8'))
        data = decode(before) or b''
        allowed = {'General': {'font','fixed','smallestReadableFont','toolBarFont','menuFont','XftAntialias','XftSubPixel'}, 'WM': {'activeFont'}}
        for section in values.sections():
            if section not in allowed or not set(values[section]).issubset(allowed[section]):
                raise Failure('Perfil de fontes tem chaves não esperadas.')
            data = edit_ini(data, section, dict(values[section]))
        changes.append(Change(path, data, 2, before.get('mode', 0o600), before))
    return changes

def notify():
    qdbus = shutil.which('qdbus6')
    if qdbus:
        result = subprocess.run([qdbus, 'org.kde.KWin', '/KWin', 'reconfigure'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode:
            print('Aviso: reconfigure indisponível. Os arquivos foram instalados; entre novamente na sessão.')
    print('Salve o trabalho, encerre a sessão e entre novamente para recarregar o QML. Nenhuma sessão foi encerrada.')

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--ativar', action='store_true', help='selecionar Irixium e a disposição declarada pelo repositório')
    parser.add_argument('--aplicar-fontes', action='store_true', help='reaplicar explicitamente o perfil de fontes do repositório')
    parser.add_argument('--restaurar', action='store_true')
    parser.add_argument('--recuperar', action='store_true')
    parser.add_argument('--qml-dir'); parser.add_argument('--menu-dir')
    args = parser.parse_args(argv)
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    if args.recuperar and not args.restaurar:
        raise Failure('--recuperar exige --restaurar.')
    if args.restaurar and (args.ativar or args.aplicar_fontes):
        raise Failure('Ativação/fontes não se aplicam à restauração.')
    home = Path.home()
    data = data_dir('XDG_DATA_HOME', home / '.local/share')
    config = data_dir('XDG_CONFIG_HOME', home / '.config')
    state_root = data_dir('XDG_STATE_HOME', home / '.local/state')
    theme = data / 'aurorae/themes/Irixium'
    def allowed(path, phase):
        if phase == 1:
            return allowed_system(path)
        if phase == 2:
            return path in (config / 'kwinrc', config / 'kdeglobals')
        return theme in path.parents
    tx = Transaction(state_root / 'irixium-update', system_writer, allowed)
    def run():
        if args.restaurar:
            tx.restore(args.recuperar, args.verificar)
        else:
            # A standalone geometry recovery must be resolved first, not overwritten.
            pointer = state_root / 'irixium-moderno-geometria/latest'
            no_links(pointer)
            if pointer.is_file():
                token = pointer.read_text().strip()
                if not token or '/' in token or '..' in token:
                    raise Failure('Referência de backup de geometria inválida.')
                receipt = pointer.parent / 'backups' / token / 'receipt.json'; no_links(receipt)
                if json.loads(receipt.read_text())['status'] in ('prepared', 'recovery_needed'):
                    raise Failure('Recupere primeiro a transação pendente de moderno/geometria.')
            if not (shutil.which('pkexec') or shutil.which('sudo')):
                raise Failure('pkexec ou sudo não encontrado.')
            group = discover('AuroraeButtonGroup.qml', args.qml_dir)
            menu = discover('MenuButton.qml', args.menu_dir)
            print('Tema moderno:', theme)
            print('Seleção e fontes:', 'alteração explícita' if args.ativar or args.aplicar_fontes else 'preservadas')
            plan = install_plan(REPO, theme, config, group, menu,
                                Path('/usr/share/kwin/aurorae/Irixium/applications.png'), args.ativar, args.aplicar_fontes)
            tx.install(plan, args.verificar)
        if not args.verificar:
            notify()  # only AFTER all files, hashes and the receipt are committed
    if args.verificar:
        run()
    else:
        # Cooperate with the standalone geometry updater without modifying its receipts.
        geo_lock = state_root / 'irixium-moderno-geometria'
        with tx.locked(), Transaction(geo_lock, system_writer, allowed).locked():
            run()
    return 0

if __name__ == '__main__':
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Sinal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    try:
        sys.exit(main())
    except (Failure, OSError, ValueError, KeyError, TypeError, configparser.Error, ET.ParseError) as exc:
        print('ERRO:', exc, file=sys.stderr); sys.exit(1)
    except KeyboardInterrupt:
        print('Interrompido. Verifique o recibo antes de repetir.', file=sys.stderr); sys.exit(130)
