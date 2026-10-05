# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('manage',ROOT/'gerenciar.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.dest=self.base/'data/kwin/decorations'/m.ID
        self.config=self.base/'config/kwinrc';self.state=self.base/'state'
        self.values={'library':'org.kde.kwin.aurorae','theme':'__aurorae__svg__Irixium',
                     'ButtonsOnRight':'IA','font':'unchanged','custom':'unchanged'}
        self.calls=[]
        def get(config,key):return self.values.get(key)
        def put(config,key,value):
            self.calls.append((key,value))
            if value is None:self.values.pop(key,None)
            else:self.values[key]=value
        self.put=put
        patches=[patch.object(m,'locations',return_value=(self.dest,self.config,self.state)),
                 patch.object(m,'get_key',side_effect=get),patch.object(m,'put_key',side_effect=put),
                 patch.object(m.os,'geteuid',return_value=1000),patch.object(m,'reconfigure'),
                 patch('sys.stdout',new_callable=io.StringIO)]
        self.ps=patches
        for p in self.ps:p.start()
    def tearDown(self):
        for p in self.ps[::-1]:p.stop()
        self.temp.cleanup()
    def test_install_does_not_activate_by_default(self):
        before=self.values.copy();m.install();self.assertEqual(before,self.values)
        self.assertEqual(m.hashes(self.dest),m.hashes(m.SOURCE))
    def test_activation_changes_only_library_and_theme(self):
        m.install(True);self.assertEqual(self.values['theme'],m.ID)
        self.assertEqual({k for k,v in self.calls},{'library','theme'})
        self.assertEqual(self.values['ButtonsOnRight'],'IA')
    def test_restore_reinstates_previous_theme(self):
        before=self.values.copy();m.install(True);m.restore()
        self.assertEqual(self.values,before);self.assertFalse(self.dest.exists())
    def test_restore_after_gui_selection(self):
        before=self.values.copy();m.install(False);self.values['theme']=m.ID;m.restore()
        self.assertEqual(self.values,before)
    def test_other_theme_selected_after_install_is_preserved(self):
        m.install(True);self.values['theme']='another';m.restore()
        self.assertEqual(self.values['theme'],'another')
    def test_unrelated_keys_edited_later_are_preserved(self):
        m.install(True);self.values['custom']='edited';m.restore()
        self.assertEqual(self.values['custom'],'edited')
    def test_previous_native_theme_directory_restored(self):
        self.dest.mkdir(parents=True);(self.dest/'custom.qml').write_text('previous')
        m.install(True);m.restore();self.assertEqual((self.dest/'custom.qml').read_text(),'previous')
    def test_missing_keys_restored_as_absent(self):
        self.values.pop('theme');self.values.pop('library');m.install(True);m.restore()
        self.assertNotIn('theme',self.values);self.assertNotIn('library',self.values)
    def test_edited_theme_is_not_destroyed_on_restore(self):
        m.install(True);(self.dest/'custom.qml').write_text('edited')
        with self.assertRaises(RuntimeError):m.restore()
        self.assertTrue((self.dest/'custom.qml').exists())
    def test_symlink_destination_refused(self):
        outside=self.base/'outside';outside.mkdir();self.dest.parent.mkdir(parents=True)
        self.dest.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(RuntimeError):m.install()
        self.assertTrue(self.dest.is_symlink())
    def test_backup_has_private_directory_permissions(self):
        b=m.install();self.assertEqual(b.stat().st_mode & 0o777,0o700)
    def test_failed_activation_rolls_back(self):
        before=self.values.copy()
        def fail(config,key,value):
            if key=='theme' and value==m.ID:raise RuntimeError('simulated failure')
            self.put(config,key,value)
        with patch.object(m,'put_key',side_effect=fail):
            with self.assertRaises(RuntimeError):m.install(True)
        self.assertEqual(self.values,before);self.assertFalse(self.dest.exists())
    def test_root_install_refused(self):
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaises(RuntimeError):m.install()
        self.assertFalse(self.dest.exists())
    def test_root_restore_refused(self):
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaises(RuntimeError):m.restore()
    def test_changed_state_path_is_refused(self):
        b=m.install();p=b/'receipt.json';d=json.loads(p.read_text());d['config']='other'
        p.write_text(json.dumps(d))
        with self.assertRaises(RuntimeError):m.restore()
    def test_path_traversal_receipt_refused(self):
        m.install();(self.state/'latest.json').write_text('{"backup":"../outside"}')
        with self.assertRaises(RuntimeError):m.restore()
    def test_repeated_restore_is_refused(self):
        m.install();m.restore()
        with self.assertRaises(RuntimeError):m.restore()
    def test_relative_xdg_paths_refused(self):
        with patch.dict(os.environ,{'XDG_DATA_HOME':'relative'}):
            with self.assertRaises(RuntimeError):m.xdg('XDG_DATA_HOME',Path('/tmp/data'))
    def test_package_has_native_metadata(self):
        d=json.loads((m.SOURCE/'metadata.json').read_text());self.assertEqual(d['KPackageStructure'],'KWin/Decoration')
        self.assertEqual(d['KPlugin']['Id'],m.ID)
    def test_no_font_binaries_or_legacy_shared_components(self):
        names=[p.name for p in m.SOURCE.rglob('*')]
        self.assertNotIn('MenuButton.qml',names);self.assertNotIn('AuroraeButtonGroup.qml',names)
        self.assertFalse(any(Path(n).suffix.lower() in ('.ttf','.otf','.woff','.woff2','.pcf','.bdf') for n in names))

if __name__=='__main__':unittest.main(verbosity=2)
