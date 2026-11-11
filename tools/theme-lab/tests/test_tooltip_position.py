# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tooltip_position import outside_control


class PositionTests(unittest.TestCase):
    def test_prefer_below_and_above_at_bottom(self):
        self.assertEqual(outside_control((540,340,120,36),(354,84),(0,0,940,700)),(423,382))
        self.assertEqual(outside_control((540,640,120,36),(354,84),(0,0,940,700)),(423,550))

    def test_side_when_vertical_space_does_not_exist(self):
        self.assertEqual(outside_control((300,0,100,700),(200,80),(0,0,940,700)),(406,310))

    def test_offset_monitor_and_all_corners(self):
        monitor=(940,-100,940,700)
        for bx,by in ((940,-100),(1750,-100),(940,550),(1750,550)):
            position=outside_control((bx,by,120,36),(354,84),monitor)
            self.assertIsNotNone(position)
            x,y=position
            self.assertTrue(940<=x<=1880-354 and -100<=y<=600-84)
            self.assertTrue(x+354<=bx or bx+120<=x or y+84<=by or by+36<=y)

    def test_no_space_is_explicit_not_overlap(self):
        self.assertIsNone(outside_control((0,0,940,700),(354,84),(0,0,940,700)))
        self.assertIsNone(outside_control((0,0,120,36),(950,84),(0,0,940,700)))


if __name__=='__main__': unittest.main()
