# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Comparison collector contracts; mocked subprocesses are not native tests."""
from pathlib import Path
import contextlib, io, json, subprocess, sys, tempfile, unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import compare_arrows as C
import diagnose_arrows as D
class Comparison(unittest.TestCase):
    def test_four_paths_are_distinct(self):
        rows=C.commands('Fusion')
        self.assertEqual([n for n,_ in rows],['widgets','quick_installed','quick_file','quick_temporary_fix'])
        self.assertIn('--original',rows[2][1]);self.assertNotIn('--original',rows[3][1])
        self.assertIn('--probe',rows[1][1])
    def test_no_install_or_system_write_commands(self):
        for _,argv in C.commands('Fusion'):
            joined=' '.join(argv)
            for token in ('sudo','pkexec','corrigir-pressao','install_kvantum'):self.assertNotIn(token,joined)
    def test_skipped_native_probe_is_not_a_pass(self):
        with patch.object(C.subprocess,'run',return_value=subprocess.CompletedProcess([],77,'{"status":"skipped"}','')):
            r=C.execute([]);self.assertEqual(r['status'],'not_run');self.assertEqual(r['returncode'],77)
    def test_report_can_record_a_failed_native_assertion(self):
        with patch.object(C.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'{"motion_ok":false}','')):
            r=C.execute([]);self.assertEqual(r['status'],'completed');self.assertFalse(r['result']['motion_ok']);self.assertEqual(r['returncode'],1)
    def test_non_json_error_is_not_completed(self):
        with patch.object(C.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'bad','error')):
            self.assertEqual(C.execute([])['status'],'probe_error')
    def test_timeout_is_classified(self):
        with patch.object(C.subprocess,'run',side_effect=subprocess.TimeoutExpired('probe',60)):
            self.assertEqual(C.execute([])['status'],'timeout')
    def test_all_missing_returns_77_and_writes_private_report(self):
        with tempfile.TemporaryDirectory() as d,patch.object(C,'inventory',return_value={}),patch.object(C,'execute',return_value={'status':'not_run','returncode':77}),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(C.main(['--saida',d]),77)
            f=Path(d)/'COMPARACAO-SETAS.json';doc=json.loads(f.read_text())
            self.assertEqual(len(doc['probes']),4);self.assertEqual(doc['collection_status'],'no_native_result')
            self.assertEqual(f.stat().st_mode&0o777,0o600)
    def test_interruption_preserves_partial_evidence(self):
        with tempfile.TemporaryDirectory() as d,patch.object(C,'inventory',return_value={}),patch.object(C,'execute',side_effect=[{'status':'completed','returncode':1,'result':{}},KeyboardInterrupt]),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(C.main(['--saida',d]),130)
            doc=json.loads((Path(d)/'COMPARACAO-SETAS.json').read_text())
            self.assertTrue(doc['interrupted']);self.assertEqual(list(doc['probes']),['widgets'])
    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stderr(io.StringIO()):
            f=Path(d)/'keep';f.write_text('keep')
            with self.assertRaises(SystemExit):C.main(['--saida',d])
            self.assertEqual(f.read_text(),'keep')
    def test_symlink_output_refused(self):
        with tempfile.TemporaryDirectory() as d,contextlib.redirect_stderr(io.StringIO()):
            f=Path(d)/'link';f.symlink_to(Path(d)/'other',target_is_directory=True)
            with self.assertRaises(SystemExit):C.main(['--saida',str(f)])
    def test_hover_hit_test_is_not_reported_as_press_hit_test(self):
        t='onPressed: mouse => { mouse.accepted = true; }\nonPositionChanged: mouse => {\n style.activeControl = style.hitTest(mouse.x, mouse.y);\n}'
        r=D.inspect_qml(t);self.assertFalse(r['click_hit_test_present']);self.assertTrue(r['any_handler_hit_test_present'])
    def test_press_hit_test_is_detected(self):
        t='onPressed: mouse => {\n style.activeControl = style.hitTest(mouse.x, mouse.y);\n}\nonReleased: mouse => {}'
        self.assertTrue(D.inspect_qml(t)['click_hit_test_present'])
if __name__=='__main__':unittest.main()
