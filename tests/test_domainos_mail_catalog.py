# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only mail-client discovery uses installed handler metadata, never mail."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[1]
SOURCE=REPO/"plasma/applets/org.irixclassic.domainos.panel/contents/code/commands.py"
SPEC=importlib.util.spec_from_file_location("domainos_mail_catalogue",SOURCE)
commands=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)

class MailCatalogue(unittest.TestCase):
    def setUp(self):
        self.private=tempfile.TemporaryDirectory(prefix=".qa-mail-catalogue-",dir=REPO)
        self.addCleanup(self.private.cleanup)
        self.user=Path(self.private.name)/"user"
        self.system=Path(self.private.name)/"system"
        self.user.mkdir();self.system.mkdir()
        directories=patch.object(commands,"application_dirs",return_value=[self.user,self.system])
        directories.start();self.addCleanup(directories.stop)
        default=patch.object(commands,"default_mail_client",return_value="alpha.desktop")
        default.start();self.addCleanup(default.stop)

    def entry(self,path,name="Client",extra="",mime="x-scheme-handler/mailto;"):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text("[Desktop Entry]\nType=Application\nName="+name+"\nExec=/bin/false\nMimeType="+mime+"\n"+extra)
        return path

    def test_only_real_mailto_handlers_and_stable_sort(self):
        self.entry(self.system/"z.desktop","Zulu")
        self.entry(self.system/"a.desktop","Alpha")
        self.entry(self.system/"utility.desktop","Exporter","Categories=Email;\n",mime="message/rfc822;")
        self.assertEqual([c["id"] for c in commands.mail_clients()["clients"]],["a.desktop","z.desktop"])

    def test_user_hidden_override_masks_system_client(self):
        self.entry(self.system/"alpha.desktop")
        self.entry(self.user/"alpha.desktop",extra="Hidden=true\n")
        self.assertEqual(commands.mail_clients()["clients"],[])

    def test_hidden_nondisplay_unavailable_and_broken_entries_do_not_break_catalogue(self):
        self.entry(self.system/"good.desktop")
        self.entry(self.system/"hidden.desktop",extra="Hidden=true\n")
        self.entry(self.system/"view.desktop",extra="NoDisplay=true\n")
        self.entry(self.system/"missing.desktop",extra="TryExec=definitely-no-domainos-client\n")
        (self.system/"broken.desktop").write_text("not a desktop entry")
        self.assertEqual([c["id"] for c in commands.mail_clients()["clients"]],["good.desktop"])

    def test_nested_xdg_identifier_and_localized_label(self):
        self.entry(self.system/"vendor/mail.desktop","Base","Name[pt_BR]=Correio\nName[pt]=Cliente\n")
        with patch.dict(os.environ,{"LANG":"pt_BR.UTF-8","LC_MESSAGES":""}):
            clients=commands.mail_clients()["clients"]
        self.assertEqual(clients[0]["id"],"vendor-mail.desktop")
        self.assertEqual(clients[0]["name"],"Correio")

    def test_invalid_preferred_default_does_not_hide_installed_handlers(self):
        self.entry(self.system/"good.desktop")
        with patch.object(commands,"default_mail_client",side_effect=ValueError("invalid desktop default")):
            report=commands.mail_clients()
        self.assertEqual(report["defaultClient"],"")
        self.assertEqual(report["clients"][0]["id"],"good.desktop")

    def test_catalogue_action_never_launches_or_reads_mail(self):
        self.entry(self.system/"good.desktop")
        with patch.object(commands,"launch_desktop") as launch, patch.object(commands.subprocess,"Popen") as spawn, patch.object(commands,"read_setting") as settings:
            report=commands.execute({"action":"mail-clients"})
        self.assertEqual(report["outcome"],"metadata-read")
        launch.assert_not_called();spawn.assert_not_called();settings.assert_not_called()
        self.assertNotIn("messages",report)
        self.assertNotIn("accounts",report)

    def test_local_entry_replaces_installed_name_without_duplicate(self):
        self.entry(self.system/"alpha.desktop","System")
        self.entry(self.user/"alpha.desktop","Local")
        clients=commands.mail_clients()["clients"]
        self.assertEqual(len(clients),1)
        self.assertEqual(clients[0]["name"],"Local")

if __name__=="__main__":unittest.main()
