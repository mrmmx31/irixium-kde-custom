#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt6 scrollbar recipe contract, palette provenance and snapshot integrity."""
import copy
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'backend.py'
ROOT = SOURCE.parents[2]
TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
sys.path.insert(0, str(SOURCE.parent))
import backend
import qt6_scrollbar_recipe as adapter
import qt6_scrollbar_route as route


def model():
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    recipes = {}
    for family in backend.FAMILIES:
        recipes[family] = {'geometry': geometry.copy(), 'palette': palette.copy(),
                           'visible_categories': 1 << 2,
                           'visible_controls': (1 << 10) | (1 << 11),
                           'selected_control': 10,
                           'positions': [[16, 16] for _ in range(16)],
                           'sizes': [[0, 0] for _ in range(16)]}
    return {'schema_version': 1, 'kind': 'theme_lab_project',
            'name': 'Qt6 scrollbar test fixture', 'reference': '',
            'selected_family': 'qt6', 'color_scheme': 'fixture',
            'recipes': recipes}


class Qt6ScrollbarRecipeTests(unittest.TestCase):
    def generate(self, project, folder, palette):
        builder = backend.load_builder(ROOT)
        selected = {'path': str(folder / 'selected.colors'), 'sha256': 'a' * 64,
                    'scheme_id': 'fixture', 'scheme_name': 'fixture palette'}
        origin = {'path': selected['path'], 'sha256': selected['sha256'],
                  'helper': {'path': '/fixture/helper', 'sha256': 'b' * 64},
                  'helper_source': {'path': '/fixture/source', 'sha256': 'c' * 64}}
        with (patch.object(backend, 'load_builder', return_value=builder),
              patch.object(backend, 'selected_palette', return_value=(None, selected)),
              patch.object(backend, 'native_roles', return_value=(palette, origin)),
              patch.object(backend, 'palette_inputs_current', return_value=True)):
            return adapter.generate(ROOT, folder, project,
                                    backend.sha(json.dumps(project, sort_keys=True).encode()),
                                    Path('/unused/kdeglobals'))

    def test_contract_carries_measured_relief_and_relations(self):
        rules = adapter.contract()
        geometry = rules['geometry']
        self.assertEqual(geometry['origin'], 'measurement_vm')
        self.assertEqual(geometry['bar_px'], geometry['arrow_px'] + 2 * geometry['shadow_px'])
        self.assertEqual(geometry['thumb_cross_px'], geometry['arrow_px'])

    def test_native_cell_retains_exact_shared_pixels_and_custom_geometry_is_pixel_sized(self):
        builder = backend.load_builder(ROOT)
        geometry = {'bar_px': 15, 'shadow_px': 2, 'arrow_px': 11}
        for direction in adapter.DIRECTIONS:
            self.assertEqual(adapter._stepper_pixels(builder.art, 'normal', direction, geometry),
                             builder.art.kvantum_scrollbar_stepper('normal', direction))
        custom = {'bar_px': 17, 'shadow_px': 2, 'arrow_px': 13}
        for state in adapter.STATES:
            for direction in adapter.DIRECTIONS:
                cell = adapter._stepper_pixels(builder.art, state, direction, custom)
                self.assertEqual((len(cell[0]), len(cell)), (17, 17))
                self.assertEqual(cell[0][0], 'dark')
                self.assertEqual(cell[-1][-1], 'light')

    def test_generated_qss_positions_all_four_native_line_controls(self):
        project = model()
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-test-', dir=TEMP_ROOT) as temp:
            folder = Path(temp) / 'snapshot'
            receipt = self.generate(project, folder, palette)
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            for position in ('top', 'bottom', 'left', 'right'):
                self.assertIn(f'subcontrol-position: {position};', qss)
            self.assertIn('QScrollBar#domainosScrollBarVertical::sub-line:vertical {', qss)
            self.assertIn('::sub-line:vertical:disabled {', qss)
            self.assertIn('::add-line:horizontal:disabled {', qss)
            self.assertIn('background-image: url(', qss)
            self.assertEqual(receipt['translated_controls'], ['scroll_h', 'scroll_v'])
            self.assertEqual(receipt['status'], 'partially_generated')
            self.assertTrue(receipt['palette_roles_applied'])
            with patch.object(backend, 'palette_inputs_current', return_value=True):
                self.assertTrue(adapter.verify(ROOT, receipt, project)['artifacts'])

    def test_generated_cells_match_adjusted_geometry_without_smoothing(self):
        project = model()
        project['recipes']['qt6']['geometry'].update(bar_px=17, shadow_px=2,
                                                       arrow_px=13, thumb_cross_px=13)
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-size-', dir=TEMP_ROOT) as temp:
            receipt = self.generate(project, Path(temp) / 'snapshot', palette)
            from PIL import Image
            for direction in adapter.DIRECTIONS:
                with Image.open(Path(receipt['asset_dir']) / f'arrow-{direction}-normal.png') as image:
                    self.assertEqual(image.size, (17, 17))
            self.assertEqual(receipt['geometry']['bar_cross_px'], 17)
            self.assertEqual(receipt['geometry']['arrow_cell_px'], 13)

    def test_selected_kde_role_changes_generated_pixels(self):
        project = model()
        builder = backend.load_builder(ROOT)
        first = dict(builder.art.DEFAULT)
        second = dict(first)
        second['theme_button_background_normal_breeze'] = '#345678'
        with tempfile.TemporaryDirectory(prefix='i170-qt6-palette-', dir=TEMP_ROOT) as temp:
            one = self.generate(project, Path(temp) / 'first', first)
            two = self.generate(project, Path(temp) / 'second', second)
            css_one = Path(one['css']).read_bytes()
            css_two = Path(two['css']).read_bytes()
            png_one = (Path(one['asset_dir']) / 'arrow-down-normal.png').read_bytes()
            png_two = (Path(two['asset_dir']) / 'arrow-down-normal.png').read_bytes()
            self.assertNotEqual(css_one, css_two)
            self.assertNotEqual(png_one, png_two)
            self.assertTrue(one['palette_roles_applied'] and two['palette_roles_applied'])

    def test_real_qt6_scrollbars_show_all_arrows_and_restore_pressed_relief(self):
        project = model()
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-native-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            output = base / 'widget-probe'
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen',
                               HOME=str(home), TMPDIR=str(temp_dir),
                               XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'),
                               PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_scrollbar_widget.py'),
                '--stylesheet', receipt['css'], '--assets', receipt['asset_dir'],
                '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['status'], 'passed')
            self.assertEqual(set(proof['axes']['vertical']['cells']), {'up', 'down'})
            self.assertEqual(set(proof['axes']['horizontal']['cells']), {'left', 'right'})
            for axis in proof['axes'].values():
                for cell in axis['cells'].values():
                    self.assertGreater(cell['heldReliefPixelChanges'], 0)
                    self.assertEqual(cell['releasePixelChanges'], 0)
            self.assertEqual(set(proof['boundaryCells']), {'up', 'down', 'left', 'right'})
            for cell in proof['boundaryCells'].values():
                self.assertEqual(cell['pixelDifferencesFromRecipe'], 0)

    def test_qt6_push_only_recipe_paints_a_real_button_and_uses_selected_kde_roles(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1
        project['recipes']['qt6']['visible_controls'] = 1
        project['recipes']['qt6']['selected_control'] = 0
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palette['theme_button_background_insensitive_breeze'] = '#b0a080'
        with tempfile.TemporaryDirectory(prefix='i170-qt6-push-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['push'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertEqual(receipt['translated_controls'], ['push'])
            self.assertIn('QPushButton#domainosRecipePushButton:pressed', qss)
            self.assertIn('QPushButton#domainosRecipePushButton:disabled', qss)
            self.assertNotIn('QScrollBar#domainosScrollBar', qss)
            alternate_palette = dict(palette)
            alternate_palette['theme_button_background_normal_breeze'] = '#345678'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            self.assertNotEqual(qss, Path(alternate['css']).read_text(encoding='utf-8'))
            output = base / 'probe'
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(home),
                               TMPDIR=str(temp_dir),
                               XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'),
                               PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_push_widget.py'),
                '--stylesheet', receipt['css'], '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['widgetClass'], 'QPushButton')
            self.assertGreater(proof['pressedPixelChanges'], 0)
            self.assertEqual(proof['releasePixelChanges'], 0)
            self.assertGreater(proof['disabledPixelChanges'], 0)

    def test_snapshot_tampering_and_other_controls_fail_closed(self):
        project = model()
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-guard-', dir=TEMP_ROOT) as temp:
            receipt = self.generate(project, Path(temp) / 'snapshot', palette)
            asset = Path(receipt['asset_dir']) / 'arrow-down-normal.png'
            asset.write_bytes(asset.read_bytes() + b'x')
            with self.assertRaisesRegex(ValueError, 'artifact hash mismatch'):
                adapter.verify(ROOT, receipt, project)
        invalid = copy.deepcopy(project)
        invalid['recipes']['qt6']['scrollbar_parts'] = {'thumb': True}
        with tempfile.TemporaryDirectory(prefix='i170-qt6-invalid-', dir=TEMP_ROOT) as temp:
            with self.assertRaisesRegex(backend.Unavailable, 'custom per-piece overrides remain pending'):
                adapter.generate(ROOT, Path(temp) / 'snapshot', invalid,
                                 'd' * 64, Path('/unused/kdeglobals'))

    def test_qt6_toggle_only_recipe_keeps_checked_relief_and_uses_selected_kde_roles(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1
        project['recipes']['qt6']['visible_controls'] = 1 << 1
        project['recipes']['qt6']['selected_control'] = 1
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palette['theme_button_background_insensitive_breeze'] = '#b0a080'
        with tempfile.TemporaryDirectory(prefix='i170-qt6-toggle-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['toggle'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertEqual(receipt['translated_controls'], ['toggle'])
            self.assertIn('QPushButton#domainosRecipeToggleButton:checked', qss)
            self.assertIn('QPushButton#domainosRecipeToggleButton:checked:pressed', qss)
            self.assertIn('QPushButton#domainosRecipeToggleButton:checked:disabled', qss)
            self.assertNotIn('QScrollBar#domainosScrollBar', qss)
            alternate_palette = dict(palette)
            alternate_palette['theme_button_background_normal_breeze'] = '#345678'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            self.assertNotEqual(qss, Path(alternate['css']).read_text(encoding='utf-8'))
            output = base / 'probe'
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(home),
                               TMPDIR=str(temp_dir),
                               XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'),
                               PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_toggle_widget.py'),
                '--stylesheet', receipt['css'], '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['widgetClass'], 'QPushButton')
            self.assertTrue(proof['checkable'])
            self.assertGreater(proof['pressedPixelChanges'], 0)
            self.assertGreater(proof['checkedPixelChanges'], 0)
            self.assertEqual(proof['checkedPressedPixelChanges'], 0)
            self.assertEqual(proof['uncheckReleasePixelChanges'], 0)
            self.assertGreater(proof['disabledPixelChanges'], 0)
            self.assertEqual(proof['toggleStates'], [True, False, True])

    def test_qt6_checkbox_recipe_paints_a_real_indicator_for_checked_and_disabled_states(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1
        project['recipes']['qt6']['visible_controls'] = 1 << 2
        project['recipes']['qt6']['selected_control'] = 2
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palette['theme_button_background_insensitive_breeze'] = '#b0a080'
        palette['theme_button_background_backdrop_insensitive_breeze'] = '#887766'
        with tempfile.TemporaryDirectory(prefix='i170-qt6-check-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['check'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertEqual(receipt['translated_controls'], ['check'])
            self.assertIn('QCheckBox#domainosRecipeCheckBox::indicator:checked', qss)
            self.assertIn('QCheckBox#domainosRecipeCheckBox::indicator:pressed:unchecked', qss)
            self.assertIn('QCheckBox#domainosRecipeCheckBox::indicator:disabled:checked', qss)
            self.assertIn('check-on-disabled.png', qss)
            self.assertNotIn('QScrollBar#domainosScrollBar', qss)
            alternate_palette = dict(palette)
            alternate_palette['theme_button_background_normal_breeze'] = '#345678'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            self.assertNotEqual(qss, Path(alternate['css']).read_text(encoding='utf-8'))
            output = base / 'probe'
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(home),
                               TMPDIR=str(temp_dir),
                               XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'),
                               PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_check_widget.py'),
                '--stylesheet', receipt['css'], '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['widgetClass'], 'QCheckBox')
            self.assertGreater(proof['checkedPixelChanges'], 0)
            self.assertGreater(proof['pressedPixelChanges'], 0)
            self.assertEqual(proof['uncheckReleasePixelChanges'], 0)
            self.assertGreater(proof['disabledPixelChanges'], 0)
            self.assertEqual(proof['toggleStates'], [True, False, True])

    def test_qt6_radio_recipe_paints_exclusive_real_buttons(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1
        project['recipes']['qt6']['visible_controls'] = 1 << 3
        project['recipes']['qt6']['selected_control'] = 3
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palette['theme_button_background_insensitive_breeze'] = '#b0a080'
        palette['theme_button_background_backdrop_insensitive_breeze'] = '#887766'
        with tempfile.TemporaryDirectory(prefix='i170-qt6-radio-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['radio'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertEqual(receipt['translated_controls'], ['radio'])
            self.assertIn('QRadioButton#domainosRecipeRadioButton::indicator:checked', qss)
            self.assertIn('QRadioButton#domainosRecipeRadioPeer::indicator:pressed:!checked', qss)
            self.assertIn('QRadioButton#domainosRecipeRadioButton::indicator:disabled:checked', qss)
            alternate_palette = dict(palette)
            alternate_palette['theme_button_background_normal_breeze'] = '#345678'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            self.assertNotEqual(qss, Path(alternate['css']).read_text(encoding='utf-8'))
            output = base / 'probe'
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(home),
                               TMPDIR=str(temp_dir),
                               XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'),
                               PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_radio_widget.py'),
                '--stylesheet', receipt['css'], '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertTrue(proof['exclusive'])
            self.assertGreater(proof['checkedStatePixelChanges'], 0)
            self.assertGreater(proof['pressedPixelChanges'], 0)
            self.assertEqual(proof['exclusiveReturnPixelChanges'], 0)
            self.assertGreater(proof['disabledPixelChanges'], 0)
            self.assertEqual(proof['states'], [[True, False], [False, True], [True, False]])

    def test_qt6_entry_recipe_preserves_native_utf8_editing_and_standard_shortcuts(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 1
        project['recipes']['qt6']['visible_controls'] = 1 << 4
        project['recipes']['qt6']['selected_control'] = 4
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-entry-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['entry'])
            self.assertEqual(receipt['translated_controls'], ['entry'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertIn('QLineEdit#domainosRecipeEntry:focus', qss)
            self.assertIn('QLineEdit#domainosRecipeEntry:disabled', qss)
            self.assertNotIn('QScrollBar#domainosScrollBar', qss)
            alternate_palette = dict(palette)
            alternate_palette['theme_base_color_breeze'] = '#456789'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            self.assertNotEqual(qss, Path(alternate['css']).read_text(encoding='utf-8'))

            output = base / 'probe'
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(home),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_entry_widget.py'),
                '--stylesheet', receipt['css'], '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['widgetClass'], 'QLineEdit')
            for operation in ('nativeEditWorked', 'undoWorked', 'redoCtrlYWorked',
                              'redoCtrlShiftZWorked', 'copyWorked', 'cutWorked',
                              'pasteWorked', 'selectAllWorked'):
                self.assertTrue(proof[operation], operation)

    def test_qt6_combo_recipe_keeps_native_popup_and_selection(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 1
        project['recipes']['qt6']['visible_controls'] = 1 << 5
        project['recipes']['qt6']['selected_control'] = 5
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-combo-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['combo'])
            self.assertEqual(receipt['translated_controls'], ['combo'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertIn('QComboBox#domainosRecipeCombo::down-arrow', qss)
            self.assertIn('QComboBox#domainosRecipeCombo::down-arrow:on {', qss)
            self.assertNotIn('QComboBox#domainosRecipeCombo:on::down-arrow {', qss)
            arrow_rules = qss.split('QComboBox#domainosRecipeCombo::down-arrow', 1)[1]
            self.assertNotIn('subcontrol-position', arrow_rules.split('}', 1)[0])
            self.assertIn('padding: 4px 19px 4px 4px;', qss)
            self.assertIn('QAbstractItemView#domainosRecipeComboPopup::item:selected', qss)
            self.assertIn('combo-arrow-down-normal.png', qss)
            alternate_palette = dict(palette)
            alternate_palette['theme_button_background_normal_breeze'] = '#345678'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            self.assertNotEqual(qss, Path(alternate['css']).read_text(encoding='utf-8'))

            output = base / 'probe'
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(home),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_combo_widget.py'),
                '--stylesheet', receipt['css'], '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['widgetClass'], 'QComboBox')
            self.assertEqual(proof['keyboardSelectionIndex'], 1)
            self.assertEqual(proof['pointerSelectionIndex'], 1)
            self.assertTrue(proof['popupClosedAfterPointerSelection'])

    def test_qt6_spin_recipe_keeps_native_step_and_edit_shortcuts(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 1
        project['recipes']['qt6']['visible_controls'] = 1 << 6
        project['recipes']['qt6']['selected_control'] = 6
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-spin-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['spin'])
            self.assertEqual(receipt['translated_controls'], ['spin'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertIn('QSpinBox#domainosRecipeSpinBox::up-button', qss)
            self.assertIn('QDoubleSpinBox#domainosRecipeDoubleSpinBox::down-arrow', qss)
            self.assertIn('spin-arrow-up-normal.png', qss)
            alternate_palette = dict(palette)
            alternate_palette['theme_base_color_breeze'] = '#456789'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            self.assertNotEqual(qss, Path(alternate['css']).read_text(encoding='utf-8'))

            output = base / 'probe'
            home = base / 'private-home'
            home.mkdir(mode=0o700)
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(home),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               XDG_STATE_HOME=str(home / '.local/state'),
                               XDG_CACHE_HOME=str(home / '.cache'), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([
                '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_spin_widget.py'),
                '--stylesheet', receipt['css'], '--output', str(output)],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['widgetClasses'], ['QSpinBox', 'QDoubleSpinBox'])
            self.assertEqual(proof['keyboardStepUp'], 43)
            self.assertEqual(proof['keyboardStepDown'], 42)
            for operation in ('undoWorked', 'redoCtrlYWorked', 'redoCtrlShiftZWorked',
                              'copyWorked', 'cutWorked', 'pasteWorked', 'selectAllWorked'):
                self.assertTrue(proof[operation], operation)

    def test_qt6_scale_h_recipe_paints_real_slider_and_keeps_native_input(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 2
        project['recipes']['qt6']['visible_controls'] = 1 << 8
        project['recipes']['qt6']['selected_control'] = 8
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-scale-h-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['scale_h'])
            self.assertEqual(receipt['translated_controls'], ['scale_h'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertIn('QSlider#domainosRecipeScaleHorizontal::groove:horizontal', qss)
            self.assertIn('QSlider#domainosRecipeScaleHorizontal::handle:horizontal', qss)
            self.assertIn('[domainosBackdrop="true"]::groove:horizontal', qss)
            self.assertNotIn('::groove:horizontal:!active', qss)
            self.assertNotIn('domainosRecipeScaleVertical', qss)

            alternate_palette = dict(palette)
            alternate_palette['theme_button_background_normal_breeze'] = '#345678'
            alternate_palette['theme_button_background_backdrop_breeze'] = '#745632'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            alternate_qss = Path(alternate['css']).read_text(encoding='utf-8')
            self.assertNotEqual(qss, alternate_qss)

            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(base),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(base / '.config'),
                               XDG_DATA_HOME=str(base / '.local/share'),
                               XDG_STATE_HOME=str(base / '.local/state'),
                               XDG_CACHE_HOME=str(base / '.cache'), PYTHONPATH=str(SOURCE.parent),
                               PYTHONDONTWRITEBYTECODE='1')
            proof_paths = []
            for name, stylesheet in (('domainos', receipt['css']), ('alternate', alternate['css'])):
                output = base / name
                result = subprocess.run([
                    '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_scale_h_widget.py'),
                    '--stylesheet', stylesheet, '--output', str(output)],
                    env=environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
                proof = json.loads(result.stdout)
                self.assertEqual(proof['widgetClass'], 'QSlider')
                self.assertTrue(proof['mouseChangedValue'])
                self.assertTrue(proof['keyboardChangedValue'])
                self.assertTrue(proof['pressedWhileHeld'])
                self.assertTrue(proof['releasedAfterPointerUp'])
                self.assertTrue(proof['backdropPropertyApplied'])
                self.assertTrue(proof['normalScreenshotSaved'])
                self.assertTrue(proof['backdropScreenshotSaved'])
                self.assertTrue(proof['disabledScreenshotSaved'])
                proof_paths.append(proof['screenshots'])
            from PIL import Image
            self.assertNotEqual(Image.open(proof_paths[0]['normal']).tobytes(),
                                Image.open(proof_paths[1]['normal']).tobytes(),
                                'the actual QSlider pixels must follow the selected KDE role palette')
            self.assertNotEqual(Image.open(proof_paths[0]['backdrop']).tobytes(),
                                Image.open(proof_paths[1]['backdrop']).tobytes(),
                                'the actual inactive QSlider pixels must follow the KDE backdrop role')

    def test_qt6_scale_v_recipe_paints_real_slider_and_keeps_native_input(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 2
        project['recipes']['qt6']['visible_controls'] = 1 << 9
        project['recipes']['qt6']['selected_control'] = 9
        palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        with tempfile.TemporaryDirectory(prefix='i170-qt6-scale-v-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipt = self.generate(project, base / 'snapshot', palette)
            self.assertEqual([row['id'] for row in route.records(project)], ['scale_v'])
            self.assertEqual(receipt['translated_controls'], ['scale_v'])
            qss = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertIn('QSlider#domainosRecipeScaleVertical::groove:vertical', qss)
            self.assertIn('QSlider#domainosRecipeScaleVertical::handle:vertical', qss)
            self.assertIn('min-width: 19px;', qss)
            self.assertIn('[domainosBackdrop="true"]::groove:vertical', qss)
            self.assertNotIn('domainosRecipeScaleHorizontal', qss)

            alternate_palette = dict(palette)
            alternate_palette['theme_button_background_normal_breeze'] = '#345678'
            alternate_palette['theme_button_background_backdrop_breeze'] = '#745632'
            alternate = self.generate(project, base / 'alternate', alternate_palette)
            alternate_qss = Path(alternate['css']).read_text(encoding='utf-8')
            self.assertNotEqual(qss, alternate_qss)

            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(base),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(base / '.config'),
                               XDG_DATA_HOME=str(base / '.local/share'),
                               XDG_STATE_HOME=str(base / '.local/state'),
                               XDG_CACHE_HOME=str(base / '.cache'), PYTHONPATH=str(SOURCE.parent),
                               PYTHONDONTWRITEBYTECODE='1')
            proof_paths = []
            for stylesheet in (receipt['css'], alternate['css']):
                output = base / ('proof-' + str(len(proof_paths)))
                result = subprocess.run([
                    '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_scale_h_widget.py'),
                    '--stylesheet', stylesheet, '--output', str(output), '--orientation', 'vertical'],
                    env=environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
                proof = json.loads(result.stdout)
                self.assertEqual(proof['widgetClass'], 'QSlider')
                self.assertEqual(proof['objectName'], 'domainosRecipeScaleVertical')
                self.assertEqual(proof['orientation'], 'vertical')
                self.assertTrue(proof['mouseChangedValue'])
                self.assertTrue(proof['keyboardChangedValue'])
                self.assertTrue(proof['pressedWhileHeld'])
                self.assertTrue(proof['releasedAfterPointerUp'])
                self.assertTrue(proof['backdropPropertyApplied'])
                self.assertTrue(proof['normalScreenshotSaved'])
                self.assertTrue(proof['backdropScreenshotSaved'])
                self.assertTrue(proof['disabledScreenshotSaved'])
                proof_paths.append(proof['screenshots'])
            from PIL import Image
            self.assertNotEqual(Image.open(proof_paths[0]['normal']).tobytes(),
                                Image.open(proof_paths[1]['normal']).tobytes(),
                                'the actual vertical QSlider pixels must follow the selected KDE role palette')
            self.assertNotEqual(Image.open(proof_paths[0]['backdrop']).tobytes(),
                                Image.open(proof_paths[1]['backdrop']).tobytes(),
                                'the actual inactive vertical QSlider pixels must follow the KDE backdrop role')

    def test_qt6_text_recipe_uses_four_kde_palettes_and_preserves_native_editing(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 1
        project['recipes']['qt6']['visible_controls'] = 1 << 7
        project['recipes']['qt6']['selected_control'] = 7
        base_palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palettes = {'domainos': dict(base_palette)}
        palettes['neutral'] = dict(base_palette)
        palettes['neutral'].update(theme_base_color_breeze='#c8c8c8',
                                   theme_text_color_breeze='#202020',
                                   theme_unfocused_base_color_breeze='#c8c8c8',
                                   theme_unfocused_view_text_color_breeze='#202020',
                                   insensitive_base_color_breeze='#dddddd',
                                   insensitive_base_fg_color_breeze='#484848')
        palettes['dark'] = dict(base_palette)
        palettes['dark'].update(theme_base_color_breeze='#242a31',
                                theme_text_color_breeze='#f4f4f4',
                                theme_unfocused_base_color_breeze='#242a31',
                                theme_unfocused_view_text_color_breeze='#e4e4e4',
                                insensitive_base_color_breeze='#3b4148',
                                insensitive_base_fg_color_breeze='#a0a5aa')
        palettes['yellow'] = dict(base_palette)
        palettes['yellow'].update(theme_base_color_breeze='#dfd264',
                                  theme_text_color_breeze='#202010',
                                  theme_unfocused_base_color_breeze='#d3c65a',
                                  theme_unfocused_view_text_color_breeze='#202010',
                                  insensitive_base_color_breeze='#c5b95a',
                                  insensitive_base_fg_color_breeze='#38351c')
        with tempfile.TemporaryDirectory(prefix='i170-qt6-text-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipts = {}
            for name, palette in palettes.items():
                receipts[name] = self.generate(project, base / name, palette)
                self.assertEqual([row['id'] for row in route.records(project)], ['text'])
                self.assertEqual(receipts[name]['translated_controls'], ['text'])
            qss = Path(receipts['domainos']['css']).read_text(encoding='utf-8')
            self.assertIn('QTextEdit#domainosRecipeText {', qss)
            self.assertIn('QTextEdit#domainosRecipeText[domainosBackdrop="true"] {', qss)
            self.assertIn('QTextEdit#domainosRecipeText:disabled {', qss)
            self.assertIn('QTextEdit#domainosRecipeText:focus {', qss)
            self.assertIn('selection-background-color:', qss)
            self.assertIn('selection-color:', qss)

            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(base),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(base / '.config'),
                               XDG_DATA_HOME=str(base / '.local/share'),
                               XDG_STATE_HOME=str(base / '.local/state'),
                               XDG_CACHE_HOME=str(base / '.cache'), PYTHONPATH=str(SOURCE.parent),
                               PYTHONDONTWRITEBYTECODE='1')
            proofs = {}
            for name, receipt in receipts.items():
                output = base / ('probe-' + name)
                result = subprocess.run([
                    '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_text_widget.py'),
                    '--stylesheet', receipt['css'], '--output', str(output)],
                    env=environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
                proof = json.loads(result.stdout)
                self.assertEqual(proof['widgetClass'], 'QTextEdit')
                self.assertEqual(proof['objectName'], 'domainosRecipeText')
                for operation in ('nativeEditWorked', 'multiStepUndoWorked', 'redoCtrlYWorked',
                                  'redoCtrlShiftZWorked', 'copyWorked', 'cutWorked',
                                  'pasteWorked', 'selectAllWorked', 'nativeEditActionsPresent',
                                  'backdropPropertyApplied', 'normalScreenshotSaved',
                                  'backdropScreenshotSaved', 'disabledScreenshotSaved'):
                    self.assertTrue(proof[operation], f'{name}: {operation}')
                proofs[name] = proof
            from PIL import Image
            normal_pixels = [Image.open(proofs[name]['screenshots']['normal']).tobytes()
                             for name in ('domainos', 'neutral', 'dark', 'yellow')]
            backdrop_pixels = [Image.open(proofs[name]['screenshots']['backdrop']).tobytes()
                               for name in ('domainos', 'neutral', 'dark', 'yellow')]
            self.assertEqual(len(set(normal_pixels)), 4,
                             'real QTextEdit normal pixels must follow each selected KDE palette')
            self.assertEqual(len(set(backdrop_pixels)), 4,
                             'real QTextEdit backdrop pixels must follow each selected KDE palette')

    def test_qt6_arrow_recipe_uses_palette_roles_and_real_qtoolbutton_states(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 2
        project['recipes']['qt6']['visible_controls'] = 1 << 12
        project['recipes']['qt6']['selected_control'] = 12
        base_palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palettes = {'domainos': dict(base_palette)}
        for name, face in (('neutral', '#c8c8c8'), ('dark', '#242a31'),
                           ('yellow', '#dfd264')):
            palette = dict(base_palette)
            palette['theme_button_background_normal_breeze'] = face
            palette['theme_button_background_backdrop_breeze'] = face
            palette['theme_button_background_insensitive_breeze'] = face
            palette['theme_button_background_backdrop_insensitive_breeze'] = face
            palettes[name] = palette

        with tempfile.TemporaryDirectory(prefix='i170-qt6-arrow-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            receipts = {}
            proofs = {}
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(base),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(base / '.config'),
                               XDG_DATA_HOME=str(base / '.local/share'),
                               XDG_STATE_HOME=str(base / '.local/state'),
                               XDG_CACHE_HOME=str(base / '.cache'), PYTHONPATH=str(SOURCE.parent),
                               PYTHONDONTWRITEBYTECODE='1')
            for name, palette in palettes.items():
                receipt = self.generate(project, base / name, palette)
                receipts[name] = receipt
                self.assertEqual([row['id'] for row in route.records(project)], ['arrow'])
                self.assertEqual(receipt['translated_controls'], ['arrow'])
                qss = Path(receipt['css']).read_text(encoding='utf-8')
                self.assertIn('QToolButton#domainosRecipeArrow {', qss)
                self.assertIn('QToolButton#domainosRecipeArrow[domainosBackdrop="true"] {', qss)
                self.assertIn('QToolButton#domainosRecipeArrow:pressed {', qss)
                self.assertIn('QToolButton#domainosRecipeArrow:disabled {', qss)
                self.assertTrue((Path(receipt['asset_dir']) /
                                 'standalone-arrow-down-normal.png').is_file())
                result = subprocess.run([
                    '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_arrow_widget.py'),
                    '--stylesheet', receipt['css'], '--assets', receipt['asset_dir'],
                    '--output', str(base / ('probe-' + name))],
                    env=environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
                proof = json.loads(result.stdout)
                self.assertEqual(proof['widgetClass'], 'RecipeArrowButton')
                self.assertEqual(proof['size'], [15, 15])
                self.assertEqual(proof['glyphSize'], [11, 11])
                for key in ('clicked', 'pressedWhileHeld', 'backdropApplied',
                            'disabledApplied', 'screenshotsSaved'):
                    self.assertTrue(proof[key], f'{name}: {key}')
                for key in ('normalAssetPixelDifferences', 'pressedAssetPixelDifferences',
                            'releasedAssetPixelDifferences', 'disabledAssetPixelDifferences'):
                    self.assertEqual(proof[key], 0, f'{name}: {key}')
                proofs[name] = proof

            from PIL import Image
            for state in ('normal', 'backdrop', 'disabled'):
                pixels = [Image.open(proofs[name]['screenshots'][state]).tobytes()
                          for name in ('domainos', 'neutral', 'dark', 'yellow')]
                self.assertEqual(len(set(pixels)), 4,
                                 f'real QToolButton {state} pixels must follow each selected KDE palette')

    def test_qt6_progress_recipe_uses_palette_roles_and_native_range_text(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 2
        project['recipes']['qt6']['visible_controls'] = 1 << 13
        project['recipes']['qt6']['selected_control'] = 13
        base_palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palettes = {'domainos': dict(base_palette)}
        for name, (view, selection) in {
                'neutral': ('#c8c8c8', '#3976a8'),
                'dark': ('#242a31', '#397ca6'),
                'yellow': ('#dfd264', '#8f6a20')}.items():
            palette = dict(base_palette)
            for key in ('theme_base_color_breeze', 'theme_unfocused_base_color_breeze',
                        'theme_unfocused_view_bg_color_breeze'):
                palette[key] = view
            for key in ('theme_selected_bg_color_breeze', 'theme_unfocused_selected_bg_color_breeze',
                        'insensitive_selected_bg_color_breeze',
                        'insensitive_unfocused_selected_bg_color_breeze'):
                palette[key] = selection
            palettes[name] = palette

        with tempfile.TemporaryDirectory(prefix='i170-qt6-progress-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            proofs = {}
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(base),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(base / '.config'),
                               XDG_DATA_HOME=str(base / '.local/share'),
                               XDG_STATE_HOME=str(base / '.local/state'),
                               XDG_CACHE_HOME=str(base / '.cache'), PYTHONPATH=str(SOURCE.parent),
                               PYTHONDONTWRITEBYTECODE='1')
            for name, palette in palettes.items():
                receipt = self.generate(project, base / name, palette)
                self.assertEqual([row['id'] for row in route.records(project)], ['progress'])
                self.assertEqual(receipt['translated_controls'], ['progress'])
                qss = Path(receipt['css']).read_text(encoding='utf-8')
                for state in ('normal', 'backdrop', 'disabled'):
                    self.assertIn(
                        f'QProgressBar#domainosRecipeProgress[domainosState="{state}"]::chunk', qss)
                self.assertIn('QProgressBar#domainosRecipeProgress[domainosState="focused"]', qss)
                self.assertIn('color:', qss)
                result = subprocess.run([
                    '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_progress_widget.py'),
                    '--stylesheet', receipt['css'], '--output', str(base / ('probe-' + name))],
                    env=environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
                proof = json.loads(result.stdout)
                self.assertEqual(proof['widgetClass'], 'RecipeProgressBar')
                self.assertTrue(proof['nativeValueAndTextWorked'])
                self.assertGreater(proof['fillValueChangedPixels'], 0)
                self.assertTrue(proof['backdropApplied'] and proof['disabledApplied'])
                self.assertTrue(proof['screenshotsSaved'])
                proofs[name] = proof

            from PIL import Image
            for state in ('normal', 'backdrop', 'disabled'):
                pixels = [Image.open(proofs[name]['screenshots'][state]).tobytes()
                          for name in ('domainos', 'neutral', 'dark', 'yellow')]
                self.assertEqual(len(set(pixels)), 4,
                                 f'real QProgressBar {state} pixels must follow each selected KDE palette')

    def test_qt6_list_recipe_uses_palette_roles_and_native_selection(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 3
        project['recipes']['qt6']['visible_controls'] = 1 << 14
        project['recipes']['qt6']['selected_control'] = 14
        base_palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palettes = {'domainos': dict(base_palette)}
        for name, (view, selection) in {
                'neutral': ('#c8c8c8', '#3976a8'),
                'dark': ('#242a31', '#397ca6'),
                'yellow': ('#dfd264', '#8f6a20')}.items():
            palette = dict(base_palette)
            for key in ('theme_base_color_breeze', 'theme_unfocused_base_color_breeze',
                        'theme_unfocused_view_bg_color_breeze'):
                palette[key] = view
            for key in ('theme_text_color_breeze', 'theme_unfocused_view_text_color_breeze'):
                palette[key] = '#202020' if name != 'dark' else '#f4f4f4'
            for key in ('theme_selected_bg_color_breeze', 'theme_unfocused_selected_bg_color_breeze',
                        'insensitive_selected_bg_color_breeze',
                        'insensitive_unfocused_selected_bg_color_breeze'):
                palette[key] = selection
            palettes[name] = palette

        with tempfile.TemporaryDirectory(prefix='i170-qt6-list-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            proofs = {}
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(base),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(base / '.config'),
                               XDG_DATA_HOME=str(base / '.local/share'),
                               XDG_STATE_HOME=str(base / '.local/state'),
                               XDG_CACHE_HOME=str(base / '.cache'), PYTHONPATH=str(SOURCE.parent),
                               PYTHONDONTWRITEBYTECODE='1')
            for name, palette in palettes.items():
                receipt = self.generate(project, base / name, palette)
                self.assertEqual([row['id'] for row in route.records(project)], ['list'])
                self.assertEqual(receipt['translated_controls'], ['list'])
                qss = Path(receipt['css']).read_text(encoding='utf-8')
                self.assertIn('QTreeWidget#domainosRecipeList::item:selected', qss)
                self.assertIn('QTreeWidget#domainosRecipeList[domainosBackdrop="true"]', qss)
                self.assertIn('QTreeWidget#domainosRecipeList:disabled', qss)
                self.assertIn('QTreeWidget#domainosRecipeList:focus', qss)
                result = subprocess.run([
                    '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_list_widget.py'),
                    '--stylesheet', receipt['css'], '--output', str(base / ('probe-' + name))],
                    env=environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
                proof = json.loads(result.stdout)
                self.assertEqual(proof['widgetClass'], 'QTreeWidget')
                self.assertEqual(proof['rowCount'], 40)
                self.assertEqual(proof['selectedAfterMouse'], 2)
                self.assertEqual(proof['selectedAfterKeyboard'], 3)
                self.assertTrue(proof['selectedItem'] and proof['selectedRows'] == 1)
                self.assertTrue(proof['backdropApplied'] and proof['disabled'])
                self.assertTrue(proof['screenshotsSaved'])
                for axis in ('verticalScrollbar', 'horizontalScrollbar'):
                    self.assertTrue(proof[axis]['visible'])
                    self.assertGreater(proof[axis]['maximum'], 0)
                proofs[name] = proof

            from PIL import Image
            for state in ('selected', 'unselected', 'backdrop', 'disabled'):
                pixels = [Image.open(proofs[name]['screenshots'][state]).tobytes()
                          for name in ('domainos', 'neutral', 'dark', 'yellow')]
                self.assertEqual(len(set(pixels)), 4,
                                 f'real QTreeWidget {state} pixels must follow each selected KDE palette')

    def test_qt6_frame_recipe_uses_kde_roles_for_real_panel_bevel_states(self):
        project = model()
        project['recipes']['qt6']['visible_categories'] = 1 << 4
        project['recipes']['qt6']['visible_controls'] = 1 << 15
        project['recipes']['qt6']['selected_control'] = 15
        base_palette = dict(backend.load_builder(ROOT).art.DEFAULT)
        palettes = {'domainos': dict(base_palette)}
        for name, view in {'neutral': '#c8c8c8', 'dark': '#242a31',
                           'yellow': '#dfd264'}.items():
            palette = dict(base_palette)
            for key in ('theme_base_color_breeze', 'theme_unfocused_base_color_breeze',
                        'theme_unfocused_view_bg_color_breeze'):
                palette[key] = view
            palette['insensitive_base_color_breeze'] = {
                'neutral': '#e5e5e5', 'dark': '#333333', 'yellow': '#807020'}[name]
            palette['theme_text_color_breeze'] = '#202020' if name != 'dark' else '#f4f4f4'
            palette['theme_unfocused_view_text_color_breeze'] = palette['theme_text_color_breeze']
            palette['insensitive_base_fg_color_breeze'] = '#484848' if name != 'dark' else '#b0b5bb'
            palettes[name] = palette

        with tempfile.TemporaryDirectory(prefix='i170-qt6-frame-', dir=TEMP_ROOT) as temp:
            base = Path(temp)
            proofs = {}
            temp_dir = base / 'tmp'
            temp_dir.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', HOME=str(base),
                               TMPDIR=str(temp_dir), XDG_CONFIG_HOME=str(base / '.config'),
                               XDG_DATA_HOME=str(base / '.local/share'),
                               XDG_STATE_HOME=str(base / '.local/state'),
                               XDG_CACHE_HOME=str(base / '.cache'), PYTHONPATH=str(SOURCE.parent),
                               PYTHONDONTWRITEBYTECODE='1')
            for name, palette in palettes.items():
                receipt = self.generate(project, base / name, palette)
                self.assertEqual([row['id'] for row in route.records(project)], ['frame'])
                self.assertEqual(receipt['translated_controls'], ['frame'])
                qss = Path(receipt['css']).read_text(encoding='utf-8')
                self.assertIn('QFrame#domainosRecipeFrame {', qss)
                self.assertIn('QFrame#domainosRecipeFrame[domainosBackdrop="true"] {', qss)
                self.assertIn('QFrame#domainosRecipeFrame:disabled {', qss)
                result = subprocess.run([
                    '/usr/bin/python3', '-B', str(SOURCE.parent / 'tests/probe_qt6_frame_widget.py'),
                    '--stylesheet', receipt['css'], '--output', str(base / ('probe-' + name))],
                    env=environment, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
                proof = json.loads(result.stdout)
                self.assertEqual(proof['widgetClass'], 'QFrame')
                self.assertEqual(proof['frameShape'], 2)
                self.assertEqual(proof['frameShadow'], 48)
                self.assertEqual(proof['lineWidth'], 2)
                self.assertEqual(proof['normalFace']['expectedKdeRoleDerived'],
                                 proof['normalFace']['actualPixel'])
                self.assertEqual(proof['backdropFace']['expectedKdeRoleDerived'],
                                 proof['backdropFace']['actualPixel'])
                self.assertEqual(proof['disabledFace']['expectedKdeRoleDerived'],
                                 proof['disabledFace']['actualPixel'])
                self.assertGreater(proof['statePixelChanges']['disabled'], 0)
                proofs[name] = proof

            from PIL import Image
            for state in ('normal', 'backdrop', 'disabled'):
                pixels = [Image.open(proofs[name]['screenshots'][state]).tobytes()
                          for name in ('domainos', 'neutral', 'dark', 'yellow')]
                self.assertEqual(len(set(pixels)), 4,
                                 f'real QFrame {state} pixels must follow each selected KDE palette')


if __name__ == '__main__':
    unittest.main(verbosity=2)
