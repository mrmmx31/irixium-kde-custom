# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import tempfile
import unittest
from test_backend import ROOT,model,backend
from gtk4_buttons import write_button_css
from gtk4_toggles import depressed,write_toggle_css
from gtk4_toggle_session import button_records, ToggleScene
from gtk4_scene_contract import push_records


class ToggleTests(unittest.TestCase):
    def test_private_session_contract_does_not_expand_public_push(self):
        project=model();project['recipes']['gtk4']['visible_controls']=3
        self.assertEqual([r['id'] for r in button_records(project)],['push','toggle'])
        with self.assertRaisesRegex(ValueError,'pending'):push_records(project)
        project['recipes']['gtk4']['visible_controls']=4
        with self.assertRaisesRegex(ValueError,'pending'):button_records(project)

    def test_selection_validation_precedes_native_construction(self):
        for value in ({1:1},{0:True},{'1':True}):
            with self.assertRaisesRegex(ValueError,'selection requires'):
                ToggleScene(selection=value)

    def test_prospective_relief_and_disabled_selection(self):
        self.assertFalse(depressed(False,False));self.assertTrue(depressed(False,True))
        self.assertTrue(depressed(True,False));self.assertFalse(depressed(True,True))
        self.assertTrue(depressed(True,True,True));self.assertFalse(depressed(False,True,True))
        with self.assertRaises(ValueError):depressed(1,False)

    def test_generator_reuses_base_roles_without_literal_colors(self):
        builder=backend.load_builder(ROOT);recipe=model()['recipes']['gtk4'];before=copy.deepcopy(recipe)
        colors={k:'#748596' for role in ('button','button-fg') for k in builder.art.ROLES[role]}
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-toggle-') as d:
            folder=Path(d);base=write_button_css(builder,recipe,colors,folder/'base')
            receipt=write_toggle_css(builder,recipe,colors,folder/'toggle',base)
            source=Path(receipt['css']).read_text();self.assertNotRegex(source,r'#[0-9a-fA-F]{6}\b')
            self.assertIn(':checked:active:not(:disabled)',source)
            self.assertIn(':checked:disabled',source)
            self.assertIn('@lab_push_disabled_face',source)
            self.assertEqual(len(list((folder/'toggle').glob('*.png'))),48)
            self.assertFalse(receipt['public_support_announced'])
            self.assertEqual(recipe,before)

    def test_mismatched_base_is_rejected_before_output(self):
        builder=backend.load_builder(ROOT);recipe=model()['recipes']['gtk4']
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-toggle-') as d:
            destination=Path(d)/'toggle'
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                write_toggle_css(builder,recipe,{},destination,{'style_class':'stale'})
            self.assertFalse(destination.exists())


if __name__=='__main__':unittest.main()
