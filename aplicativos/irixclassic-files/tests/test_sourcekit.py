# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Source-transform and release-safety tests. NOT a replacement for C++ builds."""
import importlib.util, json, os, sys, tempfile, unittest, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import prepare_source as P
import runtime_install as R

VIEW = r'''
const char ViewPropertiesFileName[] = ".directory";
ViewPropertySettings *ViewProperties::loadProperties(const QString &folderPath) const
{
    const char *s = "brace } ignored"; /* { ignored } */
    if (test) { return whatever; }
    return other;
}
ViewProperties::ViewProperties(const QUrl &url) {
    const bool useGlobalViewProps = false;
    m_node = loadProperties(m_filePath);
}
void ViewProperties::save()
{
    auto f = []() { return 5; };
    metaData.setAttribute(metaDataKey, "changed");
}
'''
XML='''<gui name="dolphin" version="43"><MenuBar>
<Menu name="file"><Action name="deletefile"/></Menu>
<Menu name="edit"><Action name="edit_copy"/><Action name="edit_paste"/></Menu>
<Menu name="view"><Action name="sort"/><Action name="show_preview"/></Menu>
<Menu name="tools"><Action name="open_terminal"/></Menu>
</MenuBar></gui>'''
BOOKMARK='''    QString bookmarksFile = QStandardPaths::locate(QStandardPaths::GenericDataLocation, QStringLiteral("kfile/bookmarks.xml"));
    if (bookmarksFile.isEmpty()) { bookmarksFile = "old"; }
    m_bookmarkManager = std::make_unique<KBookmarkManager>(bookmarksFile);
'''
def fixture(root):
    for d in ('debian/patches','.pc','src/views','src/settings'): (root/d).mkdir(parents=True,exist_ok=True)
    (root/'debian/changelog').write_text('dolphin ('+P.DEBIAN_VERSION+') trixie; urgency=medium\n')
    (root/'debian/patches/series').write_text('debian-fix.patch\n');(root/'.pc/applied-patches').write_text('debian-fix.patch\n')
    (root/'CMakeLists.txt').write_text('VERSION_MAJOR "25"\nVERSION_MINOR "04"\nVERSION_MICRO "3"\nadd_subdirectory(src)\n')
    (root/'src/CMakeLists.txt').write_text('add_library(dolphinstatic STATIC)\n')
    (root/'src/dolphinmainwindow.cpp').write_text('setComponentName(QStringLiteral("dolphin"), QGuiApplication::applicationDisplayName());\nsetObjectName(QStringLiteral("Dolphin#"));\n')
    (root/'src/settings/a.kcfg').write_text('<kcfgfile name="dolphinrc"/>')
    (root/'src/dolphin.qrc').write_text('<RCC><qresource prefix="/kxmlgui5/dolphin"><file>dolphinui.rc</file></qresource></RCC>')
    (root/'src/dolphinui.rc').write_text(XML)
    (root/'src/views/viewproperties.cpp').write_text(VIEW)
    (root/'src/dolphinbookmarkhandler.cpp').write_text(BOOKMARK)
    (root/'src/global.cpp').write_text('#include <KService>\nQString command = QStringLiteral("dolphin --new-window");\nconst QString pattern = QStringLiteral("org.kde.dolphin-");\n')

class TransformTests(unittest.TestCase):
    def test_unique_anchor(self):self.assertEqual(P.replace_one('a b','a','c'),'c b')
    def test_missing_anchor(self):
        with self.assertRaises(P.Failure):P.replace_one('a','b','c')
    def test_duplicate_anchor(self):
        with self.assertRaises(P.Failure):P.replace_one('aa','a','c')
    def test_nested_braces(self):self.assertIn('return safe;',P.replace_body(VIEW,'void ViewProperties::save()','return safe;'))
    def test_strings_comments(self):self.assertNotIn('brace',P.replace_body(VIEW,'ViewPropertySettings *ViewProperties::loadProperties(const QString &folderPath) const','return nullptr;'))
    def test_unterminated(self):
        with self.assertRaises(P.Failure):P.replace_body('void a() { // }','void a()','done;')
    def test_view_storage(self):
        s=P.transform_viewproperties(VIEW);self.assertIn('view.properties',s);self.assertIn('destinationDir(privateKey)',s);self.assertNotIn('metaData.setAttribute',s)
    def test_no_old_view_filename(self):self.assertNotIn('= ".directory"',P.transform_viewproperties(VIEW))
    def test_menu_actions_preserved(self):
        old=ET.fromstring(XML);new=ET.fromstring(P.transform_xml(XML));self.assertCountEqual([a.get('name') for a in old.iter('Action')],[a.get('name') for a in new.iter('Action')])
    def test_menu_identity(self):self.assertEqual(ET.fromstring(P.transform_xml(XML)).get('name'),'irixclassic-files')
    def test_sort_on_menu_bar(self):self.assertIsNotNone(ET.fromstring(P.transform_xml(XML)).find("MenuBar/Action[@name='sort']"))
    def test_wrong_xml(self):
        with self.assertRaises(P.Failure):P.transform_xml(XML.replace('name="dolphin"','name="other"'))
    def test_prepare_on_structural_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'orig';fixture(source);target=Path(d)/'prepared'
            before=(source/'src/global.cpp').read_bytes();record=P.prepare(source,target)
            self.assertEqual((source/'src/global.cpp').read_bytes(),before)
            self.assertTrue((target/'src/irixclassic/main.cpp').is_file())
            self.assertIn('irixclassic-filesrc',(target/'src/settings/a.kcfg').read_text())
            self.assertNotIn('kfile/bookmarks.xml"',(target/'src/dolphinbookmarkhandler.cpp').read_text())
            self.assertTrue(record['changes'])
    def test_source_without_debian(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(P.Failure):P.prepare(Path(d),Path(d)/'output')
    def test_reject_unapplied_patch(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'orig';fixture(source);(source/'.pc/applied-patches').unlink()
            with self.assertRaises(P.Failure):P.prepare(source,Path(d)/'prepared')
    def test_reject_wrong_version(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'orig';fixture(source);(source/'debian/changelog').write_text('dolphin (other) trixie; urgency=medium')
            with self.assertRaises(P.Failure):P.prepare(source,Path(d)/'prepared')
    def test_reject_existing_destination(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'orig';fixture(source);target=Path(d)/'exists';target.mkdir()
            with self.assertRaises(P.Failure):P.prepare(source,target)
    def test_reject_source_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'orig';fixture(source);(source/'src/link').symlink_to('/etc/passwd')
            with self.assertRaises(P.Failure):P.prepare(source,Path(d)/'prepared')
    def test_no_partial_tree(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'orig';fixture(source);(source/'src/dolphin.qrc').write_text('wrong')
            with self.assertRaises(P.Failure):P.prepare(source,Path(d)/'prepared')
            self.assertFalse((Path(d)/'prepared').exists())

class ArchitectureTests(unittest.TestCase):
    def text(self,path):return (ROOT/path).read_text()
    def test_no_shell_file_operations(self):
        for p in (ROOT/'src').glob('*.cpp'):
            for forbidden in ('std::system(','system("','/bin/sh','rm -rf','cp -r','mv -f'):self.assertNotIn(forbidden,p.read_text())
    def test_native_window(self):self.assertIn('new DolphinMainWindow',self.text('src/main.cpp'))
    def test_native_backend(self):self.assertIn('dolphinstatic',self.text('src/CMakeLists.txt'))
    def test_no_filemanager_service_registration(self):
        s=self.text('src/main.cpp');self.assertNotIn('registerService(',s);self.assertNotIn('DBusInterface interface;',s)
    def test_private_libraries(self):self.assertIn('OUTPUT_NAME irixclassic-files-private',self.text('src/CMakeLists.txt'))
    def test_no_upstream_install(self):self.assertNotIn("'--install'",self.text('tools/build.py'))
    def test_bounded_preview(self):
        s=self.text('src/previewworker.cpp');self.assertIn('O_NONBLOCK',s);self.assertIn('S_ISREG',s);self.assertIn('16*1024*1024',s);self.assertIn("40'000'000",s);self.assertIn('setAllocationLimit(128)',s)
    def test_plain_text(self):self.assertIn('setPlainText(',self.text('src/preview.cpp'));self.assertNotIn('setHtml(',self.text('src/preview.cpp'))
    def test_remote_preview_not_downloaded(self):self.assertIn('if (!url.isLocalFile())',self.text('src/preview.cpp'));self.assertNotIn('QNetwork',self.text('src/preview.cpp'))
    def test_kill_timeout(self):self.assertIn('m_timeout->start(3000)',self.text('src/preview.cpp'));self.assertIn('old->kill()',self.text('src/preview.cpp'))
    def test_stale_preview_guard(self):self.assertIn('ticket != m_request',self.text('src/preview.cpp'))
    def test_shelf_never_filesystem_delete(self):
        s=self.text('src/shelf.cpp');self.assertNotIn('QFile::remove',s);self.assertNotIn('KIO::del',s);self.assertIn('ShortcutOverride',s);self.assertIn('setDropAction',s)
    def test_no_sounds_integrated_yet(self):self.assertNotIn('KNotification::',self.text('src/classicshell.cpp'))
    def test_tests_gate_packages(self):
        s=self.text('tools/build.py');self.assertLess(s.index("'ctest'"),s.index("binary_root=work"));self.assertIn('--no-tests=error',s)
    def test_future_source_code_in_archive(self):self.assertIn("source_bundle/'dolphin-debian'",self.text('tools/build.py'))
    def test_no_mime_default_install(self):self.assertNotIn('MimeType=',self.text('tools/runtime_install.py'));self.assertNotIn('xdg-mime',self.text('tools/runtime_install.py'))
    def test_native_test_sources_included(self):self.assertTrue((ROOT/'tests/tst_application.cpp').is_file());self.assertTrue((ROOT/'tests/tst_core.cpp').is_file())

class RuntimeManifestTests(unittest.TestCase):
    def bundle(self,root):
        (root/'bin').mkdir();p=root/'bin/irixclassic-files';p.write_bytes(b'not-an-executable-fixture');p.chmod(0o755)
        meta={'version':R.VERSION,'native_tests_passed':True,'files':{'bin/irixclassic-files':{'sha256':R.hash_file(p),'mode':0o755}}}
        (root/'BUILD-RESULT.json').write_text(json.dumps(meta));return meta
    def test_valid_fixture_manifest(self):
        with tempfile.TemporaryDirectory() as d:self.bundle(Path(d));self.assertEqual(R.verify(Path(d))['version'],R.VERSION)
    def test_changed_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.bundle(r);(r/'bin/irixclassic-files').write_bytes(b'edited')
            with self.assertRaises(R.Failure):R.verify(r)
    def test_unknown_file(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.bundle(r);(r/'unknown').write_text('x')
            with self.assertRaises(R.Failure):R.verify(r)
    def test_changed_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.bundle(r);(r/'bin/irixclassic-files').chmod(0o644)
            with self.assertRaises(R.Failure):R.verify(r)
    def test_native_receipt_missing(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);m=self.bundle(r);m['native_tests_passed']=False;(r/'BUILD-RESULT.json').write_text(json.dumps(m))
            with self.assertRaises(R.Failure):R.verify(r)

if __name__=='__main__':unittest.main()
