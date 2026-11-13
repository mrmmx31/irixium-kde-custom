#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real controller, native spin input and GTK3 generation in disposable bwrap/Xvfb.

Requires the test-only controller_spin_probe binary passed on the command line.
Only the owned display socket and disposable home are exposed to the namespace.
"""
import json
import hashlib
import importlib.util
import os
import re
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HOME = '/home/domainos-test'


def wait(predicate, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.1)
    raise AssertionError('Timeout waiting for native controller/preview condition')


def stop_fixture_controller(display):
    """Ask only this fixture's controller to close its own preview groups."""
    expected_probe = (HOME + '/probe.json').encode()
    expected_display = ('DISPLAY=' + display).encode()
    pids = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            command = (entry / 'cmdline').read_bytes().split(b'\0')
            environment = (entry / 'environ').read_bytes().split(b'\0')
            if (command and command[0] == b'/fixture/probe' and
                    b'--work-dir' in command and HOME.encode() + b'/lab' in command and
                    expected_display in environment and
                    b'TL_SPIN_PROBE=' + expected_probe in environment):
                pids.append(int(entry.name))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    for pid in pids:
        try:
            descriptor = os.pidfd_open(pid)
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            finally:
                os.close(descriptor)
        except (ProcessLookupError, PermissionError):
            continue
    deadline = time.monotonic() + 5
    while pids and time.monotonic() < deadline:
        pids = [pid for pid in pids if Path(f'/proc/{pid}').exists()]
        time.sleep(.05)
    return pids


def main():
    binary = Path(sys.argv[1]).resolve(strict=True)
    gtk4_all_controls_mode = '--gtk4-all-controls-route' in sys.argv[2:]
    gtk4_states_mode = '--gtk4-states' in sys.argv[2:]
    gtk4_toggle_visibility = '--gtk4-toggle-visibility' in sys.argv[2:]
    gtk4_toggle_persistence = '--gtk4-toggle-persistence' in sys.argv[2:]
    gtk4_toggle_states = '--gtk4-toggle-states' in sys.argv[2:]
    gtk4_toggle_mode = '--gtk4-toggle' in sys.argv[2:] or gtk4_toggle_visibility or gtk4_toggle_persistence or gtk4_toggle_states
    gtk4_push_mode = ('--gtk4-push' in sys.argv[2:] or gtk4_states_mode or
                      gtk4_toggle_mode or gtk4_all_controls_mode)
    separate_gtk3_mode = '--separate-persistence-gtk3' in sys.argv[2:]
    paint_gtk3_sample_mode = '--paint-gtk3-sample' in sys.argv[2:]
    paint_gtk2_sample_mode = '--paint-gtk2-sample' in sys.argv[2:]
    gtk2_frame_control = '--gtk2-frame-control' in sys.argv[2:]
    gtk2_list_control = '--gtk2-list-control' in sys.argv[2:]
    arrow_pressure_mode = '--gtk2-arrow-pressure' in sys.argv[2:]
    gtk2_arrow_control = '--gtk2-arrow-control' in sys.argv[2:] or arrow_pressure_mode
    gtk2_scale_control = 8 if '--gtk2-scale-h-control' in sys.argv[2:] else 9 if '--gtk2-scale-v-control' in sys.argv[2:] else 0
    gtk2_spin_control_mode = '--gtk2-spin-control' in sys.argv[2:]
    gtk2_combo_mode = '--gtk2-combo-control' in sys.argv[2:]
    gtk2_text_mode = '--gtk2-text-control' in sys.argv[2:]
    gtk2_entry_mode = '--gtk2-entry-control' in sys.argv[2:]
    gtk2_progress_mode = '--gtk2-progress' in sys.argv[2:]
    gtk2_push_mode = '--gtk2-push' in sys.argv[2:]
    pressure_mode = '--gtk2-pressure' in sys.argv[2:] or arrow_pressure_mode
    gtk2_push_mode = gtk2_push_mode or (pressure_mode and not arrow_pressure_mode)
    gtk2_toggle_mode = '--gtk2-toggle' in sys.argv[2:]
    gtk2_radio_mode = '--gtk2-radio' in sys.argv[2:]
    gtk2_check_mode = '--gtk2-check' in sys.argv[2:]
    gtk2_launch_mode = '--gtk2-anchor' in sys.argv[2:] or '--gtk2-launch' in sys.argv[2:] or paint_gtk2_sample_mode or gtk2_push_mode or gtk2_toggle_mode or gtk2_radio_mode or gtk2_check_mode or gtk2_progress_mode or gtk2_entry_mode or gtk2_text_mode or gtk2_combo_mode or gtk2_spin_control_mode or gtk2_scale_control or gtk2_arrow_control or gtk2_list_control or gtk2_frame_control
    button_relief_mode = '--button-relief' in sys.argv[2:]
    trough_relief_mode = '--trough-relief' in sys.argv[2:]
    thumb_relief_mode = '--thumb-relief' in sys.argv[2:]
    fitting_relief_mode = '--fitting-relief' in sys.argv[2:]
    readiness_mode = '--preview-readiness' in sys.argv[2:]
    relief_mode = '--relief' in sys.argv[2:] or button_relief_mode or trough_relief_mode or thumb_relief_mode or fitting_relief_mode or readiness_mode
    history_mode = '--project-history' in sys.argv[2:]
    project_io_mode = '--project-io' in sys.argv[2:]
    gtk_transfer_mode = '--project-transfer-gtk' in sys.argv[2:]
    gtk_resume_mode = '--project-resume-gtk' in sys.argv[2:] or gtk_transfer_mode
    journal_capacity_mode = '--journal-capacity' in sys.argv[2:]
    quit_recovery_mode = '--quit-recovery' in sys.argv[2:] or journal_capacity_mode
    editor_mode = '--editor' in sys.argv[2:] or quit_recovery_mode
    axis_limits = '--axis-limits' in sys.argv[2:]
    anchor_mode = '--anchor' in sys.argv[2:] or '--gtk2-anchor' in sys.argv[2:]
    comparison_mode = '--comparison' in sys.argv[2:]
    preview_stack_layout_mode = '--preview-stack-layout' in sys.argv[2:]
    axis_mode = '--axis-lock' in sys.argv[2:] or axis_limits
    fitting_mode = '--piece-fitting' in sys.argv[2:]
    thumb_mode = '--piece-thumb' in sys.argv[2:] or fitting_mode
    trough_mode = '--piece-trough' in sys.argv[2:] or thumb_mode
    piece_mode = '--piece' in sys.argv[2:] or '--piece-button' in sys.argv[2:] or trough_mode
    button_mode = '--piece-button' in sys.argv[2:] or trough_mode
    scheme = sys.argv[sys.argv.index('--scheme')+1] if '--scheme' in sys.argv else 'DomainOS-SR10.4'
    if scheme not in ('DomainOS-SR10.4','BreezeLight','BreezeDark','TestYellow'):
        raise ValueError('Only explicitly named private palette fixtures are accepted')
    # Keep disposable fixtures in the user's task temp area. A supplied
    # Xephyr may be reused when a private X server cannot be created.
    output_root = Path(os.environ.get('TL_TEST_OUTPUT_DIR', Path.home() / 'tempia'))
    output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    output = Path(tempfile.mkdtemp(prefix='theme-lab-spin-', dir=output_root))
    print(output, flush=True)
    for directory in ('home', 'etc', 'run/user/1000', 'tmp', 'home/.config',
                      'home/.local/share', 'home/.local/state', 'home/.cache'):
        (output / directory).mkdir(parents=True, mode=0o700, exist_ok=True)
    (output / 'etc/passwd').write_text(f'domainos-test:x:1000:1000:Preview:{HOME}:/usr/sbin/nologin\n')
    (output / 'etc/group').write_text('domainos-test:x:1000:\n')
    (output / 'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    (output / 'etc/domainos-preview').touch()
    for source in ('/etc/fonts', '/etc/ld.so.cache', '/etc/alternatives'):
        path = Path(source)
        if path.is_dir():
            (output / 'etc' / path.name).mkdir()
        elif path.exists():
            (output / 'etc' / path.name).touch()
    shutil.copyfile(ROOT / 'colors/DomainOS-SR10.4.colors', output / 'home/.config/kdeglobals')
    if scheme == 'TestYellow':
        import configparser
        palette=configparser.ConfigParser(interpolation=None);palette.optionxform=str
        palette.read(ROOT/'colors/DomainOS-SR10.4.colors')
        palette['General']['Name']='Artificial yellow test'
        for section in ('Colors:Window','Colors:Button','Colors:View'):
            palette[section]['BackgroundNormal']='236,216,112'
            palette[section]['BackgroundAlternate']='216,196,92'
            palette[section]['ForegroundNormal']='32,28,12'
        palette['Colors:Selection']['BackgroundNormal']='88,72,24'
        palette['Colors:Selection']['ForegroundNormal']='255,248,216'
        directory=output/'home/.local/share/color-schemes';directory.mkdir(parents=True)
        with (directory/'TestYellow.colors').open('w') as f:palette.write(f)
    if journal_capacity_mode:
        from controller_quit_recovery import seed_journal
        seed_journal(output)
    requested_display = os.environ.get('TL_TEST_DISPLAY')
    if requested_display:
        display = requested_display
        number = int(display.rsplit(':', 1)[1].split('.', 1)[0])
        authority = Path(os.environ['TL_TEST_XAUTHORITY']).resolve(strict=True)
        server = None
    else:
        number = next((n for n in range(180, 4096) if not Path(f'/tmp/.X{n}-lock').exists()
                       and not Path(f'/tmp/.X11-unix/X{n}').exists()), None)
        if number is None:
            raise RuntimeError('Nenhum display privado livre; sessões existentes preservadas.')
        display = f':{number}'
        authority = output / 'Xauthority'
        authority.touch(mode=0o600)
        subprocess.run(['xauth', '-f', str(authority), 'add', display, '.', secrets.token_hex(16)], check=True)
    environment = dict(os.environ, DISPLAY=display, XAUTHORITY=str(authority))
    server = container = None
    log = (output / 'namespace.log').open('w')
    results = {}
    try:
        if server is None and not requested_display:
            xvfb_command = ['Xvfb', display, '-screen', '0', '2200x1200x24',
                            '-nolisten', 'tcp']
            if gtk2_launch_mode:
                # The GTK2 client runs inside bwrap's private IPC namespace,
                # while this fixture-owned Xvfb stays in the host namespace.
                # MIT-SHM would therefore fail XShmAttach with BadAccess;
                # keep IPC isolation and exercise the ordinary X image path.
                xvfb_command += ['-extension', 'MIT-SHM']
            xvfb_command += ['-auth', str(authority)]
            server = subprocess.Popen(xvfb_command,
                                      stdout=log, stderr=log, start_new_session=True)
        wait(lambda: (server is None or server.poll() is None) and subprocess.run(['xdpyinfo'], env=environment,
             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0, 10)
        command = ['unshare', '--user', '--map-root-user', '--net', 'bwrap', '--unshare-user',
                   '--unshare-ipc', '--unshare-uts', '--uid', '1000', '--gid', '1000', '--clearenv',
                   '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
                   '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
                   '--ro-bind', str(output / 'etc'), '/etc', '--proc', '/proc', '--dev', '/dev',
                   '--bind', str(output / 'run'), '/run', '--bind', str(output / 'tmp'), '/tmp',
                   '--bind', str(output / 'home'), HOME, '--ro-bind', str(ROOT), '/fixture/root',
                   '--ro-bind', str(binary), '/fixture/probe',
                   '--ro-bind', f'/tmp/.X11-unix/X{number}', f'/tmp/.X11-unix/X{number}',
                   '--ro-bind', str(authority), HOME + '/.Xauthority']
        for source in ('/etc/fonts', '/etc/ld.so.cache', '/etc/alternatives'):
            if Path(source).exists():
                command += ['--ro-bind', source, source]
        private_environment = {
            'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8', 'HOME': HOME,
            'DISPLAY': display, 'XAUTHORITY': HOME + '/.Xauthority',
            'XDG_CONFIG_HOME': HOME + '/.config', 'XDG_DATA_HOME': HOME + '/.local/share',
            'XDG_STATE_HOME': HOME + '/.local/state', 'XDG_CACHE_HOME': HOME + '/.cache',
            'XDG_RUNTIME_DIR': '/run/user/1000', 'GDK_BACKEND': 'x11', 'NO_AT_BRIDGE': '1',
            'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap', 'PRIVATE_XEPHYR': '1',
            'IRIX_DOMAINOS_PRIVATE_XEPHYR': '1', 'IRIX_DOMAINOS_SESSION_ROOT': HOME,
            'TL_SPIN_GTK2': '1' if gtk2_launch_mode else '0',
            'TL_SPIN_GTK4_PUSH': '1' if gtk4_push_mode else '0',
            'TL_SPIN_GTK4_TOGGLE': '1' if gtk4_toggle_mode else '0',
            'TL_SPIN_GTK4_ALL': '1' if gtk4_all_controls_mode else '0',
            'TL_SPIN_SEPARATE_GTK3': '1' if separate_gtk3_mode else '0',
            'TL_SPIN_GTK2_FRAME_CONTROL': '1' if gtk2_frame_control else '0',
            'TL_SPIN_GTK2_LIST_CONTROL': '1' if gtk2_list_control else '0',
            'TL_SPIN_GTK2_ARROW_CONTROL': '1' if gtk2_arrow_control else '0',
            'TL_SPIN_GTK2_SCALE_CONTROL': str(gtk2_scale_control),
            'TL_SPIN_GTK2_SPIN_CONTROL': '1' if gtk2_spin_control_mode else '0',
            'TL_SPIN_GTK2_COMBO_CONTROL': '1' if gtk2_combo_mode else '0',
            'TL_SPIN_GTK2_TEXT_CONTROL': '1' if gtk2_text_mode else '0',
            'TL_SPIN_GTK2_ENTRY_CONTROL': '1' if gtk2_entry_mode else '0',
            'TL_SPIN_GTK2_PROGRESS': '1' if gtk2_progress_mode else '0',
            'TL_SPIN_GTK2_PUSH': '1' if gtk2_push_mode else '0',
            'TL_SPIN_GTK2_TOGGLE': '1' if gtk2_toggle_mode else '0',
            'TL_SPIN_GTK2_RADIO': '1' if gtk2_radio_mode else '0',
            'TL_SPIN_GTK2_CHECK': '1' if gtk2_check_mode else '0',
            'TL_SPIN_FIXTURE': HOME + '/fixture.json', 'TL_SPIN_PROBE': HOME + '/probe.json',
            'TL_SPIN_COMMAND': HOME + '/reveal-spin', 'TL_SPIN_SCHEME_ID': scheme,
            'TL_SPIN_IMPORT_GATE': HOME + '/import-gate',
            'TL_SPIN_GENERATE_GATE': HOME + '/generate-gate',
        }
        for key, value in private_environment.items():
            command += ['--setenv', key, value]
        command += ['--die-with-parent', '--new-session', '--chdir', HOME,
                    'dbus-run-session', '--', '/fixture/probe', '--root', '/fixture/root',
                    '--work-dir', HOME + '/lab', '--project', HOME + '/fixture.json', '--family', 'gtk4' if gtk4_push_mode else 'gtk2' if gtk2_launch_mode else 'motif' if editor_mode or project_io_mode else 'gtk3']
        if gtk4_push_mode:
            command += ['--gtk4-host-bridge','/fixture/root/.qa-t04-anchor-foundation/gtk4-host-build/libtheme-lab-gtk4-host.so']
        container = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)

        def observation():
            if container.poll() is not None:
                raise AssertionError(f'Controller namespace exited {container.returncode}; see {output}/namespace.log')
            try:
                return json.loads((output / 'home/probe.json').read_text())
            except (OSError, json.JSONDecodeError):
                return {}

        def click(key, arrow=False):
            menu_actions = {
                'apply', 'save', 'load', 'export', 'import_delta',
                'reconstruct_files', 'manual_paint', 'quit',
                'projectUndo', 'projectRedo', 'projectMark',
                'projectRestore', 'projectResetPart'
            }
            if key in menu_actions:
                command_file = output / 'home/reveal-spin'
                command_file.write_text(f'action {key}')
                wait(lambda: not command_file.exists(), 5)
                return
            if key in ("automaticPreview", "separatePreview"):
                (output / "home/reveal-spin").write_text("automatic" if key == "automaticPreview" else "separate")
                wait(lambda: not (output / "home/reveal-spin").exists(), 5)
                wait(lambda: observation()[key][1] >= 0, 5)
            x, y, width, height = observation()[key]
            # --sync can wait indefinitely when the pointer is already at
            # the same coordinates. X11 requests are ordered; wait for the
            # observed widget/controller change instead of a new motion event.
            subprocess.run(['xdotool', 'mousemove', str(x + width + 8 if arrow else x + width//2),
                            str(y + height//4 if arrow else y + height//2), 'click', '1'],
                           env=environment, check=True, timeout=10)

        def allocated(width, height, both=False):
            value = observation().get('metrics', '')
            measurements = re.findall(r'GTK3 (?:acoplado|separado): (\d+) x (\d+)',value)
            count = sum((int(w),int(h)) == (width,height) for w,h in measurements)
            return value if count >= (2 if both else 1) else None

        def move_separate():
            if gtk2_launch_mode:
                from controller_gtk2_windows import native_windows
                windows = native_windows(observation, environment)
                moved = 0
                for window in windows:
                    tree = subprocess.check_output(['xwininfo','-id',window,'-tree'],env=environment,text=True,timeout=5)
                    root = re.search(r'Root window id: (0x[0-9a-f]+)',tree)
                    parent = re.search(r'Parent window id: (0x[0-9a-f]+)',tree)
                    if root and parent and root[1] == parent[1]:
                        subprocess.run(['xdotool','windowmove',window,'1400','0'],env=environment,check=True,timeout=5)
                        moved += 1
                assert moved == 1, 'Exactly one detached GTK2 window must move'
                return
            pattern = '^Theme Lab — GTK3 nativo privado$'
            matches = subprocess.run(['xdotool', 'search', '--sync', '--onlyvisible',
                                      '--name', pattern],
                                     env=environment, check=True, text=True,
                                     capture_output=True, timeout=8).stdout.split()
            assert len(matches) == 1, f'Expected one detached GTK3 window, found {len(matches)}'
            geometry = subprocess.check_output(['xdpyinfo'], env=environment, text=True, timeout=5)
            dimensions = re.search(r'dimensions:\s+(\d+)x(\d+) pixels', geometry)
            assert dimensions, 'Could not read the supplied X display dimensions'
            x = max(0, int(dimensions.group(1)) - 800)
            subprocess.run(['xdotool', 'windowmove', matches[0], str(x), '0'],
                           env=environment, check=True, timeout=5)

        def edit(key, value):
            # Limit fixtures use the public native setter and real valueChanged
            # callback. The two spin cases above use actual X11 pointer input.
            axis = 'width' if 'Width' in key else 'height'
            (output / 'home/reveal-spin').write_text(f'set-{axis} {value}')
            wait(lambda: observation().get('width_text' if 'Width' in key else 'height_text') == str(value), 5)

        def matching_native(request):
            scene = output / 'home/lab/scene.json'
            try:
                applied = json.loads(scene.read_text())['recipes']['gtk3']['sizes'][0]
                if applied != [request, request] or (output / 'home/probe.json').stat().st_mtime_ns < scene.stat().st_mtime_ns:
                    return None
            except (OSError, json.JSONDecodeError):
                return None
            text = observation().get('metrics', '')
            if f'Pedido em edição: {request} x {request} ' not in text:
                return None
            values = re.findall(r'GTK3 (?:acoplado|separado): (\d+) x (\d+)(?: px lógicos)?', text)
            if len(values) != 2 or values[0] != values[1]:
                return None
            return tuple(map(int, values[0]))

        if preview_stack_layout_mode:
            keys = ('preview_stack', 'preview_clip', 'preview_native_scroll',
                    'preview_motif_scroll')
            initial = wait(lambda: ({key: observation()[key] for key in keys}
                                    if (all(key in observation() for key in keys) and
                                        abs(observation()['preview_stack'][2] -
                                            observation()['preview_clip'][2]) <= 2 and
                                        observation()['preview_native_scroll'][2] > 100 and
                                        observation()['preview_motif_scroll'][2] > 100)
                                    else None), 15)
            base_native = initial['preview_native_scroll'][3]
            base_motif = initial['preview_motif_scroll'][3]
            base_stack_width = initial['preview_stack'][2]
            base_native_width = initial['preview_native_scroll'][2]
            base_motif_width = initial['preview_motif_scroll'][2]
            assert base_native >= 370 and base_motif >= 240, initial
            subprocess.run(['xdotool', 'windowsize', str(observation()['window']),
                            '2200', '1100'], env=environment, check=True, timeout=10)
            grown = wait(lambda: ({key: observation()[key] for key in keys}
                                  if (all(key in observation() for key in keys) and
                                      observation()['preview_native_scroll'][3] > base_native and
                                      observation()['preview_motif_scroll'][3] > base_motif and
                                      observation()['preview_stack'][2] > base_stack_width and
                                      observation()['preview_native_scroll'][2] > base_native_width and
                                      observation()['preview_motif_scroll'][2] > base_motif_width)
                                  else None), 15)
            assert grown['preview_stack'][2] >= grown['preview_clip'][2], grown
            native_delta = grown['preview_native_scroll'][3] - base_native
            motif_delta = grown['preview_motif_scroll'][3] - base_motif
            assert abs(native_delta * base_motif - motif_delta * base_native) <= \
                   base_native + base_motif, (initial, grown)
            subprocess.run(['xdotool', 'windowsize', str(observation()['window']),
                            '1280', '800'], env=environment, check=True, timeout=10)
            restored = wait(lambda: ({key: observation()[key] for key in keys}
                                     if (all(key in observation() for key in keys) and
                                         observation()['preview_native_scroll'][3] == base_native and
                                         observation()['preview_motif_scroll'][3] == base_motif and
                                         abs(observation()['preview_stack'][2] -
                                             observation()['preview_clip'][2]) <= 2 and
                                         observation()['preview_native_scroll'][2] <
                                             grown['preview_native_scroll'][2] and
                                         observation()['preview_motif_scroll'][2] <
                                             grown['preview_motif_scroll'][2])
                                     else None), 15)
            results.update(status='passed',
                           scope='Center preview viewports keep native minima and share only maximized vertical surplus proportionally; canvases remain 1:1 and independently scrollable.',
                           initial=initial, grown=grown, restored=restored,
                           native_and_motif_both_grow=True,
                           horizontal_unused_strip_removed=True,
                           proportional_surplus=True,
                           minimum_restored=True,
                           historical_fidelity_claimed=False)
            print(json.dumps(results, ensure_ascii=False), flush=True)
            return

        if paint_gtk3_sample_mode:
            wait(lambda:any(not row.get('separate') for row in observation().get('native_bars',[])),30)
            wait(lambda:observation().get('manual_paint'))
            click('manual_paint')
            label=wait(lambda:(value if 'GTK3 / amostra nativa atual /' in (value:=observation().get('paint_native_label','')) else None),30)
            assert '1:1' in label and 'px' in label, label
            subprocess.run(['import','-display',display,'-window','root',str(output/'gtk3-native-sample.png')],env=environment,check=True,timeout=10)
            results.update(status='passed',scope='Manual Paint uses a real GTK3 offscreen widget sample for the selected control/state, at native pixel size; Motif reference remains independent',
                           native_label=label,widget_source='native_gtk3',historical_fidelity_claimed=False)
            print(json.dumps(results,ensure_ascii=False),flush=True)
            return

        if paint_gtk2_sample_mode:
            wait(lambda:any(not row.get('separate') for row in observation().get('native_bars',[])),30)
            wait(lambda:observation().get('manual_paint'))
            click('manual_paint')
            label=wait(lambda:(value if 'GTK2 / amostra nativa atual /' in (value:=observation().get('paint_native_label','')) else None),30)
            assert '1:1' in label and 'px' in label, label
            subprocess.run(['import','-display',display,'-window','root',str(output/'gtk2-native-sample.png')],env=environment,check=True,timeout=10)
            results.update(status='passed',scope='Manual Paint uses a real GTK2 offscreen widget sample for the selected control/state, at native pixel size; Motif reference remains independent',
                           native_label=label,widget_source='native_gtk2',historical_fidelity_claimed=False)
            print(json.dumps(results,ensure_ascii=False),flush=True)
            return

        if quit_recovery_mode:
            from controller_quit_recovery import run
            results.update(run(output, container, observation, edit, click, environment, wait))
            if journal_capacity_mode:
                assert results["seed_histories_preserved"] == 310
            return

        if gtk4_push_mode:
            if gtk4_all_controls_mode:
                from controller_gtk4_all_controls import run
                results.update(run(output, observation, wait))
                return
            if gtk4_toggle_states:
                from controller_gtk4_toggle_states import run
                results.update(run(output,observation,click,wait,environment,scheme))
                return
            def gtk4_restart():
                nonlocal container
                click('quit');assert container.wait(timeout=15)==0
                (output/'home/probe.json').unlink(missing_ok=True)
                resumed=list(command)
                for option in ('--project','--family'):
                    index=resumed.index(option);del resumed[index:index+2]
                container=subprocess.Popen(resumed,stdout=log,stderr=log,start_new_session=True)
                wait(lambda:observation().get('separatePreview'))
            def gtk4_file(action,path):
                click(action);wait(lambda:observation().get('file_path'))
                subprocess.run(['xdotool','windowfocus',str(observation()['file_window'])],env=environment,check=True,timeout=5)
                click('file_path')
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a'],env=environment,check=True,timeout=5)
                subprocess.run(['xdotool','type','--clearmodifiers','--delay','1',path],env=environment,check=True,timeout=5)
                subprocess.run(['xdotool','key','Return'],env=environment,check=True,timeout=5)
                wait(lambda:not observation().get('file_path'))
            if gtk4_toggle_persistence:
                from controller_gtk4_toggle_persistence import run
                results.update(run(output,observation,click,wait,environment,gtk4_restart,gtk4_file))
                return
            if gtk4_toggle_mode:
                from controller_gtk4_toggle import run
                results.update(run(output,observation,click,wait,environment,visibility_only=gtk4_toggle_visibility))
                return
            if gtk4_states_mode:
                from controller_gtk4_states import run
                results.update(run(output,observation,click,wait,environment,scheme))
                return
            from controller_gtk4_push import run
            results.update(run(output,observation,click,wait,environment,gtk4_restart,gtk4_file))
            return

        if (gtk2_launch_mode or separate_gtk3_mode) and not anchor_mode:
            if pressure_mode:
                from controller_gtk2_pressure import run
                def pressure_restart():
                    nonlocal container
                    click('quit')
                    assert container.wait(timeout=15) == 0
                    (output/'home/probe.json').unlink(missing_ok=True)
                    resumed = list(command)
                    for option in ('--project', '--family'):
                        index = resumed.index(option); del resumed[index:index+2]
                    container = subprocess.Popen(resumed, stdout=log, stderr=log, start_new_session=True)
                    wait(lambda: observation().get('separatePreview'))
                def pressure_file(action, path):
                    click(action); wait(lambda: observation().get('file_path'))
                    subprocess.run(['xdotool', 'windowfocus', str(observation()['file_window'])], env=environment, check=True, timeout=5)
                    click('file_path')
                    subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a'],env=environment,check=True,timeout=5)
                    subprocess.run(['xdotool','type','--clearmodifiers','--delay','1',path],env=environment,check=True,timeout=10)
                    click('file_ok'); wait(lambda: not observation().get('file_path'))
                results.update(run(output, observation, click, wait, move_separate, environment, pressure_restart, pressure_file, control=12 if arrow_pressure_mode else 0, dimensions=(220,40) if arrow_pressure_mode else (180,50)))
            elif gtk2_progress_mode or gtk2_entry_mode or gtk2_text_mode or gtk2_combo_mode or gtk2_spin_control_mode or gtk2_scale_control or gtk2_arrow_control or gtk2_list_control or gtk2_frame_control or separate_gtk3_mode:
                from controller_gtk2_progress import run
                def restart_progress():
                    nonlocal container
                    click('quit')
                    assert container.wait(timeout=15) == 0
                    (output / 'home/probe.json').unlink(missing_ok=True)
                    resumed=list(command)
                    for option in ('--project','--family'):
                        index=resumed.index(option);del resumed[index:index+2]
                    container=subprocess.Popen(resumed,stdout=log,stderr=log,start_new_session=True)
                    wait(lambda:observation().get('separatePreview'))
                def progress_file(action,path):
                    click(action);wait(lambda:observation().get('file_path'))
                    subprocess.run(['xdotool','windowfocus',str(observation()['file_window'])],env=environment,check=True,timeout=5)
                    click('file_path')
                    subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a'],env=environment,check=True,timeout=5)
                    subprocess.run(['xdotool','type','--clearmodifiers','--delay','1',path],env=environment,check=True,timeout=10)
                    click('file_ok');wait(lambda:not observation().get('file_path'))
                results.update(run(output, observation, click, wait, move_separate, restart_progress, progress_file, family='gtk3' if separate_gtk3_mode else 'gtk2',control=15 if gtk2_frame_control else 14 if gtk2_list_control else 12 if gtk2_arrow_control else gtk2_scale_control if gtk2_scale_control else 6 if gtk2_spin_control_mode else 5 if gtk2_combo_mode else 7 if gtk2_text_mode else 4 if gtk2_entry_mode else 13))
            elif gtk2_radio_mode:
                from controller_gtk2_radio import run
                results.update(run(output, observation, click, wait, environment))
            elif gtk2_check_mode:
                from controller_gtk2_toggle import run
                results.update(run(output, observation, click, wait, environment,control=2))
            elif gtk2_toggle_mode:
                from controller_gtk2_toggle import run
                results.update(run(output, observation, click, wait, environment))
            elif gtk2_push_mode:
                from controller_gtk2_push import run
                def separate_visible():
                    child=subprocess.run(['xdotool','search','--onlyvisible','--name',
                        '^Theme Lab — GTK2 nativo(; barras de rolagem)?$'],env=environment,
                        capture_output=True,text=True,timeout=5)
                    if child.returncode not in (0,1):raise RuntimeError(child.stderr)
                    # GtkPlug carries the same title as GtkWindow. In this
                    # fixture without a WM only the detached window has the
                    # X root as parent; the Plug is nested in Motif's canvas.
                    for window in child.stdout.split():
                        tree=subprocess.check_output(['xwininfo','-id',window,'-tree'],
                            env=environment,text=True,timeout=5)
                        root=re.search(r'Root window id: (0x[0-9a-f]+)',tree)
                        parent=re.search(r'Parent window id: (0x[0-9a-f]+)',tree)
                        if root and parent and root[1]==parent[1]:return True
                    return False
                results.update(run(output, observation, click, wait, move_separate, separate_visible))
            else:
                from controller_gtk2_launch import run
                results.update(run(output, observation, click, wait, move_separate))
            print(json.dumps(results), flush=True)
            return

        if '--stale-preview' in sys.argv[2:]:
            from controller_stale_preview import run
            results.update(run(output, observation, click, wait, environment))
            print(json.dumps(results), flush=True)
            return

        if '--catalog-families' in sys.argv[2:]:
            from controller_catalog_matrix import run
            results.update(run(output, observation, click, wait, environment, families_only=True))
            print(json.dumps(results), flush=True)
            return

        if '--catalog-matrix' in sys.argv[2:]:
            from controller_catalog_matrix import run
            results.update(run(output, observation, click, wait, environment))
            print(json.dumps(results), flush=True)
            return

        if '--control-catalog' in sys.argv[2:]:
            from controller_control_catalog import run
            results.update(run(output, observation, click, wait, environment))
            print(json.dumps(results), flush=True)
            return

        if '--display-loss' in sys.argv[2:]:
            from controller_cancel_group import run
            results.update(run(output, observation, click, wait, environment, container, server))
            print(json.dumps(results), flush=True)
            return

        if '--cancel-group' in sys.argv[2:]:
            from controller_cancel_group import run
            results.update(run(output, observation, click, wait, environment, container))
            print(json.dumps(results), flush=True)
            return

        if '--backend-timeout' in sys.argv[2:]:
            from controller_backend_timeout import run
            results.update(run(output, observation, click, wait, environment))
            print(json.dumps(results), flush=True)
            return

        if '--preview-recovery' in sys.argv[2:]:
            from controller_preview_recovery import run
            results.update(run(output, observation, click, wait, environment))
            print(json.dumps(results), flush=True)
            return

        if project_io_mode or gtk_resume_mode:
            if gtk_resume_mode:
                from controller_gtk_resume import run
            else:
                from controller_project_io import run
            def restart(expected_exit=None):
                nonlocal container
                click('quit')
                assert container.wait(timeout=15) == 0, 'Native close failed'
                (output / 'home/probe.json').unlink(missing_ok=True)
                if gtk_transfer_mode:
                    # Exercise the actual launcher's snapshot between native
                    # controller incarnations, not a hand-written file copy.
                    path = ROOT / 'plasma/tools/abrir-laboratorio-temas.py'
                    spec = importlib.util.spec_from_file_location('transfer_launcher', path)
                    launcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
                    token = 'a' * 32; lab_id = secrets.token_hex(16)
                    addon = output / 'lab-addon' / ('run-' + lab_id)
                    addon.mkdir(parents=True, mode=0o700)
                    launcher.write_json(output / 'MANIFESTO.json',
                                        {'environment': {'IRIX_DOMAINOS_PREVIEW_ID': token}})
                    manifest = {'lab_id': lab_id, 'new_instance': True, 'uid': os.getuid(),
                                'session': str(output), 'preview_id': token}
                    launcher.write_json(addon / 'MANIFESTO.json', manifest)
                    work = output / 'home/lab'
                    saved = output / 'home' / launcher.instance_work(manifest).name
                    work.rename(saved)
                    receipt = launcher.resume_snapshot(output, addon / 'MANIFESTO.json', work)
                    assert receipt['applied_scene_imported']
                    assert not (work / 'generated').exists()
                    for name, digest in receipt['saved_files_sha256'].items():
                        assert hashlib.sha256((work / name).read_bytes()).hexdigest() == digest
                        assert (work / name).read_bytes() == (saved / name).read_bytes()
                    launcher.write_json(addon / 'TRANSFER.json', receipt)
                resumed = list(command)
                initial_index = resumed.index('--project')
                del resumed[initial_index:initial_index + 2]
                if gtk_resume_mode:
                    family_index = resumed.index('--family')
                    del resumed[family_index:family_index + 2]
                container = subprocess.Popen(resumed, stdout=log, stderr=log,
                                             start_new_session=True)
                if expected_exit is None:
                    wait(lambda: observation().get('load'))
                else:
                    assert container.wait(timeout=15) == expected_exit, \
                        'Invalid persisted scene was not rejected'
            results.update(run(output, observation, click, wait, environment, restart))
            if gtk_transfer_mode:
                results['native_launcher_transfer'] = 'passed: two actual snapshot transfers, scene/proposal/journals copied exactly, fresh generation, native GTK3 selection/drag'
            print(json.dumps(results), flush=True)
            return

        if history_mode:
            scene=output/'home/lab/scene.json';working=output/'home/lab/working.json'
            history=output/'home/lab/project-history.json'
            wait(lambda:observation().get('window') and scene.is_file() and history.is_file())
            subprocess.run(['xdotool','windowsize',str(observation()['window']),'2200','1100'],env=environment,check=True)
            wait(lambda:'Proposta privada gerada' in observation().get('status',''))
            def project():
                try:return json.loads(working.read_text())
                except (OSError,json.JSONDecodeError):return {}
            def journal():return json.loads(history.read_text())
            def invoke(name):
                stamp=time.time_ns();click(name)
                wait(lambda:(output/'home/probe.json').stat().st_mtime_ns>stamp)
            def input_number(key,text,reveal='width'):
                (output/'home/reveal-spin').write_text(reveal)
                time.sleep(.3);click(key)
                subprocess.run(['xdotool','key','ctrl+a','type','--clearmodifiers',str(text)],env=environment,check=True)
                wait(lambda:observation().get('glyph_text' if key=='glyph' else 'width_text')==str(text))
            original=project();assert original['recipes']['gtk3']['sizes'][0][0]==220
            invoke('projectMark');assert journal()['point']['recipes']['gtk3']['sizes'][0][0]==220
            for width in (260,270):
                input_number('controlWidth*fieldValue',width);invoke('apply')
                wait(lambda:project()['recipes']['gtk3']['sizes'][0][0]==width)
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3']['sizes'][0][0]==width)
            applied=json.loads(scene.read_text())['recipes']
            invoke('projectUndo');wait(lambda:observation().get('width_text')=='260')
            assert json.loads(scene.read_text())['recipes']==applied
            invoke('projectRedo');wait(lambda:observation().get('width_text')=='270')
            invoke('projectRestore');wait(lambda:observation().get('width_text')=='220')
            invoke('projectUndo');wait(lambda:observation().get('width_text')=='270')
            # The text editor keeps Ctrl+Z/Y, whereas Ctrl+Alt+Z/Y dispatch project history.
            input_number('controlWidth*fieldValue',290)
            subprocess.run(['xdotool','key','ctrl+z'],env=environment,check=True)
            wait(lambda:observation().get('width_text')!='290')
            subprocess.run(['xdotool','key','ctrl+y'],env=environment,check=True)
            wait(lambda:observation().get('width_text')=='290')
            invoke('apply');wait(lambda:project()['recipes']['gtk3']['sizes'][0][0]==290)
            input_number('controlWidth*fieldValue',300);invoke('apply')
            wait(lambda:project()['recipes']['gtk3']['sizes'][0][0]==300)
            (output/'home/reveal-spin').write_text('width');time.sleep(.3);click('controlWidth*fieldValue')
            subprocess.run(['xdotool','key','ctrl+alt+z'],env=environment,check=True)
            wait(lambda:observation().get('width_text')=='290')
            subprocess.run(['xdotool','key','ctrl+alt+y'],env=environment,check=True)
            wait(lambda:observation().get('width_text')=='300')
            (output/'home/reveal-spin').write_text('part 0');time.sleep(.4)
            input_number('glyph',9,'glyph');invoke('apply')
            wait(lambda:project()['recipes']['gtk3'].get('scrollbar_parts',{}).get('arrow',{}).get('glyph_px')==9)
            before=project();invoke('projectResetPart')
            wait(lambda:project()['recipes']['gtk3'].get('scrollbar_parts',{}).get('arrow',{})=={})
            reset=project()
            for family,recipe in before['recipes'].items():
                expected=json.loads(json.dumps(recipe))
                if family=='gtk3':
                    expected['scrollbar_parts'].pop('arrow',None)
                assert reset['recipes'][family]==expected
            invoke('projectUndo');wait(lambda:observation().get('glyph_text')=='9')
            saved_history=journal();saved_project=project()
            click('quit');wait(lambda:container.poll() is not None,10)
            subprocess.run(['xdotool','mousemove','2150','1150'],env=environment,check=True)
            resume=command[:-4] # remove explicit --project fixture and --family gtk3
            container=subprocess.Popen(resume,stdout=log,stderr=log,start_new_session=True)
            wait(lambda:observation().get('window') and 'Proposta privada gerada' in observation().get('status',''))
            wait(lambda:project()['recipes']==saved_project['recipes'])
            assert journal()==saved_history
            assert observation()['projectRedo_sensitive'] and observation()['projectRestore_sensitive']
            before_conflict=project();foreign=journal();foreign['external_writer_test']=True
            history.write_text(json.dumps(foreign,ensure_ascii=False))
            invoke('projectUndo');wait(lambda:'Conflito' in observation().get('status',''))
            assert project()==before_conflict and journal()==foreign
            assert observation()['glyph_text']=='9' and observation()['width_text']=='300'
            results.update(status='passed',scope='Real Motif buttons/keyboard -> controller -> atomic project history -> re-open',
                undo_redo_numbers=True,checkpoint_restore_undoable=True,scene_unchanged_until_apply=True,
                independent_text_undo_redo=True,project_shortcuts=True,selective_piece_reset=True,
                recovered_history_cursor_point=True,live_conflict_preserves_proposal=True)
            return

        if relief_mode:
            scene=output/'home/lab/scene.json';working=output/'home/lab/working.json'
            wait(lambda:observation().get('window'))
            subprocess.run(['xdotool','windowsize',str(observation()['window']),'2200','1100'],env=environment,check=True,timeout=10)
            wait(lambda: scene.is_file() and 'Proposta privada gerada' in observation().get('status',''))
            initial_metrics=observation().get('metrics','')
            results['initial_preview_measurement']=initial_metrics
            click('apply');wait(lambda:allocated(220,80))
            baseline=json.loads(scene.read_text())
            click('separatePreview');wait(lambda:allocated(220,80,True));move_separate()
            (output/'home/reveal-spin').write_text('control 10')
            wait(lambda:observation().get('selected_control_event')==10)
            click('apply');wait(lambda:json.loads(scene.read_text())['recipes']['gtk3']['selected_control']==10)
            def ready_bar_origins():
                rows=[r for r in observation().get('native_bars',[]) if r['control']==10]
                if (output/'home/probe.json').stat().st_mtime_ns<scene.stat().st_mtime_ns:return None
                return rows if len(rows)==2 and all(r.get('pieces_source')==2 for r in rows) else None
            wait(ready_bar_origins);move_separate()
            baseline=json.loads(scene.read_text())
            def choose_relief(key,index):
                command_name='relief-state' if key=='relief_state' else 'relief-kind'
                path=output/'home/reveal-spin'
                # Consumer removes the command immediately; timestamp before
                # publication avoids stat racing its unlink.
                command_stamp=time.time_ns();path.write_text(command_name)
                wait(lambda:not path.exists(),5)
                # A new code fragment can relayout the scrollable editor.
                # Wait for reports after reveal, then two identical bounds;
                # the command disappearing alone precedes layout processing.
                last_bounds=None;stable=0;last_stamp=0
                def settled_bounds():
                    nonlocal last_bounds,stable,last_stamp
                    stamp=(output/'home/probe.json').stat().st_mtime_ns
                    if stamp<=command_stamp or stamp<=last_stamp:return None
                    bounds=observation()[key+'_arrow'];last_stamp=stamp
                    stable=stable+1 if bounds==last_bounds else 0;last_bounds=bounds
                    return bounds if stable>=(10 if button_relief_mode or trough_relief_mode or thumb_relief_mode or fitting_relief_mode else 2) else None
                bounds=wait(settled_bounds,8)
                results.setdefault('relief_pointer_targets',[]).append({'key':key,'index':index,'bounds':bounds})
                x,y,w,h=observation()[key]
                prior_report=(output/'home/probe.json').stat().st_mtime_ns
                x,y,w,h=bounds
                subprocess.run(['xdotool','mousemove',str(x+w//2),str(y+h//2),'click','1'],env=environment,check=True,timeout=10)

                option=key+'_option_'+str(index)
                wait(lambda:(output/'home/probe.json').stat().st_mtime_ns>prior_report and option in observation(),5)
                click(option)
                wait(lambda:observation().get(key+'_selected')==index and option not in observation(),5)
                if button_relief_mode and key=='relief_state':
                    name=('normal','pressed','disabled','backdrop','hover','focus')[index]
                    wait(lambda:'arrow / '+name in observation().get('code',''))
                if thumb_relief_mode and key=='relief_state':
                    name=('normal','pressed','disabled','backdrop','hover','focus')[index]
                    if index<5:wait(lambda:'scroll_h / '+name in observation().get('code',''))
                    else:wait(lambda:'ainda não traduzido: focus' in observation().get('code',''))
                if fitting_relief_mode and key=='relief_state':
                    name=('normal','pressed','disabled','backdrop','hover','focus')[index]
                    if index in (0,2,3):wait(lambda:'scroll_h / '+name in observation().get('code',''))
                    else:wait(lambda:'Estado não traduzido: '+name in observation().get('code',''))
                if trough_relief_mode and key=='relief_state':
                    name=('normal','pressed','disabled','backdrop','hover','focus')[index]
                    if index in (0,2,3):wait(lambda:'scroll_h / '+name in observation().get('code',''))
                    else:wait(lambda:'Estado não traduzido: '+name in observation().get('code',''))
            if readiness_mode:
                before=json.loads(working.read_text())
                initial=wait(ready_bar_origins)
                old_window=observation()['window']
                click('quit');wait(lambda:container.poll() is not None,10)
                resumed=list(command);resumed[resumed.index('--project')+1]=HOME+'/lab/working.json'
                (output/'home/probe.json').unlink(missing_ok=True)
                container=subprocess.Popen(resumed,stdout=log,stderr=log,start_new_session=True)
                wait(lambda:observation().get('window'))
                def coupled_ready():
                    rows=[r for r in observation().get('native_bars',[]) if r['control']==10 and not r['separate'] and r.get('pieces_source')==2]
                    if (output/'home/probe.json').stat().st_mtime_ns<scene.stat().st_mtime_ns:return None
                    return rows if len(rows)==1 else None
                coupled=wait(coupled_ready)
                click('separatePreview');after=wait(ready_bar_origins);move_separate()
                assert json.loads(working.read_text())['recipes']==before['recipes']
                assert json.loads(scene.read_text())['recipes']==before['recipes']
                for old,new in zip(initial,after):
                    for key in ('width','height','pieces_mask','slider','track','arrow_first','arrow_last'):
                        assert old[key]==new[key],key
                subprocess.run(['import','-display',display,'-window','root',str(output/'preview-readiness.png')],env=environment,check=True,timeout=10)
                results.update(status='passed',scope='Initial and post-reopen coupled/detached native preview readiness and geometry',
                    initial_native=initial,reopened_coupled=coupled,reopened_both=after,
                    recipes_preserved=True,old_probe_removed=True,personal_profile_exposed=False,
                    historical_fidelity_claimed=False)
                return
            if trough_relief_mode or thumb_relief_mode or fitting_relief_mode:
                part = 'thumb' if thumb_relief_mode else 'fitting' if fitting_relief_mode else 'trough'
                part_index = 3 if thumb_relief_mode else 4 if fitting_relief_mode else 2
                supported = (0,1,2,3,4) if thumb_relief_mode else (0,2,3)
                states = ('normal','pressed','disabled','backdrop','hover','focus')
                clear_index = 4 if thumb_relief_mode else 3
                clear_state = states[clear_index]
                (output/'home/reveal-spin').write_text('piece '+str(part_index))
                wait(lambda:not (output/'home/reveal-spin').exists())
                click('apply')
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3']['selected_scroll_part']==part_index)
                baseline=json.loads(scene.read_text());native_before=wait(ready_bar_origins)
                expected_states={}
                for ordinal,index in enumerate(supported):
                    name=states[index];choice=ordinal%3+1;relief=('flat','raised','sunken')[choice-1]
                    choose_relief('relief_state',index);assert observation()['relief_kind_sensitive'],name
                    choose_relief('relief_kind',choice);expected_states[name]=relief
                    wait(lambda:json.loads(working.read_text())['recipes']['gtk3']['scrollbar_parts'][part]['state_relief']==expected_states)
                    wait(lambda:'gtk3-lab-'+part+'-'+name in observation().get('code',''))
                    assert json.loads(scene.read_text())==baseline,'Manual edit changed applied scene'
                saved_working=json.loads(working.read_text())
                for index in set(range(6))-set(supported):
                    choose_relief('relief_state',index);assert not observation()['relief_kind_sensitive']
                    assert json.loads(working.read_text())['recipes']==saved_working['recipes'],'Unsupported navigation changed proposal'
                expected={part:{'state_relief':expected_states}}
                click('apply')
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
                native_after=wait(ready_bar_origins)
                for origin in (0,1):
                    for key in ('width','height','pieces_mask'):
                        assert native_before[origin].get(key)==native_after[origin].get(key),key
                applied=json.loads(scene.read_text())
                assert applied['recipes']['gtk3']['geometry']==baseline['recipes']['gtk3']['geometry']
                assert applied['recipes']['gtk3']['sizes']==baseline['recipes']['gtk3']['sizes']
                for family,recipe in baseline['recipes'].items():
                    if family!='gtk3':assert applied['recipes'][family]==recipe,family
                choose_relief('relief_state',clear_index);wait(lambda:observation()['relief_kind_selected']==supported.index(clear_index)%3+1)
                choose_relief('relief_kind',0);del expected_states[clear_state]
                wait(lambda:json.loads(working.read_text())['recipes']['gtk3']['scrollbar_parts'][part]['state_relief']==expected_states)
                choose_relief('relief_state',2);wait(lambda:observation()['relief_kind_selected']==supported.index(2)%3+1)
                click('apply');wait(lambda:json.loads(scene.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
                saved=json.loads(working.read_text())
                click('quit');wait(lambda:container.poll() is not None,10)
                resumed=list(command);resumed[resumed.index('--project')+1]=HOME+'/lab/working.json'
                container=subprocess.Popen(resumed,stdout=log,stderr=log,start_new_session=True)
                wait(lambda:observation().get('window') and observation().get('relief_state_selected')==0)
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
                current=json.loads(working.read_text())
                for family,recipe in saved['recipes'].items():assert current['recipes'][family]==recipe,family
                choose_relief('relief_state',2);wait(lambda:observation()['relief_kind_selected']==supported.index(2)%3+1)
                subprocess.run(['import','-display',display,'-window','root',str(output/(part+'-relief-editor.png'))],env=environment,check=True,timeout=10)
                results.update(status='passed',scope='Real Motif pointer selections -> controller -> independent '+part+' states -> manual Apply and private close/reload',
                    input='X11 pointer to measured native popup row bounds',supported_states_independent=list(supported),
                    manual_apply=True,cleared_only_state=clear_state,unsupported_states_guard=True,
                    recipes_preserved=True,reload_preserved=True,native_bar_origins=native_after,
                    personal_profile_exposed=False,historical_fidelity_claimed=False)
                return
            if button_relief_mode:
                (output/'home/reveal-spin').write_text('control 12')
                wait(lambda:observation().get('selected_control_event')==12)
                (output/'home/reveal-spin').write_text('piece 1')
                wait(lambda:not (output/'home/reveal-spin').exists())
                click('apply')
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3']['selected_scroll_part']==1)
                baseline=json.loads(scene.read_text())
                expected_states={}
                names=('normal','pressed','disabled','backdrop','hover','focus')
                kinds=('flat','raised','sunken')
                for index,name in enumerate(names):
                    choose_relief('relief_state',index)
                    assert observation()['relief_kind_sensitive'],name
                    choice=index%3+1
                    choose_relief('relief_kind',choice)
                    expected_states[name]=kinds[choice-1]
                    wait(lambda:json.loads(working.read_text())['recipes']['gtk3']['scrollbar_parts']['arrow_button']['state_relief']==expected_states)
                    wait(lambda:'arrow / '+name in observation().get('code','') and 'border-color:' in observation().get('code',''))
                    assert json.loads(scene.read_text())==baseline,'Manual state edit changed applied scene'
                expected={'arrow_button':{'state_relief':expected_states}}
                click('apply')
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
                applied=json.loads(scene.read_text())
                assert applied['recipes']['gtk3']['geometry']==baseline['recipes']['gtk3']['geometry']
                assert applied['recipes']['gtk3']['sizes']==baseline['recipes']['gtk3']['sizes']
                for family,recipe in baseline['recipes'].items():
                    if family!='gtk3':assert applied['recipes'][family]==recipe,family
                choose_relief('relief_state',5)
                choose_relief('relief_kind',0)
                del expected_states['focus']
                wait(lambda:json.loads(working.read_text())['recipes']['gtk3']['scrollbar_parts']['arrow_button']['state_relief']==expected_states)
                choose_relief('relief_kind',2)
                expected_states['focus']='raised'
                wait(lambda:json.loads(working.read_text())['recipes']['gtk3']['scrollbar_parts']['arrow_button']['state_relief']==expected_states)
                saved=json.loads(working.read_text())
                click('quit');wait(lambda:container.poll() is not None,10)
                resumed=list(command);resumed[resumed.index('--project')+1]=HOME+'/lab/working.json'
                container=subprocess.Popen(resumed,stdout=log,stderr=log,start_new_session=True)
                wait(lambda:observation().get('window') and observation().get('relief_state_selected')==0)
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
                current=json.loads(working.read_text())
                for family,recipe in saved['recipes'].items():assert current['recipes'][family]==recipe,family
                choose_relief('relief_state',5)
                wait(lambda:observation().get('relief_kind_selected')==2 and observation()['relief_kind_sensitive'])
                subprocess.run(['import','-display',display,'-window','root',str(output/'button-relief-editor.png')],env=environment,check=True,timeout=10)
                results.update(status='passed',scope='Real Motif pointer selections -> controller -> six independent GtkButton border states -> manual Apply and private close/reload',
                    input='X11 pointer to measured native popup row bounds',six_states_independent=True,
                    manual_apply=True,clear_only_focus=True,recipes_preserved=True,reload_preserved=True,
                    personal_profile_exposed=False,historical_fidelity_claimed=False)
                return
            choose_relief('relief_state',1)
            choose_relief('relief_kind',3)
            wait(lambda:'scroll_h / pressed' in observation().get('code','') and 'gtk3-lab-stepper-left-pressed' in observation().get('code',''))
            choose_relief('relief_state',0)
            choose_relief('relief_kind',1)
            wait(lambda:'scroll_h / normal' in observation().get('code','') and 'gtk3-lab-stepper-left-normal' in observation().get('code',''))
            choose_relief('relief_state',1)
            wait(lambda:observation().get('relief_kind_selected')==3)
            assert json.loads(scene.read_text())==baseline,'Manual selection changed applied scene'
            click('apply')
            expected={'arrow':{'state_relief':{'normal':'flat','pressed':'sunken'}}}
            wait(lambda:json.loads(scene.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
            wait(lambda:json.loads(working.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
            def both_native():
                rows=[r for r in observation().get('native_bars',[]) if r['control']==10]
                return rows if len(rows)==2 and all(r.get('pieces_source')==2 and r.get('pieces_mask')==15 for r in rows) else None
            native=wait(both_native)
            rows=json.loads(scene.read_text())
            assert rows['recipes']['gtk3']['geometry']==baseline['recipes']['gtk3']['geometry']
            results['recipes_before_relief']=baseline['recipes']
            results['recipes_after_relief']=rows['recipes']
            for family,recipe in baseline['recipes'].items():
                if family!='gtk3':
                    # Backend canonicalization emits explicit no-op defaults.
                    # Compare all values, permitting only these two omissions.
                    before=dict(recipe);after=dict(rows['recipes'][family])
                    before.setdefault('scrollbar_parts',{})
                    before.setdefault('length_anchor',[0]*16)
                    after.setdefault('scrollbar_parts',{})
                    after.setdefault('length_anchor',[0]*16)
                    assert after==before,family
            choose_relief('relief_state',5);assert not observation()['relief_kind_sensitive']
            wait(lambda:'ainda não traduzido: focus' in observation().get('code',''))
            choose_relief('relief_state',4);assert observation()['relief_kind_sensitive']
            choose_relief('relief_kind',1)
            wait(lambda:'scroll_h / hover' in observation().get('code','') and 'gtk3-lab-stepper-left-hover' in observation().get('code',''))
            wait(lambda:json.loads(working.read_text())['recipes']['gtk3']['scrollbar_parts']['arrow']['state_relief'].get('hover')=='flat')
            choose_relief('relief_kind',0)
            results['hover_editor_independent']=True
            context_scene=json.loads(scene.read_text())
            choose_relief('relief_state',2);assert observation()['relief_kind_sensitive']
            choose_relief('relief_kind',2)
            wait(lambda:'scroll_h / disabled' in observation().get('code','') and 'gtk3-lab-stepper-left-disabled' in observation().get('code',''))
            choose_relief('relief_state',3);assert observation()['relief_kind_sensitive']
            choose_relief('relief_kind',1)
            wait(lambda:'scroll_h / backdrop' in observation().get('code','') and 'gtk3-lab-stepper-left-backdrop' in observation().get('code',''))
            wait(lambda:json.loads(working.read_text())['recipes']['gtk3']['scrollbar_parts']['arrow']['state_relief']=={
                'normal':'flat','pressed':'sunken','disabled':'raised','backdrop':'flat'})
            assert json.loads(scene.read_text())==context_scene,'Browsing/editing applied manual context scene'
            choose_relief('relief_state',2);wait(lambda:observation()['relief_kind_selected']==2)
            choose_relief('relief_kind',0)
            choose_relief('relief_state',3);wait(lambda:observation()['relief_kind_selected']==1)
            choose_relief('relief_kind',0)
            results['disabled_backdrop_editor_independent']=True
            choose_relief('relief_state',0);wait(lambda:observation().get('relief_kind_selected')==1)
            choose_relief('relief_kind',0);click('apply')
            expected={'arrow':{'state_relief':{'pressed':'sunken'}}}
            wait(lambda:json.loads(working.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
            choose_relief('relief_state',1);wait(lambda:observation().get('relief_kind_selected')==3)
            saved=json.loads(working.read_text())
            # Close only this disposable test controller, then reload its working project.
            click('quit');wait(lambda:container.poll() is not None,10)
            resumed=list(command);resumed[resumed.index('--project')+1]=HOME+'/lab/working.json'
            container=subprocess.Popen(resumed,stdout=log,stderr=log,start_new_session=True)
            wait(lambda:observation().get('window') and observation().get('relief_state_selected')==0)
            wait(lambda:json.loads(scene.read_text())['recipes']['gtk3'].get('scrollbar_parts')==expected)
            current=json.loads(working.read_text())
            for family,recipe in saved['recipes'].items():assert current['recipes'][family]==recipe,family
            choose_relief('relief_state',1);wait(lambda:observation().get('relief_kind_selected')==3)
            subprocess.run(['import','-display',display,'-window','root',str(output/'relief-editor.png')],env=environment,check=True,timeout=10)
            results.update(status='passed',scope='Real pointer selections in Motif editor -> real controller -> generated GTK3 scene/working -> native IPC both origins -> private close/reload',
                input='X11 pointer to measured native popup row bounds',state_overrides_independent=True,
                manual_apply=True,clear_only_normal=True,unsupported_focus_guard=True,
                recipes_preserved=True,reload_preserved=True,native_bar_origins=native,
                personal_profile_exposed=False,historical_fidelity_claimed=False)
            return
        if comparison_mode:
            scene=output/'home/lab/scene.json'
            wait(lambda: scene.is_file() and len(observation().get('native_bars',[]))>=2)
            baseline=json.loads(scene.read_text())
            click('separatePreview')
            wait(lambda:len(observation().get('native_bars',[]))==4)
            all_controls=wait(lambda:observation().get('native_controls') if len(observation().get('native_controls',[]))==32 else None)
            for row in all_controls:
                assert row['scale']==1
                assert row['font_kind']==(2 if row['control'] in (10,11,12) else 1)
                if row['font_kind']==1:assert row['font'].startswith('Pango contexto de ')
            results['all_16_controls_font_scale_through_ipc_both_origins']=all_controls
            move_separate()
            cases=[]
            for control,axis in ((10,'width'),(11,'height')):
                (output/'home/reveal-spin').write_text('control '+str(control))
                wait(lambda:observation().get('selected_control_event')==control and observation().get('anchor_sensitive'))
                click('apply')
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3']['selected_control']==control)
                def measured():
                    probe=observation()
                    if (output/'home/probe.json').stat().st_mtime_ns<scene.stat().st_mtime_ns:return None
                    rows=[r for r in probe.get('native_bars',[]) if r['control']==control]
                    summary=probe.get('metrics','')
                    if len(rows)!=2 or not all(r.get('pieces_source')==2 and r.get('pieces_mask')==15 for r in rows):return None
                    if summary.count('GTK3 3.24.49 verificado; caixas de margem')!=2:return None
                    if 'Motif 2.3.8 interno' not in summary:return None
                    if not summary.rstrip().endswith('VM.'):return None
                    return rows,summary
                before,summary=wait(measured)
                edit('controlWidth*fieldValue' if axis=='width' else 'controlHeight*fieldValue',260)
                click('apply')
                wait(lambda:json.loads(scene.read_text())['recipes']['gtk3']['sizes'][control][0 if control==10 else 1]==260)
                def resized():
                    value=measured()
                    return value if value and all(r[axis]==260 for r in value[0]) else None
                rows,summary=wait(resized)
                assert rows[0]['slider']==rows[1]['slider'],rows
                assert rows[0]['track']==rows[1]['track'],rows
                for row in rows:
                    for name in ('slider','track','arrow_first','arrow_last'):
                        x,y,w,h=row[name]
                        assert x>=0 and y>=0 and w>0 and h>0
                        assert x+w<=row['width'] and y+h<=row['height']
                cases.append(dict(control=control,before=before,after=rows,summary=summary))
                move_separate()
            final=json.loads(scene.read_text())
            for family,recipe in baseline['recipes'].items():
                if family!='gtk3':assert final['recipes'][family]==recipe,family
            results.update(status='passed',comparison_native_cases=cases,
                controller='real controller -> generated private GTK3 -> bounded IPC -> Motif summary',
                both_origins=True,other_recipes_preserved=True,
                personal_profile_exposed=False,historical_fidelity_claimed=False)
            return
        if anchor_mode:
            from controller_gtk_anchor import run
            def anchor_restart():
                nonlocal container
                click('quit')
                assert container.wait(timeout=15)==0
                (output/'home/probe.json').unlink(missing_ok=True)
                resumed=list(command)
                for option in ('--project','--family'):
                    index=resumed.index(option);del resumed[index:index+2]
                container=subprocess.Popen(resumed,stdout=log,stderr=log,start_new_session=True)
                wait(lambda:observation().get('separatePreview'))
            def anchor_file(action,path):
                click(action);wait(lambda:observation().get('file_path'))
                subprocess.run(['xdotool','windowfocus',str(observation()['file_window'])],env=environment,check=True,timeout=5)
                click('file_path')
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a'],env=environment,check=True,timeout=5)
                subprocess.run(['xdotool','type','--clearmodifiers','--delay','1',path],env=environment,check=True,timeout=10)
                click('file_ok');wait(lambda:not observation().get('file_path'))
            results.update(run(output, observation, click, wait, move_separate, allocated, edit, environment, 'gtk2' if gtk2_launch_mode else 'gtk3', anchor_file, anchor_restart))
            return
        if axis_mode:
            wait(lambda: allocated(220,80))
            scene=output/'home/lab/scene.json'
            baseline=json.loads(scene.read_text())
            measurements={}
            if axis_limits:
                click('separatePreview')
                wait(lambda: allocated(220,80,True))
                move_separate()
            for control,axis,length,expected in ((10,'width',320,(320,15)),(11,'height',260,(15,260))):
                (output/'home/reveal-spin').write_text('control '+str(control))
                wait(lambda: observation().get(axis+'_sensitive') and observation().get(('height' if axis=='width' else 'width')+'_sensitive') is False)
                (output/'home/reveal-spin').write_text(axis);time.sleep(.4)
                subprocess.run(['xdotool','windowfocus',str(observation()['window'])],env=environment,check=True)
                click('controlWidth*fieldValue' if axis=='width' else 'controlHeight*fieldValue')
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers',str(length)],env=environment,check=True)
                wait(lambda: observation().get(axis+'_text')==str(length))
                if control==10:
                    # Replacing the selection and typing three digits are four
                    # native edits. Verify the full multi-step history.
                    subprocess.run(['xdotool','key','--clearmodifiers',*(['ctrl+z']*4)],env=environment,check=True)
                    wait(lambda: observation().get('width_text')=='220')
                    subprocess.run(['xdotool','key','--clearmodifiers',*(['ctrl+y']*4)],env=environment,check=True)
                    wait(lambda: observation().get('width_text')=='320')
                click('apply')
                def applied_axis():
                    d=json.loads(scene.read_text())
                    r=d['recipes']['gtk3']
                    return d if r['selected_control']==control and r['sizes'][control][0 if axis=='width' else 1]==length else None
                current=wait(applied_axis)
                wait(lambda:allocated(*expected,both=axis_limits))
                if axis_limits:move_separate()
                measurements[str(control)]=observation()['metrics']
                assert current['recipes']['gtk3']['geometry']==baseline['recipes']['gtk3']['geometry']
                assert current['recipes']['gtk3']['sizes'][control][1 if axis=='width' else 0]==0
                for family,recipe in baseline['recipes'].items():
                    if family!='gtk3':assert current['recipes'][family]==recipe
                subprocess.run(['import','-display',display,'-window','root',str(output/('axis-'+str(control)+'.png'))],env=environment,check=True)
            if axis_limits:
                limits={}
                for control,axis in ((10,'width'),(11,'height')):
                    (output/'home/reveal-spin').write_text('control '+str(control))
                    wait(lambda: observation().get(axis+'_sensitive') and observation().get(('height' if axis=='width' else 'width')+'_sensitive') is False)
                    for length in (1,0):
                        (output/'home/reveal-spin').write_text(axis);time.sleep(.4)
                        click('controlWidth*fieldValue' if axis=='width' else 'controlHeight*fieldValue')
                        subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers',str(length)],env=environment,check=True)
                        wait(lambda: observation().get(axis+'_text')==str(length))
                        click('apply')
                        def limit_metrics():
                            d=json.loads(scene.read_text());r=d['recipes']['gtk3']
                            if r['selected_control']!=control or r['sizes'][control][0 if axis=='width' else 1]!=length:return None
                            if (output/'home/probe.json').stat().st_mtime_ns<scene.stat().st_mtime_ns:return None
                            text=observation().get('metrics','')
                            request=str(length)+' x 0' if axis=='width' else '0 x '+str(length)
                            if 'Pedido em edição: '+request+' ' not in text:return None
                            sizes=re.findall(r'GTK3 (?:acoplado|separado): (\d+) x (\d+)(?: px lógicos)?',text)
                            if len(sizes)!=2 or sizes[0]!=sizes[1]:return None
                            cross=int(sizes[0][1 if axis=='width' else 0])
                            long=int(sizes[0][0 if axis=='width' else 1])
                            return (text,cross,long) if cross==15 and long>1 else None
                        text,cross,long=wait(limit_metrics)
                        limits[str(control)+':'+str(length)]={'metrics':text,'cross':cross,'long':long}
                        move_separate()
                results['minimum_and_automatic_both_native_previews']=limits
            results.update(status='passed',axis_lock_native_metrics=measurements,
                           locked_cross_fields_insensitive=True,length_native_undo_redo=True,
                           unchanged_family_geometry_and_other_families=True,
                           historical_fidelity_claimed=False,personal_profile_exposed=False)
            print(json.dumps(results,ensure_ascii=False),flush=True)
            return

        if piece_mode:
            wait(lambda: allocated(220, 80))
            scene = output / 'home/lab/scene.json'
            baseline = json.loads(scene.read_text())
            def latest_masks():
                record = json.loads((output / 'home/lab/generated/latest.json').read_text())
                folder = output / 'home' / Path(record['generation_dir']).relative_to(HOME)
                receipt = json.loads((folder / 'RESULTADO.json').read_text())
                theme = output / 'home' / Path(receipt['families']['gtk3']['theme_path']).relative_to(HOME)
                return json.loads((theme / 'common/adaptive/MANIFEST.json').read_text())['files']
            masks_before = wait(latest_masks)
            reference_before = observation()['motifReferenceControls.nativePushButton'][2:]
            (output / 'home/reveal-spin').write_text('glyph')
            time.sleep(.5)
            subprocess.run(['xdotool','windowfocus',str(observation()['window'])],env=environment,check=True)
            click('glyph')
            subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers','7'],env=environment,check=True)
            wait(lambda: observation().get('glyph_text')=='7',5)
            subprocess.run(['xdotool','key','--clearmodifiers','ctrl+z'],env=environment,check=True)
            wait(lambda: observation().get('glyph_text')=='-1',5)
            subprocess.run(['xdotool','key','--clearmodifiers','ctrl+y'],env=environment,check=True)
            wait(lambda: observation().get('glyph_text')=='7',5)
            results['new_numeric_editor_native_undo_redo']=True
            subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','ctrl+c','ctrl+x'],env=environment,check=True)
            wait(lambda: observation().get('glyph_text')=='',5)
            subprocess.run(['xdotool','key','--clearmodifiers','ctrl+v'],env=environment,check=True)
            wait(lambda: observation().get('glyph_text')=='7',5)
            results['new_numeric_editor_native_copy_cut_paste']=True
            # Manual mode does not alter the applied scene until the button.
            assert json.loads(scene.read_text())==baseline
            click('apply')
            def new_scene():
                value=json.loads(scene.read_text())
                return value if value['recipes']['gtk3'].get('scrollbar_parts')=={'arrow': {'glyph_px':7}} else None
            changed=wait(new_scene)
            assert changed['recipes']['gtk3']['geometry']==baseline['recipes']['gtk3']['geometry']
            assert dict(changed['recipes']['motif'], scrollbar_parts=changed['recipes']['motif'].get('scrollbar_parts',{})) == dict(baseline['recipes']['motif'], scrollbar_parts=baseline['recipes']['motif'].get('scrollbar_parts',{}))
            def changed_masks():
                value=latest_masks()
                return value if value!=masks_before else None
            masks_after=wait(changed_masks)
            assert masks_before.keys()==masks_after.keys()
            differences=[key for key in masks_before if masks_before[key]!=masks_after[key]]
            assert differences and all(key.startswith('gtk3-stepper-') for key in differences),differences
            results['only_arrow_generated_assets_changed']=differences
            wait(lambda: allocated(220,80))
            (output/'home/reveal-spin').write_text('control 12')
            def arrow_metrics():
                text=observation().get('metrics','')
                return text if 'GTK3 acoplado:' in text and 'Pedido em edição: 0 x 0' in text else None
            results['actual_gtk3_arrow_metrics']=wait(arrow_metrics)
            wait(lambda: 'Triângulo proposto: 7px' in observation().get('code',''),10)
            results['code_matches_selected_arrow_recipe']=True
            subprocess.run(['import','-display',display,'-window','root',str(output/'arrow-native.png')],env=environment,check=True)
            assert observation()['motifReferenceControls.nativePushButton'][2:] == reference_before
            results['unchanged_family_geometry_and_motif_reference']=True
            results['schema_transition_empty_piece_objects']='Normalized absent to empty; no effective Motif parameters changed'
            results['manual_apply_real_controller_generation']=True
            if button_mode:
                arrow_scene=changed
                arrow_masks=masks_after
                (output/'home/reveal-spin').write_text('piece 1')
                wait(lambda: observation().get('glyph_sensitive') and observation().get('glyph_text')=='-1',5)
                (output/'home/reveal-spin').write_text('glyph');time.sleep(.4);click('glyph')
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers','1'],env=environment,check=True)
                wait(lambda: observation().get('glyph_text')=='1',5)
                (output/'home/reveal-spin').write_text('shadow');time.sleep(.4);click('shadow')
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers','1'],env=environment,check=True)
                wait(lambda: observation().get('shadow_text')=='1',5)
                click('apply')
                def button_scene():
                    value=json.loads(scene.read_text())
                    return value if value['recipes']['gtk3'].get('scrollbar_parts')=={
                        'arrow': {'glyph_px':7}, 'arrow_button': {'padding_px':1,'shadow_px':1}} else None
                changed=wait(button_scene)
                scene_hash=hashlib.sha256(scene.read_bytes()).hexdigest()
                wait(lambda:json.loads((output/'home/lab/generated/latest.json').read_text())['project_sha256']==scene_hash)
                assert latest_masks()==arrow_masks, 'Button recipe must not alter any arrow/trough/thumb mask'
                assert changed['recipes']['gtk3']['geometry']==arrow_scene['recipes']['gtk3']['geometry']
                assert changed['recipes']['gtk3']['scrollbar_parts']['arrow']==arrow_scene['recipes']['gtk3']['scrollbar_parts']['arrow']
                wait(lambda: 'GTK3 acoplado: 15 x 15' in observation().get('metrics',''))
                wait(lambda:'Botão isolado: moldura 1px; espaço interno 1px' in observation().get('code',''),10)
                subprocess.run(['import','-display',display,'-window','root',str(output/'button-native.png')],env=environment,check=True)
                results['button_adjustment_preserves_glyph_masks_family_geometry_and_15x15_allocation']=True
                results['button_scope']='Standalone GtkButton; GtkRange rules unchanged by offline test'
                # The real GTK canvas must contain the selected native KDE
                # button face, not a stale DomainOS/Breeze RGB snapshot.
                from PIL import Image
                record=json.loads((output/'home/lab/generated/latest.json').read_text())
                folder=output/'home'/Path(record['generation_dir']).relative_to(HOME)
                colors=json.loads((folder/'GTK3-NATIVE-COLORS.json').read_text())['colors']
                color=colors['theme_button_background_normal_breeze']
                rgb=tuple(int(color[i:i+2],16) for i in (1,3,5))
                shot=Image.open(output/'button-native.png').convert('RGB')
                x,y,w,h=observation()['canvas']
                count=sum(shot.getpixel((xx,yy))==rgb for xx in range(x,x+w) for yy in range(y,y+h))
                assert count>0, ('Selected face not rendered in GTK3 canvas',scheme,rgb)
                results['selected_palette_native_face']={'scheme':scheme,'rgb':rgb,'pixels_in_native_canvas':count}

            if trough_mode:
                def select_bar(index):
                    (output/'home/reveal-spin').write_text('control '+str(index))
                    time.sleep(.5)
                    click('apply')
                    def measured_bar():
                        text=observation().get('metrics','')
                        values=re.findall(r'GTK3 acoplado: (\d+) x (\d+) px lógicos',text)
                        if not values:return None
                        w,h=map(int,values[0])
                        return (w,h,text) if (w>=220 if index==10 else h>=180) else None
                    return wait(measured_bar)
                baseline_bars={str(index):select_bar(index) for index in (10,11)}
                baseline_masks=latest_masks()
                baseline_recipe=changed['recipes']['gtk3']
                (output/'home/reveal-spin').write_text('piece 2')
                wait(lambda: observation().get('glyph_sensitive') and observation().get('glyph_text')=='-1',5)
                for key,value in (('glyph','17'),('shadow','1')):
                    (output/'home/reveal-spin').write_text(key);time.sleep(.4);click(key)
                    subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers',value],env=environment,check=True)
                    wait(lambda: observation().get(key+'_text')==value,5)
                click('apply')
                def trough_scene():
                    value=json.loads(scene.read_text())
                    parts=value['recipes']['gtk3'].get('scrollbar_parts',{})
                    return value if parts.get('trough')=={'thickness_px':17,'shadow_px':1} else None
                changed=wait(trough_scene)
                scene_hash=hashlib.sha256(scene.read_bytes()).hexdigest()
                wait(lambda:json.loads((output/'home/lab/generated/latest.json').read_text())['project_sha256']==scene_hash)
                actual_masks=latest_masks()
                for key,value in baseline_masks.items():assert actual_masks[key]==value,key
                added=set(actual_masks)-set(baseline_masks)
                assert added and all(key.startswith('gtk3-lab-trough-frame') for key in added),added
                assert changed['recipes']['gtk3']['geometry']==baseline_recipe['geometry']
                for piece in ('arrow','arrow_button'):
                    assert changed['recipes']['gtk3']['scrollbar_parts'][piece]==baseline_recipe['scrollbar_parts'][piece]
                actual_bars={}
                for index in (10,11):
                    actual_bars[str(index)]=select_bar(index)
                    wait(lambda:'Trilho independente: espessura proposta 17px; relevo 1px' in observation().get('code',''),10)
                    subprocess.run(['import','-display',display,'-window','root',str(output/('trough-'+str(index)+'-native.png'))],env=environment,check=True)
                assert baseline_bars['10'][1]==15 and baseline_bars['11'][0]==15,baseline_bars
                assert actual_bars['10'][1]==17 and actual_bars['11'][0]==17,actual_bars
                results['trough_native_dimensions']={'baseline':baseline_bars,'actual':actual_bars}
                results['trough_preserves_previous_masks_and_independent_recipes']=True
                results['trough_added_masks']=sorted(added)
                results['trough_state_palette_and_internal_node_allocation']='not yet verified; whole bar allocation only'

            if thumb_mode:
                previous=changed
                previous_masks=latest_masks()
                (output/'home/reveal-spin').write_text('piece 3')
                wait(lambda: observation().get('glyph_sensitive') and observation().get('gap_visible'),5)
                for key,value in (('glyph','9'),('shadow','1'),('gap','3')):
                    (output/'home/reveal-spin').write_text(key);time.sleep(.4);click(key)
                    subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers',value],env=environment,check=True)
                    wait(lambda: observation().get(key+'_text')==value,5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+z'],env=environment,check=True)
                wait(lambda: observation().get('gap_text')=='-1',5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+y'],env=environment,check=True)
                wait(lambda: observation().get('gap_text')=='3',5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','ctrl+c','ctrl+x'],env=environment,check=True)
                wait(lambda: observation().get('gap_text')=='',5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+v'],env=environment,check=True)
                wait(lambda: observation().get('gap_text')=='3',5)
                click('apply')
                def thumb_scene():
                    value=json.loads(scene.read_text())
                    return value if value['recipes']['gtk3'].get('scrollbar_parts',{}).get('thumb')=={'cross_px':9,'shadow_px':1,'gap_px':3} else None
                changed=wait(thumb_scene)
                scene_hash=hashlib.sha256(scene.read_bytes()).hexdigest()
                wait(lambda:json.loads((output/'home/lab/generated/latest.json').read_text())['project_sha256']==scene_hash)
                actual_masks=latest_masks()
                differences=[key for key in previous_masks if previous_masks[key]!=actual_masks.get(key)]
                assert differences and all(key.startswith('gtk3-thumb-frame') for key in differences),differences
                assert changed['recipes']['gtk3']['geometry']==previous['recipes']['gtk3']['geometry']
                for piece in ('arrow','arrow_button','trough'):
                    assert changed['recipes']['gtk3']['scrollbar_parts'][piece]==previous['recipes']['gtk3']['scrollbar_parts'][piece]
                results['thumb_editor_three_parameters_and_gap_native_undo_clipboard']=True
                results['only_thumb_masks_changed']=differences
                wait(lambda: 'GTK3 acoplado: 17 x 180' in observation().get('metrics',''))
                results['thumb_coupled_preview_mapped_and_measured']=True
                subprocess.run(['import','-display',display,'-window','root',str(output/'thumb-native.png')],env=environment,check=True)

            (output/'home/reveal-spin').write_text('piece 4')
            wait(lambda: observation().get('glyph_sensitive') and not observation().get('gap_visible'),5)
            if fitting_mode:
                previous=changed
                previous_masks=latest_masks()
                for key,value in (('glyph','7'),('shadow','1')):
                    (output/'home/reveal-spin').write_text(key);time.sleep(.4);click(key)
                    subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','--clearmodifiers',value],env=environment,check=True)
                    wait(lambda: observation().get(key+'_text')==value,5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+z'],env=environment,check=True)
                wait(lambda: observation().get('shadow_text')=='-1',5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+y'],env=environment,check=True)
                wait(lambda: observation().get('shadow_text')=='1',5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','ctrl+c','ctrl+x'],env=environment,check=True)
                wait(lambda: observation().get('shadow_text')=='',5)
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+v'],env=environment,check=True)
                wait(lambda: observation().get('shadow_text')=='1',5)
                click('apply')
                def fitting_scene():
                    value=json.loads(scene.read_text())
                    return value if value['recipes']['gtk3'].get('scrollbar_parts',{}).get('fitting')=={'gap_px':7,'inset_px':1} else None
                changed=wait(fitting_scene)
                scene_hash=hashlib.sha256(scene.read_bytes()).hexdigest()
                wait(lambda:json.loads((output/'home/lab/generated/latest.json').read_text())['project_sha256']==scene_hash)
                actual_masks=latest_masks()
                assert all(actual_masks.get(key)==value for key,value in previous_masks.items())
                added=set(actual_masks)-set(previous_masks)
                assert added and all(key.startswith('gtk3-lab-view-frame') for key in added),added
                assert changed['recipes']['gtk3']['geometry']==previous['recipes']['gtk3']['geometry']
                for piece in ('arrow','arrow_button','trough','thumb'):
                    assert changed['recipes']['gtk3']['scrollbar_parts'][piece]==previous['recipes']['gtk3']['scrollbar_parts'][piece]
                wait(lambda: 'GTK3 acoplado: 17 x 180' in observation().get('metrics',''))
                results['fitting_editor_native_undo_clipboard_and_coupled_preview']=True
                results['fitting_preserves_all_existing_masks_and_recipes']=True
                results['fitting_added_masks']=sorted(added)
                subprocess.run(['import','-display',display,'-window','root',str(output/'fitting-native.png')],env=environment,check=True)
            working=json.loads((output/'home/lab/working.json').read_text())
            assert working['recipes']['gtk3']['scrollbar_parts']==changed['recipes']['gtk3']['scrollbar_parts']
            assert working['recipes']['gtk3']['selected_scroll_part']==4
            (output/'home/reveal-spin').write_text('piece 0')
            wait(lambda: observation().get('glyph_sensitive') and observation().get('glyph_text')=='7',5)
            results['fitting_supported_and_existing_override_preserved']=True
            results.update(status='passed',personal_profile_exposed=False,historical_fidelity_claimed=False,
                           text_input='X11 keyboard with native Undo/Redo',piece_selection='Motif callback API fixture')
            print(json.dumps(results,ensure_ascii=False),flush=True)
            return

        if editor_mode:
            wait(lambda: observation().get('notes'))
            (output / 'home/reveal-spin').write_text('notes')
            time.sleep(.4)
            subprocess.run(['xdotool','windowfocus',str(observation()['window'])],env=environment,check=True)
            click('notes')

            def key(value):
                subprocess.run(['xdotool','key','--clearmodifiers',value],env=environment,check=True)

            def text(value):
                subprocess.run(['xdotool','type','--clearmodifiers','--delay','80',value],env=environment,check=True)

            def expect(value):
                return wait(lambda: observation().get('notes_text')==value,5)

            def paste_utf8(value):
                # xdotool Unicode typing can map accented uppercase to its
                # lowercase keycode. Use an actual clipboard owner so that
                # the test checks bytes, native paste and the editor instead.
                owner = subprocess.Popen(['xclip','-selection','clipboard','-in','-quiet'],
                                         stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL,env=environment)
                try:
                    owner.stdin.write(value.encode('utf-8'))
                    owner.stdin.close()
                    time.sleep(.15)
                    key('ctrl+v');expect(value)
                finally:
                    if owner.poll() is None:
                        owner.terminate()
                    owner.wait(timeout=5)

            key('ctrl+a');text('abc');expect('abc')
            key('ctrl+z');expect('ab')
            key('ctrl+z');expect('a')
            key('ctrl+shift+z');expect('ab')
            key('ctrl+y');expect('abc')
            results['native_multistep_undo_redo'] = True
            value='ação — café\nDúvida: seleção e revisão.\nTerceiro parágrafo.'
            key('ctrl+a');paste_utf8(value)
            key('ctrl+a');key('ctrl+c');key('ctrl+x');expect('')
            key('ctrl+z');expect(value)
            key('ctrl+a');key('ctrl+v');expect(value)
            results['native_utf8_copy_cut_paste_selection'] = True
            (output/'home/reveal-spin').write_text('catalog')
            wait(lambda: not (output/'home/reveal-spin').exists(),5)
            expect(value)
            results['scheme_catalog_refresh_preserves_draft'] = True
            click('apply')
            wait(lambda: json.loads((output/'home/lab/working.json').read_text())['recipes']['motif']['notes']==value,5)
            results['model_save_after_native_edit'] = True
            click('notes');key('ctrl+a');paste_utf8('rascunho recuperável')
            wait(lambda: (output/'home/lab/editor-journal.json').is_file(),5)
            journal=output/'home/lab/editor-journal.json'
            wait(lambda: json.loads(journal.read_text())['histories']['recipe/motif/notes']['entries'][-1]=='rascunho recuperável',5)
            results['draft_and_history_checkpoint'] = True
            # Autosave now recovers the latest valid proposal from project history.
            # The text journal preserves its own per-character Undo independently.
            assert json.loads((output/'home/lab/scene.json').read_text())['recipes']['motif']['notes']==value
            subprocess.run(['xdotool','windowfocus',str(observation()['window'])],env=environment,check=True)
            click('quit');wait(lambda: container.poll() is not None,5)
            assert container.returncode==0, container.returncode
            (output/'home/probe.json').unlink()
            resume_command=list(command)
            for option in ('--project','--family'):
                index=resume_command.index(option)
                del resume_command[index:index+2]
            container=subprocess.Popen(resume_command,stdout=log,stderr=log,start_new_session=True)
            wait(lambda: observation().get('notes_text')=='rascunho recuperável')
            recovered=json.loads((output/'home/lab/working.json').read_text())
            assert recovered['recipes']['motif']['notes']=='rascunho recuperável', 'Latest valid proposal not recovered'
            history=json.loads((output/'home/lab/project-history.json').read_text())
            assert history['entries'][history['position']]['recipes']['motif']['notes']=='rascunho recuperável'
            results['implicit_history_recovers_latest_proposal_separate_from_text_undo']=True
            (output/'home/reveal-spin').write_text('notes');time.sleep(.4)
            subprocess.run(['xdotool','windowfocus',str(observation()['window'])],env=environment,check=True)
            # Replacing the selected draft by paste is one native edit
            # operation, so Undo restores the complete prior text atomically.
            click('notes');key('ctrl+z');expect(value)
            key('ctrl+y');expect('rascunho recuperável')
            results['reopened_draft_and_undo_redo'] = True
            # Numeric child must intercept Ctrl+A before the SpinBox defaults.
            (output/'home/reveal-spin').write_text('width');time.sleep(.4)
            click('controlWidth*fieldValue');key('ctrl+a');text('321')
            wait(lambda: observation().get('width_text')=='321',5)
            key('ctrl+z');wait(lambda: observation().get('width_text')=='32',5)
            key('ctrl+y');wait(lambda: observation().get('width_text')=='321',5)
            results['numeric_native_select_undo_redo'] = True
            key('shift+F10');wait(lambda: observation().get('edit_menu_entries')==6,5)
            key('Escape')
            results['native_keyboard_edit_menu_six_actions'] = True
            key('Home');wait(lambda: observation().get('width_text')=='321',5)
            key('End');wait(lambda: observation().get('width_text')=='321',5)
            results['numeric_home_end_preserve_value'] = True
            (output/'home/reveal-spin').write_text('control 1')
            wait(lambda: observation().get('width_text')=='0',5)
            (output/'home/reveal-spin').write_text('control 0')
            wait(lambda: observation().get('width_text')=='321',5)
            (output/'home/reveal-spin').write_text('width');time.sleep(.4)
            click('controlWidth*fieldValue');key('ctrl+z')
            wait(lambda: observation().get('width_text')=='32',5)
            key('ctrl+y');wait(lambda: observation().get('width_text')=='321',5)
            results['control_switch_preserves_independent_undo'] = True
            current=json.loads(journal.read_text())['histories']
            assert all(current), 'Recovered sample editors must never share an empty key'
            results['sample_recovery_keys_remain_independent'] = True
            # Font policy integration must never transform input into legacy
            # bytes or clear native Undo history when glyphs are unavailable.
            (output/'home/reveal-spin').write_text('notes');time.sleep(.4)
            click('notes');key('ctrl+a')
            multilingual = 'Árvore — ação Ελληνικά Русский 漢字 😀'
            paste_utf8(multilingual)
            key('ctrl+a');key('ctrl+c');key('ctrl+x');expect('')
            key('ctrl+v');expect(multilingual)
            key('ctrl+z');expect('')
            key('ctrl+y');expect(multilingual)
            subprocess.run(['import','-display',display,'-window','root',str(output/'font-policy-editor.png')],env=environment,check=True,timeout=10)
            results['unicode_all_scripts_storage_clipboard_undo_redo'] = True
            results['palette_fixture'] = scheme
            results.update(status='passed',personal_profile_exposed=False)
            print(json.dumps(results,ensure_ascii=False),flush=True)
            return

        results['initial_coupled'] = wait(lambda: allocated(220, 80))
        click('separatePreview')
        results['initial_both'] = wait(lambda: allocated(220, 80, True))
        move_separate()
        reference = observation()['motifReferenceControls.nativePushButton'][2:]
        (output / 'home/reveal-spin').touch()
        time.sleep(.4)
        click('controlWidth*fieldValue', arrow=True)
        width = wait(lambda: int(observation().get('width_text', '220'))
                     if observation().get('width_text') not in (None, '220') else None, 5)
        assert abs(width - 220) == 1, width
        time.sleep(.5)
        assert allocated(220, 80, True), 'Manual mode prematurely changed native allocation'
        click('apply')
        results['manual_spin_both'] = wait(lambda: allocated(width, 80, True))
        move_separate()
        assert observation()['motifReferenceControls.nativePushButton'][2:] == reference
        click('automaticPreview')
        (output / 'home/reveal-spin').write_text('height')
        time.sleep(.4)
        click('controlHeight*fieldValue', arrow=True)
        height = wait(lambda: int(observation().get('height_text', '80'))
                      if observation().get('height_text') not in (None, '80') else None, 5)
        assert abs(height - 80) == 1, height
        results['automatic_spin_both'] = wait(lambda: allocated(width, height, True))
        move_separate()
        assert observation()['motifReferenceControls.nativePushButton'][2:] == reference
        click('automaticPreview')
        edit('controlWidth*fieldValue', 1)
        edit('controlHeight*fieldValue', 1)
        click('apply')
        def refreshed_minimum():
            value = matching_native(1)
            return value if value and value != (width, height) else None
        minimum = wait(refreshed_minimum)
        assert minimum[0] > 1 and minimum[1] > 1, minimum
        results['request_below_native_minimum'] = {'requested': [1, 1], 'both_allocated': minimum}
        move_separate()
        edit('controlWidth*fieldValue', 0)
        edit('controlHeight*fieldValue', 0)
        click('apply')
        automatic = wait(lambda: matching_native(0))
        assert automatic == minimum, (automatic, minimum)
        results['automatic_native_size'] = {'requested': [0, 0], 'both_allocated': automatic}
        move_separate()
        edit('controlWidth*fieldValue', width)
        edit('controlHeight*fieldValue', height)
        click('apply')
        wait(lambda: allocated(width, height, True))
        move_separate()
        (output / 'home/reveal-spin').write_text('metrics')
        time.sleep(.4)
        subprocess.run(['import', '-display', display, '-window', 'root', str(output / 'native.png')],
                       env=environment, check=True)
        results.update(status='passed', motif_reference=reference,
                       spin_input='X11 pointer', limit_input='XmTextFieldSetString / real valueChanged callback',
                       personal_profile_exposed=False, historical_fidelity_claimed=False)
    except Exception as error:
        results.update(status='failed', error=str(error))
        if anchor_mode:
            try:
                probe=json.loads((output/'home/probe.json').read_text())
                results['anchor_diagnostic']={k:probe.get(k) for k in ('anchor_event','anchor_calls','anchor_selected','anchor_result','anchor_error','status','native_bars')}
            except (OSError,json.JSONDecodeError):
                pass
        raise
    finally:
        remaining = stop_fixture_controller(display)
        if remaining:
            results['owned_controller_shutdown_pending'] = remaining
        if server and server.poll() is None:
            try:
                subprocess.run(['import', '-display', display, '-window', 'root', str(output / 'last.png')],
                               env=environment, check=False, timeout=10)
            except subprocess.TimeoutExpired:
                results['capture_timeout'] = True
        for process in (container, server):
            if process and process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
        log.close()
        (output / 'RESULTADO.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
