# SPDX-License-Identifier: GPL-3.0-or-later
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_backend import ROOT,model
from gtk4_generation import generate_snapshot,verify_snapshot,verify_initial_snapshot
import backend


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT,prefix='.qa-gtk4-generation-')
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)/'snapshot'
        self.project=model();self.project['selected_family']='gtk4'
        self.project['recipes']['gtk4']['visible_controls']=1

    def generate(self):
        return generate_snapshot(ROOT,self.folder,self.project,'a'*64,ROOT/'colors/DomainOS-SR10.4.colors')

    def test_snapshot_provenance_and_unchanged_recipe(self):
        original=json.dumps(self.project,sort_keys=True)
        receipt=self.generate()
        verified,colors=verify_snapshot(ROOT,self.folder,self.project,'a'*64)
        self.assertEqual(receipt,verified)
        self.assertTrue(colors)
        self.assertFalse(receipt['recipe_applied'])
        self.assertEqual(json.dumps(self.project,sort_keys=True),original)

    def test_css_corruption_is_rejected(self):
        receipt=self.generate();Path(receipt['css']).write_text('corrupted')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            verify_snapshot(ROOT,self.folder,self.project,'a'*64)

    def test_digest_and_stale_palette_are_refused(self):
        self.generate()
        with self.assertRaisesRegex(ValueError,'identity mismatch'):
            verify_snapshot(ROOT,self.folder,self.project,'b'*64)
        with patch('gtk4_generation.backend.palette_inputs_current',return_value=False):
            with self.assertRaisesRegex(ValueError,'palette stale'):
                verify_snapshot(ROOT,self.folder,self.project,'a'*64)

    def test_mixed_layout_filters_to_explicit_push_capability(self):
        self.project['recipes']['gtk4']['visible_controls']=3
        receipt = self.generate()
        self.assertEqual(receipt['translated_controls'], ['push'])

    def test_initial_snapshot_accepts_distinct_serializers_of_same_scene(self):
        working=Path(self.temp.name)/'working.json'
        working.write_text(json.dumps(self.project,indent=4))
        normalized,working_digest=backend.project(working)
        self.project=normalized
        canonical=Path(self.temp.name)/'canonical.json'
        backend.write_json(canonical,normalized)
        saved_digest=backend.sha(canonical.read_bytes())
        self.assertNotEqual(saved_digest,working_digest)
        generate_snapshot(ROOT,self.folder,normalized,saved_digest,ROOT/'colors/DomainOS-SR10.4.colors')
        verify_initial_snapshot(ROOT,self.folder,normalized,working_digest)
        wrong=dict(normalized,name='Different scene')
        with self.assertRaisesRegex(ValueError,'working scene mismatch'):
            verify_initial_snapshot(ROOT,self.folder,wrong,working_digest)

    def test_initial_snapshot_refuses_digest_bound_to_neither_file(self):
        working=Path(self.temp.name)/'working.json'
        backend.write_json(working,self.project)
        self.project,working_digest=backend.project(working)
        self.generate()  # Deliberately arbitrary a*64 binding.
        with self.assertRaisesRegex(ValueError,'no actual byte identity'):
            verify_initial_snapshot(ROOT,self.folder,self.project,working_digest)

    def toggle_snapshot(self):
        self.project['recipes']['gtk4']['visible_controls']=3
        return generate_snapshot(ROOT,self.folder,self.project,'a'*64,
                                 ROOT/'colors/DomainOS-SR10.4.colors',allow_toggle=True)

    def scrollbar_snapshot(self):
        self.project['recipes']['gtk4']['visible_categories'] = 1 << 2
        self.project['recipes']['gtk4']['visible_controls'] = (1 << 10) | (1 << 11)
        return generate_snapshot(ROOT,self.folder,self.project,'a'*64,
                                 ROOT/'colors/DomainOS-SR10.4.colors',
                                 allow_scrollbar=True)

    def test_scrollbar_snapshot_verifies_initial_scene_and_private_capability(self):
        receipt=self.scrollbar_snapshot()
        checked,_=verify_snapshot(ROOT,self.folder,self.project,'a'*64,
                                  allow_scrollbar=True)
        self.assertEqual(receipt,checked)
        self.assertEqual(receipt['translated_controls'],['scroll_h','scroll_v'])
        with self.assertRaisesRegex(ValueError,'mutually exclusive'):
            verify_snapshot(ROOT,self.folder,self.project,'a'*64,
                            allow_toggle=True,allow_scrollbar=True)

    def test_initial_scrollbar_snapshot_accepts_normalized_scene_digest(self):
        self.project['recipes']['gtk4']['visible_categories'] = 1 << 2
        self.project['recipes']['gtk4']['visible_controls'] = (1 << 10) | (1 << 11)
        working=Path(self.temp.name)/'scroll-working.json'
        working.write_text(json.dumps(self.project,indent=2))
        normalized,working_digest=backend.project(working)
        self.project=normalized
        canonical=Path(self.temp.name)/'scroll-canonical.json'
        backend.write_json(canonical,normalized)
        saved_digest=backend.sha(canonical.read_bytes())
        generate_snapshot(ROOT,self.folder,normalized,saved_digest,
                          ROOT/'colors/DomainOS-SR10.4.colors',allow_scrollbar=True)
        verify_initial_snapshot(ROOT,self.folder,normalized,working_digest,
                                allow_scrollbar=True)

    def test_toggle_snapshot_requires_explicit_private_capability(self):
        receipt=self.toggle_snapshot()
        checked,_=verify_snapshot(ROOT,self.folder,self.project,'a'*64,allow_toggle=True)
        self.assertEqual(checked,receipt)
        self.assertEqual(receipt['translated_controls'],['push','toggle'])
        self.assertFalse(receipt['public_support_announced'])
        self.assertIn(str(Path(receipt['base_css']).relative_to(self.folder)),receipt['artifacts'])
        with self.assertRaisesRegex(ValueError,'capability mismatch'):
            verify_snapshot(ROOT,self.folder,self.project,'a'*64)

    def test_toggle_base_corruption_rejected(self):
        receipt=self.toggle_snapshot();Path(receipt['base_css']).write_text('changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            verify_snapshot(ROOT,self.folder,self.project,'a'*64,allow_toggle=True)

    def test_toggle_receipt_identity_and_external_base_rejected(self):
        receipt=self.toggle_snapshot();path=self.folder/'GTK4-PROPOSAL.json'
        for field,value,reason in [('style_class','stale','style identity'),
                                   ('base_css',str(ROOT/'colors/DomainOS-SR10.4.colors'),'base CSS'),
                                   ('private_toggle_session',1,'capability'),
                                   ('translated_controls',['push'],'control capability')]:
            bad=dict(receipt,**{field:value});backend.write_json(path,bad)
            with self.assertRaisesRegex(ValueError,reason):
                verify_snapshot(ROOT,self.folder,self.project,'a'*64,allow_toggle=True)
        backend.write_json(path,receipt)

    def test_toggle_initial_snapshot_binds_actual_scene_bytes(self):
        self.project['recipes']['gtk4']['visible_controls']=2
        working=Path(self.temp.name)/'working.json';backend.write_json(working,self.project)
        self.project,digest=backend.project(working)
        generate_snapshot(ROOT,self.folder,self.project,digest,
                          ROOT/'colors/DomainOS-SR10.4.colors',allow_toggle=True)
        verify_initial_snapshot(ROOT,self.folder,self.project,digest,allow_toggle=True)


if __name__=='__main__':unittest.main()
