# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Packaging tests: use the actual stable release, temporary filesystem only."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT/'distribuicao/tools'))
SPEC = importlib.util.spec_from_file_location('build_kvantum', ROOT/'distribuicao/tools/build_kvantum.py')
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def rewrite_zip(data, alter):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        items = [(copy.copy(i), z.read(i.filename)) for i in z.infolist()]
    items = alter(items)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            for item, content in items:
                z.writestr(item, content)
    return stream.getvalue()


class Packaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.report = B.build_plan(ROOT)
        cls.theme_name = 'IrixClassic-0.7.1-kvantum.zip'
        cls.code_name = 'IrixClassic-0.7.1-codigo.zip'
        cls.theme = cls.outputs[cls.theme_name]
        cls.code = cls.outputs[cls.code_name]

    def test_two_archives_and_explicit_stable_report(self):
        self.assertEqual(set(self.outputs), {self.theme_name, self.code_name, 'SHA256SUMS', 'DISTRIBUICAO.json'})
        self.assertIs(self.report['stable_approved'], True)
        self.assertEqual(self.report['pending_acceptance'], [])
        self.assertIs(self.report['qtquick_fix_included'], False)
        self.assertIs(self.report['modern_theme_included'], False)

    def test_determinism_and_no_source_writes(self):
        before = snapshot(ROOT)
        second, _ = B.build_plan(ROOT)
        self.assertEqual(self.outputs, second)
        self.assertEqual(before, snapshot(ROOT))

    def test_minimal_archive_has_no_script(self):
        with zipfile.ZipFile(io.BytesIO(self.theme)) as z:
            self.assertEqual(len(z.namelist()), 8)
            for n in z.namelist():
                self.assertTrue(n.startswith('IrixClassic/'))
                self.assertNotIn(Path(n).suffix, ('.sh', '.py'))
            for name in B.THEME_FILES | {'MANIFEST.json'}:
                self.assertEqual(z.read('IrixClassic/'+name), (ROOT/'kvantum/IrixClassic'/name).read_bytes())

    def test_code_archive_contains_actual_corresponding_source(self):
        with zipfile.ZipFile(io.BytesIO(self.code)) as z:
            prefix = 'IrixClassic-0.7.1-codigo/'
            entries = json.loads((ROOT/'distribuicao/ARQUIVOS.json').read_text())['source_files']
            for rel in entries:
                self.assertEqual(z.read(prefix+rel), (ROOT/rel).read_bytes(), rel)
            for name in z.namelist():
                self.assertTrue(B.safe_name(name))
                self.assertNotIn('qtquick_scrollbar_fix', name)
                self.assertNotIn('kvantum/Irixium/', name)
                self.assertNotIn('/.git/', name)

    def test_same_installer_bytes_not_new_installation_logic(self):
        with zipfile.ZipFile(io.BytesIO(self.code)) as z:
            for rel in ('tools/install_kvantum_classic.py','tools/theme_transaction.py',
                        'kvantum/instalar-classic.sh','kvantum/restaurar-classic.sh'):
                self.assertEqual(z.read('IrixClassic-0.7.1-codigo/'+rel), (ROOT/rel).read_bytes())

    def test_archive_metadata_normalized(self):
        for data in (self.theme, self.code):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                self.assertEqual(z.namelist(), sorted(z.namelist()))
                for item in z.infolist():
                    self.assertEqual(item.date_time, B.DATE)
                    mode=item.external_attr >> 16
                    self.assertTrue(stat.S_ISREG(mode))
                    self.assertEqual(mode & 0o777, 0o755 if item.filename.endswith('.sh') else 0o644)
                    self.assertFalse(item.comment)

    def test_external_checksums(self):
        for line in self.outputs['SHA256SUMS'].decode().splitlines():
            h, n = line.split('  ')
            self.assertEqual(h, B.digest(self.outputs[n]))

    def test_verify_both_archives_without_extracting(self):
        for data in (self.theme, self.code):
            r=B.verify_archive(data)
            self.assertEqual(r['integrity'], 'verified')
            self.assertFalse(r['signed'])

    def test_generated_svg_reproduces_from_extracted_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with zipfile.ZipFile(io.BytesIO(self.code)) as z:
                # Already verified by build_plan; never extract arbitrary input.
                z.extractall(root)
            source=root/'IrixClassic-0.7.1-codigo'
            svg=source/'kvantum/IrixClassic/IrixClassic.svg'
            before=svg.read_bytes()
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            p=subprocess.run([sys.executable,str(source/'kvantum/tools/build_classic.py')],
                             capture_output=True,env=env,timeout=30)
            self.assertEqual(p.returncode,0,p.stderr.decode())
            self.assertEqual(before,svg.read_bytes())

    def test_packaging_reproduces_from_extracted_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with zipfile.ZipFile(io.BytesIO(self.code)) as z:z.extractall(root)
            source=root/'IrixClassic-0.7.1-codigo'
            rebuilt,_=B.build_plan(source)
            self.assertEqual(rebuilt,self.outputs)

    def test_invalid_relative_names_and_fonts(self):
        for name in ('../x','/abs','a/../b','a//b','a\\b','a/.git/config','x/./y',
                     'C:/x','x\0y','x/font.ttf','x/font.WOFF2','x/__pycache__/a.pyc'):
            with self.subTest(name=name):self.assertFalse(B.safe_name(name))
        self.assertTrue(B.safe_name('kvantum/IrixClassic/IrixClassic.svg'))

    def test_duplicate_json_key(self):
        with self.assertRaises(B.Failure):B.document(b'{"a":1,"a":2}')

    def test_manifest_hash_tamper(self):
        files={n:(ROOT/'kvantum/IrixClassic'/n).read_bytes() for n in B.THEME_FILES|{'MANIFEST.json'}}
        files['IrixClassic.svg']+=b'\n'
        with self.assertRaises(B.Failure):B.check_theme(files)

    def test_manifest_extra_entry_rejected(self):
        files={n:(ROOT/'kvantum/IrixClassic'/n).read_bytes() for n in B.THEME_FILES|{'MANIFEST.json'}}
        d=B.document(files['MANIFEST.json']);d['files']['unexpected.txt']='0'*64
        files['MANIFEST.json']=B.json_bytes(d)
        with self.assertRaises(B.Failure):B.check_theme(files)

    def test_theme_version_not_silently_promoted(self):
        files={n:(ROOT/'kvantum/IrixClassic'/n).read_bytes() for n in B.THEME_FILES|{'MANIFEST.json'}}
        d=B.document(files['MANIFEST.json']);d['version']='1.0.0'
        files['MANIFEST.json']=B.json_bytes(d)
        with self.assertRaises(B.Failure):B.check_theme(files)

    def test_bad_zip_rejected(self):
        with self.assertRaises(B.Failure):B.verify_archive(b'not a zip')

    def test_zip_content_tamper(self):
        def alter(rows):
            return [(i,d+b'\n' if i.filename.endswith('README.md') else d) for i,d in rows]
        with self.assertRaises(B.Failure):B.verify_archive(rewrite_zip(self.theme,alter))

    def test_zip_extra_file_rejected(self):
        def alter(rows):
            return rows+[(zipfile.ZipInfo('IrixClassic/extra.txt'),b'undesired')]
        with self.assertRaises(B.Failure):B.verify_archive(rewrite_zip(self.theme,alter))

    def test_zip_traversal_rejected(self):
        def alter(rows):return rows+[(zipfile.ZipInfo('IrixClassic/../escape'),b'x')]
        with self.assertRaises(B.Failure):B.verify_archive(rewrite_zip(self.theme,alter))

    def test_zip_duplicate_rejected(self):
        with self.assertRaises(B.Failure):
            B.verify_archive(rewrite_zip(self.theme,lambda r:r+[r[0]]))

    def test_zip_symlink_rejected(self):
        def alter(rows):
            rows[0][0].create_system=3
            rows[0][0].external_attr=(stat.S_IFLNK|0o777)<<16
            return rows
        with self.assertRaises(B.Failure):B.verify_archive(rewrite_zip(self.theme,alter))

    def test_zip_stable_approval_forged_rejected(self):
        def alter(rows):
            out=[]
            for i,d in rows:
                if i.filename.endswith('/PACOTE.json'):
                    doc=B.document(d);doc['stable_approved']=False;d=B.json_bytes(doc)
                out.append((i,d))
            return out
        with self.assertRaises(B.Failure):B.verify_archive(rewrite_zip(self.theme,alter))

    def test_missing_source_or_link_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(B.Failure):B.read_file(root,'not-there')
            (root/'regular').write_bytes(b'ok');(root/'linked').symlink_to(root/'regular')
            with self.assertRaises(B.Failure):B.read_file(root,'linked')

    def test_renamed_font_binary_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'renamed.svg').write_bytes(b'OTTO' + b'not a real font')
            with self.assertRaises(B.Failure):B.read_file(root,'renamed.svg')

    def test_output_new_directory_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'new'
            B.write_outputs(output,self.outputs,ROOT)
            self.assertEqual(set(p.name for p in output.iterdir()),set(self.outputs))
            for name,data in self.outputs.items():self.assertEqual((output/name).read_bytes(),data)

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);(output/'keep.txt').write_bytes(b'keep')
            with self.assertRaises(B.Failure):B.write_outputs(output,self.outputs,ROOT)
            self.assertEqual((output/'keep.txt').read_bytes(),b'keep')

    def test_output_inside_source_refused(self):
        with self.assertRaises(B.Failure):B.write_outputs(ROOT/'test-dist-forbidden',self.outputs,ROOT)
        self.assertFalse((ROOT/'test-dist-forbidden').exists())

    def test_output_link_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'link').symlink_to(root, target_is_directory=True)
            with self.assertRaises(B.Failure):B.write_outputs(root/'link/new',self.outputs,ROOT)

    def test_failed_transfer_cleans_only_own_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);output=root/'new';keep=root/'keep';keep.write_bytes(b'keep')
            real=os.replace;counter=0
            def fail_second(src,dst):
                nonlocal counter
                counter+=1
                if counter==2:raise OSError('injected transfer failure')
                return real(src,dst)
            with mock.patch.object(B.os,'replace',side_effect=fail_second):
                with self.assertRaises(OSError):B.write_outputs(output,self.outputs,ROOT)
            self.assertFalse(output.exists())
            self.assertEqual(keep.read_bytes(),b'keep')

    def test_cli_dry_run_no_source_write(self):
        before=snapshot(ROOT)
        p=subprocess.run([sys.executable,str(ROOT/'distribuicao/tools/build_kvantum.py'),'--verificar'],
                         capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),timeout=30)
        self.assertEqual(p.returncode,0,p.stderr.decode())
        self.assertEqual(json.loads(p.stdout)['channel'],'stable')
        self.assertEqual(before,snapshot(ROOT))

    def test_unapproved_stable_policy_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with zipfile.ZipFile(io.BytesIO(self.code)) as z:z.extractall(root)
            code=root/'IrixClassic-0.7.1-codigo'
            policy=code/'distribuicao/LANCAMENTO.json';d=json.loads(policy.read_text());d['stable_approved']=False
            policy.write_text(json.dumps(d))
            with self.assertRaises(B.Failure):B.build_plan(code)

    def test_documented_exclusions(self):
        self.assertEqual(self.report['theme_version'],'0.7.1')
        self.assertFalse(self.report['signed'])
        for p in self.report['sources']:
            self.assertNotIn('system_theme_writer',p)
            self.assertNotIn('qtquick_scrollbar_fix',p)
            self.assertNotIn('corrigir-pressao',p)


if __name__=='__main__':unittest.main()
