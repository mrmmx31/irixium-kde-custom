# SPDX-License-Identifier: GPL-3.0-or-later
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from adapt_classic_launchers import plan, mime_changes, restore_history
from theme_transaction import Transaction, snapshot, Failure


class LauncherOverrides(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.data=self.root/'data';self.desktop=self.root/'Desktop';self.shared=self.root/'shared'
        for p in (self.data/'applications',self.desktop,self.shared,self.data/'icons/IrixClassic-SGI/scalable/apps'):
            p.mkdir(parents=True)
        for name in ('applications-development','android-studio','idea','texdoctk','snxgui'):
            (self.data/'icons/IrixClassic-SGI/scalable/apps'/(name+'.svg')).write_text('<svg/>')
    def tearDown(self):self.tmp.cleanup()
    def entry(self,p,icon):
        p.write_text('[Desktop Entry]\nName=IDE\nType=Application\nIcon='+icon+'\nExec=ide --flag %u\nStartupWMClass=IDE\n');p.chmod(0o600)
    def test_shared_entry_is_overridden_only_in_user_data_and_restore_removes_it(self):
        source=self.shared/'android-studio_android-studio.desktop';self.entry(source,'/snap/studio.png');before=snapshot(source)
        changes=plan(self.data,self.desktop,[self.data/'applications',self.shared])
        self.assertEqual(len(changes),1);self.assertEqual(changes[0].path,self.data/'applications'/source.name)
        tx=Transaction(self.root/'state',lambda _:self.fail('shared write'),lambda p,phase:phase==0 and p==changes[0].path)
        tx.install(changes)
        self.assertIn('Exec=ide --flag %u',changes[0].path.read_text());self.assertIn('Icon=android-studio',changes[0].path.read_text())
        self.assertEqual(snapshot(source),before);tx.restore();self.assertFalse(changes[0].path.exists())
    def test_existing_user_entry_shadows_system_and_modes_restore(self):
        user=self.data/'applications/android-studio_android-studio.desktop';self.entry(user,'/custom.png');before=snapshot(user)
        self.entry(self.shared/user.name,'/system.png')
        changes=plan(self.data,self.desktop,[self.data/'applications',self.shared]);self.assertEqual(len(changes),1)
        tx=Transaction(self.root/'state',lambda _:self.fail('shared write'),lambda p,phase:p==user and phase==0)
        tx.install(changes);tx.restore();self.assertEqual(snapshot(user),before)
    def test_named_icons_and_unmapped_apps_are_preserved(self):
        self.entry(self.shared/'android-studio_android-studio.desktop','my-personal-icon')
        self.entry(self.shared/'unmapped.desktop','/custom/icon.png')
        self.assertEqual(plan(self.data,self.desktop,[self.shared]),[])
    def test_desktop_shortcut_is_backed_up_and_later_edits_block_restore(self):
        p=self.desktop/'Intellij Idea.desktop';self.entry(p,'/idea.png')
        changes=plan(self.data,self.desktop,[])
        tx=Transaction(self.root/'state',lambda _:self.fail('shared write'),lambda path,phase:path==p and phase==0)
        tx.install(changes);p.write_text(p.read_text()+'Comment=personal edit\n')
        with self.assertRaises(Failure):tx.restore()

    def test_absolute_mime_icon_is_repaired_without_changing_globs(self):
        p=self.data/'mime/packages/application-x-shellscript.xml';p.parent.mkdir(parents=True)
        p.write_text('<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info"><mime-type type="application/x-shellscript"><icon name="/old/idea.png"/><glob pattern="*.sh"/></mime-type></mime-info>')
        before=snapshot(p);changes=mime_changes(self.data)
        tx=Transaction(self.root/'state',lambda _:self.fail('shared write'),lambda path,phase:path==p and phase==0)
        tx.install(changes);self.assertIn('name="text-x-script"',p.read_text());self.assertIn('pattern="*.sh"',p.read_text())
        self.assertEqual(mime_changes(self.data),[]);tx.restore();self.assertEqual(snapshot(p),before)

    def test_empty_tex_icon_is_filled_without_changing_command(self):
        p=self.shared/'texdoctk.desktop';self.entry(p,'')
        changes=plan(self.data,self.desktop,[self.shared])
        self.assertEqual(len(changes),1)
        self.assertIn('Icon=texdoctk',changes[0].data.decode())
        self.assertIn('Exec=ide --flag %u',changes[0].data.decode())

    def test_broken_snx_duplicates_are_repaired_only_in_override(self):
        p=self.shared/'snxgui.desktop';self.entry(p,'/missing/snx.png')
        p.write_bytes(p.read_bytes()*3);before=snapshot(p)
        changes=plan(self.data,self.desktop,[self.shared])
        self.assertEqual(changes[0].data.count(b'[Desktop Entry]'),1)
        self.assertIn(b'Icon=snxgui',changes[0].data)
        self.assertIn(b'Exec=ide --flag %u',changes[0].data)
        self.assertEqual(snapshot(p),before)

    def test_conflicting_snx_blocks_are_refused(self):
        p=self.shared/'snxgui.desktop';self.entry(p,'/missing/snx.png')
        p.write_bytes(p.read_bytes()+p.read_bytes().replace(b'Exec=ide',b'Exec=other'))
        with self.assertRaises(Failure):plan(self.data,self.desktop,[self.shared])

    def test_idea_generic_icon_migration_preserves_personal_alternative(self):
        p=self.desktop/'Intellij Idea.desktop';self.entry(p,'applications-development')
        self.assertIn(b'Icon=idea',plan(self.data,self.desktop,[])[0].data)
        self.entry(p,'my-own-idea-icon');self.assertEqual(plan(self.data,self.desktop,[]),[])

    def test_all_adaptation_layers_restore_in_reverse_order(self):
        from theme_transaction import Change
        a=self.data/'first';b=self.data/'second';a.write_bytes(b'original');before=snapshot(a)
        tx=Transaction(self.root/'state',lambda _:self.fail('shared write'),lambda path,phase:path in (a,b) and phase==0)
        tx.install([Change(a,b'changed')]);tx.install([Change(b,b'new')])
        restore_history(tx);self.assertEqual(snapshot(a),before);self.assertFalse(b.exists())


if __name__=='__main__':unittest.main()
