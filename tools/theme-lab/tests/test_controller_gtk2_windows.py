# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from controller_gtk2_windows import native_windows


class WindowObservationTests(unittest.TestCase):
    def test_queries_only_root_and_known_canvas(self):
        calls=[]
        def query(argv,**kwargs):
            calls.append(argv)
            if '-children' in argv:
                window='0x12' if '-root' in argv else '0x34'
                return SimpleNamespace(returncode=0,stdout=f'  {window} "Theme Lab — GTK2 nativo": 640x420')
            return SimpleNamespace(returncode=0,stdout='Map State: IsViewable')
        with patch('controller_gtk2_windows.subprocess.run',side_effect=query):
            self.assertEqual(native_windows(lambda:{'canvas_window':0x99},{}),['0x12','0x34'])
        self.assertIn(['xwininfo','-id','0x99','-children'],calls)
        self.assertFalse(any('-tree' in argv or 'search' in argv for argv in calls))

    def test_missing_canvas_does_not_query_display(self):
        with patch('controller_gtk2_windows.subprocess.run') as query:
            self.assertEqual(native_windows(lambda:{},{}),[])
            query.assert_not_called()

    def test_hidden_window_not_used_as_paint_evidence(self):
        def query(argv,**kwargs):
            return SimpleNamespace(returncode=0,stdout='  0x12 "Theme Lab — GTK2 nativo": 640x420' if '-children' in argv else 'Map State: IsUnMapped')
        with patch('controller_gtk2_windows.subprocess.run',side_effect=query):
            self.assertEqual(native_windows(lambda:{'canvas_window':0x99},{}),[])

    def test_failed_parent_query_refuses_candidate_list(self):
        with patch('controller_gtk2_windows.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')):
            self.assertEqual(native_windows(lambda:{'canvas_window':0x99},{}),[])


if __name__=='__main__':unittest.main()
