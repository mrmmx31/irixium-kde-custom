# SPDX-License-Identifier: GPL-3.0-or-later
"""Reject incomplete native runtimes before installing a broken panel."""
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import install_domainos
from theme_transaction import Failure


class DomainOSRuntimeTest(unittest.TestCase):
    def runtime(self, missing=()):
        probed = set()

        def is_file(path):
            probed.add(str(path))
            return not any(str(path) == '/native-qml/' + module + '/qmldir'
                           for module in missing)

        with patch.object(install_domainos, 'check_domainos_qt'), \
                patch.object(install_domainos.shutil, 'which', return_value='/native/bin'), \
                patch.object(install_domainos.subprocess, 'check_output', return_value='/native-qml\n'), \
                patch.object(install_domainos.subprocess, 'run', return_value=SimpleNamespace(returncode=0)), \
                patch.object(Path, 'is_file', is_file):
            install_domainos.check_runtime(Path('/private/data'))
        return probed

    def test_missing_kwindowsystem_fails_before_panel_installation(self):
        with self.assertRaisesRegex(Failure, r'org\.kde\.kwindowsystem Qt 6'):
            self.runtime(missing=('org/kde/kwindowsystem',))

    def test_all_direct_mandatory_file_backed_imports_are_checked(self):
        modules = set()
        for applet in ('org.irixclassic.domainos.panel', 'org.irixclassic.grosview'):
            for source in (ROOT / 'plasma/applets' / applet / 'contents').rglob('*.qml'):
                modules.update(re.findall(r'^import\s+([A-Za-z][A-Za-z0-9.]*)',
                                          source.read_text(), re.MULTILINE))
        # The real Plasma host registers these two APIs. PipeWire belongs to
        # the optional, lazily loaded Wayland provider, with explicit fallback.
        modules -= {'org.kde.plasma.plasmoid', 'org.kde.plasma.configuration',
                    'org.kde.pipewire'}
        expected = {'/native-qml/' + module.replace('.', '/') + '/qmldir'
                    for module in modules}
        self.assertLessEqual(expected, self.runtime())

    def test_unavailable_optional_wayland_thumbnails_do_not_block_installation(self):
        probed = self.runtime(missing=('org/kde/pipewire',))
        self.assertNotIn('/native-qml/org/kde/pipewire/qmldir', probed)


if __name__ == '__main__':
    unittest.main()
