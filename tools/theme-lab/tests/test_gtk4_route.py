# SPDX-License-Identifier: GPL-3.0-or-later
import json
import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import backend
from gtk4_route import adapter_capability, command, control_capability, renderer, verify
from test_backend import ROOT, model


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT, prefix='.qa-gtk4-route-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        data = model(); data['selected_family'] = 'gtk4'
        data['recipes']['gtk4']['visible_controls'] = 1
        path = self.folder / 'input.json'
        # Deliberately different whitespace from the normalized saved scene.
        path.write_text(json.dumps(data, indent=4))
        self.model, self.digest = backend.project(path)
        self.kde = ROOT / 'colors/DomainOS-SR10.4.colors'

    def generate(self):
        inventory = {'families': {family: {'available': True, 'native_gallery': True}
                                 for family in backend.FAMILIES}}
        with patch('backend.probe', return_value=inventory):
            return backend.generate(ROOT, self.folder / 'output', self.model,
                                    self.digest, self.kde, family_scope=['gtk4'])

    def test_route_uses_saved_scene_digest_and_verified_snapshot(self):
        result = self.generate()
        self.assertEqual(result['status'], 'partially_generated')
        self.assertEqual(list(result['families']), ['gtk4'])
        receipt = result['families']['gtk4']
        self.assertEqual(receipt['translated_controls'], ['push'])
        self.assertEqual(receipt['adapter_capability']['coverage'], '5/16')
        self.assertEqual(receipt['adapter_capability']['supported_controls'],
                         ['push', 'toggle', 'check', 'scroll_h', 'scroll_v'])
        self.assertEqual(receipt['source_project_sha256'], self.digest)
        self.assertNotEqual(receipt['preview_project_sha256'], self.digest)
        verify(ROOT, receipt, self.model)
        argv = command(ROOT, receipt, self.model, self.folder / 'events', self.kde)
        self.assertIn('preview_gtk4.py', argv[2])
        _, saved_digest = backend.project(Path(argv[argv.index('--project') + 1]))
        self.assertEqual(saved_digest, receipt['preview_project_sha256'])
        self.assertFalse(receipt['recipe_applied'])

    def test_check_scene_uses_supported_button_subset(self):
        self.model['recipes']['gtk4']['visible_controls'] = 4
        result = self.generate()
        self.assertEqual(result['status'], 'partially_generated')
        self.assertEqual(result['families']['gtk4']['translated_controls'], ['check'])
        self.assertTrue((Path(result['generation_dir']) / 'gtk4-snapshot').exists())

    def test_toggle_route_declares_and_verifies_explicit_capability(self):
        self.model['recipes']['gtk4']['visible_controls']=3
        receipt=self.generate()['families']['gtk4']
        self.assertEqual(receipt['translated_controls'],['push','toggle'])
        argv=command(ROOT,receipt,self.model,self.folder/'events',self.kde)
        self.assertIn('--private-toggle-session',argv)
        verify(ROOT,receipt,self.model)

    def test_scrollbar_route_declares_native_geometry_and_both_preview_origins(self):
        self.model['recipes']['gtk4']['visible_categories'] = 1 << 2
        self.model['recipes']['gtk4']['visible_controls'] = (1 << 10) | (1 << 11)
        receipt = self.generate()['families']['gtk4']
        self.assertEqual(receipt['translated_controls'], ['scroll_h', 'scroll_v'])
        self.assertIn('not available in GTK4', receipt['arrows'])
        argv = command(ROOT, receipt, self.model, self.folder / 'events', self.kde)
        self.assertIn('--private-scrollbar-session', argv)
        self.assertNotIn('--private-toggle-session', argv)
        verify(ROOT, receipt, self.model)

    def test_scrollbar_route_filters_mixed_catalog_without_changing_model(self):
        self.model['recipes']['gtk4']['visible_categories'] = (1 << 0) | (1 << 2)
        self.model['recipes']['gtk4']['visible_controls'] = 1 | (1 << 10)
        self.model['recipes']['gtk4']['selected_control'] = 10
        before = json.loads(json.dumps(self.model))
        result = self.generate()
        self.assertEqual(result['status'], 'partially_generated')
        self.assertEqual(result['families']['gtk4']['translated_controls'],
                         ['scroll_h', 'scroll_v'])
        self.assertEqual(self.model, before)

    def test_all_controls_refuses_visible_unsupported_selection(self):
        self.model['recipes']['gtk4']['visible_categories'] = 31
        self.model['recipes']['gtk4']['visible_controls'] = (1 << 16) - 1
        self.model['recipes']['gtk4']['selected_control'] = 12
        result = self.generate()
        self.assertEqual(result['status'], 'unavailable')
        self.assertIn("'arrow' sem tradutor DomainOS", result['reason'])
        self.assertIn('5/16', result['reason'])
        self.assertIn('galeria GTK4 ampla', result['reason'])

    def test_hidden_unsupported_selection_can_route_visible_supported_subset(self):
        self.model['recipes']['gtk4']['visible_categories'] = 31
        self.model['recipes']['gtk4']['visible_controls'] = 1
        self.model['recipes']['gtk4']['selected_control'] = 12
        receipt = self.generate()['families']['gtk4']
        self.assertEqual(receipt['translated_controls'], ['push'])

    def test_adapter_capability_is_exact_and_separate_from_current_receipt(self):
        capability = adapter_capability()
        self.assertEqual(capability['catalog_count'], 16)
        self.assertEqual(capability['supported_count'], 5)
        self.assertEqual(capability['coverage'], '5/16')
        self.assertEqual(capability['unsupported_controls'],
                         ['radio', 'entry', 'combo', 'spin', 'text', 'scale_h',
                          'scale_v', 'arrow', 'progress', 'list', 'frame'])
        self.assertIn('not a DomainOS translation', capability['scope'])

    def test_catalog_keeps_all_sixteen_rows_with_explicit_status(self):
        rows = adapter_capability()['controls']
        self.assertEqual(len(rows), 16)
        self.assertEqual([row['index'] for row in rows], list(range(16)))
        self.assertEqual([row['id'] for row in rows],
                         adapter_capability()['catalog_controls'])
        for row in rows:
            with self.subTest(control=row['id']):
                translated = row['id'] in {
                    'push', 'toggle', 'check', 'scroll_h', 'scroll_v'}
                self.assertEqual(row['status'],
                                 'translated' if translated else 'unavailable')
                self.assertEqual(row['renderer'],
                                 ('buttons' if row['id'] in {'push','toggle','check'}
                                  else 'scrollbar' if row['id'] in {'scroll_h','scroll_v'}
                                  else None))

    def test_every_visible_catalog_selection_routes_or_refuses_explicitly(self):
        self.model['recipes']['gtk4']['visible_categories'] = 31
        self.model['recipes']['gtk4']['visible_controls'] = (1 << 16) - 1
        for control in range(16):
            self.model['recipes']['gtk4']['selected_control'] = control
            identifier = adapter_capability()['catalog_controls'][control]
            with self.subTest(control=identifier):
                if control <= 2:
                    self.assertEqual(renderer(self.model), 'buttons')
                elif control in (10, 11):
                    self.assertEqual(renderer(self.model), 'scrollbar')
                else:
                    with self.assertRaisesRegex(
                            backend.Unavailable,
                            f"{identifier!r} sem tradutor DomainOS"):
                        renderer(self.model)

    def test_unknown_control_is_not_added_to_catalog(self):
        with self.assertRaisesRegex(ValueError, 'unknown'):
            control_capability('invented')

    def test_only_untranslated_controls_reports_precise_limit(self):
        self.model['recipes']['gtk4']['visible_controls'] = 1 << 3
        result = self.generate()
        self.assertEqual(result['status'], 'unavailable')
        self.assertIn('nenhum controle visível possui tradutor DomainOS', result['reason'])
        self.assertIn('5/16', result['reason'])

    def test_launch_refuses_corrupted_artifact(self):
        receipt = self.generate()['families']['gtk4']
        Path(receipt['css']).write_text('corrupted')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            command(ROOT, receipt, self.model, self.folder / 'events', self.kde)

    def test_launch_refuses_falsified_adapter_coverage(self):
        receipt = self.generate()['families']['gtk4']
        receipt['adapter_capability']['supported_count'] = 16
        with self.assertRaisesRegex(ValueError, 'capability metadata mismatch'):
            command(ROOT, receipt, self.model, self.folder / 'events', self.kde)

    def test_backend_preview_dispatches_verified_worker_and_tracks_exit(self):
        self.generate()
        child = MagicMock(); child.pid = 12345
        child.wait.return_value = 0; child.poll.return_value = 0
        with patch('backend.private_namespace', return_value={'fixture': True}), \
             patch('backend.subprocess.Popen', return_value=child) as launch, redirect_stdout(io.StringIO()):
            proof = backend.preview(ROOT, self.folder / 'output', self.model,
                                    self.digest, self.kde, 'gtk4')
        argv = launch.call_args.args[0]
        self.assertTrue(argv[2].endswith('/preview_gtk4.py'))
        self.assertIn('--snapshot', argv)
        self.assertEqual(proof['status'], 'closed')
        self.assertEqual(proof['translated_controls'], ['push'])
        self.assertFalse(proof['recipe_applied'])
        child.wait.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
