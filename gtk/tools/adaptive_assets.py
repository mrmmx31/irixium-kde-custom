#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build recolorable integer masks from Classic's own, generated artwork.

GTK recolors three explicit symbolic channels (error/success/warning). Splitting
each image into groups of at most three colors keeps every integer pixel while
allowing independent GTK CSS expressions for all of its original color roles.
The installed theme needs only GTK's native SVG loader, never this Python tool.

Stretchable frames use fixed corners and one-dimensional edge slices. Their
center belongs to the widget's background-color, like the original border-image
without the `fill` keyword. A whole frame SVG is never stretched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Callable

PACKAGE = Path(__file__).resolve().parents[1] / "IrixClassic"
SOURCE = PACKAGE / "common" / "assets"
DESTINATION = PACKAGE.parent / "IrixClassic-KDE" / "common" / "adaptive"
CHANNELS = ("error", "success", "warning")
CHANNEL_INKS = ("#cc0000", "#4e9a06", "#f57900")
FRAME_BORDERS = {
    "command": 3, "palettebutton": 2,
    "input": 3, "inset": 3, "option": 3, "spin": 2,
}


def _name(asset: str) -> str:
    value = asset.removesuffix(".png")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Invalid Classic asset name: " + asset)
    return value


def _border(asset: str) -> int:
    stem, _, state = asset.rpartition("-")
    if state in ("normal", "focused", "pressed", "toggled", "disabled"):
        return FRAME_BORDERS.get(stem, 0)
    return 0


def _regions(width: int, height: int, border: int) -> list[dict]:
    if not border:
        return [{"part": "glyph", "box": [0, 0, width, height],
                 "position": "center", "size": f"{width}px {height}px", "repeat": "no-repeat"}]
    if min(width, height) <= 2 * border:
        raise ValueError("Frame is smaller than its two borders")
    n = border
    # The center is absent. Corners paint first (CSS's upper layers); opaque
    # corner masks cover repeated edge strips at the four intersections. Each
    # edge is a 1px strip, repeated rather than rescaled: Gtk3's bilinear image
    # scaling would otherwise soften the first/last pixels of every color mask.
    return [
        {"part": "top-left", "box": [0, 0, n, n], "position": "left top", "size": f"{n}px {n}px", "repeat": "no-repeat"},
        {"part": "top-right", "box": [width-n, 0, width, n], "position": "right top", "size": f"{n}px {n}px", "repeat": "no-repeat"},
        {"part": "bottom-left", "box": [0, height-n, n, height], "position": "left bottom", "size": f"{n}px {n}px", "repeat": "no-repeat"},
        {"part": "bottom-right", "box": [width-n, height-n, width, height], "position": "right bottom", "size": f"{n}px {n}px", "repeat": "no-repeat"},
        {"part": "top", "box": [n, 0, n+1, n], "position": "left top", "size": f"1px {n}px", "repeat": "repeat-x"},
        {"part": "bottom", "box": [n, height-n, n+1, height], "position": "left bottom", "size": f"1px {n}px", "repeat": "repeat-x"},
        {"part": "left", "box": [0, n, n, n+1], "position": "left top", "size": f"{n}px 1px", "repeat": "repeat-y"},
        {"part": "right", "box": [width-n, n, width, n+1], "position": "right top", "size": f"{n}px 1px", "repeat": "repeat-y"},
    ]


def _svg(pixels: list[list], colors: list[str]) -> str:
    """Run-length rectangles retain exact pixels and keep generated SVG small."""
    height, width = len(pixels), len(pixels[0])
    rows = ['<!-- SPDX-License-Identifier: GPL-3.0-or-later -->',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">']
    for index, color in enumerate(colors):
        for y, row in enumerate(pixels):
            x = 0
            while x < width:
                if row[x] != color:
                    x += 1
                    continue
                start = x
                while x < width and row[x] == color:
                    x += 1
                rows.append(f'<rect x="{start}" y="{y}" width="{x-start}" height="1" '
                            f'class="{CHANNELS[index]}" fill="{CHANNEL_INKS[index]}"/>')
    rows.append("</svg>")
    return "\n".join(rows) + "\n"


def generate(destination: Path = DESTINATION, source: Path = SOURCE,
             names: list[str] | None = None) -> dict:
    """Generate masks/metadata only; never modify original PNGs or stylesheets."""
    from PIL import Image

    destination = Path(destination)
    source = Path(source)
    destination.mkdir(parents=True, exist_ok=True)
    if names is None:
        names = sorted({Path(name).stem
                        for path in (PACKAGE / "common" / "gtk.css", PACKAGE / "gtk-3.0" / "gtk.css", PACKAGE / "gtk-4.0" / "gtk.css")
                        for name in re.findall(r'url\("([^"]+\.png)"\)', path.read_text())})
    selected = sorted(_name(n) for n in names)
    assets = {}
    generated = {}
    for name in selected:
        original = source / (name + ".png")
        image = Image.open(original).convert("RGBA")
        if any(pixel[3] not in (0, 255) for pixel in image.getdata()):
            raise ValueError("Classic masks require integer opaque/transparent pixels: " + name)
        width, height = image.size
        border = _border(name)
        if border:
            n = border
            corners = [(x, y) for x0, y0 in ((0, 0), (width-n, 0), (0, height-n), (width-n, height-n))
                       for y in range(y0, y0+n) for x in range(x0, x0+n)]
            if any(image.getpixel(point)[3] != 255 for point in corners):
                raise ValueError("Repeated frame strips need opaque corners: " + name)
            for y in (*range(n), *range(height-n, height)):
                if len({image.getpixel((x, y)) for x in range(n, width-n)}) != 1:
                    raise ValueError("Frame has a nonuniform horizontal edge: " + name)
            for x in (*range(n), *range(width-n, width)):
                if len({image.getpixel((x, y)) for y in range(n, height-n)}) != 1:
                    raise ValueError("Frame has a nonuniform vertical edge: " + name)
        parts = []
        for region in _regions(width, height, border):
            x0, y0, x1, y1 = region["box"]
            pixels = [["#%02x%02x%02x" % image.getpixel((x, y))[:3]
                       if image.getpixel((x, y))[3] else None
                       for x in range(x0, x1)] for y in range(y0, y1)]
            colors = sorted({color for row in pixels for color in row if color})
            layers = []
            for first in range(0, len(colors), len(CHANNELS)):
                group = colors[first:first+len(CHANNELS)]
                filename = f"{name}-{region['part']}-{first//len(CHANNELS)}-symbolic.svg"
                payload = _svg(pixels, group)
                (destination / filename).write_text(payload)
                generated[filename] = hashlib.sha256(payload.encode()).hexdigest()
                layers.append({"file": filename, "colors": group})
            parts.append({**region, "layers": layers})
        assets[name] = {"width": width, "height": height, "border": border,
                        "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                        "slices": parts}
    manifest = {"schema": 1, "algorithm": "GTK symbolic three-channel integer masks",
                "assets": assets, "files": generated}
    (destination / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _asset(asset: str, manifest: dict | None) -> dict:
    if manifest is None:
        manifest = json.loads((DESTINATION / "MANIFEST.json").read_text())
    name = _name(asset)
    try:
        return manifest["assets"][name]
    except KeyError as exc:
        raise ValueError("Classic adaptive asset has not been generated: " + name) from exc


def geometry(asset: str, *, manifest: dict | None = None) -> dict:
    """Return intrinsic pixel size and invariant border thickness."""
    value = _asset(asset, manifest)
    return {key: value[key] for key in ("width", "height", "border")}


def slices(asset: str, *, manifest: dict | None = None) -> list[dict]:
    """Return fixed-corner / longitudinal-edge / glyph mask metadata."""
    return _asset(asset, manifest)["slices"]


def expression(asset: str, colorresolver: Callable[[str], str], *,
               prefix: str = "adaptive/", manifest: dict | None = None) -> dict[str, str]:
    """CSS properties for a recolored asset; resolver(hex) supplies GTK colors.

    Relative `prefix` is resolved from the importing stylesheet. This API does
    not change widget metrics or its center background-color. Keep the original
    border width for frames. Glyph callers may override position/repeat.
    """
    if '"' in prefix or "\n" in prefix or "\r" in prefix:
        raise ValueError("Invalid adaptive asset URL prefix")
    images, positions, sizes, repeats = [], [], [], []
    value = _asset(asset, manifest)
    for part in value["slices"]:
        for layer in part["layers"]:
            palette = []
            for channel, color in zip(CHANNELS, layer["colors"]):
                resolved = colorresolver(color)
                if not isinstance(resolved, str) or not resolved.strip():
                    raise ValueError("Color resolver did not provide a CSS color for " + color)
                palette.append(channel + " " + resolved)
            images.append('-gtk-recolor(url("' + prefix + layer["file"] + '"), ' + ", ".join(palette) + ")")
            positions.append(part["position"])
            sizes.append(part["size"])
            repeats.append(part["repeat"])
    if not images:
        return {"background-image": "none"}
    result = {
        "background-image": ", ".join(images),
        "background-position": ", ".join(positions),
        "background-size": ", ".join(sizes),
        "background-repeat": ", ".join(repeats),
        "background-origin": "border-box",
        "background-clip": "border-box",
    }
    if value["border"]:
        result["border-image-source"] = "none"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    parser.add_argument("--source-dir", type=Path, default=SOURCE)
    parser.add_argument("assets", nargs="*")
    args = parser.parse_args()
    manifest = generate(args.output_dir, args.source_dir, args.assets or None)
    print(f"Built {len(manifest['assets'])} Classic adaptive assets / {len(manifest['files'])} SVG masks")


if __name__ == "__main__":
    main()
