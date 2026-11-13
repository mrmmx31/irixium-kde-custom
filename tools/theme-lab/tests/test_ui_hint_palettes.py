"""Native Motif tooltip resources; schemes do not change the real desktop."""
import configparser
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
schemes = {
    "DomainOS": root / "colors/DomainOS-SR10.4.colors",
    "BreezeLight": Path("/usr/share/color-schemes/BreezeLight.colors"),
    "BreezeDark": Path("/usr/share/color-schemes/BreezeDark.colors"),
}
rows = []
file_dialog = len(sys.argv) > 2 and sys.argv[2] == "--file-dialog"
for name in (*schemes, "TestYellow"):
    if name == "TestYellow":
        # Artificial role fixture, never product colours or installed settings.
        face, text, view = "ecd870", "201c0c", "f3e6a4"
    else:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        if not schemes[name].is_file():
            raise SystemExit("Missing scheme fixture: " + str(schemes[name]))
        parser.read(schemes[name])
        values = parser["Colors:Window"]
        face, text = (
            "%02x%02x%02x" % tuple(map(int, values[key].split(",")))
            for key in ("BackgroundNormal", "ForegroundNormal")
        )
        view = "%02x%02x%02x" % tuple(map(int, parser["Colors:View"]["BackgroundNormal"].split(",")))
    result = subprocess.run(
        [sys.argv[1]], text=True, capture_output=True, timeout=30,
        env={**os.environ, "TL_FILE_HINTS_ONLY" if file_dialog else "TL_HINTS_ONLY": "1", "TL_HINT_FACE": face,
             "TL_HINT_TEXT": text, "TL_HINT_VIEW": view, "LC_ALL": "C.UTF-8"},
    )
    rows.append({"scheme": name, "terminal": result.returncode,
                 "stdout": result.stdout, "stderr": result.stderr})
    if result.returncode:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        raise SystemExit(result.returncode)
scope = (
    "export comparison dialog: read-only UTF-8, native select/copy and blocked cut/paste/undo/redo, dynamic UI roles, button and WM close/reopen, project field preserved; four initial schemes; not full export dispatch or historical glyph fidelity"
    if os.environ.get("TL_EXPORT_REVIEW_ONLY") else
    "SpinBox painted-arrow hover: cold delay, bounds, no overlap, stability, live source roles, dismissal, native increment/decrement/repeat and no late hint; four initial UI schemes; disabled field/painted-arrow hints with blocked clicks and unchanged value; not all layouts"
    if os.environ.get("TL_SPIN_HINT_HOVER") else
    "dynamic hints for five scrollbar pieces and both size axes in all recipe families: native child resources, visibility, sensitivity, inheritance and unchanged model; four initial UI schemes; not hover or adapters"
    if os.environ.get("TL_DYNAMIC_HINTS") else
    "five enabled project-history buttons: cold delay, native hover, bounds, no overlap, stability and leave; disabled Undo delayed bridge, bounds/non-overlap, stability, blocked click and leave; four initial UI role schemes and preview isolation; not history dispatch or all layouts"
    if os.environ.get("TL_HISTORY_HOVER") else
    "file dialog hints, editing popup hints and runtime palette/Undo/Redo, four initial schemes; not glyph fidelity or End navigation"
    if file_dialog else
    "tooltip and help menu/text UI face/content/text roles; FontSet resources; preview palette isolation, four schemes; not rendered glyph/pixel fidelity"
)
print(json.dumps({"status": "passed", "scope": scope, "rows": rows},
                 ensure_ascii=False, indent=2))
