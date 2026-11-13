#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run backend -> private bwrap -> real Qt5 gallery on an existing Xephyr."""
import configparser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
HOME = '/home/domainos-test'
TEMP = Path.home() / 'tempia' / 'qt5-scrollbar-xephyr'
TEMP.mkdir(mode=0o700, parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend


def wait(predicate, process, environment, timeout=40):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        if process.poll() is not None:
            raise AssertionError(f'private Qt5 backend exited early ({process.returncode})')
        if subprocess.run(['xdpyinfo'], env=environment, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=2).returncode:
            time.sleep(.05)
    raise AssertionError('private Qt5 gallery launch timed out')


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
        'name': 'Qt5 Xephyr scrollbar fixture', 'reference': '',
        'selected_family': 'qt5', 'color_scheme': 'DomainOS-SR10.4',
        'recipes': {},
    }
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    for family in backend.FAMILIES:
        project['recipes'][family] = {
            'geometry': geometry.copy(), 'palette': palette.copy(),
            'visible_categories': (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4),
            'visible_controls': sum(1 << bit for bit in range(16)),
            'selected_control': 10,
            'positions': [[16, 16] for _ in range(16)],
            'sizes': [[0, 0] for _ in range(16)],
        }
    backend.write_json(output / 'home/project.json', project)


def main():
    display = os.environ.get('DISPLAY', '')
    authority_source = os.environ.get('XAUTHORITY')
    if not display.startswith(':') or not authority_source:
        raise RuntimeError('Use DISPLAY/XAUTHORITY da Xephyr existente; este teste não inicia nem encerra X.')
    number = display[1:].split('.', 1)[0]
    socket_path = Path('/tmp/.X11-unix') / ('X' + number)
    if not socket_path.exists():
        raise RuntimeError('O socket do Xephyr existente não está disponível: ' + str(socket_path))
    output = TEMP / ('run-' + uuid.uuid4().hex[:12])
    output.mkdir(mode=0o700)
    print('fixture=' + str(output), flush=True)
    private_fixture(output)
    authority = output / 'Xauthority'
    shutil.copyfile(authority_source, authority)
    authority.chmod(0o600)
    host_environment = dict(os.environ, DISPLAY=display, XAUTHORITY=str(authority))
    if subprocess.run(['xdpyinfo'], env=host_environment, stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL, timeout=3).returncode:
        raise RuntimeError('Não foi possível autenticar no Xephyr já aberto.')
    command = [
        'unshare', '--user', '--map-root-user', '--net', 'bwrap', '--unshare-user',
        '--unshare-ipc', '--unshare-uts', '--uid', '1000', '--gid', '1000', '--clearenv',
        '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
        '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
        '--ro-bind', str(output / 'etc'), '/etc', '--proc', '/proc', '--dev', '/dev',
        '--bind', str(output / 'run'), '/run', '--bind', str(output / 'tmp'), '/tmp',
        '--bind', str(output / 'home'), HOME, '--ro-bind', str(ROOT), '/fixture/root',
        '--ro-bind', str(socket_path), str(socket_path),
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
        'QT_QPA_PLATFORM': 'xcb', 'QT_QPA_PLATFORMTHEME': 'kde',
        'NO_AT_BRIDGE': '1', 'PRIVATE_XEPHYR': '1',
        'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap',
        'IRIX_DOMAINOS_PRIVATE_XEPHYR': '1', 'IRIX_DOMAINOS_SESSION_ROOT': HOME,
        'TMPDIR': '/tmp',
    }
    for key, value in values.items():
        command += ['--setenv', key, value]
    command += [
        '--die-with-parent', '--new-session', '--chdir', HOME, 'dbus-run-session', '--',
        '/usr/bin/python3', '-B', '/fixture/root/tools/theme-lab/backend.py', '--preview',
        '--root', '/fixture/root', '--project', HOME + '/project.json',
        '--output', HOME + '/out', '--kdeglobals', HOME + '/.config/kdeglobals',
        '--family', 'qt5', '--private-test-close-ms', '3500',
    ]
    log_path = output / 'namespace.log'
    with log_path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
        try:
            receipt_path, preview = wait(lambda: next((
                (row, json.loads(row.read_text(encoding='utf-8')))
                for row in (output / 'home/out/revisions').glob('*/qt5-PREVIEW.json')
                if json.loads(row.read_text(encoding='utf-8')).get('status') == 'launched'), None),
                process, host_environment)
            result_path = output / 'home/qt5widgets-proof/RESULTADO.json'
            wait(lambda: json.loads(result_path.read_text(encoding='utf-8'))
                 if result_path.is_file() else None, process, host_environment)
            native = json.loads(result_path.read_text(encoding='utf-8'))
            scrollbar = native['qt5ScrollbarRecipe']
            assert preview['guards']['verified'] and not preview['guards']['personalHomeExposed']
            assert not preview['guards']['systemBusSocketExposed']
            assert scrollbar['applied'] is True
            adapters = scrollbar['scrollSpacingAdapters']
            assert any(row['widgetClass'] == 'QScrollArea' and row['targetGapPx'] == 4
                       and row['finalized'] is True
                       and row['frameAndStyleContributionPx']
                           + row['explicitViewportMarginsPx'][2]
                           + row['addedViewportMarginPx'] == 4
                       for row in adapters)
            assert preview['translated_controls'] == ['arrow', 'check', 'combo', 'entry', 'frame', 'list', 'progress', 'push', 'radio', 'scale_h', 'scale_v', 'scroll_h', 'scroll_v', 'spin', 'text', 'toggle']
            assert native['qt5PushButtonRecipe']['applied'] is True
            assert native['qt5PushButtonRecipe']['objectName'] == 'domainosRecipePushButton'
            assert native['qt5ToggleButtonRecipe']['applied'] is True
            assert native['qt5ToggleButtonRecipe']['objectName'] == 'domainosRecipeToggleButton'
            assert native['qt5ToggleButtonRecipe']['checkable'] is True
            assert native['qt5CheckBoxRecipe']['applied'] is True
            assert native['qt5CheckBoxRecipe']['objectName'] == 'domainosRecipeCheckBox'
            assert native['qt5CheckBoxRecipe']['checkable'] is True
            assert native['qt5CheckBoxRecipe']['initiallyChecked'] is True
            assert native['qt5RadioButtonRecipe']['applied'] is True
            assert native['qt5RadioButtonRecipe']['objectName'] == 'domainosRecipeRadioButton'
            assert native['qt5RadioButtonRecipe']['initiallyChecked'] is True
            assert native['qt5RadioButtonRecipe']['exclusiveGroup'] is True
            assert native['qt5RadioButtonRecipe']['peerObjectName'] == 'domainosRecipeRadioPeer'
            assert native['qt5RadioButtonRecipe']['peerInitiallyChecked'] is False
            assert native['qt5EntryRecipe']['applied'] is True
            assert native['qt5EntryRecipe']['objectName'] == 'domainosRecipeEntry'
            assert native['qt5ComboRecipe']['applied'] is True
            assert native['qt5ComboRecipe']['objectName'] == 'domainosRecipeCombo'
            assert native['qt5ComboRecipe']['popupObjectName'] == 'domainosRecipeComboPopup'
            assert native['qt5SpinRecipe']['applied'] is True
            assert [row['class'] for row in native['qt5SpinRecipe']['widgets']] == ['QSpinBox', 'QDoubleSpinBox']
            assert native['qt5TextRecipe']['applied'] is True
            assert native['qt5TextRecipe']['objectName'] == 'domainosRecipeText'
            text_screenshot = output / 'home/qt5widgets-proof/qt5-textedit.png'
            assert text_screenshot.is_file() and native['textEditScreenshotSaved'], native
            assert native['qt5ScaleRecipe']['applied'] is True
            assert native['qt5ArrowRecipe']['applied'] is True
            assert native['qt5ArrowRecipe']['widgetClass'] == 'RecipeArrowButton'
            assert native['qt5ArrowRecipe']['objectName'] == 'domainosRecipeArrow'
            assert native['qt5ArrowRecipe']['states'] == ['normal', 'pressed while held', 'backdrop', 'disabled', 'focused']
            arrow_screenshot = output / 'home/qt5widgets-proof/qt5-arrow-button.png'
            assert arrow_screenshot.is_file() and native['qt5ArrowScreenshotSaved'], native
            assert native['qt5ProgressRecipe']['applied'] is True
            assert native['qt5ProgressRecipe']['widgetClass'] == 'RecipeProgressBar'
            assert native['qt5ProgressRecipe']['objectName'] == 'domainosRecipeProgress'
            assert native['qt5ProgressRecipe']['value'] == 43
            progress_screenshot = output / 'home/qt5widgets-proof/qt5-progress.png'
            assert progress_screenshot.is_file() and native['qt5ProgressScreenshotSaved'], native
            assert native['qt5ListRecipe']['applied'] is True
            assert native['qt5ListRecipe']['widgetClass'] == 'QTreeWidget'
            assert native['qt5ListRecipe']['rowCount'] == 40
            assert native['qt5ListRecipe']['nativeScrollbars']['vertical']['visible']
            assert native['qt5ListRecipe']['nativeScrollbars']['horizontal']['visible']
            list_screenshot = output / 'home/qt5widgets-proof/qt5-list.png'
            assert list_screenshot.is_file() and native['qt5ListScreenshotSaved'], native
            assert native['qt5FrameRecipe']['applied'] is True
            assert native['qt5FrameRecipe']['widgetClass'] == 'QFrame'
            assert native['qt5FrameRecipe']['frameShadow'] == 48
            frame_screenshot = output / 'home/qt5widgets-proof/qt5-frame.png'
            assert frame_screenshot.is_file() and native['qt5FrameScreenshotSaved'], native
            assert [row['orientation'] for row in native['qt5ScaleRecipe']['widgets']] == ['horizontal', 'vertical']
            scale_screenshot = output / 'home/qt5widgets-proof/qt5-scales.png'
            assert scale_screenshot.is_file() and native['scaleScreenshotSaved'], native
            assert native['checkBoxCheckedScreenshotSaved'] is True
            assert native['checkBoxUncheckedScreenshotSaved'] is True
            vertical = scrollbar['nativeMetrics']['vertical']
            horizontal = scrollbar['nativeMetrics']['horizontal']
            assert vertical['visible'] and vertical['allocation'][0] == 15 and vertical['allocation'][1] > 15, vertical
            assert horizontal['visible'] and horizontal['allocation'][1] == 15 and horizontal['allocation'][0] > 15, horizontal
            for metrics in (vertical, horizontal):
                assert metrics['maximum'] > 0 and metrics['pageStep'] > 0, metrics
            screenshot = output / 'home/qt5widgets-proof/qtwidgets.png'
            assert screenshot.is_file(), native
            push_screenshot = output / 'home/qt5widgets-proof/qt5-pushbutton.png'
            assert push_screenshot.is_file(), native
            toggle_screenshot = output / 'home/qt5widgets-proof/qt5-togglebutton-checked.png'
            assert toggle_screenshot.is_file(), native
            check_checked_screenshot = output / 'home/qt5widgets-proof/qt5-checkbox-checked.png'
            check_unchecked_screenshot = output / 'home/qt5widgets-proof/qt5-checkbox-unchecked.png'
            assert check_checked_screenshot.is_file() and check_unchecked_screenshot.is_file(), native
            radio_checked_screenshot = output / 'home/qt5widgets-proof/qt5-radiobutton-checked.png'
            radio_unchecked_screenshot = output / 'home/qt5widgets-proof/qt5-radiobutton-unchecked.png'
            assert radio_checked_screenshot.is_file() and radio_unchecked_screenshot.is_file(), native
            entry_screenshot = output / 'home/qt5widgets-proof/qt5-entry.png'
            assert entry_screenshot.is_file() and native['entryScreenshotSaved'] is True, native
            combo_screenshot = output / 'home/qt5widgets-proof/qt5-combo.png'
            assert combo_screenshot.is_file() and native['qt5ComboScreenshotSaved'] is True, native
            combo_popup_screenshot = output / 'home/qt5widgets-proof/qt5-combo-popup-selection.png'
            assert combo_popup_screenshot.is_file() and native['qt5ComboPopupSelectionScreenshotSaved'], native
            assert native['qt5ComboPopupSelection']['visible'] and native['qt5ComboPopupSelection']['selected'], native
            spin_screenshot = output / 'home/qt5widgets-proof/qt5-spinboxes.png'
            assert spin_screenshot.is_file() and native['spinScreenshotSaved'], native
            _, final_preview = wait(
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
                      'scrollbars': scrollbar['nativeMetrics'], 'screenshot': str(screenshot),
                      'pushButton': native['qt5PushButtonRecipe'],
                      'toggleButton': native['qt5ToggleButtonRecipe'],
                      'checkBox': native['qt5CheckBoxRecipe'],
                      'radioButton': native['qt5RadioButtonRecipe'],
                      'pushButtonScreenshot': str(push_screenshot),
                      'toggleButtonCheckedScreenshot': str(toggle_screenshot),
                      'checkBoxCheckedScreenshot': str(check_checked_screenshot),
                      'checkBoxUncheckedScreenshot': str(check_unchecked_screenshot),
                      'radioButtonCheckedScreenshot': str(radio_checked_screenshot),
                      'radioButtonUncheckedScreenshot': str(radio_unchecked_screenshot),
                      'entryScreenshot': native.get('entryScreenshot'),
                      'comboBox': native['qt5ComboRecipe'],
                      'comboScreenshot': str(combo_screenshot),
                      'comboPopupSelectionScreenshot': str(combo_popup_screenshot),
                      'comboPopupSelection': native['qt5ComboPopupSelection'],
                      'spinBoxes': native['qt5SpinRecipe'],
                      'spinScreenshot': str(spin_screenshot),
                      'textEdit': native['qt5TextRecipe'],
                      'textScreenshot': str(text_screenshot),
                      'scales': native['qt5ScaleRecipe'],
                      'scaleScreenshot': str(scale_screenshot),
                      'arrow': native['qt5ArrowRecipe'],
                      'arrowScreenshot': str(arrow_screenshot),
                      'progress': native['qt5ProgressRecipe'],
                      'progressScreenshot': str(progress_screenshot),
                      'list': native['qt5ListRecipe'],
                      'listScreenshot': str(list_screenshot),
                      'frame': native['qt5FrameRecipe'],
                      'frameScreenshot': str(frame_screenshot),
                      'scope': 'public Qt5 preview route, KDE-role QSS/assets, real Qt5 check/radio/entry/text/combo/spin/scale/arrow/progress/list/frame/push/scroll widgets, private bwrap over existing Xephyr; not human or historical visual approval'}
            report_path = output / 'QT5-XEPHYR-PREVIEW-RESULT.json'
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            report_path.chmod(0o600)
            print(json.dumps(report, ensure_ascii=False), flush=True)
            return 0
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=3)


if __name__ == '__main__':
    raise SystemExit(main())
