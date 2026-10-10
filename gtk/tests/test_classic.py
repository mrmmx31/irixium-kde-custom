#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Theme/package invariants; native behavior is exercised by the private hosts."""
import configparser
import hashlib
import json
from pathlib import Path
import re
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GTK = ROOT / "gtk"
CLASSIC = GTK / "IrixClassic"


class GTKPackageTests(unittest.TestCase):
    def test_modern_preserved_byte_for_byte(self):
        evidence = json.loads((GTK / "MODERN-PRESERVED.json").read_text())
        modern = GTK / "Irixium"
        files = {str(p.relative_to(modern)) for p in modern.rglob("*") if p.is_file()}
        self.assertEqual(files, set(evidence["files"]))
        for name, digest in evidence["files"].items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((modern / name).read_bytes()).hexdigest(), digest)

    def test_separate_installable_identities(self):
        for name in ("Irixium", "IrixClassic"):
            parser = configparser.ConfigParser()
            parser.read(GTK / name / "index.theme")
            self.assertEqual(parser["X-GNOME-Metatheme"]["GtkTheme"], name)
            self.assertEqual(parser["Desktop Entry"]["Name"], name)
            for version, filename in (("2.0", "gtkrc"), ("3.0", "gtk.css"), ("4.0", "gtk.css")):
                self.assertTrue((GTK / name / ("gtk-" + version) / filename).is_file())

    def test_all_resources_resolve_inside_classic_package(self):
        used = set()
        for path in list(CLASSIC.rglob("*.css")) + [CLASSIC / "gtk-2.0/gtkrc"]:
            text = path.read_text()
            references = re.findall(r'url\("([^\"]+)"\)', text)
            references += re.findall(r'(?:overlay_file|file)\s*=\s*"([^\"]+)"', text)
            for reference in references:
                target = (path.parent / reference).resolve()
                with self.subTest(path=str(path), reference=reference):
                    self.assertTrue(target.is_file())
                    self.assertIn(CLASSIC.resolve(), target.parents)
                used.add(target)
        self.assertGreater(len(used), 80)
        self.assertFalse(list(CLASSIC.rglob("*.so")), "GTK2's external engine must not be bundled")

    def test_palette_tracks_local_classic_color_roles(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ROOT / "kvantum/IrixClassic/IrixClassic.kvconfig")
        colors = parser["GeneralColors"]
        css = (CLASSIC / "common/gtk.css").read_text()
        mapping = {"theme_bg_color": "window.color", "theme_fg_color": "window.text.color",
                   "theme_base_color": "base.color", "theme_text_color": "text.color",
                   "theme_selected_bg_color": "highlight.color", "theme_selected_fg_color": "highlight.text.color",
                   "inactive_selection": "inactive.highlight.color", "insensitive_fg_color": "disabled.text.color"}
        for gtkname, qtname in mapping.items():
            self.assertRegex(css, r"@define-color\s+" + gtkname + r"\s+" + colors[qtname] + ";")

    def test_feedback_has_no_css_timing_or_soft_gradients(self):
        css = (CLASSIC / "common/gtk.css").read_text()
        self.assertRegex(css, r"transition-property:\s*none;")
        self.assertRegex(css, r"transition-duration:\s*0s;")
        self.assertRegex(css, r"transition-delay:\s*0s;")
        self.assertRegex(css, r"animation-name:\s*none;")
        self.assertNotRegex(css, r"(?:linear|radial|repeating-\w+)-gradient\(")
        self.assertTrue(all(value.strip() in ("0", "0px") for value in re.findall(r"border-radius:([^;]+);", css)))
        self.assertIn("gtk-enable-animations = 0", (CLASSIC / "gtk-2.0/gtkrc").read_text())

    def test_pressed_asset_inverts_inner_bands_without_moving_outline(self):
        assets = CLASSIC / "common/assets"
        normal = Image.open(assets / "command-normal.png").convert("RGBA")
        pressed = Image.open(assets / "command-pressed.png").convert("RGBA")
        self.assertEqual(normal.size, pressed.size)
        width, height = normal.size
        for x in range(width):
            self.assertEqual(normal.getpixel((x, 0)), pressed.getpixel((x, 0)))
            self.assertEqual(normal.getpixel((x, height - 1)), pressed.getpixel((x, height - 1)))
        for y in range(height):
            self.assertEqual(normal.getpixel((0, y)), pressed.getpixel((0, y)))
            self.assertEqual(normal.getpixel((width - 1, y)), pressed.getpixel((width - 1, y)))
        self.assertNotEqual(normal.getpixel((1, 1)), pressed.getpixel((1, 1)))
        self.assertEqual(normal.getpixel((width // 2, height // 2)), pressed.getpixel((width // 2, height // 2)))

    def test_distinct_check_radio_and_unavailable_marks(self):
        assets = CLASSIC / "common/assets"
        for kind, ink in (("check", (204, 0, 0, 255)), ("radio", (0, 0, 204, 255))):
            active = Image.open(assets / f"{kind}-on.png").convert("RGBA")
            disabled = Image.open(assets / f"{kind}-on-disabled.png").convert("RGBA")
            self.assertEqual(active.size, (15, 15))
            self.assertEqual(disabled.size, active.size)
            self.assertIn(ink, set(active.getdata()))
            self.assertNotIn(ink, set(disabled.getdata()))
            self.assertIn((133, 133, 133, 255), set(disabled.getdata()))
        self.assertNotEqual((assets / "check-on.png").read_bytes(), (assets / "radio-on.png").read_bytes())

    def test_theme_inherits_profile_font_family_and_size(self):
        css = (CLASSIC / "common/gtk.css").read_text()
        self.assertNotIn("font-family:", css)
        for value in re.findall(r"font-size:([^;]+);", css):
            self.assertTrue(value.strip().endswith("em"), "Relative typography must inherit the user's size")
        rc = (CLASSIC / "gtk-2.0/gtkrc").read_text()
        self.assertNotIn("gtk-font-name", rc)
        self.assertEqual(re.findall(r'font_name\s*=\s*"([^\"]+)"', rc), ["Italic"])

    def test_classic_manifest_covers_whole_installed_package(self):
        manifest = json.loads((CLASSIC / "MANIFEST.json").read_text())
        files = {str(p.relative_to(CLASSIC)) for p in CLASSIC.rglob("*") if p.is_file() and p.name != "MANIFEST.json"}
        self.assertEqual(files, set(manifest["files"]))
        for name, digest in manifest["files"].items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((CLASSIC / name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
