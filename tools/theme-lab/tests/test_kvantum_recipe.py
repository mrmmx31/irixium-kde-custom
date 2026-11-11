#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recipe -> role-derived SVG/metrics -> real Kvantum preview route."""
import configparser
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(ROOT / 'tools'))
import backend
import kvantum_recipe
import kvantum_route
import domainos_motif_art as art


QT = {group: {'Base': '#607f91', 'AlternateBase': '#678799', 'Shadow': '#20282d'}
      for group in ('Active', 'Inactive', 'Disabled')}


def model():
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    recipes = {family: {'geometry': geometry.copy(), 'palette': palette.copy(),
                        'visible_categories': 1 << 2,
                        'visible_controls': (1 << 10) | (1 << 11),
                        'selected_control': 10,
                        'positions': [[16, 16] for _ in range(16)],
                        'sizes': [[0, 0] for _ in range(16)]}
               for family in backend.FAMILIES}
    return {'schema_version': 1, 'kind': 'theme_lab_project',
            'name': 'Kvantum recipe fixture', 'reference': '',
            'selected_family': 'kvantum', 'color_scheme': 'fixture',
            'recipes': recipes}


def source_palette(builder, shade='#78a0d5'):
    colors = dict(builder.art.DEFAULT)
    for key in colors:
        if key.endswith('_breeze'):
            colors[key] = '#ffffff' if ('text' in key or 'foreground' in key or '_fg_' in key) else shade
    return colors


class KvantumRecipeTests(unittest.TestCase):
    def generate(self, output, project, shade='#78a0d5'):
        builder = backend.load_builder(ROOT)
        selected_config = configparser.ConfigParser(interpolation=None)
        selected_config['General'] = {'ColorScheme': 'fixture'}
        selected = {'path': '/fixture/selected.colors', 'sha256': 'a' * 64,
                    'scheme_id': 'fixture', 'scheme_name': 'Fixture palette'}
        origin = {'path': selected['path'], 'sha256': selected['sha256'],
                  'helper': {'path': '/fixture/kde-reader', 'sha256': 'b' * 64},
                  'helper_source': {'path': '/fixture/kde-reader.cpp', 'sha256': 'c' * 64}}
        colors = source_palette(builder, shade)
        with (patch.object(backend, 'load_builder', return_value=builder),
              patch.object(backend, 'selected_palette', return_value=(selected_config, selected)),
              patch.object(backend, 'native_roles', return_value=(colors, origin)),
              patch('kvantum_native_palette.read', return_value={
                  'palette': QT, 'qt_version': '6.8.2', 'source_signature': 'd' * 64,
                  'checks': {'kde_platform_loaded': True, 'kvantum_not_loaded': True,
                             'no_widget_palette_injection': True}}),
              patch.object(backend, 'palette_inputs_current', return_value=True)):
            output.mkdir(parents=True, exist_ok=True, mode=0o700)
            backend.write_json(output / 'PROJECT.json', project)
            digest = backend.sha(backend.read_file(output / 'PROJECT.json'))
            receipt = kvantum_recipe.generate(ROOT, output, project, digest,
                                               Path('/fixture/kdeglobals'))
        return receipt

    def test_contract_drives_svg_cells_and_kvantum_metrics(self):
        project = model()
        for recipe in project['recipes'].values():
            recipe['selected_scroll_part'] = 0
            recipe['edit_state'] = 0
        with tempfile.TemporaryDirectory(prefix='.qa-kvantum-i171-', dir=ROOT) as temp:
            output = Path(temp) / 'snapshot'
            receipt = self.generate(output, project)
            self.assertEqual(receipt['status'], 'partially_generated')
            self.assertEqual(receipt['translated_controls'], ['scroll_h', 'scroll_v'])
            self.assertEqual(receipt['contract']['sha256'], backend.sha(
                backend.read_file(ROOT / 'tools/domainos_scrollbar_rules.json')))
            self.assertEqual(receipt['config_geometry'], {'scroll_width': 15, 'indicator_size': 15})
            self.assertEqual(Path(receipt['theme_dir']).parent,
                             Path(receipt['preview_config']) / 'Kvantum')
            self.assertEqual(Path(receipt['selector']).parent, Path(receipt['preview_config']) / 'Kvantum')
            config = Path(receipt['kvconfig']).read_text(encoding='utf-8')
            self.assertIn('scroll_width=15\n', config)
            self.assertIn('indicator.size=15\n', config)
            self.assertIn('window.color=none\n', config)
            self.assertIn('button.color=none\n', config)
            svg = Path(receipt['svg']).read_bytes()
            self.assertEqual(art.geometry_sha(svg), art.geometry_sha(
                art.svg(source_palette(backend.load_builder(ROOT)), scrollbar_geometry={
                    'bar_px': 15, 'shadow_px': 2, 'arrow_px': 11})))
            self.assertIn(b'id="dm-stepper-down-normal"', svg)
            self.assertEqual(receipt['palette_roles_applied'], True)
            with patch.object(backend, 'palette_inputs_current', return_value=True):
                with (patch.object(backend, 'load_builder', return_value=backend.load_builder(ROOT)),
                      patch.object(backend, 'selected_palette', return_value=(
                          configparser.ConfigParser(interpolation=None), {
                              'path': '/fixture/selected.colors', 'sha256': 'a' * 64,
                              'scheme_id': 'fixture', 'scheme_name': 'Fixture palette'})),
                      patch.object(backend, 'native_roles', return_value=(
                          source_palette(backend.load_builder(ROOT)), {
                              'helper': {'path': '/fixture/kde-reader', 'sha256': 'b' * 64},
                              'helper_source': {'path': '/fixture/kde-reader.cpp', 'sha256': 'c' * 64}})),
                      patch('kvantum_native_palette.read', return_value={
                          'palette': QT, 'qt_version': '6.8.2', 'source_signature': 'd' * 64,
                          'checks': {'kde_platform_loaded': True, 'kvantum_not_loaded': True,
                                     'no_widget_palette_injection': True}}),
                      patch.object(backend, 'palette_inputs_current', return_value=True)):
                    routed_model = json.loads(json.dumps(project))
                    routed_model.setdefault('separate_preview', False)
                    routed_model.setdefault('color_scheme', '')
                    verified = kvantum_route.generate(ROOT, output.parent / 'routed', routed_model,
                        backend.sha(json.dumps(routed_model, sort_keys=True).encode()), Path('/fixture/kdeglobals'))
                self.assertEqual(kvantum_route.verify(ROOT, verified, routed_model)['family'], 'kvantum')
                env = kvantum_route.environment(ROOT, verified, routed_model)
                self.assertEqual(env['QT_STYLE_OVERRIDE'], 'kvantum')
                command = kvantum_route.command(ROOT, verified, routed_model,
                    Path(verified['snapshot']) / 'PROJECT.json')
                self.assertIn('--theme-lab-kvantum-snapshot', command)
                self.assertIn('--theme-lab-kvantum-root', command)

    def test_recipe_palette_changes_pixels_without_changing_integer_geometry(self):
        project = model()
        with tempfile.TemporaryDirectory(prefix='.qa-kvantum-i171-', dir=ROOT) as temp:
            first = self.generate(Path(temp) / 'one', project, '#7894a7')
            second = self.generate(Path(temp) / 'two', project, '#e8d070')
            one = Path(first['svg']).read_bytes()
            two = Path(second['svg']).read_bytes()
            self.assertNotEqual(one, two)
            self.assertEqual(art.geometry_sha(one), art.geometry_sha(two))
            self.assertEqual(first['geometry'], second['geometry'])

    def test_mixed_scene_keeps_scrollbars_and_reports_untranslated_controls(self):
        project = model()
        project['recipes']['kvantum']['visible_categories'] |= 1 << 0
        project['recipes']['kvantum']['visible_controls'] |= 1 << 0
        with tempfile.TemporaryDirectory(prefix='.qa-kvantum-i171-', dir=ROOT) as temp:
            receipt = self.generate(Path(temp) / 'mixed', project)
        self.assertEqual(receipt['translated_controls'], ['scroll_h', 'scroll_v'])
        self.assertEqual(receipt['untranslated_visible_controls'], ['push'])

    def test_backend_generation_receipt_is_accepted_by_preview_verifier(self):
        """Exercise the same generate -> verify handoff used by the GUI."""
        project = model()
        project['recipes']['kvantum']['selected_scroll_part'] = 0
        project['recipes']['kvantum']['edit_state'] = 0
        selected_config = configparser.ConfigParser(interpolation=None)
        selected_config['General'] = {'ColorScheme': 'fixture'}
        selected = {'path': '/fixture/selected.colors', 'sha256': 'a' * 64,
                    'scheme_id': 'fixture', 'scheme_name': 'Fixture palette'}
        origin = {'path': selected['path'], 'sha256': selected['sha256'],
                  'helper': {'path': '/fixture/kde-reader', 'sha256': 'b' * 64},
                  'helper_source': {'path': '/fixture/kde-reader.cpp', 'sha256': 'c' * 64}}
        colors = source_palette(backend.load_builder(ROOT))
        capabilities = {'families': {family: {'available': family == 'kvantum',
                                               'native_gallery': family == 'kvantum',
                                               'reason': 'fixture'}
                                     for family in backend.FAMILIES}}
        with tempfile.TemporaryDirectory(prefix='.qa-kvantum-backend-', dir=ROOT) as temp:
            output = Path(temp) / 'generated'
            source_project = Path(temp) / 'working.json'
            backend.write_json(source_project, project)
            project, project_hash = backend.project(source_project)
            with (patch.object(backend, 'probe', return_value=capabilities),
                  patch.object(backend, 'load_builder', return_value=backend.load_builder(ROOT)),
                  patch.object(backend, 'selected_palette', return_value=(selected_config, selected)),
                  patch.object(backend, 'native_roles', return_value=(colors, origin)),
                  patch.object(backend, 'palette_inputs_current', return_value=True),
                  patch('kvantum_native_palette.read', return_value={
                      'palette': QT, 'qt_version': '6.8.2', 'source_signature': 'd' * 64,
                      'checks': {'kde_platform_loaded': True, 'kvantum_not_loaded': True,
                                 'no_widget_palette_injection': True}})):
                generated = backend.generate(ROOT, output, project, project_hash,
                                             Path('/fixture/kdeglobals'), {'kvantum'})
                receipt = generated['families']['kvantum']
                saved_receipt = json.loads(backend.read_file(
                    Path(receipt['snapshot']) / 'KVANTUM-RECIPE.json'))
                verified = kvantum_route.verify(ROOT, saved_receipt, project)
                environment = kvantum_route.environment(ROOT, saved_receipt, project)
            self.assertEqual(receipt['status'], 'partially_generated')
            self.assertTrue(saved_receipt['snapshot'])
            self.assertEqual(saved_receipt['preview_project_sha256'],
                             backend.sha(backend.read_file(Path(saved_receipt['snapshot']) / 'PROJECT.json')))
            self.assertEqual(verified['family'], 'kvantum')
            self.assertEqual(environment['QT_STYLE_OVERRIDE'], 'kvantum')

    def test_custom_odd_metrics_generate_integer_cells_and_bad_recipe_fails_closed(self):
        builder = backend.load_builder(ROOT)
        cell = builder.art.kvantum_scrollbar_stepper(
            'normal', 'right', bar_px=17, shadow_px=2, arrow_px=13)
        self.assertEqual((len(cell), len(cell[0])), (17, 17))
        project = model()
        project['recipes']['kvantum']['geometry'].update(bar_px=17, arrow_px=13, thumb_cross_px=13)
        with tempfile.TemporaryDirectory(prefix='.qa-kvantum-i171-', dir=ROOT) as temp:
            receipt = self.generate(Path(temp) / 'custom', project)
            self.assertEqual(receipt['config_geometry'], {'scroll_width': 17, 'indicator_size': 17})
            project['recipes']['kvantum']['geometry']['thumb_cross_px'] = 12
            with self.assertRaisesRegex(ValueError, 'odd arrow'):
                kvantum_recipe._geometry(project['recipes']['kvantum'],
                                         kvantum_recipe.contract(ROOT)[0])


if __name__ == '__main__':
    unittest.main()
