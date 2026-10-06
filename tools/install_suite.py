#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install both complete themes, offline, only for the invoking user."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from theme_transaction import Failure, no_links
from user_bundle import Bundle

ROOT = Path(__file__).resolve().parents[1]


def roots():
    home = Path.home()
    paths = [Path(os.environ.get(key) or home/default).expanduser() for key, default in (
        ('XDG_DATA_HOME', '.local/share'), ('XDG_CONFIG_HOME', '.config'),
        ('XDG_STATE_HOME', '.local/state'))]
    for p in paths:
        no_links(p)
        # XDG overrides must not redirect a user install into a shared system root.
        if any(p == base or base in p.parents for base in map(Path, ('/usr','/etc','/opt','/var'))):
            raise Failure(f'Destino compartilhado recusado: {p}')
        existing = next(q for q in (p, *p.parents) if q.exists())
        if existing.stat().st_uid != os.getuid() and existing != Path('/tmp'):
            raise Failure(f'Destino não pertence ao usuário: {p}')
    return paths


def sources(data, config):
    pairs = [
        ('modern-rewrite-rc1/package', data/'kwin/decorations/irixium_modern'),
        ('classic-rewrite-rc1/package', data/'kwin/decorations/irixium_irix_classic_v4'),
        ('icons/Irixium', data/'icons/Irixium'),
        ('icons/themes/IrixClassic-SGI', data/'icons/IrixClassic-SGI'),
        ('cursors/sgi', data/'icons/sgi'),
        ('gtk', data/'themes/Irixium'),
        ('colors/Irixium.colors', data/'color-schemes/Irixium.colors'),
    ]
    for name in ('Irixium', 'IrixClassic'):
        pairs += [(f'plasma/{name}', data/f'plasma/desktoptheme/{name}'),
                  (f'wallpapers/{name}', data/f'wallpapers/{name}'),
                  (f'kvantum/{name}', config/f'Kvantum/{name}')]
    for name in ('irixium', 'irixclassic'):
        package = f'org.magpie.{name}.desktop'
        pairs.append((f'look-and-feel/{package}', data/f'plasma/look-and-feel/{package}'))
    return [(ROOT/source, dest) for source, dest in pairs]


def refresh_icons(data):
    # GTK cache belongs to a specific theme. KDE also watches the top-level mtime.
    cache_tool = shutil.which('gtk-update-icon-cache')
    for name in ('Irixium', 'IrixClassic-SGI'):
        theme = data/'icons'/name
        if not theme.is_dir():
            continue
        os.utime(theme, None)
        if cache_tool:
            result = subprocess.run([cache_tool, '-f', '-t', str(theme)], capture_output=True, text=True)
            if result.returncode:
                print(f'Aviso: cache GTK de {name}: {result.stderr.strip()}')
    tool = shutil.which('kbuildsycoca6')
    if tool:
        result = subprocess.run([tool, '--noincremental'], capture_output=True, text=True)
        if result.returncode:
            print('Aviso: cache KDE não atualizado nesta sessão; entre novamente para recarregar.')

    # KIconLoader listens on the current user's session bus. This invalidates
    # existing loaders even when the selected theme name has not changed.
    signal = shutil.which('dbus-send')
    if signal and os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        for group in range(6):  # Desktop, Toolbar, MainToolbar, Small, Panel, Dialog
            result = subprocess.run([signal, '--session', '--type=signal', '/KIconLoader',
                'org.kde.KIconLoader.iconChanged', f'int32:{group}'], capture_output=True, text=True)
            if result.returncode:
                print('Aviso: aplicativos não receberam atualização de ícones; reabra-os.')
                break


def check_runtime():
    missing = [name for name in ('plasma-apply-lookandfeel', 'kreadconfig6', 'qtpaths6')
               if not shutil.which(name)]
    if not missing:
        def query(name):
            return Path(subprocess.check_output(['qtpaths6','--query',name],text=True).strip())
        qml = query('QT_INSTALL_QML')
        plugins = query('QT_INSTALL_PLUGINS')
        for path, label in [(qml/'org/kde/kwin/decoration/qmldir','Aurorae Qt 6'),
                            (qml/'org/kde/ksvg/qmldir','KSvg QML Qt 6'),
                            (plugins/'styles/libkvantum.so','Kvantum Qt 6')]:
            if not path.is_file():
                missing.append(label)
    if missing:
        raise Failure('Dependências de execução ausentes: '+', '.join(missing)+
                      '. Instale os pacotes da sua distribuição antes de continuar. Nenhum pacote de sistema foi alterado.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--restaurar', action='store_true')
    parser.add_argument('--sem-cache', action='store_true', help='para testes sem sessão gráfica')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    data, config, state = roots()
    if not args.restaurar:
        check_runtime()
    pairs = sources(data, config)
    bundle = Bundle(state/'irixium-suite', [dest for _, dest in pairs])
    if args.restaurar:
        if args.verificar:
            bundle.restore(dry=True)
        else:
            with bundle.locked():
                bundle.restore()
            if not args.sem_cache:
                refresh_icons(data)
        return
    sys.path.insert(0, str(ROOT/'icons/tools'))
    from icon_common import audit
    for source in (ROOT/'icons/Irixium', ROOT/'icons/themes/IrixClassic-SGI'):
        report = audit(source)
        if report['errors']:
            raise Failure(f'Ícones inválidos em {source}: {report["errors"]} erro(s). Execute icons/tools/validate_theme.py.')
    # Stage metadata with the same ID used by the global theme. Preserve only
    # known appearance settings, not old QML implementations or interaction delays.
    spec = importlib.util.spec_from_file_location('classic_manager', ROOT/'classic-rewrite-rc1/tools/manage.py')
    classic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(classic)
    from user_bundle import fingerprint
    for folder in ('classic-rewrite-rc1', 'modern-rewrite-rc1'):
        expected = json.loads((ROOT/folder/'MANIFEST.json').read_text())['package']
        if fingerprint(ROOT/folder/'package') != expected:
            raise Failure(f'Manifesto divergente: {folder}')
    with tempfile.TemporaryDirectory(prefix='irix-suite-') as tmp:
        staged = Path(tmp)/'classic'
        shutil.copytree(pairs[1][0], staged)
        metadata = staged/'metadata.json'
        value = json.loads(metadata.read_text())
        value['KPlugin']['Id'] = pairs[1][1].name
        metadata.write_text(json.dumps(value, ensure_ascii=False, indent=4)+'\n')
        if pairs[1][1].exists():
            classic.merge_settings(pairs[1][1], staged)
        pairs[1] = (staged, pairs[1][1])
        if args.verificar:
            bundle.install(pairs, dry=True)
        else:
            with bundle.locked():
                bundle.install(pairs)
            if not args.sem_cache:
                refresh_icons(data)
    if not args.verificar:
        print('Os dois temas e suas dependências foram instalados no seu perfil.')
        print('Para aplicar o conjunto: bash aplicar-tema.sh classic (ou moderno).')
        print('Após atualizar QML em uso, salve o trabalho e entre novamente na sessão.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(f'ERRO: {exc}')
