# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from adapt_kate_icons import changes
from theme_transaction import Transaction,Failure,snapshot
from adapt_classic_launchers import restore_history
class KateIcons(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.data=self.root/'user';self.payload=self.root/'payload';self.payload.mkdir()
        for n in ('libirix-kate-icons.so','manifest.json'):(self.payload/n).write_bytes(b'test')
        self.source=self.root/'shared.desktop';self.source.write_text('[Desktop Entry]\nName=Kate\nExec=kate -b %U\nIcon=kate\nComment=Preserve\n')
    def tearDown(self):self.temp.cleanup()
    def test_install_idempotence_restore_and_shared_preservation(self):
        before=snapshot(self.source);plan=changes(self.data,self.payload,self.source);allowed={c.path for c in plan};tx=Transaction(self.root/'state',lambda e:self.fail('shared write'),lambda p,phase:p in allowed and phase==0)
        with tx.locked():tx.install(plan)
        text=(self.data/'applications/org.kde.kate.desktop').read_text();self.assertIn('Comment=Preserve',text);self.assertIn('Icon=kate',text);self.assertIn('kate-sgi" -b %U',text)
        with tx.locked():self.assertIsNone(tx.install(changes(self.data,self.payload,self.source)))
        with tx.locked():restore_history(tx)
        self.assertFalse((self.data/'applications/org.kde.kate.desktop').exists());self.assertEqual(snapshot(self.source),before)
    def test_custom_command_is_not_overwritten(self):
        dest=self.data/'applications/org.kde.kate.desktop';dest.parent.mkdir(parents=True);dest.write_text(self.source.read_text().replace('kate -b','kate --custom -b'));before=snapshot(dest)
        with self.assertRaises(Failure):changes(self.data,self.payload,self.source)
        self.assertEqual(snapshot(dest),before)
    def test_symlink_destination_is_not_followed(self):
        dest=self.data/'applications/org.kde.kate.desktop';dest.parent.mkdir(parents=True);dest.symlink_to(self.source)
        with self.assertRaises(Failure):changes(self.data,self.payload,self.source)
if __name__=='__main__':unittest.main()
