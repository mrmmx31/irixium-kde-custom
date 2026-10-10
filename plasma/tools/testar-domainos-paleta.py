#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify live palette changes against an approved, untouched DomainOS copy.

Uses private HOME/XDG directories, a disabled session bus and offscreen Qt.
Pass the extracted backup folder with --referencia; the backup is read only.
This verifies rendering and button feedback, without real desktop actions.
"""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
IDENTIFIER = "org.irixclassic.domainos.panel"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    return {str(p.relative_to(path)): digest(p) for p in sorted(path.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True, help="New or empty output directory")
    parser.add_argument("--referencia", type=Path, required=True, help="Extracted approved backup; never modified")
    args = parser.parse_args()
    output = args.saida.resolve()
    backup = args.referencia.resolve()
    frozen = backup / "repositorio/plasma/applets" / IDENTIFIER
    approved_file = backup / "prints/PAINEL-APROVADO.png"
    if not (frozen / "contents/ui/DomainOSPanel.qml").is_file() or not approved_file.is_file():
        parser.error("Reference must contain the frozen applet and prints/PAINEL-APROVADO.png")
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory must be new or empty")
    if output == backup or backup in output.parents:
        parser.error("Output must be outside the reference backup")
    output.mkdir(parents=True, exist_ok=True)
    production = REPO / "plasma/applets" / IDENTIFIER
    source_before = inventory(production)
    frozen_before = inventory(frozen)
    approved_hash = digest(approved_file)
    checks = {}
    warnings = []
    report = {"format": 1, "status": "failed", "checks": checks, "qml_diagnostics": warnings,
              "reference": str(backup), "reference_panel_sha256": approved_hash,
              "real_profiles_modified": False, "scope": "Private Qt application palettes; visual feedback only"}

    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    with tempfile.TemporaryDirectory(prefix="irix-domainos-palette-") as folder:
        private = Path(folder)
        for key, name in [("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                          ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")]:
            path = private / name
            path.mkdir(mode=0o700)
            os.environ[key] = str(path)
        for key in ("QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "QT_SCALE_FACTOR", "QT_SCREEN_SCALE_FACTORS",
                    "QT_FONT_DPI", "QT_AUTO_SCREEN_SCALE_FACTOR", "QT_ENABLE_HIGHDPI_SCALING",
                    "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "WAYLAND_DISPLAY", "DISPLAY", "KDE_SESSION_VERSION",
                    "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "LD_PRELOAD"):
            os.environ.pop(key, None)
        os.environ.update(QT_QUICK_BACKEND="software", QT_QPA_PLATFORM="offscreen",
                          QT_QPA_PLATFORMTHEME="generic", XDG_CURRENT_DESKTOP="NONE", QT_SCALE_FACTOR="1",
                          DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(private / "disabled-session-bus"),
                          DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(private / "disabled-system-bus"))
        # The approved capture used native Fontconfig without antialiasing.
        # Reproduce that preference privately; do not force a QFont strategy.
        fontconfig = private / "fonts.conf"
        fontconfig.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
                              '<fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
                              '<match target="font"><edit name="antialias" mode="assign"><bool>false</bool></edit></match>'
                              '</fontconfig>\n')
        os.environ["FONTCONFIG_FILE"] = str(fontconfig)
        from PyQt6 import sip
        from PyQt6.QtCore import QObject, QPointF, QRect, Qt, QUrl, qVersion, QMetaObject, Q_RETURN_ARG
        from PyQt6.QtGui import QColor, QFont, QFontInfo, QGuiApplication, QImage, QPainter, QPalette
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickItem, QQuickWindow
        from PyQt6.QtTest import QTest

        app = QGuiApplication([sys.argv[0]])
        engine = QQmlApplicationEngine()
        engine.warnings.connect(lambda messages: warnings.extend(m.toString() for m in messages))
        engine.setInitialProperties({"referenceUrl": QUrl.fromLocalFile(str(frozen / "contents/ui/DomainOSPanel.qml"))})
        engine.load(QUrl.fromLocalFile(str(REPO / "plasma/tests/DomainOSPalettePreview.qml")))
        require("palette_fixture_loaded", bool(engine.rootObjects()))
        window = sip.cast(engine.rootObjects()[0], QQuickWindow)

        def descendants(root):
            yield root
            for child in root.childItems():
                yield from descendants(child)

        panel = next(node for node in descendants(window.contentItem()) if node.objectName() == "domainosPaletteCandidate")
        loader = window.findChild(QObject, "domainosPaletteReferenceLoader")

        def candidate_item(name):
            node = next((n for n in descendants(panel) if n.objectName() == name), None)
            if node is None:
                raise AssertionError("Missing candidate item: " + name)
            return node

        def images():
            # Read enums in QML: PyQt does not register QQuickImageBase::Status.
            return json.loads(QMetaObject.invokeMethod(window, "imageInventory", Qt.ConnectionType.DirectConnection,
                                                       Q_RETURN_ARG("QVariant")))

        def settle():
            deadline = time.monotonic() + 5
            while True:
                app.processEvents()
                current = images()
                if window.property("referenceReady") and current and all(record["status"] == 1 for record in current.values()):
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("Images did not become ready: " + json.dumps(current, ensure_ascii=False))
                QTest.qWait(10)
            window.requestUpdate()
            QTest.qWait(60)
            app.processEvents()

        def normalized(image):
            return image.convertToFormat(QImage.Format.Format_RGBA8888)

        def panel_capture(filename=None, reference=False):
            settle()
            node = sip.cast(loader.property("item"), QQuickItem) if reference else panel
            origin = node.mapToScene(QPointF(0, 0)).toPoint()
            result = normalized(window.grabWindow().copy(QRect(origin.x(), origin.y(), round(node.width() * node.scale()), round(node.height() * node.scale()))))
            if filename:
                require("capture_" + filename, not result.isNull() and result.save(str(output / filename)))
            return result

        def geometry():
            return {node.objectName(): [node.x(), node.y(), node.width(), node.height()]
                    for node in descendants(panel) if node.objectName() and node is not panel}

        roles = ("background", "recessed", "dark", "shadow", "highlight", "pale", "blue", "white", "text", "black",
                 "green", "greenDark", "metalLight", "metalDark", "cyan", "cyanShadow", "lens", "label", "focus")

        def palette_colors():
            colors = panel.property("colorPalette")
            return {name: colors.property(name).name() for name in roles}

        def source_hashes(records):
            return {key: hashlib.sha256(value["url"].encode()).hexdigest() for key, value in records.items()}

        def application_palette(file):
            scheme = configparser.ConfigParser(interpolation=None)
            scheme.read(file)
            palette = QPalette(app.palette())
            mapping = {"Window": ("Window", "BackgroundNormal"), "WindowText": ("Window", "ForegroundNormal"),
                       "Base": ("View", "BackgroundNormal"), "Text": ("View", "ForegroundNormal"),
                       "AlternateBase": ("View", "BackgroundAlternate"), "Button": ("Button", "BackgroundNormal"),
                       "ButtonText": ("Button", "ForegroundNormal"), "Highlight": ("Selection", "BackgroundNormal"),
                       "HighlightedText": ("Selection", "ForegroundNormal")}
            for role, (group, entry) in mapping.items():
                value = scheme.get("Colors:" + group, entry, fallback=None)
                if value:
                    palette.setColor(getattr(QPalette.ColorRole, role), QColor(*(int(v) for v in value.split(",")[:3])))
            return palette

        def apply_palette(palette):
            app.setPalette(palette)
            settle()

        try:
            approved = normalized(QImage(str(approved_file)))
            frozen_image = panel_capture("REFERENCIA-CONGELADA.png", reference=True)
            original = panel_capture("CANDIDATO-REFERENCIA.png")
            require("approved_panel_dimensions", approved.size() == original.size() == frozen_image.size())
            require("frozen_reference_matches_approved_pixels", frozen_image == approved)
            require("candidate_reference_matches_approved_pixels", original == approved)
            baseline_geometry = geometry()
            fixed_sources = source_hashes(images())
            apply_palette(application_palette(REPO / "colors/DomainOS-SR10.4.colors"))
            require("reference_mode_ignores_application_palette", panel_capture() == original and source_hashes(images()) == fixed_sources)
            window.setProperty("followSystemColors", True)
            reference_system = panel_capture("CANDIDATO-DOMAINOS.png")
            # Live mode also assigns accent and text their semantic Qt roles;
            # only reference mode promises the historic RGB values everywhere.
            reference_roles = palette_colors()
            require("domainos_system_palette_matches_schema_roles", reference_roles["background"] == "#7894a7"
                    and reference_roles["recessed"] == "#607f91" and reference_roles["blue"] == "#3297c7"
                    and reference_roles["white"] == "#ffffff" and reference_roles["text"] == "#102b37")
            require("domainos_system_relief_keeps_reference_calibration", reference_roles["pale"] == "#a3d0e6"
                    and reference_roles["dark"] == "#194b63" and reference_roles["metalLight"] == "#c4d5ed"
                    and reference_roles["metalDark"] == "#3e536e")
            require("palette_connection_keeps_geometry", geometry() == baseline_geometry)
            records = images()
            require("multicolor_svg_sources_are_reactive_data_urls", any(record["svg"] for record in records.values())
                    and all(record["url"].startswith("data:image/svg+xml") for record in records.values() if record["svg"]))
            profiles = [("BREEZE-CLARO", Path("/usr/share/color-schemes/BreezeLight.colors")),
                        ("BREEZE-ESCURO", Path("/usr/share/color-schemes/BreezeDark.colors")),
                        ("IRIXIUM", REPO / "colors/Irixium.colors")]
            captures = [("Protótipo aprovado", approved), ("Conexão: DomainOS", reference_system)]
            profile_reports = {}
            last = reference_system
            for name, file in profiles:
                require(name + "_scheme_available", file.is_file())
                prior_sources = images()
                apply_palette(application_palette(file))
                image = panel_capture(name + ".png")
                current_sources = images()
                require(name + "_updates_without_recreating_panel", image != last)
                require(name + "_geometry_unchanged", geometry() == baseline_geometry)
                require(name + "_svg_sources_change_with_palette", any(record["url"] != prior_sources[key]["url"]
                        for key, record in current_sources.items() if record["svg"]))
                require(name + "_metal_and_emblem_sources_change_with_background", all(record["url"] != prior_sources[key]["url"]
                        for key, record in current_sources.items() if record["name"] in {"metal-lines.svg", "metal-weave.svg", "gnu-linux.svg"}))
                require(name + "_application_bitmaps_unchanged", all(record["url"] == prior_sources[key]["url"]
                        for key, record in current_sources.items() if not record["svg"]))
                font = candidate_item("domainosDateLettering").property("font")
                info = QFontInfo(font)
                require(name + "_courier_native_strike_preserved", font.family() == info.family() == "Adobe Courier"
                        and info.pixelSize() == 14 and info.exactMatch() and font.styleStrategy() == QFont.StyleStrategy.PreferDefault)
                captures.append((name, image))
                profile_reports[name] = {"scheme": str(file), "colors": palette_colors(),
                                         "image_sources_sha256": source_hashes(current_sources)}
                last = image
            report["profiles"] = profile_reports
            before_resize = source_hashes(images())
            window.setWidth(1537)
            window.setProperty("drawingScale", 0.75)
            panel_capture("REDIMENSIONADO.png")
            require("resize_does_not_rebuild_palette_images", source_hashes(images()) == before_resize)
            require("resize_keeps_canonical_geometry", geometry() == baseline_geometry)
            window.setProperty("drawingScale", 0.5)
            window.setWidth(1051)
            restored = panel_capture()
            require("resizing_back_restores_pixels", restored == last)
            for name in ("domainosDate", "domainosApplicationsDrawer", "domainosTray_network"):
                button = candidate_item(name)
                point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
                QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
                require(name + "_feedback_immediate", button.property("pressed"))
                held = panel_capture("PRESSIONADO-" + name + ".png")
                require(name + "_press_changes_rendered_pixels", held != restored)
                require(name + "_press_does_not_rebuild_palette_images", source_hashes(images()) == before_resize)
                QTest.mouseMove(window, QPointF(15, 15).toPoint())
                QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPointF(15, 15).toPoint())
                require(name + "_cancel_restores_pixels", not button.property("pressed") and panel_capture() == restored)
            # A second change after input proves the same live bindings survive.
            apply_palette(application_palette(REPO / "colors/DomainOS-SR10.4.colors"))
            require("return_to_domainos_restores_live_palette_pixels", panel_capture("RETORNO-DOMAINOS.png") == reference_system)
            window.setProperty("followSystemColors", False)
            require("return_to_reference_restores_approved_pixels", panel_capture("RETORNO-REFERENCIA.png") == approved)
            require("geometry_preserved_after_all_palette_and_input_changes", geometry() == baseline_geometry)
            composite = QImage(1011, len(captures) * 145 + 20, QImage.Format.Format_RGB32)
            composite.fill(QColor("#303030"))
            painter = QPainter(composite)
            painter.setPen(QColor("white"))
            for index, (label, image) in enumerate(captures):
                painter.drawText(20, 20 + index * 145, label)
                painter.drawImage(20, 30 + index * 145, image)
            painter.end()
            require("comparison_saved", composite.save(str(output / "COMPARACAO-PALETAS.png")))
            require("qml_diagnostics_zero", not warnings)
            require("production_source_unchanged", source_before == inventory(production))
            require("reference_backup_sources_unchanged", frozen_before == inventory(frozen) and approved_hash == digest(approved_file))
            report.update(status="passed", qt=qVersion(), geometry=baseline_geometry,
                          production_source_sha256=source_before, frozen_reference_source_sha256=frozen_before,
                          comparison=str(output / "COMPARACAO-PALETAS.png"))
        except Exception as error:
            report["error"] = str(error)
        finally:
            window.close()
            app.processEvents()
            (output / "RESULTADO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "checks": len(checks), "report": str(output / "RESULTADO.json"),
                          "error": report.get("error")}, ensure_ascii=False))
        return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
