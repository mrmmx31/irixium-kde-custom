#!/usr/bin/env python3
"""Ownership, cleanup and failed construction of the pressure controller."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtk2_pressed_state import PressedButtonDemo


class Button:
    def __init__(self):
        self.handlers = {}
        self.next_id = 0

    def connect(self, signal, callback):
        self.next_id += 1
        self.handlers[self.next_id] = (signal, callback)
        return self.next_id

    connect_after = connect

    def disconnect(self, handler):
        del self.handlers[handler]

    def emit(self, signal):
        for name, callback in list(self.handlers.values()):
            if name == signal:
                if signal in ('destroy', 'released'):
                    callback(self)
                else:
                    callback(self, None)


class PressedStateTests(unittest.TestCase):
    def test_hover_reapplies_then_close_disconnects_and_restores_once(self):
        button, states = Button(), []
        demo = PressedButtonDemo(button, states.append)
        button.emit('enter-notify-event')
        button.emit('leave-notify-event')
        demo.close()
        demo.close()
        button.emit('enter-notify-event')
        self.assertEqual(states, [True, True, True, False])
        self.assertEqual(button.handlers, {})

    def test_destroy_does_not_call_native_setter_on_dying_widget(self):
        button, states = Button(), []
        demo = PressedButtonDemo(button, states.append)
        button.emit('destroy')
        demo.close()
        self.assertEqual(states, [True])
        self.assertEqual(button.handlers, {})

    def test_native_release_reapplies_visual_state_without_emitting_input(self):
        button, states = Button(), []
        demo = PressedButtonDemo(button, states.append)
        button.emit('released')
        self.assertEqual(states, [True, True])
        demo.close()
        button.emit('released')
        self.assertEqual(states, [True, True, False])

    def test_rejected_native_setter_does_not_leave_handlers(self):
        button, states = Button(), []
        def setter(enabled):
            states.append(enabled)
            if enabled:
                raise ValueError('Unsupported native ABI')
        with self.assertRaisesRegex(ValueError, 'Unsupported native ABI'):
            PressedButtonDemo(button, setter)
        self.assertEqual(button.handlers, {})
        self.assertEqual(states, [True, False])

    def test_hover_setter_failure_stops_the_demonstration(self):
        button, states = Button(), []
        def setter(enabled):
            states.append(enabled)
            if len(states) == 2:
                raise RuntimeError('Native setter unavailable')
        demo = PressedButtonDemo(button, setter)
        with self.assertRaisesRegex(RuntimeError, 'Native setter unavailable'):
            button.emit('enter-notify-event')
        self.assertTrue(demo.closed)
        self.assertEqual(button.handlers, {})
        self.assertEqual(states, [True, True, False])

    def test_construction_error_is_preserved_when_reset_also_fails(self):
        button = Button()
        def setter(enabled):
            raise ValueError('Initial error' if enabled else 'Reset error')
        with self.assertRaisesRegex(ValueError, 'Initial error') as raised:
            PressedButtonDemo(button, setter)
        self.assertEqual(str(raised.exception.__cause__), 'Reset error')
        self.assertEqual(button.handlers, {})


if __name__ == '__main__':
    unittest.main()
