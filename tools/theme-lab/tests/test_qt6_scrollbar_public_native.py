#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise backend -> private bwrap -> real Qt6 gallery with scrollbar recipe."""
import configparser
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HOME = '/home/domainos-test'
SCRATCH = Path.home() / 'tempia'
SCRATCH.mkdir(mode=0o700, parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend


def wait(predicate, process, environment, timeout=65):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        if process.poll() is not None:
            raise AssertionError(f'private backend exited early ({process.returncode})')
        if subprocess.run(['xdpyinfo'], env=environment, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=2).returncode:
            time.sleep(.05)
    raise AssertionError('private Qt6 gallery launch timed out')


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
        'name': 'Qt6 public scrollbar fixture', 'reference': '',
        'selected_family': 'qt6', 'color_scheme': 'DomainOS-SR10.4',
        'recipes': {},
    }
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    for family in backend.FAMILIES:
        project['recipes'][family] = {
            'geometry': geometry.copy(), 'palette': palette.copy(),
            'visible_categories': (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4),
            'visible_controls': (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6) | (1 << 7) | (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11) | (1 << 12) | (1 << 13) | (1 << 14) | (1 << 15),
            'selected_control': 0,
            'positions': [[16, 16] for _ in range(16)],
            'sizes': [[0, 0] for _ in range(16)],
        }
    backend.write_json(output / 'home/project.json', project)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-display', help='use an already running Xephyr display without managing its lifetime')
    parser.add_argument('--xauthority', type=Path, help='Xauthority file for --reuse-display')
    parser.add_argument('--preview-ms', type=int, default=5000,
                        help='maximum time the private gallery remains visible')
    args = parser.parse_args()
    output = Path(tempfile.mkdtemp(prefix='i170-qt6-public-', dir=SCRATCH))
    print('fixture=' + str(output), flush=True)
    private_fixture(output)
    if not 1500 <= args.preview_ms <= 120000:
        raise ValueError('--preview-ms must be between 1500 and 120000')
    if args.reuse_display:
        match = re.fullmatch(r':([0-9]+)(?:\.[0-9]+)?', args.reuse_display)
        if not match or args.xauthority is None or not args.xauthority.is_file():
            raise ValueError('--reuse-display requires a local :N display and its existing Xauthority file')
        number = int(match.group(1))
        display = args.reuse_display
        authority = args.xauthority.resolve()
        server = None
    else:
        number = next(n for n in range(180, 4096)
                      if not Path(f'/tmp/.X{n}-lock').exists() and not Path(f'/tmp/.X11-unix/X{n}').exists())
        display = f':{number}'
        authority = output / 'Xauthority'
        authority.touch(mode=0o600)
        subprocess.run(['xauth', '-f', str(authority), 'add', display, '.', secrets.token_hex(16)], check=True)
        server = None
    host_environment = dict(os.environ, DISPLAY=display, XAUTHORITY=str(authority))
    process = None
    log_path = output / 'namespace.log'
    with log_path.open('w', encoding='utf-8') as log:
        try:
            if args.reuse_display:
                if subprocess.run(['xdpyinfo'], env=host_environment,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  timeout=2).returncode:
                    raise RuntimeError('the requested existing Xephyr display is unavailable')
            else:
                server = subprocess.Popen(['/usr/bin/Xvfb', display, '-screen', '0', '900x700x24',
                                           '-nolisten', 'tcp', '-auth', str(authority)],
                                          stdout=log, stderr=log, start_new_session=True)
                wait(lambda: True if subprocess.run(['xdpyinfo'], env=host_environment,
                                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                                     timeout=2).returncode == 0 else None,
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
                'QT_QPA_PLATFORM': 'xcb',
                'NO_AT_BRIDGE': '1', 'PRIVATE_XEPHYR': '1',
                'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap',
                'IRIX_DOMAINOS_PRIVATE_XEPHYR': '1', 'IRIX_DOMAINOS_SESSION_ROOT': HOME,
            }
            for key, value in values.items():
                command += ['--setenv', key, value]
            command += [
                '--die-with-parent', '--new-session', '--chdir', HOME, 'dbus-run-session', '--',
                '/usr/bin/python3', '-B', '/fixture/root/tools/theme-lab/backend.py', '--preview',
                '--root', '/fixture/root', '--project', HOME + '/project.json',
                '--output', HOME + '/out', '--kdeglobals', HOME + '/.config/kdeglobals',
                '--family', 'qt6', '--private-test-close-ms', str(args.preview_ms),
            ]
            process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
            def loaded_preview():
                rows = list((output / 'home/out/revisions').glob('*/qt6-PREVIEW.json'))
                for row in rows:
                    try:
                        proof = json.loads(row.read_text(encoding='utf-8'))
                        if proof.get('status') == 'launched':
                            return row, proof
                    except (OSError, json.JSONDecodeError):
                        pass
                return None
            receipt_path, preview = wait(loaded_preview, process, host_environment)
            result_path = output / 'home/qtwidgets-proof/RESULTADO.json'
            wait(lambda: json.loads(result_path.read_text(encoding='utf-8'))
                 if result_path.is_file() else None, process, host_environment)
            native = json.loads(result_path.read_text(encoding='utf-8'))
            scrollbar = native['qt6ScrollbarRecipe']
            push_button = native['qt6PushButtonRecipe']
            toggle_button = native['qt6ToggleButtonRecipe']
            check_box = native['qt6CheckBoxRecipe']
            radio = native['qt6RadioButtonRecipe']
            entry = native['qt6EntryRecipe']
            text = native['qt6TextRecipe']
            combo = native['qt6ComboRecipe']
            spin = native['qt6SpinRecipe']
            scale = native['qt6ScaleRecipe']
            scale_v = native['qt6ScaleVRecipe']
            arrow = native['qt6ArrowRecipe']
            progress = native['qt6ProgressRecipe']
            listing = native['qt6ListRecipe']
            frame = native['qt6FrameRecipe']
            assert preview['guards']['verified'] and not preview['guards']['personalHomeExposed']
            assert scrollbar['applied'] is True
            adapters = scrollbar['scrollSpacingAdapters']
            assert any(row['widgetClass'] == 'QScrollArea' and row['targetGapPx'] == 4
                       and row['finalized'] is True
                       and row['frameAndStyleContributionPx']
                           + row['explicitViewportMarginsPx'][2]
                           + row['addedViewportMarginPx'] == 4
                       for row in adapters)
            assert push_button['applied'] is True
            assert push_button['objectName'] == 'domainosRecipePushButton'
            assert toggle_button['applied'] is True
            assert toggle_button['objectName'] == 'domainosRecipeToggleButton'
            assert toggle_button['checkable'] is True
            assert native['toggleButtonScreenshotSaved'] is True
            assert check_box['applied'] is True
            assert check_box['objectName'] == 'domainosRecipeCheckBox'
            assert check_box['checkable'] is True
            assert native['checkBoxCheckedScreenshotSaved'] is True
            assert native['checkBoxUncheckedScreenshotSaved'] is True
            assert radio['applied'] is True
            assert radio['objectName'] == 'domainosRecipeRadioButton'
            assert radio['exclusiveGroup'] is True
            assert radio['peerObjectName'] == 'domainosRecipeRadioPeer'
            assert native['radioButtonCheckedScreenshotSaved'] is True
            assert native['radioButtonUncheckedScreenshotSaved'] is True
            assert entry['applied'] is True
            assert entry['objectName'] == 'domainosRecipeEntry'
            assert entry['scope'].startswith('one real QLineEdit')
            assert native['qt6EntryScreenshotSaved'] is True
            assert text['applied'] is True
            assert text['objectName'] == 'domainosRecipeText'
            assert text['backdropSelector'] == '[domainosBackdrop="true"]'
            assert text['backdropTracksTopLevelActivation'] is True
            assert native['qt6TextScreenshotSaved'] is True
            assert combo['applied'] is True
            assert combo['objectName'] == 'domainosRecipeCombo'
            assert combo['popupObjectName'] == 'domainosRecipeComboPopup'
            assert native['qt6ComboScreenshotSaved'] is True
            assert native['qt6ComboPopupSelectionScreenshotSaved'] is True
            assert native['qt6ComboPopupSelection']['visible'] is True
            assert native['qt6ComboPopupSelection']['selectedIndex'] == 1
            assert native['qt6ComboPopupSelection']['selected'] is True
            assert spin['applied'] is True
            assert [row['objectName'] for row in spin['widgets']] == [
                'domainosRecipeSpinBox', 'domainosRecipeDoubleSpinBox']
            assert native['qt6SpinScreenshotSaved'] is True
            assert scale['applied'] is True
            assert scale['widgetClass'] == 'QSlider'
            assert scale['objectName'] == 'domainosRecipeScaleHorizontal'
            assert scale['orientation'] == 'horizontal'
            assert scale['backdropSelector'] == '[domainosBackdrop="true"]'
            assert scale['backdropTracksTopLevelActivation'] is True
            assert native['qt6ScaleScreenshotSaved'] is True
            assert scale_v['applied'] is True
            assert scale_v['widgetClass'] == 'QSlider'
            assert scale_v['objectName'] == 'domainosRecipeScaleVertical'
            assert scale_v['orientation'] == 'vertical'
            assert scale_v['backdropSelector'] == '[domainosBackdrop="true"]'
            assert scale_v['backdropTracksTopLevelActivation'] is True
            assert native['qt6ScaleVScreenshotSaved'] is True
            assert arrow['applied'] is True
            assert arrow['objectName'] == 'domainosRecipeArrow'
            assert arrow['widgetClass'] == 'RecipeArrowButton'
            assert arrow['size'] == [15, 15] and arrow['glyphSize'] == 11
            assert arrow['backdropTracksTopLevelActivation'] is True
            assert native['qt6ArrowScreenshotSaved'] is True
            assert progress['applied'] is True
            assert progress['objectName'] == 'domainosRecipeProgress'
            assert progress['widgetClass'] == 'RecipeProgressBar'
            assert progress['range'] == [0, 100] and progress['value'] == 43
            assert progress['textColorSource'].startswith('KDE view ink role')
            assert native['qt6ProgressScreenshotSaved'] is True
            assert listing['applied'] is True
            assert listing['widgetClass'] == 'QTreeWidget'
            assert listing['rowCount'] == 40
            assert listing['selectionMode'] == 'single row'
            assert listing['backdropTracksTopLevelActivation'] is True
            assert listing['nativeScrollbars']['vertical']['visible'] is True
            assert listing['nativeScrollbars']['horizontal']['visible'] is True
            assert native['qt6ListScreenshotSaved'] is True
            assert frame['applied'] is True
            assert frame['objectName'] == 'domainosRecipeFrame'
            assert frame['widgetClass'] == 'QFrame'
            assert frame['frameShape'] == 2 and frame['frameShadow'] == 48
            assert frame['lineWidth'] == 2
            assert frame['backdropSelector'] == '[domainosBackdrop="true"]'
            assert frame['backdropTracksTopLevelActivation'] is True
            assert native['qt6FrameScreenshotSaved'] is True
            assert preview['translated_controls'] == ['arrow', 'check', 'combo', 'entry', 'frame', 'list', 'progress', 'push', 'radio', 'scale_h', 'scale_v', 'scroll_h', 'scroll_v', 'spin', 'text', 'toggle']
            vertical = scrollbar['nativeMetrics']['vertical']
            horizontal = scrollbar['nativeMetrics']['horizontal']
            assert vertical['visible'] and vertical['allocation'][0] == 15 and vertical['allocation'][1] > 15, vertical
            assert horizontal['visible'] and horizontal['allocation'][1] == 15 and horizontal['allocation'][0] > 15, horizontal
            for metrics in (vertical, horizontal):
                assert metrics['maximum'] > 0 and metrics['pageStep'] > 0, metrics
            screenshot = output / 'home/qtwidgets-proof/qtwidgets.png'
            assert screenshot.is_file(), native
            receipt_path, final_preview = wait(
                lambda: (receipt_path, json.loads(receipt_path.read_text(encoding='utf-8')))
                if json.loads(receipt_path.read_text(encoding='utf-8')).get('status') in ('closed', 'failed')
                else None,
                process, host_environment, timeout=20)
            process.wait(timeout=10)
            assert process.returncode == 0, (process.returncode, log_path.read_text())
            assert final_preview['status'] == 'closed' and final_preview['exit_code'] == 0, final_preview
            report = {'status': 'passed', 'display': display, 'backend_preview': final_preview,
                      'guards': native['guards'], 'qt': {key: native[key] for key in
                      ('qtVersion', 'pyqtVersion', 'platform', 'style')},
                      'scrollbars': scrollbar['nativeMetrics'], 'pushButton': push_button,
                      'toggleButton': toggle_button,
                      'checkBox': check_box,
                      'radioButton': radio,
                      'entry': entry,
                      'combo': combo,
                      'spin': spin,
                      'text': text,
                      'arrow': arrow,
                      'progress': progress,
                      'list': listing,
                      'scale': scale,
                      'scale_v': scale_v,
                      'screenshot': str(screenshot),
                      'scope': 'public preview route, generated KDE-role QSS, genuine Qt6 widgets in private bwrap; Xvfb or reused Xephyr; not historical visual approval'}
            report_path = output / 'QT6-PUBLIC-PREVIEW-RESULT.json'
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            report_path.chmod(0o600)
            print(json.dumps(report, ensure_ascii=False), flush=True)
            return 0
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=3)
            if server and server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill(); server.wait(timeout=3)


if __name__ == '__main__':
    raise SystemExit(main())
