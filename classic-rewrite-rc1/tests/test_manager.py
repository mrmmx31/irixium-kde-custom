# SPDX-License-Identifier: GPL-3.0-or-later
"""Real filesystem tests, with the native KDE config backend mocked explicitly."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('manager',ROOT/'tools/manage.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class FakeConfig:
    def __init__(self,path):
        self.path=path;self.data={'library':m.LIBRARY,'theme':'irixium_irix_classic_v4','ButtonsOnRight':'IA'}
        self.fail=False
    def get(self,key):return self.data.get(key)
    def put(self,key,value):
        if self.fail and key=='theme':
            self.fail=False;raise RuntimeError('simulated backend failure')
        if value is None:self.data.pop(key,None)
        else:self.data[key]=value
    def values(self):return {k:self.get(k) for k in m.KEYS}

class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.base=self.root/'data/kwin/decorations';self.base.mkdir(parents=True)
        self.cfg=FakeConfig(self.root/'config/kwinrc')
        self.state=self.root/'state';self.manager=m.Manager(self.base,self.cfg,self.state)
        self.user=patch.object(m.os,'geteuid',return_value=1000);self.user.start()
        self.reload=patch.object(m,'reconfigure');self.reload.start()
        self.stdout=contextlib.redirect_stdout(io.StringIO());self.stdout.__enter__()
    def tearDown(self):
        self.stdout.__exit__(None,None,None);self.reload.stop();self.user.stop();self.temp.cleanup()
    def seed(self,tid='irixium_irix_classic_v4'):
        dest=self.base/tid;shutil.copytree(m.BUNDLE/'package',dest)
        meta=m.read_json(dest/'metadata.json');meta['KPlugin']['Id']=tid;m.atomic_json(dest/'metadata.json',meta)
        (dest/'old-note.txt').write_text('local-before')
        return dest
    def test_reuses_selected_v4(self):
        self.seed();self.assertEqual(self.manager.choose(),'irixium_irix_classic_v4')
    def test_reuses_selected_v5(self):
        self.cfg.data['theme']='irixium_irix_classic_v5';self.seed(self.cfg.get('theme'))
        self.assertEqual(self.manager.choose(),'irixium_irix_classic_v5')
    def test_new_user_gets_stable_id(self):
        self.cfg.data['theme']='Breeze';self.assertEqual(self.manager.choose(),'irix_classic')
    def test_unselected_single_install_is_reused(self):
        self.seed();self.cfg.data['theme']='Breeze';self.assertEqual(self.manager.choose(),'irixium_irix_classic_v4')
    def test_ambiguous_installations_refuse_guess(self):
        self.seed();self.seed('irixium_irix_classic_v5');self.cfg.data['theme']='Breeze'
        with self.assertRaises(RuntimeError):self.manager.choose()
    def test_explicit_target_resolves_ambiguity(self):
        self.seed();self.seed('irixium_irix_classic_v5');self.cfg.data['theme']='Breeze'
        self.assertEqual(self.manager.choose('irixium_irix_classic_v5'),'irixium_irix_classic_v5')
    def test_unknown_target_rejected(self):
        with self.assertRaises(RuntimeError):self.manager.choose('../etc')
    def test_verify_is_read_only(self):
        d=self.seed();before=m.tree_hashes(self.root);self.manager.verify()
        self.assertEqual(before,m.tree_hashes(self.root));self.assertFalse(self.state.exists())
    def test_metadata_mismatch_rejected(self):
        d=self.seed();meta=m.read_json(d/'metadata.json');meta['KPlugin']['Id']='other';m.atomic_json(d/'metadata.json',meta)
        with self.assertRaises(RuntimeError):self.manager.verify()
    def test_install_updates_in_place_and_has_backup(self):
        d=self.seed();before=m.tree_hashes(d);r=self.manager.install(d.name)
        self.assertEqual(m.tree_hashes(r/'before'),before)
        self.assertEqual(m.read_json(d/'metadata.json')['KPlugin']['Name'],'IRIX Classic')
        self.assertEqual([p.name for p in self.base.iterdir()], [d.name])
    def test_installer_preserves_config_without_activation(self):
        d=self.seed();self.cfg.data['theme']='Breeze';before=dict(self.cfg.data)
        self.manager.install(d.name);self.assertEqual(self.cfg.data,before)
    def test_activation_changes_only_two_keys(self):
        d=self.seed();self.cfg.data['theme']='Breeze';self.manager.install(d.name,True)
        self.assertEqual(self.cfg.get('theme'),d.name);self.assertEqual(self.cfg.get('ButtonsOnRight'),'IA')
    def test_restore_exact_original_files(self):
        d=self.seed();before=m.tree_hashes(d);self.manager.install(d.name);self.manager.restore()
        self.assertEqual(m.tree_hashes(d),before)
    def test_restore_preserves_other_theme_selected_afterward(self):
        d=self.seed();self.manager.install(d.name);self.cfg.data['theme']='another-theme';self.manager.restore()
        self.assertEqual(self.cfg.get('theme'),'another-theme')
    def test_restore_refuses_local_edits(self):
        d=self.seed();self.manager.install(d.name);(d/'local.txt').write_text('new')
        with self.assertRaises(RuntimeError):self.manager.restore()
        self.assertTrue((d/'local.txt').exists())
    def test_restore_refuses_tampered_backup(self):
        d=self.seed();r=self.manager.install(d.name);(r/'before/old-note.txt').write_text('tamper')
        with self.assertRaises(RuntimeError):self.manager.restore()
    def test_symlink_inside_dest_refused(self):
        d=self.seed();(d/'link').symlink_to(self.root)
        with self.assertRaises(RuntimeError):self.manager.verify()
    def test_symlink_parent_refused(self):
        real=self.root/'real';real.mkdir();link=self.root/'link';link.symlink_to(real,target_is_directory=True)
        with self.assertRaises(RuntimeError):m.no_links(link/'data/dest')
    def test_activation_failure_restores_config_and_files(self):
        d=self.seed();before=m.tree_hashes(d);self.cfg.data['theme']='Breeze';before_cfg=dict(self.cfg.data)
        self.cfg.fail=True
        with self.assertRaises(RuntimeError):self.manager.install(d.name,True)
        self.assertEqual(m.tree_hashes(d),before);self.assertEqual(self.cfg.data,before_cfg)
        self.assertFalse((self.state/'pending.json').exists())
    def test_second_update_restore_then_first_restore(self):
        d=self.seed();before=m.tree_hashes(d);self.manager.install(d.name);v1=m.tree_hashes(d)
        self.manager.install(d.name);self.manager.restore();self.assertEqual(m.tree_hashes(d),v1)
        self.manager.restore();self.assertEqual(m.tree_hashes(d),before)
    def test_first_install_restore_removes_new_theme(self):
        self.cfg.data={'ButtonsOnRight':'IA'};tid='irix_classic';self.manager.install(tid,True);self.manager.restore()
        self.assertFalse((self.base/tid).exists());self.assertIsNone(self.cfg.get('theme'));self.assertIsNone(self.cfg.get('library'))
    def test_appearance_migrated_without_global_changes(self):
        d=self.seed();ui=d/'contents/ui';(ui/'Settings.qml').unlink()
        (ui/'Appearance.qml').write_text('import QtQuick\nQtObject {\n property int pixelScale: 2\n property int titlePixels: 16\n property string titleFamily: "Noto Sans"\n property bool titleBold: false\n}\n')
        self.manager.install(d.name);t=(ui/'Settings.qml').read_text()
        self.assertIn('pixelScale: 2',t);self.assertIn('titlePixels: 16',t);self.assertIn('titleBold: false',t)
    def test_nonliteral_settings_refused_before_replacement(self):
        d=self.seed();file=d/'contents/ui/Settings.qml';file.write_text(file.read_text().replace('pixelScale: 1','pixelScale: arbitraryFunction()'))
        before=m.tree_hashes(d)
        with self.assertRaises(RuntimeError):self.manager.install(d.name)
        self.assertEqual(before,m.tree_hashes(d))
    def test_root_execution_rejected(self):
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaises(RuntimeError):self.manager.install('irix_classic')
    def test_pending_install_blocks_new_update(self):
        self.state.mkdir();m.atomic_json(self.state/'pending.json',{'backup':'placeholder'})
        with self.assertRaises(RuntimeError):self.manager.install('irix_classic')
    def test_recovery_after_interrupted_directory_swap(self):
        d=self.seed();before=m.tree_hashes(d);real_replace=m.os.replace
        def interrupted(a,b):
            if '.stage-' in str(a) and Path(b)==d:raise KeyboardInterrupt('simulated process interruption')
            return real_replace(a,b)
        with patch.object(m.os,'replace',side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):self.manager.install(d.name)
        self.assertFalse(d.exists());self.assertTrue((self.state/'pending.json').exists())
        self.manager.restore(recover=True);self.assertEqual(m.tree_hashes(d),before)
        self.assertFalse((self.state/'pending.json').exists())
    def test_malformed_receipt_paths_refused(self):
        d=self.seed();r=self.manager.install(d.name);data=m.read_json(r/'receipt.json');data['destination']='/etc';m.atomic_json(r/'receipt.json',data)
        with self.assertRaises(RuntimeError):self.manager.restore()
        self.assertTrue(d.exists())
    def test_backup_dir_private(self):
        d=self.seed();r=self.manager.install(d.name);self.assertEqual(r.stat().st_mode & 0o777,0o700)
    def test_manifest_detects_payload_change(self):
        altered=self.root/'altered';shutil.copytree(m.BUNDLE/'package',altered);(altered/'contents/ui/main.qml').write_text('broken')
        manager=m.Manager(self.base,self.cfg,self.state,altered)
        with self.assertRaises(RuntimeError):manager.verify()

if __name__=='__main__':unittest.main(verbosity=2)
