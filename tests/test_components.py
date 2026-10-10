# SPDX-License-Identifier: GPL-3.0-or-later
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import audit_suite
import components
from theme_transaction import Failure


class ComponentsTest(unittest.TestCase):
    def test_three_profiles_have_all_shipped_dependencies(self):
        report=audit_suite.audit()
        self.assertEqual(report['failures'],[])
        self.assertEqual(len(report['components']),40)
        self.assertFalse(report['sounds']['automatic_download'])
        self.assertFalse(report['sounds']['audio_in_repository'])

    def test_inventory_cannot_escape_install_roots(self):
        doc=components.catalog()
        doc['components'][0]['destination']='../shared/theme'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'components.json').write_text(json.dumps(doc))
            with patch.object(components,'ROOT',root),self.assertRaises(Failure):
                components.catalog()

    def test_classic_gtk_and_optional_modern_decorations_are_installed(self):
        doc = components.catalog()
        self.assertEqual(doc['profiles']['classic']['gtk'], 'IrixClassic-KDE')
        self.assertEqual(doc['profiles']['moderno']['gtk'], 'Irixium-KDE')
        destinations = {e['destination'] for e in doc['components']}
        self.assertTrue({'themes/IrixClassic', 'themes/Irixium',
            'themes/IrixClassic-KDE', 'themes/IrixClassic-KDE-Reload',
            'themes/Irixium-KDE', 'themes/Irixium-KDE-Reload',
            'kwin/decorations/irixium_modern', 'kwin/decorations/irixium_modern_13',
            'kwin/decorations/irixium_modern_41',
            'plasma/plasmoids/org.irixclassic.grosview'}.issubset(destinations))

    def test_domainos_options_keep_the_classic_profile_and_style_independent(self):
        doc = components.catalog()
        self.assertEqual(set(doc['profiles']), {'classic', 'moderno', 'domainos'})
        self.assertEqual(doc['profiles']['classic'], {
            'global': 'org.magpie.irixclassic.desktop', 'kvantum': 'IrixClassic',
            'decoration': 'irixium_irix_classic_v4', 'icons': 'IrixClassic-SGI',
            'plasma': 'IrixClassic', 'wallpaper': 'IrixClassic',
            'gtk': 'IrixClassic-KDE', 'cursor': 'SGI-Classic','colors':'Irixium'})
        entries = {e['source']: (e['root'], e['destination']) for e in doc['components']}
        self.assertEqual(entries['plasma/IrixClassic'],
                         ('data', 'plasma/desktoptheme/IrixClassic'))
        self.assertEqual(entries['plasma/IrixClassicDomainOS'],
                         ('data', 'plasma/desktoptheme/IrixClassicDomainOS'))
        self.assertEqual(entries['plasma/applets/org.irixclassic.domainos.panel'],
                         ('data', 'plasma/plasmoids/org.irixclassic.domainos.panel'))
        self.assertEqual(entries['colors/DomainOS-SR10.4.colors'],
                         ('data', 'color-schemes/DomainOS-SR10-4.colors'))
        self.assertEqual(entries['decorations/domainos/package'],
                         ('data', 'kwin/decorations/domainos_sr104'))
        self.assertIn(components.ROOT/'decorations/domainos/package',
                      components.decoration_sources())
        self.assertEqual(doc['profiles']['moderno']['decoration'], 'irixium_modern')

    def test_duplicate_destination_is_rejected(self):
        doc=components.catalog();doc['components'].append(doc['components'][0])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'components.json').write_text(json.dumps(doc))
            with patch.object(components,'ROOT',root),self.assertRaises(Failure):
                components.catalog()

    def test_independent_catalog_requires_its_explicit_four_component_scope(self):
        doc=components.catalog()
        targets={'plasma/plasmoids/org.irixclassic.domainos.panel',
                 'plasma/plasmoids/org.irixclassic.grosview',
                 'plasma/desktoptheme/IrixClassicDomainOS','color-schemes/DomainOS-SR10-4.colors'}
        minimal={'format':1,'scope':components.INDEPENDENT_SCOPE,
                 'profiles':{'classic':{},'moderno':{}},
                 'components':[entry for entry in doc['components'] if entry['destination'] in targets]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);file=root/'components.json'
            file.write_text(json.dumps(minimal))
            with patch.object(components,'ROOT',root):self.assertEqual(components.catalog(),minimal)
            invalid=dict(minimal);invalid.pop('scope');file.write_text(json.dumps(invalid))
            with patch.object(components,'ROOT',root),self.assertRaises(Failure):components.catalog()
            invalid=dict(minimal,components=minimal['components']+[doc['components'][0]])
            file.write_text(json.dumps(invalid))
            with patch.object(components,'ROOT',root),self.assertRaises(Failure):components.catalog()

    def test_local_comparison_normalizes_materialized_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';installed=root/'installed'
            source.mkdir();installed.mkdir()
            (source/'image').write_bytes(b'image');(source/'alias').symlink_to('image')
            (installed/'image').write_bytes(b'image');(installed/'alias').write_bytes(b'image')
            self.assertEqual(audit_suite.hashes(source),audit_suite.hashes(installed))
            (installed/'alias').write_bytes(b'different')
            self.assertNotEqual(audit_suite.hashes(source),audit_suite.hashes(installed))

    def test_user_preference_overrides_global_theme_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp);(config/'kdedefaults').mkdir()
            (config/'kdedefaults/kdeglobals').write_text('[Icons]\nTheme=Default\n')
            (config/'kdeglobals').write_text('[Icons]\nTheme=User\n')
            self.assertEqual(audit_suite.preference(config,'kdeglobals','Icons','Theme'),'User')
            (config/'kdeglobals').unlink()
            self.assertEqual(audit_suite.preference(config,'kdeglobals','Icons','Theme'),'Default')

    def test_missing_native_preference_is_reported_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(audit_suite.preference(Path(tmp),'kdeglobals','Icons','Theme'))

    def test_cursor_compatibility_uses_only_the_three_known_theme_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pairs = components.cursor_compat_sources(root)
            self.assertEqual({p.name for _,p in pairs}, {'sgi','SGI-Classic','SGI-Irixium'})
            self.assertTrue(all(dest.parent==root for _,dest in pairs))
            self.assertTrue(all(source.parent==components.ROOT/'cursors' for source,_ in pairs))

    def test_gtk2_discovery_installs_both_themes_in_user_compat_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pairs = components.gtk_compat_sources(root)
            self.assertEqual({dest.name for _,dest in pairs}, {'IrixClassic', 'Irixium',
                'IrixClassic-KDE', 'IrixClassic-KDE-Reload', 'Irixium-KDE', 'Irixium-KDE-Reload',
                'DomainOS-SR10-4','DomainOS-SR10-4-KDE','DomainOS-SR10-4-KDE-Reload'})
            self.assertTrue(all(dest.parent == root for _,dest in pairs))
            self.assertTrue(all((source/'gtk-2.0/gtkrc').is_file() for source,_ in pairs))
