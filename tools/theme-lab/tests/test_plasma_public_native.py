#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the public backend -> bwrap -> native Plasma/KSvg scrollbar path."""
import configparser
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HOME = '/home/domainos-test'
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend


def wait(predicate, process, environment, timeout=40):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        if process.poll() is not None:
            raise AssertionError(f'private Plasma backend exited early ({process.returncode})')
        if subprocess.run(['xdpyinfo'], env=environment, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=2).returncode:
            time.sleep(.05)
    raise AssertionError('private Plasma/KSvg preview timed out')


def private_fixture(output):
    for name in ('home/.config', 'home/.local/share/color-schemes',
                 'home/.local/state', 'home/.cache', 'etc', 'run/user/1000', 'tmp'):
        (output / name).mkdir(mode=0o700, parents=True, exist_ok=True)
    (output / 'etc/passwd').write_text(
        f'domainos-test:x:1000:1000:Preview:{HOME}:/usr/sbin/nologin\n', encoding='utf-8')
    (output / 'etc/group').write_text('domainos-test:x:1000:\n', encoding='utf-8')
    (output / 'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n', encoding='utf-8')
    (output / 'etc/domainos-preview').touch()
    for source in ('/etc/fonts', '/etc/ld.so.cache', '/etc/alternatives'):
        path = Path(source)
        target = output / 'etc' / path.name
        if path.is_dir():
            target.mkdir()
        elif path.exists():
            target.touch()
    scheme = ROOT / 'colors/DomainOS-SR10.4.colors'
    shutil.copyfile(scheme, output / 'home/.local/share/color-schemes/DomainOS-SR10.4.colors')
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(scheme, encoding='utf-8')
    config['General']['ColorScheme'] = 'DomainOS-SR10.4'
    config['KDE'] = {'LookAndFeelPackage': 'org.magpie.irixclassic.domainos.desktop'}
    with (output / 'home/.config/kdeglobals').open('w', encoding='utf-8') as stream:
        config.write(stream)
    project = {
        'schema_version': 1, 'kind': 'theme_lab_project',
        'name': 'Plasma public scrollbar fixture', 'reference': '',
        'selected_family': 'plasma', 'color_scheme': 'DomainOS-SR10.4',
        'recipes': {},
    }
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    for family in backend.FAMILIES:
        project['recipes'][family] = {
            'geometry': geometry.copy(), 'palette': palette.copy(),
            'visible_categories': 1 << 2,
            'visible_controls': (1 << 10) | (1 << 11),
            'selected_control': 10,
            'positions': [[16, 16] for _ in range(16)],
            'sizes': [[0, 0] for _ in range(16)],
        }
    backend.write_json(output / 'home/project.json', project)


def main():
    output = Path(tempfile.mkdtemp(prefix='.qa-i172-plasma-public-', dir=ROOT))
    print('fixture=' + str(output), flush=True)
    private_fixture(output)
    number = next(n for n in range(180, 4096)
                  if not Path(f'/tmp/.X{n}-lock').exists() and not Path(f'/tmp/.X11-unix/X{n}').exists())
    display = f':{number}'
    authority = output / 'Xauthority'
    authority.touch(mode=0o600)
    subprocess.run(['xauth', '-f', str(authority), 'add', display, '.', secrets.token_hex(16)], check=True)
    host_environment = dict(os.environ, DISPLAY=display, XAUTHORITY=str(authority))
    server = process = None
    log_path = output / 'namespace.log'
    with log_path.open('w', encoding='utf-8') as log:
        try:
            server = subprocess.Popen(['/usr/bin/Xvfb', display, '-screen', '0', '900x700x24',
                                       '-nolisten', 'tcp', '-auth', str(authority)],
                                      stdout=log, stderr=log, start_new_session=True)
            wait(lambda: True if subprocess.run(['xdpyinfo'], env=host_environment,
                                                 stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL, timeout=2).returncode == 0 else None,
                 server, host_environment, timeout=10)
            command = [
                'unshare', '--user', '--map-root-user', '--net', 'bwrap', '--unshare-user',
                '--unshare-ipc', '--unshare-uts', '--uid', '1000', '--gid', '1000', '--clearenv',
                '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
                '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
                '--ro-bind', str(output / 'etc'), '/etc', '--proc', '/proc', '--dev', '/dev',
                '--bind', str(output / 'run'), '/run', '--bind', str(output / 'tmp'), '/tmp',
                '--bind', str(output / 'home'), HOME, '--ro-bind', str(ROOT), '/fixture/root',
                '--ro-bind', f'/tmp/.X11-unix/X{number}', f'/tmp/.X11-unix/X{number}',
                '--ro-bind', str(authority), HOME + '/.Xauthority',
            ]
            for source in ('/etc/fonts', '/etc/ld.so.cache', '/etc/alternatives'):
                if Path(source).exists():
                    command += ['--ro-bind', source, source]
            values = {
                'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8', 'HOME': HOME,
                'DISPLAY': display, 'XAUTHORITY': HOME + '/.Xauthority',
                'XDG_CONFIG_HOME': HOME + '/.config', 'XDG_DATA_HOME': HOME + '/.local/share',
                'XDG_STATE_HOME': HOME + '/.local/state', 'XDG_CACHE_HOME': HOME + '/.cache',
                'XDG_RUNTIME_DIR': '/run/user/1000', 'GDK_BACKEND': 'x11',
                'QT_QPA_PLATFORM': 'xcb', 'NO_AT_BRIDGE': '1', 'PRIVATE_XEPHYR': '1',
                'QT_QPA_PLATFORMTHEME': 'generic', 'XDG_DESKTOP_PORTAL_DIR': '/nonexistent',
                'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap',
                'IRIX_DOMAINOS_PRIVATE_XEPHYR': '1', 'IRIX_DOMAINOS_SESSION_ROOT': HOME,
                'THEMELAB_PLASMA_TEST_CLOSE_MS': '2200',
            }
            for key, value in values.items():
                command += ['--setenv', key, value]
            command += [
                '--die-with-parent', '--new-session', '--chdir', HOME, 'dbus-run-session', '--',
                '/usr/bin/python3', '-B', '/fixture/root/tools/theme-lab/backend.py', '--preview',
                '--root', '/fixture/root', '--project', HOME + '/project.json',
                '--output', HOME + '/out', '--kdeglobals', HOME + '/.config/kdeglobals',
                '--family', 'plasma',
            ]
            process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)

            def native_result():
                rows = list((output / 'home/out/revisions').glob('*/RESULTADO.json'))
                for row in rows:
                    try:
                        data = json.loads(row.read_text(encoding='utf-8'))
                        result = data.get('families', {}).get('plasma')
                        if result and result.get('status') == 'partially_generated':
                            virtual = Path(result['snapshot'])
                            path = output / 'home' / virtual.relative_to(HOME) / 'native-preview/RESULTADO.json'
                            preview = row.parent / 'plasma-PREVIEW.json'
                            if path.is_file() and preview.is_file():
                                proof = json.loads(preview.read_text(encoding='utf-8'))
                                if proof.get('status') == 'closed':
                                    return row, data, json.loads(path.read_text(encoding='utf-8'))
                    except (OSError, json.JSONDecodeError):
                        continue
                return None

            revision_path, generated, native = wait(native_result, process, host_environment)
            assert generated['families']['plasma']['translated_controls'] == ['scroll_h', 'scroll_v']
            assert native['guards']['verified'] and not native['guards']['personalHomeExposed']
            assert native['runtime']['native_qml']
            assert native['runtime']['renderer'] == 'org.kde.plasma.components.ScrollBar + KSvg'
            assert not native['qml_warnings'], native['qml_warnings']
            assert native['screenshot_saved'], native
            vertical = native['bars']['plasmaVerticalScrollBar']
            horizontal = native['bars']['plasmaHorizontalScrollBar']
            assert (vertical['width'], vertical['height']) == (15.0, 230.0), vertical
            assert (horizontal['width'], horizontal['height']) == (380.0, 15.0), horizontal
            for bar in (vertical, horizontal):
                assert bar['found'], native['bars']
                assert bar['leftPadding'] == bar['rightPadding'] == 2.0, bar
                assert bar['topPadding'] == bar['bottomPadding'] == 2.0, bar
            assert native['personal_profile_changed'] is False and native['theme_installed'] is False
            preview_path = next((output / 'home/out/revisions').glob('*/plasma-PREVIEW.json'))
            preview = json.loads(preview_path.read_text(encoding='utf-8'))
            assert preview['guards']['verified'] and preview['status'] == 'closed', preview
            assert preview['exit_code'] == 0, preview
            report = {
                'status': 'passed', 'display': display,
                'preview': str(preview_path), 'backend_preview': preview,
                'runtime': native['runtime'], 'guards': native['guards'],
                'scheme': native['selected_scheme'], 'bars': native['bars'],
                'reference_viewport': native['reference_viewport'], 'expected_geometry': native['expected_geometry'],
                'qml_warnings': native['qml_warnings'],
                'screenshot': str(output / 'home' / Path(native['screenshot']).relative_to(HOME)),
                'screenshot_sha256': native['screenshot_sha256'],
                'profile_changed': native['personal_profile_changed'],
                'theme_installed': native['theme_installed'],
                'limitations': native['limitations'],
                'scope': 'backend route, private KDE scheme/theme snapshot, genuine Plasma Components + KSvg QML render in bwrap/Xvfb; not SR10.4 visual approval',
            }
            report_path = output / 'PLASMA-PUBLIC-PREVIEW-RESULT.json'
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            report_path.chmod(0o600)
            process.terminate()
            process.wait(timeout=8)
            print(json.dumps(report, ensure_ascii=False), flush=True)
            return 0
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            if server and server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=3)


if __name__ == '__main__':
    raise SystemExit(main())
