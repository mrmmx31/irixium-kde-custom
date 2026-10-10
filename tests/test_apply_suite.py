# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import redirect_stdout
import builtins
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
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import apply_suite


class ApplySuiteTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='.gtk-suite-test-',dir=ROOT);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        home_patch=patch('select_gtk.Path.home',return_value=self.root)
        home_patch.start();self.addCleanup(home_patch.stop)
        live_patch=patch.object(apply_suite,'native_ready',return_value=False)
        live_patch.start();self.addCleanup(live_patch.stop)
        self.data,self.config,self.state=[self.root/p for p in ('data','config','state')]
        for package,kvantum,decoration in apply_suite.PROFILES.values():
            for p in (self.data/'plasma/look-and-feel'/package/'contents/defaults',
                      self.config/'Kvantum'/kvantum/(kvantum+'.kvconfig'),
                      self.data/'kwin/decorations'/decoration/'contents/ui/main.qml',
                      self.data/'themes'/next(p['gtk'] for p in apply_suite.PROFILE_COMPONENTS.values() if p['global']==package)/'gtk-2.0/gtkrc',
                      self.root/'.themes'/next(p['gtk'] for p in apply_suite.PROFILE_COMPONENTS.values() if p['global']==package)/'gtk-2.0/gtkrc',
                      self.data/'themes'/next(p['gtk'] for p in apply_suite.PROFILE_COMPONENTS.values() if p['global']==package)/'gtk-3.0/gtk.css',
                      self.data/'themes'/next(p['gtk'] for p in apply_suite.PROFILE_COMPONENTS.values() if p['global']==package)/'gtk-4.0/gtk.css'):
                p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
        for profile in apply_suite.PROFILE_COMPONENTS.values():
            for p in (self.data/'icons'/profile['icons']/'index.theme',
                      self.data/'icons'/profile['cursor']/'index.theme',
                      self.data/'icons'/profile['cursor']/'cursors/wait',
                      self.data/'icons'/profile['cursor']/'cursors/progress',
                      self.data/'color-schemes'/(profile['colors']+'.colors'),
                      self.data/'plasma/desktoptheme'/profile['plasma']/'metadata.desktop',
                      self.data/'wallpapers'/profile['wallpaper']/'metadata.json',
                      self.data/'plasma/look-and-feel'/profile['global']/'contents/splash/Splash.qml'):
                p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
        self.kv=self.config/'Kvantum/kvantum.kvconfig'
        self.original=b'[General]\ntheme=Before\n[Applications]\nOther=example\n'
        self.kv.write_bytes(self.original)
        self.output=redirect_stdout(io.StringIO());self.output.__enter__()
        self.addCleanup(self.output.__exit__,None,None,None)

    def run_apply(self,*args,side_effect=None):
        with patch.object(apply_suite,'roots',return_value=(self.data,self.config,self.state)), \
             patch.object(sys,'argv',['apply_suite',*args]), \
             patch.object(apply_suite.shutil,'which',return_value='/fake/plasma-apply-lookandfeel'), \
             patch.object(apply_suite.subprocess,'run',side_effect=side_effect) as call:
            apply_suite.main()
            return call

    def test_dry_run_does_not_write(self):
        call=self.run_apply('classic','--verificar');call.assert_not_called()
        self.assertEqual(self.kv.read_bytes(),self.original);self.assertFalse(self.state.exists())

    def test_domainos_uses_own_companions_and_scheme_without_resetting_layout(self):
        call=self.run_apply('domainos')
        call.assert_called_once_with(['/fake/plasma-apply-lookandfeel','--apply',
            'org.magpie.irixclassic.domainos.desktop'],check=True)
        self.assertIn(b'theme=DomainOS-SR10-4',self.kv.read_bytes())
        self.assertIn(b'gtk-theme-name=DomainOS-SR10-4-KDE',
                      (self.config/'gtk-3.0/settings.ini').read_bytes())
        self.run_apply('--restaurar');self.assertEqual(self.kv.read_bytes(),self.original)

    def test_domainos_requires_own_scheme_even_when_irixium_exists(self):
        (self.data/'color-schemes/DomainOS-SR10-4.colors').unlink()
        with self.assertRaises(apply_suite.Failure):self.run_apply('domainos')
        self.assertEqual(self.kv.read_bytes(),self.original)

    def test_matching_kvantum_preserves_exceptions_and_native_apply_preserves_layout(self):
        call=self.run_apply('classic')
        call.assert_called_once_with(['/fake/plasma-apply-lookandfeel','--apply','org.magpie.irixclassic.desktop'],check=True)
        self.assertIn(b'theme=IrixClassic',self.kv.read_bytes())
        self.assertIn(b'Other=example',self.kv.read_bytes())
        self.run_apply('--restaurar');self.assertEqual(self.kv.read_bytes(),self.original)

    def test_partial_native_failure_restores_previous_files(self):
        def fail(*args,**kwargs):
            (self.config/'kdeglobals').write_text('partial mutation')
            raise OSError('native failure')
        with self.assertRaises(OSError):self.run_apply('moderno',side_effect=fail)
        self.assertEqual(self.kv.read_bytes(),self.original)
        self.assertFalse((self.config/'kdeglobals').exists())

    def test_restore_refuses_subsequent_user_edit(self):
        self.run_apply('classic');self.kv.write_text('user edit')
        with self.assertRaises(apply_suite.Failure):self.run_apply('--restaurar')
        self.assertEqual(self.kv.read_text(),'user edit')

    def test_native_gtk_and_qt_settings_are_restored(self):
        gtk = self.config/'gtkrc'
        gtk.write_bytes(b'original GTK settings\n')
        def apply(*args, **kwargs):
            for name in ('gtkrc', 'gtkrc-2.0', 'Trolltech.conf'):
                (self.config/name).write_text('native theme settings\n')
        self.run_apply('classic', side_effect=apply)
        self.run_apply('--restaurar')
        self.assertEqual(gtk.read_bytes(), b'original GTK settings\n')
        self.assertFalse((self.config/'gtkrc-2.0').exists())
        self.assertFalse((self.config/'Trolltech.conf').exists())

    def test_gtk_selection_preserves_other_preferences_and_restores(self):
        settings=self.config/'gtk-3.0/settings.ini'
        settings.parent.mkdir(parents=True)
        original=b'[Settings]\ngtk-theme-name=Before\ngtk-font-name=User font\n'
        settings.write_bytes(original)
        self.run_apply('classic')
        self.assertIn(b'gtk-theme-name=IrixClassic',settings.read_bytes())
        self.assertIn(b'gtk-icon-theme-name=IrixClassic-SGI',settings.read_bytes())
        self.assertIn(b'gtk-font-name=User font',settings.read_bytes())
        self.run_apply('--restaurar')
        self.assertEqual(settings.read_bytes(),original)
        self.assertFalse((self.config/'gtk-4.0/settings.ini').exists())

    def test_profile_cursor_is_selected_for_kde_and_gtk_without_changing_size(self):
        settings = self.config/'kcminputrc'
        original = b'[Mouse]\ncursorTheme=Before\ncursorSize=48\nX11LibInputXAccelProfileFlat=true\n'
        settings.write_bytes(original)
        for profile, cursor in (('classic', 'SGI-Classic'), ('moderno', 'SGI-Irixium')):
            self.run_apply(profile)
            self.assertIn(('cursorTheme='+cursor).encode(), settings.read_bytes())
            self.assertIn(b'cursorSize=48', settings.read_bytes())
            self.assertIn(b'X11LibInputXAccelProfileFlat=true', settings.read_bytes())
            for version in ('3.0', '4.0'):
                self.assertIn(('gtk-cursor-theme-name='+cursor).encode(),
                              (self.config/f'gtk-{version}/settings.ini').read_bytes())
            self.run_apply('--restaurar')
            self.assertEqual(settings.read_bytes(), original)

    def test_missing_profile_cursor_refuses_application_before_writing(self):
        cursor = self.data/'icons'/apply_suite.PROFILE_COMPONENTS['classic']['cursor']/'index.theme'
        cursor.unlink()
        with self.assertRaises(apply_suite.Failure): self.run_apply('classic')
        self.assertEqual(self.kv.read_bytes(), self.original)
        self.assertFalse(self.state.exists())

    def test_gtk2_theme_selection_preserves_preferences_and_is_restored(self):
        rc = self.root/'.gtkrc-2.0'
        original = b'gtk-theme-name = "Before"\ngtk-font-name="User font"\ngtk-cursor-theme-size=48\n'
        rc.write_bytes(original)
        self.run_apply('classic')
        self.assertIn(b'gtk-theme-name="IrixClassic-KDE"', rc.read_bytes())
        self.assertIn(b'gtk-font-name="User font"', rc.read_bytes())
        self.assertIn(b'gtk-cursor-theme-size=48', rc.read_bytes())
        self.run_apply('--restaurar')
        self.assertEqual(rc.read_bytes(), original)

    def test_missing_sound_profile_can_be_required_before_native_apply(self):
        with self.assertRaises(apply_suite.Failure):
            self.run_apply('classic','--exigir-sons')
        self.assertEqual(self.kv.read_bytes(),self.original)
        self.assertFalse(self.state.exists())

    def test_absent_optional_sound_support_preserves_selection_by_default(self):
        original_import = builtins.__import__
        def absent(name, *args, **kwargs):
            if name == 'audit_suite':
                raise ModuleNotFoundError("No module named 'audit_suite'", name=name)
            return original_import(name, *args, **kwargs)
        globals_file = self.config/'kdeglobals'
        original = b'[Sounds]\nTheme=User sounds\nEnable=false\n'
        globals_file.write_bytes(original)
        with patch('builtins.__import__', side_effect=absent):
            call = self.run_apply('classic')
        call.assert_called_once()
        self.assertEqual(globals_file.read_bytes(), original)
        self.assertIn(b'theme=IrixClassic', self.kv.read_bytes())

    def test_absent_required_sound_support_refuses_before_selection(self):
        original_import = builtins.__import__
        def absent(name, *args, **kwargs):
            if name == 'audit_suite':
                raise ModuleNotFoundError("No module named 'audit_suite'", name=name)
            return original_import(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=absent):
            with self.assertRaisesRegex(apply_suite.Failure, 'Suporte opcional de sons ausente'):
                self.run_apply('classic', '--exigir-sons')
        self.assertEqual(self.kv.read_bytes(), self.original)
        self.assertFalse(self.state.exists())

    def test_no_sounds_never_imports_optional_support(self):
        with patch.object(apply_suite, 'optional_sound_module', side_effect=AssertionError('unexpected sound import')):
            call = self.run_apply('classic', '--sem-sons')
        call.assert_called_once()

    def test_existing_sound_support_import_failure_is_not_optional(self):
        error = ModuleNotFoundError("No module named 'irix_sounds'", name='irix_sounds')
        with patch('audit_suite.sound_module', side_effect=error):
            with self.assertRaises(ModuleNotFoundError) as caught:
                self.run_apply('classic')
        self.assertIs(caught.exception, error)
        self.assertEqual(self.kv.read_bytes(), self.original)
        self.assertFalse(self.state.exists())

    def test_existing_sound_catalog_failure_is_not_optional(self):
        from types import SimpleNamespace
        theme = self.data/'sounds/IrixClassic'; theme.mkdir(parents=True)
        def corrupt(): raise apply_suite.Failure('catálogo de sons corrompido')
        module = SimpleNamespace(THEME='IrixClassic', catalog=corrupt, validate_theme=lambda *_: None)
        with patch('audit_suite.sound_module', return_value=module):
            with self.assertRaisesRegex(apply_suite.Failure, 'catálogo de sons corrompido'):
                self.run_apply('classic')
        self.assertEqual(self.kv.read_bytes(), self.original)
        self.assertFalse(self.state.exists())

    def test_distribution_wrapper_without_sounds_applies_and_restores_in_private_session(self):
        """Real wrapper/files/backup, private D-Bus; only KDE apply is a process double."""
        session = shutil.which('dbus-run-session')
        if not session:
            self.skipTest('dbus-run-session required for the private wrapper test')
        distribution = self.root/'distribution'
        shutil.copytree(ROOT/'tools', distribution/'tools',
                        ignore=shutil.ignore_patterns('audit_suite.py', '__pycache__'))
        shutil.copy2(ROOT/'components.json', distribution/'components.json')
        shutil.copy2(ROOT/'aplicar-tema.sh', distribution/'aplicar-tema.sh')
        binary = self.root/'bin'; binary.mkdir()
        native = binary/'plasma-apply-lookandfeel'
        calls = self.root/'KDE-APPLY-CALLS.jsonl'
        native.write_text('#!/usr/bin/python3\nimport json,os,sys\n'
            'with open(os.environ["PRIVATE_KDE_APPLY_LOG"],"a") as f:\n'
            ' f.write(json.dumps({"args":sys.argv[1:],"home":os.environ["HOME"],'
            '"bus":os.environ["DBUS_SESSION_BUS_ADDRESS"]})+"\\n")\n')
        native.chmod(0o755)
        runtime = self.root/'runtime'; runtime.mkdir(mode=0o700)
        env = dict(os.environ, HOME=str(self.root), XDG_DATA_HOME=str(self.data),
            XDG_CONFIG_HOME=str(self.config), XDG_STATE_HOME=str(self.state),
            XDG_RUNTIME_DIR=str(runtime), PATH=str(binary)+os.pathsep+'/usr/bin:/bin',
            PRIVATE_KDE_APPLY_LOG=str(calls), PYTHONDONTWRITEBYTECODE='1')
        for name in ('DBUS_SESSION_BUS_ADDRESS', 'DBUS_SYSTEM_BUS_ADDRESS', 'DISPLAY',
                     'WAYLAND_DISPLAY', 'PYTHONPATH', 'PYTHONHOME', 'GTK2_RC_FILES', 'XDG_CONFIG_DIRS'):
            env.pop(name, None)
        globals_file = self.config/'kdeglobals'
        original = b'[Sounds]\nTheme=User sounds\nEnable=false\n'
        globals_file.write_bytes(original)
        def wrapper(*arguments):
            return subprocess.run([session, '--', '/bin/bash', str(distribution/'aplicar-tema.sh'),
                                   *arguments], env=env, capture_output=True, text=True, timeout=20)
        required = wrapper('classic', '--exigir-sons')
        self.assertNotEqual(required.returncode, 0)
        self.assertIn('Suporte opcional de sons ausente', required.stderr)
        self.assertFalse(calls.exists()); self.assertFalse(self.state.exists())
        applied = wrapper('classic')
        self.assertEqual(applied.returncode, 0, applied.stdout+applied.stderr)
        self.assertEqual(globals_file.read_bytes(), original)
        self.assertIn(b'theme=IrixClassic', self.kv.read_bytes())
        call = json.loads(calls.read_text())
        self.assertEqual(call['args'], ['--apply', apply_suite.PROFILES['classic'][0]])
        self.assertEqual(call['home'], str(self.root))
        self.assertNotEqual(call['bus'], os.environ.get('DBUS_SESSION_BUS_ADDRESS'))
        restored = wrapper('--restaurar')
        self.assertEqual(restored.returncode, 0, restored.stdout+restored.stderr)
        self.assertEqual(self.kv.read_bytes(), self.original)
        self.assertEqual(globals_file.read_bytes(), original)
        without = wrapper('classic', '--sem-sons')
        self.assertEqual(without.returncode, 0, without.stdout+without.stderr)
        self.assertEqual(globals_file.read_bytes(), original)

    def test_validated_sound_profile_selects_theme_without_enabling_sounds(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        theme=self.data/'sounds/IrixClassic';theme.mkdir(parents=True)
        globals_file=self.config/'kdeglobals'
        original=b'[Sounds]\nTheme=Before\nEnable=false\n'
        globals_file.write_bytes(original)
        validate=Mock()
        module=SimpleNamespace(THEME='IrixClassic',catalog=lambda: {},validate_theme=validate)
        with patch('audit_suite.sound_module',return_value=module):
            self.run_apply('classic','--exigir-sons')
        validate.assert_called_once_with(theme,{})
        self.assertIn(b'Theme=IrixClassic',globals_file.read_bytes())
        self.assertIn(b'Enable=false',globals_file.read_bytes())
        self.run_apply('--restaurar')
        self.assertEqual(globals_file.read_bytes(),original)

    def test_invalid_sound_profile_refuses_application_before_writes(self):
        from types import SimpleNamespace
        theme=self.data/'sounds/IrixClassic';theme.mkdir(parents=True)
        def fail(*args): raise apply_suite.Failure('invalid sound data')
        module=SimpleNamespace(THEME='IrixClassic',catalog=lambda:{},validate_theme=fail)
        with patch('audit_suite.sound_module',return_value=module),self.assertRaises(apply_suite.Failure):
            self.run_apply('classic')
        self.assertEqual(self.kv.read_bytes(),self.original)
        self.assertFalse(self.state.exists())

    def test_missing_profile_icon_theme_refuses_partial_application(self):
        (self.data/'icons/IrixClassic-SGI/index.theme').unlink()
        with self.assertRaises(apply_suite.Failure):
            self.run_apply('classic')
        self.assertEqual(self.kv.read_bytes(),self.original)
        self.assertFalse(self.state.exists())
