# SPDX-License-Identifier: GPL-3.0-or-later
"""Journaled GTK2 resources: private files only, no session or GTK selection."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import re
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
import domainos_motif_art as art
import gtk2_domainos_palette
from gtk2_palette import BEGIN, exported_palette
from theme_transaction import Failure, replace_checked, snapshot
from test_gtk2_palette import native_export


def files(root):
    return {str(path.relative_to(root)): (hashlib.sha256(path.read_bytes()).hexdigest(),
                                          stat.S_IMODE(path.stat().st_mode))
            for path in root.rglob('*') if path.is_file() and not path.is_symlink()}


class Gtk2PaletteRuntimeTests(unittest.TestCase):
    def setUp(self):
        # Keep the established two-family fixture; DomainOS has separate real
        # artwork and manifests, exercised by DomainOSGtk2RuntimeTests below.
        owners={name:family for name,family in runtime.OWNED.items()
                if family in ('IrixClassic','Irixium')}
        owner_patch=patch.object(runtime,'OWNED',owners)
        owner_patch.start();self.addCleanup(owner_patch.stop)
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
        self.user_rc.write_bytes(b'# user settings\ngtk-theme-name="IrixClassic-KDE"\ninclude "my-unrelated.rc"\ngtk-font-name="DejaVu Sans 10"\n')
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

    def test_restored_binding_accepts_new_wrapper_as_baseline_and_preserves_it(self):
        self.call(runtime.setup)
        self.call(runtime.restore)
        target = next(iter(self.roots.wrappers()))
        replacement = target.read_bytes() + b'\n# installed revision or user customization\n'
        target.write_bytes(replacement)
        self.assertEqual(self.call(runtime.setup)['status'], 'updated')
        self.assertIn(b'# installed revision or user customization', target.read_bytes())
        self.call(runtime.restore)
        self.assertEqual(target.read_bytes(), replacement)

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

    def test_palette_refresh_does_not_change_the_selected_gtk2_theme_name(self):
        selected_theme = b'gtk-theme-name="IrixClassic-KDE"'
        self.assertIn(selected_theme, self.user_rc.read_bytes())
        self.call(runtime.setup)
        self.css.write_bytes(native_export({'theme_bg_color_breeze': '#b84f39'}))
        self.assertEqual(self.call(runtime.refresh)['status'], 'updated')
        self.assertIn(selected_theme, self.user_rc.read_bytes())
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


class DomainOSGtk2RuntimeTests(unittest.TestCase):
    @staticmethod
    def palette(overrides=None):
        # Complete synthetic role fixture, never claimed as native exporter
        # coverage. DomainOS also consumes Selection/Titlebar disabled roles.
        from domainos_motif_art import DEFAULT
        return native_export({**DEFAULT, **(overrides or {})})

    def setUp(self):
        temp_root=Path.home()/'tempia';temp_root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='gtk2-domainos-runtime-test-',dir=temp_root)
        self.addCleanup(self.temp.cleanup);self.private=Path(self.temp.name)
        self.args=tuple(self.private/name for name in ('data','config','state','home'))
        self.data,self.config,self.state,self.home=self.args
        for path in self.args:path.mkdir()
        shutil.copytree(ROOT/'gtk/DomainOS-SR10-4',self.data/'themes/DomainOS-SR10-4')
        self.css=self.config/'gtk-3.0/colors.css';self.css.parent.mkdir()
        self.css.write_bytes(self.palette())
        self.roots=runtime.Roots(*self.args)
        self.wrappers=[]
        for path,name in self.roots.wrappers().items():
            if not name.startswith('DomainOS-'):continue
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes((self.data/'themes/DomainOS-SR10-4/gtk-2.0/gtkrc').read_bytes())
            path.chmod(0o640);self.wrappers.append(path)
        self.before={path:snapshot(path) for path in self.wrappers}
        self.source=self.data/'themes/DomainOS-SR10-4'
        self.protected=files(self.source)

    def call(self,operation,**options):
        with redirect_stdout(io.StringIO()):return operation(*self.args,**options)

    def test_own_family_updates_four_wrappers_and_restores_exact_bytes_modes(self):
        result=self.call(runtime.setup,theme='DomainOS-SR10-4-KDE')
        self.assertEqual(result['status'],'updated')
        self.assertEqual(result['themes'],['DomainOS-SR10-4-KDE','DomainOS-SR10-4-KDE-Reload'])
        record=json.loads(self.roots.control.read_text())
        self.assertEqual(len(record['themes']),4)
        self.assertEqual(len(set(result['bundles'].values())),1)
        self.assertTrue(all('Irix' not in entry['name'] for entry in record['themes']))
        current=files(self.private)
        self.assertEqual(self.call(runtime.refresh)['status'],'unchanged')
        self.assertEqual(files(self.private),current)
        self.call(runtime.restore)
        for path,before in self.before.items():self.assertEqual(snapshot(path),before)
        self.assertEqual(files(self.source),self.protected)

    def test_color_change_rebuilds_actual_pixmaps_without_touching_canonical_art(self):
        first=self.call(runtime.setup)
        initial=Path(next(iter(first['bundles'].values())))
        before={path.name:path.read_bytes() for path in (initial/'assets').glob('*.png')}
        self.css.write_bytes(self.palette({'theme_button_background_normal_breeze':'#126789',
                                           'theme_bg_color_breeze':'#204060'}))
        second=self.call(runtime.refresh)
        final=Path(next(iter(second['bundles'].values())))
        after={path.name:path.read_bytes() for path in (final/'assets').glob('*.png')}
        self.assertEqual(set(before),set(after));self.assertTrue(any(before[name]!=after[name] for name in before))
        self.assertTrue(initial.is_dir(),'existing GTK2 processes can still reference the preceding immutable bundle')
        self.assertEqual(files(self.source),self.protected)

    def test_active_stepper_corners_follow_kde_roles_through_oriented_troughs(self):
        from PIL import Image
        import io

        def rendered_pixels(bundle):
            assets=bundle/'assets'
            def image(name):
                return Image.open(io.BytesIO((assets/name).read_bytes())).convert('RGBA')
            trough=image('scroll-trough-pressed-horizontal.png')
            vertical_trough=image('scroll-trough-pressed-vertical.png')
            plain_trough=image('scroll-trough-pressed.png')
            left=image('scrollbar-stepper-left-normal.png')
            right=image('scrollbar-stepper-right-normal.png')
            up=image('scrollbar-stepper-up-normal.png')
            down=image('scrollbar-stepper-down-normal.png')
            down_focused=image('scrollbar-stepper-down-focused.png')
            down_pressed=image('scrollbar-stepper-down-pressed.png')
            self.assertEqual(trough.size,(24,24))
            self.assertEqual(vertical_trough.size,(24,24))
            self.assertEqual(left.size,(15,15))
            self.assertEqual(right.size,(15,15))
            self.assertEqual(up.size,(15,15))
            self.assertEqual(down.size,(15,15))
            self.assertEqual(down_focused.size,(15,15))
            palette=exported_palette(self.css.read_bytes())
            for name,actual in (
                ('scrollbar-stepper-down-normal',down),
                ('scrollbar-stepper-down-focused',down_focused),
            ):
                pixels,family,_border=art.gtk2_assets()[name]
                expected=gtk2_domainos_palette.png(pixels,family,palette)
                expected_pixels=Image.open(io.BytesIO(expected)).convert('RGBA').tobytes()
                self.assertEqual(actual.tobytes(),expected_pixels,
                                 'normal/prelight down arrow must preserve its role-rendered reference artwork')
            self.assertEqual(down.tobytes(),down_focused.tobytes(),
                             'source-equivalent NORMAL/PRELIGHT cells must remain identical')
            held_delta=[
                (x,y,down.getpixel((x,y))[:3],down_pressed.getpixel((x,y))[:3])
                for y in range(15) for x in range(15)
                if down.getpixel((x,y)) != down_pressed.getpixel((x,y))
            ]
            self.assertEqual(len(held_delta),53,
                             'the native held state changes only the 53-pixel arrow relief')
            self.assertTrue(all(2 <= x < 13 and 2 <= y < 13
                                for x,y,_,_ in held_delta),
                            'pressing the arrow must not alter the outer stepper cell')
            transitions={(before,after) for _,_,before,after in held_delta}
            self.assertEqual(len(transitions),2)
            self.assertEqual({(after,before) for before,after in transitions},transitions,
                             'the held state swaps the role-derived light and shadow bands')
            for target,source,point in (
                    ((2,22),left,(0,13)), ((3,22),left,(1,13)),
                    ((2,23),left,(0,14)), ((21,1),right,(14,1))):
                self.assertEqual(trough.getpixel(target),source.getpixel(point))
            for target,source,point in (
                    ((22,2),up,(13,0)), ((23,2),up,(14,0)),
                    ((22,3),up,(13,1)), ((1,21),down,(1,14))):
                self.assertEqual(vertical_trough.getpixel(target),source.getpixel(point))
            return trough.tobytes()+vertical_trough.tobytes()+plain_trough.tobytes()

        first=self.call(runtime.setup,theme='DomainOS-SR10-4-KDE')
        bundle=Path(first['bundles']['DomainOS-SR10-4-KDE'])
        rc=(bundle/'gtkrc').read_text()
        active=[line for line in rc.splitlines()
                if 'function = BOX  state = ACTIVE  detail = "trough"' in line]
        self.assertEqual(len(active),2)
        horizontal=next(line for line in active if 'orientation = HORIZONTAL' in line)
        vertical=next(line for line in active if 'orientation = VERTICAL' in line)
        self.assertIn('scroll-trough-pressed-horizontal.png',horizontal)
        self.assertIn('border = { 4, 4, 2, 2 }',horizontal)
        self.assertIn('scroll-trough-pressed-vertical.png',vertical)
        self.assertNotIn('scroll-trough-pressed-horizontal.png',vertical)
        self.assertIn('border = { 2, 2, 4, 4 }',vertical)
        self.assertNotIn('GtkRange::trough-under-steppers',rc)
        normal=[line for line in rc.splitlines()
                if 'function = BOX  state = NORMAL  detail = "trough"' in line]
        self.assertEqual(len(normal),2)
        self.assertIn('scroll-trough-normal-horizontal.png',
                      next(line for line in normal if 'orientation = HORIZONTAL' in line))
        self.assertIn('scroll-trough-normal-vertical.png',
                      next(line for line in normal if 'orientation = VERTICAL' in line))
        for state in ('PRELIGHT','SELECTED'):
            line=next(line for line in rc.splitlines()
                      if f'function = BOX  state = {state}  detail = "trough"' in line)
            self.assertIn('border = { 2, 2, 2, 2 }',line)
        first_pixels=rendered_pixels(bundle)

        self.css.write_bytes(self.palette({'theme_button_background_normal_breeze':'#cb3426'}))
        refreshed=self.call(runtime.refresh,theme='DomainOS-SR10-4-KDE')
        next_bundle=Path(refreshed['bundles']['DomainOS-SR10-4-KDE'])
        next_pixels=rendered_pixels(next_bundle)
        self.assertNotEqual(first_pixels,next_pixels)
        self.assertEqual(files(self.source),self.protected)

    def test_normal_horizontal_stepper_corners_follow_kde_roles(self):
        from PIL import Image
        patterns=art.gtk2_stepper_trough_junctions()

        def verify(bundle):
            assets=bundle/'assets'
            def image(name):
                return Image.open(assets/name).convert('RGBA')
            rc=(bundle/'gtkrc').read_text()
            rules=[line for line in rc.splitlines()
                   if 'function = BOX  state = NORMAL  detail = "trough"' in line]
            self.assertEqual(len(rules),2)
            horizontal=next(line for line in rules if 'orientation = HORIZONTAL' in line)
            vertical=next(line for line in rules if 'orientation = VERTICAL' in line)
            self.assertIn('scroll-trough-normal-horizontal.png',horizontal)
            self.assertIn('border = { 5, 5, 2, 2 }',horizontal)
            self.assertIn('scroll-trough-normal-vertical.png',vertical)
            self.assertIn('border = { 2, 2, 5, 5 }',vertical)
            horizontal_trough=image('scroll-trough-normal-horizontal.png')
            vertical_trough=image('scroll-trough-normal-vertical.png')
            self.assertEqual(horizontal_trough.size,(24,15))
            self.assertEqual(vertical_trough.size,(15,24))
            palette=exported_palette(self.css.read_bytes())
            for rows,im,orientation,at_end in (
                    (patterns['horizontal_start_rows'],horizontal_trough,'horizontal',False),
                    (patterns['horizontal_end_rows'],horizontal_trough,'horizontal',True),
                    (patterns['vertical_start_rows'],vertical_trough,'vertical',False),
                    (patterns['vertical_end_rows'],vertical_trough,'vertical',True)):
                for y,row in enumerate(rows):
                    for x,token in enumerate(row):
                        point=((im.width-5+x,y) if orientation=='horizontal' and at_end else
                               (x,y) if orientation=='horizontal' else
                               (x,im.height-5+y) if at_end else (x,y))
                        value=art.evaluate(art.pixel_plan('button',token),palette)
                        expected=tuple(int(value[index:index+2],16) for index in (1,3,5))+(255,)
                        self.assertEqual(im.getpixel(point),expected)
            return horizontal_trough.tobytes()+vertical_trough.tobytes()

        first=self.call(runtime.setup,theme='DomainOS-SR10-4-KDE')
        first_bundle=Path(first['bundles']['DomainOS-SR10-4-KDE'])
        first_caps=verify(first_bundle)
        self.css.write_bytes(self.palette({'theme_button_background_normal_breeze':'#cb3426'}))
        refreshed=self.call(runtime.refresh,theme='DomainOS-SR10-4-KDE')
        next_bundle=Path(refreshed['bundles']['DomainOS-SR10-4-KDE'])
        next_caps=verify(next_bundle)
        self.assertNotEqual(first_caps,next_caps)
        self.assertEqual(files(self.source),self.protected)

    def test_insensitive_stepper_corners_follow_kde_roles_through_oriented_troughs(self):
        from PIL import Image
        import io

        def verify(bundle):
            assets=bundle/'assets'
            def image(name):
                return Image.open(io.BytesIO((assets/name).read_bytes())).convert('RGBA')
            rc=(bundle/'gtkrc').read_text()
            rules=[line for line in rc.splitlines()
                   if 'function = BOX  state = INSENSITIVE  detail = "trough"' in line]
            self.assertEqual(len(rules),2)
            horizontal=next(line for line in rules if 'orientation = HORIZONTAL' in line)
            vertical=next(line for line in rules if 'orientation = VERTICAL' in line)
            self.assertIn('scroll-trough-disabled-horizontal.png',horizontal)
            self.assertIn('border = { 4, 4, 2, 2 }',horizontal)
            self.assertIn('scroll-trough-disabled-vertical.png',vertical)
            self.assertIn('border = { 2, 2, 4, 4 }',vertical)
            horizontal_trough=image('scroll-trough-disabled-horizontal.png')
            vertical_trough=image('scroll-trough-disabled-vertical.png')
            self.assertEqual(horizontal_trough.size,(24,24))
            self.assertEqual(vertical_trough.size,(24,24))
            left=image('scrollbar-stepper-left-disabled.png')
            right=image('scrollbar-stepper-right-disabled.png')
            up=image('scrollbar-stepper-up-disabled.png')
            down=image('scrollbar-stepper-down-disabled.png')
            for target,source,point in (
                    ((2,22),left,(0,13)), ((3,22),left,(1,13)),
                    ((2,23),left,(0,14)), ((21,1),right,(14,1))):
                self.assertEqual(horizontal_trough.getpixel(target),source.getpixel(point))
            for target,source,point in (
                    ((22,2),up,(13,0)), ((23,2),up,(14,0)),
                    ((22,3),up,(13,1)), ((1,21),down,(1,14))):
                self.assertEqual(vertical_trough.getpixel(target),source.getpixel(point))
            return horizontal_trough.tobytes()+vertical_trough.tobytes()

        first=self.call(runtime.setup,theme='DomainOS-SR10-4-KDE')
        bundle=Path(first['bundles']['DomainOS-SR10-4-KDE'])
        first_corners=verify(bundle)
        self.css.write_bytes(self.palette({
            'insensitive_bg_color_breeze':'#d6a27c',
            'theme_button_background_insensitive_breeze':'#293d55',
            'theme_button_foreground_insensitive_breeze':'#d9e7a1',
        }))
        refreshed=self.call(runtime.refresh,theme='DomainOS-SR10-4-KDE')
        next_bundle=Path(refreshed['bundles']['DomainOS-SR10-4-KDE'])
        next_corners=verify(next_bundle)
        self.assertNotEqual(first_corners,next_corners)
        self.assertTrue(bundle.is_dir(),'an existing GTK2 process may still reference the prior immutable bundle')
        self.assertEqual(files(self.source),self.protected)

    def test_tooltips_use_kde_roles_and_palette_namespaces_change_on_refresh(self):
        first=self.call(runtime.setup,theme='DomainOS-SR10-4-KDE')
        initial=Path(first['bundles']['DomainOS-SR10-4-KDE'])
        initial_rc=(initial/'gtkrc').read_text()
        first_palette=exported_palette(self.css.read_bytes())
        first_id=re.search(r'style "domainos-tooltip-([0-9a-f]{10})"',initial_rc)
        self.assertIsNotNone(first_id)
        self.assertIn('widget "*gtk-tooltip*" style : highest "domainos-tooltip-'+first_id[1]+'"',initial_rc)
        self.assertIn('bg[NORMAL] = "'+first_palette['tooltip_background_breeze']+'"',initial_rc)
        self.assertIn('fg[NORMAL] = "'+first_palette['tooltip_text_breeze']+'"',initial_rc)

        next_palette=self.palette({'tooltip_background_breeze':'#e7d2a8',
                                   'tooltip_text_breeze':'#203448'})
        self.css.write_bytes(next_palette)
        result=self.call(runtime.refresh,theme='DomainOS-SR10-4-KDE')
        refreshed=Path(result['bundles']['DomainOS-SR10-4-KDE'])
        refreshed_rc=(refreshed/'gtkrc').read_text()
        second_id=re.search(r'style "domainos-tooltip-([0-9a-f]{10})"',refreshed_rc)
        self.assertIsNotNone(second_id)
        self.assertNotEqual(first_id[1],second_id[1])
        self.assertIn('bg[NORMAL] = "#e7d2a8"',refreshed_rc)
        self.assertIn('fg[NORMAL] = "#203448"',refreshed_rc)
        self.assertTrue(initial.is_dir(),'unreparsed GTK2 processes may still reference the previous immutable bundle')
        self.assertEqual(files(self.source),self.protected)

    def test_iconview_uses_view_and_selection_roles_after_live_palette_refresh(self):
        first=self.call(runtime.setup,theme='DomainOS-SR10-4-KDE')
        initial=Path(first['bundles']['DomainOS-SR10-4-KDE'])
        initial_rc=(initial/'gtkrc').read_text()
        first_palette=exported_palette(self.css.read_bytes())
        first_id=re.search(r'style "domainos-iconview-([0-9a-f]{10})"',initial_rc)
        self.assertIsNotNone(first_id)
        self.assertIn('widget_class "*GtkIconView" style : highest "domainos-iconview-'+first_id[1]+'"',initial_rc)

        def iconview_block(text,identity):
            return re.search(
                r'style "domainos-iconview-'+identity+r'" = "domainos-default-'+identity+
                r'" \{(?P<body>.*?)\}',text,re.S)

        block=iconview_block(initial_rc,first_id[1])
        self.assertIsNotNone(block)
        first_selected_face,first_selected_ink=gtk2_domainos_palette.iconview_selected_colors(first_palette)
        for declaration in (
            'base[NORMAL] = "'+first_palette['theme_base_color_breeze']+'"',
            'text[NORMAL] = "'+first_palette['theme_text_color_breeze']+'"',
            'base[SELECTED] = "'+first_selected_face+'"',
            'text[SELECTED] = "'+first_selected_ink+'"',
            'base[INSENSITIVE] = "'+first_palette['insensitive_base_color_breeze']+'"',
            'text[INSENSITIVE] = "'+first_palette['insensitive_base_fg_color_breeze']+'"',
        ):
            self.assertIn(declaration,block['body'])

        second_palette=self.palette({
            'theme_base_color_breeze':'#e8d070','theme_text_color_breeze':'#151515',
            'theme_selected_bg_color_breeze':'#6655aa','theme_selected_fg_color_breeze':'#ffffff',
            'insensitive_base_color_breeze':'#bca958','insensitive_base_fg_color_breeze':'#534c32',
        })
        self.css.write_bytes(second_palette)
        refreshed=self.call(runtime.refresh,theme='DomainOS-SR10-4-KDE')
        final=Path(refreshed['bundles']['DomainOS-SR10-4-KDE'])
        final_rc=(final/'gtkrc').read_text()
        next_id=re.search(r'style "domainos-iconview-([0-9a-f]{10})"',final_rc)
        self.assertIsNotNone(next_id)
        self.assertNotEqual(first_id[1],next_id[1])
        next_palette=exported_palette(second_palette)
        next_selected_face,next_selected_ink=gtk2_domainos_palette.iconview_selected_colors(next_palette)
        next_block=iconview_block(final_rc,next_id[1])
        self.assertIsNotNone(next_block)
        for declaration in (
            'base[NORMAL] = "'+next_palette['theme_base_color_breeze']+'"',
            'text[NORMAL] = "'+next_palette['theme_text_color_breeze']+'"',
            'base[SELECTED] = "'+next_selected_face+'"',
            'text[SELECTED] = "'+next_selected_ink+'"',
            'base[INSENSITIVE] = "'+next_palette['insensitive_base_color_breeze']+'"',
            'text[INSENSITIVE] = "'+next_palette['insensitive_base_fg_color_breeze']+'"',
        ):
            self.assertIn(declaration,next_block['body'])
        self.assertNotRegex(next_block['body'],r'GtkIconView::(?:columns|item-width|item-padding|column-spacing|row-spacing|margin|spacing)')
        self.assertTrue(initial.is_dir(),'an open GTK2 process may still reference the preceding immutable bundle')
        self.assertEqual(files(self.source),self.protected)

    def test_entry_selected_state_inverts_active_view_roles_only(self):
        first=self.call(runtime.setup,theme='DomainOS-SR10-4-KDE')
        initial=Path(first['bundles']['DomainOS-SR10-4-KDE'])
        initial_rc=(initial/'gtkrc').read_text()
        first_palette=exported_palette(self.css.read_bytes())
        entry_id=re.search(r'style "domainos-entry-([0-9a-f]{10})"',initial_rc)
        self.assertIsNotNone(entry_id)
        view=first_palette['theme_base_color_breeze']
        view_text=first_palette['theme_text_color_breeze']
        entry_face=art.tone(first_palette[art.ROLES['header'][0]],
                            1.0-gtk2_domainos_palette.ENTRY_FACE_FACTOR,'#000000')
        self.assertEqual(entry_face,'#2a80a9')
        entry_style=re.search(
            r'style "domainos-entry-'+entry_id[1]+r'" = "domainos-default-'+entry_id[1]+
            r'" \{(?P<body>.*?)\}',initial_rc,re.S)
        self.assertIsNotNone(entry_style)
        for declaration in (
            'base[NORMAL] = "'+entry_face+'"',
            'base[PRELIGHT] = "'+entry_face+'"',
            'base[ACTIVE] = "'+entry_face+'"',
            'bg[SELECTED] = "'+view_text+'"',
            'fg[SELECTED] = "'+view+'"',
            'base[SELECTED] = "'+view_text+'"',
            'text[SELECTED] = "'+view+'"',
        ):
            self.assertIn(declaration,entry_style['body'])
        self.assertIn('widget_class "*GtkEntry" style : highest "domainos-entry-'+entry_id[1]+'"',initial_rc)
        # Generic list/menu selection must continue using the KDE Selection roles.
        self.assertIn('bg[SELECTED] = "'+first_palette['theme_selected_bg_color_breeze']+'"',initial_rc)
        self.assertIn('fg[SELECTED] = "'+first_palette['theme_selected_fg_color_breeze']+'"',initial_rc)

        next_header='#e7d955'
        self.css.write_bytes(self.palette({'theme_text_color_breeze':'#d8e28a',
                                           'theme_base_color_breeze':'#34485c',
                                           'theme_header_background_breeze':next_header}))
        refreshed=self.call(runtime.refresh,theme='DomainOS-SR10-4-KDE')
        next_rc=(Path(refreshed['bundles']['DomainOS-SR10-4-KDE'])/'gtkrc').read_text()
        next_id=re.search(r'style "domainos-entry-([0-9a-f]{10})"',next_rc)
        self.assertIsNotNone(next_id)
        self.assertNotEqual(entry_id[1],next_id[1])
        next_face=art.tone(next_header,1.0-gtk2_domainos_palette.ENTRY_FACE_FACTOR,'#000000')
        self.assertIn('base[NORMAL] = "'+next_face+'"',next_rc)
        self.assertIn('base[SELECTED] = "#d8e28a"',next_rc)
        self.assertIn('text[SELECTED] = "#34485c"',next_rc)
        self.assertEqual(files(self.source),self.protected)

    def test_edited_domainos_source_is_rejected_before_wrapper_publication(self):
        asset=self.source/'common/assets/scrollbar-stepper-up-normal.png'
        asset.write_bytes(asset.read_bytes()+b'edited fixture')
        before=files(self.private)
        with self.assertRaises(Failure):self.call(runtime.setup)
        after=files(self.private)
        lock=str((self.roots.runtime/'lock').relative_to(self.private))
        after.pop(lock,None)
        self.assertEqual(after,before)
        self.assertFalse(self.roots.control.exists())


if __name__ == '__main__':
    unittest.main()
