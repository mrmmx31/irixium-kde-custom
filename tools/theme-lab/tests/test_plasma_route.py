#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Plasma recipe -> KSvg theme snapshot -> native preview dispatch checks."""
import configparser
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import sys

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
import backend
import plasma_recipe
import plasma_route


ROOT = backend.ROOT


def model():
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    recipes = {family: {'geometry': geometry.copy(), 'palette': palette.copy(),
                        'visible_categories': 1 << 2,
                        'visible_controls': (1 << 10) | (1 << 11),
                        'selected_control': 10, 'edit_state': 0,
                        'positions': [[16, 16] for _ in range(16)],
                        'sizes': [[0, 0] for _ in range(16)]}
               for family in backend.FAMILIES}
    return {'schema_version': 1, 'kind': 'theme_lab_project',
            'name': 'Plasma route fixture', 'reference': '',
            'selected_family': 'plasma', 'color_scheme': 'FixtureDomainOS',
            'recipes': recipes}


class PlasmaRouteTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='.qa-plasma-i172-', dir=ROOT)
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.scheme = self.work / 'FixtureDomainOS.colors'
        self.scheme.write_text(
            '[General]\nName=Fixture DomainOS\nColorScheme=FixtureDomainOS\n'
            '[Colors:Button]\nBackgroundNormal=120,160,210\nForegroundNormal=255,255,255\n'
            '[Colors:Window]\nBackgroundNormal=80,100,120\nForegroundNormal=240,240,240\n'
            '[Colors:View]\nBackgroundNormal=70,90,110\nForegroundNormal=245,245,245\n'
            '[Colors:Selection]\nBackgroundNormal=50,140,190\nForegroundNormal=255,255,255\n',
            encoding='utf-8')
        self.selected_config = configparser.ConfigParser(interpolation=None)
        self.selected_config.optionxform = str
        self.selected_config.read(self.scheme, encoding='utf-8')
        self.selected = {'path': str(self.scheme), 'sha256': backend.sha(self.scheme.read_bytes()),
                         'scheme_id': 'FixtureDomainOS', 'scheme_name': 'Fixture DomainOS'}
        self.data = model()
        self.data['recipes']['plasma']['selected_control'] = 10
        self.project_file = self.work / 'PROJECT-input.json'
        backend.write_json(self.project_file, self.data)
        self.data, self.digest = backend.project(self.project_file)
        self.output = self.work / 'generated'

    def generate(self):
        capabilities = {'families': {family: {'available': family == 'plasma',
                                               'native_gallery': family == 'plasma',
                                               'reason': 'fixture'}
                                     for family in backend.FAMILIES}}
        with patch.object(backend, 'probe', return_value=capabilities), \
             patch.object(backend, 'selected_palette', return_value=(self.selected_config, self.selected)), \
             patch.object(backend, 'palette_inputs_current', return_value=True):
            return backend.generate(ROOT, self.output, self.data, self.digest,
                                    self.scheme, {'plasma'})

    def test_generation_maps_recipe_geometry_roles_and_native_theme_snapshot(self):
        result = self.generate()
        receipt = result['families']['plasma']
        self.assertEqual(result['status'], 'partially_generated')
        self.assertEqual(receipt['translated_controls'], ['scroll_h', 'scroll_v'])
        self.assertEqual(receipt['effective_geometry'], {
            'vertical_bar_px': 15, 'horizontal_bar_px': 15,
            'thumb_cross_px': 11, 'cross_inset_px': 2})
        self.assertEqual(receipt['theme_name'], plasma_recipe.THEME_NAME)
        svg = Path(receipt['svg']).read_text(encoding='utf-8')
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', svg)
        self.assertNotIn('<ns0:', svg)
        self.assertIn('ColorScheme-ButtonBackground', svg)
        self.assertIn('ColorScheme-ButtonText', svg)
        self.assertIn('id="hint-scrollbar-size" width="11" height="11"', svg)
        self.assertIn('id="slider-hint-left-inset"', svg)
        self.assertEqual(plasma_route.verify(ROOT, receipt, self.data)['family'], 'plasma')
        environment = plasma_route.environment(ROOT, receipt, self.data)
        self.assertEqual(environment['XDG_CONFIG_HOME'], receipt['preview_config'])
        self.assertIn('plasma/desktoptheme/ThemeLabDomainOS', receipt['theme_dir'])
        argv = plasma_route.command(ROOT, receipt, self.data,
                                    Path(receipt['snapshot']) / 'PROJECT.json')
        self.assertTrue(argv[2].endswith('/plasma_style_demo.py'))
        self.assertIn('--snapshot', argv)

    def test_custom_geometry_and_palette_changes_apply_without_changing_svg_topology(self):
        self.data['recipes']['plasma']['geometry'].update(
            bar_px=17, arrow_px=13, thumb_cross_px=13)
        self.data['recipes']['plasma']['palette'].update(
            face_role='Colors:Window/BackgroundNormal',
            text_role='Colors:Window/ForegroundNormal', light=.4, shade=.3, trough=.2)
        path = self.work / 'custom.json'
        backend.write_json(path, self.data)
        project, digest = backend.project(path)
        with patch.object(backend, 'selected_palette', return_value=(self.selected_config, self.selected)), \
             patch.object(backend, 'palette_inputs_current', return_value=True):
            output = self.work / 'custom-output'
            output.mkdir(mode=0o700)
            backend.write_json(output / 'PROJECT.json', project)
            receipt = plasma_recipe.generate(ROOT, output, project, digest, self.scheme)
        self.assertEqual(receipt['effective_geometry'], {
            'vertical_bar_px': 17, 'horizontal_bar_px': 17,
            'thumb_cross_px': 13, 'cross_inset_px': 2})
        svg = Path(receipt['svg']).read_text(encoding='utf-8')
        self.assertIn('ColorScheme-Background', svg)
        self.assertIn('ColorScheme-Text', svg)
        self.assertIn('width="13" height="13"', svg)

    def test_route_filters_untranslated_visible_controls_and_refuses_piece_overrides(self):
        self.data['recipes']['plasma']['visible_categories'] = (1 << 0) | (1 << 2)
        self.data['recipes']['plasma']['visible_controls'] = (1 << 10) | 1
        self.output.mkdir(mode=0o700)
        backend.write_json(self.output / 'PROJECT.json', self.data)
        with patch.object(backend, 'selected_palette', return_value=(self.selected_config, self.selected)), \
             patch.object(backend, 'palette_inputs_current', return_value=True):
            receipt = plasma_recipe.generate(
                ROOT, self.output, self.data, self.digest, self.scheme)
        self.assertEqual(receipt['translated_controls'], ['scroll_h'])
        self.assertEqual(receipt['untranslated_visible_controls'], ['push'])
        self.data['recipes']['plasma']['visible_controls'] = (1 << 10) | (1 << 11)
        self.data['recipes']['plasma']['scrollbar_parts'] = {'thumb': {'cross_px': 11}}
        with self.assertRaisesRegex(backend.Unavailable, 'piece overrides'):
            plasma_recipe.generate(ROOT, self.output, self.data, self.digest, self.scheme)

    def test_route_refuses_asymmetric_geometry_and_corrupt_snapshot(self):
        self.data['recipes']['plasma']['geometry'].update(bar_px=16, thumb_cross_px=11)
        with self.assertRaisesRegex(ValueError, 'equal integer insets'):
            plasma_recipe._geometry(self.data['recipes']['plasma'], plasma_recipe.contract(ROOT)[0])
        self.data['recipes']['plasma']['geometry'].update(bar_px=15, thumb_cross_px=11)
        result = self.generate()
        receipt = result['families']['plasma']
        Path(receipt['svg']).write_text('corrupt', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            plasma_route.verify(ROOT, receipt, self.data)


if __name__ == '__main__':
    unittest.main()
