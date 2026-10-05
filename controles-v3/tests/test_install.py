# SPDX-License-Identifier: GPL-2.0-or-later
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import controles as c

ART = b'<svg xmlns="http://www.w3.org/2000/svg"><g id="active-center"/><g id="inactive-center"/><g id="hover-center"/><g id="pressed-center"/></svg>'
CONF = b'# preserve comment\n[Windows]\nFocusPolicy=ClickToFocus\n\n[org.kde.kdecoration2]\nBorderSize=Normal\nButtonsOnLeft=M\nButtonsOnRight=HXA\ntheme=__aurorae__svg__Irixium\n[Other]\nKey=Value\n'

class ConfigTests(unittest.TestCase):
    def test_mapping(self):
        n = c.config(CONF, c.DESIRED)
        self.assertEqual(c.config(n)['ButtonsOnRight'], 'IA')
        self.assertEqual(c.config(n)['ButtonsOnLeft'], 'M')
    def test_only_order_changes(self):
        self.assertEqual(c.config(CONF, c.DESIRED), CONF.replace(b'ButtonsOnRight=HXA', b'ButtonsOnRight=IA'))
    def test_crlf(self):
        n = c.config(CONF.replace(b'\n', b'\r\n'), c.DESIRED)
        self.assertNotIn(b'\n', n.replace(b'\r\n', b''))
    def test_missing_keys(self):
        b = CONF.replace(b'ButtonsOnRight=HXA\n', b'')
        n = c.config(b, c.DESIRED)
        self.assertEqual(c.config(n)['ButtonsOnRight'], 'IA')
        self.assertEqual(c.config(n, {'ButtonsOnRight': None}), b)
    def test_duplicate_header_rejected(self):
        with self.assertRaises(c.Failure): c.config(CONF+b'[org.kde.kdecoration2]\n')
    def test_duplicate_key_rejected(self):
        with self.assertRaises(c.Failure): c.config(CONF.replace(b'ButtonsOnRight=HXA',b'ButtonsOnRight=IA\nButtonsOnRight=HXA'))
    def test_immutable_rejected(self):
        with self.assertRaises(c.Failure): c.config(CONF.replace(b'[org.kde.kdecoration2]',b'[org.kde.kdecoration2][$i]'))
    def test_key_flag_rejected(self):
        with self.assertRaises(c.Failure): c.config(CONF.replace(b'ButtonsOnRight=',b'ButtonsOnRight[$i]='))

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.theme = self.root / 'Irixium'; self.theme.mkdir()
        self.qml = self.root / 'MenuButton.qml'; self.qml.write_bytes((c.BUNDLE/'upstream/MenuButton.qml').read_bytes())
        self.kwin = self.root / 'kwinrc'; self.kwin.write_bytes(CONF)
        (self.theme/'close.svg').write_bytes(ART)
        (self.theme/'minimize.svg').write_bytes(b'original minimize')
        (self.theme/'Irixiumrc').write_bytes(b'untouched margins')
        (self.root/'AuroraeButtonGroup.qml').write_bytes(b'v2 separators')
        self.asset = self.root/'applications.png'; self.asset.write_bytes(b'fixture asset')
        self.state = self.root/'state'
        self.inst = c.Installer(self.qml,self.theme,self.kwin,self.state,shutil.copyfile,asset=self.asset)
        self.addCleanup(patch.stopall)
        patch.object(c,'EXPECTED_CLOSE_BLOB',c.git_blob(ART)).start()
        self.out = contextlib.redirect_stdout(io.StringIO()); self.out.__enter__()
        self.addCleanup(self.out.__exit__,None,None,None)
    def apply(self): return self.inst.install()
    def test_dry_run_is_read_only(self):
        before = {str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.inst.install(dry=True)
        self.assertFalse(self.state.exists())
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_install_exact_artwork_and_menu(self):
        self.apply()
        self.assertEqual((self.theme/'minimize.svg').read_bytes(),ART)
        self.assertEqual(self.qml.read_bytes(),(c.BUNDLE/'MenuButton.qml').read_bytes())
        self.assertEqual(c.config(self.kwin.read_bytes())['ButtonsOnRight'],'IA')
    def test_preserves_separators_rc_and_close(self):
        self.apply()
        self.assertEqual((self.root/'AuroraeButtonGroup.qml').read_bytes(),b'v2 separators')
        self.assertEqual((self.theme/'Irixiumrc').read_bytes(),b'untouched margins')
        self.assertEqual((self.theme/'close.svg').read_bytes(),ART)
    def test_idempotent(self):
        self.apply(); self.assertIsNone(self.apply())
        self.assertEqual(len(list((self.state/'backups').iterdir())),1)
    def test_accepts_older_menu(self):
        self.qml.write_bytes((c.BUNDLE/'upstream/MenuButton-6f12fdc.qml').read_bytes()); self.apply()
    def test_unknown_menu_rejected(self):
        self.qml.write_text('custom')
        with self.assertRaises(c.Failure): self.apply()
        self.assertFalse(self.state.exists())
    def test_unknown_square_rejected(self):
        (self.theme/'close.svg').write_bytes(ART+b' ')
        with self.assertRaises(c.Failure): self.apply()
    def test_invalid_svg_states_rejected(self):
        a=b'<svg/>'; (self.theme/'close.svg').write_bytes(a)
        with patch.object(c,'EXPECTED_CLOSE_BLOB',c.git_blob(a)):
            with self.assertRaises(c.Failure): self.apply()
    def test_other_theme_rejected(self):
        self.kwin.write_bytes(CONF.replace(b'__aurorae__svg__Irixium',b'Breeze'))
        with self.assertRaises(c.Failure): self.apply()
    def test_symlink_rejected(self):
        m=self.theme/'minimize.svg'; m.unlink(); m.symlink_to(self.theme/'close.svg')
        with self.assertRaises(c.Failure): self.apply()
    def test_missing_asset_rejected(self):
        self.asset.unlink()
        with self.assertRaises(c.Failure): self.apply()
    def test_admin_denied_no_changes(self):
        orig=self.qml.read_bytes()
        self.inst.copy_system=lambda *args: (_ for _ in ()).throw(c.Failure('cancel'))
        with self.assertRaises(c.Failure): self.apply()
        self.assertEqual(self.qml.read_bytes(),orig); self.assertEqual(self.kwin.read_bytes(),CONF)
    def test_partial_admin_write_rollback(self):
        orig=self.qml.read_bytes(); calls=[]
        def copier(src,dst):
            calls.append(1)
            if len(calls)==1:
                dst.write_bytes(b'partial'); raise c.Failure('simulated disk error')
            shutil.copyfile(src,dst)
        self.inst.copy_system=copier
        with self.assertRaises(c.Failure): self.apply()
        self.assertEqual(self.qml.read_bytes(),orig)
        self.assertEqual((self.theme/'minimize.svg').read_bytes(),b'original minimize')
    def test_restore(self):
        orig=self.qml.read_bytes(); self.apply(); self.inst.restore()
        self.assertEqual(self.qml.read_bytes(),orig)
        self.assertEqual(self.kwin.read_bytes(),CONF)
        self.assertEqual((self.theme/'minimize.svg').read_bytes(),b'original minimize')
    def test_restore_preserves_unrelated_new_settings(self):
        self.apply()
        self.kwin.write_bytes(self.kwin.read_bytes().replace(b'Key=Value',b'Key=Changed'))
        self.inst.restore()
        self.assertIn(b'Key=Changed',self.kwin.read_bytes())
        self.assertEqual(c.config(self.kwin.read_bytes())['ButtonsOnRight'],'HXA')
    def test_restore_refuses_new_layout(self):
        self.apply(); self.kwin.write_bytes(c.config(self.kwin.read_bytes(),{'ButtonsOnRight':'IAX'}))
        with self.assertRaises(c.Failure): self.inst.restore()
    def test_restore_refuses_changed_menu(self):
        self.apply(); self.qml.write_bytes(self.qml.read_bytes()+b'// other edit')
        with self.assertRaises(c.Failure): self.inst.restore()
    def test_restore_refuses_corrupted_backup(self):
        b=self.apply(); (b/'menu.before').write_bytes(b'corrupt')
        with self.assertRaises(c.Failure): self.inst.restore()
    def test_restore_admin_denied_keeps_v3(self):
        self.apply()
        self.inst.copy_system=lambda *args: (_ for _ in ()).throw(c.Failure('cancel'))
        with self.assertRaises(c.Failure): self.inst.restore()
        self.assertEqual(self.qml.read_bytes(),(c.BUNDLE/'MenuButton.qml').read_bytes())
        self.assertEqual(c.config(self.kwin.read_bytes())['ButtonsOnRight'],'IA')
    def test_restore_dry_run(self):
        self.apply(); self.inst.restore(dry=True)
        self.assertEqual(c.config(self.kwin.read_bytes())['ButtonsOnRight'],'IA')
    def test_scope(self):
        b=self.apply(); m=json.loads((b/'manifest.json').read_text())
        self.assertEqual(set(m['paths']),{'menu','minimize','kwinrc'})
    def test_origin_blob_integrity(self):
        self.assertEqual(c.git_blob((c.BUNDLE/'upstream/MenuButton.qml').read_bytes()),'bcf07652fa4a3e45f5d61a42a68ee946fe85b17b')
        self.assertEqual(c.git_blob((c.BUNDLE/'upstream/MenuButton-6f12fdc.qml').read_bytes()),'5102380b3ea6fbd48bd7913605931938017d0b51')

class RepoPlanTests(unittest.TestCase):
    def test_plan_preserves_other_script_actions(self):
        spec=importlib.util.spec_from_file_location('integrate',c.BUNDLE/'integrar-repositorio.py')
        m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); (r/'aurorae/Irixium').mkdir(parents=True)
            (r/'MenuButton.qml').write_bytes((c.BUNDLE/'upstream/MenuButton.qml').read_bytes())
            (r/'aurorae/Irixium/close.svg').write_bytes(ART)
            (r/'aurorae/Irixium/minimize.svg').write_bytes(b'old')
            (r/'kwin-decoration.conf').write_bytes(CONF)
            s=b'#!/bin/sh\nkwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight HXA\necho unchanged\n'
            (r/'update-irixium.sh').write_bytes(s)
            with patch.object(m,'EXPECTED_CLOSE_BLOB',c.git_blob(ART)):
                old,new=m.plan(r)
            self.assertEqual(new['update-irixium.sh'],s.replace(b'HXA',b'IA'))
            self.assertEqual(new['aurorae/Irixium/minimize.svg'],ART)
            self.assertEqual(set(new),set(m.FILES))
            self.assertEqual((r/'update-irixium.sh').read_bytes(),s)  # plan is read-only

if __name__=='__main__': unittest.main(verbosity=2)
