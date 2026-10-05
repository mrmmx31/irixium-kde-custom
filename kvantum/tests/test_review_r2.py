# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression contracts for review reporting/input, not native acceptance."""
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import native_gallery_input as N
import review_integrated as R

class ReviewR2(unittest.TestCase):
    def test_walk_ends_at_center_and_stays_inside(self):
        for x,y,w,h in ((10,20,150,24),(0,0,3,3),(3,5,80,19)):
            points=N.interior_walk(x,y,w,h)
            self.assertGreaterEqual(len(points),8)
            self.assertEqual(points[-1],(x+(w-1)//2,y+(h-1)//2))
            self.assertTrue(all(x<=px<x+w and y<=py<y+h for px,py in points))
            self.assertGreater(len(set(points)),1)
    def test_invalid_area_refused(self):
        for w,h in ((2,5),(5,1),(0,0),(-1,5)):
            with self.assertRaises(ValueError):N.interior_walk(0,0,w,h)
    def test_skips_not_passes(self):
        self.assertEqual(R.unittest_counts('Ran 282 tests in 8.282s\n\nOK (skipped=7)\n'),
                         {'run':282,'skipped':7,'passed':275})
    def test_no_skips(self):
        self.assertEqual(R.unittest_counts('Ran 42 tests in 0.602s\n\nOK\n'),
                         {'run':42,'skipped':0,'passed':42})
    def test_failed_summary_does_not_invent_pass_count(self):
        self.assertEqual(R.unittest_counts('Ran 2 tests in 1s\nFAILED (errors=1)\n')['passed'],None)
    def test_unrelated_log_has_no_count(self):
        self.assertIsNone(R.unittest_counts('{"passed":true}'))
    def test_installed_failure_and_temporary_success_kept_separate(self):
        d={'probes':{}}
        for name,verdict,code,change in (('quick_installed','failed_pressure',1,False),('quick_temporary_fix','passed',0,True)):
            d['probes'][name]={'returncode':code,'result':{'assessment':{'verdict':verdict,'all_passed':code==0},
                'temporary_fix':name.endswith('_fix'),'checks':[{'arrow_pixels_changed':change} for _ in range(4)]}}
        r=R.arrow_paths(d)
        self.assertEqual(r['quick_installed']['assessment']['verdict'],'failed_pressure')
        self.assertEqual(r['quick_installed']['pixel_changes'],0)
        self.assertEqual(r['quick_temporary_fix']['pixel_changes'],4)
        self.assertTrue(r['quick_temporary_fix']['temporary_fix'])
    def test_empty_collection_is_not_a_pass(self):
        self.assertEqual(R.arrow_paths({'probes':{}}),{})
        self.assertIsNone(R.arrow_paths({'probes':{'widgets':{'returncode':77}}})['widgets']['assessment'])
    def test_html_discloses_both_paths(self):
        with tempfile.TemporaryDirectory() as d:
            doc={'status':'pendencia_setas_qtquick','tasks':[],'acceptance':[],
                'arrow_paths':{'quick_installed':{'assessment':{'verdict':'failed_pressure'},'check_count':4,'pixel_changes':0},
                               'quick_temporary_fix':{'assessment':{'verdict':'passed'},'check_count':4,'pixel_changes':4}}}
            R.write_reports(Path(d),doc);html=(Path(d)/'REVISAO-INTEGRADA.html').read_text()
            self.assertIn('quick_installed',html);self.assertIn('quick_temporary_fix',html)
            self.assertIn('0/4',html);self.assertIn('4/4',html)
    def test_summary_still_does_not_auto_install(self):
        self.assertTrue(all('corrigir-pressao' not in ' '.join(t[1]) for t in R.tasks(True)))
    def test_input_path_does_not_force_a_menu_action(self):
        s=inspect.getsource(N.GalleryInput.menu_action)
        self.assertNotIn('.trigger(',s);self.assertNotIn('.setActiveAction(',s)
        self.assertIn('QTest.mouseMove(window,',s);self.assertIn('QTest.mouseClick(window,',s)
    def test_click_geometry_uses_actual_style(self):
        s=inspect.getsource(N.GalleryInput.toggle)
        self.assertIn('SE_CheckBoxClickRect',s);self.assertIn('SE_RadioButtonClickRect',s)
        self.assertIn('SE_CheckBoxIndicator',s);self.assertIn('SE_RadioButtonIndicator',s)
        self.assertNotIn('.setChecked(',s)
    def test_mouse_and_keyboard_checks_are_independent(self):
        s=(ROOT/'tools/preview_selection.py').read_text()
        self.assertIn('before_space=',s)
        self.assertIn("isChecked()!=before_space",s)
    def test_observer_does_not_consume_events(self):
        s=inspect.getsource(N.GalleryInput._watch)
        self.assertIn('return False',s);self.assertNotIn('return True',s)

if __name__=='__main__':unittest.main()
