import configparser
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import apply_color_scheme as colors


class ApplyColors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data, self.config, self.state = (self.root/p for p in ('data', 'config', 'state'))
        (self.data/'color-schemes').mkdir(parents=True)
        self.config.mkdir()
        self.scheme = self.data/'color-schemes/Private.colors'
        self.scheme.write_text('[General]\nName=Private\n'
            '[Colors:Window]\nBackgroundNormal=12,34,56\nForegroundNormal=234,221,203\n'
            '[WM]\nactiveBackground=78,90,12\ninactiveBackground=34,56,78\n')
        self.globals = self.config/'kdeglobals'
        self.globals.write_text('[General]\nColorScheme=Private\n[User]\nKeep=custom\n'
                               '[Colors:Window]\nBackgroundNormal=1,2,3\n')
        self.calls = []

    def native(self, args, **kwargs):
        scheme = args[1]
        self.calls.append(scheme)
        # Model KDE's actual short circuit, which caused this regression.
        if colors.selected(self.config) == scheme:
            return
        source = colors.ini(self.data/'color-schemes'/(scheme+'.colors'))
        current = colors.ini(self.globals)
        current.set('General', 'ColorScheme', scheme)
        for group in source.sections():
            if group == 'WM' or group.startswith('Colors:'):
                if not current.has_section(group): current.add_section(group)
                for key, value in source.items(group): current.set(group, key, value)
        with self.globals.open('w') as stream: current.write(stream)

    def run_apply(self, native=None):
        with patch.object(colors.subprocess, 'run', side_effect=native or self.native):
            return colors.apply(self.data, self.config, self.state, 'Private')

    def test_same_name_updated_palette_is_applied_and_alias_removed(self):
        result = self.run_apply()
        self.assertEqual(result['status'], 'applied')
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.calls[-1], 'Private')
        current = colors.ini(self.globals)
        self.assertEqual(current.get('Colors:Window', 'BackgroundNormal'), '12,34,56')
        self.assertEqual(current.get('WM', 'activeBackground'), '78,90,12')
        self.assertEqual(current.get('User', 'Keep'), 'custom')
        self.assertEqual(list((self.data/'color-schemes').glob('IrixPaletteReload-*')), [])

    def test_different_scheme_needs_no_alias(self):
        self.globals.write_text('[General]\nColorScheme=Before\n')
        self.run_apply()
        self.assertEqual(self.calls, ['Private'])

    def test_reported_name_without_roles_is_rejected(self):
        def broken(args, **kwargs):
            self.globals.write_text('[General]\nColorScheme='+args[1]+'\n')
        with self.assertRaisesRegex(colors.Failure, 'Papéis KDE'):
            self.run_apply(broken)

    def test_failed_final_apply_keeps_selected_alias_valid(self):
        def broken(args, **kwargs):
            if args[1] == 'Private':
                raise subprocess.CalledProcessError(1, args)
            return self.native(args, **kwargs)
        with self.assertRaises(subprocess.CalledProcessError): self.run_apply(broken)
        selected = colors.selected(self.config)
        self.assertTrue(selected.startswith('IrixPaletteReload-'))
        self.assertEqual((self.data/'color-schemes'/(selected+'.colors')).read_bytes(),
                         self.scheme.read_bytes())

    def test_alias_with_concurrent_edit_is_preserved(self):
        def altered(args, **kwargs):
            self.native(args, **kwargs)
            if args[1].startswith('IrixPaletteReload-'):
                path = self.data/'color-schemes'/(args[1]+'.colors')
                path.write_text(path.read_text()+'\n# independent edit\n')
        self.run_apply(altered)
        remaining = list((self.data/'color-schemes').glob('IrixPaletteReload-*'))
        self.assertEqual(len(remaining), 1)
        self.assertIn('independent edit', remaining[0].read_text())

    def test_invalid_identifier_and_source_rejected_before_native_application(self):
        with patch.object(colors.subprocess, 'run') as native:
            with self.assertRaises(colors.Failure):
                colors.apply(self.data, self.config, self.state, '../Private')
            self.scheme.write_text('[General]\nName=OnlyName\n')
            with self.assertRaises(colors.Failure): self.run_apply()
            native.assert_not_called()


if __name__ == '__main__': unittest.main()
