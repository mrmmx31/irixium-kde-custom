# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import validate_snapshot
from native_scene_gtk2 import ScrollbarScene

TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class EntryIntegrationTests(unittest.TestCase):
    def test_generation_and_binding_guard_without_gui(self):
        data = model()
        data['selected_family'] = 'gtk2'
        data['recipes']['gtk2'].update(visible_controls=1 << 4, selected_control=4)
        original = copy.deepcopy(data)
        snippet = backend.snippet(ROOT, data, kdeglobals=ROOT/'colors/DomainOS-SR10.4.colors')
        self.assertEqual(snippet['source_kind'], 'translated_native_fragment')
        self.assertIn('detail = \"entry\"', snippet['source'])
        self.assertIn('GtkEntry::state-hint = 1', snippet['source'])
        self.assertIn('detail = "entry" state = ACTIVE', snippet['source'])
        with self.assertRaisesRegex(backend.Unavailable, 'origem explícita'):
            backend.snippet(ROOT, data)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-entry-generation-') as temp:
            folder = Path(temp)
            receipt = generate_scrollbar_snapshot(backend, ROOT, folder, data,
                                                  ROOT/'colors/DomainOS-SR10.4.colors')
            self.assertIn('entry', receipt['translated_controls'])
            self.assertFalse(receipt['recipe_applied'])
            self.assertFalse(receipt['scene_integrated'])
            self.assertEqual(validate_snapshot(backend, ROOT, receipt['rc'], data)['entry_style_id'],
                             receipt['entry_style_id'])
            manifest = folder/'GTK2-SCROLLBAR-PROPOSAL.json'
            receipt['entry_style_id'] = '0123456789abcdef'
            manifest.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'não corresponde aos recursos'):
                validate_snapshot(backend, ROOT, receipt['rc'], data)
        self.assertEqual(data, original)

    def test_missing_style_rejected_before_widget_creation(self):
        data = model()
        data['recipes']['gtk2']['visible_controls'] = 1 << 4
        with self.assertRaisesRegex(ValueError, 'estilo de entrada'):
            ScrollbarScene(None, data)


if __name__ == '__main__':
    unittest.main()
