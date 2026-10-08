"""Verify independent identities and preservation of complete imported theme snapshots."""
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class ModernOptionsTests(unittest.TestCase):
    def test_imported_snapshots_preserve_every_original_file(self):
        for slug in ("modern-13", "modern-41"):
            with self.subTest(slug=slug):
                folder = ROOT / slug
                origin = json.loads((folder / "ORIGEM.json").read_text())
                for name, expected in origin["arquivos_originais"].items():
                    directory = "assets" if Path(name).suffix in (".svg", ".svgz", ".png") else "upstream"
                    stored_name = "upstream-metadata.json" if name == "metadata.json" else name
                    stored = folder / "package" / directory / stored_name
                    self.assertEqual(hashlib.sha256(stored.read_bytes()).hexdigest(), expected, name)
                    if stored.suffix == ".svg":
                        ET.parse(stored)
                self.assertEqual((folder / "LICENSE").read_bytes(), (folder / "package/upstream/LICENSE").read_bytes())

    def test_independent_ids_and_package_integrity(self):
        for slug, plugin_id in (("modern-13", "irixium_modern_13"), ("modern-41", "irixium_modern_41")):
            with self.subTest(slug=slug):
                folder = ROOT / slug
                package = folder / "package"
                metadata = json.loads((package / "metadata.json").read_text())
                self.assertEqual(metadata["KPackageStructure"], "KWin/Decoration")
                self.assertEqual(metadata["KPlugin"]["Id"], plugin_id)
                expected = json.loads((folder / "MANIFEST.json").read_text())["package"]
                actual = {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(package.rglob("*")) if p.is_file()}
                self.assertEqual(actual, expected)
                self.assertEqual(list(package.rglob("metadata.json")), [package / "metadata.json"])


if __name__ == "__main__":
    unittest.main()
