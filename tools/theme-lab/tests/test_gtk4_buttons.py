# SPDX-License-Identifier: GPL-3.0-or-later
import copy,json,tempfile,unittest
from pathlib import Path
from test_backend import backend,ROOT,model
from gtk4_buttons import write_button_css


class Gtk4ButtonTests(unittest.TestCase):
    def setUp(self):
        self.builder=backend.load_builder(ROOT)
        self.palette={key:'#748596' for role in ('button','button-fg') for key in self.builder.art.ROLES[role]}
        self.recipe=model()['recipes']['gtk4']
        self.temp=tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-buttons-')
    def tearDown(self):self.temp.cleanup()
    def test_private_recipe_is_not_mutated(self):
        before=copy.deepcopy(self.recipe);result=write_button_css(self.builder,self.recipe,self.palette,Path(self.temp.name)/'generated')
        self.assertEqual(self.recipe,before);self.assertEqual(len(result['assets']),4)
        css=Path(result['css']).read_text();self.assertIn('background-image:',css);self.assertIn(':active',css)
    def test_flat_recipe_and_lighting_identity(self):
        destination=Path(self.temp.name)
        first=write_button_css(self.builder,self.recipe,self.palette,destination/'first')
        self.recipe['palette']['light']=.35
        second=write_button_css(self.builder,self.recipe,self.palette,destination/'second')
        self.assertNotEqual(first['style_class'],second['style_class'])
        self.recipe['geometry']['shadow_px']=0
        flat=write_button_css(self.builder,self.recipe,self.palette,destination/'flat')
        self.assertIn('background-image: none;',Path(flat['css']).read_text())
        self.assertNotIn('calc(100%',Path(flat['css']).read_text())

    def test_missing_role_refuses_before_output(self):
        destination=Path(self.temp.name)/'missing'
        with self.assertRaisesRegex(ValueError,'effective KDE role'):write_button_css(self.builder,self.recipe,{},destination)
        self.assertFalse(destination.exists())
    def test_invalid_geometry_refuses_before_output(self):
        self.recipe['geometry']['shadow_px']=-1;destination=Path(self.temp.name)/'invalid'
        with self.assertRaises(ValueError):write_button_css(self.builder,self.recipe,self.palette,destination)
        self.assertFalse(destination.exists())


if __name__=='__main__':unittest.main()
