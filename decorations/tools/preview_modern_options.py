#!/usr/bin/env python3
"""Render and exercise the packaged Aurorae variants without installing or touching KWin."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
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
    runtime_dirs = tempfile.TemporaryDirectory(prefix="irixium-decoration-preview-")
    for key, name in (("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")):
        path = Path(runtime_dirs.name) / name
        path.mkdir()
        os.environ[key] = str(path)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QPA_PLATFORMTHEME", "generic")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    from PyQt6.QtCore import QObject, QPoint, QUrl, Qt
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQuick import QQuickView
    from PyQt6.QtTest import QTest

    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName("IrixiumDecorationVariantsPreview")
    view = QQuickView()
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setSource(QUrl.fromLocalFile(str(ROOT / "tests/modern-options-preview.qml")))
    if view.status() == QQuickView.Status.Error:
        for error in view.errors():
            print(error.toString(), file=sys.stderr)
        return 1
    view.show()
    QTest.qWait(150)
    root = view.rootObject()
    checks = []

    def check(name, value):
        checks.append({"check": name, "passed": bool(value)})

    def point(surface, button):
        return QPoint(round(surface.property("x") + button.property("x") + button.property("width") / 2),
                      round(surface.property("y") + button.property("y") + button.property("height") / 2))

    for name in ("legacyActive", "legacyInactive", "legacyMaximized", "currentActive", "currentInactive", "currentMaximized"):
        surface = root.findChild(QObject, name)
        check(name + " frame artwork", surface is not None and surface.property("artworkValid"))
        if surface is None:
            continue
        buttons = [surface.findChild(QObject, "irixiumNative" + action) for action in ("Menu", "Minimize", "Maximize")]
        check(name + " exactly three controls", all(button is not None for button in buttons)
              and len([child for child in surface.children() if child.objectName().startswith("irixiumNative") and child.objectName() not in ("irixiumNativeFrame", "irixiumNativeCaption")]) == 3)
        for button in buttons:
            check(name + " " + button.objectName() + " artwork", button.property("artworkValid"))
        if name.endswith("Active"):
            menu, minimize, maximize = buttons
            p = point(surface, menu)
            count = root.property("menuCalls")
            QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p)
            check(name + " menu stays closed while pressed", root.property("menuCalls") == count)
            QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p)
            check(name + " menu opens once immediately on release", root.property("menuCalls") == count + 1)
            p = point(surface, minimize)
            count = root.property("minimizeCalls")
            QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p)
            check(name + " minimize pressed state", minimize.property("pressed") and minimize.property("renderedPrefix") == "pressed")
            check(name + " minimize waits for release", root.property("minimizeCalls") == count)
            QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p)
            check(name + " minimize action on release", root.property("minimizeCalls") == count + 1 and not minimize.property("pressed"))
            p = point(surface, maximize)
            for mouse in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
                count = root.property("maximizeCalls")
                QTest.mouseClick(view, mouse, Qt.KeyboardModifier.NoModifier, p)
                check(name + " maximize " + mouse.name, root.property("maximizeCalls") == count + 1 and root.property("maximizeButton") == mouse.value)
        if name == "currentInactive":
            count = root.property("minimizeCalls")
            QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point(surface, buttons[1]))
            check("disabled minimize has no action", root.property("minimizeCalls") == count)
        caption = surface.findChild(QObject, "irixiumNativeCaption")
        check(name + " caption never overlaps controls", caption.property("x") >= buttons[0].property("x") + buttons[0].property("width")
              and caption.property("x") + caption.property("width") <= buttons[1].property("x"))
    QTest.mouseMove(view, QPoint(500, 100))
    QTest.qWait(30)
    output.mkdir(parents=True)
    screenshot = view.grabWindow()
    check("standalone screenshot", not screenshot.isNull() and screenshot.save(str(output / "modern-options.png")))
    check("no QML warnings", not warnings)
    report = {"scope": "Actual package QML, KSvg and pointer input in an isolated QtQuick preview; not a live KWin integration test",
              "checks": checks, "warnings": warnings, "status": "passed" if all(c["passed"] for c in checks) else "failed"}
    (output / "modern-options.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    view.close()
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
