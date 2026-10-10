# SPDX-License-Identifier: GPL-3.0-or-later
"""Configuration rollback and session boundaries for the one-shot QML reload."""
import configparser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import reload_decoration as module

class ReloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.config=self.root/'kwinrc';self.state=self.root/'state'
        self.original=b'[Plugins]\nblurEnabled=true\n\n[org.kde.kdecoration2]\nBorderSize=Normal\n'
        self.config.write_bytes(self.original);self.config.chmod(0o640);self.calls=[]
    def transport(self, method):
        self.calls.append(method)
        if method=='reconfigure':return None
        parser=configparser.ConfigParser();parser.optionxform=str
        parser.read(self.config)
        group=parser['org.kde.kdecoration2'] if parser.has_section('org.kde.kdecoration2') else {}
        plugin=group.get('library',module.AURORAE);theme=group.get('theme','irixium_irix_classic_v4')
        return f'Plugin: {plugin}\nTheme: {theme}\n'
    def run_reload(self,**kwargs):
        return module.reload(self.config,self.state,call=self.transport,**kwargs)
    def test_restores_exact_bytes_permissions_and_effect_preferences(self):
        receipt=self.run_reload();record=json.loads(receipt.read_text())
        self.assertEqual(self.config.read_bytes(),self.original)
        self.assertEqual(self.config.stat().st_mode & 0o777,0o640)
        self.assertEqual(record['before'],record['after']);self.assertEqual(record['status'],'reloaded')
        self.assertEqual(self.calls.count('reconfigure'),2)
    def test_restores_modern_selection(self):
        self.original=b'[org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae\ntheme=irixium_modern\nButtonsOnRight=IA\n'
        self.config.write_bytes(self.original);self.run_reload()
        self.assertEqual(self.config.read_bytes(),self.original)
    def test_restores_domainos_selection_and_preferences(self):
        self.original=b'[org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae\ntheme=domainos_sr104\nButtonsOnRight=IA\n'
        self.config.write_bytes(self.original)
        receipt=self.run_reload()
        self.assertEqual(json.loads(receipt.read_text())['status'],'reloaded')
        self.assertEqual(self.config.read_bytes(),self.original)
    def test_waits_for_asynchronous_native_plugin_change(self):
        values=iter(['Plugin: org.kde.kwin.aurorae\nTheme: domainos_sr104\n',
                     'Plugin: org.kde.breeze\nTheme: Breeze\n'])
        with patch.object(module.time,'sleep'):
            self.assertTrue(module.wait_selection(lambda _:next(values),(module.BREEZE,None),plugin_only=True))
    def test_absent_user_config_returns_to_absence(self):
        self.config.unlink();self.run_reload();self.assertFalse(self.config.exists())
    def test_failure_still_restores_configuration_and_reconfigures(self):
        def failing(method):
            if method=='reconfigure' and self.calls.count('reconfigure')==0:
                self.calls.append(method);raise subprocess.CalledProcessError(1,['gdbus'])
            return self.transport(method)
        with self.assertRaises(subprocess.CalledProcessError):
            module.reload(self.config,self.state,call=failing)
        self.assertEqual(self.config.read_bytes(),self.original)
        self.assertEqual(self.calls.count('reconfigure'),2)
    def test_concurrent_changes_are_not_overwritten(self):
        def changing(method):
            output=self.transport(method)
            if method=='supportInformation' and module.BREEZE in output:
                self.config.write_bytes(self.config.read_bytes()+b'new_user_setting=keep\n')
            return output
        with self.assertRaises(module.Failure):module.reload(self.config,self.state,call=changing)
        self.assertIn(b'new_user_setting=keep',self.config.read_bytes())
    def test_dry_run_does_not_write(self):
        self.run_reload(dry=True);self.assertFalse(self.state.exists())
        self.assertEqual(self.config.read_bytes(),self.original);self.assertNotIn('reconfigure',self.calls)
    def test_qml_engine_release_is_checked_before_restoring_selection(self):
        def refusing(method):
            self.calls.append(method)
            return None if method=='reconfigure' else 'Plugin: org.kde.kwin.aurorae\nTheme: irixium_irix_classic_v4\n'
        with self.assertRaises(module.Failure):module.reload(self.config,self.state,call=refusing)
        self.assertEqual(self.config.read_bytes(),self.original)
        self.assertEqual(self.calls.count('reconfigure'),2)
    def test_other_decoration_is_not_touched(self):
        receipt=module.reload(self.config,self.state,call=lambda method:'Plugin: org.kde.breeze\nTheme: Breeze\n')
        self.assertIsNone(receipt);self.assertFalse(self.state.exists());self.assertEqual(self.config.read_bytes(),self.original)
    def test_root_is_refused(self):
        with patch.object(module.os,'geteuid',return_value=0),self.assertRaises(module.Failure):module.check_session()
    def test_foreign_session_is_refused(self):
        with patch.object(module.os,'getuid',return_value=1003),patch.object(module.os,'geteuid',return_value=1003),patch.dict(module.os.environ,{'XDG_RUNTIME_DIR':'/run/user/1000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1000/bus'}),self.assertRaises(module.Failure):module.check_session()

if __name__=='__main__':unittest.main()
