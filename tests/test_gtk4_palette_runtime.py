# SPDX-License-Identifier: GPL-3.0-or-later
"""Guarded files and native-selection failures, in disposable profiles only."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import gtk4_palette_runtime as runtime
from gtk2_palette import REQUIRED
from select_gtk import gtk_paths, edit_gtkrc
from theme_transaction import Failure, edit_ini, snapshot


class PaletteRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.gtk-kde-runtime-test-', dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.data, self.config, self.state = [self.home/name for name in ('data', 'config', 'state')]
        self.theme = 'IrixClassic-KDE'
        self.current = self.theme
        self.settings = repr(self.current)
        self.calls = []
        self.fail = False
        self.files = gtk_paths(self.config, self.home)
        for file in self.files:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'[Settings]\ngtk-theme-name=IrixClassic-KDE\ngtk-font-name=Personal 13\n'
                if file.name == 'settings.ini' else b'gtk-theme-name="IrixClassic-KDE"\n'
                if file == self.files[0] else b'/* independently generated KDE CSS */\n')
        for base in (self.data/'themes', self.home/'.themes'):
            for name in (self.theme, self.theme+'-Reload'):
                folder = base/name
                (folder/'common').mkdir(parents=True)
                (folder/'gtk-4.0').mkdir()
                (folder/'common/gtk.css').write_text('@define-color theme_bg_color_breeze #c1c1c1;\n'
                    'window {color: @theme_fg_color_breeze; background-color: @theme_bg_color_breeze;}\n')
                (folder/'gtk-4.0/gtk.css').write_text('@import url("../common/gtk.css");\n')
                manifest = {'files': {file.relative_to(folder).as_posix(): runtime.sha(file.read_bytes())
                    for file in folder.rglob('*.css')}}
                (folder/'MANIFEST.json').write_text(json.dumps(manifest))
        self.set_palette('#123456')
        self.protected = self.config/'kdeglobals'
        self.protected.write_text('[General]\nColorScheme=Independent\n[KDE]\nwidgetStyle=kvantum\n')
        self.before_protected = snapshot(self.protected)
        self.before_files = {file: snapshot(file) for file in self.files}

    def set_palette(self, color):
        values = {name: color for name in REQUIRED}
        values['theme_bg_color_breeze'] = color
        values['theme_fg_color_breeze'] = '#ffffff'
        (self.config/'gtk-3.0/colors.css').write_text(''.join('@define-color '+name+' '+value+';\n'
            for name, value in values.items()))

    def notify(self, name=None):
        if name is None: return self.current
        self.calls.append(name)
        self.current = name; self.settings = repr(name)
        for path in self.files:
            if path == self.files[0]: path.write_bytes(edit_gtkrc(path.read_bytes(), {'gtk-theme-name': name}))
            elif path.name == 'settings.ini':
                path.write_bytes(edit_ini(path.read_bytes(), 'Settings', {'gtk-theme-name': name}))
        if self.fail and name.endswith('-Reload'): raise OSError('native GTK setter interrupted')

    def gsettings(self, value=None):
        if value is None: return self.settings
        self.settings = value

    def refresh(self, **options):
        return runtime.refresh(self.data, self.config, self.state, self.home, self.theme,
            notify_call=self.notify, settings_call=self.gsettings, **options)

    def test_three_palettes_reload_existing_identity_without_theme_proliferation(self):
        for color, name in (('#123456', self.theme+'-Reload'), ('#ffee33', self.theme), ('#181828', self.theme+'-Reload')):
            self.set_palette(color)
            self.assertEqual(self.refresh()['status'], 'reloaded')
            self.assertEqual(self.current, name)
            for root in runtime.roots_for(self.data, self.home, self.theme):
                mirror = (root/'common/gtk.kde-live.css').read_text()
                self.assertIn('@define-color irix_kde_theme_bg_color_breeze '+color+';', mirror)
                self.assertNotIn('background-color: @theme_bg_color_breeze', mirror)
                self.assertEqual((root/'common/gtk.css').read_text().count('kde-live'), 0)
        self.assertEqual(len(list((self.data/'themes').iterdir())), 2)
        self.assertEqual(snapshot(self.protected), self.before_protected)
        self.assertIn('Personal 13', (self.config/'gtk-4.0/settings.ini').read_text())

    def test_unchanged_palette_does_not_toggle_theme_again(self):
        self.refresh(); self.calls.clear()
        self.assertEqual(self.refresh()['status'], 'unchanged')
        self.assertEqual(self.calls, [])

    def test_gtk2_rc_reload_alternates_once_even_if_gtk4_colors_are_unchanged(self):
        self.refresh(); self.calls.clear()
        current = self.current
        self.assertEqual(self.refresh(force_reload=True)['status'], 'reloaded')
        self.assertNotEqual(self.current, current)
        self.assertEqual(len(self.calls), 1)
        self.calls.clear()
        self.assertEqual(self.refresh()['status'], 'unchanged')
        self.assertEqual(self.calls, [])

    def test_failed_native_only_reload_preserves_existing_palette_resources(self):
        self.refresh()
        roots = runtime.roots_for(self.data, self.home, self.theme)
        before = {file: snapshot(file) for root in roots for file in root.rglob('*') if file.is_file()}
        self.current = self.theme; self.settings = repr(self.theme)
        self.fail = True
        with self.assertRaisesRegex(OSError, 'interrupted'):
            self.refresh(force_reload=True)
        self.assertEqual({file: snapshot(file) for file in before}, before)

    def test_independent_gtk_choice_preserved_on_palette_change(self):
        self.current = 'OtherTheme'
        self.assertEqual(self.refresh()['status'], 'preserved_independent_gtk_theme')
        self.assertFalse(self.state.exists()); self.assertEqual(self.calls, [])

    def test_personal_css_edit_blocks_updates_and_restore(self):
        self.refresh()
        edited = self.data/'themes'/self.theme/'gtk-4.0/gtk.css'
        edited.write_text('/* later personal GTK4 change */\n')
        self.set_palette('#ffee33'); self.calls.clear()
        with self.assertRaisesRegex(Failure, 'Edição posterior'): self.refresh()
        with self.assertRaisesRegex(Failure, 'Edição posterior'):
            runtime.restore(self.data, self.config, self.state, self.home, self.theme)
        self.assertEqual(edited.read_text(), '/* later personal GTK4 change */\n')
        self.assertEqual(self.calls, [])

    def test_native_setter_failure_restores_stored_selection_and_own_files(self):
        self.fail = True
        with self.assertRaisesRegex(OSError, 'interrupted'): self.refresh()
        self.assertEqual(self.current, self.theme)
        self.assertEqual({file: snapshot(file) for file in self.files}, self.before_files)
        for root in runtime.roots_for(self.data, self.home, self.theme):
            self.assertFalse((root/'common/gtk.kde-live.css').exists())
            self.assertNotIn('kde-live', (root/'gtk-4.0/gtk.css').read_text())

    def test_missing_reload_alias_refuses_before_native_changes(self):
        shutil.rmtree(self.home/'.themes'/(self.theme+'-Reload'))
        with self.assertRaisesRegex(Failure, 'não instalada'): self.refresh()
        self.assertEqual(self.calls, []); self.assertFalse(self.state.exists())

    def test_source_edit_without_updated_manifest_is_refused(self):
        (self.data/'themes'/self.theme/'common/gtk.css').write_text('window {color:red;}\n')
        with self.assertRaisesRegex(Failure, 'manifesto divergente'): self.refresh()
        self.assertEqual(self.calls, [])

    def test_palette_export_missing_waits_without_fallback_claim(self):
        (self.config/'gtk-3.0/colors.css').unlink()
        self.assertEqual(self.refresh()['status'], 'waiting_native_palette')
        self.assertEqual(self.calls, []); self.assertFalse(self.state.exists())

    def test_restore_preserves_original_imports_and_native_personal_preferences(self):
        self.refresh()
        result = runtime.restore(self.data, self.config, self.state, self.home, self.theme)
        self.assertEqual(result['status'], 'restored')
        for root in runtime.roots_for(self.data, self.home, self.theme):
            self.assertEqual((root/'gtk-4.0/gtk.css').read_text(), '@import url("../common/gtk.css");\n')
            self.assertFalse((root/'common/gtk.kde-live.css').exists())
        self.assertEqual(snapshot(self.protected), self.before_protected)


if __name__ == '__main__': unittest.main()
