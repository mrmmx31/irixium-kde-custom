#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise recoverable DomainOS replacement in an isolated native Plasma.

Uses private HOME/XDG paths, bus, Xvfb and owned KWin/Plasma processes. The
production applet and CLI run unchanged; fault injection loses only the reply
after a real create/commit operation. Never activates a personal panel.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import tarfile
import time
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PLUGIN = 'org.irixclassic.domainos.panel'
SESSION_ENTRY = Path(__file__).resolve()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def semantic(panel):
    """Compare recovered settings/order while allowing genuine renewed IDs."""
    value = json.loads(json.dumps(panel))

    def config(node):
        for key in ('SystrayContainmentId', 'PreloadWeight', 'UserBackgroundHints', 'AppletOrder',
                    'DomainOSLayoutToken', 'domainosActivationToken'):
            node.get('entries', {}).pop(key, None)
        # KDE stores the grouping exceptions as QSets and may serialize them
        # in a different order when recreating a native Task Manager. Their
        # membership matters; pins, widget order and trayOrder stay ordered.
        for key in ('groupingAppIdBlacklist', 'groupingLauncherUrlBlacklist'):
            value = node.get('entries', {}).get(key)
            if isinstance(value, str):
                node['entries'][key] = sorted(entry.replace('\\,', ',')
                    for entry in re.split(r'(?<!\\),', value) if entry)
            elif isinstance(value, list): node['entries'][key] = sorted(value)
        for child in node.get('groups', {}).values():
            config(child)

    def item(widget):
        widget.pop('id', None)
        widget.pop('geometry', None)
        config(widget['config'])
        if 'tray' in widget:
            widget['tray'].pop('id', None)
            config(widget['tray']['config'])
            for child in widget['tray']['widgets']:
                item(child)

    value.pop('id', None)
    value['geometry'].pop('length', None)
    config(value['config'])
    for widget in value['widgets']:
        item(widget)
    return value


def worker(output):
    if os.environ.get('IRIX_DOMAINOS_ACTIVATION_PRIVATE') != '1':
        raise RuntimeError('Private session required')
    sys.path.insert(0, str(ROOT / 'tools'))
    import activate_domainos as module
    from classic_panel import stable
    checks = {}; observations = {'cli': []}; processes = []

    def wait_for(function, timeout=30):
        until = time.monotonic() + timeout; last = None
        while time.monotonic() < until:
            try:
                last = function()
                if last:
                    return last
            except Exception as error:
                last = repr(error)
            time.sleep(.2)
        raise RuntimeError('Timed out: ' + str(last))

    def run(*arguments):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/activate_domainos.py'), *arguments],
            capture_output=True, text=True, timeout=60)
        observations['cli'].append({'args': arguments, 'code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr})
        return result

    def inspect():
        return module.call({'action': 'inspect'})

    def one_panel(domainos):
        current = inspect()['state']['panels']
        if len(current) != 1:
            return None
        found = any(widget['type'] == PLUGIN for widget in current[0]['widgets'])
        return current[0] if found == domainos else None

    def evaluate(source):
        result = subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.kde.plasmashell',
            '--object-path', '/PlasmaShell', '--method', 'org.kde.PlasmaShell.evaluateScript', source],
            capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr)
        return ast.literal_eval(result.stdout)[0]

    def receipt():
        directory = Path(os.environ['XDG_STATE_HOME']) / 'irixium-domainos-panel'
        token = (directory / 'latest').read_text().strip()
        path = directory / 'backups' / token / 'receipt.json'
        return path, json.loads(path.read_text())

    def native_geometry(prefix):
        def ready():
            path = output / 'UI.json'
            if not path.exists():
                return None
            report = json.loads(path.read_text())
            values = report.get('panels', [])
            return values[0] if len(values) == 1 and values[0]['visible'] else None
        measured = wait_for(ready)
        # Let the real containment's delayed layout finish before measuring.
        time.sleep(1)
        measured = ready()
        observations[prefix + '_native_geometry'] = measured
        checks[prefix + '_native_panel_content_971_109'] = bool(measured) and abs(measured['width'] - 971) < .01 and abs(measured['height'] - 109) < .01
        checks[prefix + '_native_drawing_scale_half'] = bool(measured) and abs(measured['scale'] - .5) < .00001
        checks[prefix + '_chassis_inside_native_window'] = bool(measured) and measured['x'] >= 0 and measured['y'] >= 0 and measured['x'] + 971 <= measured['windowWidth'] + .01 and measured['y'] + 109 <= measured['windowHeight'] + .01
        image = output / 'panel-live.png'
        if image.exists():
            shutil.copy2(image, output / (prefix.upper() + '.png'))
        checks[prefix + '_own_native_panel_captured'] = (output / (prefix.upper() + '.png')).is_file()

    try:
        for name, command in (('kwin', ['kwin_x11', '--replace']), ('plasma', ['plasmashell', '--no-respawn'])):
            stream = (output / (name + '.log')).open('w')
            environment = dict(os.environ)
            if name == 'plasma':
                environment['LD_PRELOAD'] = str(output / 'activation-host.so')
            process = subprocess.Popen(command, env=environment, stdout=stream, stderr=stream)
            processes.append((process, stream))
        wait_for(lambda: inspect())
        time.sleep(3)
        before = wait_for(lambda: one_panel(False))
        # A customized source must survive the first full replacement, not
        # merely be available later in a restore receipt.
        evaluate(module.SCRIPT + '''
var source=panels()[0];
var manager=source.widgets().find(w=>w.type==="org.kde.plasma.icontasks");
manager.currentConfigGroup=["General"];
var customized={showOnlyCurrentDesktop:false,showOnlyCurrentScreen:true,showOnlyCurrentActivity:false,
 showOnlyMinimized:true,onlyGroupWhenFull:false,groupingStrategy:0,sortingStrategy:2,middleClickAction:1,
 wheelEnabled:false,wheelSkipMinimized:false,showToolTips:false,interactiveMute:false,
 highlightWindows:false,unhideOnAttention:false,groupingAppIdBlacklist:["private-a.desktop","private-b.desktop"]};
Object.keys(customized).forEach(key=>manager.writeConfig(key,customized[key]));manager.reloadConfig();
var wrapper=source.widgets().find(w=>isTray(w.type)),contained=inner(wrapper);
contained.currentConfigGroup=["General"];
contained.writeConfig("shownItems",["org.kde.plasma.volume"]);
contained.writeConfig("hiddenItems",["org.kde.plasma.clipboard"]);
contained.writeConfig("showAllItems",false);contained.reloadConfig();
var volume=contained.widgets().find(w=>w.type==="org.kde.plasma.volume");
volume.currentConfigGroup=["General"];volume.writeConfig("volumeStep",3);volume.reloadConfig();
print("source-customized");
''')
        time.sleep(1)
        before = wait_for(lambda: one_panel(False))
        expected_settings, expected_tray = module.seed_preferences(before)
        observations['before'] = before
        observations['expected_seed_settings'] = expected_settings
        checks['dry_run_cli_success'] = run('--verificar').returncode == 0
        checks['dry_run_preserves_semantics_and_ids'] = stable(one_panel(False)) == stable(before)
        checks['activation_cli_success'] = run().returncode == 0
        active = wait_for(lambda: one_panel(True))
        observations['activated'] = active
        checks['old_panel_removed_no_hidden_duplicate'] = len(inspect()['state']['panels']) == 1 and active['id'] != before['id']
        checks['domainos_is_only_widget'] = len(active['widgets']) == 1
        actual_settings = active['widgets'][0]['config']['groups']['General']['entries']
        checks['first_activation_preserves_custom_task_and_tray_choices'] = all(
            module.setting_value(actual_settings[key], kind) == expected_settings[key]
            for key, kind in ((target, kind) for target, kind in module.TASK_SETTINGS.values())
            if key in expected_settings and kind != 'filter') and actual_settings['tasksFilterMode'] == expected_settings['tasksFilterMode']
        checks['first_activation_preserves_tray_visibility_lists'] = all(
            module.config_list(actual_settings[key]) == expected_settings[key]
            for key in ('trayVisibleItems', 'trayHiddenItems'))
        actual_tray = active['widgets'][0]['tray']
        def tray_semantic(tray):
            shell = json.loads(json.dumps(before))
            shell['widgets'] = [json.loads(json.dumps(active['widgets'][0]))]
            shell['widgets'][0]['tray'] = json.loads(json.dumps(tray))
            return semantic(shell)['widgets'][0]['tray']
        observations['seeded_tray'] = actual_tray
        checks['first_activation_preserves_complete_provider_configs'] = tray_semantic(actual_tray) == tray_semantic(expected_tray)
        checks['first_activation_allocates_independent_tray_and_provider_ids'] = actual_tray['id'] != expected_tray['id'] and not (
            {child['id'] for child in actual_tray['widgets']} & {child['id'] for child in expected_tray['widgets']})
        checks['new_approved_wheel_default_browses_without_activation'] = actual_settings.get('iconboxWheelActivates', 'false') == 'false'
        checks['native_panel_floating_requested'] = active['geometry']['floating'] is True
        checks['new_panel_requested_geometry'] = active['geometry']['location'] == 'bottom' and active['geometry']['height'] >= 109 and active['geometry']['minimumLength'] >= 971 and active['geometry']['maximumLength'] == active['geometry']['minimumLength']
        native_geometry('activated')
        path, record = receipt(); observations['activation_receipt'] = record
        checks['layout_files_backed_up'] = set(record['layoutFiles']) == {'plasmashellrc', 'plasma-org.kde.plasma.desktop-appletsrc'}
        checks['second_activation_idempotent'] = run().returncode == 0 and one_panel(True)['id'] == active['id']
        current = one_panel(True)
        checks['restore_dry_run_success'] = run('--restaurar', '--verificar').returncode == 0
        checks['restore_dry_run_leaves_panel_untouched'] = stable(one_panel(True)) == stable(current)
        plasma_process, plasma_stream = processes[-1]
        plasma_process.terminate(); plasma_process.wait(timeout=10); plasma_stream.close()
        restart_stream = (output / 'plasma-restart.log').open('w')
        restart = subprocess.Popen(['plasmashell', '--no-respawn'],
            env=dict(os.environ, LD_PRELOAD=str(output / 'activation-host.so')),
            stdout=restart_stream, stderr=restart_stream)
        processes.append((restart, restart_stream))
        restarted = wait_for(lambda: one_panel(True)); time.sleep(2)
        checks['native_shell_restart_keeps_single_active_panel'] = restarted['id'] == active['id'] and len(inspect()['state']['panels']) == 1
        checks['restore_cli_success'] = run('--restaurar').returncode == 0
        restored = wait_for(lambda: one_panel(False))
        wait_for(lambda: semantic(one_panel(False)) == semantic(before))
        restored = one_panel(False); observations['restored'] = restored
        checks['restored_panel_widgets_configs_tray_order_geometry'] = semantic(restored) == semantic(before)
        checks['restored_ids_are_new_valid_instances'] = restored['id'] != before['id'] and all(widget['id'] > 0 for widget in restored['widgets'])
        checks['restored_receipt'] = json.loads(path.read_text())['status'] == 'restored'

        # The bridge reuses the saved DomainOS instance's own preferences when
        # switching back, and is idempotent if DomainOS is already selected.
        checks['bridge_reactivation_success'] = run('--ponte').returncode == 0
        bridge_panel = wait_for(lambda: one_panel(True))
        pinned = ['domainos-own-a.desktop', 'domainos-own-b.desktop']
        evaluate('var w=panelById(' + str(bridge_panel['id']) + ').widgets()[0];w.currentConfigGroup=["General"];w.writeConfig("pinnedApplications",' + json.dumps(pinned) + ');w.writeConfig("iconboxHintsEnabled",false);w.reloadConfig();print("ok");')
        time.sleep(.5)
        own_general = one_panel(True)['widgets'][0]['config']['groups']['General']['entries']
        observations['saved_domainos_general'] = own_general
        checks['bridge_active_call_idempotent'] = run('--ponte').returncode == 0 and one_panel(True)['id'] == bridge_panel['id']
        checks['bridge_restore_success'] = run('--restaurar', '--ponte').returncode == 0
        wait_for(lambda: one_panel(False))
        checks['bridge_restored_original_semantics'] = semantic(one_panel(False)) == semantic(before)
        checks['bridge_reactivate_saved_preferences_success'] = run('--ponte').returncode == 0
        wait_for(lambda: one_panel(True)); time.sleep(.5)
        returned_general = one_panel(True)['widgets'][0]['config']['groups']['General']['entries']
        checks['bridge_keeps_pins_and_iconbox_hint_preference'] = all(returned_general.get(key) == own_general.get(key) for key in ('pinnedApplications', 'iconboxHintsEnabled'))
        checks['bridge_second_restore_success'] = run('--restaurar', '--ponte').returncode == 0
        restored = wait_for(lambda: one_panel(False))

        # Starting with a top-edge source must still yield only one bottom panel.
        evaluate('var p=panelById(' + str(restored['id']) + ');p.location="top";print("ok");')
        top = wait_for(lambda: one_panel(False) if one_panel(False)['geometry']['location'] == 'top' else None)
        checks['top_source_activation_success'] = run().returncode == 0
        top_active = wait_for(lambda: one_panel(True))
        checks['top_source_one_bottom_panel'] = top_active['geometry']['location'] == 'bottom' and len(inspect()['state']['panels']) == 1
        native_geometry('top_activated')
        checks['top_source_restore_success'] = run('--restaurar').returncode == 0
        wait_for(lambda: semantic(one_panel(False)) == semantic(top))
        checks['top_source_geometry_and_settings_restored'] = semantic(one_panel(False)) == semantic(top)

        # The original call really executes in our native fixture; only its reply
        # is lost. Test create and commit separately because their recoveries differ.
        for action in ('create', 'commit'):
            source = one_panel(False)
            original_call = module.call
            fired = {'value': False}

            def lose_reply(payload):
                reply = original_call(payload)
                if payload.get('action') == action and not fired['value']:
                    fired['value'] = True
                    raise subprocess.TimeoutExpired('owned Plasma reply-loss probe', 30)
                return reply

            failure = None
            try:
                with patch.object(module, 'call', lose_reply), patch.object(sys, 'argv', [str(ROOT / 'tools/activate_domainos.py')]):
                    module.main()
            except BaseException as error:
                failure = repr(error)
            observations[action + '_lost_reply_exception'] = failure
            observations[action + '_lost_reply_state'] = inspect()
            checks[action + '_reply_loss_fault_exercised'] = fired['value']
            _, lost_record = receipt(); observations[action + '_lost_reply_receipt'] = lost_record
            # The public recovery command, rather than manually editing a receipt,
            # must always get back to an equivalent single original panel.
            recovery = run('--restaurar')
            checks[action + '_lost_reply_cli_restore_success'] = recovery.returncode == 0
            wait_for(lambda: semantic(one_panel(False)) == semantic(source))
            checks[action + '_lost_reply_restores_semantics_without_duplicates'] = semantic(one_panel(False)) == semantic(source)
    except BaseException as error:
        observations['error'] = repr(error)
        try:
            observations['failure_final_state'] = inspect()
        except BaseException as final_error:
            observations['failure_final_state_error'] = repr(final_error)
    finally:
        for process, _ in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process, stream in reversed(processes):
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=8)
            stream.close()
        checks['own_kwin_plasma_processes_stopped'] = all(process.poll() is not None for process, _ in processes)
        report = {'checks': checks, 'observations': observations}
        (output / 'WORKER.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if checks and all(checks.values()) and 'error' not in observations else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--internal-session', action='store_true', help=argparse.SUPPRESS)
    arguments = parser.parse_args(); output = arguments.saida.resolve()
    if arguments.internal_session:
        return worker(output)
    if output == Path('/tmp') or not output.is_relative_to(Path('/tmp')) or output.exists():
        parser.error('Use um diretório novo dentro de /tmp')
    output.mkdir(mode=0o700)
    protected = [Path.home() / '.config' / name for name in ('kdeglobals', 'plasmarc', 'kwinrc', 'plasmashellrc', 'plasma-org.kde.plasma.desktop-appletsrc')]
    protected_before = {str(path): digest(path) for path in protected}
    sources = [ROOT / 'tools' / name for name in ('activate_domainos.py', 'panel_layout.py', 'install_domainos.py')]
    sources += list((ROOT / 'plasma/applets/org.irixclassic.domainos.panel').rglob('*'))
    source_before = {str(path): digest(path) for path in sources if path.is_file()}
    flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt6Widgets'], text=True))
    subprocess.run(['c++', '-std=c++17', '-shared', '-fPIC', str(ROOT / 'plasma/tests/domainos-activation-host.cpp'),
        '-o', str(output / 'activation-host.so'), *flags, '-ldl'], check=True)
    # Cache/data/profile live on the workspace filesystem, whose inode budget
    # is independent of /tmp. This is an owned disposable fixture only.
    with tempfile.TemporaryDirectory(prefix='.domainos-activation-fixture-', dir=ROOT) as directory:
        home = Path(directory)
        (output / 'PROFILE.json').write_text(json.dumps({'ownedFixtureHome': str(home)}))
        paths = {name: home / subdirectory for name, subdirectory in (
            ('HOME', 'home'), ('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
            ('XDG_STATE_HOME', 'state'), ('XDG_CACHE_HOME', 'cache'), ('XDG_RUNTIME_DIR', 'runtime'))}
        for path in paths.values():
            path.mkdir(mode=0o700)
        for destination, source in (
            ('plasma/plasmoids/org.irixclassic.domainos.panel', 'plasma/applets/org.irixclassic.domainos.panel'),
            ('plasma/plasmoids/org.irixclassic.grosview', 'plasma/applets/org.irixclassic.grosview'),
            ('plasma/desktoptheme/IrixClassicDomainOS', 'plasma/IrixClassicDomainOS')):
            target = paths['XDG_DATA_HOME'] / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(ROOT / source, target)
        colors = paths['XDG_DATA_HOME'] / 'color-schemes'; colors.mkdir()
        shutil.copy2(ROOT / 'colors/DomainOS-SR10.4.colors', colors)
        env = dict(os.environ)
        for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'DBUS_STARTER_ADDRESS',
                    'DBUS_STARTER_BUS_TYPE', 'XAUTHORITY', 'LD_PRELOAD', 'SESSION_MANAGER', 'SSH_AUTH_SOCK',
                    'XDG_SESSION_ID', 'QML_IMPORT_PATH', 'QML2_IMPORT_PATH', 'QT_STYLE_OVERRIDE'):
            env.pop(key, None)
        env.update({name: str(path) for name, path in paths.items()})
        env.update(XDG_DATA_DIRS='/usr/local/share:/usr/share', XDG_CONFIG_DIRS='/etc/xdg',
            KDE_FULL_SESSION='true', KDE_SESSION_VERSION='6', XDG_CURRENT_DESKTOP='KDE',
            XDG_SESSION_TYPE='x11', QT_QPA_PLATFORM='xcb', QT_QUICK_BACKEND='software',
            QSG_RENDER_LOOP='basic', QML_DISABLE_DISK_CACHE='1',
            DBUS_SYSTEM_BUS_ADDRESS='unix:path=' + str(paths['XDG_RUNTIME_DIR'] / 'no-system-bus'),
            PULSE_SERVER='unix:' + str(paths['XDG_RUNTIME_DIR'] / 'no-audio'),
            IRIX_DOMAINOS_ACTIVATION_PRIVATE='1', IRIX_DOMAINOS_ACTIVATION_UI=str(output / 'UI.json'),
            IRIX_DOMAINOS_ACTIVATION_CAPTURE=str(output / 'panel-live.png'))
        run = subprocess.run(['xvfb-run', '--auto-servernum', '--server-args=-screen 0 1600x1000x24',
            'dbus-run-session', '--', sys.executable, str(SESSION_ENTRY),
            '--saida', str(output), '--internal-session'], env=env, capture_output=True, text=True, timeout=210)
        (output / 'session.log').write_text(run.stdout + run.stderr)
        worker_path = output / 'WORKER.json'
        report = json.loads(worker_path.read_text()) if worker_path.exists() else {'checks': {}, 'observations': {'error': 'Missing worker result'}}
        # Keep complete owned profiles/receipts in one artifact, so a nearly
        # exhausted /tmp inode budget cannot prevent saving recovery evidence.
        with tarfile.open(output / 'PRIVATE-PROFILE.tar.gz', 'w:gz') as archive:
            for key in ('XDG_CONFIG_HOME', 'XDG_STATE_HOME', 'XDG_DATA_HOME'):
                archive.add(paths[key], arcname=paths[key].name)
        report['checks']['personal_configs_untouched'] = all(digest(Path(name)) == value for name, value in protected_before.items())
        source_after = {name: digest(Path(name)) for name in source_before}
        report['observations']['production_sources_before'] = source_before
        report['observations']['production_sources_after'] = source_after
        report['observations']['production_sources_changed'] = [name for name, value in source_before.items() if source_after[name] != value]
        report['checks']['production_sources_unchanged_during_native_test'] = not report['observations']['production_sources_changed']
        report['checks']['private_session_completed'] = run.returncode == 0
        own_diagnostics = []
        for log in (output / 'plasma.log', output / 'plasma-restart.log'):
            for line in log.read_text().splitlines() if log.exists() else []:
                if any(component in line for component in ('org.irixclassic.domainos.panel/contents/', 'org.irixclassic.grosview/contents/')) and any(
                        marker in line for marker in ('TypeError:', 'ReferenceError:', 'SyntaxError:', 'Cannot assign', 'is not a type', 'Binding loop detected')):
                    own_diagnostics.append(line)
        report['observations']['own_qml_diagnostics'] = own_diagnostics
        report['checks']['production_applet_qml_errors_zero_including_removal'] = not own_diagnostics
    report['status'] = 'passed' if report['checks'] and all(report['checks'].values()) and 'error' not in report['observations'] else 'failed'
    (output / 'RESULTADO.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(output / 'RESULTADO.json')
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
