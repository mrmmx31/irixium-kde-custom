#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 scene masks and snapshot validation without a scrollbar."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import validate_snapshot


class GenerationVisibilityTests(unittest.TestCase):
    def test_all_visible_scene_receipt_matches_catalog(self):
        data = model()
        data['selected_family'] = 'gtk2'
        recipe = data['recipes']['gtk2']
        recipe.update(visible_categories=31, visible_controls=(1 << 16) - 1)
        temp_root = Path.home() / 'tempia'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='qa-gtk2-all-mask-', dir=temp_root) as temp:
            folder = Path(temp) / 'generation'
            folder.mkdir(mode=0o700)
            receipt = generate_scrollbar_snapshot(
                backend, ROOT, folder, data,
                ROOT / 'colors/DomainOS-SR10.4.colors')
            from scene_contract import CONTROLS
            self.assertEqual(receipt['scene_controls'], list(CONTROLS))
            self.assertEqual(receipt['translated_controls'], list(CONTROLS))
            self.assertEqual(receipt['untranslated_controls'], [])
            validated = validate_snapshot(backend, ROOT, receipt['rc'], data)
            self.assertEqual(validated['scene_controls'], list(CONTROLS))
            self.assertEqual(validated['translated_controls'], list(CONTROLS))
            self.assertTrue(backend.generation_sources_current(validated, ROOT))

    def test_frame_only_scene_needs_no_scrollbar_style(self):
        data = model()
        data['selected_family'] = 'gtk2'
        recipe = data['recipes']['gtk2']
        recipe.update(visible_categories=1 << 4,
                      visible_controls=1 << 15,
                      selected_control=15)
        temp_root = Path.home() / 'tempia'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='qa-gtk2-mask-', dir=temp_root) as temp:
            receipt = generate_scrollbar_snapshot(
                backend, ROOT, Path(temp), data,
                ROOT / 'colors/DomainOS-SR10.4.colors')
            self.assertEqual(receipt['scene_controls'], ['frame'])
            self.assertEqual(receipt['translated_controls'], ['frame'])
            self.assertIn('tools/theme-lab/backend.py', receipt['sources'])
            self.assertIn('tools/theme-lab/scene_contract.py', receipt['sources'])
            self.assertNotIn('scrollbar_style_id', receipt)
            validated = validate_snapshot(backend, ROOT, receipt['rc'], data)
            self.assertEqual(validated['translated_controls'], ['frame'])
            self.assertTrue(backend.generation_sources_current(validated, ROOT))

            project = Path(temp) / 'PROJECT.json'
            backend.write_json(project, data)
            native_output = Path(temp) / 'native'
            probe = Path(__file__).with_name('probe_gtk2_frame_only_native.py')
            tmp_root = Path.home() / 'tempia' / 'domainos-theme-work' / 'xvfb-runtime'
            tmp_root.mkdir(parents=True, exist_ok=True)
            child_env = dict(os.environ, TMPDIR=str(tmp_root), GDK_BACKEND='x11',
                             GTK_MODULES='', GTK2_RC_FILES='/dev/null',
                             I167_PRIVATE_PROBE='1')
            child = subprocess.run(
                ['xvfb-run', '-a', '/usr/bin/python3', '-B', str(probe), '--project', str(project),
                 '--rc', receipt['rc'], '--output', str(native_output)],
                check=True, capture_output=True, text=True, timeout=30,
                env=child_env)
            native = json.loads(child.stdout)
            self.assertEqual(native['status'], 'passed')
            self.assertEqual(native['controls'], ['frame'])
            self.assertEqual(native['widget_source'], 'native_gtk2')
            self.assertGreater(native['allocation'][2], 0)
            self.assertGreater(native['allocation'][3], 0)
            self.assertTrue((native_output / 'gtk2-frame-only.png').is_file())


if __name__ == '__main__':
    unittest.main()
