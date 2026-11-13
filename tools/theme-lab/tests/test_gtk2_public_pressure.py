# SPDX-License-Identifier: GPL-3.0-or-later
"""Public preflight must require the bridge before any generation mutation."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from test_backend import backend, ROOT, model


class PressurePreflightTests(unittest.TestCase):
    def proposal(self, control=0):
        data = model()
        data['selected_family'] = 'gtk2'
        data['recipes']['gtk2'].update(visible_controls=1 << control,
                                     selected_control=control, edit_state=1)
        return data

    def test_push_passes_public_preflight_only_with_verified_bridge(self):
        data = self.proposal()
        before = copy.deepcopy(data)
        with patch.object(backend, 'private_namespace', return_value={}), \
             patch('gtk2_press_bridge.Gtk2PressBridge') as bridge, \
             patch.object(backend, 'private_output', side_effect=RuntimeError('passed preflight')):
            with self.assertRaisesRegex(RuntimeError, 'passed preflight'):
                backend.preview(ROOT, Path('/unused'), data, 'hash', Path('/unused'), 'gtk2')
            bridge.assert_called_once_with(ROOT)
        self.assertEqual(data, before)

    def test_arrow_passes_same_verified_bridge_preflight(self):
        data = self.proposal(12)
        before = copy.deepcopy(data)
        with patch.object(backend, 'private_namespace', return_value={}), \
             patch('gtk2_press_bridge.Gtk2PressBridge') as bridge, \
             patch.object(backend, 'private_output', side_effect=RuntimeError('passed preflight')):
            with self.assertRaisesRegex(RuntimeError, 'passed preflight'):
                backend.preview(ROOT, Path('/unused'), data, 'hash', Path('/unused'), 'gtk2')
            bridge.assert_called_once_with(ROOT)
        self.assertEqual(data, before)

    def test_missing_bridge_refuses_before_output(self):
        with patch.object(backend, 'private_namespace', return_value={}), \
             patch('gtk2_press_bridge.Gtk2PressBridge', side_effect=ValueError('missing bridge')), \
             patch.object(backend, 'private_output') as output:
            with self.assertRaisesRegex(ValueError, 'missing bridge'):
                backend.preview(ROOT, Path('/unused'), self.proposal(), 'hash', Path('/unused'), 'gtk2')
            output.assert_not_called()

    def test_other_controls_refuse_before_loading_bridge_or_output(self):
        for control in (i for i in range(1, 16) if i != 12):
            with self.subTest(control=control), \
                 patch.object(backend, 'private_namespace', return_value={}), \
                 patch('gtk2_press_bridge.Gtk2PressBridge') as bridge, \
                 patch.object(backend, 'private_output') as output:
                with self.assertRaises(ValueError):
                    backend.preview(ROOT, Path('/unused'), self.proposal(control), 'hash', Path('/unused'), 'gtk2')
                bridge.assert_not_called()
                output.assert_not_called()


if __name__ == '__main__':
    unittest.main()
