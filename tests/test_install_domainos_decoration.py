# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the independent decoration installer without a personal profile."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import install_domainos_decoration as installer
from theme_transaction import Failure
from user_bundle import fingerprint


class DomainOSDecorationInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='domainos-decoration-install-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root/'repo'
        self.package = self.repo/installer.SOURCE
        (self.package/'contents/ui').mkdir(parents=True)
        (self.package/'contents/ui/main.qml').write_text('import QtQuick\nItem {}\n')
        self.metadata = {
            'KPackageStructure': 'KWin/Decoration',
            'KPlugin': {'Id': 'domainos_sr104', 'Name': 'DomainOS SR10.4'}}
        (self.package/'metadata.json').write_text(json.dumps(self.metadata))
        self.write_manifest()
        self.data, self.config, self.state = [self.root/name for name in ('data', 'config', 'state')]
        self.config.mkdir()
        (self.config/'kwinrc').write_text(
            '[org.kde.kdecoration2]\ntheme=irixium_irix_classic_v4\nButtonsOnRight=IA\n')
        (self.config/'plasma-org.kde.plasma.desktop-appletsrc').write_text(
            '[Containments][14]\nplugin=org.kde.panel\n')
        self.preferences = fingerprint(self.config)
        self.sibling = self.data/'kwin/decorations/irixium_irix_classic_v4'
        self.sibling.mkdir(parents=True)
        (self.sibling/'preserve').write_text('independent Classic decoration')
        self.before_sibling = fingerprint(self.sibling)
        for name, value in (
            ('ROOT', self.repo),
            ('catalog', lambda: {'components': [{
                'source': installer.SOURCE, 'root': 'data', 'destination': installer.DESTINATION}]}),
            ('check_runtime', lambda: None)):
            context = patch.object(installer, name, value)
            context.start()
            self.addCleanup(context.stop)
        environment = patch.dict('os.environ', {
            'XDG_DATA_HOME': str(self.data), 'XDG_CONFIG_HOME': str(self.config),
            'XDG_STATE_HOME': str(self.state)})
        environment.start()
        self.addCleanup(environment.stop)
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def write_manifest(self):
        files = {path.relative_to(self.package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(self.package.rglob('*')) if path.is_file()}
        (self.package.parent/'MANIFEST.json').write_text(json.dumps({'package': files}))

    @property
    def destination(self):
        return self.data/installer.DESTINATION

    def assert_preferences_preserved(self):
        self.assertEqual(fingerprint(self.config), self.preferences)
        self.assertEqual(fingerprint(self.sibling), self.before_sibling)

    def test_check_install_repeat_and_restore_preserve_preferences_and_sibling(self):
        installer.main(['--verificar'])
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.state.exists())
        self.assert_preferences_preserved()
        installer.main([])
        self.assertEqual(fingerprint(self.destination), fingerprint(self.package))
        pointer = self.state/'irixium-domainos-decoration/latest'
        token = pointer.read_text()
        installer.main([])
        self.assertEqual(pointer.read_text(), token)
        installer.main(['--restaurar', '--verificar'])
        self.assertTrue(self.destination.exists())
        installer.main(['--restaurar'])
        self.assertFalse(self.destination.exists())
        self.assert_preferences_preserved()

    def test_existing_package_is_backed_up_and_restored_exactly(self):
        self.destination.mkdir()
        (self.destination/'previous.qml').write_text('previous optional theme')
        (self.destination/'alias.qml').symlink_to('previous.qml')
        before = fingerprint(self.destination)
        installer.main([])
        self.assertNotIn('previous.qml', fingerprint(self.destination))
        installer.main(['--restaurar'])
        self.assertEqual(fingerprint(self.destination), before)
        self.assertTrue((self.destination/'alias.qml').is_symlink())
        self.assert_preferences_preserved()

    def test_source_mutation_is_rejected_before_install(self):
        (self.package/'contents/ui/main.qml').write_text('changed without updating manifest')
        with self.assertRaises(Failure):
            installer.main([])
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.state.exists())
        self.assert_preferences_preserved()

    def test_wrong_identity_is_rejected_even_with_matching_hashes(self):
        self.metadata['KPlugin']['Id'] = 'irixium_irix_classic_v4'
        (self.package/'metadata.json').write_text(json.dumps(self.metadata))
        self.write_manifest()
        with self.assertRaises(Failure):
            installer.main([])
        self.assertFalse(self.destination.exists())
        self.assert_preferences_preserved()

    def test_post_install_user_edit_prevents_restore(self):
        installer.main([])
        (self.destination/'contents/ui/main.qml').write_text('user modification')
        with self.assertRaises(Failure):
            installer.main(['--restaurar'])
        self.assertEqual((self.destination/'contents/ui/main.qml').read_text(), 'user modification')
        self.assert_preferences_preserved()

    def test_root_is_rejected_before_writes(self):
        with patch.object(installer.os, 'geteuid', return_value=0), self.assertRaises(Failure):
            installer.main([])
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.state.exists())
        self.assert_preferences_preserved()


if __name__ == '__main__':
    unittest.main()
