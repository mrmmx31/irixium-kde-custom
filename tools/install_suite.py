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
import uuid

from theme_transaction import Failure, no_links, snapshot, image, atomic, replace_checked
from user_bundle import Bundle
from components import sources, cursor_compat_sources, decoration_sources, gtk_compat_sources
from domainos_native_menu import prepared_source_pairs

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



def migrate_user_hook(data, config, state, dry=False):
    """Detach only this checkout's existing optional hook from its source tree."""
    # Standalone DomainOS packages import this module without the Classic hook.
    # The optional helper is needed only when this suite migration is requested.
    from classic_hook_runtime import migrate
    return migrate(ROOT, data, config, state, dry=dry)


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


def check_domainos_qt():
    """The DomainOS separate popup windows require Qt Quick Controls 6.8."""
    version = subprocess.check_output(['qtpaths6', '--qt-version'], text=True).strip()
    try:
        major, minor = (int(part) for part in version.split('.')[:2])
    except (ValueError, TypeError):
        raise Failure('Não foi possível verificar a versão Qt 6 usada pelo Plasma: ' + version)
    if (major, minor) < (6, 8):
        raise Failure('DomainOS exige Qt 6.8 ou superior; Qt encontrado: ' + version
                      + '. Atualize pelos pacotes da distribuição. Nenhum pacote de sistema foi alterado.')


def check_runtime():
    missing = [name for name in ('plasma-apply-lookandfeel', 'kreadconfig6', 'qtpaths6', 'qdbus6')
               if not shutil.which(name)]
    if shutil.which('qtpaths6'):
        check_domainos_qt()
    if not missing:
        def query(name):
            return Path(subprocess.check_output(['qtpaths6','--query',name],text=True).strip())
        qml = query('QT_INSTALL_QML')
        plugins = query('QT_INSTALL_PLUGINS')
        for path, label in [(qml/'org/kde/kwin/decoration/qmldir','Aurorae Qt 6'),
                            (qml/'org/kde/ksvg/qmldir','KSvg QML Qt 6'),
                            (qml/'org/kde/ksysguard/sensors/qmldir','KSystemStats QML Qt 6'),
                            (qml/'org/kde/taskmanager/qmldir','TaskManager QML Plasma 6'),
                            (qml/'org/kde/plasma/private/pager/qmldir','Pager QML Plasma 6'),
                            (qml/'org/kde/plasma/private/kicker/qmldir','Aplicativos QML Plasma 6'),
                            (qml/'org/kde/plasma/private/taskmanager/qmldir','Menu de tarefas QML Plasma 6'),
                            (qml/'org/kde/plasma/private/sessions/qmldir','Sessão QML Plasma 6'),
                            (qml/'org/kde/plasma/plasma5support/qmldir','Plasma5Support Qt 6'),
                            (qml/'org/kde/plasma/workspace/dbus/qmldir','D-Bus QML Plasma 6'),
                            (qml/'org/kde/plasma/workspace/calendar/qmldir','Calendário QML Plasma 6'),
                            (qml/'org/kde/kcmutils/qmldir','Preferências QML Plasma 6'),
                            (plugins/'kf6/kded/gtkconfig.so','GTK Config nativo do KDE'),
                            (plugins/'styles/libkvantum.so','Kvantum Qt 6')]:
            if not path.is_file():
                missing.append(label)
    if not shutil.which('ksystemstats'):
        missing.append('ksystemstats')
    # The transient KWin bridge deliberately uses distribution Qt bindings,
    # matching KDE's libraries rather than an unrelated virtual environment.
    python = Path('/usr/bin/python3')
    if not python.is_file() or subprocess.run(
            [str(python), '-c', 'from PyQt6 import QtCore, QtDBus, QtGui; from PIL import Image'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        missing.append('PyQt6 QtCore/QtDBus/QtGui e Pillow do Python da distribuição')
    if missing:
        raise Failure('Dependências de execução ausentes: '+', '.join(missing)+
                      '. Instale os pacotes da sua distribuição antes de continuar. Nenhum pacote de sistema foi alterado.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--restaurar', action='store_true')
    parser.add_argument('--recuperar', action='store_true',
                        help='concluir a restauração de uma migração interrompida; exige --restaurar')
    parser.add_argument('--recarregar-decoracao', action='store_true',
                        help='liberar QML antigo da decoração IRIX na sessão do próprio usuário')
    parser.add_argument('--sem-cache', action='store_true', help='para testes sem sessão gráfica')
    parser.add_argument('--sem-integracao', action='store_true',
                        help='não instalar/iniciar o observador GTK/Kvantum por usuário')
    parser.add_argument('--cursor-compat-root', type=Path,
                        help='raiz de compatibilidade libXcursor; padrão ~/.icons; útil para testes isolados')
    parser.add_argument('--gtk-compat-root', type=Path,
                        help='raiz de descoberta GTK2; padrão ~/.themes; útil para testes isolados')
    args = parser.parse_args()
    if args.recuperar and not args.restaurar:
        parser.error('--recuperar exige --restaurar')
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    data, config, state = roots()
    if args.recarregar_decoracao:
        if args.sem_cache or args.restaurar:
            parser.error('--recarregar-decoracao exige instalação na sessão gráfica, sem --sem-cache/--restaurar')
        from reload_decoration import check_session
        check_session()
    if not args.restaurar:
        check_runtime()
    pairs = sources(data, config) + cursor_compat_sources(args.cursor_compat_root) + gtk_compat_sources(args.gtk_compat_root)
    from theme_companion_bridge import (install as install_companion_bridge, locations as companion_locations,
        restore_palette_resources, stop_if_installed, start as start_companion_bridge,
        uninstall as uninstall_companion_bridge, service as companion_service, UNIT as companion_unit)
    from domainos_color_migration import LEGACY_FILENAME, prepare_migration, install_with_migration, restore_migration
    bundle = Bundle(state/'irixium-suite', [dest for _, dest in pairs]
                    + [data/'color-schemes'/LEGACY_FILENAME])
    if args.restaurar:
        uninstall_companion_bridge(data, config, state, dry=True)
        palette_plan = restore_palette_resources(data, config, state, Path.home(), dry=True)
        if not args.verificar:
            if not args.sem_cache: stop_if_installed(data, config, state)
            restore_palette_resources(data, config, state, Path.home())
        restore_migration(data, state, dry=True, recovery=args.recuperar)
        overlays = [entry for result in palette_plan for entry in result.get('overlays', [])]
        bundle.restore(dry=True, overlays=overlays if args.verificar else None)
        if args.verificar:
            return
        else:
            with bundle.locked():
                restore_migration(data, state, dry=True, recovery=args.recuperar)
                bundle.restore(dry=True)
                restore_migration(data, state, recovery=args.recuperar)
                bundle.restore()
            if not args.sem_cache:
                refresh_icons(data)
            companion_control = companion_locations(data, config, state)['control']
            if companion_control.exists() and not args.sem_cache:
                companion_service(['disable', companion_unit])
            uninstall_companion_bridge(data, config, state)
        return
    sys.path.insert(0, str(ROOT/'icons/tools'))
    if not args.sem_integracao:
        install_companion_bridge(data, config, state, Path.home(), dry=True)
    from icon_common import audit
    for source in (ROOT/'icons/Irixium', ROOT/'icons/themes/IrixClassic-SGI'):
        report = audit(source)
        if report['errors']:
            raise Failure(f'Ícones inválidos em {source}: {report["errors"]} erro(s). Execute icons/tools/validate_theme.py.')
    sys.path.insert(0, str(ROOT/'cursors/tools'))
    from cursor_audit import audit_theme as audit_cursors
    for source, _ in pairs:
        if source.parent == ROOT/'cursors':
            report = audit_cursors(source)
            if report['errors']:
                raise Failure('Cursores inválidos: '+ '; '.join(report['errors']))
    # Stage metadata with the same ID used by the global theme. Preserve only
    # known appearance settings, not old QML implementations or interaction delays.
    spec = importlib.util.spec_from_file_location('classic_manager', ROOT/'decorations/classic/tools/manage.py')
    classic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(classic)
    from user_bundle import fingerprint
    for package in decoration_sources():
        folder = package.parent.relative_to(ROOT)
        expected = json.loads((ROOT/folder/'MANIFEST.json').read_text())['package']
        if fingerprint(ROOT/folder/'package') != expected:
            raise Failure(f'Manifesto divergente: {folder}')
    with tempfile.TemporaryDirectory(prefix='irix-suite-') as tmp:
        classic_index = next(i for i, (_, dest) in enumerate(pairs)
                             if dest.name == 'irixium_irix_classic_v4')
        classic_source, classic_dest = pairs[classic_index]
        staged = Path(tmp)/'classic'
        shutil.copytree(classic_source, staged)
        metadata = staged/'metadata.json'
        value = json.loads(metadata.read_text())
        value['KPlugin']['Id'] = classic_dest.name
        metadata.write_text(json.dumps(value, ensure_ascii=False, indent=4)+'\n')
        if classic_dest.exists():
            classic.merge_settings(classic_dest, staged)
        pairs[classic_index] = (staged, classic_dest)
        with prepared_source_pairs(ROOT, pairs, dry=args.verificar) as prepared:
            # Dynamic palette files belong to their own journals. Validate
            # those guards before replacing a complete installed theme tree.
            restore_palette_resources(data, config, state, Path.home(), dry=True)
            if not args.verificar:
                if not args.sem_cache: stop_if_installed(data, config, state)
                restore_palette_resources(data, config, state, Path.home())
            migration = prepare_migration(data, state)
            install_with_migration(bundle, prepared, migration, dry=args.verificar)
        if not args.verificar:
            if not args.sem_cache:
                refresh_icons(data)
    migrate_user_hook(data, config, state, dry=args.verificar)
    if not args.sem_integracao:
        install_companion_bridge(data, config, state, Path.home(), dry=args.verificar)
        if not args.verificar and not args.sem_cache:
            from select_gtk import native_ready
            if native_ready(): start_companion_bridge()
            else: print('Integração instalada. Inicie-a na própria sessão KDE: python3 tools/theme_companion_bridge.py --instalar --iniciar')
    if args.recarregar_decoracao:
        from reload_decoration import reload
        reload(config/'kwinrc', state/'irixium-decoration-reload', dry=args.verificar)
    if not args.verificar:
        print('Os dois temas e suas dependências gráficas foram instalados no seu perfil.')
        print('Sons SGI: use sons/instalar.sh --baixar, --origem DIRETORIO ou o cache local já preparado.')
        print('Para aplicar o conjunto: bash aplicar-tema.sh classic (ou moderno).')
        if not args.recarregar_decoracao:
            print('Para liberar QML antigo em uso: python3 tools/reload_decoration.py (na própria sessão KDE).')
        print('Reabra os aplicativos para recarregar Kvantum e os ícones.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(f'ERRO: {exc}')
