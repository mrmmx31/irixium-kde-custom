# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional Classic hook: ownership, transaction and checkout independence."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import classic_hook_runtime as hook
import install_suite
import user_bundle
from theme_transaction import Failure, snapshot
from user_bundle import Bundle, fingerprint


class HookMigrationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='irix-hook-tests-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.profile = self.root / 'profile with % $ " quote'
        self.data, self.config, self.state = (self.profile / name for name in ('data', 'config', 'state'))
        self.runtime, self.service, self.bookkeeping = hook.locations(self.data, self.config, self.state)

    def write_service(self, command=None):
        self.service.parent.mkdir(parents=True, exist_ok=True)
        command = command or ('ExecStart=' + str(hook.ROOT / 'classic-rewrite-rc1/hooks/irix-classic-user.sh'))
        self.service.write_text('[Unit]\nDescription=Preserved\n[Service]\nType=oneshot\n' + command + '\n[Install]\nWantedBy=graphical-session.target\n')
        self.service.chmod(0o640)
        return snapshot(self.service)

    def migrate(self, source=hook.ROOT, dry=False):
        with patch.object(hook, 'reload_user_manager') as reload, redirect_stdout(io.StringIO()):
            result = hook.migrate(source, self.data, self.config, self.state, dry=dry)
        return result, reload

    def test_dry_migration_performs_no_writes_or_reload(self):
        before = self.write_service()
        changed, reload = self.migrate(dry=True)
        self.assertFalse(changed)
        self.assertEqual(snapshot(self.service), before)
        self.assertFalse(self.data.exists())
        self.assertFalse(self.state.exists())
        reload.assert_not_called()

    def test_exact_legacy_commands_migrate_once_and_preserve_settings(self):
        for command in sorted(hook.legacy_commands(hook.ROOT)):
            with self.subTest(command=command), tempfile.TemporaryDirectory(dir=self.root) as directory:
                base = Path(directory)
                data, config, state = (base / name for name in ('data', 'config', 'state'))
                runtime, service, bookkeeping = hook.locations(data, config, state)
                service.parent.mkdir(parents=True)
                original = ('[Unit]\nDescription=Preserved\n[Service]\nType=oneshot\n'
                            'Environment=ONE=1\nEnvironment=TWO=2\n' + command + '\n'
                            'TimeoutStartSec=19\n[Install]\nWantedBy=graphical-session.target\n')
                service.write_text(original)
                service.chmod(0o640)
                with patch.object(hook, 'reload_user_manager') as reload, redirect_stdout(io.StringIO()):
                    self.assertTrue(hook.migrate(hook.ROOT, data, config, state))
                    self.assertFalse(hook.migrate(hook.ROOT, data, config, state))
                reload.assert_called_once_with()
                updated = service.read_text()
                self.assertIn(hook.execution_line(runtime), updated)
                self.assertIn('Environment=ONE=1\nEnvironment=TWO=2\n', updated)
                self.assertIn('TimeoutStartSec=19\n', updated)
                self.assertNotIn(str(hook.ROOT), updated)
                self.assertEqual(service.stat().st_mode & 0o777, 0o640)
                expected = {relative: hashlib.sha256(path.read_bytes()).hexdigest() for path, relative in hook.source_files(hook.ROOT)}
                self.assertEqual(fingerprint(runtime), expected)
                self.assertEqual(Bundle(bookkeeping, (runtime, service)).latest()[1]['status'], 'installed')

    def test_suite_passes_all_xdg_roots(self):
        with patch.object(hook, 'migrate', return_value=True) as migrate:
            self.assertTrue(install_suite.migrate_user_hook(self.data, self.config, self.state, dry=True))
        migrate.assert_called_once_with(install_suite.ROOT, self.data, self.config, self.state, dry=True)

    def test_unrelated_and_ambiguous_commands_are_preserved(self):
        commands = ['ExecStart=/other/checkout/decorations/classic/hooks/irix-classic-user.sh',
                    'ExecStart=' + str(hook.ROOT / 'decorations/classic/hooks/irix-classic-user.sh') + ' --custom',
                    'ExecStart=\nExecStart=' + str(hook.ROOT / 'decorations/classic/hooks/irix-classic-user.sh'),
                    'ExecStart=' + str(hook.ROOT / 'decorations/classic/hooks/irix-classic-user.sh') + '\\\n extra',
                    'ExecStart=' + str(hook.ROOT / 'decorations/classic/hooks/irix-classic-user.sh') + '\n[Service]\nExecStart=/other']
        for command in commands:
            with self.subTest(command=command):
                before = self.write_service(command)
                changed, reload = self.migrate()
                self.assertFalse(changed)
                reload.assert_not_called()
                self.assertEqual(snapshot(self.service), before)
                self.assertFalse(self.data.exists())
                self.assertFalse(self.state.exists())

    def test_systemd_quoting_preserves_literal_punctuation(self):
        value = '/tmp/space % $ " back\\slash'
        self.assertEqual(hook.quoted(value), '"/tmp/space %% $$ \\" back\\\\slash"')
        self.assertEqual(hook.quoted(value, command=False), '"/tmp/space %% $ \\" back\\\\slash"')
        for control in ('\n', '\r', '\t', '\x00', '\x7f'):
            with self.subTest(control=repr(control)), self.assertRaises(Failure):
                hook.quoted('/tmp/' + control)
        unit = hook.service_content(self.runtime, self.data, self.config, self.state).decode()
        self.assertEqual(hook.exact_command(unit), hook.execution_line(self.runtime).removeprefix('ExecStart='))
        self.assertIn('%% $$ \\" quote', unit)
        self.assertIn('Environment="XDG_DATA_HOME=' + str(self.data).replace('%', '%%').replace('"', '\\"'), unit)

    def test_opt_in_repeated_install_enables_and_starts_only_when_invoked(self):
        with patch.object(hook.subprocess, 'run') as run, redirect_stdout(io.StringIO()):
            hook.install_opt_in(hook.ROOT, self.data, self.config, self.state, dry=True)
            run.assert_not_called()
            self.assertFalse(self.data.exists())
            self.assertFalse(self.config.exists())
            self.assertFalse(self.state.exists())
            hook.install_opt_in(hook.ROOT, self.data, self.config, self.state)
            hook.install_opt_in(hook.ROOT, self.data, self.config, self.state)
        expected = [['systemctl', '--user', 'daemon-reload'], ['systemctl', '--user', 'enable', hook.UNIT], ['systemctl', '--user', 'start', hook.UNIT]]
        self.assertEqual([call.args[0] for call in run.call_args_list], expected * 2)
        self.assertTrue(all(call.kwargs == {'check': True} for call in run.call_args_list))
        self.assertEqual(len(list(self.bookkeeping.glob('backups/*/receipt.json'))), 1)

    def test_opt_in_refuses_custom_service(self):
        before = self.write_service('ExecStart=/other/custom-service')
        with self.assertRaises(Failure), patch.object(hook.subprocess, 'run') as run:
            hook.install_opt_in(hook.ROOT, self.data, self.config, self.state)
        run.assert_not_called()
        self.assertEqual(snapshot(self.service), before)
        self.assertFalse(self.data.exists())
        self.assertFalse(self.state.exists())

    def test_migration_reloads_only_without_enable_or_start(self):
        self.write_service()
        with patch.dict(os.environ, {'DBUS_SESSION_BUS_ADDRESS': 'private-test'}), patch.object(hook.shutil, 'which', return_value='/fake/systemctl'), patch.object(hook.subprocess, 'run') as run, redirect_stdout(io.StringIO()):
            run.return_value.returncode = 0
            self.assertTrue(hook.migrate(hook.ROOT, self.data, self.config, self.state))
        run.assert_called_once_with(['systemctl', '--user', 'daemon-reload'], capture_output=True, text=True)

    def test_restore_recovers_exact_original_service_and_removes_runtime(self):
        before = self.write_service()
        self.migrate()
        installed = snapshot(self.service)
        with patch.object(hook, 'reload_user_manager') as reload, redirect_stdout(io.StringIO()):
            hook.restore(self.data, self.config, self.state, dry=True)
            self.assertEqual(snapshot(self.service), installed)
            self.assertTrue(self.runtime.is_dir())
            reload.assert_not_called()
            hook.restore(self.data, self.config, self.state)
        reload.assert_called_once_with()
        self.assertEqual(snapshot(self.service), before)
        self.assertFalse(self.runtime.exists())
        self.assertEqual(Bundle(self.bookkeeping, (self.runtime, self.service)).latest()[1]['status'], 'restored')

    def test_modified_runtime_is_preserved_and_not_started(self):
        self.write_service()
        self.migrate()
        marker = self.runtime / 'tools/manage.py'
        marker.write_text(marker.read_text() + '\n# private edit\n')
        before = fingerprint(self.runtime)
        with self.assertRaises(Failure), patch.object(hook.subprocess, 'run') as run:
            hook.install_opt_in(hook.ROOT, self.data, self.config, self.state)
        self.assertEqual(fingerprint(self.runtime), before)
        run.assert_not_called()

    def test_symlink_destination_is_refused_without_writes(self):
        self.profile.mkdir(parents=True)
        self.data.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(Failure):
            hook.install_opt_in(hook.ROOT, self.data, self.config, self.state, dry=True)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.state.exists())

    def test_unit_rename_failure_rolls_back_both_resources(self):
        before = self.write_service()
        original_replace = os.replace
        attempted = []
        def fail_unit_stage(source, destination):
            if Path(destination) == self.service and '.stage-' in Path(source).name and not attempted:
                attempted.append(True)
                raise OSError('injected unit rename failure')
            return original_replace(source, destination)
        with patch.object(user_bundle.os, 'replace', side_effect=fail_unit_stage), patch.object(hook, 'reload_user_manager') as reload, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(OSError, 'injected unit rename failure'):
                hook.migrate(hook.ROOT, self.data, self.config, self.state)
        self.assertEqual(attempted, [True])
        reload.assert_not_called()
        self.assertEqual(snapshot(self.service), before)
        self.assertFalse(self.runtime.exists())
        self.assertEqual(Bundle(self.bookkeeping, (self.runtime, self.service)).latest()[1]['status'], 'restored')

    def test_extracted_checkout_can_be_deleted_before_real_native_hook_runs(self):
        if not shutil.which('kreadconfig6') or not shutil.which('kwriteconfig6'):
            self.skipTest('Native KDE configuration tools are required for this proof.')
        archive = self.root / 'classic-hook-source.zip'
        with zipfile.ZipFile(archive, 'w') as zipped:
            for source, relative in hook.source_files(hook.ROOT):
                zipped.write(source, 'decorations/classic/' + relative)
        checkout = self.root / 'extracted checkout with % $ " quote'
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(checkout)
        before = self.write_service('ExecStart=' + hook.quoted(checkout / 'decorations/classic/hooks/irix-classic-user.sh'))
        self.migrate(checkout)
        runtime_before = fingerprint(self.runtime)
        shutil.rmtree(checkout)
        self.assertFalse(checkout.exists())
        kwinrc = self.config / 'kwinrc'
        kwinrc.write_bytes(b'[org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae\ntheme=org.example.selected\n\n[PrivateTest]\nmarker=preserved\n')
        kwinrc_before = snapshot(kwinrc)
        env = dict(os.environ)
        env.update({'HOME': str(self.profile), 'XDG_DATA_HOME': str(self.data), 'XDG_CONFIG_HOME': str(self.config), 'XDG_STATE_HOME': str(self.state), 'XDG_CACHE_HOME': str(self.profile / 'cache'), 'XDG_CONFIG_DIRS': str(self.profile / 'config-dirs'), 'XDG_DATA_DIRS': '/usr/local/share:/usr/share', 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=' + str(self.root / 'absent-session-bus'), 'DBUS_SYSTEM_BUS_ADDRESS': 'unix:path=' + str(self.root / 'absent-system-bus'), 'QT_QPA_PLATFORM': 'offscreen', 'PYTHONDONTWRITEBYTECODE': '1'})
        for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'XDG_RUNTIME_DIR'):
            env.pop(key, None)
        arguments = ['/usr/bin/python3', str(self.runtime / 'tools/manage.py'), '--hook', '--destino', 'irixium_irix_classic_v4']
        first = subprocess.run(arguments, env=env, capture_output=True, text=True, timeout=40)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        installed = self.data / 'kwin/decorations/irixium_irix_classic_v4'
        self.assertEqual(json.loads((installed / 'metadata.json').read_text())['KPlugin']['Id'], 'irixium_irix_classic_v4')
        self.assertEqual(snapshot(kwinrc), kwinrc_before)
        backup_count = len(list((self.state / 'irix-classic').glob('backups/*')))
        second = subprocess.run(arguments, env=env, capture_output=True, text=True, timeout=40)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(snapshot(kwinrc), kwinrc_before)
        self.assertEqual(fingerprint(self.runtime), runtime_before)
        self.assertEqual(len(list((self.state / 'irix-classic').glob('backups/*'))), backup_count)
        self.assertNotIn(str(checkout), self.service.read_text())
        with patch.object(hook, 'reload_user_manager'), redirect_stdout(io.StringIO()):
            hook.restore(self.data, self.config, self.state)
        self.assertEqual(snapshot(self.service), before)
        self.assertFalse(self.runtime.exists())
        self.assertEqual(snapshot(kwinrc), kwinrc_before)


if __name__ == '__main__':
    unittest.main()
