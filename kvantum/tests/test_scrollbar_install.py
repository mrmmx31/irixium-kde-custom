# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import install_kvantum_classic as I
from theme_transaction import Failure

class InstallVersion(unittest.TestCase):
    def test_new_version_passes_full_manifest_validation(self):
        files=I.theme_files(ROOT)
        self.assertIn(b'0.3.0-rc1',files['IrixClassic.kvconfig'])
    def test_old_candidate_is_still_recognized(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);dest=repo/'kvantum/IrixClassic'
            shutil.copytree(ROOT/'kvantum/IrixClassic',dest)
            doc=json.loads((dest/'MANIFEST.json').read_text());doc['version']='0.1.0-rc1'
            (dest/'MANIFEST.json').write_text(json.dumps(doc))
            self.assertIn('IrixClassic.svg',I.theme_files(repo))
    def test_unknown_version_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);dest=repo/'kvantum/IrixClassic'
            shutil.copytree(ROOT/'kvantum/IrixClassic',dest)
            doc=json.loads((dest/'MANIFEST.json').read_text());doc['version']='999.0'
            (dest/'MANIFEST.json').write_text(json.dumps(doc))
            with self.assertRaises(Failure):I.theme_files(repo)
    def test_corrupt_svg_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);dest=repo/'kvantum/IrixClassic'
            shutil.copytree(ROOT/'kvantum/IrixClassic',dest)
            with (dest/'IrixClassic.svg').open('ab') as f:f.write(b'broken')
            with self.assertRaises(Failure):I.theme_files(repo)
    def test_install_plan_default_only_touches_irixclassic(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)
            for change in I.plan(ROOT,config,False):
                self.assertEqual(change.path.parent,config/'Kvantum/IrixClassic')
    def test_source_styles_remain_unchanged_by_planning(self):
        import hashlib
        source=ROOT/'kvantum/IrixClassic/IrixClassic.svg';before=hashlib.sha256(source.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:I.plan(ROOT,Path(tmp),False)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)
