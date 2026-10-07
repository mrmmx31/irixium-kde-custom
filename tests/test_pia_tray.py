# SPDX-License-Identifier: GPL-3.0-or-later
import configparser
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from adapt_pia_tray import changes, wrapper, desktop_entry
from theme_transaction import Transaction, Failure, snapshot
from adapt_classic_launchers import restore_history

class PiaIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.data=self.root/'user';self.payload=self.root/'payload';self.payload.mkdir()
        for n in ('libirix-pia-tray.so','manifest.json'):(self.payload/n).write_bytes(b'test-only')
        self.source=self.root/'shared.desktop'
        self.source.write_text('[Desktop Entry]\nName=Private Internet Access\nExec=env XDG_SESSION_TYPE=X11 /opt/piavpn/bin/pia-client %u\nIcon=piavpn\nComment=Preserved\n')
    def tearDown(self):self.temp.cleanup()
    def transaction(self):
        allowed={c.path for c in changes(self.data,self.payload,self.source)}
        return Transaction(self.root/'state',lambda entries:self.fail('shared write'),lambda p,phase:p in allowed and phase==0)
    def test_roundtrip_only_user_files_and_preserves_desktop_fields(self):
        shared=snapshot(self.source);tx=self.transaction()
        with tx.locked():tx.install(changes(self.data,self.payload,self.source))
        p=self.data/'applications/piavpn.desktop';self.assertIn('Comment=Preserved',p.read_text())
        launcher=self.data/'irixium/integrations/pia/pia-client-sgi'
        self.assertEqual(launcher.stat().st_mode&0o777,0o755)
        self.assertEqual(snapshot(self.source),shared)
        with tx.locked():restore_history(tx)
        self.assertFalse(p.exists());self.assertFalse(launcher.exists())
        self.assertEqual(snapshot(self.source),shared)
    def test_custom_exec_is_preserved_by_refusing_replacement(self):
        p=self.data/'applications/piavpn.desktop';p.parent.mkdir(parents=True)
        p.write_text(self.source.read_text().replace('pia-client %u','pia-client --custom %u'))
        before=snapshot(p)
        with self.assertRaises(Failure):changes(self.data,self.payload,self.source)
        self.assertEqual(snapshot(p),before)
    def test_later_user_edits_block_restore(self):
        tx=self.transaction()
        with tx.locked():tx.install(changes(self.data,self.payload,self.source))
        p=self.data/'applications/piavpn.desktop';p.write_text(p.read_text()+'# user edit\n')
        with tx.locked(),self.assertRaises(Failure):restore_history(tx)
        self.assertIn('# user edit',p.read_text())
    def test_second_install_is_idempotent(self):
        tx=self.transaction()
        with tx.locked():tx.install(changes(self.data,self.payload,self.source))
        with tx.locked():self.assertIsNone(tx.install(changes(self.data,self.payload,self.source)))
    def test_wrapper_passes_uri_and_preload_without_shell_interpretation(self):
        app=self.root/'fake-client';app.write_text('#!/usr/bin/python3\nimport os,sys,json\nprint(json.dumps([sys.argv[1:],os.environ["LD_PRELOAD"]]))\n');app.chmod(0o755)
        launcher=self.root/'launcher with spaces';launcher.write_bytes(wrapper(Path('/tmp/nonexistent irix-test.so'),app));launcher.chmod(0o755)
        uri='piavpn://test?value=$(no-command)&quote="'
        result=subprocess.run([str(launcher),uri],env={**os.environ,'LD_PRELOAD':'/tmp/nonexistent prior-test.so'},capture_output=True,text=True,check=True)
        import json
        argv,preload=json.loads(result.stdout)
        self.assertEqual(argv,[uri]);self.assertEqual(preload,'/tmp/nonexistent irix-test.so:/tmp/nonexistent prior-test.so')
    def test_symlink_destination_is_rejected(self):
        p=self.data/'applications/piavpn.desktop';p.parent.mkdir(parents=True);p.symlink_to(self.source)
        with self.assertRaises(Failure):changes(self.data,self.payload,self.source)

if __name__=='__main__':unittest.main()
