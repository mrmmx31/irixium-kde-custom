#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""User-only integration for the GTK and Kvantum companions of Global Themes.

Observe committed KDE choices and GTKConfig's exported palette. Never select
a Global Theme, color scheme, panel layout, font, icon theme or cursor here.
There is no polling loop, rendering hook or restart of the desktop.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from components import catalog
from select_companions import effective_look_and_feel, select, require_global
from select_gtk import notify
from theme_transaction import Failure, atomic, no_links, sha
from user_bundle import Bundle, fingerprint

ROOT = Path(__file__).resolve().parents[1]
UNIT = 'irix-theme-companions.service'
MODULES = ('theme_companion_bridge.py', 'select_companions.py', 'select_gtk.py',
           'theme_transaction.py', 'components.py', 'reload_decoration.py',
           'gtk2_palette.py', 'gtk2_scrollbar_assets.py', 'gtk2_modern_palette.py', 'gtk2_palette_runtime.py',
           'gtk2_domainos_palette.py', 'domainos_motif_art.py',
           'gtk4_palette_runtime.py', 'user_bundle.py', 'apply_kvantum_colors.py', 'apply_color_scheme.py',
           'kvantum_native_palette.py', 'kvantum_palette_runtime.py',
           'kvantum_classic_palette.py', 'kvantum_modern_palette.py', 'kvantum_domainos_palette.py',
           'kvantum_palette_config.py')


def locations(data, config, state):
    return {'runtime': data/'irixium/theme-companions',
            'unit': config/'systemd/user'/UNIT,
            'control': state/'irixium-theme-companions/control.json',
            'state': state/'irixium-theme-companions'}


def validate_roots(data, config, state, home):
    for path in (data, config, state, home):
        no_links(path)
        if any(path == base or base in path.parents for base in map(Path, ('/usr', '/etc', '/opt', '/var'))):
            raise Failure('A integração só pode usar as pastas deste usuário.')
        existing = next(part for part in (path, *path.parents) if part.exists())
        if existing.stat().st_uid != os.getuid() and existing != Path('/tmp'):
            raise Failure('Pasta não pertence ao usuário: ' + str(path))


def roots():
    home = Path.home()
    data, config, state = [Path(os.environ.get(key) or home/default).expanduser()
        for key, default in (('XDG_DATA_HOME', '.local/share'),
                             ('XDG_CONFIG_HOME', '.config'), ('XDG_STATE_HOME', '.local/state'))]
    validate_roots(data, config, state, home)
    return data, config, state, home


def quote(value, *, command=False):
    value = str(value)
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Failure('Caractere de controle no caminho do serviço.')
    value = value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
    if command: value = value.replace('$', '$$')
    return '"' + value + '"'


def service_content(paths, data, config, state):
    return ('[Unit]\nDescription=IRIX: GTK e Kvantum do tema global deste usuário\n'
        'After=graphical-session.target\nPartOf=graphical-session.target\n\n'
        '[Service]\nType=simple\nExecStart=/usr/bin/python3 -B '
        + quote(paths['runtime']/'tools/theme_companion_bridge.py', command=True) + ' --observar\n'
        + ''.join('Environment=' + quote(key+'='+str(value)) + '\n' for key, value in (
            ('XDG_DATA_HOME', data), ('XDG_CONFIG_HOME', config), ('XDG_STATE_HOME', state)))
        + 'Restart=no\n\n[Install]\nWantedBy=graphical-session.target\n').encode()


def install(data, config, state, home, *, source_root=ROOT, dry=False):
    validate_roots(data, config, state, home)
    paths = locations(data, config, state)
    bundle = Bundle(paths['state']/'installation', (paths['runtime'], paths['unit'], paths['control']))
    no_links(source_root)
    required = [source_root/'tools'/name for name in MODULES] + [source_root/'components.json']
    for file in required:
        no_links(file)
        if not file.is_file(): raise Failure('Dependência da integração ausente: ' + str(file))
    if not bundle.latest() and any(paths[key].exists() for key in ('runtime', 'unit', 'control')):
        raise Failure('Integração existente sem recibo; substituição recusada.')
    # Use this user's state directory. In particular, do not populate /tmp with
    # another complete icon/theme tree just to install a few helper modules.
    if dry:
        return {'status': 'ready', 'unit': UNIT, 'modules': len(MODULES)}
    paths['state'].mkdir(parents=True, mode=0o700, exist_ok=True)
    with bundle.locked(), tempfile.TemporaryDirectory(prefix='.stage-', dir=paths['state']) as temp:
        if bundle.latest(): verify_runtime(paths)
        stage = Path(temp); runtime = stage/'runtime'
        for file in required:
            relative = file.relative_to(source_root)
            atomic(runtime/relative, file.read_bytes(), 0o644)
        unit = stage/UNIT
        atomic(unit, service_content(paths, data, config, state), 0o600)
        control = stage/'control.json'
        atomic(control, (json.dumps({'format': 1, 'uid': os.getuid(),
            'paths': {key: str(paths[key]) for key in ('runtime', 'unit')},
            'fingerprints': {'runtime': fingerprint(runtime), 'unit': fingerprint(unit)}}) + '\n').encode())
        bundle.install(((runtime, paths['runtime']), (unit, paths['unit']), (control, paths['control'])))
    return {'status': 'installed', 'unit': UNIT, 'runtime': str(paths['runtime'])}


def verify_runtime(paths):
    bundle = Bundle(paths['state']/'installation', (paths['runtime'], paths['unit'], paths['control']))
    prior = bundle.latest()
    if not prior or prior[1]['status'] != 'installed':
        raise Failure('Integração não instalada ou restauração pendente.')
    no_links(paths['control'])
    control = json.loads(paths['control'].read_text())
    if control.get('format') != 1 or control.get('uid') != os.getuid() or \
            control.get('paths') != {key: str(paths[key]) for key in ('runtime', 'unit')}:
        raise Failure('Controle da integração não pertence a estes caminhos/usuário.')
    for key in ('runtime', 'unit'):
        if fingerprint(paths[key]) != control['fingerprints'][key]:
            raise Failure('Integração editada após a instalação: ' + str(paths[key]))


def restore_palette_resources(data, config, state, home, *, dry=False):
    """Before upgrading/removing owned theme trees, restore their own overlays.

    Never remove a receipt to pretend a personal edit was a fresh baseline.
    No native GTK selection or system configuration is changed here.
    """
    results = []
    gtk2_control = state/'irixium-gtk2-palette/active.json'
    no_links(gtk2_control)
    if gtk2_control.is_file() and json.loads(gtk2_control.read_text()).get('status') == 'active':
        from gtk2_palette_runtime import restore
        results.append(restore(data, config, state, home, dry=dry))
    from gtk4_palette_runtime import THEMES, restore as restore_gtk4
    for name in THEMES:
        control = state/'irixium-gtk4-palette'/name/'control.json'
        no_links(control)
        if control.is_file(): results.append(restore_gtk4(data, config, state, home, name, dry=dry))
    from kvantum_palette_runtime import THEMES as QT_THEMES, restore as restore_qt
    for name in QT_THEMES:
        control = state/'irixium-kvantum-palette'/name/'control.json'
        no_links(control)
        if control.is_file(): results.append(restore_qt(config, state, name, dry=dry))
    return results


def service(arguments):
    subprocess.run(['systemctl', '--user', *arguments], capture_output=True, text=True, check=True, timeout=20)


def start():
    from reload_decoration import check_session
    check_session()
    service(['daemon-reload'])
    service(['enable', '--now', UNIT])


def stop_if_installed(data, config, state):
    paths = locations(data, config, state)
    if paths['control'].exists():
        verify_runtime(paths)
        service(['stop', UNIT])


def uninstall(data, config, state, *, dry=False):
    paths = locations(data, config, state)
    if not paths['control'].exists(): return {'status': 'not_installed'}
    verify_runtime(paths)
    bundle = Bundle(paths['state']/'installation', (paths['runtime'], paths['unit'], paths['control']))
    if dry: bundle.restore(dry=True)
    else:
        with bundle.locked(): bundle.restore()
    return {'status': 'restore_ready' if dry else 'restored'}


def profile_for(global_theme):
    for name, profile in catalog()['profiles'].items():
        if profile['global'] == global_theme: return name
    return None


def effective_widget_style(config):
    environment = dict(os.environ, XDG_CONFIG_HOME=str(config))
    environment['XDG_CONFIG_DIRS'] = str(config/'kdedefaults') + ':' + (environment.get('XDG_CONFIG_DIRS') or '/etc/xdg')
    return subprocess.check_output(['kreadconfig6', '--file', 'kdeglobals', '--group', 'KDE',
        '--key', 'widgetStyle'], env=environment, text=True, timeout=10).strip()


def reload_kvantum(config, profile):
    require_global(config, profile['global'])
    if effective_widget_style(config).lower() != 'kvantum':
        return 'preserved_independent_application_style'
    # PlasmaIntegration reads the *current* widgetStyle again on this native
    # event, then creates a fresh QStyle (including Kvantum's selected subtheme).
    # This signal stays on the invoking user's session bus.
    subprocess.run(['dbus-send', '--session', '--type=signal', '/KGlobalSettings',
        'org.kde.KGlobalSettings.notifyChange', 'int32:2', 'int32:0'],
        capture_output=True, text=True, timeout=10, check=True)
    return 'native_style_change_sent'


def native_palette_signature(config):
    """Fingerprint KDE's inputs independently of its asynchronous GTK export.

    A Global Theme applied by the GUI can change these inputs while colors.css
    still contains the preceding theme. Reading only colors.css misses that
    change. Notifications do not write these files, so our own notification
    cannot change this signature and request another export.
    """
    sources = []
    for relative in ('kdeglobals', 'kdedefaults/kdeglobals'):
        path = config/relative
        no_links(path)
        if path.exists():
            if not path.is_file() or path.stat().st_size > 1048576:
                raise Failure('Origem KDE inválida para a paleta: ' + str(path))
            sources.append((relative, sha(path.read_bytes())))
        else:
            sources.append((relative, None))
    return sha(json.dumps(sources, separators=(',', ':')).encode())


def palette_export_identity(config):
    identities = []
    for version in ('3.0', '4.0'):
        path = config/f'gtk-{version}/colors.css'
        no_links(path)
        if not path.exists():
            identities.append(None)
            continue
        stat = path.stat()
        if not path.is_file() or stat.st_size > 262144:
            raise Failure('Exportação GTK nativa inválida: ' + str(path))
        identities.append((stat.st_ino, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size))
    return tuple(identities)


def wait_for_native_palette(config, profile, before, source, *, timeout=2):
    """Bounded configuration-worker wait for GTKConfig's actual file write.

    KDE exports asynchronously, even for identical colors. Do not generate
    GTK2/4 resources from the preceding theme during that interval. This wait
    runs in the separate worker; the desktop and observer stay responsive.
    """
    from gtk2_palette import exported_palette
    deadline = time.monotonic() + timeout
    while True:
        current = palette_export_identity(config)
        previous = before or (None, None)
        if all(value is not None and value != old for value, old in zip(current, previous)):
            try:
                palettes = [exported_palette((config/f'gtk-{version}/colors.css').read_bytes())
                            for version in ('3.0', '4.0')]
                complete = palettes[0] == palettes[1] and current == palette_export_identity(config)
            except (OSError, Failure):
                complete = False  # Native exporter may still be writing.
            if complete:
                require_global(config, profile['global'])
                if native_palette_signature(config) != source:
                    raise Failure('A paleta KDE mudou durante a exportação; atualização anterior recusada.')
                return
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise Failure('GTKConfig não confirmou a nova exportação de cores; paleta anterior não aplicada.')
        time.sleep(min(0.025, remaining))


def reload_gtk_palette(config, profile):
    """Ask KDE to re-read its committed palette, without writing KDE settings.

    GTKConfig's public theme setter does not refresh colors. KConfigWatcher
    reparses kdeglobals on this native notification; GTKConfig then exports
    the current KColorScheme. Its resulting file event is handled by watch().
    The static GVariant payload contains only the native ColorScheme key.
    """
    require_global(config, profile['global'])
    from gtk4_palette_runtime import accepts
    if not accepts(notify(), profile['gtk']):
        return 'preserved_independent_gtk_theme'
    source = native_palette_signature(config)
    before = palette_export_identity(config)
    subprocess.run(['gdbus', 'emit', '--session', '--object-path', '/kdeglobals',
        '--signal', 'org.kde.kconfig.notify.ConfigChanged',
        "@a{saay} {'General': [[byte 67, 111, 108, 111, 114, 83, 99, 104, 101, 109, 101]]}"],
        capture_output=True, text=True, timeout=10, check=True)
    wait_for_native_palette(config, profile, before, source)
    if not accepts(notify(), profile['gtk']):
        return 'preserved_independent_gtk_theme'
    return 'native_palette_exported'


def synchronize(data, config, state, home, *, companions=True, palette=True, native_palette=False):
    global_theme = effective_look_and_feel(config)
    name = profile_for(global_theme)
    if not name: return {'status': 'ignored_other_global_theme', 'global': global_theme}
    profile = catalog()['profiles'][name]
    result = {'status': 'synchronized', 'profile': name}
    if companions:
        result['companions'] = select(name, data, config, state, home)
        if result['companions']['status'] == 'applied':
            result['kvantum'] = reload_kvantum(config, profile)
    if palette:
        require_global(config, global_theme)
        # Respect an independent GTK selection until the user chooses this
        # Global Theme again. A color change alone does not select its GTK.
        from gtk4_palette_runtime import accepts
        if accepts(notify(), profile['gtk']):
            if native_palette:
                result['native_palette'] = reload_gtk_palette(config, profile)
                if result['native_palette'] == 'preserved_independent_gtk_theme':
                    result['gtk2_palette'] = {'status': 'preserved_independent_gtk_theme'}
                    return result
            from gtk2_palette_runtime import refresh, setup
            palette_control = state/'irixium-gtk2-palette/active.json'
            no_links(palette_control)
            if palette_control.exists():
                status = json.loads(palette_control.read_text()).get('status')
                if status not in ('active', 'restored'):
                    raise Failure('A paleta GTK2 tem uma atualização incompleta; confira o recibo.')
            else: status = None
            operation = refresh if status == 'active' else setup
            result['gtk2_palette'] = operation(data, config, state, home, profile['gtk'])
            from gtk4_palette_runtime import refresh as refresh_gtk4
            result['gtk4_palette'] = refresh_gtk4(data, config, state, home, profile['gtk'],
                force_reload=result['gtk2_palette'].get('native_reload_required', False))
        else:
            result['gtk2_palette'] = {'status': 'preserved_independent_gtk_theme'}
    return result


def watch(data, config, state, home, *, app=None, worker=None):
    from PyQt6.QtCore import (QCoreApplication, QFileSystemWatcher, QMetaObject,
                             QObject, QProcess, Qt, pyqtSlot)
    from PyQt6.QtDBus import QDBusConnection
    from reload_decoration import check_session
    check_session()
    paths = locations(data, config, state)
    verify_runtime(paths)
    application = app or QCoreApplication(sys.argv)

    class Observer(QObject):
        def __init__(self):
            super().__init__()
            self.watcher = QFileSystemWatcher(self)
            self.watcher.fileChanged.connect(self.changed)
            self.watcher.directoryChanged.connect(self.changed)
            self.process = None
            self.queued = False
            self.pending = False
            # Starting or upgrading the integration installs options; it is
            # not an explicit Global Theme choice. Keep an independently
            # selected GTK/Kvantum theme until a later native transition.
            # Initial reconciliation may still refresh an already selected
            # companion's palette, using its existing ownership guards.
            self.seen_global = effective_look_and_feel(config)
            self.attempted = None
            self.attempted_native = None
            # Ignore the complex KConfig payload and read its effective value
            # with the public KConfig CLI, including kdedefaults and [$i]/[$d].
            # Filesystem events additionally cover atomic replacements and
            # GTKConfig's colors.css export after the native KDE notification.
            self.bus = QDBusConnection.sessionBus()
            if not self.bus.connect('', '/kdeglobals', 'org.kde.kconfig.notify', 'ConfigChanged', self.native_changed):
                raise Failure('Não foi possível observar as escolhas KDE desta sessão.')
            self.changed()

        def arm(self):
            candidates = [config, config/'kdeglobals', config/'kdedefaults',
                config/'kdedefaults/kdeglobals', config/'gtk-3.0', config/'gtk-3.0/colors.css']
            desired = {str(path) for path in candidates if path.exists()}
            existing = set(self.watcher.files()+self.watcher.directories())
            if existing-desired: self.watcher.removePaths(sorted(existing-desired))
            if desired-existing: self.watcher.addPaths(sorted(desired-existing))

        @pyqtSlot()
        def native_changed(self):
            self.changed()

        def changed(self, *_):
            self.pending = True
            if not self.queued:
                self.queued = True
                QMetaObject.invokeMethod(self, 'reconcile', Qt.ConnectionType.QueuedConnection)

        @pyqtSlot()
        def reconcile(self):
            self.queued = False
            self.arm()
            if self.process is not None: return
            self.pending = False
            try:
                selected = effective_look_and_feel(config)
                transition = selected != self.seen_global
                self.seen_global = selected
                name = profile_for(selected)
                if not name:
                    self.attempted = None
                    self.attempted_native = None
                    return
                css = config/'gtk-3.0/colors.css'
                no_links(css)
                digest = sha(css.read_bytes()) if css.is_file() and css.stat().st_size <= 1048576 else None
                theme = notify()
                source = native_palette_signature(config)
                key = (selected, theme, source, digest)
                if key == self.attempted and not transition: return
                self.attempted = key
                arguments = ['--sincronizar']
                if not transition: arguments.append('--somente-paleta')
                native_key = (selected, source)
                if native_key != self.attempted_native:
                    self.attempted_native = native_key
                    arguments.append('--notificar-paleta')
                self.process = QProcess(self)
                self.process.finished.connect(self.finished)
                self.process.errorOccurred.connect(self.failed)
                self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
                executable = worker or paths['runtime']/'tools/theme_companion_bridge.py'
                self.process.start('/usr/bin/python3', ['-B', str(executable), *arguments])
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                print('Integração: ' + str(error), file=sys.stderr, flush=True)

        def finished(self, code, _status):
            process = self.process
            self.process = None
            if process is None: return
            output = bytes(process.readAllStandardOutput()).decode(errors='replace').strip()
            if output: print(output, flush=True)
            process.deleteLater()
            # Own GTK setter/file events may arrive during the worker. Read
            # the resulting state once; do not repeatedly retry a failed key.
            if code: print('Integração recusada; consulte o recibo. Sem repetição automática.', file=sys.stderr, flush=True)
            if self.pending: self.changed()

        def failed(self, error):
            if error == QProcess.ProcessError.FailedToStart:
                process = self.process; self.process = None
                if process: process.deleteLater()
                print('Integração: helper não iniciou.', file=sys.stderr, flush=True)

    observer = Observer()
    if app is not None: return observer
    return application.exec()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--instalar', action='store_true')
    mode.add_argument('--observar', action='store_true')
    mode.add_argument('--sincronizar', action='store_true')
    mode.add_argument('--restaurar', action='store_true')
    parser.add_argument('--iniciar', action='store_true')
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--somente-paleta', action='store_true')
    parser.add_argument('--notificar-paleta', action='store_true')
    args = parser.parse_args()
    if os.geteuid() == 0 or os.geteuid() != os.getuid(): raise Failure('Execute como usuário normal, sem sudo.')
    data, config, state, home = roots()
    paths = locations(data, config, state)
    if args.observar: return watch(data, config, state, home)
    if args.instalar:
        result = install(data, config, state, home, dry=args.verificar)
        if args.iniciar and not args.verificar:
            from reload_decoration import check_session
            check_session()
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True, timeout=20)
            subprocess.run(['systemctl', '--user', 'enable', '--now', UNIT], check=True, timeout=20)
    elif args.restaurar:
        bundle = Bundle(paths['state']/'installation', (paths['runtime'], paths['unit'], paths['control']))
        bundle.restore(dry=True)
        if not args.verificar:
            subprocess.run(['systemctl', '--user', 'disable', '--now', UNIT], check=True, timeout=20)
            with bundle.locked(): bundle.restore()
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True, timeout=20)
        result = {'status': 'restore_ready' if args.verificar else 'restored'}
    else:
        from reload_decoration import check_session
        check_session()
        result = synchronize(data, config, state, home, companions=not args.somente_paleta,
                             native_palette=args.notificar_paleta)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit('ERRO: ' + str(error))
