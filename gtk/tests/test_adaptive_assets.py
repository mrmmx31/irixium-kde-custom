#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check generated masks against independent original Classic pixel maps."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from PIL import Image

GTK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("classic_adaptive_assets", GTK / "tools" / "adaptive_assets.py")
adaptive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adaptive)


def mask_pixels(directory, part):
    """Decode integer SVG rectangles using the recorded symbolic palette."""
    width, height = part["box"][2]-part["box"][0], part["box"][3]-part["box"][1]
    pixels = [[None] * width for _ in range(height)]
    for layer in part["layers"]:
        palette = dict(zip(adaptive.CHANNELS, layer["colors"]))
        tree = ET.parse(directory / layer["file"])
        for rect in tree.getroot().findall("{http://www.w3.org/2000/svg}rect"):
            color = palette[rect.attrib["class"]]
            x0, y0, w, h = (int(rect.attrib[key]) for key in ("x", "y", "width", "height"))
            for y in range(y0, y0+h):
                for x in range(x0, x0+w):
                    if pixels[y][x] is not None:
                        raise AssertionError("Color masks overlap")
                    pixels[y][x] = color
    return pixels


class AdaptiveAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="irixclassic-adaptive-unit-")
        cls.output = Path(cls.temporary.name)
        cls.names = ["command-normal", "command-pressed", "input-normal", "check-on"]
        cls.manifest = adaptive.generate(cls.output, names=cls.names)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_every_mask_pixel_matches_original_source_crop(self):
        for name, asset in self.manifest["assets"].items():
            original = Image.open(adaptive.SOURCE / (name + ".png")).convert("RGBA")
            self.assertEqual(asset["source_sha256"], hashlib.sha256((adaptive.SOURCE / (name + ".png")).read_bytes()).hexdigest())
            for part in asset["slices"]:
                pixels = mask_pixels(self.output, part)
                x0, y0, x1, y1 = part["box"]
                expected = [["#%02x%02x%02x" % original.getpixel((x, y))[:3]
                             if original.getpixel((x, y))[3] else None
                             for x in range(x0, x1)] for y in range(y0, y1)]
                with self.subTest(asset=name, part=part["part"]):
                    self.assertEqual(pixels, expected)

    def test_command_repeated_edges_and_corners_match_independent_large_artwork(self):
        spec = importlib.util.spec_from_file_location("button_art", GTK.parent / "kvantum" / "tools" / "button_art.py")
        art = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(art)
        for state in ("normal", "pressed"):
            parts = adaptive.slices("command-" + state, manifest=self.manifest)
            for width, height in ((9, 9), (157, 31), (47, 63)):
                result = [[art.FACE] * width for _ in range(height)]
                # CSS paints the last image first. Corner layers cover strips.
                for part in reversed(parts):
                    mask = mask_pixels(self.output, part)
                    mh, mw = len(mask), len(mask[0])
                    positions = part["position"].split()
                    left = width-mw if "right" in positions else 0
                    top = height-mh if "bottom" in positions else 0
                    for y in range(height if part["repeat"] == "repeat-y" else mh):
                        for x in range(width if part["repeat"] == "repeat-x" else mw):
                            color = mask[y % mh][x % mw]
                            if color:
                                result[top+y][left+x] = color
                with self.subTest(state=state, width=width, height=height):
                    self.assertEqual(result, art.surface("command", state, width, height)[0])

    def test_geometry_and_css_do_not_rescale_bands_or_add_timing(self):
        self.assertEqual(adaptive.geometry("command-normal", manifest=self.manifest), {"width": 24, "height": 24, "border": 3})
        props = adaptive.expression("command-normal", lambda color: "@paint_" + color[1:], manifest=self.manifest)
        self.assertEqual(props["background-origin"], "border-box")
        self.assertEqual(props["background-clip"], "border-box")
        self.assertEqual(props["border-image-source"], "none")
        self.assertNotIn("calc", props["background-size"])
        self.assertNotIn("100%", props["background-size"])
        self.assertIn("repeat-x", props["background-repeat"])
        self.assertIn("repeat-y", props["background-repeat"])
        self.assertNotIn("border", props)  # Existing CSS owns the widget metrics.
        self.assertNotIn("background-color", props)  # Existing CSS owns its face.
        self.assertTrue(all(not key.startswith(("transition", "animation")) for key in props))

    def test_glyph_uses_at_most_three_explicit_channels_and_keeps_transparency(self):
        asset = self.manifest["assets"]["check-on"]
        self.assertEqual(asset["border"], 0)
        self.assertEqual(len(asset["slices"]), 1)
        self.assertEqual(len(asset["slices"][0]["layers"]), 3)
        for layer in asset["slices"][0]["layers"]:
            self.assertLessEqual(len(layer["colors"]), 3)
        props = adaptive.expression("check-on", lambda color: color, manifest=self.manifest)
        self.assertNotIn("foreground ", props["background-image"])
        self.assertNotIn("border-image-source", props)

    def test_generated_manifest_and_files_are_deterministic(self):
        before = {name: (self.output / name).read_bytes() for name in self.manifest["files"]}
        rebuilt = adaptive.generate(self.output, names=list(reversed(self.names)))
        self.assertEqual(rebuilt, self.manifest)
        self.assertEqual(before, {name: (self.output / name).read_bytes() for name in rebuilt["files"]})
        for name, digest in rebuilt["files"].items():
            self.assertEqual(hashlib.sha256(before[name]).hexdigest(), digest)

    def test_missing_assets_invalid_identifiers_and_empty_colors_are_refused(self):
        for name in ("../command-normal", "command-normal.svg", "not-generated"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                adaptive.expression(name, lambda color: color, manifest=self.manifest)
        with self.assertRaises(ValueError):
            adaptive.expression("command-normal", lambda color: "", manifest=self.manifest)
        with self.assertRaises(ValueError):
            adaptive.expression("command-normal", lambda color: color, prefix='bad"url', manifest=self.manifest)


if __name__ == "__main__":
    unittest.main()
