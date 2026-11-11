# SPDX-License-Identifier: GPL-3.0-or-later
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gtk2_indicators import indicator_pixels
from gtk2_radios import paint_radio
from test_backend import backend,model,ROOT


class RadioTests(unittest.TestCase):
    def test_default_radio_uses_independent_motif_local_geometry(self):
        art=backend.load_builder(ROOT).art
        self.assertEqual(len(indicator_pixels(art,15,2,False,'radio')),15)
        self.assertEqual(indicator_pixels(art,15,2,False,'radio')[0],[None]*15)
        self.assertEqual(indicator_pixels(art,15,2,True,'radio')[0],[None]*15)

    def test_impossible_geometry_and_missing_role_do_not_create_output(self):
        builder=backend.load_builder(ROOT);recipe=model()['recipes']['gtk2']
        with tempfile.TemporaryDirectory(dir=Path.home()/'tempia',prefix='i167-radio-pure-') as folder:
            target=Path(folder)/'absent'
            bad=copy.deepcopy(recipe);bad['geometry']['radio_indicator_px']=5
            with self.assertRaisesRegex(ValueError,'interior'):paint_radio(builder,bad,{},target)
            self.assertFalse(target.exists())
            with self.assertRaisesRegex(ValueError,'effective role'):paint_radio(builder,recipe,{},target)
            self.assertFalse(target.exists())

    def test_option_detail_and_shared_prelight_background_are_scoped(self):
        builder=backend.load_builder(ROOT);recipe=model()['recipes']['gtk2'];before=copy.deepcopy(recipe)
        palette={name:'#789abc' for role in ('button','button-fg','window','window-fg')
                 for name in builder.art.ROLES[role]}
        with tempfile.TemporaryDirectory(dir=Path.home()/'tempia',prefix='i167-radio-pure-') as folder:
            r=paint_radio(builder,recipe,palette,folder);rc=Path(r['rc']).read_text()
            self.assertEqual(r['translated_control'],'radio')
            self.assertEqual(len(r['assets']),9)
            self.assertEqual(recipe['geometry']['arrow_px'],11)
            self.assertIn('function = OPTION detail = "radiobutton"',rc)
            self.assertIn('GtkCheckButton::indicator-size = 15',rc)
            self.assertIn('GtkCheckButton::indicator-spacing = 2',rc)
            self.assertIn('function = FLAT_BOX detail = "checkbutton"',rc)
            self.assertIn('themeLabRadio',rc)
            self.assertNotIn('function = CHECK',rc)
        self.assertEqual(recipe,before)

    def test_motif_native_symbolic_masks_match_unselected_and_selected(self):
        art=backend.load_builder(ROOT).art
        expected_off=(
            '......L......','.....LLL.....','....LLLLL....','...LLLFLLL...',
            '..LLL...LLL..','.LLL.....LLL.','LLL.......DDD','.DDD.....DDD.',
            '..DDD...DDD..','...DDD.DDD...','....DDDDD....','.....DDD.....','......D......')
        expected_on=(
            '......D......','.....DDD.....','....DDDDD....','...DDDSDDD...',
            '..DDDSSSDDD..','.DDDSSSSSDDDF','DDDSSSSSSSLLL','.LLLSSSSSLLLF',
            '..LLLSSSLLL..','...LLLSLLL...','....LLLLL....','.....LLL.....','......L......')
        for selected, expected in ((False,expected_off),(True,expected_on)):
            image=indicator_pixels(art,15,2,selected,'radio')[1:14]
            roles={'light':'L','dark':'D','face':'F','trough':'S'}
            actual=[''.join(roles.get(value,'.') for value in row[1:14]) for row in image]
            self.assertEqual(actual,list(expected))


if __name__ == '__main__':unittest.main()
