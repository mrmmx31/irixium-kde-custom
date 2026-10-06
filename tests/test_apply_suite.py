# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import apply_suite


class ApplySuiteTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.data,self.config,self.state=[self.root/p for p in ('data','config','state')]
        for package,kvantum,decoration in apply_suite.PROFILES.values():
            for p in (self.data/'plasma/look-and-feel'/package/'contents/defaults',
                      self.config/'Kvantum'/kvantum/(kvantum+'.kvconfig'),
                      self.data/'kwin/decorations'/decoration/'contents/ui/main.qml'):
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
