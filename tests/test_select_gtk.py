# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import select_gtk
import apply_suite
from theme_transaction import Failure, edit_ini, replace_checked, snapshot


class GtkSelectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='.gtk-selection-test-',dir=ROOT); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.data, self.config, self.state = [self.home/name for name in ('data', 'config', 'state')]
        self.paths = select_gtk.gtk_paths(self.config, self.home)
        for path in self.paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.name == 'settings.ini':
                path.write_bytes(b'[Settings]\ngtk-theme-name=Before\ngtk-font-name=User font 12\ngtk-cursor-theme-size=48\n')
            elif path.name == '.gtkrc-2.0':
                path.write_bytes(b'gtk-theme-name="Before"\ngtk-font-name="User font 12"\ngtk-cursor-theme-size=48\n')
            elif path.name in ('gtk.css','colors.css'):
                path.write_bytes(b'/* independent user color choice */\n')
            else:
                path.write_bytes(b'/* private decoration choice */\n')
            path.chmod(0o640)
        self.before = {path: snapshot(path) for path in self.paths}
        for theme in {profile['gtk'] for profile in select_gtk.catalog()['profiles'].values()}:
            legacy = self.home/'.themes'/theme/'gtk-2.0/gtkrc'
            legacy.parent.mkdir(parents=True, exist_ok=True); legacy.write_text('fixture')
            for version in ('2.0', '3.0', '4.0'):
                path = self.data/'themes'/theme/('gtk-'+version)/('gtkrc' if version == '2.0' else 'gtk.css')
                path.parent.mkdir(parents=True, exist_ok=True); path.write_text('fixture')
        self.theme = 'Before'; self.settings = "'Before'"
        self.events = []
        self.fail_verify = False; self.fail_restore_notify = False; self.fail_final_settings = False
        self.write_generated_colors = False
        self.settings_reads = 0

    def notify(self, theme=None):
        self.events.append(('notify', theme))
        if theme is None:
            if self.fail_verify and self.theme != 'Before': raise OSError('original native verification failure')
            return self.theme
        if self.fail_restore_notify and theme == 'Before': raise OSError('rollback bus unavailable')
        self.theme = theme; self.settings = repr(theme)
        for path in self.paths:
            if path.name == '.gtkrc-2.0':
                contents = select_gtk.edit_gtkrc(path.read_bytes(), {'gtk-theme-name': theme})
            elif path.name == 'settings.ini':
                contents = edit_ini(path.read_bytes(), 'Settings', {'gtk-theme-name': theme})
            elif path.name == 'window_decorations.css':
                contents = ('/* KDE decoration for '+theme+' */\n').encode()
            else:
                continue
            path.write_bytes(contents); path.chmod(0o644)
        if self.write_generated_colors and theme != 'Before':
            for version in ('3.0','4.0'):
                css=self.config/('gtk-'+version)/'gtk.css'
                css.write_bytes(css.read_bytes()+b"@import 'colors.css';\n")
                colors=css.parent/'colors.css'
                colors.write_bytes(b'@define-color theme_bg_color_breeze #abcdef;\n')
                css.chmod(0o644); colors.chmod(0o644)

    def gsettings(self, value=None):
        self.events.append(('gsettings', value))
        if value is not None:
            self.settings = value; return
        self.settings_reads += 1
        if self.fail_final_settings and self.settings_reads == 2: raise OSError('final GSettings query failed')
        return self.settings

    def run_main(self, *args):
        with patch.object(sys, 'argv', ['select_gtk', *args]), \
             patch('reload_decoration.check_session'), \
             patch('install_suite.roots', return_value=(self.data, self.config, self.state)), \
             patch.object(select_gtk.Path, 'home', return_value=self.home), \
             patch.dict(os.environ, {'GTK2_RC_FILES': ''}), \
             patch.object(select_gtk, 'notify', side_effect=self.notify), \
             patch.object(select_gtk, 'gsettings', side_effect=self.gsettings), \
             redirect_stdout(io.StringIO()):
            select_gtk.main()

    def receipt(self):
        paths = list(self.state.glob('irixium-gtk-selection/*/receipt.json'))
        self.assertEqual(len(paths), 1)
        return json.loads(paths[0].read_text())

    def assert_files_restored(self):
        self.assertEqual({p: snapshot(p) for p in self.paths}, self.before)

    def test_dry_run_queries_native_theme_without_writing_anything(self):
        self.run_main('classic', '--verificar')
        self.assert_files_restored(); self.assertFalse(self.state.exists())
        self.assertEqual(self.events, [('notify', None), ('gsettings', None)])

    def test_domainos_selection_and_restore_preserve_independent_font_and_cursor_size(self):
        self.run_main('domainos')
        self.assertEqual(self.theme,'DomainOS-SR10-4-KDE')
        self.assertEqual(self.settings,"'DomainOS-SR10-4-KDE'")
        for path in self.paths:
            if path.name in ('settings.ini','.gtkrc-2.0'):
                self.assertIn(b'User font 12',path.read_bytes());self.assertIn(b'48',path.read_bytes())
        self.run_main('--restaurar');self.assert_files_restored()

    def test_apply_and_restore_keep_exact_file_bytes_modes_and_native_preferences(self):
        self.run_main('classic')
        record = self.receipt()
        self.assertEqual(record['status'], 'applied')
        self.assertEqual({Path(v['path']): v['before'] for v in record['files']}, self.before)
        self.assertEqual(self.theme, 'IrixClassic-KDE'); self.assertEqual(self.settings, "'IrixClassic-KDE'")
        for path in self.paths:
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            if path.name in ('settings.ini', '.gtkrc-2.0'):
                self.assertIn(b'User font 12', path.read_bytes())
                self.assertIn(b'48', path.read_bytes())
        self.run_main('--restaurar')
        self.assert_files_restored()
        self.assertEqual(self.theme, 'Before'); self.assertEqual(self.settings, "'Before'")
        self.assertEqual(self.receipt()['status'], 'restored')

    def assert_partial_native_selection_is_recovered(self, target):
        original=self.notify
        before=target.read_bytes()
        colors={}
        for version in ('3.0','4.0'):
            for name in ('gtk.css','colors.css'):
                path=self.config/('gtk-'+version)/name
                colors[path]=snapshot(path)
        def partial(theme=None):
            value=original(theme)
            if theme is not None and theme!='Before': target.write_bytes(before)
            return value
        self.notify=partial
        with self.assertRaisesRegex(Failure,'seleção GTK não foi confirmada'):
            self.run_main('classic')
        self.assert_files_restored()
        self.assertEqual(self.theme,'Before'); self.assertEqual(self.settings,"'Before'")
        self.assertEqual(self.receipt()['status'],'failed_restored')
        self.assertFalse((self.state/'irixium-gtk-selection/latest').exists())
        self.assertEqual({p:snapshot(p) for p in colors},colors)

    def test_native_gtk2_partial_write_does_not_report_success(self):
        self.assert_partial_native_selection_is_recovered(self.paths[0])

    def test_native_gtk3_partial_write_does_not_report_success(self):
        self.assert_partial_native_selection_is_recovered(self.config/'gtk-3.0/settings.ini')

    def test_native_gtk4_partial_write_does_not_report_success(self):
        self.assert_partial_native_selection_is_recovered(self.config/'gtk-4.0/settings.ini')

    def test_confirmation_uses_last_gtk2_assignment_and_literal_ini_values(self):
        self.notify('IrixClassic')
        select_gtk.verify_theme_files(self.paths,'IrixClassic')
        with self.paths[0].open('a') as stream:
            stream.write('gtk-theme-name = "Before" # explicit later choice\n')
        with self.assertRaisesRegex(Failure,'seleção GTK não foi confirmada'):
            select_gtk.verify_theme_files(self.paths,'IrixClassic')
        self.paths[0].write_text('gtk-theme-name="IrixClassic"\n')
        settings=self.config/'gtk-4.0/settings.ini'
        settings.write_text('[DEFAULT]\ngtk-theme-name=IrixClassic\n[Settings]\nother=value\n')
        with self.assertRaisesRegex(Failure,'seleção GTK não foi confirmada'):
            select_gtk.verify_theme_files(self.paths,'IrixClassic')

    def test_generated_css_imports_and_colors_are_saved_and_restored_exactly(self):
        self.write_generated_colors=True
        self.run_main('classic')
        record=self.receipt()
        self.assertEqual(record['format'],2)
        self.assertEqual({Path(v['path']) for v in record['files']},set(self.paths))
        for path in self.paths:
            if path.name in ('gtk.css','colors.css'):
                self.assertNotEqual(snapshot(path),self.before[path])
        self.run_main('--restaurar'); self.assert_files_restored()

    def test_failed_native_verification_restores_generated_css_bytes_and_modes(self):
        self.write_generated_colors=True; self.fail_verify=True
        with self.assertRaisesRegex(OSError,'original native verification failure'):
            self.run_main('classic')
        self.assert_files_restored()
        self.assertEqual(self.receipt()['status'],'failed_restored')

    def test_old_five_file_receipt_restores_only_its_original_scope(self):
        self.run_main('classic')
        record=self.receipt(); record.pop('format')
        record['files']=[v for v in record['files']
            if Path(v['path']).name not in ('gtk.css','colors.css')]
        receipt=next(self.state.glob('irixium-gtk-selection/*/receipt.json'))
        receipt.write_text(json.dumps(record))
        colors={path:snapshot(path) for path in self.paths if path.name in ('gtk.css','colors.css')}
        self.run_main('--restaurar'); self.assert_files_restored()
        self.assertEqual({p:snapshot(p) for p in colors},colors)

    def test_new_receipt_missing_generated_css_is_refused_before_native_changes(self):
        self.run_main('classic')
        record=self.receipt(); record['files']=[v for v in record['files']
            if Path(v['path']).name!='colors.css']
        receipt=next(self.state.glob('irixium-gtk-selection/*/receipt.json'))
        receipt.write_text(json.dumps(record)); self.events.clear()
        with self.assertRaisesRegex(Failure,'não corresponde'):
            self.run_main('--restaurar')
        self.assertEqual(self.events,[])

    def test_generated_css_user_edit_refuses_restore_without_native_mutation(self):
        self.run_main('classic')
        css=self.config/'gtk-4.0/gtk.css'
        css.write_text('/* later independent user choice */\n'); self.events.clear()
        with self.assertRaisesRegex(Failure,'alteradas após'):
            self.run_main('--restaurar')
        self.assertEqual(css.read_text(),'/* later independent user choice */\n')
        self.assertFalse(any(value is not None for _,value in self.events))

    def test_native_rollback_failure_does_not_block_gsettings_or_five_file_recovery(self):
        self.fail_verify = True; self.fail_restore_notify = True
        with self.assertRaisesRegex(Failure, 'original native verification failure.*rollback bus unavailable'):
            self.run_main('classic')
        self.assert_files_restored(); self.assertEqual(self.settings, "'Before'")
        record = self.receipt()
        self.assertEqual(record['status'], 'recovery_needed')
        self.assertIn('original native verification failure', record['error'])
        self.assertIn('rollback bus unavailable', record['recovery_errors'][0])
        self.assertFalse((self.state/'irixium-gtk-selection/latest').exists())

    def test_final_native_query_failure_also_rolls_back_and_records_original_error(self):
        self.fail_final_settings = True
        with self.assertRaisesRegex(OSError, 'final GSettings query failed'):
            self.run_main('classic')
        self.assert_files_restored(); self.assertEqual(self.theme, 'Before')
        self.assertEqual(self.receipt()['status'], 'failed_restored')

    def test_final_receipt_failure_rolls_back_selection(self):
        original = select_gtk.atomic
        def failing_atomic(path, contents, *args, **kwargs):
            if path.name == 'receipt.json' and json.loads(contents)['status'] == 'applied':
                raise OSError('final journal write failed')
            return original(path, contents, *args, **kwargs)
        with patch.object(select_gtk, 'atomic', side_effect=failing_atomic), \
             self.assertRaisesRegex(OSError, 'final journal write failed'):
            self.run_main('classic')
        self.assert_files_restored(); self.assertEqual(self.theme, 'Before')
        self.assertEqual(self.receipt()['status'], 'failed_restored')

    def test_restore_native_bus_failure_still_restores_files_and_gsettings(self):
        self.run_main('classic'); self.fail_restore_notify = True
        with self.assertRaisesRegex(Failure, 'rollback bus unavailable'):
            self.run_main('--restaurar')
        self.assert_files_restored(); self.assertEqual(self.settings, "'Before'")
        self.assertEqual(self.receipt()['status'], 'recovery_needed')

    def test_rollback_file_failure_does_not_skip_remaining_paths(self):
        self.fail_verify = True
        def recovery(path, expected, desired):
            if path == self.paths[0]: raise OSError('first file blocked')
            return replace_checked(path, expected, desired)
        with patch.object(select_gtk, 'replace_checked', side_effect=recovery), \
             self.assertRaisesRegex(Failure, 'original native verification failure.*first file blocked'):
            self.run_main('classic')
        for path in self.paths[1:]: self.assertEqual(snapshot(path), self.before[path])
        self.assertIn('first file blocked', self.receipt()['recovery_errors'][0])

    def test_restore_refuses_subsequent_user_edit_before_any_native_mutation(self):
        self.run_main('classic'); self.paths[1].write_text('new user preference')
        self.events.clear()
        with self.assertRaisesRegex(Failure, 'alteradas após'):
            self.run_main('--restaurar')
        self.assertEqual(self.paths[1].read_text(), 'new user preference')
        self.assertFalse(any(value is not None for _, value in self.events))

    def test_missing_gtk2_resource_refuses_before_native_calls_or_backup(self):
        (self.data/'themes/IrixClassic-KDE/gtk-2.0/gtkrc').unlink()
        with self.assertRaisesRegex(Failure, 'Tema GTK incompleto'):
            self.run_main('classic')
        self.assertEqual(self.events, []); self.assertFalse(self.state.exists()); self.assert_files_restored()

    def test_other_profile_gtkrc_path_is_refused(self):
        with patch.dict(os.environ, {'GTK2_RC_FILES': '/tmp/another-user/gtkrc'}), self.assertRaises(Failure):
            select_gtk.gtk_paths(self.config, self.home)

    def test_symbolic_link_is_refused_before_reading_native_preferences(self):
        self.paths[0].unlink(); self.paths[0].symlink_to(self.paths[1])
        with self.assertRaisesRegex(Failure, 'Link simbólico'):
            self.run_main('classic')
        self.assertEqual(self.events, []); self.assertFalse(self.state.exists())

    def test_gtkrc_updates_theme_without_losing_font_cursor_size_or_quoted_paths(self):
        before = b'include "/path with spaces/user.rc"\ngtk-font-name="User font"\ngtk-theme-name="Before"\ngtk-cursor-theme-size=48\n'
        after = select_gtk.edit_gtkrc(before, {'gtk-theme-name': 'Classic "quoted"'})
        self.assertIn(b'include "/path with spaces/user.rc"', after)
        self.assertIn(b'gtk-font-name="User font"', after)
        self.assertIn(b'gtk-cursor-theme-size=48', after)
        self.assertIn(b'gtk-theme-name="Classic \\"quoted\\""', after)

    def prepare_suite(self):
        profile = apply_suite.PROFILE_COMPONENTS['classic']
        files = [self.data/'plasma/look-and-feel'/profile['global']/'contents/defaults',
                 self.config/'Kvantum'/profile['kvantum']/(profile['kvantum']+'.kvconfig'),
                 self.data/'kwin/decorations'/profile['decoration']/'contents/ui/main.qml',
                 self.data/'icons'/profile['icons']/'index.theme',
                 self.data/'icons'/profile['cursor']/'index.theme',
                 self.data/'icons'/profile['cursor']/'cursors/wait',
                 self.data/'icons'/profile['cursor']/'cursors/progress',
                 self.data/'color-schemes/Irixium.colors',
                 self.data/'plasma/desktoptheme'/profile['plasma']/'metadata.desktop',
                 self.data/'wallpapers'/profile['wallpaper']/'metadata.json',
                 self.data/'plasma/look-and-feel'/profile['global']/'contents/splash/Splash.qml']
        for path in files:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text('fixture')
        kv = self.config/'Kvantum/kvantum.kvconfig'; kv.write_bytes(b'[General]\ntheme=Before\n')
        return kv

    def run_suite(self, *args):
        with patch.object(sys, 'argv', ['apply_suite', *args]), \
             patch.object(apply_suite, 'roots', return_value=(self.data, self.config, self.state)), \
             patch.object(select_gtk.Path, 'home', return_value=self.home), \
             patch.dict(os.environ, {'GTK2_RC_FILES': ''}), \
             patch.object(apply_suite, 'native_ready', return_value=True), \
             patch.object(apply_suite, 'notify_gtk', side_effect=self.notify), \
             patch.object(apply_suite, 'gtk_gsettings', side_effect=self.gsettings), \
             patch.object(apply_suite.shutil, 'which', return_value='/fake/plasma-apply-lookandfeel'), \
             patch.object(apply_suite.subprocess, 'run'), \
             redirect_stdout(io.StringIO()):
            apply_suite.main()

    def suite_receipt(self):
        paths = list(self.state.glob('irixium-selection/*/receipt.json'))
        self.assertEqual(len(paths), 1)
        return json.loads(paths[0].read_text())

    def test_full_suite_bus_recovery_failure_still_restores_gtk_and_kvantum(self):
        kv = self.prepare_suite(); kv_before = snapshot(kv)
        self.fail_verify = True; self.fail_restore_notify = True
        with self.assertRaisesRegex(Failure, 'original native verification failure.*rollback bus unavailable'):
            self.run_suite('classic', '--sem-sons')
        self.assert_files_restored(); self.assertEqual(snapshot(kv), kv_before)
        self.assertEqual(self.settings, "'Before'")
        self.assertEqual(self.suite_receipt()['status'], 'recovery_needed')
        self.assertEqual(self.suite_receipt()['native_gtk']['theme_before'], 'Before')
        self.assertEqual(self.suite_receipt()['native_gtk']['before'], "'Before'")

    def test_full_suite_partial_gtk4_write_restores_native_selection_and_kvantum(self):
        kv=self.prepare_suite(); kv_before=snapshot(kv)
        target=self.config/'gtk-4.0/settings.ini'; before=target.read_bytes()
        original=self.notify
        def partial(theme=None):
            value=original(theme)
            if theme is not None and theme!='Before': target.write_bytes(before)
            return value
        self.notify=partial
        with self.assertRaisesRegex(Failure,'seleção GTK não foi confirmada'):
            self.run_suite('classic','--sem-sons')
        self.assert_files_restored(); self.assertEqual(snapshot(kv),kv_before)
        self.assertEqual(self.theme,'Before'); self.assertEqual(self.settings,"'Before'")
        self.assertEqual(self.suite_receipt()['status'],'failed_restored')
        self.assertFalse((self.state/'irixium-selection/latest').exists())

    def test_full_suite_failure_restores_generated_css_imports_colors_and_modes(self):
        kv=self.prepare_suite(); kv_before=snapshot(kv)
        self.write_generated_colors=True; self.fail_verify=True
        with self.assertRaisesRegex(OSError,'original native verification failure'):
            self.run_suite('classic','--sem-sons')
        self.assert_files_restored(); self.assertEqual(snapshot(kv),kv_before)
        self.assertEqual(self.suite_receipt()['status'],'failed_restored')

    def test_full_suite_restore_checks_kde_theme_even_when_gsettings_did_not_change(self):
        self.prepare_suite(); self.run_suite('classic', '--sem-sons')
        self.theme = 'Foreign'; self.events.clear()
        applied = {p: snapshot(p) for p in self.paths}
        with self.assertRaisesRegex(Failure, 'seleção GTK nativa mudou'):
            self.run_suite('--restaurar')
        self.assertEqual({p: snapshot(p) for p in self.paths}, applied)
        self.assertFalse(any(value is not None for _, value in self.events))

    def test_full_suite_final_receipt_failure_restores_native_theme_and_private_files(self):
        kv = self.prepare_suite(); kv_before = snapshot(kv)
        original = apply_suite.atomic
        def failing_atomic(path, contents, *args, **kwargs):
            if path.name == 'receipt.json' and json.loads(contents)['status'] == 'applied':
                raise OSError('suite final journal failed')
            return original(path, contents, *args, **kwargs)
        with patch.object(apply_suite, 'atomic', side_effect=failing_atomic), \
             self.assertRaisesRegex(OSError, 'suite final journal failed'):
            self.run_suite('classic', '--sem-sons')
        self.assert_files_restored(); self.assertEqual(snapshot(kv), kv_before)
        self.assertEqual(self.theme, 'Before'); self.assertEqual(self.settings, "'Before'")
        self.assertEqual(self.suite_receipt()['status'], 'failed_restored')

    def test_full_suite_restore_recovers_files_even_if_native_notify_fails(self):
        kv = self.prepare_suite(); kv_before = snapshot(kv)
        self.run_suite('classic', '--sem-sons'); self.fail_restore_notify = True
        with self.assertRaisesRegex(Failure, 'rollback bus unavailable'):
            self.run_suite('--restaurar')
        self.assert_files_restored(); self.assertEqual(snapshot(kv), kv_before)
        self.assertEqual(self.settings, "'Before'")
        self.assertEqual(self.suite_receipt()['status'], 'recovery_needed')
