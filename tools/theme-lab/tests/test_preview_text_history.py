# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest
s=importlib.util.spec_from_file_location('history',Path(__file__).resolve().parents[1]/'preview_text_history.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def state(text, cursor=0, anchor=0):return (text,cursor,anchor,None)
class HistoryTests(unittest.TestCase):
 def test_selection_unicode_branch_and_no_empty_undo(self):
  h=m.TextHistory(state('ação'));h.remember_selection(state('ação',4,0));h.push(state('São Paulo',9,9))
  self.assertEqual(h.step(-1),state('ação',4,0));self.assertIsNone(h.step(-1))
  self.assertEqual(h.step(1),state('São Paulo',9,9));h.step(-1);h.push(state('novo'))
  self.assertIsNone(h.step(1));self.assertEqual(h.step(-1),state('ação',4,0))
 def test_bounded_utf8_preserves_at_least_previous_and_current(self):
  h=m.TextHistory(state('á'),limit=3,byte_limit=12)
  for i in range(20):h.push(state('á'*i))
  self.assertEqual(len(h.states),2);self.assertEqual(h.step(-1)[0],'á'*18)
  self.assertEqual(h.step(1)[0],'á'*19)
 def test_duplicate_text_updates_selection_without_losing_redo(self):
  h=m.TextHistory(state('a'));h.push(state('b'));h.step(-1);h.push(state('a',1,1))
  self.assertEqual(h.step(1)[0],'b')
if __name__=='__main__':unittest.main()
