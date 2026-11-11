#!/usr/bin/python3
"""Private export isolation and exact proposal differences, without GUI claims."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend
from proposal_export import differences, affected_families, model_digest, replay_delta


class ExportTests(unittest.TestCase):
    def palette_fixture(self, output):
        geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
        data = {'schema_version': 1, 'kind': 'theme_lab_project', 'selected_family': 'gtk3',
                'recipes': {family: {'geometry': geometry.copy(),
                    'palette': dict(backend.DEFAULT_ROLES, **backend.FACTORS)}
                    for family in backend.FAMILIES}}
        scene = output / 'scene.json'; scene.write_text(json.dumps(data))
        applied, digest = backend.project(scene)
        folder = output / 'revisions/fixture'; folder.mkdir(parents=True, mode=0o700)
        # Generation serializes the normalized model; its byte hash need not
        # match the original scene. Identity must compare normalized content.
        (folder / 'PROJECT.json').write_text(json.dumps(applied, indent=2))
        palette = output / 'palette-input'; palette.write_text('snapshot A')
        # Palette auditing covers every translated family, including Qt6.
        # A missing receipt must remain unknown and therefore export-scoped.
        receipts = {family: {'palette_inputs': [{'path': str(palette),
                      'sha256': backend.sha(palette.read_bytes())}]}
                    for family in ('gtk2', 'gtk3', 'qt6')}
        result = {'project_sha256': digest, 'generation_dir': str(folder), 'families': receipts}
        (folder / 'RESULTADO.json').write_text(json.dumps(result))
        (output / 'latest.json').write_text(json.dumps({
            'project_sha256': digest, 'generation_dir': str(folder)}))
        return applied, digest, palette, folder, result

    def test_palette_change_detected_with_same_model_and_scheme(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            applied, digest, palette, _, _ = self.palette_fixture(output)
            affected, audit = backend.scene_palette_scope(Path.cwd(), output, applied, digest)
            self.assertEqual(affected, [])
            self.assertEqual(audit['gtk3']['status'], 'unchanged')
            palette.write_text('snapshot B')
            affected, audit = backend.scene_palette_scope(Path.cwd(), output, applied, digest)
            self.assertEqual(affected, ['gtk2', 'gtk3', 'qt6'])
            self.assertEqual(audit['gtk3']['status'], 'changed')
            palette.unlink()
            affected, audit = backend.scene_palette_scope(Path.cwd(), output, applied, digest)
            self.assertEqual(audit['gtk2']['status'], 'changed')

    def test_missing_palette_baseline_is_unknown_not_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            applied, digest, _, folder, result = self.palette_fixture(output)
            result['families']['gtk3']['palette_inputs'] = []
            (folder / 'RESULTADO.json').write_text(json.dumps(result))
            affected, audit = backend.scene_palette_scope(Path.cwd(), output, applied, digest)
            self.assertEqual(affected, ['gtk3'])
            self.assertEqual(audit['gtk3']['status'], 'unknown')

    def test_foreign_scene_cannot_prove_palette_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            applied, digest, _, folder, _ = self.palette_fixture(output)
            saved = copy.deepcopy(applied); saved['recipes']['gtk3']['notes'] = 'outra cena'
            (folder / 'PROJECT.json').write_text(json.dumps(saved))
            affected, audit = backend.scene_palette_scope(Path.cwd(), output, applied, digest)
            self.assertEqual(affected, ['gtk2', 'gtk3', 'qt6'])
            self.assertEqual(audit['gtk3']['status'], 'unknown')
            (output / 'latest.json').write_text(json.dumps({'generation_dir': '/etc'}))
            with self.assertRaisesRegex(ValueError, 'fora das revisões'):
                backend.scene_palette_scope(Path.cwd(), output, applied, digest)

    def test_export_includes_changed_external_palette_without_model_delta(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            applied, digest, palette, _, _ = self.palette_fixture(output)
            palette.write_text('changed reader or scheme contents')
            def generate(root, directory, model, project_hash, kdeglobals, family_scope=None):
                self.assertEqual(family_scope, ['gtk2', 'gtk3', 'qt6'])
                directory.mkdir(mode=0o700)
                folder = directory / 'fixture'; folder.mkdir()
                return {'status': 'ok', 'generation_dir': str(folder), 'families': {}}
            with patch.object(backend, 'generate', side_effect=generate):
                result = backend.export_proposal(Path.cwd(), output, applied, digest,
                                                 None, output / 'scene.json')
            self.assertEqual(result['comparison']['changes'], [])
            self.assertEqual(result['comparison']['scene_palette_comparison']['gtk3']['status'], 'changed')

    def test_export_refuses_palette_race_in_omitted_family(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            applied, digest, palette, _, _ = self.palette_fixture(output)
            def generate(root, directory, model, project_hash, kdeglobals, family_scope=None):
                self.assertEqual(family_scope, [])
                directory.mkdir(mode=0o700)
                folder = directory / 'fixture'; folder.mkdir()
                palette.write_text('changed during export')
                return {'status': 'ok', 'generation_dir': str(folder), 'families': {}}
            with patch.object(backend, 'generate', side_effect=generate):
                with self.assertRaisesRegex(backend.Unavailable, 'durante a exportação'):
                    backend.export_proposal(Path.cwd(), output, applied, digest,
                                            None, output / 'scene.json')
            self.assertFalse((output / 'exports/fixture/DELTA.json').exists())

    def test_export_wires_minimal_package_to_verified_scene_base(self):
        from artifact_delta import reconstruct_files
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            applied, digest, _, folder, baseline = self.palette_fixture(output)
            base_theme = folder / 'theme'; base_theme.mkdir()
            original = {'gtk.css': b'old css', 'arrow.svg': b'same asset'}
            for name, data in original.items(): (base_theme / name).write_bytes(data)
            (base_theme / 'MANIFEST.json').write_text(json.dumps({
                'files': {name: backend.sha(data) for name, data in original.items()}}))
            baseline['families']['gtk3'].update(family='gtk3', status='generated', theme_path=str(base_theme))
            (folder / 'RESULTADO.json').write_text(json.dumps(baseline))
            pointer = (output / 'latest.json').read_bytes()
            proposal = copy.deepcopy(applied)
            proposal['recipes']['gtk3']['geometry']['control_padding_px'] += 1
            def generate(root, directory, model, project_hash, kdeglobals, family_scope=None):
                self.assertEqual(family_scope, ['gtk3'])
                directory.mkdir(mode=0o700)
                generation = directory / 'fixture'; generation.mkdir()
                theme = generation / 'theme'; theme.mkdir()
                proposed = {'gtk.css': b'new css', 'arrow.svg': b'same asset'}
                for name, data in proposed.items(): (theme / name).write_bytes(data)
                (theme / 'MANIFEST.json').write_text(json.dumps({
                    'files': {name: backend.sha(data) for name, data in proposed.items()}}))
                return {'status': 'ok', 'generation_dir': str(generation), 'families': {
                    'gtk3': {'family': 'gtk3', 'status': 'generated', 'theme_path': str(theme)}}}
            with patch.object(backend, 'generate', side_effect=generate):
                result = backend.export_proposal(Path.cwd(), output, proposal, 'proposed',
                                                 None, output / 'scene.json')
            self.assertEqual(result['artifact_packages']['gtk3'], {
                'status': 'delta', 'payload_files': 1, 'reused_files': 1, 'removed_files': 0})
            package = Path(result['package_directory']) / 'gtk3'
            manifest = json.loads((package / 'FILES.json').read_text())
            reconstruct_files(manifest, package, base_theme, output / 'restored', backend.read_file)
            self.assertEqual((output / 'restored/gtk.css').read_bytes(), b'new css')
            self.assertEqual((output / 'restored/arrow.svg').read_bytes(), b'same asset')
            self.assertEqual((output / 'latest.json').read_bytes(), pointer)
            self.assertIn(str(result['package_directory']), result['review_text'])
            self.assertIn('Nenhum tema foi instalado', result['review_text'])
            self.assertIn('recipes/gtk3/geometry/control_padding_px', result['review_text'])
            self.assertIn('1 dependências da base', result['review_text'])

    def test_diff_preserves_null_add_remove_and_types(self):
        changes = differences({'gone': None, 'same': [1], 'number': 1},
                              {'added': None, 'same': [1], 'number': True})
        self.assertEqual(changes, [
            {'path': ['added'], 'operation': 'add', 'value': None},
            {'path': ['gone'], 'operation': 'remove', 'previous': None},
            {'path': ['number'], 'operation': 'replace', 'previous': 1, 'value': True}])

    def test_export_keeps_preview_pointer_and_compares_scene(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            pointer = output / 'latest.json'
            pointer.write_text('{"generation_dir":"original-preview"}')
            before_pointer = pointer.read_bytes()
            scene = {'recipes': {'gtk3': {'width': 16}, 'qt6': {'width': 24}}}
            proposal = copy.deepcopy(scene)
            proposal['recipes']['gtk3']['width'] = 20
            before = copy.deepcopy(proposal)
            def generate(root, directory, model, digest, kdeglobals, family_scope=None):
                self.assertEqual(directory, output / 'exports')
                self.assertEqual(family_scope, ['gtk3'])
                directory.mkdir(mode=0o700)
                folder = directory / 'fixture'; folder.mkdir()
                (directory / 'latest.json').write_text('export-only')
                return {'status': 'ok', 'generation_dir': str(folder), 'families': {}}
            with patch.object(backend, 'project', return_value=(scene, 'scene-hash')), \
                 patch.object(backend, 'scene_generation', return_value=None), \
                 patch.object(backend, 'scene_palette_scope', return_value=([], {})), \
                 patch.object(backend, 'generate', side_effect=generate):
                result = backend.export_proposal(Path.cwd(), output, proposal,
                                                 'proposal-hash', None, output / 'scene.json')
            self.assertEqual(pointer.read_bytes(), before_pointer)
            self.assertEqual(proposal, before)
            comparison = json.loads((Path(result['generation_dir']) / 'COMPARISON.json').read_text())
            self.assertEqual(comparison['changes'], [{'path': ['recipes', 'gtk3', 'width'],
                'operation': 'replace', 'previous': 16, 'value': 20}])
            self.assertFalse(comparison['installed'])
            self.assertFalse(comparison['live_preview_verified'])
            self.assertEqual(json.loads((Path(result['generation_dir']) / 'SCENE.json').read_text()), scene)
            delta = json.loads((Path(result['generation_dir']) / 'DELTA.json').read_text())
            self.assertEqual(replay_delta(scene, delta), proposal)
            self.assertEqual(delta['affected_families'], ['gtk3'])
            self.assertEqual(delta['shared_contract']['sha256'], backend.sha(
                (Path.cwd() / 'tools/domainos_scrollbar_rules.json').read_bytes()))

    def test_delta_replay_preserves_other_families_and_refuses_divergence(self):
        before = {'recipes': {'gtk3': {'notes': 'Ação', 'width': 16},
                              'qt6': {'positions': [12, 30], 'notes': 'preservar'}}}
        after = copy.deepcopy(before)
        after['recipes']['gtk3']['width'] = 19
        after['recipes']['gtk3']['notes'] = 'São Paulo — prévia'
        delta = {'base_model_sha256': model_digest(before),
                 'proposal_model_sha256': model_digest(after),
                 'changes': differences(before, after)}
        original = copy.deepcopy(before)
        self.assertEqual(replay_delta(before, delta), after)
        self.assertEqual(before, original)
        changed = copy.deepcopy(before); changed['recipes']['qt6']['notes'] = 'novo'
        with self.assertRaisesRegex(ValueError, 'base divergente'):
            replay_delta(changed, delta)
        broken = copy.deepcopy(delta); broken['changes'][0]['value'] = 'corrompido'
        with self.assertRaisesRegex(ValueError, 'inconsistente'):
            replay_delta(before, broken)

    def test_family_scope_tracks_palette_and_nested_types(self):
        before = {'recipes': {'gtk2': {'state': [1]}, 'gtk3': {}}}
        after = copy.deepcopy(before)
        self.assertEqual(affected_families(before, after), [])
        after['recipes']['gtk2']['state'] = [True]
        self.assertEqual(affected_families(before, after), ['gtk2'])
        after['color_scheme'] = 'DomainOS'
        self.assertEqual(affected_families(before, after), ['gtk2', 'gtk3'])

    def test_missing_scene_rejected_before_generation(self):
        with patch.object(backend, 'generate') as generate:
            with self.assertRaisesRegex(ValueError, 'applied-project'):
                backend.export_proposal(Path.cwd(), Path('/tmp'), {}, 'hash', None, None)
            generate.assert_not_called()

    def test_generator_omits_unaffected_family_and_empty_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            model = {'selected_family': 'gtk3', 'recipes': {
                family: {'notes': ''} for family in backend.FAMILIES}}
            capabilities = {'families': {family: {'available': True}
                                         for family in backend.FAMILIES}}
            with patch.object(backend, 'probe', return_value=capabilities), \
                 patch.object(backend, 'generate_gtk3', return_value={
                     'status': 'generated', 'recipe_applied': True}) as gtk3:
                result = backend.generate(Path.cwd(), Path(temp) / 'output', model,
                                          'hash', None, family_scope=['gtk3'])
                self.assertEqual(set(result['families']), {'gtk3'})
                self.assertEqual(gtk3.call_count, 1)
                folder = Path(result['generation_dir'])
                self.assertFalse((folder / 'qt6-RECEIPT.json').exists())
                empty = backend.generate(Path.cwd(), Path(temp) / 'output', model,
                                         'hash', None, family_scope=[])
                self.assertEqual(empty['families'], {})
                self.assertEqual(gtk3.call_count, 1)


if __name__ == '__main__':
    unittest.main()
