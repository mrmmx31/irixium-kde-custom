#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt5 scrollbar adapter generation and real-widget contract tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'backend.py'
ROOT = SOURCE.parents[2]
TEMP = Path.home() / 'tempia' / 'qt5-scrollbar-tests'
TEMP.mkdir(mode=0o700, parents=True, exist_ok=True)
sys.path.insert(0, str(SOURCE.parent))
import backend
import qt5_scrollbar_recipe as adapter


def model():
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    recipes = {}
    for family in backend.FAMILIES:
        recipes[family] = {'geometry': geometry.copy(), 'palette': palette.copy(),
            'visible_categories': (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4),
            'visible_controls': sum(1 << bit for bit in range(16)),
                           'selected_control': 10,
                           'positions': [[16, 16] for _ in range(16)],
                           'sizes': [[0, 0] for _ in range(16)]}
    return {'schema_version': 1, 'kind': 'theme_lab_project',
            'name': 'Qt5 scrollbar test fixture', 'reference': '',
            'selected_family': 'qt5', 'color_scheme': 'fixture',
            'recipes': recipes}


class Qt5ScrollbarRecipeTests(unittest.TestCase):
    def setUp(self):
        self.builder = backend.load_builder(ROOT)
        self.palette = dict(self.builder.art.DEFAULT)
        self.selected = {'path': str(TEMP / 'selected.colors'), 'sha256': 'a' * 64,
                         'scheme_id': 'fixture', 'scheme_name': 'fixture palette'}
        self.origin = {'path': self.selected['path'], 'sha256': self.selected['sha256'],
                       'helper': {'path': '/fixture/helper', 'sha256': 'b' * 64},
                       'helper_source': {'path': '/fixture/source', 'sha256': 'c' * 64}}

    def generate(self, project, folder, palette=None):
        selected_palette = self.palette if palette is None else palette
        def private_dir(path, _root):
            Path(path).mkdir(mode=0o700, parents=True, exist_ok=True)
            return Path(path)
        with (patch.object(backend, 'load_builder', return_value=self.builder),
              patch.object(backend, 'selected_palette', return_value=(None, self.selected)),
              patch.object(backend, 'native_roles', return_value=(selected_palette, self.origin)),
              patch.object(backend, 'palette_inputs_current', return_value=True),
              patch.object(backend, 'private_output', side_effect=private_dir)):
            return adapter.generate(ROOT, folder, project,
                                    backend.sha(json.dumps(project, sort_keys=True).encode()),
                                    Path('/unused/kdeglobals'))

    def test_contract_and_generation_are_family_scoped(self):
        project = model()
        with tempfile.TemporaryDirectory(prefix='generation-', dir=TEMP) as temporary:
            receipt = self.generate(project, Path(temporary) / 'snapshot')
            self.assertEqual(receipt['family'], 'qt5')
            self.assertEqual(receipt['status'], 'partially_generated')
            self.assertEqual(receipt['translated_controls'], ['arrow', 'check', 'combo', 'entry', 'frame', 'list', 'progress', 'push', 'radio', 'scale_h', 'scale_v', 'scroll_h', 'scroll_v', 'spin', 'text', 'toggle'])
            self.assertEqual(receipt['geometry']['bar_cross_px'], 15)
            self.assertTrue(receipt['palette_roles_applied'])
            self.assertEqual(receipt['selected_scheme']['path'], receipt['palette_inputs'][0]['path'])
            def private_dir(path, _root):
                return Path(path)
            with (patch.object(backend, 'private_output', side_effect=private_dir),
                  patch.object(backend, 'palette_inputs_current', return_value=True)):
                self.assertTrue(adapter.verify(ROOT, receipt, project)['artifacts'])
            self.assertIn('QScrollBar#domainosScrollBarVertical',
                          Path(receipt['css']).read_text(encoding='utf-8'))
            self.assertIn('QPushButton#domainosRecipePushButton:pressed',
                          Path(receipt['css']).read_text(encoding='utf-8'))
            self.assertIn('QPushButton#domainosRecipeToggleButton:checked',
                          Path(receipt['css']).read_text(encoding='utf-8'))
            self.assertIn('QCheckBox#domainosRecipeCheckBox::indicator:checked',
                          Path(receipt['css']).read_text(encoding='utf-8'))
            self.assertIn('QRadioButton#domainosRecipeRadioButton::indicator:checked',
                          Path(receipt['css']).read_text(encoding='utf-8'))
            self.assertIn('QRadioButton#domainosRecipeRadioPeer::indicator:checked',
                          Path(receipt['css']).read_text(encoding='utf-8'))
            self.assertTrue((Path(receipt['asset_dir']) / 'check-on-normal.png').is_file())
            self.assertTrue((Path(receipt['asset_dir']) / 'check-off-normal.png').is_file())
            self.assertTrue((Path(receipt['asset_dir']) / 'radio-on-normal.png').is_file())
            self.assertTrue((Path(receipt['asset_dir']) / 'radio-off-normal.png').is_file())
            css = Path(receipt['css']).read_text(encoding='utf-8')
            self.assertIn('QLineEdit#domainosRecipeEntry:focus', css)
            self.assertIn('selection-background-color:', css)
            self.assertIn('QLineEdit#domainosRecipeEntry:disabled', css)
            self.assertIn('QTextEdit#domainosRecipeText:focus', css)
            self.assertIn('QTextEdit#domainosRecipeText:disabled', css)
            self.assertIn('QTextEdit#domainosRecipeText', css)
            self.assertIn('QSlider#domainosRecipeScaleHorizontal::groove:horizontal', css)
            self.assertIn('QSlider#domainosRecipeScaleVertical::handle:vertical:disabled', css)
            self.assertIn('QSlider#domainosRecipeScaleHorizontal::handle:horizontal:focus', css)
            self.assertIn('QSlider#domainosRecipeScaleHorizontal::groove:horizontal:disabled', css)
            self.assertIn('QComboBox#domainosRecipeCombo::down-arrow:disabled', css)
            self.assertIn('QComboBox#domainosRecipeCombo:on::down-arrow', css)
            self.assertIn('subcontrol-origin: padding; subcontrol-position: center;', css)
            self.assertIn('QAbstractItemView#domainosRecipeComboPopup::item:selected', css)
            self.assertIn('QSpinBox#domainosRecipeSpinBox::up-button', css)
            self.assertIn('QDoubleSpinBox#domainosRecipeDoubleSpinBox::down-arrow:disabled', css)
            self.assertIn('QSpinBox#domainosRecipeSpinBox::up-arrow:off', css)
            self.assertIn('QToolButton#domainosRecipeArrow:pressed', css)
            self.assertIn('QToolButton#domainosRecipeArrow:disabled', css)
            self.assertIn('QToolButton#domainosRecipeArrow:focus', css)
            self.assertIn('QProgressBar#domainosRecipeProgress[domainosState="normal"]::chunk', css)
            self.assertIn('QProgressBar#domainosRecipeProgress[domainosState="backdrop"]::chunk', css)
            self.assertIn('QProgressBar#domainosRecipeProgress[domainosState="disabled"]::chunk', css)
            self.assertIn('QProgressBar#domainosRecipeProgress[domainosState="focused"]', css)
            self.assertIn('QTreeWidget#domainosRecipeList:!active', css)
            self.assertIn('QTreeWidget#domainosRecipeList:disabled', css)
            self.assertIn('QTreeWidget#domainosRecipeList:focus', css)
            self.assertIn('selection-background-color:', css)
            self.assertIn('selection-color:', css)
            self.assertIn('QFrame#domainosRecipeFrame', css)
            self.assertIn('QFrame#domainosRecipeFrame:!active', css)
            self.assertIn('QFrame#domainosRecipeFrame:disabled', css)
            for state in adapter.STATES:
                self.assertTrue((Path(receipt['asset_dir']) / f'standalone-arrow-down-{state}.png').is_file())
            for state in adapter.STATES:
                self.assertTrue((Path(receipt['asset_dir']) / f'combo-arrow-down-{state}.png').is_file())
                for direction in ('up', 'down'):
                    self.assertTrue((Path(receipt['asset_dir']) / f'spin-arrow-{direction}-{state}.png').is_file())
            output = Path(temporary) / 'list-probe'
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen',
                               HOME=str(Path(temporary) / 'home'),
                               TMPDIR=str(TEMP), PYTHONDONTWRITEBYTECODE='1')
            Path(environment['HOME']).mkdir(mode=0o700)
            probe = SOURCE.parent / 'tests/probe_qt5_list_widget.py'
            result = subprocess.run(['/usr/bin/python3', '-B', str(probe),
                                     '--stylesheet', receipt['css'],
                                     '--output', str(output)],
                                    env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['status'], 'passed')
            self.assertEqual(proof['widgetClass'], 'QTreeWidget')
            self.assertEqual(proof['selectedAfterMouse'], 2)
            self.assertEqual(proof['selectedAfterKeyboard'], 3)
            self.assertTrue(proof['verticalScrollbar']['visible'])
            self.assertTrue(proof['horizontalScrollbar']['visible'])
            self.assertGreater(proof['selectionChangesPixels'], 0)
            self.assertGreater(proof['disabledChangesPixels'], 0)
            frame_probe = SOURCE.parent / 'tests/probe_qt5_frame_widget.py'
            frame_result = subprocess.run(
                ['/usr/bin/python3', '-B', str(frame_probe),
                 '--stylesheet', receipt['css'],
                 '--output', str(Path(temporary) / 'frame-probe')],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(frame_result.returncode, 0,
                             frame_result.stderr + '\n' + frame_result.stdout)
            frame_proof = json.loads(frame_result.stdout)
            self.assertEqual(frame_proof['widgetClass'], 'QFrame')
            self.assertEqual(frame_proof['frameShadow'], 48)
            self.assertEqual(frame_proof['normalFace']['actualPixel'],
                             frame_proof['normalFace']['expectedKdeRoleDerived'])
            self.assertEqual(frame_proof['disabledFace']['actualPixel'],
                             frame_proof['disabledFace']['expectedKdeRoleDerived'])
            self.assertGreater(frame_proof['disabledPixelChanges'], 0)

    def test_selected_kde_roles_change_generated_qss_and_arrow_assets(self):
        project = model()
        changed = dict(self.palette)
        changed['theme_button_background_normal_breeze'] = '#345678'
        with tempfile.TemporaryDirectory(prefix='palette-', dir=TEMP) as temporary:
            first = self.generate(project, Path(temporary) / 'first', self.palette)
            second = self.generate(project, Path(temporary) / 'second', changed)
            self.assertNotEqual(Path(first['css']).read_bytes(), Path(second['css']).read_bytes())
            self.assertNotEqual((Path(first['asset_dir']) / 'arrow-down-normal.png').read_bytes(),
                                (Path(second['asset_dir']) / 'arrow-down-normal.png').read_bytes())
            self.assertNotEqual((Path(first['asset_dir']) / 'combo-arrow-down-normal.png').read_bytes(),
                                (Path(second['asset_dir']) / 'combo-arrow-down-normal.png').read_bytes())
            self.assertTrue(first['palette_roles_applied'] and second['palette_roles_applied'])

    def test_qt5_real_widgets_apply_recipe_and_keep_scroll_range(self):
        project = model()
        with tempfile.TemporaryDirectory(prefix='native-', dir=TEMP) as temporary:
            base = Path(temporary)
            disabled_palette = dict(self.palette)
            disabled_palette.update({
                'insensitive_base_color_breeze': '#b0a080',
                'insensitive_base_fg_color_breeze': '#432810',
                'insensitive_selected_bg_color_breeze': '#6f5830',
                'insensitive_selected_fg_color_breeze': '#f2e8c0',
            })
            receipt = self.generate(project, base / 'snapshot', disabled_palette)
            output = base / 'probe'
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen',
                               HOME=str(base / 'home'), TMPDIR=str(TEMP),
                               XDG_CONFIG_HOME=str(base / 'home/.config'),
                               XDG_DATA_HOME=str(base / 'home/.local/share'),
                               XDG_STATE_HOME=str(base / 'home/.local/state'),
                               XDG_CACHE_HOME=str(base / 'home/.cache'),
                               PYTHONDONTWRITEBYTECODE='1')
            Path(environment['HOME']).mkdir(mode=0o700)
            probe = SOURCE.parent / 'tests/probe_qt5_scrollbar_widget.py'
            result = subprocess.run(['/usr/bin/python3', '-B', str(probe),
                                     '--stylesheet', receipt['css'],
                                     '--assets', receipt['asset_dir'],
                                     '--output', str(output)],
                                    env=environment, capture_output=True, text=True, timeout=25)
            self.assertEqual(result.returncode, 0, result.stderr + '\n' + result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(proof['status'], 'passed')
            self.assertEqual(proof['qtMajor'], 5)
            self.assertEqual(proof['pushButton']['widgetClass'], 'QPushButton')
            self.assertGreater(proof['pushButton']['heldReliefPixelChanges'], 0)
            self.assertEqual(proof['pushButton']['releasePixelChanges'], 0)
            self.assertEqual(proof['pushButton']['clickCount'], 1)
            self.assertEqual(proof['checkBox']['widgetClass'], 'QCheckBox')
            self.assertTrue(proof['checkBox']['checkedAfterClick'])
            self.assertGreater(proof['checkBox']['checkedPixelChanges'], 0)
            self.assertTrue(proof['checkBox']['uncheckedAfterSecondClick'])
            self.assertEqual(proof['checkBox']['restoredPixelChanges'], 0)
            self.assertEqual(proof['checkBox']['checkedAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['checkBox']['uncheckedAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['radioButtons']['widgetClass'], 'QRadioButton')
            self.assertTrue(proof['radioButtons']['exclusiveGroup'])
            self.assertTrue(proof['radioButtons']['selectedAfterPeerClick'])
            self.assertTrue(proof['radioButtons']['returnedToFirst'])
            self.assertGreater(proof['radioButtons']['selectionPixelChanges'], 0)
            self.assertEqual(proof['radioButtons']['initialCheckedAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['radioButtons']['initialUncheckedAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['radioButtons']['peerCheckedAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['radioButtons']['radioUncheckedAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['entry']['widgetClass'], 'QLineEdit')
            self.assertTrue(proof['entry']['focused'])
            self.assertTrue(proof['entry']['nativeEditWorked'])
            self.assertTrue(proof['entry']['selectionWorked'])
            self.assertTrue(proof['entry']['disabled'])
            self.assertEqual(proof['entry']['normalFacePixel'], proof['entry']['expectedNormalFace'])
            self.assertEqual(proof['entry']['disabledFacePixel'], proof['entry']['expectedDisabledFace'])
            self.assertEqual(proof['comboBox']['widgetClass'], 'QComboBox')
            self.assertTrue(proof['comboBox']['popupOpened'])
            self.assertTrue(proof['comboBox']['nativeSelectionWorked'])
            self.assertEqual(proof['comboBox']['selectedIndex'], 2)
            self.assertTrue(proof['comboBox']['popupClosedAfterSelection'])
            self.assertTrue(proof['comboBox']['disabled'])
            self.assertEqual(proof['comboBox']['normalFacePixel'], proof['comboBox']['normalFaceRole'])
            self.assertEqual(proof['comboBox']['disabledFacePixel'], proof['comboBox']['disabledFaceRole'])
            self.assertEqual(proof['comboBox']['normalArrowAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['comboBox']['disabledArrowAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['spinBoxes']['integer']['widgetClass'], 'QSpinBox')
            self.assertEqual(proof['spinBoxes']['decimal']['widgetClass'], 'QDoubleSpinBox')
            self.assertEqual(proof['spinBoxes']['integer']['valueAfterUp'], 43)
            self.assertEqual(proof['spinBoxes']['integer']['valueAfterDown'], 42)
            self.assertEqual(proof['spinBoxes']['decimal']['valueAfterUp'], 10.5)
            self.assertEqual(proof['spinBoxes']['decimal']['valueAfterDown'], 10.4)
            self.assertTrue(proof['spinBoxes']['integer']['disabled'])
            self.assertTrue(proof['spinBoxes']['decimal']['disabled'])
            self.assertEqual(proof['spinBoxes']['integer']['upArrowAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['spinBoxes']['integer']['downArrowAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['spinBoxes']['integer']['disabledUpArrowAsset']['pixelDifferences'], 0)
            self.assertEqual(proof['spinBoxes']['integer']['disabledDownArrowAsset']['pixelDifferences'], 0)
            for orientation in ('horizontal', 'vertical'):
                scale = proof['scales'][orientation]
                self.assertEqual(scale['widgetClass'], 'QSlider')
                self.assertNotEqual(scale['valueAfterMouse'], scale['initialValue'])
                self.assertNotEqual(scale['valueAfterKey'], scale['valueBeforeKey'])
                self.assertTrue(scale['disabled'])
            self.assertTrue(proof['scales']['screenshotSaved'])
            arrow = proof['standaloneArrow']
            self.assertEqual(arrow['widgetClass'], 'RecipeArrowButton')
            self.assertEqual(arrow['clickCount'], 2)
            self.assertTrue(arrow['disabled'])
            self.assertEqual(arrow['normalAsset']['pixelDifferences'], 0)
            self.assertEqual(arrow['pressedAsset']['pixelDifferences'], 0)
            self.assertEqual(arrow['releasedAsset']['pixelDifferences'], 0)
            self.assertEqual(arrow['disabledAsset']['pixelDifferences'], 0)
            self.assertTrue(arrow['screenshotSaved'])
            progress = proof['progressBar']
            self.assertEqual(progress['widgetClass'], 'RecipeProgressBar')
            self.assertEqual(progress['initialText'], '43%')
            self.assertEqual(progress['textAfterChange'], '70%')
            self.assertGreater(progress['fillValueChangedPixels'], 0)
            self.assertTrue(progress['disabled'])
            self.assertGreater(progress['disabledStateChangedPixels'], 0)
            self.assertTrue(progress['normalScreenshotSaved'] and progress['disabledScreenshotSaved'])
            self.assertEqual(proof['toggleButton']['widgetClass'], 'QPushButton')
            self.assertTrue(proof['toggleButton']['checkable'])
            self.assertTrue(proof['toggleButton']['checkedAfterClick'])
            self.assertGreater(proof['toggleButton']['checkedPixelChanges'], 0)
            self.assertFalse(proof['toggleButton']['checkedAfterSecondClick'])
            self.assertEqual(proof['toggleButton']['restoredPixelChanges'], 0)
            self.assertEqual(set(proof['axes']['vertical']['cells']), {'up', 'down'})
            self.assertEqual(set(proof['axes']['horizontal']['cells']), {'left', 'right'})
            for axis in proof['axes'].values():
                for cell in axis['cells'].values():
                    self.assertGreater(cell['heldReliefPixelChanges'], 0)
                    self.assertEqual(cell['releasePixelChanges'], 0)

    def test_other_controls_and_recipe_overrides_fail_closed(self):
        project = model()
        project['recipes']['qt5']['scrollbar_parts'] = {'arrow': {'glyph_px': 9}}
        with tempfile.TemporaryDirectory(prefix='invalid-', dir=TEMP) as temporary:
            with self.assertRaisesRegex(backend.Unavailable, 'custom per-piece overrides'):
                self.generate(project, Path(temporary) / 'snapshot')


if __name__ == '__main__':
    unittest.main(verbosity=2)
