# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wine_manage',ROOT/'wine/IrixClassic/package/manage.py')
manage = importlib.util.module_from_spec(spec)
previous = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True; spec.loader.exec_module(manage)
finally: sys.dont_write_bytecode = previous


class WineClassicTest(unittest.TestCase):
    def test_export_roundtrip_handles_binary_unicode_default_and_continuation(self):
        raw = ('Windows Registry Editor Version 5.00\r\n\r\n'
               '[HKEY_CURRENT_USER\\Control Panel\\Desktop\\WindowMetrics]\r\n'
               '"CaptionFont"=hex:01,ab,\\\r\n  cd,ef\r\n'
               '"Nome"="ação \\\"SGI\\\""\r\n@=dword:00000001\r\n').encode('utf-16')
        values = manage.parse_reg(raw)
        self.assertEqual(len(values),3)
        self.assertEqual(manage.parse_reg(manage.reg_patch({},values)),values)
        self.assertIn('hex:01,ab,cd,ef',[v[2] for v in values.values()])

    def test_outside_registry_scopes_rejected(self):
        with self.assertRaises(RuntimeError):
            manage.parse_reg(b'[HKEY_CURRENT_USER\\Software\\Other]\n"x"="y"')

    def test_restore_preserves_later_unrelated_settings(self):
        before={'color':['key','"color"','"gray"'],'font':['key','"font"','"original"']}
        after={**before,'color':['key','"color"','"teal"'],'new':['key','"new"','"new"']}
        later={**after,'font':['key','"font"','"user-font"'],'app':['key','"app"','"user"']}
        desired=manage.merged_restore(later,before,after)
        self.assertEqual(desired['color'],before['color'])
        self.assertEqual(desired['font'],later['font'])
        self.assertEqual(desired['app'],later['app'])
        self.assertNotIn('new',desired)

    def test_restore_refuses_later_change_to_managed_value(self):
        with self.assertRaises(RuntimeError):
            manage.merged_restore({'color':['key','"color"','"red"']},
                                 {'color':['key','"color"','"gray"']},
                                 {'color':['key','"color"','"teal"']})

    def test_no_theme_or_registry_changes_when_prefix_uninitialized(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(manage.subprocess,'run') as run, self.assertRaises(RuntimeError):
                manage.Wine(Path(folder)/'absent')
            run.assert_not_called()
            self.assertFalse((Path(folder)/'absent').exists())

    def test_symlink_prefix_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            link=Path(folder)/'prefix';link.symlink_to(folder,target_is_directory=True)
            with self.assertRaises(RuntimeError): manage.Wine(link)

    def test_portable_registry_file_has_no_font_or_application_overrides(self):
        text=(ROOT/'wine/IrixClassic/package/IrixClassic.theme').read_text(encoding='utf-16')
        self.assertNotIn('Font',text);self.assertNotIn('AppDefaults',text)

    def test_resource_style_has_no_code_entry_imports_or_timestamp(self):
        data=(ROOT/'wine/IrixClassic/package/IrixClassic.msstyles').read_bytes()
        pe=struct.unpack_from('<I',data,0x3c)[0]; opt=pe+24
        self.assertEqual(data[:2],b'MZ');self.assertEqual(data[pe:pe+4],b'PE\0\0')
        self.assertEqual(struct.unpack_from('<I',data,pe+8)[0],0)
        self.assertEqual(struct.unpack_from('<I',data,opt+16)[0],0)
        self.assertEqual(struct.unpack_from('<II',data,opt+96+8),(0,0))

    def test_original_artwork_and_native_source_hashes_match(self):
        package=ROOT/'wine/IrixClassic/package'
        origin=json.loads((package/'ORIGEM.json').read_text())
        self.assertEqual(origin['msstyles_sha256'],hashlib.sha256((package/'IrixClassic.msstyles').read_bytes()).hexdigest())
        for name,expected in origin['artwork_sources'].items():
            self.assertTrue(name.startswith('gtk/IrixClassic/common/assets/'))
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
        for name,expected in origin['native_utilities'].items():
            file=ROOT/name if name.startswith('wine/') else package/name
            self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),expected)


if __name__ == '__main__': unittest.main()
