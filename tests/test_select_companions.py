# SPDX-License-Identifier: GPL-3.0-or-later
"""Companion-only changes in disposable profiles; no live KDE/GTK actions."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import select_companions as companions
from theme_transaction import Failure, decode, edit_ini, snapshot
from select_gtk import edit_gtkrc


class CompanionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='.companion-selection-test-', dir=ROOT)
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.data, self.config, self.state = [self.home / name for name in ('data', 'config', 'state')]
        self.paths = [self.config / 'Kvantum/kvantum.kvconfig',
                      *companions.gtk_paths(self.config, self.home)]
        for path in self.paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.name == 'kvantum.kvconfig':
                value = b'[General]\ntheme=Before\n[Applications]\nSpecial=Personal\n'
            elif path.name == 'settings.ini':
                value = b'[Settings]\ngtk-theme-name=Before\ngtk-font-name=Personal font 12\ngtk-cursor-theme-size=48\n'
            elif path.name == '.gtkrc-2.0':
                value = b'gtk-theme-name="Before"\ngtk-font-name="Personal font 12"\ngtk-cursor-theme-size=48\n'
            else:
                value = b'/* personal colors/decorations/imports */\n'
            path.write_bytes(value)
            path.chmod(0o640)
        for profile in companions.catalog()['profiles'].values():
            for path in [self.config / 'Kvantum' / profile['kvantum'] / (profile['kvantum'] + suffix)
                         for suffix in ('.kvconfig', '.svg')] + [
                    self.data / 'themes' / profile['gtk'] / ('gtk-' + version) /
                    ('gtkrc' if version == '2.0' else 'gtk.css')
                    for version in ('2.0', '3.0', '4.0')] + [
                    self.home / '.themes' / profile['gtk'] / 'gtk-2.0/gtkrc']:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('public resource fixture\n')
        self.globals = self.config / 'kdeglobals'
        self.globals.write_text('[KDE]\nLookAndFeelPackage=org.magpie.irixclassic.desktop\n'
                                '[General]\nColorScheme=IndependentColors\n[Sounds]\nEnable=false\n')
        self.protected = [self.globals, *[self.config / name for name in (
            'kwinrc', 'plasmarc', 'kcminputrc', 'ksplashrc', 'klaunchrc',
            'plasma-org.kde.plasma.desktop-appletsrc', 'konsolerc')]]
        for path in self.protected[1:]:
            path.write_text('Independent configuration ' + path.name + '\n')
            path.chmod(0o600)
        self.before = {path: snapshot(path) for path in self.paths}
        self.protected_before = {path: snapshot(path) for path in self.protected}
        self.theme = 'Before'
        self.settings = "'Before'"
        self.calls = []
        self.partial = None
        self.fail_setter = False
        self.fail_rollback = False
        self.after_setter = None
        for key, value in (('notify', self.notify), ('gsettings', self.gsettings)):
            p = patch.object(companions, key, side_effect=value)
            p.start(); self.addCleanup(p.stop)
        p = patch.dict(os.environ, {'GTK2_RC_FILES': ''})
        p.start(); self.addCleanup(p.stop)
        # All helper tests exercise the real public KConfig CLI against our
        # disposable files. It neither accesses a session bus nor mutates them.
        if not shutil.which('kreadconfig6'):
            self.skipTest('public kreadconfig6 is required for native precedence')

    def notify(self, theme=None):
        self.calls.append(('notify', theme))
        if theme is None:
            return self.theme
        if self.fail_rollback and theme == 'Before':
            raise OSError('native rollback bus unavailable')
        self.theme, self.settings = theme, repr(theme)
        for path in self.paths[1:]:
            if path.name == '.gtkrc-2.0':
                value = edit_gtkrc(path.read_bytes(), {'gtk-theme-name': theme})
            elif path.name == 'settings.ini':
                value = edit_ini(path.read_bytes(), 'Settings', {'gtk-theme-name': theme})
            else:
                continue
            path.write_bytes(value); path.chmod(0o644)
        if theme != 'Before':
            if self.partial:
                self.partial.write_bytes(decode(self.before[self.partial]))
            if self.after_setter:
                self.after_setter()
            if self.fail_setter:
                raise OSError('native GTK setter failed after partial writes')

    def gsettings(self, value=None):
        self.calls.append(('gsettings', value))
        if value is None:
            return self.settings
        self.settings = value

    def select(self, name='classic', **kwargs):
        return companions.select(name, self.data, self.config, self.state, self.home, **kwargs)

    def restore(self, **kwargs):
        return companions.restore(self.config, self.state, self.home, **kwargs)

    def receipt(self):
        base = self.state / 'irixium-companions'
        token = (base / 'latest').read_text().strip()
        file = base / token / 'receipt.json'
        return file, json.loads(file.read_text())

    def assert_protected_unchanged(self):
        self.assertEqual({path: snapshot(path) for path in self.protected}, self.protected_before)

    def assert_restored(self):
        self.assertEqual({path: snapshot(path) for path in self.paths}, self.before)

    def owned_kvantum_alias(self, *, theme='IrixClassic', alias=None):
        """Create consistent resource/control snapshots, never load a QStyle.

        Selection exercises the real public owned_selection reader. Painting
        and native notification delivery belong to the palette tests instead.
        """
        from kvantum_palette_runtime import generated_paths
        alias = alias or theme+'-KDE'
        selector_before = snapshot(self.paths[0])
        self.paths[0].write_bytes(edit_ini(decode(selector_before), 'General', {'theme': alias}))
        self.paths[0].chmod(selector_before['mode'])
        targets = generated_paths(self.config, theme)
        originals = {str(path): snapshot(path) for path in targets}
        for path in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('generated private resource '+path.name+'\n')
            path.chmod(0o644)
        source = {str(path): snapshot(path)['sha256'] for path in (
            self.config/'Kvantum'/theme/(theme+suffix) for suffix in ('.svg', '.kvconfig'))}
        control = self.state/'irixium-kvantum-palette'/theme/'control.json'
        control.parent.mkdir(parents=True, exist_ok=True)
        control.write_text(json.dumps({'format': 1, 'uid': os.getuid(), 'theme': theme,
            'targets': [str(path) for path in targets], 'selector': str(self.paths[0]),
            'originals': originals, 'after': {str(path): snapshot(path) for path in targets},
            'source': source, 'selector_before': selector_before,
            'selector_after': snapshot(self.paths[0]), 'signature': 'private-consistent-fixture'})+'\n')
        control.chmod(0o600)
        return control, targets

    def fixture_gtk_selection(self, theme):
        # Prepare the same three settings files that the callback mutates,
        # without recording a fake native setter in the action-under-test log.
        self.notify(theme)
        self.calls.clear()

    def test_dry_run_does_not_create_lock_or_journal_or_change_preferences(self):
        result = self.select(dry=True)
        self.assertEqual(result['status'], 'ready')
        self.assertFalse(self.state.exists())
        self.assertEqual(self.calls, [('notify', None), ('gsettings', None)])
        self.assert_restored(); self.assert_protected_unchanged()

    def test_apply_restore_ten_files_modes_and_native_state_without_global_changes(self):
        self.assertEqual(self.select()['status'], 'applied')
        _, record = self.receipt()
        self.assertEqual(len(record['files']), 10)
        self.assertEqual({Path(value['path']) for value in record['files']}, set(self.paths))
        self.assertEqual(companions.kvantum_theme(self.paths[0]), 'IrixClassic')
        self.assertIn(b'Special=Personal', self.paths[0].read_bytes())
        for path in self.paths:
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            if path.name in ('.gtkrc-2.0', 'settings.ini'):
                self.assertIn(b'Personal font 12', path.read_bytes())
                self.assertIn(b'48', path.read_bytes())
            elif path.name != 'kvantum.kvconfig':
                self.assertEqual(snapshot(path), self.before[path])
        self.assert_protected_unchanged()
        self.assertEqual(self.restore()['status'], 'restored')
        self.assert_restored(); self.assert_protected_unchanged()
        self.assertEqual((self.theme, self.settings), ('Before', "'Before'"))

    def test_repeated_matching_selection_is_noop_without_setter_or_new_backup(self):
        self.select(); receipt, before = self.receipt()
        tree = {str(path.relative_to(self.state)): path.read_bytes()
                for path in self.state.rglob('*') if path.is_file()}
        self.calls.clear()
        self.assertEqual(self.select()['status'], 'unchanged')
        self.assertFalse(any(value is not None for _, value in self.calls))
        self.assertEqual(self.receipt(), (receipt, before))
        self.assertEqual({str(path.relative_to(self.state)): path.read_bytes()
                          for path in self.state.rglob('*') if path.is_file()}, tree)

    def test_matching_owned_kvantum_and_gtk_reload_are_unchanged_after_observer_restart(self):
        control, targets = self.owned_kvantum_alias()
        gtk = companions.catalog()['profiles']['classic']['gtk']+'-Reload'
        self.fixture_gtk_selection(gtk)
        before = {path: snapshot(path) for path in [*self.paths, control, *targets]}
        state_before = {path: snapshot(path) for path in self.state.rglob('*') if path.is_file()}
        self.assertEqual(self.select()['status'], 'unchanged')
        self.assertEqual(self.calls, [('notify', None), ('gsettings', None)])
        self.assertEqual({path: snapshot(path) for path in before}, before)
        self.assertEqual({path: snapshot(path) for path in self.state.rglob('*') if path.is_file()}, state_before)
        self.assertFalse((self.state/'irixium-companions/latest').exists())
        self.assert_protected_unchanged()

    def test_gtk_mismatch_is_corrected_without_resetting_owned_kvantum_alias(self):
        control, targets = self.owned_kvantum_alias(alias='IrixClassic-KDE-Reload')
        own_before = {path: snapshot(path) for path in [self.paths[0], control, *targets]}
        self.assertEqual(self.select()['status'], 'applied')
        gtk = companions.catalog()['profiles']['classic']['gtk']
        self.assertEqual((self.theme, self.settings), (gtk, repr(gtk)))
        companions.verify_theme_files(self.paths[1:], gtk)
        self.assertEqual([value for key, value in self.calls if key == 'notify' and value is not None], [gtk])
        self.assertEqual({path: snapshot(path) for path in own_before}, own_before)
        self.assert_protected_unchanged()

    def test_unreceipted_aliases_and_old_global_family_are_not_preserved(self):
        gtk = companions.catalog()['profiles']['classic']['gtk']+'-Reload'
        self.fixture_gtk_selection(gtk)
        for alias in ('IrixClassic-KDE', 'IrixClassic-KDE-Reload'):
            with self.subTest(unreceipted_alias=alias):
                self.paths[0].write_bytes(edit_ini(self.paths[0].read_bytes(), 'General', {'theme': alias}))
                self.assertEqual(self.select()['status'], 'applied')
                self.assertEqual(companions.kvantum_theme(self.paths[0]), 'IrixClassic')
                self.assertFalse((self.state/'irixium-kvantum-palette/IrixClassic/control.json').exists())
                self.assert_protected_unchanged()
        control, targets = self.owned_kvantum_alias()
        resources = {path: snapshot(path) for path in [control, *targets]}
        self.globals.write_text('[KDE]\nLookAndFeelPackage=org.magpie.irixium.desktop\n'
                                '[General]\nColorScheme=IndependentColors\n[Sounds]\nEnable=false\n')
        global_before = snapshot(self.globals)
        self.assertEqual(self.select('moderno')['status'], 'applied')
        self.assertEqual(companions.kvantum_theme(self.paths[0]), 'Irixium')
        self.assertEqual(self.theme, companions.catalog()['profiles']['moderno']['gtk'])
        self.assertEqual(snapshot(self.globals), global_before)
        self.assertEqual({path: snapshot(path) for path in resources}, resources)
        self.assertEqual({path: snapshot(path) for path in self.protected[1:]},
                         {path: self.protected_before[path] for path in self.protected[1:]})

    def test_moderno_requires_selected_moderno_and_uses_its_own_companions(self):
        self.globals.write_text('[KDE]\nLookAndFeelPackage=org.magpie.irixium.desktop\n')
        self.assertEqual(self.select('moderno')['status'], 'applied')
        self.assertEqual(self.theme, 'Irixium-KDE')
        self.assertEqual(companions.kvantum_theme(self.paths[0]), 'Irixium')
        self.assertEqual(self.globals.read_text(), '[KDE]\nLookAndFeelPackage=org.magpie.irixium.desktop\n')

    def test_other_global_theme_refuses_before_queries_or_writes(self):
        self.globals.write_text('[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n')
        with self.assertRaisesRegex(Failure, 'Tema Global efetivo'):
            self.select()
        self.assertEqual(self.calls, []); self.assertFalse(self.state.exists()); self.assert_restored()

    def test_native_kdedefaults_precedence_empty_deleted_and_immutable(self):
        fallback = self.config / 'kdedefaults/kdeglobals'
        fallback.parent.mkdir()
        fallback.write_text('[KDE]\nLookAndFeelPackage=org.magpie.irixclassic.desktop\n')
        for text, expected in (
            ('[KDE]\n', 'org.magpie.irixclassic.desktop'),
            ('[KDE]\nLookAndFeelPackage=\n', ''),
            ('[KDE]\nLookAndFeelPackage[$d]=\n', ''),
            ('[KDE]\nLookAndFeelPackage[$i]=org.magpie.irixium.desktop\n', 'org.magpie.irixium.desktop')):
            self.globals.write_text(text)
            self.assertEqual(companions.effective_look_and_feel(self.config), expected)
        self.globals.write_text('[KDE]\n')
        self.assertEqual(self.select()['status'], 'applied')

    def test_missing_companion_asset_refuses_before_native_actions_and_journal(self):
        (self.config / 'Kvantum/IrixClassic/IrixClassic.svg').unlink()
        with self.assertRaisesRegex(Failure, 'Companion instalado ausente'):
            self.select()
        self.assertEqual(self.calls, []); self.assertFalse(self.state.exists()); self.assert_restored()

    def test_native_gtk2_partial_write_rolls_back_without_false_success(self):
        self.partial = self.paths[1]
        self.check_partial()

    def test_native_gtk3_partial_write_rolls_back_without_false_success(self):
        self.partial = self.config / 'gtk-3.0/settings.ini'
        self.check_partial()

    def test_native_gtk4_partial_write_rolls_back_without_false_success(self):
        self.partial = self.config / 'gtk-4.0/settings.ini'
        self.check_partial()

    def check_partial(self):
        with self.assertRaisesRegex(Failure, 'seleção GTK não foi confirmada'):
            self.select()
        self.assert_restored(); self.assert_protected_unchanged()
        self.assertEqual(self.receipt()[1]['status'], 'failed_restored')
        self.assertEqual((self.theme, self.settings), ('Before', "'Before'"))

    def test_native_setter_bus_failure_restores_all_files_and_reports_original_error(self):
        self.fail_setter = True
        with self.assertRaisesRegex(OSError, 'native GTK setter failed'):
            self.select()
        self.assert_restored(); self.assert_protected_unchanged()
        self.assertEqual(self.receipt()[1]['status'], 'failed_restored')

    def test_failed_native_rollback_recovers_files_but_blocks_automatic_retry(self):
        self.fail_setter = True; self.fail_rollback = True
        with self.assertRaisesRegex(Failure, 'setter failed.*rollback bus unavailable'):
            self.select()
        self.assert_restored(); self.assert_protected_unchanged()
        self.assertEqual(self.settings, "'Before'")
        self.assertEqual(self.receipt()[1]['status'], 'recovery_needed')
        self.calls.clear()
        with self.assertRaisesRegex(Failure, 'seleção interrompida'):
            self.select()
        self.assertEqual(self.calls, [])

    def test_global_changed_during_selection_restores_companions_not_user_global_choice(self):
        self.after_setter = lambda: self.globals.write_text('[KDE]\nLookAndFeelPackage=org.magpie.irixium.desktop\n')
        with self.assertRaisesRegex(Failure, 'Tema Global efetivo'):
            self.select()
        self.assert_restored()
        self.assertIn('org.magpie.irixium.desktop', self.globals.read_text())

    def test_restore_dry_run_preserves_files_journal_and_native_state(self):
        self.select(); receipt, record = self.receipt()
        after = {path: snapshot(path) for path in self.paths}; self.calls.clear()
        self.assertEqual(self.restore(dry=True)['status'], 'restore_ready')
        self.assertEqual({path: snapshot(path) for path in self.paths}, after)
        self.assertEqual(self.receipt(), (receipt, record))
        self.assertFalse(any(value is not None for _, value in self.calls))

    def test_restore_refuses_later_css_edit_before_native_mutation(self):
        self.select(); edited = self.config / 'gtk-4.0/colors.css'
        edited.write_text('/* later independent colors */\n'); self.calls.clear()
        with self.assertRaisesRegex(Failure, 'alterados após'):
            self.restore()
        self.assertEqual(edited.read_text(), '/* later independent colors */\n')
        self.assertEqual(self.calls, [])

    def test_restore_refuses_global_change_without_reapplying_old_theme(self):
        self.select(); self.globals.write_text('[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n')
        self.calls.clear()
        with self.assertRaisesRegex(Failure, 'Tema Global efetivo'):
            self.restore()
        self.assertEqual(self.calls, [])

    def test_incomplete_receipt_cannot_restore_or_overwrite_unrecorded_files(self):
        self.select(); receipt, record = self.receipt()
        record['files'].pop(); receipt.write_text(json.dumps(record)); self.calls.clear()
        with self.assertRaisesRegex(Failure, 'não corresponde'):
            self.restore()
        self.assertEqual(self.calls, [])

    def test_malformed_native_receipt_is_rejected_before_native_calls(self):
        self.select(); receipt, record = self.receipt()
        record.pop('theme_before'); receipt.write_text(json.dumps(record)); self.calls.clear()
        with self.assertRaisesRegex(Failure, 'Recibo de companions inválido'):
            self.restore()
        self.assertEqual(self.calls, [])

    def test_symlink_target_refuses_before_native_mutation(self):
        target = self.config / 'gtk-4.0/colors.css'
        elsewhere = self.home / 'unrelated.css'; elsewhere.write_text('keep\n')
        target.unlink(); target.symlink_to(elsewhere)
        with self.assertRaisesRegex(Failure, 'Link simbólico'):
            self.select()
        self.assertEqual(self.calls, []); self.assertFalse(self.state.exists())
        self.assertEqual(elsewhere.read_text(), 'keep\n')

    def test_concurrent_selection_lock_refuses_without_native_setter(self):
        state = self.state / 'irixium-companions'
        state.mkdir(parents=True)
        with (state / 'lock').open('a+b') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(Failure, 'Outra seleção'):
                self.select()
        self.assertFalse(any(value is not None for _, value in self.calls))
        self.assertFalse((state / 'latest').exists()); self.assert_restored()

    def test_final_journal_failure_restores_companions_and_keeps_failure_receipt(self):
        original = companions.save
        def failing_save(receipt, record):
            if record['status'] == 'applied':
                raise OSError('final companion receipt failed')
            original(receipt, record)
        with patch.object(companions, 'save', side_effect=failing_save), \
                self.assertRaisesRegex(OSError, 'final companion receipt failed'):
            self.select()
        self.assert_restored(); self.assert_protected_unchanged()
        self.assertEqual(self.receipt()[1]['status'], 'failed_restored')

    def test_gsettings_mismatch_does_not_report_false_success(self):
        self.after_setter = lambda: setattr(self, 'settings', "'Different'" )
        with self.assertRaisesRegex(Failure, 'GSettings não confirmou'):
            self.select()
        self.assert_restored(); self.assert_protected_unchanged()

    def test_kvantum_protected_key_refuses_before_native_or_target_mutation(self):
        self.paths[0].write_text('[General]\ntheme[$i]=Personal\n')
        previous = snapshot(self.paths[0])
        with self.assertRaisesRegex(Failure, 'Chave duplicada ou protegida'):
            self.select()
        self.assertEqual(snapshot(self.paths[0]), previous)
        self.assertFalse(any(value is not None for _, value in self.calls))
        self.assertFalse((self.state / 'irixium-companions/latest').exists())

    def test_restore_bus_failure_still_recovers_ten_files_with_honest_status(self):
        self.select(); self.fail_rollback = True
        with self.assertRaisesRegex(Failure, 'rollback bus unavailable'):
            self.restore()
        self.assert_restored()
        self.assertEqual(self.receipt()[1]['status'], 'recovery_needed')


if __name__ == '__main__':
    unittest.main()
