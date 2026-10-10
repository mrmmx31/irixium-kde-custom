# SPDX-License-Identifier: GPL-3.0-or-later
"""Transaction/CLI contracts with private files and mocked native providers.

These tests never emit a session signal or claim native palette/pixel coverage.
"""
import contextlib, io, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
sys.dont_write_bytecode = True
import kvantum_palette_runtime as runtime
import apply_kvantum_colors as cli
import kvantum_native_palette as native_reader
from theme_companion_bridge import native_palette_signature
from theme_transaction import Failure, snapshot
from select_companions import kvantum_theme


class Runtime(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.qa-kvantum-runtime-test-', dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.config, self.state = self.home/'config', self.home/'state'
        self.data = self.home/'data'
        self.data.mkdir()
        self.theme = 'IrixClassic'
        self.profile = {'global': 'org.magpie.irixclassic.desktop', 'kvantum': self.theme}
        self.selector = self.config/'Kvantum/kvantum.kvconfig'
        self.selector.parent.mkdir(parents=True)
        self.selector.write_text('[General]\ntheme=IrixClassic\n[Applications]\napp=PersonalTheme\n')
        (self.config/'kdeglobals').write_text('[General]\nColorScheme=PrivateOne\n[KDE]\nwidgetStyle=kvantum\n')
        self.source = self.config/'Kvantum/IrixClassic'
        self.source.mkdir()
        for suffix in ('.svg', '.kvconfig'): (self.source/('IrixClassic'+suffix)).write_text('canonical'+suffix)
        self.css = self.config/'gtk-3.0/colors.css'
        self.css.parent.mkdir()
        self.css.write_text('native palette one')
        self.canon_before = {path: snapshot(path) for path in self.source.iterdir()}
        self.selection_before = snapshot(self.selector)
        self.patches = [patch.object(runtime, 'require_global'),
            patch.object(runtime, 'exported_palette', side_effect=lambda data: {'native': data.decode()}),
            patch.object(runtime, 'render', side_effect=lambda theme, svg, cfg, colors, **kwargs:
                (svg+str(colors).encode(), cfg+b'\ncolors=none\n', {'geometry': 'unchanged'}))]
        for item in self.patches: item.start(); self.addCleanup(item.stop)
        self.events = []
        self.notify = lambda *_: self.events.append('style+palette') or 'native_style_and_palette_sent'

    def refresh(self, **kwargs):
        options = {'notify_style': self.notify, 'style_name': lambda _: 'kvantum',
                   'native': self.native(), **kwargs}
        with contextlib.redirect_stdout(io.StringIO()):
            return runtime.refresh(self.config, self.state, self.profile, **options)

    def native(self):
        return {'palette': {'Active': {'Base': '#102030', 'AlternateBase': '#203040'},
                            'Inactive': {'Base': '#304050', 'AlternateBase': '#405060'},
                            'Disabled': {'Base': '#506070', 'AlternateBase': '#607080'}},
                'source_signature': native_palette_signature(self.config)}

    def restore(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return runtime.restore(self.config, self.state, self.theme, **kwargs)

    def owned_files(self):
        return {path: snapshot(path) for path in
                runtime.generated_paths(self.config, self.theme)+[self.selector]}

    def change_kde_source(self):
        (self.config/'kdeglobals').write_text('[General]\nColorScheme=PrivateTwo\n[KDE]\nwidgetStyle=kvantum\n')

    def test_alias_reload_same_palette_no_repeat_canonical_unchanged(self):
        self.assertEqual(self.refresh()['theme'], 'IrixClassic-KDE')
        self.assertEqual(self.refresh()['status'], 'unchanged')
        self.assertEqual(self.events, ['style+palette'])
        self.css.write_text('native palette two')
        self.assertEqual(self.refresh()['theme'], 'IrixClassic-KDE-Reload')
        self.assertEqual(self.events, ['style+palette', 'style+palette'])
        self.assertEqual({path: snapshot(path) for path in self.source.iterdir()}, self.canon_before)
        self.assertIn('app=PersonalTheme', self.selector.read_text())

    def test_existing_variant_without_receipt_never_overwritten(self):
        target = runtime.generated_paths(self.config, self.theme)[0]
        target.parent.mkdir(parents=True); target.write_text('personal artwork')
        with self.assertRaisesRegex(Failure, 'sem recibo'): self.refresh()
        self.assertEqual(target.read_text(), 'personal artwork')
        self.assertEqual(snapshot(self.selector), self.selection_before)

    def test_later_edit_guards_no_notification(self):
        self.refresh()
        target = runtime.generated_paths(self.config, self.theme)[0]
        target.write_text('later personal edit')
        self.css.write_text('next palette')
        with self.assertRaisesRegex(Failure, 'editada'): self.refresh()
        self.assertEqual(self.events, ['style+palette'])
        self.assertEqual(target.read_text(), 'later personal edit')

    def test_notify_failure_rolls_back_files_and_selection(self):
        def fail(*_): raise RuntimeError('private bus failed')
        with self.assertRaisesRegex(RuntimeError, 'bus failed'): self.refresh(notify_style=fail)
        self.assertEqual(snapshot(self.selector), self.selection_before)
        self.assertTrue(all(not p.exists() for p in runtime.generated_paths(self.config, self.theme)))
        self.assertFalse((self.state/'irixium-kvantum-palette/IrixClassic/control.json').exists())

    def test_dry_run_no_resources_or_selector_write(self):
        self.assertEqual(self.refresh(dry=True)['status'], 'ready')
        self.assertFalse(self.state.exists())
        self.assertEqual(snapshot(self.selector), self.selection_before)
        self.assertTrue(all(not p.exists() for p in runtime.generated_paths(self.config, self.theme)))
        self.assertEqual(self.events, [])

    def test_unknown_qt_choices_preserved(self):
        self.assertEqual(self.refresh(style_name=lambda _: 'breeze')['status'], 'preserved_independent_application_style')
        self.selector.write_text('[General]\ntheme=OtherTheme\n')
        before = snapshot(self.selector)
        self.assertEqual(self.refresh()['status'], 'preserved_independent_kvantum_theme')
        self.assertEqual(snapshot(self.selector), before)
        self.assertFalse(self.state.exists())

    def test_restore_removes_only_owned_variants_preserves_later_manual_choice(self):
        self.refresh()
        self.selector.write_text('[General]\ntheme=UserTheme\n')
        choice = snapshot(self.selector)
        self.assertEqual(self.restore()['status'], 'restored')
        self.assertEqual(snapshot(self.selector), choice)
        self.assertTrue(all(not p.exists() for p in runtime.generated_paths(self.config, self.theme)))
        self.assertEqual({path: snapshot(path) for path in self.source.iterdir()}, self.canon_before)

    def test_restore_exact_selector(self):
        self.refresh(); self.css.write_text('another palette'); self.refresh()
        self.restore()
        self.assertEqual(snapshot(self.selector), self.selection_before)

    def test_source_change_rejected_with_no_new_event(self):
        self.refresh()
        (self.source/'IrixClassic.svg').write_text('later source edit')
        self.css.write_text('next native palette')
        with self.assertRaisesRegex(Failure, 'Fonte Kvantum mudou'): self.refresh()
        self.assertEqual(self.events, ['style+palette'])

    def test_crash_before_notification_never_skips_or_repeats_native_event(self):
        self.refresh()
        journal = self.state/'irixium-kvantum-palette/IrixClassic/native-notification.json'
        record = json.loads(journal.read_text()); record['status'] = 'prepared'
        journal.write_text(json.dumps(record)+'\n')
        before = {p: snapshot(p) for p in runtime.generated_paths(self.config, self.theme)+[self.selector]}
        with self.assertRaisesRegex(Failure, 'Notificação Qt interrompida'): self.refresh()
        self.assertEqual({p: snapshot(p) for p in before}, before)
        self.assertEqual(self.events, ['style+palette'])

    def test_common_lock_prevents_refresh_restore_overlap(self):
        self.refresh()
        before = {p: snapshot(p) for p in runtime.generated_paths(self.config, self.theme)+[self.selector]}
        with runtime.Bundle(self.state/'irixium-kvantum-palette/IrixClassic/operation-lock', ()).locked():
            with self.assertRaises(BlockingIOError): self.restore()
            with self.assertRaises(BlockingIOError): self.refresh()
        self.assertEqual({p: snapshot(p) for p in before}, before)

    def test_manual_switch_between_owned_aliases_gets_one_new_native_notification(self):
        self.refresh()
        self.selector.write_text(self.selector.read_text().replace('theme=IrixClassic-KDE\n','theme=IrixClassic-KDE-Reload\n'))
        self.assertEqual(self.refresh()['status'], 'reloaded')
        self.assertEqual(self.refresh()['status'], 'unchanged')
        self.assertEqual(self.events, ['style+palette','style+palette'])

    def test_selection_change_before_native_event_preserved(self):
        original_install = runtime.Transaction.install
        def external_change_after_commit(tx, changes, *args, **kwargs):
            receipt = original_install(tx, changes, *args, **kwargs)
            self.selector.write_text('[General]\ntheme=LaterManualChoice\n')
            return receipt
        with patch.object(runtime.Transaction, 'install', external_change_after_commit):
            with self.assertRaisesRegex(Failure, 'recuperação incompleta'): self.refresh()
        self.assertEqual(kvantum_theme(self.selector), 'LaterManualChoice')
        self.assertEqual(self.events, [])

    def test_alias_without_receipt_is_not_adopted_even_with_no_resources(self):
        self.selector.write_text('[General]\ntheme=IrixClassic-KDE\n')
        before = self.owned_files()
        with self.assertRaisesRegex(Failure, 'sem recibo'):
            self.refresh()
        self.assertEqual(self.owned_files(), before)
        self.assertEqual(self.events, [])

    def test_native_palette_reaches_mapper_after_previous_notification(self):
        self.refresh()
        current = self.native()
        current['palette']['Active']['Base'] = '#123456'
        with patch.object(runtime, 'render', return_value=(b'new svg', b'new cfg', {})) as mapper:
            self.assertEqual(self.refresh(native=current)['status'], 'reloaded')
        self.assertEqual(mapper.call_args.kwargs['native_qt_palette'], current['palette'])
        self.assertEqual(self.events, ['style+palette', 'style+palette'])

    def test_stale_native_source_is_rejected_before_state_write(self):
        native = self.native()
        self.change_kde_source()
        before = self.owned_files()
        with self.assertRaisesRegex(Failure, 'cores do KDE mudaram'):
            self.refresh(native=native, dry=True)
        self.assertEqual(self.owned_files(), before)
        self.assertFalse(self.state.exists())
        self.assertEqual(self.events, [])

    def test_palette_change_during_render_is_rejected_before_commit(self):
        before = self.owned_files()
        def changed(*args, **kwargs):
            self.change_kde_source()
            return b'svg', b'cfg', {}
        with patch.object(runtime, 'render', side_effect=changed):
            with self.assertRaisesRegex(Failure, 'Paleta/fonte mudou antes'):
                self.refresh()
        self.assertEqual(self.owned_files(), before)
        self.assertFalse((self.state/'irixium-kvantum-palette/IrixClassic/control.json').exists())
        self.assertEqual(self.events, [])

    def test_css_change_during_render_is_rejected_before_commit(self):
        before = self.owned_files()
        def changed(*args, **kwargs):
            self.css.write_text('new asynchronous export')
            return b'svg', b'cfg', {}
        with patch.object(runtime, 'render', side_effect=changed):
            with self.assertRaisesRegex(Failure, 'Paleta/fonte mudou antes'):
                self.refresh()
        self.assertEqual(self.owned_files(), before)
        self.assertEqual(self.events, [])

    def test_palette_change_after_commit_rolls_back_only_owned_resources(self):
        original_install = runtime.Transaction.install
        def changed(tx, changes, *args, **kwargs):
            receipt = original_install(tx, changes, *args, **kwargs)
            self.change_kde_source()
            return receipt
        before = self.owned_files()
        with patch.object(runtime.Transaction, 'install', changed):
            with self.assertRaisesRegex(Failure, 'Paleta/fonte mudou durante'):
                self.refresh()
        self.assertEqual(self.owned_files(), before)
        self.assertIn('PrivateTwo', (self.config/'kdeglobals').read_text())
        self.assertEqual(self.events, [])

    def test_unsuccessful_notification_status_rolls_back(self):
        before = self.owned_files()
        with self.assertRaisesRegex(Failure, 'Qt mudou de estilo'):
            self.refresh(notify_style=lambda *_: 'preserved_independent_application_style')
        self.assertEqual(self.owned_files(), before)
        self.assertEqual(self.events, [])

    def test_wrong_owner_receipt_rejected_before_native_event(self):
        self.refresh()
        control = self.state/'irixium-kvantum-palette/IrixClassic/control.json'
        record = json.loads(control.read_text())
        record['uid'] = os.getuid()+1
        control.write_text(json.dumps(record)+'\n')
        before = self.owned_files()
        with self.assertRaisesRegex(Failure, 'caminhos/usuário'):
            self.refresh()
        self.assertEqual(self.owned_files(), before)
        self.assertFalse(runtime.owned_selection(self.config, self.state, self.theme))
        self.assertEqual(self.events, ['style+palette'])

    def test_owned_selection_requires_all_generated_bytes_and_modes(self):
        self.refresh()
        self.assertTrue(runtime.owned_selection(self.config, self.state, self.theme))
        target = runtime.generated_paths(self.config, self.theme)[0]
        target.chmod(0o600)
        self.assertFalse(runtime.owned_selection(self.config, self.state, self.theme))
        with self.assertRaisesRegex(Failure, 'Edição posterior'):
            self.restore()

    def test_restore_dry_run_preserves_all_owned_files_and_receipt(self):
        self.refresh()
        paths = list(self.home.rglob('*'))
        before = {path: snapshot(path) for path in paths if path.is_file()}
        self.assertEqual(self.restore(dry=True)['status'], 'restore_ready')
        self.assertEqual({path: snapshot(path) for path in before}, before)
        self.assertEqual({path for path in self.home.rglob('*') if path.is_file()}, set(before))
        self.assertEqual(self.events, ['style+palette'])

    def test_generated_symlink_refused_without_touching_destination(self):
        target = runtime.generated_paths(self.config, self.theme)[0]
        target.parent.mkdir(parents=True)
        unrelated = self.home/'unrelated.svg'
        unrelated.write_bytes(b'personal')
        target.symlink_to(unrelated)
        with self.assertRaises(Failure):
            self.refresh(dry=True)
        self.assertEqual(unrelated.read_bytes(), b'personal')
        self.assertTrue(target.is_symlink())
        self.assertEqual(snapshot(self.selector), self.selection_before)


class Cli(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.qa-kvantum-cli-test-', dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.data, self.config, self.state = [self.home/name for name in ('data', 'config', 'state')]
        for path in (self.data, self.config): path.mkdir()
        self.profile = {'global': 'org.magpie.irixclassic.desktop', 'kvantum': 'IrixClassic'}
        self.selector = self.config/'Kvantum/kvantum.kvconfig'
        self.selector.parent.mkdir()
        self.selector.write_text('[General]\ntheme=IrixClassic\n')
        self.native = {'palette': {'Active': {'Base': '#123456'}}, 'source_signature': 'frozen-input'}
        self.original_export = cli.export_colors
        specs = [(cli, 'roots', {'return_value': (self.data, self.config, self.state, self.home)}),
                 (cli, 'effective_look_and_feel', {'return_value': self.profile['global']}),
                 (cli, 'profile_for', {'return_value': 'classic'}),
                 (cli, 'theme_profile', {'return_value': self.profile}),
                 (cli, 'effective_widget_style', {'return_value': 'kvantum'}),
                 (cli, 'require_global', {}),
                 (cli, 'read', {'return_value': self.native}),
                 (cli, 'refresh', {'return_value': {'status': 'ready'}}),
                 (cli, 'export_colors', {'return_value': 'frozen-input'}),
                 (cli.subprocess, 'run', {})]
        self.mocks = {}
        for obj, name, options in specs:
            item = patch.object(obj, name, **options)
            self.mocks[name] = item.start()
            self.addCleanup(item.stop)
        import reload_decoration
        item = patch.object(reload_decoration, 'check_session')
        self.check_session = item.start()
        self.addCleanup(item.stop)

    def test_dry_run_preflights_runtime_without_session_notifications(self):
        before = snapshot(self.selector)
        result = cli.run(dry=True)
        self.assertEqual(result['status'], 'ready_for_native_export')
        self.mocks['refresh'].assert_called_once()
        self.assertTrue(self.mocks['refresh'].call_args.kwargs['dry'])
        self.assertEqual(self.mocks['refresh'].call_args.kwargs['native'], self.native)
        self.mocks['run'].assert_not_called()
        self.mocks['export_colors'].assert_not_called()
        self.check_session.assert_not_called()
        self.assertEqual(snapshot(self.selector), before)
        self.assertFalse(self.state.exists())

    def test_dry_run_propagates_receipt_guard_instead_of_ready(self):
        self.mocks['refresh'].side_effect = Failure('Variante editada')
        with self.assertRaisesRegex(Failure, 'editada'):
            cli.run(dry=True)
        self.mocks['export_colors'].assert_not_called()
        self.mocks['run'].assert_not_called()

    def test_incompatible_scheme_options_fail_before_any_native_action(self):
        for options in ({'scheme': 'DomainOS-SR10-4', 'dry': True},
                        {'scheme': 'DomainOS-SR10-4', 'restoring': True},
                        {'scheme': 'bad;identifier'}):
            with self.subTest(options=options), self.assertRaises(Failure):
                cli.run(**options)
        self.check_session.assert_not_called()
        self.mocks['read'].assert_not_called()
        self.mocks['run'].assert_not_called()

    def test_independent_application_style_never_exports_or_selects(self):
        self.mocks['effective_widget_style'].return_value = 'breeze'
        before = snapshot(self.selector)
        with self.assertRaisesRegex(Failure, 'escolha foi preservada'):
            cli.run()
        self.mocks['export_colors'].assert_not_called()
        self.mocks['refresh'].assert_not_called()
        self.mocks['run'].assert_not_called()
        self.assertEqual(snapshot(self.selector), before)

    def test_independent_kvantum_theme_never_exports_or_selects(self):
        self.selector.write_text('[General]\ntheme=PersonalKvantum\n')
        before = snapshot(self.selector)
        with self.assertRaisesRegex(Failure, 'independente'):
            cli.run()
        self.mocks['export_colors'].assert_not_called()
        self.mocks['refresh'].assert_not_called()
        self.mocks['run'].assert_not_called()
        self.assertEqual(snapshot(self.selector), before)

    def test_scheme_change_is_explicit_and_native_data_must_match_export(self):
        cli.run(scheme='DomainOS-SR10-4')
        self.mocks['run'].assert_called_once_with(['plasma-apply-colorscheme', 'DomainOS-SR10-4'],
            capture_output=True, text=True, check=True, timeout=20)
        self.assertEqual(self.mocks['refresh'].call_args.kwargs['native'], self.native)
        self.mocks['refresh'].reset_mock()
        self.mocks['read'].return_value = {**self.native, 'source_signature': 'changed-after-export'}
        with self.assertRaisesRegex(Failure, 'esquema mudou'):
            cli.run()
        self.mocks['refresh'].assert_not_called()

    def test_native_notifier_orders_style_then_palette_once(self):
        self.assertEqual(cli.notify_qt(self.config, self.profile), 'native_style_and_palette_sent')
        calls = self.mocks['run'].call_args_list
        self.assertEqual([call.args[0][-2:] for call in calls], [['int32:2', 'int32:0'], ['int32:0', 'int32:0']])
        for call in calls:
            self.assertEqual(call.args[0][:5], ['dbus-send', '--session', '--type=signal',
                '/KGlobalSettings', 'org.kde.KGlobalSettings.notifyChange'])
            self.assertEqual(call.kwargs, {'capture_output': True, 'text': True, 'timeout': 10, 'check': True})

    def test_native_notifier_aborts_second_event_if_style_changed(self):
        self.mocks['effective_widget_style'].side_effect = ['kvantum', 'kvantum', 'breeze']
        with self.assertRaisesRegex(Failure, 'estilo mudou'):
            cli.notify_qt(self.config, self.profile)
        self.assertEqual(self.mocks['run'].call_count, 1)
        self.assertEqual(self.mocks['run'].call_args.args[0][-2:], ['int32:2', 'int32:0'])

    def test_native_notifier_failed_palette_event_does_not_claim_success(self):
        self.mocks['run'].side_effect = [subprocess.CompletedProcess([], 0),
            subprocess.CalledProcessError(1, ['dbus-send'])]
        with self.assertRaises(subprocess.CalledProcessError):
            cli.notify_qt(self.config, self.profile)
        self.assertEqual(self.mocks['run'].call_count, 2)

    def test_native_export_only_emits_color_notification_then_waits_frozen_source(self):
        # Unpatch the mocked high-level adapter while keeping all process calls inert.
        with patch.object(cli, 'native_palette_signature', return_value='source'), \
             patch.object(cli, 'palette_export_identity', return_value=('old3', 'old4')), \
             patch.object(cli, 'wait_for_native_palette') as wait:
            result = self.original_export(self.config, self.profile)
        self.assertEqual(result, 'source')
        wait.assert_called_once_with(self.config, self.profile, ('old3', 'old4'), 'source')
        command = self.mocks['run'].call_args.args[0]
        self.assertEqual(command[:7], ['gdbus', 'emit', '--session', '--object-path', '/kdeglobals', '--signal',
            'org.kde.kconfig.notify.ConfigChanged'])
        self.assertIn("'General': [[byte 67, 111, 108, 111, 114, 83, 99, 104, 101, 109, 101]]", command[-1])
        self.assertFalse(any('setGtkTheme' in argument for argument in command))

    def test_restore_dry_run_never_notifies_or_checks_live_session(self):
        control = self.state/'irixium-kvantum-palette/IrixClassic/control.json'
        control.parent.mkdir(parents=True)
        control.write_text('{}')
        before = snapshot(control)
        with patch.object(cli, 'restore', return_value={'status': 'restore_ready'}) as restore, \
             patch.object(cli, 'notify_qt') as notify:
            result = cli.run(dry=True, restoring=True)
        self.assertEqual(result['results'], [{'status': 'restore_ready'}])
        restore.assert_called_once_with(self.config, self.state, 'IrixClassic', dry=True)
        notify.assert_not_called()
        self.check_session.assert_not_called()
        self.mocks['run'].assert_not_called()
        self.assertEqual(snapshot(control), before)

    def test_restore_preserves_manual_kvantum_choice_without_notification(self):
        control = self.state/'irixium-kvantum-palette/IrixClassic/control.json'
        control.parent.mkdir(parents=True)
        control.write_text('{}')
        self.selector.write_text('[General]\ntheme=PersonalKvantum\n')
        before = snapshot(self.selector)
        with patch.object(cli, 'restore', return_value={'status': 'restored'}), \
             patch.object(cli, 'notify_qt') as notify:
            self.assertEqual(cli.run(restoring=True)['status'], 'restored')
        notify.assert_not_called()
        self.assertEqual(snapshot(self.selector), before)


class NativeReader(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.qa-kvantum-native-reader-test-', dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name)/'config'
        self.config.mkdir()
        (self.config/'kdeglobals').write_text('[General]\nColorScheme=PrivateOne\n')
        self.response = {'palette': {'Active': {'Base': '#123456'}}, 'checks':
            {'kde_platform_loaded': True, 'kvantum_not_loaded': True,
             'no_widget_palette_injection': True}}

    def result(self, *_args, **_kwargs):
        return subprocess.CompletedProcess([], 0, json.dumps(self.response), '')

    def test_native_reader_strips_style_injections_and_preserves_defaults_precedence(self):
        environment = {'DISPLAY': ':test', 'WAYLAND_DISPLAY': 'test', 'QT_STYLE_OVERRIDE': 'Other',
            'KDE_COLOR_SCHEME_PATH': 'other.colors', 'QT_PLUGIN_PATH': 'other/plugins',
            'QT_QPA_PLATFORM_PLUGIN_PATH': 'other/platforms', 'QT_QPA_GENERIC_PLUGINS': 'other',
            'XDG_CONFIG_DIRS': '/fixture-defaults'}
        before = snapshot(self.config/'kdeglobals')
        with patch.dict(os.environ, environment), \
             patch.object(native_reader.subprocess, 'run', side_effect=self.result) as process:
            result = native_reader.read(self.config)
        self.assertEqual(result['source_signature'], native_palette_signature(self.config))
        self.assertEqual(snapshot(self.config/'kdeglobals'), before)
        env = process.call_args.kwargs['env']
        self.assertTrue(all(key not in env for key in environment if key != 'XDG_CONFIG_DIRS'))
        self.assertEqual(env['XDG_CONFIG_DIRS'], str(self.config/'kdedefaults')+':/fixture-defaults')
        self.assertEqual(env['XDG_CONFIG_HOME'], str(self.config))
        self.assertEqual(env['QT_QPA_PLATFORM'], 'offscreen')
        self.assertEqual(env['QT_QPA_PLATFORMTHEME'], 'kde')
        self.assertEqual(process.call_args.kwargs['timeout'], 20)
        self.assertTrue(process.call_args.kwargs['check'])
        self.assertEqual(process.call_args.args[0][-1], '--read')

    def test_native_reader_rejects_changed_kde_source(self):
        def changed(*args, **kwargs):
            (self.config/'kdeglobals').write_text('[General]\nColorScheme=PrivateTwo\n')
            return self.result()
        with patch.object(native_reader.subprocess, 'run', side_effect=changed):
            with self.assertRaisesRegex(Failure, 'mudaram'):
                native_reader.read(self.config)

    def test_native_reader_rejects_unconfirmed_kde_provider(self):
        self.response['checks']['kvantum_not_loaded'] = False
        with patch.object(native_reader.subprocess, 'run', side_effect=self.result):
            with self.assertRaises(Failure):
                native_reader.read(self.config)


if __name__ == '__main__': unittest.main()
