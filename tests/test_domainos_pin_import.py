# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]/"plasma/applets/org.irixclassic.domainos.panel/contents/code/pin_import.py"
spec = importlib.util.spec_from_file_location("domainos_pin_import", SOURCE)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class PinImportTest(unittest.TestCase):
    def test_source_is_read_only_and_independent_from_favorites(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/"appletsrc"
            config.write_text("[Containments][3][Applets][7]\nplugin=org.irixclassic.iconbox\n"
                "[Containments][3][Applets][7][Configuration][General]\nlaunchers=applications:org.kde.konsole.desktop,applications:org.kde.dolphin.desktop\n"
                "[Containments][3][Applets][9]\nplugin=org.kde.plasma.kickoff\n"
                "[Containments][3][Applets][9][Configuration][General]\nfavorites=application:unrelated.desktop\n")
            before=hashlib.sha256(config.read_bytes()).hexdigest()
            listed=module.execute({"action":"origins"},config)
            self.assertEqual(len(listed["origins"]),1)
            self.assertNotIn("desktopIds",listed["origins"][0])
            source=module.execute({"action":"source","sourceId":"3/7"},config)
            self.assertEqual(source["desktopIds"],["org.kde.konsole.desktop","org.kde.dolphin.desktop"])
            self.assertEqual(hashlib.sha256(config.read_bytes()).hexdigest(),before)

    def test_only_application_ids_imported_once(self):
        self.assertEqual(module.desktop_ids("applications:one.desktop,applications:one.desktop,applications:two.desktop,file:///tmp/anything.desktop,sh;bad.desktop,../unsafe.desktop"),["one.desktop","two.desktop"])

    def test_kconfig_escaped_commas_not_split_into_fake_entries(self):
        self.assertEqual(module.list_value(r"a\,b,c\\d"),["a,b","c\\d"])

    def test_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,"no longer exists"):
                module.execute({"action":"source","sourceId":"1/99"},Path(directory)/"absent")

    def test_unknown_action_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,"Unknown"):
                module.execute({"action":"sync"},Path(directory)/"absent")

    def test_existing_quicklaunch_files_resolve_only_from_xdg_applications(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); apps=root/"applications"; apps.mkdir()
            entry=apps/"browser.desktop"; entry.write_text("[Desktop Entry]\nType=Application\n")
            external=root/"external.desktop"; external.write_text("[Desktop Entry]\nType=Application\n")
            with patch.object(module,"application_dirs",return_value=[apps]):
                self.assertEqual(module.desktop_ids(entry.as_uri()+","+external.as_uri()),["browser.desktop"])


if __name__=="__main__": unittest.main()
