# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

import backend
from gtk4_scrollbars import geometry, selected_fragment
from gtk4_scrollbar_snapshot import generate_snapshot, verify_snapshot
from test_backend import ROOT, model


class GTK4ScrollbarTests(unittest.TestCase):
    def setUp(self):
        self.data = model()
        self.data['selected_family'] = 'gtk4'
        self.data['recipes']['gtk4']['visible_categories'] = 1 << 2
        self.data['recipes']['gtk4']['visible_controls'] = (1 << 10) | (1 << 11)
        self.kde = ROOT / 'colors/DomainOS-SR10.4.colors'
        self.builder = backend.load_builder(ROOT)
        _config, selected = backend.selected_palette(self.data, self.kde, ROOT)
        self.palette, _origin = backend.native_roles(ROOT, Path(selected['path']),
                                                     self.builder.art, selected['sha256'])

    def test_contract_geometry_tracks_shared_measured_reference(self):
        contract=json.loads((ROOT/'tools/domainos_scrollbar_rules.json').read_text())
        geom=self.data['recipes']['gtk4']['geometry']
        for key in ('bar_px','shadow_px','thumb_cross_px'):
            self.assertEqual(geom[key],contract['geometry'][key])
        self.assertEqual(geometry(self.data['recipes']['gtk4']), (15,2,11))

    def test_snapshot_generates_role_based_native_css_and_verified_assets(self):
        before=copy.deepcopy(self.data)
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-scrollbar-') as tmp:
            folder=Path(tmp)/'snapshot'
            receipt=generate_snapshot(ROOT,folder,self.data,'a'*64,self.kde)
            self.assertEqual(receipt['status'],'partially_generated')
            self.assertEqual(receipt['translated_controls'],['scroll_h','scroll_v'])
            self.assertFalse(receipt['recipe_applied'])
            self.assertEqual(receipt['geometry'],{'bar_cross_px':15,'shadow_px':2,
                                                   'thumb_cross_px':11,
                                                   'length':'native adjustment/page size'})
            self.assertEqual(receipt['arrows'],'not available in GTK4; no substitute drawn or bound')
            css=Path(receipt['css']).read_text(encoding='utf-8')
            self.assertIn('.vertical > range > trough > slider',css)
            self.assertIn('.horizontal > range > trough > slider',css)
            self.assertIn(':active',css)
            self.assertIn(':backdrop',css)
            self.assertIn(':disabled',css)
            self.assertNotRegex(css,r'arrow|stepper')
            self.assertTrue(all((folder/name).is_file() for name in receipt['artifacts']))
            self.assertEqual(verify_snapshot(ROOT,folder,self.data,'a'*64)[0],receipt)
        self.assertEqual(self.data,before)

    def test_snippets_are_state_specific_and_keep_absent_arrow_contract(self):
        original=copy.deepcopy(self.data)
        recipe=self.data['recipes']['gtk4']
        with backend.recipe_rules(self.builder,recipe['palette']):
            for state in ('normal','pressed','backdrop','disabled','hover'):
                for control in ('scroll_h','scroll_v'):
                    result=backend.snippet(ROOT,self.data,'gtk4',control,state,self.kde)
                    self.assertEqual(result['status'],'ok')
                    self.assertEqual(result['source_kind'],'translated_native_fragment')
                    self.assertEqual(result['language'],'css')
                    self.assertIn('@import url("scrollbar.css");',result['source'])
                    self.assertIn('GtkAdjustment',result['source'])
                    expressions=re.sub(r'mix\([^,]+,\s*#(?:000000|ffffff),\s*[0-9.]+\)', '', result['source'])
                    self.assertNotRegex(expressions,r'#[0-9a-fA-F]{6}\b')
                    self.assertNotRegex(result['source'],r'arrow|stepper')
        self.assertEqual(self.data,original)

    def test_invalid_geometry_is_rejected(self):
        recipe=copy.deepcopy(self.data['recipes']['gtk4'])
        recipe['geometry']['bar_px']=14
        with self.assertRaisesRegex(ValueError,'bar must contain thumb'):
            geometry(recipe)


if __name__=='__main__':
    unittest.main()
