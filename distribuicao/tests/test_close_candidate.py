# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Finalization decisions and collection contracts. No installed theme changes."""
from __future__ import annotations
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'distribuicao/tools'))
import close_candidate as F
import smoke_package as S


def sample_report(name='classic-menus'):
    key,theme,complete=F.EXPECTED_NATIVE[name]
    return {key:[{'test':'test '+str(i),'passed':True} for i in range(F.EXPECTED_COUNTS[name])], 'theme':theme,'status':'passed', 'completed':True,
            'style_class':'Kvantum::Style','platform':'wayland'}


def complete_document():
    names=list(F.EXPECTED_NATIVE)+['static-theme','static-install','static-distribution']
    return {'tasks':[{'name':n,'status':'passed','category':'native' if n in F.EXPECTED_NATIVE else 'static','desktop_evidence':True} for n in names],
            'preserved':True,'packages_verified':True,'packages_reproducible':True,
            'installation':{'status':'passed'},'evidence':{p:'0'*64 for p in (
                'capturas/finishing/01-acabamento.png','capturas/finishing/02-toolbar-horizontal.png',
                'capturas/finishing/03-toolbar-vertical.png','capturas/classic-integrated/01-conjunto.png',
                'capturas/modern-integrated/01-conjunto.png')}}


class ClosurePolicy(unittest.TestCase):
    def test_valid_native_report(self): self.assertEqual(F.native_verdict('classic-menus',0,sample_report()),'passed')
    def test_truncated_native_result_is_not_pass(self):
        d=sample_report();d['results']=d['results'][:1]
        self.assertEqual(F.native_verdict('classic-menus',0,d),'inconclusive')
    def test_empty_report_is_not_pass(self): self.assertEqual(F.native_verdict('classic-menus',0,{}),'inconclusive')
    def test_missing_qt_is_unavailable_not_pass(self): self.assertEqual(F.native_verdict('classic-menus',77,None),'unavailable')
    def test_error_status_is_not_pass(self): self.assertEqual(F.native_verdict('classic-menus',1,sample_report()),'failed')
    def test_incomplete_menu_does_not_pass(self):
        d=sample_report();d['completed']=False
        self.assertEqual(F.native_verdict('classic-menus',0,d),'inconclusive')
    def test_one_failed_check_is_not_hidden(self):
        d=sample_report();d['results'].append({'passed':False})
        self.assertEqual(F.native_verdict('classic-menus',0,d),'failed')
    def test_wrong_theme_is_not_pass(self):
        d=sample_report();d['theme']='Irixium'
        self.assertEqual(F.native_verdict('classic-menus',0,d),'inconclusive')
    def test_fusion_fallback_is_not_pass(self):
        d=sample_report();d['style_class']='QFusionStyle'
        self.assertEqual(F.native_verdict('classic-menus',0,d),'inconclusive')
    def test_platform_required(self):
        d=sample_report();del d['platform']
        self.assertEqual(F.native_verdict('classic-menus',0,d),'inconclusive')
    def test_complete_native_still_waits_for_human(self):
        self.assertEqual(F.decision(complete_document())[:2],('awaiting_visual_acceptance',2))
    def test_offscreen_never_desktop_acceptance(self):
        d=complete_document();d['tasks'][0]['desktop_evidence']=False
        self.assertEqual(F.decision(d)[0],'evidence_incomplete')
    def test_missing_native_blocks_acceptance(self):
        d=complete_document();d['tasks']=d['tasks'][1:]
        self.assertEqual(F.decision(d)[1],77)
    def test_missing_static_blocks_acceptance(self):
        d=complete_document();d['tasks']=d['tasks'][:-1]
        self.assertEqual(F.decision(d)[1],77)
    def test_skips_are_not_counted_as_full_acceptance(self):
        d=complete_document();d['tasks'][-1]['status']='passed_with_skips'
        self.assertEqual(F.decision(d)[1],77)
    def test_failure_blocks(self):
        d=complete_document();d['tasks'][0]['status']='failed'
        self.assertEqual(F.decision(d)[1],1)
    def test_changed_sources_block(self):
        d=complete_document();d['preserved']=False
        self.assertEqual(F.decision(d)[1],1)
    def test_package_corruption_blocks(self):
        d=complete_document();d['packages_verified']=False
        self.assertEqual(F.decision(d)[1],1)
    def test_installation_missing_blocks(self):
        d=complete_document();d['installation']['status']='unavailable'
        self.assertEqual(F.decision(d)[1],77)
    def test_installation_failure_blocks(self):
        d=complete_document();d['installation']['status']='failed'
        self.assertEqual(F.decision(d)[1],1)
    def test_no_capture_no_visual_acceptance(self):
        d=complete_document();d['evidence']={}
        self.assertEqual(F.decision(d)[1],77)
    def test_empty_human_acceptance_refused(self):
        with self.assertRaises(F.B.Failure):F.decision(complete_document(),{})
    def test_explicit_acceptance_stays_candidate(self):
        manual={'responsible':'mrmmx31','date':'2026-10-05','items':{k:{'status':'aprovado'} for k in F.MANUAL}}
        self.assertEqual(F.decision(complete_document(),manual)[:2],('candidate_accepted_locally',0))
    def test_rejection_respected(self):
        manual={'items':{k:{'status':'aprovado'} for k in F.MANUAL}}
        manual['items']['spinbox']['status']='reprovado'
        self.assertEqual(F.decision(complete_document(),manual)[:2],('visual_changes_requested',2))
    def test_unknown_acceptance_status_refused(self):
        manual={'items':{k:{'status':True} for k in F.MANUAL}}
        with self.assertRaises(F.B.Failure):F.decision(complete_document(),manual)
    def test_date_and_nick_required(self):
        manual={'items':{k:{'status':'aprovado'} for k in F.MANUAL}}
        with self.assertRaises(F.B.Failure):F.decision(complete_document(),manual)
    def test_counts_distinguish_skips(self):
        self.assertEqual(F.counts('Ran 9 tests in 0.1s\n\nOK (skipped=2)\n'),{'run':9,'skipped':2,'passed':7})
    def test_malformed_json_is_not_report(self):self.assertIsNone(F.extract_json('not { JSON'))
    def test_json_can_follow_startup_text(self):
        d=sample_report();self.assertEqual(F.extract_json('Starting\n'+json.dumps(d,indent=2)),d)
    def test_no_native_jobs_when_disabled(self):
        self.assertEqual(len(F.tasks(False)),3);self.assertEqual(len(F.tasks(True)),10)
    def test_resolved_scrollbar_not_repaired_or_retested(self):
        args=repr(F.tasks());self.assertNotIn('qtquick_scrollbar_fix',args);self.assertNotIn('compare_arrows',args)
    def test_root_smoke_is_not_approved(self):
        with mock.patch.object(os,'geteuid',return_value=0):self.assertEqual(S.run(ROOT)['status'],'unavailable')
    def test_output_must_be_new_and_outside_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp)/'repo';r.mkdir()
            with self.assertRaises(F.B.Failure):F.new_output(r/'out',r)
            p=F.new_output(Path(tmp)/'out',r);self.assertEqual(p.stat().st_mode&0o777,0o700)
            with self.assertRaises(FileExistsError):F.new_output(p,r)
    def test_symlink_output_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'real';p.mkdir();q=Path(tmp)/'alias';q.symlink_to(p)
            with self.assertRaises(F.B.Failure):F.new_output(q/'out')
    def test_task_missing_binding_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'logs').mkdir();(out/'resultados').mkdir()
            response=subprocess.CompletedProcess([],77,'','SKIP')
            with mock.patch.object(subprocess,'run',return_value=response):
                row=F.run_task(F.tasks()[3],ROOT,out)
            self.assertEqual(row['status'],'unavailable');self.assertFalse(row['desktop_evidence'])
    def test_timeout_keeps_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'logs').mkdir();(out/'resultados').mkdir()
            with mock.patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired([],1,output=b'partial output')):
                row=F.run_task(F.tasks()[3],ROOT,out)
            self.assertEqual(row['returncode'],124);self.assertIn('partial output',(out/row['log']).read_text())
    def test_export_never_copies_unknown_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'FECHAMENTO.json').write_bytes(F.dump({'evidence':{}}));(out/'private.txt').write_text('private')
            F.export_evidence(out)
            with zipfile.ZipFile(out/'EVIDENCIAS-PARA-REVISAO.zip') as z:
                self.assertNotIn('irixclassic-fechamento/private.txt',z.namelist())
    def test_capture_script_only_own_widgets(self):
        s=(ROOT/'kvantum/tools/preview_finish.py').read_text()
        self.assertIn("p.add_argument('--capturas'",s)
        self.assertIn("capture('02-toolbar-horizontal',horizontal)",s)
        self.assertIn("capture('03-toolbar-vertical',vertical)",s)
        self.assertIn('widget.grab()',s);self.assertNotIn('grabWindow(',s)
        self.assertNotIn('setStyleSheet(',s)
    def test_capture_press_always_has_finally_release(self):
        s=(ROOT/'kvantum/tools/preview_finish.py').read_text()
        self.assertIn('finally:\n                    T.QTest.mouseRelease',s)



class EvaluationIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
        self.doc=complete_document();self.doc.update(format=1,revision='fechamento-r1',theme_version=F.CANDIDATE_VERSION,source_files={})
        self.doc['evidence']={}
        (self.folder/'FECHAMENTO.json').write_bytes(F.dump(self.doc))
        self.manual={'format':1,'theme_version':F.CANDIDATE_VERSION,
                     'report_sha256':F.sha((self.folder/'FECHAMENTO.json').read_bytes()),
                     'responsible':'mrmmx31','date':'2026-10-05',
                     'items':{k:{'status':'aprovado'} for k in F.MANUAL}}
        (self.folder/'ACEITE-VISUAL.json').write_bytes(F.dump(self.manual))
    def tearDown(self):self.temp.cleanup()
    def test_changed_report_rejected(self):
        p=self.folder/'FECHAMENTO.json';p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaises(F.B.Failure):F.evaluate(self.folder)
    def test_changed_sources_rejected(self):
        with mock.patch.object(F,'sources',return_value={'changed':'hash'}):
            with self.assertRaises(F.B.Failure):F.evaluate(self.folder)
    def test_changed_evidence_rejected(self):
        with mock.patch.object(F,'sources',return_value={}),mock.patch.object(F,'evidence_hashes',return_value={'extra':'hash'}):
            with self.assertRaises(F.B.Failure):F.evaluate(self.folder)
    def test_linked_acceptance_rejected(self):
        p=self.folder/'ACEITE-VISUAL.json';b=p.read_bytes();p.unlink()
        target=self.folder/'other';target.write_bytes(b);p.symlink_to(target)
        with self.assertRaises(F.B.Failure):F.evaluate(self.folder)
    def test_missing_captures_still_prevent_acceptance(self):
        with mock.patch.object(F,'sources',return_value={}):
            code=F.evaluate(self.folder)
        self.assertEqual(code,77)
        verdict=json.loads((self.folder/'PARECER-FINAL.json').read_text())
        self.assertFalse(verdict['stable_approved']);self.assertFalse(verdict['published'])
    def test_manual_pending_cannot_become_publication(self):
        self.manual['items']['toolbar']['status']='pendente'
        (self.folder/'ACEITE-VISUAL.json').write_bytes(F.dump(self.manual))
        with mock.patch.object(F,'sources',return_value={}):code=F.evaluate(self.folder)
        self.assertNotEqual(code,0)
    def test_source_archive_does_not_include_desktop_repair(self):
        outputs,_=F.B.build_plan(ROOT)
        import io,zipfile
        for n,b in outputs.items():
            if not n.endswith('.zip'):continue
            with zipfile.ZipFile(io.BytesIO(b)) as z:
                self.assertFalse(any('qtquick_scrollbar_fix' in x for x in z.namelist()))
    def test_installer_still_refuses_privilege_escalation(self):
        s=(ROOT/'distribuicao/tools/smoke_package.py').read_text()
        self.assertIn("os.geteuid() == 0",s)
        self.assertNotIn("['sudo'",s);self.assertNotIn("['pkexec'",s)

if __name__=='__main__':unittest.main()
