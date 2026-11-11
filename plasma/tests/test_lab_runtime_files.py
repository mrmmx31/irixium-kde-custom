#!/usr/bin/env python3
"""Private fixture must include the runtime's local import dependencies."""
import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('lab_launcher', ROOT / 'plasma/tools/abrir-laboratorio-temas.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class RuntimeFilesTests(unittest.TestCase):
    def test_scene_and_gallery_helpers_are_delivered(self):
        files = set(lab.runtime_python_files(ROOT))
        for name in ('control_hints.py', 'scene_contract.py', 'preview_event_writer.py',
                     'native_scene_gtk2.py', 'gtk2_hint_position.py', 'tooltip_position.py'):
            self.assertIn(ROOT / 'tools/theme-lab' / name, files)
        self.assertIn(ROOT / 'plasma/tests/galerias-nativas/qt_widget_hints.py', files)
        self.assertFalse(any('/theme-lab/tests/' in str(p) for p in files))

    def test_local_static_and_filename_imports_are_closed(self):
        files = set(lab.runtime_python_files(ROOT))
        for path in files:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    names.append(node.module.split('.')[0] + '.py')
                elif isinstance(node, ast.Import):
                    names.extend(alias.name.split('.')[0] + '.py' for alias in node.names)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.endswith('.py'):
                    names.append(node.value)
                for name in names:
                    target = path.parent / name
                    if target.is_file():
                        self.assertIn(target, files, f'{path.name} imports {name}')


if __name__ == '__main__':
    unittest.main()
