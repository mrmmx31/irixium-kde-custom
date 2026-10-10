#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Record the complete standalone decoration package, rejecting symlinks."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
package = root / "package"
entries = {}
for path in sorted(package.rglob("*")):
    if path.is_symlink():
        raise ValueError(f"Symlink in standalone package: {path}")
    if path.is_file():
        entries[path.relative_to(package).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
version = json.loads((package / "metadata.json").read_text())["KPlugin"]["Version"]
(root / "MANIFEST.json").write_text(json.dumps({"version": version, "package": entries}, indent=2) + "\n")
