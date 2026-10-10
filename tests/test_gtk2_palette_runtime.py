# SPDX-License-Identifier: GPL-3.0-or-later
"""Journaled GTK2 resources: private files only, no session or GTK selection."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import gtk2_palette_runtime as runtime
from gtk2_palette import BEGIN, exported_palette
from theme_transaction import Failure, replace_checked, snapshot
from test_gtk2_palette import native_export


def files(root):
    return {str(path.relative_to(root)): (hashlib.sha256(path.read_bytes()).hexdigest(),
                                          stat.S_IMODE(path.stat().st_mode))
            for path in root.rglob('*') if path.is_file() and not path.is_symlink()}


class Gtk2PaletteRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.gtk2-runtime-test-', dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.private = Path(self.temporary.name)
        self.data, self.config, self.state, self.home = [self.private / name for name in (
            'data with spaces', 'config with spaces', 'state with spaces', 'home with spaces')]
        self.args = (self.data, self.config, self.state, self.home)
        self.roots = runtime.Roots(*self.args)
        for path in self.args:
            path.mkdir()
        self.css = self.config / 'gtk-3.0/colors.css'
        self.css.parent.mkdir(); self.css.write_bytes(native_export())
        self.user_rc = self.home / '.gtkrc-2.0'
        self.user_rc.write_bytes(b'# user settings\ninclude "my-unrelated.rc"\ngtk-font-name="DejaVu Sans 10"\n')
        for original in ('IrixClassic', 'Irixium'):
            target = self.data / 'themes' / original
            (target / 'gtk-2.0').mkdir(parents=True)
            shutil.copyfile(ROOT / 'gtk' / original / 'gtk-2.0/gtkrc', target / 'gtk-2.0/gtkrc')
            if original == 'IrixClassic':
                shutil.copytree(ROOT / 'gtk' / original / 'common/assets', target / 'common/assets')
        for path, name in self.roots.wrappers().items():
            self.install_wrapper(path, name)
        self.baselines = {path: snapshot(path) for path in self.roots.wrappers()}
        self.protected = {str(path): path.read_bytes() for base in (self.data / 'themes/IrixClassic',
                                                                   self.data / 'themes/Irixium')
                          for path in base.rglob('*') if path.is_file()}
        self.protected[str(self.user_rc)] = self.user_rc.read_bytes()

    def install_wrapper(self, path, name):
        original = runtime.OWNED[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((self.data / 'themes' / original / 'gtk-2.0/gtkrc').read_bytes()
                         + b'\n# installed adaptive wrapper, preserve this edit\n')
        path.chmod(0o640 if name.endswith('-Reload') else 0o644)

    def call(self, action, **options):
        with redirect_stdout(io.StringIO()):
            return action(*self.args, **options)

    def active(self):
        return json.loads(self.roots.control.read_bytes())

    def protected_unchanged(self):
        for path, data in self.protected.items():
            self.assertEqual(Path(path).read_bytes(), data, path)

    def test_setup_shares_two_bundles_across_eight_owned_copies_and_is_idempotent(self):
        result = self.call(runtime.setup)
        self.assertEqual(result['status'], 'updated')
        self.assertEqual(len(result['themes']), 4)
        self.assertEqual(len(set(result['bundles'].values())), 2)
        self.assertEqual(len(self.active()['themes']), 8)
        self.assertEqual(len(self.active()['resources']), 107)
        for name in runtime.OWNED:
            paths = [path for path, owner in self.roots.wrappers().items() if owner == name]
            includes = []
            for path in paths:
                text = path.read_text()
                self.assertEqual(text.count(BEGIN), 1)
                self.assertIn('# installed adaptive wrapper', text)
                self.assertIn(str(self.roots.store), text)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), self.baselines[path]['mode'])
                includes.append(text[text.index(BEGIN):])
            self.assertEqual(includes[0], includes[1])
        before = files(self.private)
        self.assertEqual(self.call(runtime.refresh)['status'], 'unchanged')
        self.assertEqual(files(self.private), before)
        self.protected_unchanged()

    def test_three_colors_refresh_then_restore_setup_bytes_and_modes_not_only_last_update(self):
        self.call(runtime.setup)
        original_bundle = self.active()['resources'][0]['path']
        for overrides in ({'theme_bg_color_breeze': '#e8d840', 'theme_button_background_normal_breeze': '#d0bc48'},
                          {'theme_bg_color_breeze': '#18222c', 'theme_button_background_normal_breeze': '#28323c'}):
            self.css.write_bytes(native_export(overrides))
            result = self.call(runtime.refresh)
            self.assertEqual(result['status'], 'updated')
            self.assertEqual(result['colors_sha256'], hashlib.sha256(self.css.read_bytes()).hexdigest())
        self.assertTrue(Path(original_bundle).is_file(), 'unreparsed apps may still use old immutable resources')
        restored = self.call(runtime.restore)
        self.assertEqual(restored['status'], 'restored')
        for path, baseline in self.baselines.items():
            self.assertEqual(snapshot(path), baseline)
        self.assertEqual(self.active()['status'], 'restored')
        self.assertEqual(self.call(runtime.refresh)['reason'], 'not_set_up')
        self.protected_unchanged()

    def test_dry_run_creates_no_files_or_journal_and_external_theme_is_ignored(self):
        before = files(self.private)
        self.assertEqual(self.call(runtime.setup, dry=True)['status'], 'ready')
        self.assertFalse(self.roots.runtime.exists())
        self.assertEqual(self.call(runtime.setup, theme='Adwaita')['reason'], 'theme_not_owned')
        self.assertEqual(self.call(runtime.refresh, theme='Irixium')['reason'], 'theme_not_owned')
        self.assertEqual(files(self.private), before)
        self.protected_unchanged()

    def test_canonical_only_install_accepts_aliases_added_later_without_duplicate_assets(self):
        aliases = [path for path, name in self.roots.wrappers().items() if name.endswith('-Reload')]
        for path in aliases:
            path.unlink()
        self.assertEqual(len(self.call(runtime.setup)['themes']), 2)
        resource_files = files(self.roots.store)
        for path in aliases:
            self.install_wrapper(path, self.roots.wrappers()[path])
        self.assertEqual(len(self.call(runtime.refresh)['themes']), 4)
        self.assertEqual(files(self.roots.store), resource_files)
        self.assertEqual(len(self.active()['themes']), 8)

    def test_native_export_missing_duplicate_expression_and_symlink_are_refused_before_targets(self):
        wrappers = {path: snapshot(path) for path in self.roots.wrappers()}
        for bad in (b'@define-color theme_bg_color_breeze #123456;\n',
                    native_export() + b'@define-color theme_bg_color_breeze #123456;\n',
                    native_export().replace(b'#456789', b'rgb(1,2,3)')):
            self.css.write_bytes(bad)
            with self.assertRaises(Failure):
                self.call(runtime.setup)
            self.assertFalse(self.roots.store.exists())
            self.assertEqual({p: snapshot(p) for p in wrappers}, wrappers)
        self.css.unlink(); self.css.symlink_to(self.user_rc)
        with self.assertRaises(Failure):
            self.call(runtime.setup)
        self.assertFalse(self.roots.store.exists())
        self.protected_unchanged()

    def test_other_config_css_is_never_read_and_wrappers_with_symlink_are_refused(self):
        alien = self.private / 'alien/colors.css'; alien.parent.mkdir(); alien.write_bytes(native_export())
        with self.assertRaisesRegex(Failure, 'origem'):
            self.call(runtime.setup, colors_path=alien)
        wrapper = next(iter(self.roots.wrappers()))
        wrapper.unlink(); wrapper.symlink_to(self.user_rc)
        with self.assertRaisesRegex(Failure, 'Link simbólico'):
            self.call(runtime.setup)
        self.assertFalse(self.roots.store.exists())

    def test_edited_wrapper_or_generated_asset_blocks_refresh_restore_and_all_other_targets(self):
        self.call(runtime.setup)
        target = next(iter(self.roots.wrappers()))
        original = target.read_bytes()
        target.write_bytes(original + b'# user post-setup edit\n')
        before = files(self.private)
        for operation in (runtime.refresh, runtime.restore):
            with self.assertRaisesRegex(Failure, 'Edição posterior'):
                self.call(operation)
            self.assertEqual(files(self.private), before)
        target.write_bytes(original)
        resource = Path(next(e['path'] for e in self.active()['resources'] if e['path'].endswith('.png')))
        resource.write_bytes(b'edited asset')
        before = files(self.private)
        with self.assertRaisesRegex(Failure, 'gerado foi modificado'):
            self.call(runtime.refresh)
        self.assertEqual(files(self.private), before)

    def test_native_colors_change_during_rendering_aborts_before_resource_or_include_write(self):
        from gtk2_palette import prepare
        def changed(source, css, destination):
            result = prepare(source, css, destination)
            self.css.write_bytes(native_export({'theme_bg_color_breeze': '#112233'}))
            return result
        with self.assertRaisesRegex(Failure, 'cores nativas mudaram'):
            self.call(runtime.setup, renderers={'IrixClassic-KDE': changed})
        self.assertFalse(self.roots.store.exists())
        self.assertFalse(self.roots.control.exists())
        self.assertEqual({p: snapshot(p) for p in self.baselines}, self.baselines)

    def test_mid_commit_failure_restores_all_targets_and_retry_is_explicit_safe(self):
        count = 0
        def fail_once(path, before, after):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError('private injected write failure')
            return replace_checked(path, before, after)
        with self.assertRaisesRegex(Failure, 'anteriores restaurados'):
            self.call(runtime.setup, writer=fail_once)
        self.assertEqual({p: snapshot(p) for p in self.baselines}, self.baselines)
        self.assertFalse(self.roots.control.exists())
        self.assertFalse(any(self.roots.store.rglob('*.png')))
        latest = (self.roots.runtime / 'latest').read_text().strip()
        receipt = json.loads((self.roots.runtime / 'backups' / latest / 'receipt.json').read_bytes())
        self.assertEqual(receipt['status'], 'restored')
        self.assertEqual(self.call(runtime.setup)['status'], 'updated')
        self.protected_unchanged()

    def test_colors_change_after_resource_write_cannot_publish_stale_rc_or_active_record(self):
        changed = False
        def changed_colors(path, before, after):
            nonlocal changed
            replace_checked(path, before, after)
            if path.is_relative_to(self.roots.store) and not changed:
                changed = True
                self.css.write_bytes(native_export({'theme_bg_color_breeze': '#112233'}))
        with self.assertRaisesRegex(Failure, 'cores nativas mudaram'):
            self.call(runtime.setup, writer=changed_colors)
        self.assertEqual({p: snapshot(p) for p in self.baselines}, self.baselines)
        self.assertFalse(self.roots.control.exists())
        self.assertFalse(any(self.roots.store.rglob('*.png')))

    def test_unknown_write_blocks_rollback_and_recovery_until_explicit_edit_preservation(self):
        victim = next(path for path in self.roots.wrappers() if path.is_relative_to(self.home))
        conflict = b'# a concurrent private user edit\n'
        failed = False
        def conflicting(path, before, after):
            nonlocal failed
            if path in self.roots.wrappers() and not failed:
                failed = True; victim.write_bytes(conflict)
                raise OSError('private conflict')
            return replace_checked(path, before, after)
        with self.assertRaisesRegex(Failure, 'recuperação necessária'):
            self.call(runtime.setup, writer=conflicting)
        self.assertEqual(victim.read_bytes(), conflict)
        with self.assertRaisesRegex(Failure, 'interrompida'):
            self.call(runtime.setup)
        before = files(self.private)
        with self.assertRaisesRegex(Failure, 'Edição posterior'):
            self.call(runtime.restore, recovery=True)
        self.assertEqual(files(self.private), before)
        victim.write_bytes(__import__('theme_transaction').decode(self.baselines[victim]))
        self.assertEqual(self.call(runtime.restore, recovery=True)['status'], 'recovered')
        self.assertEqual({p: snapshot(p) for p in self.baselines}, self.baselines)
        self.assertFalse(self.roots.control.exists())

    def test_malformed_or_relocated_active_record_cannot_expand_scope(self):
        self.call(runtime.setup)
        record = self.active()
        record['themes'][0]['path'] = str(self.user_rc)
        self.roots.control.write_text(json.dumps(record))
        before = files(self.private)
        with self.assertRaisesRegex(Failure, 'fora do escopo'):
            self.call(runtime.refresh)
        self.assertEqual(files(self.private), before)
        self.protected_unchanged()

    def test_installed_helpers_work_from_relocated_path_and_arbitrary_cwd_without_repository(self):
        helpers = self.private / 'installed helpers with spaces'; helpers.mkdir()
        for name in ('gtk2_palette_runtime.py', 'gtk2_palette.py', 'gtk2_scrollbar_assets.py',
                     'gtk2_modern_palette.py', 'theme_transaction.py'):
            shutil.copyfile(ROOT / 'tools' / name, helpers / name)
        cwd = self.private / 'unrelated current directory'; cwd.mkdir()
        code = ('import contextlib,io,json,pathlib,sys;sys.path.insert(0,sys.argv[1]);'
                'import gtk2_palette_runtime as m;'
                '\nwith contextlib.redirect_stdout(io.StringIO()):\n'
                ' r=m.setup(*map(pathlib.Path,sys.argv[2:]),dry=True)\n'
                'print(json.dumps(r))\n')
        result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(helpers), *map(str, self.args)],
                                cwd=cwd, env={'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'ready')
        self.assertFalse(self.roots.control.exists())


if __name__ == '__main__':
    unittest.main()
