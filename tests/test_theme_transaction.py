# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import base64
import hashlib
import json
import os
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from theme_transaction import Change, Failure, Transaction, image, snapshot, replace_checked, edit_ini
from system_theme_writer import apply as apply_system, allowed as allowed_system

class Transactions(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.state=self.root/'state';self.calls=[]
        self.allowed=lambda path,phase:self.root in path.parents and self.state not in path.parents
        self.system=lambda entries:apply_system(entries,validator=lambda path:self.allowed(path,1))
        self.tx=Transaction(self.state,self.system,self.allowed)
    def tearDown(self):self.temp.cleanup()
    def changes(self):
        self.paths=[self.root/'theme/rc',self.root/'system/group.qml',self.root/'system/menu.qml',self.root/'config/kwinrc']
        changes=[]
        for i,p in enumerate(self.paths):
            p.parent.mkdir(exist_ok=True);p.write_bytes(('before'+str(i)).encode());p.chmod(0o600)
            changes.append(Change(p,('after'+str(i)).encode(),(0,1,1,2)[i],0o644))
        self.before=[snapshot(p) for p in self.paths]
        return changes
    def assertBefore(self):
        self.assertEqual([snapshot(p) for p in self.paths],self.before)
    def test_dry_run_has_no_state_or_file_writes(self):
        c=self.changes();self.tx.install(c,True);self.assertBefore();self.assertFalse(self.state.exists())
    def test_install_then_restore_including_modes(self):
        self.tx.install(self.changes());self.tx.restore();self.assertBefore()
    def test_new_files_removed_by_restore(self):
        p=self.root/'new/theme.svg';self.tx.install([Change(p,b'svg')]);self.tx.restore();self.assertFalse(p.exists())
    def test_no_change_does_not_create_receipt(self):
        p=self.root/'file';p.write_bytes(b'old');p.chmod(0o644)
        self.assertIsNone(self.tx.install([Change(p,b'old')]))
        self.assertFalse(self.state.exists())
    def test_system_denial_restores_user_theme(self):
        changes=self.changes()
        def denied(items):raise Failure('authorization cancelled')
        self.tx.system_writer=denied
        with self.assertRaises(Failure):self.tx.install(changes)
        self.assertBefore();self.assertEqual(self.tx.latest()[1]['status'],'restored')
    def test_system_batch_partial_failure_rolls_itself_back(self):
        changes=self.changes();done=False
        def writer(path,before,after):
            nonlocal done
            if path==self.paths[2] and not done:
                done=True;raise OSError('disk full')
            replace_checked(path,before,after)
        self.tx.system_writer=lambda entries:apply_system(entries,writer=writer,validator=lambda p:True)
        with self.assertRaises(Failure):self.tx.install(changes)
        self.assertBefore()
    def test_activation_failure_restores_system_and_theme(self):
        changes=self.changes();once=True
        def writer(path,before,after):
            nonlocal once
            if path==self.paths[3] and once:once=False;raise OSError('config failure')
            replace_checked(path,before,after)
        self.tx.writer=writer
        with self.assertRaises(Failure):self.tx.install(changes)
        self.assertBefore()
    def test_failure_after_activation_write_also_rolls_back(self):
        changes=self.changes();once=True
        def writer(path,before,after):
            nonlocal once
            replace_checked(path,before,after)
            if path==self.paths[3] and once:once=False;raise OSError('after rename')
        self.tx.writer=writer
        with self.assertRaises(Failure):self.tx.install(changes)
        self.assertBefore()
    def test_keyboard_interrupt_restores(self):
        changes=self.changes();once=True
        def writer(path,before,after):
            nonlocal once
            if path==self.paths[3] and once:once=False;raise KeyboardInterrupt()
            replace_checked(path,before,after)
        self.tx.writer=writer
        with self.assertRaises(Failure):self.tx.install(changes)
        self.assertBefore()
    def test_rollback_denied_blocks_new_install_until_recovery(self):
        changes=self.changes();count=0;once=True
        def system(entries):
            nonlocal count
            count+=1
            if count==2:raise Failure('rollback denied')
            self.system(entries)
        def writer(path,before,after):
            nonlocal once
            if path==self.paths[3] and once:once=False;raise OSError('config failure')
            replace_checked(path,before,after)
        self.tx.system_writer=system;self.tx.writer=writer
        with self.assertRaises(Failure):self.tx.install(changes)
        self.assertEqual(self.tx.latest()[1]['status'],'recovery_needed')
        with self.assertRaises(Failure):self.tx.plan(changes)
        self.tx.restore(recovery=True);self.assertBefore()
    def test_prepared_journal_recovery_after_simulated_hard_crash(self):
        changes=self.changes();self.tx.install(changes)
        file,rec=self.tx.latest();rec['status']='prepared';self.tx.save(file,rec)
        # Simulate only some files having been written at the time of SIGKILL.
        replace_checked(self.paths[3],snapshot(self.paths[3]),self.before[3])
        with self.assertRaises(Failure):self.tx.restore()
        self.tx.restore(recovery=True);self.assertBefore()
    def test_unrecognized_later_edit_blocks_all_rollback_writes(self):
        self.tx.install(self.changes());self.paths[0].write_bytes(b'manual edit')
        before=[snapshot(p) for p in self.paths]
        with self.assertRaises(Failure):self.tx.restore()
        self.assertEqual(before,[snapshot(p) for p in self.paths])
    def test_tampered_receipt_hash_refused(self):
        self.tx.install(self.changes());file,rec=self.tx.latest()
        rec['entries'][0]['before']['base64']=base64.b64encode(b'fake').decode();self.tx.save(file,rec)
        with self.assertRaises(Failure):self.tx.restore()
    def test_tampered_receipt_path_refused(self):
        self.tx.install(self.changes());file,rec=self.tx.latest()
        rec['entries'][0]['path']='/etc/passwd';self.tx.save(file,rec)
        with self.assertRaises(Failure):self.tx.restore()
    def test_symlink_target_refused(self):
        a=self.root/'a';a.write_bytes(b'a');b=self.root/'b';b.symlink_to(a)
        with self.assertRaises(Failure):self.tx.install([Change(b,b'b')])
    def test_symlink_parent_refused(self):
        actual=self.root/'real';actual.mkdir();alias=self.root/'alias';alias.symlink_to(actual)
        with self.assertRaises(Failure):self.tx.install([Change(alias/'c',b'c')])
    def test_source_plan_detects_concurrent_edit(self):
        p=self.root/'a';p.write_bytes(b'a');old=snapshot(p);p.write_bytes(b'other')
        with self.assertRaises(Failure):self.tx.install([Change(p,b'b',expected=old)])
    def test_duplicate_paths_refused(self):
        p=self.root/'a'
        with self.assertRaises(Failure):self.tx.install([Change(p,b'a'),Change(p,b'b')])
    def test_phase_order_and_receipt_precede_writes(self):
        changes=self.changes();events=[]
        def writer(path,before,after):
            self.assertEqual(self.tx.latest()[1]['status'],'prepared')
            events.append(str(path));replace_checked(path,before,after)
        def system(entries):
            for e in entries:writer(Path(e['path']),e['before'],e['after'])
        self.tx.writer=writer;self.tx.system_writer=system;self.tx.install(changes)
        self.assertEqual(events,[str(p) for p in self.paths])
    def test_lock_exclusion(self):
        with self.tx.locked():
            with self.assertRaises(Failure):
                with self.tx.locked():pass
    def test_root_helper_allowlist(self):
        for path in ['/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/kwin/decoration/MenuButton.qml',
                     '/usr/share/kwin/aurorae/AuroraeButtonGroup.qml','/usr/share/kwin/aurorae/Irixium/applications.png']:
            self.assertTrue(allowed_system(Path(path)))
        for path in ['/etc/passwd','/tmp/AuroraeButtonGroup.qml','/usr/share/kwin/aurorae/../../x',
                     '/usr/lib/x86_64-linux-gnu/qt5/qml/org/kde/kwin/decoration/MenuButton.qml']:
            self.assertFalse(allowed_system(Path(path)))
    def test_root_helper_validates_entire_batch_before_first_write(self):
        c=self.changes();entries=self.tx.plan(c);system=[e for e in entries if e['phase']==1]
        system[1]['before']['sha256']='bad'
        with self.assertRaises(Failure):apply_system(system,validator=lambda p:True)
        self.assertBefore()

class IniEdits(unittest.TestCase):
    def test_preserves_other_groups_comments_and_app_exceptions(self):
        src=b'# Keep\n[General]\ntheme=Irixium\n[Applications]\nOther=app\n'
        out=edit_ini(src,'General',{'theme':'IrixClassic'})
        self.assertEqual(out,src.replace(b'theme=Irixium',b'theme=IrixClassic'))
    def test_new_file(self):self.assertIn(b'[General]\ntheme=X\n',edit_ini(b'','General',{'theme':'X'}))
    def test_duplicates_refused(self):
        with self.assertRaises(Failure):edit_ini(b'[General]\ntheme=X\ntheme=Y\n','General',{'theme':'Z'})
    def test_immutable_key_refused(self):
        with self.assertRaises(Failure):edit_ini(b'[General]\ntheme[$i]=X\n','General',{'theme':'Z'})
    def test_immutable_group_refused(self):
        with self.assertRaises(Failure):edit_ini(b'[General][$i]\ntheme=X\n','General',{'theme':'Z'})
    def test_crlf_and_missing_newline(self):
        self.assertEqual(edit_ini(b'[General]\r\ntheme=X','General',{'theme':'Z'}),b'[General]\r\ntheme=Z\r\n')
    def test_other_group_unmodified_when_adding(self):
        src=b'[Other]\nfoo=1\n';out=edit_ini(src,'General',{'theme':'X'})
        self.assertTrue(out.startswith(src));self.assertEqual(out.count(b'foo=1'),1)

if __name__=='__main__':unittest.main()
