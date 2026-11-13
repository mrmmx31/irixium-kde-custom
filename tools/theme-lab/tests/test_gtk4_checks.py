# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_backend import ROOT, model, backend
from gtk4_checks import write_check_css
from gtk4_generation import generate_snapshot, verify_snapshot
from gtk4_route import renderer, needs_check, command
from gtk4_toggle_session import button_records


class GTK4CheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.home() / 'tempia', prefix='t04-gtk4-check-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.project = model()
        self.project['selected_family'] = 'gtk4'
        recipe = self.project['recipes']['gtk4']
        recipe['visible_controls'] = 1 << 2
        recipe['selected_control'] = 2
        recipe.setdefault('positions', [[16 + (i % 4)*160, 16 + (i // 4)*80]
                                        for i in range(16)])
        recipe.setdefault('sizes', [[0, 0] for _ in range(16)])
        recipe['positions'][2] = [32, 32]
        recipe['sizes'][2] = [180, 50]
        self.kde = ROOT / 'colors/DomainOS-SR10.4.colors'

    def test_check_uses_native_record_and_rejects_unimplemented_neighbors(self):
        self.assertEqual([r['id'] for r in button_records(self.project)], ['check'])
        self.assertEqual(renderer(self.project), 'buttons')
        self.assertTrue(needs_check(self.project))
        unsupported = copy.deepcopy(self.project)
        unsupported['recipes']['gtk4']['visible_controls'] |= 1 << 3
        with self.assertRaisesRegex(ValueError, 'pending'):
            button_records(unsupported)

    def test_assets_are_kde_role_derived_and_css_keeps_native_check_input(self):
        builder = backend.load_builder(ROOT)
        recipe = copy.deepcopy(self.project['recipes']['gtk4'])
        roles = {name: color for index, names in enumerate(builder.art.ROLES.values())
                 for color, name in zip(('#8798a9', '#738495', '#526374', '#aabbcc'), names)}
        with backend.recipe_rules(builder, recipe['palette']):
            receipt = write_check_css(builder, recipe, roles, self.folder / 'check-assets')
        css = Path(receipt['css']).read_text(encoding='utf-8')
        self.assertIn('checkbutton.theme-lab-gtk4-check-', css)
        self.assertIn(':checked', css)
        self.assertIn(':disabled', css)
        self.assertIn(':backdrop', css)
        self.assertIn('background-image: url("file://', css)
        self.assertNotRegex(css, r'#[0-9a-fA-F]{6}\b')
        self.assertEqual(len(list((self.folder / 'check-assets').glob('*.png'))), 6)
        self.assertIn('KDE role aliases', receipt['palette_source'])

    def test_snapshot_route_and_receipt_bind_check_capability_and_schema(self):
        snapshot = self.folder / 'snapshot'
        project_path = self.folder / 'source-project.json'
        backend.write_json(project_path, self.project)
        self.project, _ = backend.project(project_path)
        backend.write_json(project_path, self.project)
        self.project, digest = backend.project(project_path)
        receipt = generate_snapshot(ROOT, snapshot, self.project, digest, self.kde,
                                    allow_check=True)
        verified, _colors = verify_snapshot(ROOT, snapshot, self.project, digest,
                                            allow_check=True)
        self.assertEqual(receipt, verified)
        self.assertEqual(receipt['translated_controls'], ['check'])
        self.assertTrue(receipt['private_check_session'])
        self.assertFalse(receipt['private_toggle_session'])
        saved, saved_digest = backend.project(snapshot / 'PROJECT.json')
        route_receipt = dict(receipt, snapshot=str(snapshot), source_project_sha256=digest,
                             preview_project_sha256=saved_digest)
        argv = command(ROOT, route_receipt,
                       self.project, self.folder / 'events', self.kde)
        self.assertIn('--private-check-session', argv)
        self.assertNotIn('--private-toggle-session', argv)
        with self.assertRaisesRegex(ValueError, 'capability mismatch'):
            verify_snapshot(ROOT, snapshot, self.project, digest,
                            allow_toggle=True, allow_check=False)

    def test_mixed_native_button_scene_lists_each_translated_control(self):
        project = copy.deepcopy(self.project)
        project['recipes']['gtk4']['visible_controls'] = 1 | 2 | 4
        self.assertEqual([r['id'] for r in button_records(project)], ['push', 'toggle', 'check'])
        self.assertEqual(renderer(project), 'buttons')


if __name__ == '__main__':
    unittest.main()
