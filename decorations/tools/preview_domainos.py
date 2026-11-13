#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Preview the actual DomainOS SR10.4 KDecoration package without applying it."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parents[1] / "domainos/tests"
sys.path.insert(0, str(TESTS))
from common import hashes, prepare, protected_paths, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--interativo", action="store_true", help="Keep the native preview window open until closed")
    parser.add_argument("--referencia", type=Path, help="Optional SR10.4 screenshot for comparison; never downloaded")
    args = parser.parse_args()
    reference = args.referencia.expanduser().resolve() if args.referencia else None
    if reference is not None and not reference.is_file():
        parser.error("A imagem de referência informada não existe")
    paths = protected_paths(reference)
    before = hashes(paths)
    original_display = os.environ.get("DISPLAY")
    environment = prepare(args.saida, graphical=args.interativo)
    if args.interativo:
        if not original_display:
            parser.error("Interactive gallery needs an existing display; it does not alter that session's decoration")
        environment["DISPLAY"] = original_display
        if os.environ.get("XAUTHORITY"):
            environment["XAUTHORITY"] = os.environ["XAUTHORITY"]
    os.environ.clear(); os.environ.update(environment)
    from PyQt6.QtCore import QObject, QUrl
    from PyQt6.QtGui import QColor, QImage, QPainter
    from PyQt6.QtQuick import QQuickView
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    app.setApplicationName("DomainOSDecorationPreview")
    view = QQuickView()
    warnings = []
    view.engine().warnings.connect(lambda values: warnings.extend(e.toString() for e in values))
    view.setSource(QUrl.fromLocalFile(str(TESTS / "native-preview.qml")))
    if view.status() == QQuickView.Status.Error:
        raise RuntimeError([e.toString() for e in view.errors()])
    view.setTitle("DomainOS SR10.4 — decoração isolada, sem aplicar")
    view.show(); QTest.qWait(250)
    root = view.rootObject()
    checks = []
    def check(label, result):
        checks.append({"check": label, "passed": bool(result)})
    check("actual native KDecoration clients ready", root.property("ready"))
    for name in ("nativeDomainOSPrimary", "nativeDomainOSSecondary"):
        item = root.findChild(QObject, name)
        check(name + " decoration exists", item is not None and item.property("decoration") is not None)
    for active, maximized, filename in ((True, False, "native-active.png"), (False, False, "native-inactive.png"),
                                      (True, True, "native-maximized.png")):
        root.setProperty("activeState", active); root.setProperty("maximizedState", maximized)
        QTest.qWait(80)
        check(filename + " saved", view.grabWindow().save(str(args.saida / filename)))
    root.setProperty("activeState", True); root.setProperty("maximizedState", False); QTest.qWait(50)
    if reference is not None:
        image = QImage(str(reference))
        if image.isNull():
            raise RuntimeError("A referência informada não é uma imagem válida")
        crop_active = image.copy(629, 370, 380, 31)
        crop_inactive = image.copy(37, 372, 577, 31)
        rendered = view.grabWindow()
        comparison = QImage(1000, 800, QImage.Format.Format_RGB32)
        comparison.fill(QColor("#263a4d"))
        painter = QPainter(comparison); painter.setPen(QColor("white"))
        painter.drawText(16, 22, "Referência fornecida: DomainOS SR10.4 (recortes intactos em escala 1:1)")
        painter.drawImage(16, 35, crop_active); painter.drawImage(414, 35, crop_inactive)
        painter.drawText(16, 90, "Decoração real no preview nativo KDecoration3: ativa e inativa")
        painter.drawImage(0, 112, rendered); painter.end()
        check("reference and native comparison saved", comparison.save(str(args.saida / "reference-native-comparison.png")))
    check("no QML warnings", not warnings)
    if args.interativo:
        app.exec()
    view.close(); app.processEvents()
    check("personal configuration and Classic package unchanged", hashes(paths) == before)
    report = {"scope": "Actual Aurorae main.qml in KDecoration3 native preview; private HOME/XDG; no application to live KWin",
              "checks": checks, "warnings": warnings,
              "status": "passed" if all(c["passed"] for c in checks) else "failed"}
    write_json(args.saida / "RESULTADO.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
