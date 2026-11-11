"""Compare observed X11 font metrics with Pango/Qt measurements.

This is an evidence reader. It neither installs fonts nor applies a theme.
ASCII is intentional: HP-Roman8 bytes are not Unicode code points.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

GLYPH = re.compile(
    r"^\s+0x([0-9a-fA-F]+)\s+\(\d+\)\s+"
    r"(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+0x"
)
SAMPLES = ("OK", "Cancel", "Help", "Terminal", "File Manager", "0123456789")


def read_x11(path):
    raw = path.read_bytes()
    text = raw.decode("latin1")
    glyphs = {}
    for line in text.splitlines():
        match = GLYPH.match(line)
        if match:
            code = int(match[1], 16)
            if code in glyphs:
                raise ValueError("Repeated glyph in font query")
            glyphs[code] = tuple(map(int, match.groups()[1:]))
    if not glyphs or len(glyphs) > 256:
        raise ValueError("Missing or unexpected glyph table")
    identity = re.search(r"^\s+FONT\s+(-[^\n]+)$", text, re.M)
    if identity is None:
        raise ValueError("Resolved FONT property is missing")
    return {
        "source": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "resolved_xlfd": identity[1].strip(),
        "glyph_count": len(glyphs),
        "samples": {sample: text_metrics(glyphs, sample) for sample in SAMPLES},
    }


def text_metrics(glyphs, text):
    if not text.isascii():
        raise ValueError("Unicode cannot be interpreted as HP-Roman8")
    advance = 0
    boxes = []
    for char in text:
        width, left, right, ascent, descent = glyphs[ord(char)]
        if char != " ":
            boxes.append((advance + left, -ascent, advance + right, descent))
        advance += width
    left = min(box[0] for box in boxes)
    top = min(box[1] for box in boxes)
    right = max(box[2] for box in boxes)
    bottom = max(box[3] for box in boxes)
    return {"advance": advance, "ink": [left, top, right-left, bottom-top]}


def compare(reference, measured, toolkit):
    output = []
    for row in measured["rows"]:
        differences = {}
        for sample in SAMPLES:
            native = reference["samples"][sample]
            current = row["samples"][sample]
            advance = current["logical"][2] if toolkit == "pango" else current["advance"]
            differences[sample] = {
                "advance_delta_px": advance - native["advance"],
                "ink_width_delta_px": current["ink"][2] - native["ink"][2],
                "ink_height_delta_px": current["ink"][3] - native["ink"][3],
            }
        average = sum(abs(d["advance_delta_px"]) for d in differences.values()) / len(SAMPLES)
        output.append({
            "requested": row["requested"], "absolute_px": row["absolute_px"],
            "resolved": row.get("resolved", row.get("resolved_family")),
            "mean_absolute_advance_delta_px": average, "differences": differences,
        })
    # Ranking is only a measurement aid, not a visual or licensing approval.
    return sorted(output, key=lambda row: row["mean_absolute_advance_delta_px"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swiss", type=Path, required=True)
    parser.add_argument("--prestige", type=Path, required=True)
    parser.add_argument("--pango", type=Path, required=True)
    parser.add_argument("--qt5", type=Path, required=True)
    parser.add_argument("--qt6", type=Path, required=True)
    args = parser.parse_args()
    references = {"swiss": read_x11(args.swiss), "prestige": read_x11(args.prestige)}
    measurements = {name: json.loads(getattr(args, name).read_text())
                    for name in ("pango", "qt5", "qt6")}
    result = {
        "scope": "ASCII text metrics only; not glyph equality or native widget equivalence",
        "references": references,
        "comparisons": {name: {toolkit: compare(reference, measured, toolkit)
                               for toolkit, measured in measurements.items()}
                        for name, reference in references.items()},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
