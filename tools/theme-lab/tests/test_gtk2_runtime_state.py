# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('runtime_states',
    Path(__file__).resolve().parents[1] / 'gtk2_runtime_state.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class Adjustment:
    def __init__(self, value=37, lower=0, upper=100, page_size=20):
        self.value, self.lower, self.upper, self.page_size = value, lower, upper, page_size
    def get_value(self): return self.value
    def get_lower(self): return self.lower
    def get_upper(self): return self.upper
    def get_page_size(self): return self.page_size
    def set_value(self, value): self.value = value


class Widget:
    def __init__(self): self.active = False; self.adjustment = Adjustment()
    def get_active(self): return self.active
    def set_active(self, value): self.active = value
    def get_adjustment(self): return self.adjustment


class RuntimeStateTests(unittest.TestCase):
    def test_real_bounds_and_types_are_preserved_in_detached_snapshot(self):
        widgets = {1: Widget(), 8: Widget(), 10: Widget()}
        widgets[1].active = True
        widgets[8].adjustment = Adjustment(73.5, -10, 120, 0)
        scene = SimpleNamespace(widgets=widgets)
        value = m.capture(scene)
        self.assertEqual(value['toggle'], True)
        self.assertEqual(value['scale_h'], {'value': 73.5, 'lower': -10, 'upper': 120, 'page_size': 0})
        widgets[8].adjustment.value = 12
        self.assertEqual(value['scale_h']['value'], 73.5)
        m.restore(scene, value)
        self.assertEqual(widgets[8].adjustment.value, 73.5)

    def test_hidden_controls_are_kept_without_mutating_previous(self):
        previous = {'check': True, 'radio': 1, 'combo': 2,
                    'list': {'rows': ['ação🙂'], 'selected': ['0'], 'horizontal': 12, 'vertical': 0}}
        original = copy.deepcopy(previous)
        result = m.capture(SimpleNamespace(widgets={1: Widget()}), previous)
        self.assertEqual(previous, original)
        self.assertEqual(result['list'], previous['list'])
        result['list']['rows'][0] = 'new'
        self.assertEqual(previous, original)

    def test_invalid_document_is_refused_before_any_control_changes(self):
        scene = SimpleNamespace(widgets={1: Widget()})
        for extra in ({'combo': 3}, {'check': 1}, {'radio': True}, {'unknown': 0},
                      {'progress': 1.1}, {'scale_h': {'value': float('nan'), 'lower': 0, 'upper': 100, 'page_size': 0}}):
            with self.assertRaises(ValueError): m.restore(scene, {'toggle': True, **extra})
            self.assertFalse(scene.widgets[1].active)

    def test_changed_native_range_preflight_does_not_change_checkbox(self):
        scene = SimpleNamespace(widgets={1: Widget(), 10: Widget()})
        values = {'toggle': True, 'scroll_h': {'value': 20, 'lower': 0, 'upper': 100, 'page_size': 10}}
        with self.assertRaisesRegex(ValueError, 'Intervalo nativo mudou'): m.restore(scene, values)
        self.assertFalse(scene.widgets[1].active)
        self.assertEqual(scene.widgets[10].adjustment.value, 37)

    def test_list_selection_utf8_and_limits(self):
        value = {'rows': ['ação', 'São Paulo'], 'selected': ['1'], 'horizontal': 0, 'vertical': 12}
        self.assertEqual(m.validate({'list': value})['list'], value)
        for extra in ({'selected': ['01']}, {'selected': ['2']}, {'selected': ['0', '1']},
                      {'rows': ['\ud800']}, {'rows': ['a\0']}, {'horizontal': -1},
                      {'vertical': True}, {'rows': ['x' * 4097]}, {'rows': [''] * 4097}):
            with self.assertRaises(ValueError): m.validate({'list': {**value, **extra}})

    def test_range_uses_upper_minus_page_and_rejects_nonfinite(self):
        value = {'value': 80, 'lower': 0, 'upper': 100, 'page_size': 20}
        self.assertEqual(m.validate({'scroll_v': value})['scroll_v']['value'], 80)
        for extra in ({'value': 81}, {'page_size': 101}, {'lower': 101}, {'value': True},
                      {'upper': float('inf')}, {'value': 10**1000}):
            with self.assertRaises(ValueError): m.validate({'scroll_v': {**value, **extra}})


if __name__ == '__main__': unittest.main()
