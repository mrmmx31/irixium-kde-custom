# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure report/runner contracts. Native UI acceptance is deliberately separate."""
import contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import analyze_arrow_report as A
import review_integrated as R
import preview_integrated as P

class Analysis(unittest.TestCase):
    def test_unknown_report_kind_is_refused(self):
        with self.assertRaises(ValueError):A.analyse({'kind':'other'})
    def test_legacy_wrong_target_is_inconclusive(self):
        doc={'kind':'four_path_arrow_comparison','probes':{'quick_temporary_fix':{'result':{'checks':[
            {'orientation':'vertical','arrow':'down','motion_ok':False,'held_sunken':False,'held':{'activeControl':'upPage'}}]}}}}
        row=A.analyse(doc)['paths']['quick_temporary_fix']['checks'][0]
        self.assertEqual(row['assessment'],'invalid_target_observed');self.assertFalse(row['target_validated'])
    def test_motion_with_mouse_press_but_no_sunken_is_observed(self):
        doc={'kind':'four_path_arrow_comparison','probes':{'quick_installed':{'result':{'checks':[
            {'orientation':'vertical','direction':'subtract','motion':'ok','held_states':{
            'mouseAreaPressed':True,'styleItems':[{'active':'up','sunken':False,'opacity':1,'visible':True}]}}]}}}}
        row=A.analyse(doc)['paths']['quick_installed']['checks'][0]
        self.assertEqual(row['assessment'],'motion_without_pressure_observed');self.assertIsNone(row['target_validated'])
    def test_empty_results_do_not_become_passes(self):
        doc=A.analyse({'kind':'four_path_arrow_comparison','probes':{'widgets':{'returncode':77}}})
        self.assertEqual(doc['paths']['widgets']['checks'],[])

class Review(unittest.TestCase):
    def test_delivered_theme_and_system_patch_remain_byte_identical(self):
        baseline=json.loads((ROOT/'tests/data/integration-baseline.json').read_text())
        for rel,expected in baseline['protected_files'].items():
            self.assertEqual(R.digest((ROOT.parent/rel).read_bytes()),expected,rel)

    def test_seven_blocks_preserved(self):self.assertEqual([r[0] for r in R.BLOCKS],list('1234567'))
    def test_no_native_tasks_without_opt_in(self):self.assertTrue(all(t[2]=='static' for t in R.tasks(False)))
    def test_native_tasks_include_all_blocks_and_combined_gallery(self):
        names={t[0] for t in R.tasks(True)}
        self.assertTrue({'native-block-'+n for n in '1234567'}<=names);self.assertIn('native-integrated',names)
    def test_offscreen_is_disclosed(self):
        rows={r[0]:r[2] for r in R.tasks(True)}
        self.assertEqual(rows['native-block-1'],'qt-widgets-offscreen')
        self.assertEqual(rows['native-integrated'],'qt-widgets-session')
    def test_missing_native_not_approved(self):
        self.assertEqual(R.overall([{'status':'unavailable'}],True,True,True),'nativo_incompleto')
    def test_static_pass_is_not_full_acceptance(self):
        self.assertEqual(R.overall([{'status':'passed'}],False,True,True),'estaticos_concluidos_nativo_pendente')
    def test_file_change_during_review_is_failure(self):
        self.assertEqual(R.overall([],False,False,True),'falhas_detectadas')
    def test_all_native_pass_still_requires_visual_acceptance(self):
        self.assertEqual(R.overall([{'status':'passed'}],True,True,True),'aguarda_aceitacao_visual')
    def test_integrity_detects_corrupt_file(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);f=r/'kvantum/IrixClassic';f.mkdir(parents=True)
            vals={'IrixClassic.svg':b'<svg/>','IrixClassic.kvconfig':b'config','LICENSE':b'license'}
            for n,v in vals.items():(f/n).write_bytes(v)
            (f/'MANIFEST.json').write_text(json.dumps({'version':'test','files':{n:R.digest(v) for n,v in vals.items()}}))
            self.assertTrue(R.integrity(r)['passed']);(f/'IrixClassic.svg').write_bytes(b'bad');self.assertFalse(R.integrity(r)['passed'])
    def test_report_html_escapes_external_task_text(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);R.write_reports(r,{'status':'pending','tasks':[{'name':'<script>','category':'static','status':'passed','returncode':0}],'acceptance':[]})
            s=(r/'REVISAO-INTEGRADA.html').read_text();self.assertNotIn('<script>',s);self.assertIn('&lt;script&gt;',s)
    def test_gallery_missing_qt_returns_77(self):
        with patch.object(P.importlib.util,'find_spec',return_value=None),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(P.main(['--testar']),77)
    def test_no_global_theme_installer_in_review_plan(self):
        for _,args,_,_ in R.tasks(True):
            for token in ('sudo','pkexec','instalar','corrigir-pressao','update-irixium'):
                self.assertNotIn(token,' '.join(args))
if __name__=='__main__':unittest.main()
