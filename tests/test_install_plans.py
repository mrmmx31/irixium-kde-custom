# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from install_kvantum_classic import plan as kvplan, theme_files

class KvantumPlan(unittest.TestCase):
    def test_theme_manifest_and_svg(self):self.assertIn('IrixClassic.svg',theme_files(ROOT))
    def test_default_only_installs_new_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            changes=kvplan(ROOT,Path(tmp),False)
            self.assertTrue(all(c.path.parent.name=='IrixClassic' and c.phase==0 for c in changes))
            self.assertFalse((Path(tmp)/'Kvantum').exists())
    def test_activation_keeps_application_exceptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp);(config/'Kvantum').mkdir()
            p=config/'Kvantum/kvantum.kvconfig';p.write_bytes(b'[General]\ntheme=Irixium\n[Applications]\nOther=example\n')
            changes=kvplan(ROOT,config,True)
            c=next(c for c in changes if c.phase==2)
            self.assertIn(b'theme=IrixClassic',c.data);self.assertIn(b'Other=example',c.data)
            self.assertEqual(c.path,p);self.assertIn(b'theme=Irixium',p.read_bytes())

if __name__=='__main__':unittest.main()
