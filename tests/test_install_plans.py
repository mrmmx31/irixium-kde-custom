# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from theme_transaction import Failure, snapshot, decode
from update_irixium import install_plan
from install_kvantum_classic import plan as kvplan, theme_files

class GlobalPlan(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.repo=self.root/'repo';self.repo.mkdir()
        self.source=self.repo/'aurorae/Irixium';self.source.mkdir(parents=True)
        self.theme=self.root/'home/theme';self.theme.mkdir(parents=True)
        self.config=self.root/'home/config';self.config.mkdir()
        self.system=self.root/'system';self.system.mkdir()
        self.group=self.system/'AuroraeButtonGroup.qml';self.group.write_bytes(b'known-original')
        self.menu=self.system/'MenuButton.qml';self.menu.write_bytes(b'previous menu')
        self.asset=self.system/'applications.png'
        self.geo=self.repo/'moderno/geometria';(self.geo/'tools').mkdir(parents=True)
        (self.geo/'compatibilidade').mkdir()
        shutil.copyfile(ROOT/'moderno/geometria/tools/layout.py',self.geo/'tools/layout.py')
        (self.geo/'compatibilidade/base.qml').write_bytes(b'known-original')
        (self.geo/'AuroraeButtonGroup.qml').write_bytes(b'modern-new')
        (self.repo/'AuroraeButtonGroup.qml').write_bytes(b'DO NOT INSTALL THIS LEGACY OVERLAY')
        files=[p for p in self.geo.rglob('*') if p.is_file()]
        (self.geo/'MANIFEST.json').write_text(json.dumps({'version':'1.0.0-rc1','files':{str(p.relative_to(self.geo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}))
        self.rc=b'[General]\nActiveTextColor=1,2,3,255\n[Layout]\nTitleHeight=34\nButtonWidth=22\nButtonHeight=22\nButtonSpacing=4\n'
        (self.source/'Irixiumrc').write_bytes(self.rc)
        (self.theme/'Irixiumrc').write_bytes(self.rc)
        for n in ('decoration','minimize','maximize','restore','close'):
            (self.source/(n+'.svg')).write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
        (self.source/'applications.png').write_bytes(b'\x89PNG\r\n\x1a\nplaceholder')
        (self.source/'metadata.desktop').write_text('[Desktop Entry]\nName=Irixium\n')
        (self.repo/'MenuButton.qml').write_bytes(b'import org.kde.kwin.decoration\n// isIrixium guarded menu')
        (self.repo/'kwin-decoration.conf').write_text('[org.kde.kdecoration2]\nBorderSize=Normal\nButtonsOnLeft=M\nButtonsOnRight=IA\n')
        (self.repo/'kde-fonts.conf').write_text('[General]\nfont=Test\n[WM]\nactiveFont=Test title\n')
        (self.config/'kwinrc').write_text('[org.kde.kdecoration2]\ntheme=irix_classic\n[Other]\nKey=unchanged\n')
        (self.config/'kdeglobals').write_text('[General]\nfont=Local\n[KDE]\nwidgetStyle=kvantum\n')
    def tearDown(self):self.tmp.cleanup()
    def plan(self,activate=False,fonts=False):
        return install_plan(self.repo,self.theme,self.config,self.group,self.menu,self.asset,activate,fonts)
    def test_default_does_not_modify_selection_fonts_kvantum_or_classic(self):
        changes=self.plan()
        self.assertFalse(any(c.phase==2 for c in changes))
        self.assertTrue(all(c.path.parent in (self.theme,self.system) for c in changes))
    def test_uses_only_new_group_not_legacy_root(self):
        c=next(c for c in self.plan() if c.path==self.group);self.assertEqual(c.data,b'modern-new')
    def test_local_rc_colors_preserved_spacing_updated(self):
        c=next(c for c in self.plan() if c.path.name=='Irixiumrc')
        self.assertIn(b'ActiveTextColor=1,2,3,255',c.data);self.assertIn(b'ButtonSpacing=6',c.data)
    def test_fresh_install_supported(self):
        (self.theme/'Irixiumrc').unlink();self.assertTrue(self.plan())
    def test_activation_explicit_and_last_phase(self):
        changes=self.plan(activate=True)
        c=next(c for c in changes if c.path.name=='kwinrc');self.assertEqual(c.phase,2)
        self.assertIn(b'theme=__aurorae__svg__Irixium',c.data);self.assertIn(b'Key=unchanged',c.data)
        self.assertFalse(any(c.path.name=='kdeglobals' for c in changes))
    def test_fonts_explicit_do_not_touch_theme_selection(self):
        changes=self.plan(fonts=True)
        self.assertFalse(any(c.path.name=='kwinrc' for c in changes))
        c=next(c for c in changes if c.path.name=='kdeglobals');self.assertEqual(c.phase,2)
        self.assertIn(b'widgetStyle=kvantum',c.data)
    def test_unknown_qml_refused(self):
        self.group.write_bytes(b'unknown')
        with self.assertRaises(Failure):self.plan()
    def test_corrupt_manifest_refused(self):
        (self.geo/'AuroraeButtonGroup.qml').write_bytes(b'corrupted')
        with self.assertRaises(Failure):self.plan()
    def test_missing_asset_refused_before_destination_write(self):
        before=snapshot(self.theme/'Irixiumrc');(self.source/'maximize.svg').unlink()
        with self.assertRaises(Failure):self.plan()
        self.assertEqual(snapshot(self.theme/'Irixiumrc'),before)
    def test_custom_dimensions_are_not_silently_changed(self):
        (self.theme/'Irixiumrc').write_bytes(self.rc.replace(b'ButtonWidth=22',b'ButtonWidth=25'))
        with self.assertRaises(ValueError):self.plan()

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
