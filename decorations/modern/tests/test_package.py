import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "package"

class ModernPackageTests(unittest.TestCase):
    def test_metadata_has_independent_id(self):
        metadata = json.loads((PACKAGE / "metadata.json").read_text())
        self.assertEqual(metadata["KPackageStructure"], "KWin/Decoration")
        self.assertEqual(metadata["KPlugin"]["Id"], "irixium_modern")

    def test_package_owns_actions_artwork(self):
        for name in ("applications.png", "minimize.svg", "maximize.svg",
                     "restore.svg", "close.svg"):
            self.assertTrue((PACKAGE / "assets" / name).is_file())
        self.assertIn("applications.png", (PACKAGE / "contents/ui/Surface.qml").read_text())
        self.assertIn("menuDoubleClickClosesWindow: false",
                      (PACKAGE / "contents/ui/Settings.qml").read_text())
        main = (PACKAGE / "contents/ui/main.qml").read_text()
        self.assertIn("previewHost: root.parent", main)
        self.assertIn("expectedDecoration: decoration", main)

    def test_no_system_paths(self):
        for path in PACKAGE.rglob("*"):
            if path.is_file() and path.suffix in {".qml", ".js"}:
                text = path.read_text()
                self.assertNotIn("/usr/share", text)
                self.assertNotIn("/usr/lib", text)

    def test_manifest_matches_package(self):
        expected = json.loads((ROOT / "MANIFEST.json").read_text())["package"]
        actual = {
            p.relative_to(PACKAGE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(PACKAGE.rglob("*")) if p.is_file()
        }
        self.assertEqual(actual, expected)
