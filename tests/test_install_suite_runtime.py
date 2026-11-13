# SPDX-License-Identifier: GPL-3.0-or-later
"""Preflight the actual native GTK provider and distribution helper bindings."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import install_suite
from theme_transaction import Failure


class SuiteRuntimeTest(unittest.TestCase):
    def runtime(self, *, missing_gtk=False, python_failure=False):
        probed, imports = set(), []

        def is_file(path):
            probed.add(str(path))
            return not (missing_gtk and str(path) == '/native-plugins/kf6/kded/gtkconfig.so')

        def query(command, **kwargs):
            return '/native-qml\n' if command[-1] == 'QT_INSTALL_QML' else '/native-plugins\n'

        def run(command, **kwargs):
            imports.append(command)
            return SimpleNamespace(returncode=int(python_failure))

        with patch.object(install_suite, 'check_domainos_qt'), \
                patch.object(install_suite.shutil, 'which', return_value='/native/bin'), \
                patch.object(install_suite.subprocess, 'check_output', side_effect=query), \
                patch.object(install_suite.subprocess, 'run', side_effect=run), \
                patch.object(Path, 'is_file', is_file):
            install_suite.check_runtime()
        return probed, imports

    def test_complete_runtime_checks_native_gtk_provider_and_distribution_bindings(self):
        probed, imports = self.runtime()
        self.assertIn('/native-plugins/kf6/kded/gtkconfig.so', probed)
        self.assertIn('/native-plugins/styles/libkvantum.so', probed)
        self.assertEqual(imports, [['/usr/bin/python3', '-c',
                                  'from PyQt6 import QtCore, QtDBus, QtGui; from PIL import Image']])

    def test_missing_native_gtk_provider_is_reported_even_with_qt_and_python_present(self):
        with self.assertRaisesRegex(Failure, 'GTK Config nativo do KDE'):
            self.runtime(missing_gtk=True)

    def test_missing_distribution_qt_or_image_bindings_blocks_installation(self):
        with self.assertRaisesRegex(Failure, 'PyQt6 QtCore/QtDBus/QtGui e Pillow'):
            self.runtime(python_failure=True)


if __name__ == '__main__':
    unittest.main()
