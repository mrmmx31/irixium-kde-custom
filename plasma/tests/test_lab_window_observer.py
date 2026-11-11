#!/usr/bin/env python3
"""Identity and visibility guards for the non-recursive delivery observer."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('lab_launcher',
    Path(__file__).resolve().parents[1] / 'tools/abrir-laboratorio-temas.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class WindowObserverTests(unittest.TestCase):
    def observe(self, replies):
        def run(argv, **kwargs):
            self.assertGreater(kwargs['timeout'], 0)
            self.assertLessEqual(kwargs['timeout'], 2)
            self.assertEqual(kwargs['env']['LC_ALL'], 'C')
            self.assertNotIn('xdotool', argv)
            return subprocess.CompletedProcess(argv, 0, next(replies), '')
        with patch.object(lab.subprocess, 'run', side_effect=run):
            return lab.mapped_lab_windows(123)

    def test_foreign_pid_and_wrong_class_cannot_satisfy_readiness(self):
        self.assertEqual(self.observe(iter([
            '_NET_CLIENT_LIST(WINDOW): window id # 0x10, 0x20, 0x30\n',
            '_NET_WM_PID(CARDINAL) = 123\nWM_CLASS(STRING) = "x", "Other"\n',
            '_NET_WM_PID(CARDINAL) = 999\nWM_CLASS(STRING) = "x", "ThemeLab"\n',
            '_NET_WM_PID(CARDINAL) = 123\nWM_CLASS(STRING) = "x", "ThemeLab"\n',
            '  Map State: IsViewable\n',
        ])), ['0x10'])

    def test_unmapped_client_is_not_ready(self):
        self.assertEqual(self.observe(iter([
            '_NET_CLIENT_LIST(WINDOW): window id # 0x10\n',
            '_NET_WM_PID(CARDINAL) = 123\nWM_CLASS(STRING) = "x", "ThemeLab"\n',
            '  Map State: IsUnMapped\n',
        ])), [])

    def test_absent_client_list_does_not_fall_back_to_recursive_search(self):
        self.assertEqual(self.observe(iter(['_NET_CLIENT_LIST: not found.\n'])), [])

    def test_timeout_is_not_interpreted_as_terminal_app_state(self):
        with patch.object(lab.subprocess, 'run',
                          side_effect=subprocess.TimeoutExpired('xprop', 2)):
            with self.assertRaises(subprocess.TimeoutExpired):
                lab.mapped_lab_windows(123)


if __name__ == '__main__':
    unittest.main()
