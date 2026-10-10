# SPDX-License-Identifier: GPL-3.0-or-later
"""Use real DomainOS artwork through the private Kvantum transaction backend.

Native signals are replaced by an explicit recorder. This test verifies file
ownership and mapper dispatch, not live application or native palette pixels.
"""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import kvantum_palette_runtime as runtime
from theme_companion_bridge import native_palette_signature
from theme_transaction import Failure, snapshot
from test_domainos_motif import QT, css, exported


class DomainOSRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.domainos-kvantum-runtime-', dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.private = Path(self.temp.name)
        self.config, self.state = self.private/'config', self.private/'state'
        self.theme = 'DomainOS-SR10-4'
        self.profile = {'global': 'org.magpie.irixclassic.domainos.desktop', 'kvantum': self.theme}
        self.source = self.config/'Kvantum'/self.theme
        self.source.mkdir(parents=True)
        for suffix in ('.svg', '.kvconfig'):
            shutil.copyfile(ROOT/'kvantum'/self.theme/(self.theme+suffix), self.source/(self.theme+suffix))
        self.selector = self.config/'Kvantum/kvantum.kvconfig'
        self.selector.write_text('[General]\ntheme='+self.theme+'\n[Applications]\npersonal=Other\n')
        (self.config/'kdeglobals').write_text('[KDE]\nwidgetStyle=kvantum\nLookAndFeelPackage='+self.profile['global']+'\n')
        self.css = self.config/'gtk-3.0/colors.css'
        self.css.parent.mkdir(); self.css.write_bytes(css(exported()))
        self.protected = self.config/'Kvantum/IrixClassic/IrixClassic.svg'
        self.protected.parent.mkdir(); self.protected.write_bytes(b'other family must remain unchanged')
        self.before = {path: snapshot(path) for path in [*self.source.iterdir(), self.protected, self.selector]}
        self.events = []

    def refresh(self):
        native = {'palette': QT, 'source_signature': native_palette_signature(self.config)}
        with redirect_stdout(io.StringIO()), patch.object(runtime, 'require_global'):
            return runtime.refresh(self.config, self.state, self.profile,
                notify_style=lambda *_: self.events.append('native-event') or 'native_style_and_palette_sent',
                style_name=lambda _: 'kvantum', native=native)

    def test_distinct_domainos_aliases_recolor_preserve_geometry_and_restore_exact_selection(self):
        first = self.refresh()
        self.assertEqual(first['theme'], self.theme+'-KDE')
        self.assertTrue(first['coverage']['geometryUnchanged'])
        before_svg = runtime.generated_paths(self.config, self.theme)[0].read_bytes()
        self.css.write_bytes(css(exported('yellow')))
        second = self.refresh()
        self.assertEqual(second['theme'], self.theme+'-KDE-Reload')
        self.assertEqual(first['coverage']['geometrySha256'], second['coverage']['geometrySha256'])
        self.assertNotEqual(runtime.generated_paths(self.config, self.theme)[0].read_bytes(), before_svg)
        self.assertEqual(self.refresh()['status'], 'unchanged')
        self.assertEqual(len(self.events), 2)
        record = json.loads((self.state/'irixium-kvantum-palette'/self.theme/'control.json').read_text())
        self.assertTrue(all('/DomainOS-SR10-4' in target for target in record['targets']))
        with redirect_stdout(io.StringIO()): runtime.restore(self.config, self.state, self.theme)
        self.assertEqual({path: snapshot(path) for path in self.before}, self.before)
        self.assertTrue(all(not path.exists() for path in runtime.generated_paths(self.config, self.theme)))

    def test_later_domainos_art_edit_blocks_update_without_touching_classic(self):
        self.refresh()
        generated = runtime.generated_paths(self.config, self.theme)[0]
        generated.write_bytes(generated.read_bytes()+b'<!-- personal edit -->')
        before = {path: snapshot(path) for path in [generated, self.selector, self.protected]}
        self.css.write_bytes(css(exported('dark')))
        with self.assertRaisesRegex(Failure, 'editada'): self.refresh()
        self.assertEqual({path: snapshot(path) for path in before}, before)
        self.assertEqual(len(self.events), 1)


if __name__ == '__main__': unittest.main()
