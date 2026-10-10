#!/usr/bin/env python3
"""Load all three actual decoration packages in KDE's native preview, entirely under /tmp."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    args = parser.parse_args()
    output = args.saida.absolute()
    if output.exists() or ROOT.parent in output.parents:
        parser.error("A saída deve ser uma pasta nova fora do clone.")
    runtime_dirs = tempfile.TemporaryDirectory(prefix="irixium-native-preview-")
    runtime = Path(runtime_dirs.name)
    for key, name in (("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")):
        path = runtime / name
        path.mkdir()
        os.environ[key] = str(path)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QPA_PLATFORMTHEME", "generic")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    for slug, plugin_id in (("modern", "irixium_modern"), ("modern-13", "irixium_modern_13"), ("modern-41", "irixium_modern_41")):
        shutil.copytree(ROOT / slug / "package", runtime / "data/kwin/decorations" / plugin_id)
    from PyQt6.QtCore import QObject, QUrl
    from PyQt6.QtQuick import QQuickView
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv[:1])
    app.setApplicationName("IrixiumNativeDecorationPreview")
    view = QQuickView()
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setSource(QUrl.fromLocalFile(str(ROOT / "tests/native-kwin-preview.qml")))
    if view.status() == QQuickView.Status.Error:
        for error in view.errors():
            print(error.toString(), file=sys.stderr)
        return 1
    view.show()
    QTest.qWait(200)
    root = view.rootObject()
    checks = []

    def check(name, value):
        checks.append({"check": name, "passed": bool(value)})

    check("native KDecoration preview clients ready", root.property("decorationsReady"))
    for name in ("nativeModern", "nativeLegacy", "nativeCurrent"):
        item = root.findChild(QObject, name)
        check(name + " actual decoration created", item is not None and item.property("decoration") is not None)
    output.mkdir(parents=True)
    for active, maximized, filename in ((True, False, "active.png"), (False, False, "inactive.png"), (True, True, "maximized.png")):
        root.setProperty("windowActive", active)
        root.setProperty("windowMaximized", maximized)
        QTest.qWait(50)
        screenshot = view.grabWindow()
        check(filename + " native screenshot", not screenshot.isNull() and screenshot.save(str(output / filename)))
    check("no QML warnings in actual main.qml packages", not warnings)
    report = {"scope": "Actual main.qml packages loaded by org.kde.kwin.aurorae through KDecoration3 preview; temporary XDG roots; no live session changes",
              "checks": checks, "warnings": warnings, "status": "passed" if all(c["passed"] for c in checks) else "failed"}
    (output / "native-preview.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    view.close()
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
