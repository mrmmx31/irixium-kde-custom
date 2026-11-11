#!/usr/bin/env python3
"""Native scene ownership during container transfer, separate and GtkPlug."""
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

if os.environ.get('T04_PRIVATE_PRESSED_PROBE') != '1':
    raise SystemExit('Use the private GTK2 Xvfb fixture.')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk
from gtk2_press_bridge import Gtk2PressBridge
from native_scene_gtk2 import ScrollbarScene

Gtk.init([])
ROOT = Path(__file__).resolve().parents[3]


def settle():
    deadline = time.monotonic() + .15
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(.005)


def model():
    return {'recipes': {'gtk2': {'visible_controls': 1, 'selected_control': 0,
        'edit_state': 1, 'sizes': [[220, 80]] + [[0, 0] for _ in range(15)]}}}


class PressedSceneTests(unittest.TestCase):
    def exercise(self, embedded):
        subprocess.run(['xdotool', 'mousemove', '700', '500'], check=True, timeout=3)
        bridge = Gtk2PressBridge(ROOT)
        host = None
        if embedded:
            host = Gtk.Window()
            socket = Gtk.Socket()
            host.add(socket)
            host.show_all()
            settle()
            xid = socket.get_id()
        else:
            xid = None
        old = ScrollbarScene(Gtk, model(), embed_window=xid, press_bridge=bridge)
        candidate = None
        try:
            settle()
            self.assertEqual(old.widgets[0].get_state(), Gtk.StateType.ACTIVE)
            size = old.widgets[0].get_allocation()
            self.assertEqual([size.width, size.height], [220, 80])
            candidate = ScrollbarScene(Gtk, model(), show=False, press_bridge=bridge)
            staging = candidate.window
            staging.remove(candidate.fixed)
            old.window.remove(old.fixed)
            old.window.add(candidate.fixed)
            candidate.window = old.window
            staging.destroy()
            old.fixed.destroy()
            candidate.window.show_all()
            settle()
            self.assertTrue(old.press_demos[0].closed)
            self.assertTrue(old.press_demos[0].set_visual.closed)
            self.assertFalse(candidate.press_demos[0].closed)
            self.assertEqual(candidate.widgets[0].get_state(), Gtk.StateType.ACTIVE)
            size = candidate.widgets[0].get_allocation()
            self.assertEqual([size.width, size.height], [220, 80])
            candidate.window.destroy()
            settle()
            self.assertTrue(candidate.press_demos[0].closed)
            self.assertTrue(candidate.press_demos[0].set_visual.closed)
        finally:
            old.window.destroy()
            if candidate is not None:
                candidate.window.destroy()
            if host is not None:
                host.destroy()
            settle()

    def test_separate_transfer_and_close(self):
        self.exercise(False)

    def test_embedded_transfer_and_close(self):
        self.exercise(True)

    def test_rejected_bridge_destroys_uncommitted_scene(self):
        class RejectedBridge:
            def bind(self, _button):
                raise ValueError('Native binding rejected')
        before = set(Gtk.Window.list_toplevels())
        with self.assertRaisesRegex(ValueError, 'Native binding rejected'):
            ScrollbarScene(Gtk, model(), press_bridge=RejectedBridge())
        settle()
        self.assertEqual(set(Gtk.Window.list_toplevels()), before)


if __name__ == '__main__':
    unittest.main()
