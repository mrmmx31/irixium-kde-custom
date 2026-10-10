# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
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
import theme_companion_bridge as bridge
from theme_transaction import Failure, snapshot


class CompanionBridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.gtk-kde-bridge-test-', dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.data, self.config, self.state = [self.home/name for name in ('data', 'config', 'state')]
        self.paths = bridge.locations(self.data, self.config, self.state)

    def install(self, **options):
        with contextlib.redirect_stdout(io.StringIO()):
            return bridge.install(self.data, self.config, self.state, self.home, **options)

    def sync(self, **options):
        return bridge.synchronize(self.data, self.config, self.state, self.home, **options)

    def test_runtime_installed_with_dependencies_and_no_checkout_path(self):
        self.assertEqual(self.install()['status'], 'installed')
        bridge.verify_runtime(self.paths)
        runtime = self.paths['runtime']
        self.assertEqual({file.name for file in (runtime/'tools').iterdir()}, set(bridge.MODULES))
        self.assertEqual(json.loads((runtime/'components.json').read_text())['profiles'], bridge.catalog()['profiles'])
        unit = self.paths['unit'].read_text()
        self.assertIn(str(runtime/'tools/theme_companion_bridge.py'), unit)
        self.assertNotIn(str(ROOT), unit.replace(str(self.home), '<private-profile>'))

    def test_repeated_install_and_later_edits_guard_whole_runtime(self):
        self.install(); self.install()
        file = self.paths['runtime']/'tools/select_gtk.py'
        file.write_text('# later personal modification\n')
        with self.assertRaisesRegex(Failure, 'editada'): bridge.verify_runtime(self.paths)
        with self.assertRaisesRegex(Failure, 'editada'): self.install()
        self.assertEqual(file.read_text(), '# later personal modification\n')

    def test_dry_install_writes_nothing(self):
        self.assertEqual(self.install(dry=True)['status'], 'ready')
        self.assertFalse(self.state.exists()); self.assertFalse(self.data.exists())

    def test_destination_without_own_receipt_refused(self):
        self.paths['runtime'].mkdir(parents=True)
        with self.assertRaisesRegex(Failure, 'sem recibo'): self.install()

    def test_shared_and_symbolic_roots_refused(self):
        with self.assertRaises(Failure): bridge.validate_roots(Path('/usr/share'), self.config, self.state, self.home)
        link = self.home/'link'; link.symlink_to(self.home)
        with self.assertRaises(Failure): bridge.validate_roots(link, self.config, self.state, self.home)

    def test_systemd_token_quoting_keeps_dollar_percent_and_quotes_literal(self):
        value = 'a $item %h "space"'
        self.assertEqual(bridge.quote(value, command=True), '"a $$item %%h \\"space\\""')
        with self.assertRaises(Failure): bridge.quote('line\nbreak')

    def test_other_global_theme_does_not_query_or_change_gtk(self):
        with patch.object(bridge, 'effective_look_and_feel', return_value='org.kde.breeze.desktop'), \
                patch.object(bridge, 'select') as select, patch.object(bridge, 'notify') as notify:
            self.assertEqual(self.sync()['status'], 'ignored_other_global_theme')
            select.assert_not_called(); notify.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_native_kvantum_reload_only_after_applied_companions(self):
        profile = bridge.catalog()['profiles']['classic']
        with patch.object(bridge, 'effective_look_and_feel', return_value=profile['global']), \
                patch.object(bridge, 'select', return_value={'status': 'applied'}) as select, \
                patch.object(bridge, 'reload_kvantum', return_value='native_style_change_sent') as reload:
            result = self.sync(palette=False)
            self.assertEqual(result['kvantum'], 'native_style_change_sent')
            select.assert_called_once_with('classic', self.data, self.config, self.state, self.home)
            reload.assert_called_once_with(self.config, profile)

    def test_no_repeated_style_event_for_unchanged_companions(self):
        profile = bridge.catalog()['profiles']['classic']
        with patch.object(bridge, 'effective_look_and_feel', return_value=profile['global']), \
                patch.object(bridge, 'select', return_value={'status': 'unchanged'}), \
                patch.object(bridge, 'reload_kvantum') as reload:
            self.sync(palette=False); reload.assert_not_called()

    def test_color_change_preserves_independent_gtk_choice(self):
        profile = bridge.catalog()['profiles']['classic']
        with patch.object(bridge, 'effective_look_and_feel', return_value=profile['global']), \
                patch.object(bridge, 'require_global'), patch.object(bridge, 'select') as select, \
                patch.object(bridge, 'notify', return_value='OtherGTK'), \
                patch('gtk2_palette_runtime.setup') as setup, patch('gtk4_palette_runtime.refresh') as refresh:
            self.assertEqual(self.sync(companions=False)['gtk2_palette']['status'], 'preserved_independent_gtk_theme')
            select.assert_not_called(); setup.assert_not_called(); refresh.assert_not_called()

    def test_native_source_change_is_visible_even_with_stale_gtk_export(self):
        self.config.mkdir()
        kde = self.config/'kdeglobals'
        kde.write_text('[Colors:Window]\nBackgroundNormal=239,240,241\n')
        css = self.config/'gtk-3.0/colors.css'
        css.parent.mkdir()
        css.write_text('@define-color theme_bg_color_breeze #eff0f1;\n')
        before = bridge.native_palette_signature(self.config)
        kde.write_text('[Colors:Window]\nBackgroundNormal=193,193,193\n')
        after = bridge.native_palette_signature(self.config)
        self.assertNotEqual(before, after)
        css.write_text('@define-color theme_bg_color_breeze #c1c1c1;\n')
        self.assertEqual(after, bridge.native_palette_signature(self.config))
        defaults = self.config/'kdedefaults/kdeglobals'
        defaults.parent.mkdir()
        defaults.write_text('[General]\nColorScheme=IrixClassic\n')
        self.assertNotEqual(after, bridge.native_palette_signature(self.config))

    def test_native_export_uses_guarded_session_signal_without_kde_writes(self):
        profile = bridge.catalog()['profiles']['classic']
        self.config.mkdir()
        kde = self.config/'kdeglobals'
        kde.write_text('[Colors:Window]\nBackgroundNormal=193,193,193\n')
        before = snapshot(kde)
        with patch.object(bridge, 'require_global') as guard, \
                patch.object(bridge, 'notify', return_value=profile['gtk']), \
                patch.object(bridge, 'wait_for_native_palette') as wait, \
                patch.object(bridge.subprocess, 'run') as run:
            result = bridge.reload_gtk_palette(self.config, profile)
            self.assertEqual(result, 'native_palette_exported')
            guard.assert_called_once_with(self.config, profile['global'])
            wait.assert_called_once_with(self.config, profile, (None, None),
                                         bridge.native_palette_signature(self.config))
            argv = run.call_args.args[0]
            self.assertEqual(argv[:4], ['gdbus', 'emit', '--session', '--object-path'])
            self.assertIn('/kdeglobals', argv)
            self.assertIn('org.kde.kconfig.notify.ConfigChanged', argv)
            self.assertEqual(snapshot(kde), before)

    def test_native_export_preserves_independent_gtk_selection(self):
        profile = bridge.catalog()['profiles']['classic']
        with patch.object(bridge, 'require_global'), \
                patch.object(bridge, 'notify', return_value='OtherGTK'), \
                patch.object(bridge.subprocess, 'run') as run:
            self.assertEqual(bridge.reload_gtk_palette(self.config, profile),
                             'preserved_independent_gtk_theme')
            run.assert_not_called()

    def test_native_export_refused_if_global_choice_changed_during_worker(self):
        profile = bridge.catalog()['profiles']['classic']
        with patch.object(bridge, 'require_global', side_effect=Failure('Tema global mudou')), \
                patch.object(bridge, 'notify') as notify, \
                patch.object(bridge.subprocess, 'run') as run:
            with self.assertRaises(Failure): bridge.reload_gtk_palette(self.config, profile)
            notify.assert_not_called(); run.assert_not_called()

    def test_worker_rejects_unchanged_or_partial_native_export_at_deadline(self):
        profile = bridge.catalog()['profiles']['classic']
        path = self.config/'gtk-3.0/colors.css'
        path.parent.mkdir(parents=True)
        path.write_text('@define-color theme_bg_color_breeze #eff0f1;\n')
        before = bridge.palette_export_identity(self.config)
        with self.assertRaisesRegex(Failure, 'não confirmou'):
            bridge.wait_for_native_palette(self.config, profile, before,
                bridge.native_palette_signature(self.config), timeout=0)
        with self.assertRaisesRegex(Failure, 'não confirmou'):
            bridge.wait_for_native_palette(self.config, profile, None,
                bridge.native_palette_signature(self.config), timeout=0)

    def test_worker_refuses_palette_changed_during_native_export(self):
        profile = bridge.catalog()['profiles']['classic']
        path = self.config/'gtk-3.0/colors.css'
        path.parent.mkdir(parents=True)
        path.write_text('native complete export')
        other = self.config/'gtk-4.0/colors.css'
        other.parent.mkdir(parents=True)
        other.write_text('native complete export')
        with patch('gtk2_palette.exported_palette'), patch.object(bridge, 'require_global'):
            with self.assertRaisesRegex(Failure, 'paleta KDE mudou'):
                bridge.wait_for_native_palette(self.config, profile, None,
                                              'previous-native-fingerprint', timeout=0)

    def test_changed_gtk2_rc_reloads_native_theme_even_when_gtk4_palette_is_unchanged(self):
        profile = bridge.catalog()['profiles']['classic']
        for changed in (False, True):
            with self.subTest(gtk2_rc_changed=changed), \
                    patch.object(bridge, 'effective_look_and_feel', return_value=profile['global']), \
                    patch.object(bridge, 'require_global'), \
                    patch.object(bridge, 'notify', return_value=profile['gtk']), \
                    patch('gtk2_palette_runtime.setup', return_value={'native_reload_required': changed}), \
                    patch('gtk4_palette_runtime.refresh', return_value={'status': 'unchanged'}) as refresh:
                self.sync(companions=False)
                refresh.assert_called_once_with(self.data, self.config, self.state, self.home,
                    profile['gtk'], force_reload=changed)


if __name__ == '__main__': unittest.main()
