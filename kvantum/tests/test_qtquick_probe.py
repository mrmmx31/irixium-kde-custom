# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Harness regression tests, not a substitute for native Qt/KDE execution."""
import contextlib,io,json,subprocess,sys,shutil,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import arrow_runtime as R
import preview_qtquick_pressure as P
import arrow_probe_logic as L

class PressureProbe(unittest.TestCase):
    def test_one_scene_for_all_loading_paths(self):
        a=R.scene_text('installed');b=R.scene_text('file');c=R.scene_text('temporary_fix')
        self.assertEqual(b,c);self.assertEqual(b.replace(': ProbeScrollBar { // PROBE_BAR_TYPE',': ScrollBar { // PROBE_BAR_TYPE'),a)
    def test_unknown_mode_refused(self):
        with self.assertRaises(ValueError):R.scene_text('other')
    def test_corner_is_reserved_not_overlapped(self):
        s=R.scene_text('installed')
        self.assertIn('width:stage.width-vbar.width;height:stage.height-hbar.height',s)
        self.assertIn('x:area.width;y:0;width:implicitWidth;height:area.height',s)
        self.assertIn('x:0;y:area.height;width:area.width;height:implicitHeight',s)
    def test_no_unsupported_arrow_subcontrol_queries(self):
        s=R.scene_text('installed');self.assertNotIn('subControlRect(',s);self.assertIn('s.hitTest(',s)
    def test_receiver_observation_does_not_change_acceptance_or_pressed(self):
        s=R.scene_text('installed');self.assertIn('lastPress={bar:which,hit:',s)
        self.assertNotRegex(s,r'(?m)^\s*sunken\s*:');self.assertNotIn('mouse.accepted =',s)
        self.assertNotIn('style.activeControl =',s)
    def test_fresh_geometry_on_each_snapshot(self):
        s=R.scene_text('installed');self.assertIn('function refreshProbe()',s)
        self.assertIn('Probe.scan(',s);self.assertIn('onSampleTickChanged: refreshProbe()',s)
        self.assertNotIn('property string irixProbeGeometry:',s)
    def test_scene_coordinates_mapping_instead_of_assumed_origins(self):
        s=R.scene_text('installed');self.assertIn('mapToItem(null',s);self.assertIn('mapFromItem(b.background',s)
    def test_runtime_no_implicit_backend_override(self):
        s=(ROOT/'tools/arrow_runtime.py').read_text()
        self.assertIn("if offscreen:\n            os.environ['QT_QPA_PLATFORM']='offscreen'",s)
        self.assertNotIn("if manual:\n            os.environ['QT_QPA_PLATFORM']",s)
    def test_source_copy_is_exact_for_file_path(self):
        s=(ROOT/'tools/arrow_runtime.py').read_text()
        self.assertIn("source=raw if mode=='file'",s);self.assertIn('.write_bytes(source)',s)
        self.assertNotIn('instrument(',s)
    def test_no_system_installer_called(self):
        for f in ('arrow_runtime.py','preview_qtquick_pressure.py'):
            s=(ROOT/'tools'/f).read_text()
            for forbidden in ('system_main(','make_plan(','sudo','pkexec','killall','systemctl'):
                self.assertNotIn(forbidden,s)
    def test_missing_binding_returns_77(self):
        with patch.object(R.importlib.util,'find_spec',return_value=None):
            report,code=R.run_quick('installed');self.assertEqual(code,77);self.assertEqual(report['status'],'skipped')
    def test_wrapper_selects_original_vs_temporary_without_install(self):
        with patch.object(P,'run_quick',return_value=({'status':'skipped'},77)) as run,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(P.main(['--testar','--original']),77);self.assertEqual(run.call_args.args[0],'file')
            P.main(['--testar']);self.assertEqual(run.call_args.args[0],'temporary_fix')
    def test_javascript_scan_remeasures_down_after_resize(self):
        if not shutil.which('node'):self.skipTest('Node ausente')
        js=(ROOT/'tests/qml/ArrowProbe.js').read_text().replace('.pragma library','')
        code=js+'''
const assert=require('node:assert/strict');
let len=230;
const hit=(x,y)=>y<18?'up':y>=len-18?'down':'upPage';
assert.equal(scan(len,9,true,hit,'down').y,220);
len=350;
assert.equal(scan(len,9,true,hit,'down').y,340);
const horizontal=(x,y)=>x<18?'up':x>=445-18?'down':'handle';
assert.equal(scan(445,9,false,horizontal,'down').x,435);
assert.equal(scan(445,9,false,horizontal,'up').x,8);
assert.equal(scan(20,9,true,()=> 'handle','up'),null);
assert.equal(clearTarget({x:600,y:337},{x:12,y:328,width:596,height:18},{x:590,y:64,width:18,height:282}),false);
assert.equal(clearTarget({x:580,y:337},{x:12,y:328,width:578,height:18},{x:590,y:64,width:18,height:264}),true);
'''
        run=subprocess.run(['node','-e',code],capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)

class Evidence(unittest.TestCase):
    def samples(self):
        return ({'position':.4,'target':{'hit':'up','clear':True},'contentX':100,'contentY':100},
            {'position':.38,'sunken':True,'lastPress':{'bar':'vertical','hit':'up','button':1},'contentX':100,'contentY':80},
            {'position':.38,'sunken':False,'contentX':100,'contentY':80})
    def test_valid_pressure_passes(self):
        self.assertTrue(L.judge(*self.samples(),'vertical','up')['passed'])
    def test_motion_alone_is_not_pressure(self):
        b,h,r=self.samples();h['sunken']=False;got=L.judge(b,h,r,'vertical','up')
        self.assertTrue(got['motion_ok']);self.assertFalse(got['passed'])
    def test_wrong_axis_movement_invalidates_probe(self):
        b,h,r=self.samples();h['contentX']=99;got=L.judge(b,h,r,'vertical','up')
        self.assertIsNone(got['motion_ok']);self.assertIn('other_axis_moved',got['invalid_reasons'])
    def test_wrong_press_hit_is_not_failure_of_arrow(self):
        b,h,r=self.samples();h['lastPress']['hit']='upPage';got=L.judge(b,h,r,'vertical','up')
        self.assertEqual(got['status'],'invalid_target');self.assertIsNone(got['passed'])
    def test_wrong_mouse_receiver_invalidates_probe(self):
        b,h,r=self.samples();h['lastPress']['bar']='horizontal';self.assertFalse(L.judge(b,h,r,'vertical','up')['valid_target'])
    def test_stuck_pressed_state_fails(self):
        b,h,r=self.samples();r['sunken']=True;self.assertFalse(L.judge(b,h,r,'vertical','up')['passed'])
    def test_four_valid_targets_required(self):
        row=L.judge(*self.samples(),'vertical','up')
        self.assertEqual(L.summarize([row])['verdict'],'partial')
        self.assertFalse(L.summarize([row.copy() for _ in range(4)])['all_passed'])
        all_rows=[dict(row,orientation=o,arrow=a) for o in ('vertical','horizontal') for a in ('up','down')]
        self.assertTrue(L.summarize(all_rows)['all_passed'])
    def test_invalid_target_yields_2_not_certified_failure(self):
        s=L.summarize([{'status':'invalid_target','valid_target':False}]);self.assertEqual(L.exit_code(s),2)
    def test_unavailable_is_77(self):
        s=L.summarize([{'status':'not_available'}]);self.assertEqual(L.exit_code(s),77)
    def test_known_overlap_rectangle(self):
        got=L.intersect_rect({'x':590,'y':64,'width':18,'height':282},{'x':12,'y':328,'width':596,'height':18})
        self.assertEqual(got,{'x':590,'y':328,'width':18,'height':18})
    def test_nonfinite_or_outside_point_refused(self):
        r={'x':0,'y':0,'width':18,'height':18}
        for pt in ({'x':18,'y':2},{'x':float('nan'),'y':0},None):self.assertFalse(L.point_in_rect(pt,r))
if __name__=='__main__':unittest.main()
