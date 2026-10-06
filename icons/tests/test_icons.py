#!/usr/bin/env python3
"""Regression tests; only temporary fixture themes are modified. MIT."""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from icon_common import audit, parse_index, png_size
from repair_irixium import build_fixed
from install_theme import install
import build_classic


def tiny_png(w,h):
    def chunk(tag,data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    data=b''.join(b'\0'+b'\x90\x80\x70\xff'*w for _ in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b'')


def fixture(path: Path, mismatch=False):
    (path/'24x24/apps').mkdir(parents=True)
    (path/'256x256/places').mkdir(parents=True)
    (path/'24x24/apps/editor.png').write_bytes(tiny_png(16 if mismatch else 24,24))
    (path/'256x256/places/folder.png').write_bytes(tiny_png(256,256))
    (path/'index.theme').write_text('[Icon Theme]\nName=Irixium\nComment=Fixture\nInherits=hicolor,breeze\nToolbarDefault=24\nToolbarSizes=16,22,32,48\nDirectories=24x24/apps,256x256/places\n\n[24x24/apps]\nSize=24\nType=Fixed\nContext=Applications\n\n[256x256/places]\nSize=256\nType=Scalable\nMinSize=56\nMaxSize=512\nContext=Places\n')
    return path


def tree_hash(path: Path):
    return {p.relative_to(path).as_posix(): ('link:'+os.readlink(p) if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()) for p in path.rglob('*') if p.is_file() or p.is_symlink()}


class Repairs(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.src=fixture(self.root/'Irixium')
    def tearDown(self):self.tmp.cleanup()
    def test_readonly_audit(self):
        before=tree_hash(self.src);r=audit(self.src)
        self.assertEqual(before,tree_hash(self.src));self.assertEqual(r['errors'],0)
        self.assertEqual({i['code'] for i in r['issues']},{'fallback-order','default-not-in-sizes','raster-scalable'})
    def test_fixed_metadata_and_unchanged_source(self):
        before=tree_hash(self.src);dest=self.root/'Irixium-Fixed'
        r=build_fixed(self.src,dest);self.assertEqual(before,tree_hash(self.src))
        self.assertEqual(r['after']['errors'],0);self.assertEqual(r['after']['warnings'],0)
        self.assertEqual((self.src/'256x256/places/folder.png').read_bytes(),(dest/'256x256/places/folder.png').read_bytes())
        cp=parse_index(dest/'index.theme')
        self.assertEqual(cp['Icon Theme']['Inherits'],'breeze,hicolor')
        self.assertIn('24',cp['Icon Theme']['ToolbarSizes'].split(','))
        self.assertEqual(cp['256x256/places']['Type'],'Fixed')
        self.assertNotIn('MinSize',cp['256x256/places'])
    def test_refuse_existing(self):
        dest=self.root/'Already';dest.mkdir()
        with self.assertRaises(FileExistsError):build_fixed(self.src,dest)
    def test_refuse_nested(self):
        with self.assertRaises(ValueError):build_fixed(self.src,self.src/'Nested')
    def test_refuse_source_equal(self):
        with self.assertRaises(ValueError):build_fixed(self.src,self.src)
    def test_refuse_ancestor(self):
        with self.assertRaises(ValueError):build_fixed(self.src,self.root)
    def test_broken_alias_falls_back(self):
        (self.src/'24x24/apps/missing.png').symlink_to('absent.png')
        r=build_fixed(self.src,self.root/'Fixed')
        self.assertIn('24x24/apps/missing.png',r['skipped_files'])
        self.assertEqual(r['after']['errors'],0)
    def test_good_alias_dereferenced(self):
        (self.src/'24x24/apps/alias.png').symlink_to('editor.png')
        dest=self.root/'Fixed';build_fixed(self.src,dest)
        self.assertFalse((dest/'24x24/apps/alias.png').is_symlink())
        self.assertEqual((dest/'24x24/apps/alias.png').read_bytes(),(dest/'24x24/apps/editor.png').read_bytes())
    def test_external_link_not_copied(self):
        outside=self.root/'external.png';outside.write_bytes(tiny_png(24,24))
        (self.src/'24x24/apps/unsafe.png').symlink_to(outside)
        r=build_fixed(self.src,self.root/'Fixed')
        self.assertIn('24x24/apps/unsafe.png',r['skipped_files'])
    def test_directory_symlink_not_followed(self):
        (self.src/'elsewhere').symlink_to(self.src/'24x24',target_is_directory=True)
        r=audit(self.src)
        self.assertIn('directory-symlink',{i['code'] for i in r['issues']})
    def test_png_mismatch_detected_not_silently_resized(self):
        p=self.src/'24x24/apps/editor.png';p.write_bytes(tiny_png(16,24))
        dest=self.root/'Fixed';r=build_fixed(self.src,dest)
        self.assertEqual(r['after']['errors'],1)
        self.assertEqual(p.read_bytes(),(dest/'24x24/apps/editor.png').read_bytes())
    def test_optin_normalization(self):
        try:import PIL
        except ImportError:self.skipTest('Pillow not installed')
        p=self.src/'24x24/apps/editor.png';p.write_bytes(tiny_png(16,24));original=p.read_bytes()
        dest=self.root/'Fixed';r=build_fixed(self.src,dest,normalize_png=True)
        self.assertEqual(r['after']['errors'],0)
        self.assertEqual(p.read_bytes(),original)
        self.assertEqual(png_size(dest/'24x24/apps/editor.png'),(24,24))
        self.assertEqual(r['normalized_png'],['24x24/apps/editor.png'])
    def test_sprite_sheet_preserved(self):
        p=self.src/'24x24/apps/editor.png';p.write_bytes(tiny_png(24,192))
        index=self.src/'index.theme';index.write_text(index.read_text().replace('Context=Applications','Context=Animations'))
        r=build_fixed(self.src,self.root/'Fixed',normalize_png=True)
        self.assertEqual(r['normalized_png'],[])
        self.assertEqual(r['after']['errors'],0)
        self.assertEqual(png_size(self.root/'Fixed/24x24/apps/editor.png'),(24,192))
    def test_flattened_symlink_not_png(self):
        (self.src/'24x24/apps/bad.png').write_text('editor.png')
        r=audit(self.src);self.assertIn('invalid-image',{i['code'] for i in r['issues']})
    def test_whitespace_in_icon_name_rejects_invalid_gtk_cache(self):
        (self.src/'24x24/apps/invalid name.png').write_bytes(tiny_png(24,24))
        self.assertIn('invalid-cache-name',{i['code'] for i in audit(self.src)['issues']})
    def test_crc_error(self):
        p=self.src/'24x24/apps/editor.png';b=bytearray(p.read_bytes());b[40]^=1;p.write_bytes(b)
        with self.assertRaises(ValueError):png_size(p)
    def test_install_no_activation(self):
        fixed=self.root/'Fixed';build_fixed(self.src,fixed)
        dest=install(fixed,self.root/'data/icons')
        self.assertTrue((dest/'index.theme').is_file())
        self.assertFalse((self.root/'kdeglobals').exists())
    def test_install_refuses_overwrite(self):
        fixed=self.root/'Fixed';build_fixed(self.src,fixed)
        install(fixed,self.root/'icons')
        with self.assertRaises(FileExistsError):install(fixed,self.root/'icons')
    def test_bad_theme_not_installed(self):
        (self.src/'24x24/apps/editor.png').write_bytes(tiny_png(10,10))
        with self.assertRaises(ValueError):install(self.src,self.root/'icons')


class Package(unittest.TestCase):
    def test_original_fixture_hash(self):
        b=(ROOT/'tests/fixtures/Irixium-index.theme').read_bytes()
        self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'b4ad6335a7fa38dc8d832838aced0635ebf2ac78')
    def test_patch_applies_to_audited_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);p=base/'icons/Irixium';p.mkdir(parents=True)
            (p/'index.theme').write_bytes((ROOT/'tests/fixtures/Irixium-index.theme').read_bytes())
            patch=str(ROOT/'patches/0001-irixium-icon-metadata.patch')
            subprocess.run(['git','apply','--check',patch],cwd=base,check=True,capture_output=True)
            subprocess.run(['git','apply',patch],cwd=base,check=True,capture_output=True)
            cp=parse_index(p/'index.theme')
            self.assertEqual(cp['Icon Theme']['Inherits'],'breeze,hicolor')
            self.assertEqual(cp['256x256/places']['Type'],'Fixed')
    def test_new_theme_complete(self):
        theme=ROOT/'themes/IrixClassic-SGI';r=audit(theme)
        self.assertEqual(r['errors'],0);self.assertEqual(r['warnings'],0)
        self.assertEqual(r['symlinks'],0)
        manifest=json.loads((theme/'manifest.json').read_text())
        # The generated core is mandatory; contributed aliases can extend it.
        # audit() above validates every image, including those additions.
        self.assertGreaterEqual(r['png'],manifest['icon_names']*len(manifest['sizes']))
        self.assertGreaterEqual(r['svg'],manifest['icon_names'])
    @unittest.skipUnless(shutil.which('gtk-update-icon-cache'), 'GTK cache tool unavailable')
    def test_both_distributed_themes_generate_valid_gtk_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            for source in (ROOT/'Irixium', ROOT/'themes/IrixClassic-SGI'):
                target=Path(tmp)/source.name
                shutil.copytree(source,target,symlinks=False)
                for options in (['-f','-t'],['--validate']):
                    p=subprocess.run(['gtk-update-icon-cache',*options,str(target)],capture_output=True,text=True)
                    self.assertEqual(p.returncode,0,p.stderr)

    def test_unique_names(self):
        names=[n for i in build_classic.ITEMS for n in [i['name'],*i['aliases']]]
        self.assertEqual(len(names),len(set(names)))
    def test_all_aliases_match_canonical_bytes(self):
        theme=ROOT/'themes/IrixClassic-SGI'
        for item in build_classic.ITEMS:
            for folder,ext in [('scalable','svg')]+[(f'{s}x{s}','png') for s in build_classic.SIZES]:
                parent=theme/folder/item['category'];original=(parent/(item['name']+'.'+ext)).read_bytes()
                for name in item['aliases']:
                    self.assertEqual(original,(parent/(name+'.'+ext)).read_bytes())
    def test_manifest_counts(self):
        m=json.loads((ROOT/'themes/IrixClassic-SGI/manifest.json').read_text())
        self.assertEqual(m['canonical_icons'],126);self.assertEqual(m['unique_artworks'],110)
        self.assertEqual(m['icon_names'],292)
    def test_generator_refuses_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):build_classic.build(Path(tmp),None)


if __name__=='__main__':unittest.main(verbosity=2)
