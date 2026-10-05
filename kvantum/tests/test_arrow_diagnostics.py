# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Diagnostic contracts, not native input test results."""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import diagnose_arrows as D
class Diagnostics(unittest.TestCase):
    def test_motion_classification_requires_direction(self):
        self.assertEqual(D.classify(50,51,51,1)['motion'],'ok')
        self.assertEqual(D.classify(50,49,49,-1)['motion'],'ok')
        self.assertEqual(D.classify(50,51,51,-1)['motion'],'failed')
    def test_no_motion_is_failure_not_inferred_from_pixels(self):
        self.assertEqual(D.classify(50,50,50,1)['motion'],'failed')
        self.assertNotIn('arrow_pixels_changed',D.classify(50,51,51,1))
    def test_old_pressure_path_is_detectable(self):
        r=D.inspect_qml('sunken: controlRoot.pressed\n // normally minSize')
        self.assertTrue(r['native_pressed_only']);self.assertFalse(r['previous_optional_patch_marker'])
    def test_patch_marker_detection_does_not_certify_loaded_module(self):
        r=D.inspect_qml('IRIXCLASSIC_QTQUICK_ARROW_PRESS_V1\nsunken: foo')
        self.assertTrue(r['previous_optional_patch_marker']);self.assertFalse(r['native_pressed_only'])
    def test_inspection_is_content_addressed(self):
        self.assertNotEqual(D.inspect_qml('a')['sha256'],D.inspect_qml('b')['sha256'])
    def test_inventory_queries_are_read_only(self):
        with patch.object(D,'run_info',return_value={'code':0,'text':'mock'}) as p:
            D.inventory()
            self.assertTrue(all(c.args[0][0]=='dpkg-query' for c in p.call_args_list))
    def test_default_cli_does_not_spawn_qt_probes(self):
        with patch.object(D,'inventory',return_value={'kind':'read_only_inventory'}), patch.object(D.subprocess,'run') as run, contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(D.main([]),0);run.assert_not_called()
            self.assertEqual(json.loads(out.getvalue())['kind'],'read_only_inventory')
    def test_missing_qt_returns_77_not_pass(self):
        with patch.object(D.importlib.util,'find_spec',return_value=None):
            r,code=D.native_probe('widgets','Fusion');self.assertEqual(code,77);self.assertEqual(r['status'],'skipped')
    def test_output_never_overwrites_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'keep';f.write_text('original')
            with patch.object(D,'inventory',return_value={}),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):D.main(['--saida',d])
            self.assertEqual(f.read_text(),'original')
    def test_report_permissions_are_private(self):
        with tempfile.TemporaryDirectory() as d,patch.object(D,'inventory',return_value={'ok':True}),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(D.main(['--saida',d]),0)
            f=Path(d)/'DIAGNOSTICO-SETAS.json';self.assertEqual(f.stat().st_mode & 0o777,0o600)
    def test_system_patch_is_not_called_by_diagnostic(self):
        text=(ROOT/'tools/diagnose_arrows.py').read_text()
        self.assertNotIn('qtquick_scrollbar_fix',text);self.assertNotIn('pkexec',text);self.assertNotIn('sudo',text)
    def test_qml_probe_uses_installed_controls_not_replacement(self):
        text=(ROOT/'tests/qml/ProbeScrollbars.qml').read_text()
        self.assertIn('import QtQuick.Controls',text);self.assertIn('ScrollBar.vertical:',text)
        self.assertNotRegex(text,r'(?m)^\s*sunken\s*:');self.assertNotIn('MouseArea {',text)
        self.assertIn('mouseAreaPressed',text);self.assertIn('contentY',text)
        self.assertIn('s.hitTest(',text)
        self.assertNotIn('subControlRect("up")',text)
if __name__=='__main__':unittest.main()
