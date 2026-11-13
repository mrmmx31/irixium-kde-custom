#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone archive integrity and install/restore in disposable user roots."""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import package_domainos as package


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.domainos-inventory-test-', dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.checkout = Path(self.temporary.name)
        subprocess.run(['git', 'init', '--quiet', str(self.checkout)], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for name in package.SUPPORT:
            self.write(name, b'required fixture\n')
        self.removed = 'plasma/IrixClassicDomainOS/colors'
        self.retained = 'plasma/IrixClassicDomainOS/widgets/panel-background.svg'
        self.write(self.removed, b'obsolete fixed palette\n')
        self.write(self.retained, b'<svg/>\n')
        self.write('.gitignore', b'*.log\nignored.qml\n')
        subprocess.run(['git', '-C', str(self.checkout), 'add', '--all'], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def write(self, name, content):
        path = self.checkout / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_working_tree_deletions_are_omitted_but_new_sources_are_included(self):
        (self.checkout / self.removed).unlink()
        added = 'plasma/applets/org.irixclassic.domainos.panel/contents/ui/New.qml'
        self.write(added, b'import QtQuick\nItem {}\n')
        self.write('plasma/IrixClassicDomainOS/ignored.qml', b'ignored source\n')
        self.write('plasma/IrixClassicDomainOS/private.log', b'ignored artifact\n')
        names = package.source_names(self.checkout)
        self.assertNotIn(self.removed, names)
        self.assertIn(self.retained, names)
        self.assertIn(added, names)
        self.assertTrue(set(package.SUPPORT).issubset(names))
        self.assertFalse(any(name.endswith(('ignored.qml', '.log')) for name in names))
        self.assertEqual(package.read_file(self.checkout, added), b'import QtQuick\nItem {}\n')

    def test_deleted_required_support_still_blocks_inventory(self):
        (self.checkout / 'LICENSE').unlink()
        with self.assertRaisesRegex(package.Failure, 'Inventário incompleto'):
            package.source_names(self.checkout)

    def test_present_broken_link_is_not_silently_treated_as_deleted(self):
        link = self.write('plasma/IrixClassicDomainOS/link.svg', b'tracked resource\n')
        subprocess.run(['git', '-C', str(self.checkout), 'add', str(link)], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        link.unlink()
        link.symlink_to('missing-target.svg')
        name = link.relative_to(self.checkout).as_posix()
        self.assertIn(name, package.source_names(self.checkout))
        with self.assertRaisesRegex(package.Failure, 'Links de origem recusados'):
            package.read_file(self.checkout, name)

    def test_private_roots_and_unknown_documents_are_out_of_scope(self):
        private = '.qa-domainos-package/profile/data/plasma/plasmoids/private.qml'
        unknown_document = 'docs/PRIVATE-AUDIT.md'
        self.write(private, b'private test cache\n')
        self.write(unknown_document, b'not approved for the package\n')
        subprocess.run(['git', '-C', str(self.checkout), 'add', '--all'], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        names = package.source_names(self.checkout)
        self.assertNotIn(private, names)
        self.assertNotIn(unknown_document, names)
        self.assertIn('docs/VALIDACAO-DOMAINOS-AJUSTES-2026-10-09.md', names)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files,cls.versions=package.build_plan()
        cls.content=package.archive(cls.files,cls.versions)

    def rewrite(self,mutation):
        output=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(self.content)) as source, zipfile.ZipFile(output,'w') as dest:
            for info in source.infolist():
                data=source.read(info.filename)
                result=mutation(info,data)
                if result is not None:
                    changed,value=result;dest.writestr(changed,value)
        return output.getvalue()

    def test_deterministic_archive_preserves_versions_licenses_and_complete_sources(self):
        self.assertEqual(package.archive(self.files,self.versions),self.content)
        result=package.verify_archive(self.content)
        self.assertEqual(result['integrity'],'verified')
        self.assertEqual(len(package.TARGETS),4)
        self.assertTrue(set(package.SUPPORT).issubset(self.files))
        for name,data in self.files.items():
            if name.endswith('metadata.json'): self.assertEqual(data,(ROOT/name).read_bytes())
        self.assertIn('LICENSE',self.files)
        self.assertTrue(any(name.endswith('.pcf') for name in self.files),'bitmap date font absent')
        self.assertTrue(any('LICENSE' in name and 'fonts/' in name for name in self.files),'font license absent')
        self.assertTrue(any(name.startswith('plasma/IrixClassic/') and name.endswith('.svg') for name in self.files))
        integration = 'integrations/thunderbird-domainos/'
        self.assertIn(integration.rstrip('/'), package.SOURCE_ONLY)
        for name in ('README.md', 'install.py', 'native_host.py',
                     'extension/manifest.json', 'extension/background.js'):
            self.assertIn(integration + name, self.files)
        self.assertFalse(any(name.startswith(integration) for name in package.TARGETS.values()))
        self.assertFalse(any(name.endswith('.xpi') for name in self.files))
        self.assertFalse(package.safe_name(integration + 'generated.xpi'))
        self.assertNotIn('plasma/IrixClassicDomainOS/colors', self.files,
            'the Plasma Style must inherit the selected KDE color scheme')
        self.assertFalse(any(name.startswith(('icons/','sons/','decorations/')) for name in self.files))
        # Ship the artwork fixture and the public palette/control contracts.
        # Personal audit outputs and private profiles stay outside.
        self.assertEqual({name for name in self.files if name.startswith('plasma/tests/')}, {
            'plasma/tests/test_domainos_native_style_palette.py',
            'plasma/tests/DomainOSNativeStylePalettePreview.qml',
            'plasma/tests/test_domainos_popup_palette.py',
            'plasma/tests/test_domainos_controls.py',
            'plasma/tests/test_domainos_palette.py',
            'plasma/tests/test_domainos_tray_refresh_failure.py',
        })
        with zipfile.ZipFile(io.BytesIO(self.content)) as archive:
            self.assertTrue(all(stat.S_IFMT(info.external_attr>>16)==stat.S_IFREG for info in archive.infolist()))
            record=json.loads(archive.read(package.NAME+'/PACOTE.json'))
            self.assertEqual(record['channel'],'initial-use');self.assertFalse(record['signed'])

    def test_modified_payload_is_rejected(self):
        target=package.NAME+'/tools/install_domainos.py'
        changed=self.rewrite(lambda info,data:(info,data+b'\n# changed\n') if info.filename==target else (info,data))
        with self.assertRaisesRegex(package.Failure,'Hash/tamanho'): package.verify_archive(changed)

    def test_unsafe_duplicate_and_link_entries_are_rejected(self):
        def unsafe(info,data):
            if info.filename==package.NAME+'/LICENSE':info.filename=package.NAME+'/../outside'
            return info,data
        with self.assertRaisesRegex(package.Failure,'inseguro'):package.verify_archive(self.rewrite(unsafe))
        def link(info,data):
            if info.filename==package.NAME+'/LICENSE':info.external_attr=(stat.S_IFLNK|0o777)<<16
            return info,data
        with self.assertRaisesRegex(package.Failure,'regulares'):package.verify_archive(self.rewrite(link))
        out=io.BytesIO(self.content)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(out,'a') as archive:
                archive.writestr(package.NAME+'/LICENSE',b'duplicate')
        with self.assertRaisesRegex(package.Failure,'duplicado'):package.verify_archive(out.getvalue())

    def test_manifest_cannot_omit_required_runtime(self):
        files=dict(self.files);files.pop('tools/domainos_style_bridge.py')
        with self.assertRaisesRegex(package.Failure,'ausentes'): package.archive(files,self.versions)

    def test_extracted_package_operates_without_checkout_and_restores_only_four_resources(self):
        with tempfile.TemporaryDirectory(prefix='.domainos-package-test-',dir=ROOT) as temporary:
            base=Path(temporary);extracted=base/'extracted';extracted.mkdir()
            package.verify_archive(self.content)
            with zipfile.ZipFile(io.BytesIO(self.content)) as archive:archive.extractall(extracted)
            standalone=extracted/package.NAME
            self.assertFalse((standalone/'.git').exists())
            self.assertEqual(package.build_plan(standalone), (self.files,self.versions))
            home=base/'profile';home.mkdir(mode=0o700)
            data=home/'data';config=home/'config';state=home/'state'
            for path in (data,config,state):path.mkdir(mode=0o700)
            old=data/'plasma/plasmoids/org.irixclassic.domainos.panel'
            old.mkdir(parents=True);(old/'old.txt').write_text('previous resource\n')
            (old/'old.txt').chmod(0o600)
            old_style=data/'plasma/desktoptheme/IrixClassicDomainOS'
            old_style.mkdir(parents=True)
            (old_style/'colors').write_text('previous fixed palette\n')
            (data/'unrelated.txt').write_text('other theme\n')
            protected = {
                'kdeglobals': b'[General]\nColorScheme=PrivateUnchanged\n',
                'plasmarc': b'[Theme]\nname=PrivateUnchanged\n',
                'kwinrc': b'[org.kde.kdecoration2]\ntheme=private-unchanged\n',
                'plasma-org.kde.plasma.desktop-appletsrc': b'untouched panel configuration\n',
            }
            for name, content in protected.items():
                (config/name).write_bytes(content); (config/name).chmod(0o600)
            def file_snapshot(path):
                return path.read_bytes(), stat.S_IMODE(path.stat().st_mode)
            def resource_snapshot(path):
                if not path.exists(): return None
                if path.is_file(): return {'@file': file_snapshot(path)}
                return {item.relative_to(path).as_posix(): file_snapshot(item)
                    for item in sorted(path.rglob('*')) if item.is_file()}
            def hashed(snapshot):
                return None if snapshot is None else {name: {'sha256': package.digest(value[0]), 'mode': value[1]}
                    for name,value in snapshot.items()}
            before_resources = {dest: resource_snapshot(data/dest) for dest in package.TARGETS}
            before_config = {name: file_snapshot(config/name) for name in protected}
            stages = []
            environment=dict(os.environ)
            for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','PYTHONPATH','QML2_IMPORT_PATH','QML_IMPORT_PATH'):
                environment.pop(key,None)
            environment.update(HOME=str(home),XDG_DATA_HOME=str(data),XDG_CONFIG_HOME=str(config),
                XDG_STATE_HOME=str(state),XDG_CACHE_HOME=str(home/'cache'),
                PYTHONDONTWRITEBYTECODE='1',QML_DISABLE_DISK_CACHE='1')
            def run(script,*arguments):
                result=subprocess.run(['/usr/bin/python3','-B',str(standalone/'tools'/script),*arguments],
                    cwd=base,env=environment,text=True,capture_output=True,timeout=45)
                self.assertEqual(result.returncode,0,result.stderr+'\n'+result.stdout)
                self.assertEqual({name: file_snapshot(config/name) for name in protected}, before_config)
                stages.append({'command':[script,*arguments], 'protected_configs':hashed(
                    {name: file_snapshot(config/name) for name in protected})})
                return result.stdout
            run('install_domainos.py','--verificar')
            self.assertTrue((old/'old.txt').is_file())
            run('install_domainos.py')
            receipt_dir=state/'irixium-domainos'
            token=(receipt_dir/'latest').read_text().strip()
            receipt=json.loads((receipt_dir/'backups'/token/'receipt.json').read_text())
            self.assertEqual({entry['destination'] for entry in receipt['entries']},
                {str(data/dest) for dest in package.TARGETS})
            self.assertEqual((old/'metadata.json').read_bytes(),self.files['plasma/applets/org.irixclassic.domainos.panel/metadata.json'])
            for dest, source in package.TARGETS.items():
                installed = resource_snapshot(data/dest)
                expected = {'@file':self.files[source]} if source in self.files else {
                    name.removeprefix(source+'/'): content
                    for name,content in self.files.items() if name.startswith(source+'/')}
                self.assertEqual({name:value[0] for name,value in installed.items()}, expected)
            installed_resources = {dest: resource_snapshot(data/dest) for dest in package.TARGETS}
            self.assertFalse((old_style/'colors').exists(), 'the old fixed palette must be removed')
            saved_backups = sorted(path.name for path in (receipt_dir/'backups').iterdir())
            run('install_domainos.py')
            self.assertEqual((receipt_dir/'latest').read_text().strip(), token)
            self.assertEqual(sorted(path.name for path in (receipt_dir/'backups').iterdir()), saved_backups)
            self.assertEqual({dest: resource_snapshot(data/dest) for dest in package.TARGETS}, installed_resources)
            run('install_domainos.py','--restaurar','--verificar')
            self.assertEqual({dest: resource_snapshot(data/dest) for dest in package.TARGETS}, installed_resources)
            run('install_domainos.py','--restaurar')
            self.assertEqual({dest: resource_snapshot(data/dest) for dest in package.TARGETS}, before_resources)
            self.assertEqual((old/'old.txt').read_text(),'previous resource\n')
            self.assertFalse((old/'metadata.json').exists())
            self.assertEqual((old_style/'colors').read_text(),'previous fixed palette\n')
            self.assertFalse((data/'plasma/plasmoids/org.irixclassic.grosview').exists())
            self.assertFalse((data/'color-schemes/DomainOS-SR10-4.colors').exists())
            self.assertEqual((data/'unrelated.txt').read_text(),'other theme\n')
            self.assertEqual((config/'plasma-org.kde.plasma.desktop-appletsrc').read_text(),'untouched panel configuration\n')
            self.assertFalse((home/'cache').exists())
            self.assertEqual(set(path.name for path in state.iterdir()),{'irixium-domainos'})
            report_path = os.environ.get('IRIX_DOMAINOS_PACKAGE_TEST_REPORT')
            if report_path:
                result = {
                    'format':1, 'status':'passed',
                    'scope':'Extracted independent archive in a disposable repository-local profile. No real desktop activation, cache refresh, D-Bus or global installation.',
                    'install_targets':package.TARGETS,
                    'checks':{'four_destinations_match_archive':True,
                        'reinstall_preserves_resources_and_backup':True,
                        'restore_dry_run_preserves_resources':True,
                        'restore_recovers_exact_bytes_and_modes':True,
                        'obsolete_style_colors_removed':True,
                        'protected_configs_preserved_after_each_command':True},
                    'resources':{'before':{dest:hashed(value) for dest,value in before_resources.items()},
                        'installed':{dest:hashed(value) for dest,value in installed_resources.items()},
                        'restored':{dest:hashed(resource_snapshot(data/dest)) for dest in package.TARGETS}},
                    'protected_configs_before':hashed(before_config), 'commands':stages,
                }
                # Opt-in test evidence only; never overwrite an older report.
                with Path(report_path).open('x', encoding='utf-8') as output:
                    json.dump(result, output, indent=2, ensure_ascii=False); output.write('\n')


if __name__=='__main__':unittest.main()
