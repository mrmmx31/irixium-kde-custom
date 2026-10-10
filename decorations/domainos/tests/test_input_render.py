#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt input/rendering for the DomainOS surface; native KWin actions are tested separately."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from common import hashes, prepare, protected_paths, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--referencia", type=Path, help="Optional SR10.4 screenshot for pixel comparison")
    args = parser.parse_args()
    reference_path = args.referencia.expanduser().resolve() if args.referencia else None
    if reference_path is not None and not reference_path.is_file():
        parser.error("A imagem de referência informada não existe")
    protected = protected_paths(reference_path); before = hashes(protected)
    environment = prepare(args.saida)
    os.environ.clear(); os.environ.update(environment)
    from PyQt6.QtCore import QEvent, QPoint, QPointF, QRectF, QUrl, Qt
    from PyQt6.QtGui import QColor, QGuiApplication, QImage, QMouseEvent, QSurfaceFormat
    from PyQt6.QtQuick import QQuickItem, QQuickView
    from PyQt6.QtTest import QTest
    fmt = QSurfaceFormat(); fmt.setAlphaBufferSize(8); QSurfaceFormat.setDefaultFormat(fmt)
    app = QGuiApplication([])
    view = QQuickView(); view.setFlags(Qt.WindowType.FramelessWindowHint)
    view.setColor(QColor(Qt.GlobalColor.transparent))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    source = args.saida / "data/kwin/decorations/domainos_sr104/contents/ui/Surface.qml"
    view.setSource(QUrl.fromLocalFile(str(source)))
    if view.status() == QQuickView.Status.Error:
        raise RuntimeError([error.toString() for error in view.errors()])
    surface = view.rootObject(); view.resize(800, 400); view.show(); QTest.qWait(100)
    checks = []
    def check(name, passed, detail=None):
        row = {"check": name, "passed": bool(passed)}
        if detail is not None: row["detail"] = detail
        checks.append(row)
        if not passed: raise AssertionError(row)
    calls = []
    surface.menuRequested.connect(lambda button: calls.append("menu"))
    surface.closeRequested.connect(lambda: calls.append("close"))
    surface.minimizeRequested.connect(lambda: calls.append("minimize"))
    surface.maximizeRequested.connect(lambda button: calls.append("maximize"))
    buttons = {name: surface.findChild(QQuickItem, "domainos" + name) for name in ("Menu", "Minimize", "Maximize")}
    for name, button in buttons.items():
        check(name + " real input component present", button is not None)
    check("no separate close button", surface.findChild(QQuickItem, "domainosClose") is None)
    def point(button):
        return button.mapToScene(QPointF(button.width()/2, button.height()/2)).toPoint()
    def capture(name):
        return view.grabWindow().save(str(args.saida / name))
    interval = app.styleHints().mouseDoubleClickInterval()
    try:
        title = surface.findChild(QQuickItem, "domainosTitleRelief")
        check("passive title feedback component present", title is not None)
        title_position = point(title)
        title_rectangle = title.mapRectToScene(QRectF(0, 0, title.width(), title.height())).toRect()
        title_normal = view.grabWindow().copy(title_rectangle)
        calls.clear()
        QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, title_position)
        check("title immediately depressed with no window-button action", title.property("down") and not calls)
        QTest.qWait(30)
        title_held = view.grabWindow().copy(title_rectangle)
        check("title reverses relief while held", title_normal != title_held)
        check("title held screenshot", capture("title-held.png"))
        QTest.mouseMove(view, QPoint(400, 200))
        check("passive title feedback follows held pointer outside title", title.property("down") and not calls)
        QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(400, 200))
        QTest.qWait(30)
        check("title returns to original relief after release", not title.property("down")
              and not calls and view.grabWindow().copy(title_rectangle) == title_normal)
        QTest.mousePress(view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, title_position)
        check("right title press does not apply left-button feedback", not title.property("down"))
        QTest.mouseRelease(view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, title_position)
        for name in ("Minimize", "Maximize"):
            button = buttons[name]; position = point(button)
            calls.clear(); QTest.mouseMove(view, position); QTest.qWait(30)
            unpressed = view.grabWindow()
            QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
            check(name + " immediately depressed before action", button.property("down") and not calls)
            QTest.qWait(30)  # Renderer observation only; production has no animation delay.
            depressed = view.grabWindow()
            rectangle = button.mapRectToScene(QRectF(0, 0, button.width(), button.height())).toRect()
            check(name + " pressed relief changes pixels", unpressed.copy(rectangle) != depressed.copy(rectangle))
            check(name + " normal screenshot", unpressed.save(str(args.saida / (name.lower() + "-normal.png"))))
            check(name + " held screenshot", depressed.save(str(args.saida / (name.lower() + "-held.png"))))
            QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
            check(name + " one action on release, no retained relief", calls == [name.lower()] and not button.property("down"))
            calls.clear(); QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
            QTest.mouseMove(view, QPoint(400, 200)); QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(400, 200))
            check(name + " dragging out cancels action and relief", not calls and not button.property("down"))
            QTest.qWait(40)
        menu = buttons["Menu"]; position = point(menu)
        calls.clear(); QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
        check("menu immediately depressed without early popup", menu.property("down") and not calls)
        QTest.qWait(30); check("menu held screenshot", capture("menu-held.png"))
        QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
        check("menu single release removes relief immediately", not menu.property("down") and not calls)
        QTest.qWait(interval + 100)
        check("single menu click resolves at system double-click interval", calls == ["menu"])
        for first_active, second_active in ((True, True), (False, False), (False, True), (True, False)):
            calls.clear(); surface.setProperty("activeWindow", first_active)
            QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
            surface.setProperty("activeWindow", second_active); QTest.qWait(10)
            QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
            event = QMouseEvent(QEvent.Type.MouseButtonDblClick, QPointF(position), QPointF(view.mapToGlobal(position)),
                                Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QGuiApplication.sendEvent(view, event)
            check(f"double menu second press relief {first_active}/{second_active}", not calls and menu.property("down"))
            QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
            check(f"double menu closes once {first_active}/{second_active}", calls == ["close"] and not menu.property("down"))
            QTest.qWait(interval + 100)
            check(f"double menu has no delayed popup {first_active}/{second_active}", calls == ["close"])
        calls.clear(); QTest.mouseClick(view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, position)
        check("right menu click immediate", calls == ["menu"])
        for name, property_name in (("Minimize", "minimizeAllowed"), ("Maximize", "maximizeAllowed")):
            button = buttons[name]; position = point(button); calls.clear()
            surface.setProperty(property_name, False)
            check(name + " unavailable control is omitted", not button.isVisible() and not button.property("down") and not calls)
            surface.setProperty(property_name, True)
        # Resizing and maximizing are separate capabilities. A resizable
        # window without maximize keeps the thick frame; a fixed-size dialog
        # has the thin frame and no drawn corner grips, at both pixel scales.
        for scale in (1, 2):
            surface.setProperty("pixelScale", scale); view.resize(400*scale, 240*scale)
            surface.setProperty("maximizeAllowed", False)
            surface.setProperty("resizeAllowed", True); QTest.qWait(30)
            check("resizable without maximize retains thick inset " + str(scale), buttons["Menu"].x() == 10*scale)
            surface.setProperty("resizeAllowed", False); QTest.qWait(30)
            check("fixed-size dialog has thin title inset " + str(scale), buttons["Menu"].x() == 5*scale)
            check("dialog omits maximize " + str(scale), not buttons["Maximize"].isVisible())
            thin=view.grabWindow()
            check("fixed-size dialog screenshot " + str(scale), thin.save(str(args.saida / ("dialog-thin-"+str(scale)+".png"))))
            view.setColor(QColor("#ff00ff")); QTest.qWait(30)
            thin=view.grabWindow()
            check("thin client starts at measured 6px/25px inset " + str(scale),
                thin.pixelColor(6*scale,25*scale).name() == "#ff00ff"
                and thin.pixelColor(5*scale,25*scale).name() != "#ff00ff")
        surface.setProperty("resizeAllowed", True); surface.setProperty("maximizeAllowed", True)
        surface.setProperty("activeWindow", True); surface.setProperty("caption", "Help Index")
        for width, height, scale in ((380, 351, 1), (577, 346, 1), (101, 70, 1), (1400, 780, 1), (380, 351, 2)):
            surface.setProperty("pixelScale", scale); view.resize(width * scale, height * scale); QTest.qWait(50)
            # Qt's software grabWindow returns RGB32. Compare two composition
            # backgrounds to prove that every frame pixel is opaque, while the
            # application interior remains an unpainted transparent area.
            view.setColor(QColor("#ff00ff")); QTest.qWait(30)
            image = view.grabWindow().convertToFormat(QImage.Format.Format_RGBA8888)
            check(f"resize presents correct dimensions {width}/{height}/{scale}", image.width() == width*scale and image.height() == height*scale)
            border = 11 * scale; top = 30 * scale
            samples = [(x, y) for x in range(image.width()) for y in range(top)]
            samples += [(x, y) for y in range(top, image.height()) for x in list(range(border)) + list(range(image.width()-border, image.width()))]
            samples += [(x, y) for y in range(image.height()-border, image.height()) for x in range(image.width())]
            view.setColor(QColor("#00ff00")); QTest.qWait(30)
            other = view.grabWindow().convertToFormat(QImage.Format.Format_RGBA8888)
            check(f"entire decoration frame opaque after resize {width}/{height}/{scale}", all(image.pixelColor(x, y) == other.pixelColor(x, y) for x, y in samples))
            check(f"client interior left unpainted {width}/{height}/{scale}", image.pixelColor(image.width()//2, image.height()//2).name() == "#ff00ff" and other.pixelColor(other.width()//2, other.height()//2).name() == "#00ff00")
        view.setColor(QColor("#78a0d5"))
        surface.setProperty("pixelScale", 1); view.resize(380, 351); QTest.qWait(50)
        check("standalone active screenshot", capture("surface-active.png"))
        active = view.grabWindow()
        surface.setProperty("activeWindow", False); view.resize(577, 346); QTest.qWait(50)
        check("standalone inactive screenshot", capture("surface-inactive.png"))
        inactive = view.grabWindow()
        if reference_path is not None:
            reference = QImage(str(reference_path))
            if reference.isNull():
                raise RuntimeError("A referência informada não é uma imagem válida")
            comparisons = []
            for label, rendered, origin, regions in (
                    ("active", active, (629, 370), ((0, 0, 380, 10), (0, 10, 30, 20), (330, 10, 40, 20), (0, 30, 11, 310), (369, 30, 11, 310), (0, 340, 380, 11))),
                    ("inactive", inactive, (37, 372), ((0, 0, 577, 10), (0, 10, 30, 20), (527, 10, 40, 20), (0, 30, 11, 305), (566, 30, 11, 305), (0, 335, 577, 11)))):
                original = reference.copy(origin[0], origin[1], rendered.width(), rendered.height())
                for x, y, width, height in regions:
                    differing = sum(rendered.pixelColor(a, b).rgba() != original.pixelColor(a, b).rgba()
                                    for a in range(x, x+width) for b in range(y, y+height))
                    comparisons.append({"state": label, "region": [x, y, width, height], "different_pixels": differing,
                                        "pixels": width*height})
                original.save(str(args.saida / ("reference-" + label + ".png")))
            write_json(args.saida / "REFERENCE-PIXELS.json", {"reference": str(reference_path), "sha256": hashes([reference_path])[str(reference_path)],
                                                            "scope": "Reference frame/buttons only; caption and application client artwork excluded", "regions": comparisons})
            for sample in comparisons:
                check("reference pixels " + sample["state"] + " " + str(sample["region"]),
                      sample["different_pixels"] == 0, sample)
        surface.setProperty("activeWindow", True); surface.setProperty("maximizedWindow", True); view.resize(800, 400); QTest.qWait(50)
        check("standalone maximized screenshot", capture("surface-maximized.png"))
        check("maximized controls fit title", all(buttons[name].y() == 0 for name in buttons))
        check("no QML warnings", not warnings)
    except Exception as error:
        checks.append({"check": "test execution", "passed": False, "error": str(error)})
    finally:
        view.close(); app.processEvents()
        checks.append({"check": "personal configuration and Classic package unchanged", "passed": hashes(protected) == before})
        report = {"scope": "Production Surface.qml copied unchanged; actual Qt pointer events and framebuffer; no native KWin dispatch claimed",
                  "checks": checks, "warnings": warnings, "status": "passed" if all(c["passed"] for c in checks) else "failed"}
        write_json(args.saida / "RESULTADO.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
