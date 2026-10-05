# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the diagnostic harness; synthetic JS is not a native Qt test."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import preview_qtquick_pressure as P
from test_qtquick_pressure import FIXTURE

class PressureProbe(unittest.TestCase):
    def test_instrumentation_keeps_original_source(self):
        original=FIXTURE.decode();result=P.instrument(original)
        self.assertEqual(result.replace(P.INSTRUMENT,'',1),original)
    def test_unknown_or_ambiguous_qml_is_refused(self):
        for text in ('Item {}',FIXTURE.decode()*2):
            with self.assertRaises(P.Failure):P.instrument(text)
    def test_no_unsupported_subcontrol_rect_queries(self):
        self.assertNotIn('subControlRect(',P.INSTRUMENT)
        self.assertIn('style.hitTest',P.INSTRUMENT)
        self.assertIn('Math.min(2048',P.INSTRUMENT)
    def test_probe_observes_action_and_render_state_separately(self):
        for key in ('position:position','sunken:style.sunken','mousePressed:mouseArea.pressed'):
            self.assertIn(key,P.INSTRUMENT)
        s=(ROOT/'tools/preview_qtquick_pressure.py').read_text()
        for key in ('motion_ok','held_sunken','released_sunken'):self.assertIn(key,s)
    def test_test_mode_does_not_silently_force_offscreen(self):
        s=(ROOT/'tools/preview_qtquick_pressure.py').read_text()
        self.assertIn("if a.offscreen:\n            os.environ['QT_QPA_PLATFORM']='offscreen'",s)
        self.assertNotIn("if a.testar:\n            os.environ['QT_QPA_PLATFORM']",s)
    def test_styles_and_original_vs_temporary_are_exposed(self):
        s=(ROOT/'tools/preview_qtquick_pressure.py').read_text()
        for t in ("choices=('Fusion','Breeze','kvantum')",'on_disk_already_patched',"'temporary_fix':not a.original"):
            self.assertIn(t,s)
    def test_hit_scan_finds_real_arrow_centers_in_two_orientations(self):
        if not shutil.which('node'):self.skipTest('node absent; synthetic scan not executed')
        body=P.INSTRUMENT.split('property string irixProbeGeometry: {',1)[1].rsplit('}',1)[0]
        for vertical in (True,False):
            width,height=(18,230) if vertical else (445,18)
            setup=f'''const width={width},height={height};
const Qt={{Vertical:1,Horizontal:2}},orientation={1 if vertical else 2};
const style={{width,height,hitTest(x,y){{const k=orientation===1?y:x;
return k<18?"up":k>=(orientation===1?height:width)-18?"down":"handle";}}}};
console.log((function(){{{body}}})());'''
            p=subprocess.run(['node','-e',setup],capture_output=True,text=True,timeout=10,check=True)
            result=json.loads(p.stdout)
            self.assertEqual(result['up'],{'x':9,'y':8} if vertical else {'x':8,'y':9})
            self.assertEqual(result['down'],{'x':9,'y':220} if vertical else {'x':435,'y':9})
    def test_source_does_not_modify_system_or_restart_processes(self):
        s=(ROOT/'tools/preview_qtquick_pressure.py').read_text()
        for forbidden in ('sudo','pkexec','killall','systemctl','os.replace('):self.assertNotIn(forbidden,s)
        self.assertIn('TemporaryDirectory',s)

if __name__=='__main__':unittest.main()
