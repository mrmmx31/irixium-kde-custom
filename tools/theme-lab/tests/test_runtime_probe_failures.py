#!/usr/bin/python3
"""A failed runtime query must not certify it or hide other families."""
import importlib.util
import json
from pathlib import Path
import subprocess
import threading
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'backend.py'
spec = importlib.util.spec_from_file_location('runtime_failure_backend', SOURCE)
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


class RuntimeProbeFailures(unittest.TestCase):
    def test_six_independent_queries_overlap_without_omitting_families(self):
        barrier = threading.Barrier(6, timeout=5)
        threads = set()
        lock = threading.Lock()

        def query(command, **kwargs):
            with lock:
                threads.add(threading.get_ident())
            barrier.wait()
            return subprocess.CompletedProcess(command, 0,
                json.dumps({'available': True, 'version': 'artificial'}), '')

        with patch.object(backend.subprocess, 'run', side_effect=query), \
                patch.object(backend, 'package_version', return_value=None), \
                patch.object(backend.ctypes.util, 'find_library', return_value=None):
            result = backend.probe(backend.ROOT)
        self.assertEqual(len(threads), 6)
        self.assertEqual(set(result['families']), set(backend.FAMILIES))
        for family in ('gtk2', 'gtk3', 'gtk4', 'qt5', 'qt6'):
            self.assertTrue(result['families'][family]['available'])
        self.assertFalse(result['gui_started'])
        self.assertEqual(result['families']['gtk2']['adapter'], 'gtk2_private_recipe')
        self.assertFalse(result['families']['gtk2']['recipe_applied'])
        self.assertEqual(result['families']['gtk4']['adapter'],
                         'gtk4_private_partial_recipe')
        self.assertEqual(result['families']['gtk4']['translated_controls'],
                         ['push', 'toggle', 'check', 'scroll_h', 'scroll_v'])
        self.assertFalse(result['families']['gtk1']['available'])
        self.assertIn('galeria nativa', result['families']['gtk1']['reason'])
        self.assertFalse(result['families']['gtk5']['available'])
        self.assertIn('não é simulado', result['families']['gtk5']['reason'])

    def test_python_timeout_and_launch_error_are_unconfirmed(self):
        for error, status in ((subprocess.TimeoutExpired('probe', 10), 'timeout'),
                              (OSError('cannot launch'), 'error')):
            with self.subTest(status=status), patch.object(backend.subprocess, 'run', side_effect=error):
                result = backend.python_probe('unused')
                self.assertFalse(result['available'])
                self.assertEqual(result['probe_status'], status)
                self.assertTrue(result['reason'])

    def test_invalid_response_does_not_certify_runtime(self):
        for output in ('bad json', '[]', '{}', '{"available": "yes"}'):
            with self.subTest(output=output), patch.object(backend.subprocess, 'run',
                    return_value=subprocess.CompletedProcess('probe', 0, output, '')):
                result = backend.python_probe('unused')
                self.assertFalse(result['available'])
                self.assertEqual(result['probe_status'], 'invalid_response')

    def test_optional_package_version_timeout_has_no_fabricated_version(self):
        with patch.object(backend.shutil, 'which', return_value='/usr/bin/dpkg-query'), \
                patch.object(backend.subprocess, 'run', side_effect=subprocess.TimeoutExpired('dpkg', 3)):
            self.assertIsNone(backend.package_version('libxm4'))

    def test_gtk3_and_gtk4_timeout_leave_full_inventory_and_gtk2_available(self):
        calls = []

        def query(command, **kwargs):
            calls.append(command)
            if '--verificar' in command or 'libgtk-3.so.0' in command[-1]:
                raise subprocess.TimeoutExpired(command, 10)
            return subprocess.CompletedProcess(command, 0,
                json.dumps({'available': True, 'version': 'artificial'}), '')

        with patch.object(backend.subprocess, 'run', side_effect=query), \
                patch.object(backend, 'package_version', return_value=None), \
                patch.object(backend.ctypes.util, 'find_library', return_value=None):
            result = backend.probe(backend.ROOT)
        self.assertEqual(set(result['families']), set(backend.FAMILIES))
        self.assertTrue(result['families']['gtk2']['available'])
        for family in ('gtk3', 'gtk4'):
            self.assertFalse(result['families'][family]['available'])
            self.assertEqual(result['families'][family]['probe_status'], 'timeout')
            self.assertFalse(result['families'][family]['recipe_applied'])
        self.assertTrue(result['families']['qt5']['available'])
        self.assertTrue(result['families']['qt6']['available'])
        self.assertEqual(len(calls), 6)
        self.assertFalse(result['gui_started'])

    def test_unavailable_gtk1_and_gtk5_keep_selection_and_report_exact_limit(self):
        from test_backend import model
        for family, reason in (('gtk1', 'GTK1 não instalado'),
                               ('gtk5', 'não é simulado')):
            with self.subTest(family=family), tempfile.TemporaryDirectory(
                    dir=backend.ROOT, prefix='.qa-gtk-unavailable-') as directory:
                data = model()
                data['selected_family'] = family
                before = json.loads(json.dumps(data))
                capabilities = {'families': {
                    name: {'available': name not in ('gtk1', 'gtk5'),
                           'native_gallery': name not in ('gtk1', 'gtk5'),
                           'reason': ('GTK1 não instalado; sem galeria nativa.'
                                      if name == 'gtk1' else
                                      'Nenhum runtime ou galeria GTK5 disponível; não é simulado.')}
                    for name in backend.FAMILIES}}
                with patch.object(backend, 'probe', return_value=capabilities):
                    result = backend.generate(backend.ROOT, Path(directory) / 'output',
                                              data, 'a' * 64, Path(directory) / 'kdeglobals',
                                              family_scope=[family])
                self.assertEqual(result['status'], 'unavailable')
                self.assertIn(reason, result['reason'])
                self.assertEqual(data, before)


if __name__ == '__main__':
    unittest.main()
