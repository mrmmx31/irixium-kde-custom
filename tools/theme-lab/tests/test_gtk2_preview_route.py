# SPDX-License-Identifier: GPL-3.0-or-later
"""Public routing and cache integrity, without a GUI or simulated rendering."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from test_backend import backend, model, ROOT

TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class PreviewRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='qa-gtk2-route-', dir=TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.data = model()
        self.data['selected_family'] = 'gtk2'
        self.data['recipes']['gtk2']['visible_controls'] = (1 << 10) | (1 << 11)
        self.digest = 'a' * 64

    def cached(self):
        folder = self.output / 'revisions' / 'fixture'
        folder.mkdir(parents=True, mode=0o700)
        receipt = {'status': 'partially_generated', 'rc': str(folder / 'gtkrc'),
                   'translated_controls': ['scroll_h', 'scroll_v'],
                   'sources': {name: backend.sha((ROOT / name).read_bytes()) for name in (
                       'tools/theme-lab/backend.py',
                       'tools/theme-lab/scene_contract.py',
                       'tools/theme-lab/gtk2_generation.py')},
                   'capability': {'available': True, 'native_gallery': True}}
        result = {'project_sha256': self.digest, 'generation_dir': str(folder),
                  'families': {'gtk2': receipt}}
        backend.write_json(folder / 'PROJECT.json', self.data)
        backend.write_json(folder / 'RESULTADO.json', result)
        backend.write_json(self.output / 'latest.json', {
            'project_sha256': self.digest, 'generation_dir': str(folder)})
        return folder, result

    def launch(self, generate=None, palette=True):
        process = Mock(pid=12345)
        process.wait.return_value = 0
        process.poll.return_value = 0
        with patch.object(backend, 'private_namespace', return_value={'fixture': True}), \
             patch.object(backend, 'palette_inputs_current', return_value=palette), \
             patch.object(backend, 'generate', generate or Mock()) as generator, \
             patch.object(backend.subprocess, 'Popen', return_value=process) as popen, \
             contextlib.redirect_stdout(io.StringIO()):
            proof = backend.preview(ROOT, self.output, self.data, self.digest,
                                    self.output / 'kdeglobals', 'gtk2')
        return proof, popen, generator

    def test_verified_cache_routes_to_scene_and_reports_partial_scope(self):
        before = copy.deepcopy(self.data)
        folder, _ = self.cached()
        proof, popen, generator = self.launch()
        generator.assert_not_called()
        argv = popen.call_args.args[0]
        self.assertEqual(argv[2], str(ROOT / 'tools/theme-lab/preview_gtk2.py'))
        self.assertIn(str(folder / 'PROJECT.json'), argv)
        self.assertIn(str(folder / 'gtkrc'), argv)
        self.assertEqual(proof['preview_project_sha256'], backend.sha(
            (folder / 'PROJECT.json').read_bytes()))
        self.assertFalse(proof['recipe_applied'])
        self.assertEqual(proof['recipe_scope'], 'translated_controls')
        self.assertEqual(proof['translated_controls'], ['scroll_h', 'scroll_v'])
        self.assertEqual(proof['status'], 'closed')
        self.assertEqual(self.data, before)

    def test_stale_receipt_scene_directory_or_palette_regenerates(self):
        folder, valid = self.cached()
        for defect in ('receipt_hash', 'scene', 'directory', 'palette', 'source'):
            with self.subTest(defect=defect):
                corrupted = copy.deepcopy(valid)
                if defect == 'receipt_hash': corrupted['project_sha256'] = 'b' * 64
                if defect == 'directory': corrupted['generation_dir'] = str(folder / 'other')
                if defect == 'source':
                    corrupted['families']['gtk2']['sources'][
                        'tools/theme-lab/scene_contract.py'] = '0' * 64
                backend.write_json(folder / 'RESULTADO.json', corrupted)
                scene = copy.deepcopy(self.data)
                if defect == 'scene': scene['name'] = 'changed scene'
                backend.write_json(folder / 'PROJECT.json', scene)
                def fresh(*args, **kwargs):
                    if kwargs.get('family_scope') != ['gtk2']:
                        raise AssertionError('GTK2 preview generation must be family-scoped')
                    backend.write_json(folder / 'PROJECT.json', self.data)
                    return valid
                generator = Mock(side_effect=fresh)
                _, _, called = self.launch(generator, palette=defect != 'palette')
                called.assert_called_once()

    def test_old_range_only_snapshot_cannot_paint_new_button(self):
        self.data['recipes']['gtk2']['visible_controls'] |= 1
        folder, valid = self.cached()
        fresh = copy.deepcopy(valid)
        fresh['families']['gtk2']['translated_controls'].insert(0, 'push')
        generator = Mock(return_value=fresh)
        proof, _, called = self.launch(generator)
        called.assert_called_once()
        self.assertIn('push', proof['translated_controls'])

    def test_private_namespace_guard_precedes_output_and_launch(self):
        with patch.object(backend, 'private_namespace', side_effect=backend.Unavailable('guard')), \
             patch.object(backend, 'private_output') as output, \
             patch.object(backend.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(backend.Unavailable, 'guard'):
                backend.preview(ROOT, self.output, self.data, self.digest,
                                self.output / 'kdeglobals', 'gtk2')
            output.assert_not_called()
            popen.assert_not_called()

    def test_unsupported_recipe_precedes_output_and_launch(self):
        self.data['recipes']['gtk2']['scrollbar_parts'] = {'fitting': {'gap_px': 4}}
        with patch.object(backend, 'private_namespace', return_value={'fixture': True}), \
             patch.object(backend, 'private_output') as output, \
             patch.object(backend.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(backend.Unavailable, 'content fitting'):
                backend.preview(ROOT, self.output, self.data, self.digest,
                                self.output / 'kdeglobals', 'gtk2')
            output.assert_not_called()
            popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
