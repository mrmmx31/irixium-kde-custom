# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic source-contract and transaction tests; NOT a native KDE session."""
from pathlib import Path
from unittest import mock
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import qtquick_scrollbar_fix as F
from theme_transaction import Transaction,Failure,replace_checked
# Minimal parser fixture. Not an installable replacement for KDE's ScrollBar.qml.
FIXTURE='''import QtQuick
import QtQuick.Templates as T
T.ScrollBar {
    id: controlRoot
    background: MouseArea {
        id: mouseArea
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        onExited: style.activeControl = "groove";
        onPressed: mouse => {
            if (style.activeControl === "down") { buttonTimer.running = true; }
            else if (style.activeControl === "up") { buttonTimer.running = true; }
        }
        onReleased: mouse => {
            style.activeControl = style.hitTest(mouse.x, mouse.y);
            buttonTimer.running = false;
        }
        onCanceled: buttonTimer.running = false;
        Item {
            id: style
            property string elementType: "scrollbar"
            sunken: controlRoot.pressed
        }
    }
}
'''.encode()
QMLDIR=b'module org.kde.desktop\nplugin org_kde_desktop\nprefer :/qt/qml/org/kde/desktop/\nScrollBar 1.0 ScrollBar.qml\nButton 1.0 Button.qml\n'

class QtQuickPressure(unittest.TestCase):
    def fixture(self,root):
        file=root/'ScrollBar.qml';file.write_bytes(FIXTURE)
        (root/'Button.qml').write_text('import QtQuick\nItem {}\n')
        (root/'qmldir').write_bytes(QMLDIR)
        return file
    def test_patch_updates_only_five_exact_anchors(self):
        new=F.patch_scrollbar(FIXTURE).decode();old=new
        for a,b in reversed(F.REPLACEMENTS):self.assertEqual(old.count(b),1);old=old.replace(b,a,1)
        self.assertEqual(old.encode(),FIXTURE)
    def test_patch_idempotent(self):
        new=F.patch_scrollbar(FIXTURE);self.assertEqual(F.patch_scrollbar(new),new)
    def test_edited_patch_refused(self):
        new=F.patch_scrollbar(FIXTURE).replace(b'irixPressedArrow: ""',b'irixPressedArrow: "up"')
        with self.assertRaises(Failure):F.patch_scrollbar(new)
    def test_upstream_fixed_or_ambiguous_anchor_refused(self):
        for data in (FIXTURE.replace(b'sunken: controlRoot.pressed',b'sunken: mouseArea.pressed'),FIXTURE+FIXTURE):
            with self.assertRaises(Failure):F.patch_scrollbar(data)
    def test_crlf_or_invalid_contract_refused(self):
        for data in (FIXTURE.replace(b'\n',b'\r\n'),b'Item {}',b'\0',b'x'*100001):
            with self.assertRaises(Failure):F.patch_scrollbar(data)
    def test_qrc_prefer_removed_only_with_complete_local_sources(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root)
            result=F.patch_qmldir(QMLDIR,root)
            self.assertNotIn(b'\nprefer ',result);self.assertIn(b'plugin org_kde_desktop',result)
            self.assertIn(F.PREFER_MARKER.encode(),result)
            self.assertEqual(F.patch_qmldir(result,root),result)
    def test_missing_source_blocks_qmldir_change(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'Button.qml').unlink()
            with self.assertRaises(Failure):F.patch_qmldir(QMLDIR,root)
    def test_external_qrc_prefer_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root)
            for data in (QMLDIR.replace(b':/qt/qml/org/kde/desktop/',b':/custom/'),QMLDIR.replace(b'org.kde.desktop',b'org.other')):
                with self.assertRaises(Failure):F.patch_qmldir(data,root)
    def test_symlink_source_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'Button.qml').unlink();(root/'Button.qml').symlink_to(root/'ScrollBar.qml')
            with self.assertRaises(Failure):F.patch_qmldir(QMLDIR,root)
    def test_no_prefer_file_remains_byte_identical(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);data=QMLDIR.replace(b'prefer :/qt/qml/org/kde/desktop/\n',b'')
            self.assertEqual(F.patch_qmldir(data,root),data)
    def test_system_allowlist_is_two_files_only(self):
        p=Path('/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/desktop')
        self.assertTrue(F.allowed(p/'ScrollBar.qml',1));self.assertTrue(F.allowed(p/'qmldir',1))
        for other in (p/'Button.qml',Path('/tmp/ScrollBar.qml'),Path('/usr/lib/qt5/qml/org/kde/desktop/ScrollBar.qml')):
            self.assertFalse(F.allowed(other,1))
        self.assertFalse(F.allowed(p/'ScrollBar.qml',0))
    def test_dry_run_does_not_write_or_authorize(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);file=self.fixture(root);writer=mock.Mock()
            tx=Transaction(root/'state',writer,lambda p,phase: p.parent==root and phase==1)
            tx.install(F.make_plan(file),True)
            writer.assert_not_called();self.assertEqual(file.read_bytes(),FIXTURE);self.assertFalse((root/'state').exists())
    def test_install_and_restore_in_temporary_files(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);file=self.fixture(root)
            def writer(entries):
                for e in entries:replace_checked(Path(e['path']),e['before'],e['after'])
            tx=Transaction(root/'state',writer,lambda p,phase:p.parent==root and phase==1)
            with tx.locked():tx.install(F.make_plan(file));tx.restore()
            self.assertEqual(file.read_bytes(),FIXTURE);self.assertEqual((root/'qmldir').read_bytes(),QMLDIR)
    def test_denied_authorization_preserves_source(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);file=self.fixture(root)
            def fail(entries):raise Failure('authorization denied for test')
            tx=Transaction(root/'state',fail,lambda p,phase:p.parent==root and phase==1)
            with tx.locked():
                with self.assertRaises(Failure):tx.install(F.make_plan(file))
            self.assertEqual(file.read_bytes(),FIXTURE);self.assertEqual((root/'qmldir').read_bytes(),QMLDIR)
    def test_native_press_binding_truth_table_in_js(self):
        # Execute the actual expression copied from the generated QML, not a second implementation.
        import shutil
        if not shutil.which('node'):self.skipTest('Node unavailable')
        text=F.patch_scrollbar(FIXTURE).decode()
        expression=text.split('            sunken: ',1)[1].split('\n        }',1)[0].strip()
        js='''const assert=require('node:assert/strict'); const Qt={LeftButton:1};
        function state(native,pressed,buttons,origin,active){
          const controlRoot={pressed:native}, mouseArea={pressed:pressed,pressedButtons:buttons,irixPressedArrow:origin};
          const activeControl=active; return Boolean(EXPRESSION);
        }
        assert.equal(state(false,true,1,'up','up'),true);
        assert.equal(state(false,true,1,'down','down'),true);
        assert.equal(state(false,false,0,'up','up'),false);
        assert.equal(state(false,true,4,'','handle'),false);
        assert.equal(state(false,true,1,'up','groove'),false);
        assert.equal(state(false,true,1,'up','down'),false);
        assert.equal(state(true,false,0,'','handle'),true);
        assert.equal(state(false,true,1,'','up'),false);
        '''.replace('EXPRESSION',expression)
        result=subprocess.run(['node','-e',js],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
if __name__=='__main__':unittest.main()
