#!/usr/bin/env python3
"""Native bridge rejection boundaries; run only in the private Xvfb fixture."""
import os
from pathlib import Path
import sys
import subprocess
import time
import unittest
from unittest.mock import Mock, patch

if os.environ.get('T04_PRIVATE_PRESSED_PROBE') != '1':
    raise SystemExit('Use the private GTK2 Xvfb fixture.')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk
from gtk2_press_bridge import Gtk2PressBridge

Gtk.init([])
ROOT = Path(__file__).resolve().parents[3]


class BridgeTests(unittest.TestCase):
    @staticmethod
    def settle():
        deadline = time.monotonic() + .1
        while time.monotonic() < deadline:
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            time.sleep(.005)

    def test_missing_bridge_is_explicit(self):
        with self.assertRaisesRegex(ValueError, 'ausente'):
            Gtk2PressBridge(ROOT / 'missing-test-root')

    def test_abi_rejected_before_binding_native_setters(self):
        library = Mock()
        library.theme_lab_gtk2_press_abi.return_value = 0
        with patch('gtk2_press_bridge.C.CDLL', return_value=library):
            with self.assertRaisesRegex(ValueError, 'incompatível'):
                Gtk2PressBridge(ROOT)
        self.assertFalse(library.theme_lab_gtk2_press_set.called)

    def test_toggle_and_label_are_rejected_without_type_substitution(self):
        bridge = Gtk2PressBridge(ROOT)
        for widget in (Gtk.ToggleButton(label='Toggle'), Gtk.Label(label='Label')):
            try:
                with self.assertRaisesRegex(ValueError, 'só aceita GtkButton'):
                    bridge.bind(widget)
            finally:
                widget.destroy()

    def test_insensitive_button_and_non_boolean_are_rejected(self):
        bridge = Gtk2PressBridge(ROOT)
        button = Gtk.Button(label='Push')
        try:
            setter = bridge.bind(button)
            with self.assertRaisesRegex(ValueError, 'booleano'):
                setter(1)
            button.set_sensitive(False)
            with self.assertRaisesRegex(ValueError, r'\(-5\)'):
                setter(True)
            self.assertEqual(button.get_state(), Gtk.StateType.INSENSITIVE)
        finally:
            button.destroy()

    def test_destroyed_or_released_binding_never_calls_native_setter(self):
        bridge = Gtk2PressBridge(ROOT)
        button = Gtk.Button(label='Push')
        setter = bridge.bind(button)
        button.destroy()
        self.assertTrue(setter.closed)
        with self.assertRaisesRegex(ValueError, 'fechado ou destruído'):
            setter(True)
        button = Gtk.Button(label='Push')
        setter = bridge.bind(button)
        setter.close()
        with self.assertRaisesRegex(ValueError, 'fechado ou destruído'):
            setter(False)
        button.destroy()

    def test_reset_while_pointer_inside_preserves_native_hover_policy(self):
        bridge = Gtk2PressBridge(ROOT)
        window = Gtk.Window()
        window.set_title('T04 private GTK2 bridge reset hover')
        button = Gtk.Button(label='Reset')
        button.set_size_request(180, 60)
        window.add(button)
        settings = Gtk.Settings.get_default()
        original_mode = settings.get_property('gtk-touchscreen-mode')
        setter = bridge.bind(button)
        try:
            window.show_all()
            self.settle()
            xid = subprocess.check_output(['xdotool', 'search', '--name',
                '^T04 private GTK2 bridge reset hover$'], text=True, timeout=3).strip()
            self.assertTrue(xid.isdecimal())
            subprocess.run(['xdotool', 'mousemove', '--window', xid, '80', '25'],
                           check=True, timeout=3)
            self.settle()
            for touchscreen, expected in ((False, Gtk.StateType.PRELIGHT),
                                           (True, Gtk.StateType.NORMAL)):
                settings.set_property('gtk-touchscreen-mode', touchscreen)
                setter(True)
                self.assertEqual(button.get_state(), Gtk.StateType.ACTIVE)
                setter(False)
                self.assertEqual(button.get_state(), expected)
        finally:
            settings.set_property('gtk-touchscreen-mode', original_mode)
            setter.close()
            window.destroy()


if __name__ == '__main__':
    unittest.main()
