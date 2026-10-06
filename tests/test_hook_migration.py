# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import install_suite


class HookMigrationTest(unittest.TestCase):
    def test_existing_checkout_service_is_migrated_with_backup_without_starting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config';state=root/'state'
            service=config/'systemd/user/irix-classic-user.service'
            service.parent.mkdir(parents=True)
            original='[Service]\nExecStart='+str(install_suite.ROOT/'classic-rewrite-rc1/hooks/irix-classic-user.sh')+'\n'
            service.write_text(original)
            with patch.dict('os.environ',{'DBUS_SESSION_BUS_ADDRESS':'test'}), \
                 patch.object(install_suite.shutil,'which',return_value='/fake/systemctl'), \
                 patch.object(install_suite.subprocess,'run') as call,redirect_stdout(io.StringIO()):
                call.return_value.returncode=0
                install_suite.migrate_user_hook(config,state,dry=True)
                self.assertEqual(service.read_text(),original);call.assert_not_called()
                install_suite.migrate_user_hook(config,state)
                call.assert_called_once_with(['systemctl','--user','daemon-reload'],capture_output=True,text=True)
            self.assertIn('decorations/classic/hooks/irix-classic-user.sh',service.read_text())
            record=json.loads(next(state.rglob('receipt.json')).read_text())
            self.assertEqual(record['path'],str(service))
            install_suite.replace_checked(service,record['after'],record['before'])
            self.assertEqual(service.read_text(),original)

    def test_unrelated_service_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);service=root/'config/systemd/user/irix-classic-user.service'
            service.parent.mkdir(parents=True);service.write_text('[Service]\nExecStart=/other/checkout/hook\n')
            install_suite.migrate_user_hook(root/'config',root/'state')
            self.assertEqual(service.read_text(),'[Service]\nExecStart=/other/checkout/hook\n')
            self.assertFalse((root/'state').exists())
