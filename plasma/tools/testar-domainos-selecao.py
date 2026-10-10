#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise prototype pager/iconbox selection with real, isolated Qt mouse input.

Reads the current user's color settings only. Private HOME/XDG/Fontconfig and
disabled D-Bus addresses prevent desktop effects. No real workspace or window
is activated. Screenshots cover four KDE palettes and private yellow stress cases.
"""
import argparse
import configparser
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
IDENTIFIER = "org.irixclassic.domainos.panel"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def inventory(path):
    return {str(p.relative_to(path)): digest(p) for p in sorted(path.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True, help="New or empty output directory")
    args = parser.parse_args()
    output = args.saida.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    production = REPO / "plasma/applets" / IDENTIFIER
    source_before = inventory(production)
    real_config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    protected = [real_config / name for name in ("kdeglobals", "plasmarc", "kwinrc", "kcmfonts",
                                                 "plasma-org.kde.plasma.desktop-appletsrc")]
    config_before = {str(path): digest(path) for path in protected}
    profiles = [("ATUAL-LSI", real_config / "kdeglobals"),
                ("DOMAINOS", REPO / "colors/DomainOS-SR10.4.colors"),
                ("BREEZE-CLARO", Path("/usr/share/color-schemes/BreezeLight.colors")),
                ("BREEZE-ESCURO", Path("/usr/share/color-schemes/BreezeDark.colors"))]
    synthetic = [("AMARELO-COLISAO", "#dddd28", "#dddd28"),
                 ("AMARELO-PASTEL", "#ffff99", "#fff4bb"),
                 ("AMARELO-OURO", "#c8ac20", "#e2c84a"),
                 ("AMARELO-ESCURO", "#332c07", "#1c1803")]
    synthetic_dir = output / "esquemas-fixture"
    synthetic_dir.mkdir()
    for name, background, base in synthetic:
        scheme = configparser.ConfigParser(interpolation=None)
        scheme.optionxform = str
        scheme.read(REPO / "colors/DomainOS-SR10.4.colors")
        def rgb(color):
            return ",".join(str(int(color[index:index + 2], 16)) for index in (1, 3, 5))
        scheme.set("Colors:Window", "BackgroundNormal", rgb(background))
        scheme.set("Colors:View", "BackgroundNormal", rgb(base))
        scheme.set("Colors:Button", "BackgroundNormal", rgb(background))
        scheme.set("Colors:Window", "ForegroundNormal", "255,255,255" if name == "AMARELO-ESCURO" else "16,43,55")
        file = synthetic_dir / (name + ".colors")
        with file.open("w") as stream:
            scheme.write(stream)
        profiles.append((name, file))
    protected_profiles = {name for name, _, _ in synthetic if name != "AMARELO-ESCURO"}
    checks, warnings, captures = {}, [], []
    report = {"format": 1, "status": "failed", "checks": checks, "qml_diagnostics": warnings,
              "desktop_modified": False, "profiles": {},
              "scope": "Real Qt input switches prototype samples only; no desktop, task or device actions",
              "synthetic_schemes_scope": str(synthetic_dir)}

    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    with tempfile.TemporaryDirectory(prefix="irix-domainos-selection-") as folder:
        private = Path(folder)
        for key, name in [("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                          ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")]:
            path = private / name
            path.mkdir(mode=0o700)
            os.environ[key] = str(path)
        for key in ("QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "QT_SCALE_FACTOR", "QT_SCREEN_SCALE_FACTORS",
                    "QT_FONT_DPI", "QT_AUTO_SCREEN_SCALE_FACTOR", "QT_ENABLE_HIGHDPI_SCALING", "QML_IMPORT_PATH",
                    "QML2_IMPORT_PATH", "WAYLAND_DISPLAY", "DISPLAY", "KDE_SESSION_VERSION", "LD_PRELOAD",
                    "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE"):
            os.environ.pop(key, None)
        os.environ.update(QT_QUICK_BACKEND="software", QT_QPA_PLATFORM="offscreen",
                          QT_QPA_PLATFORMTHEME="generic", XDG_CURRENT_DESKTOP="NONE", QT_SCALE_FACTOR="1",
                          DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(private / "disabled-session-bus"),
                          DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(private / "disabled-system-bus"))
        fontconfig = private / "fonts.conf"
        fontconfig.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
                              '<fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
                              '<match target="font"><edit name="antialias" mode="assign"><bool>false</bool></edit></match>'
                              '</fontconfig>\n')
        os.environ["FONTCONFIG_FILE"] = str(fontconfig)
        from PyQt6 import sip
        from PyQt6.QtCore import QPoint, QPointF, QRect, Qt, QUrl, qVersion, QMetaObject, Q_RETURN_ARG
        from PyQt6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPalette
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickWindow
        from PyQt6.QtTest import QTest

        app = QGuiApplication([sys.argv[0]])
        engine = QQmlApplicationEngine()
        engine.warnings.connect(lambda messages: warnings.extend(m.toString() for m in messages))
        engine.load(QUrl.fromLocalFile(str(REPO / "plasma/tests/DomainOSSelectionPreview.qml")))
        require("selection_fixture_loaded", bool(engine.rootObjects()))
        window = sip.cast(engine.rootObjects()[0], QQuickWindow)

        def descendants(root):
            yield root
            for child in root.childItems():
                yield from descendants(child)

        panel = next(n for n in descendants(window.contentItem()) if n.objectName() == "domainosSelectionCandidate")

        def item(name):
            result = next((n for n in descendants(panel) if n.objectName() == name), None)
            if result is None:
                raise AssertionError("Missing item: " + name)
            return result

        def images():
            return json.loads(QMetaObject.invokeMethod(window, "imageInventory", Qt.ConnectionType.DirectConnection,
                                                       Q_RETURN_ARG("QVariant")))

        def settle():
            deadline = time.monotonic() + 5
            while True:
                app.processEvents()
                records = images()
                if records and all(record["status"] == 1 for record in records.values()):
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("Images did not become ready")
                QTest.qWait(10)
            window.requestUpdate()
            QTest.qWait(30)
            app.processEvents()

        def capture(filename=None):
            settle()
            origin = panel.mapToScene(QPointF(0, 0)).toPoint()
            image = window.grabWindow().copy(QRect(origin.x(), origin.y(), 971, 109))
            image = image.convertToFormat(QImage.Format.Format_RGBA8888)
            if filename:
                require("capture_" + filename, not image.isNull() and image.save(str(output / filename)))
            return image

        def geometry():
            return {n.objectName(): [n.x(), n.y(), n.width(), n.height()] for n in descendants(panel) if n.objectName()}

        def sources():
            return {key: hashlib.sha256(record["url"].encode()).hexdigest() for key, record in images().items()}

        def point(node, x=None, y=None):
            return node.mapToScene(QPointF(node.width() / 2 if x is None else x,
                                          node.height() / 2 if y is None else y)).toPoint()

        def image_point(node, x, y):
            pos = node.mapToScene(QPointF(x, y)) - panel.mapToScene(QPointF(0, 0))
            return round(pos.x()), round(pos.y())

        def color_at(image, node, x, y):
            px, py = image_point(node, x, y)
            return image.pixelColor(px, py).name()

        def color_property(node, name):
            value = node.property(name)
            return value.name() if isinstance(value, QColor) else str(value)

        def luminance(color):
            def linear(value):
                value /= 255
                return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            value = QColor(color)
            return sum(weight * linear(channel) for weight, channel in
                       zip((0.2126, 0.7152, 0.0722), (value.red(), value.green(), value.blue())))

        def contrast(first, second):
            light, dark = sorted((luminance(first), luminance(second)), reverse=True)
            return (light + 0.05) / (dark + 0.05)

        def ink_colors(image, node):
            left, top = image_point(node, 0, 0)
            right, bottom = image_point(node, node.width(), node.height())
            counts = {}
            for py in range(top, bottom):
                for px in range(left, right):
                    color = image.pixelColor(px, py).name()
                    counts[color] = counts.get(color, 0) + 1
            return counts

        def selected_appearance(button_name, title_name, text_name, image, palette, label):
            button, title, text = item(button_name), item(title_name), item(text_name)
            highlight = palette.highlight().color().name()
            foreground = palette.highlightedText().color().name()
            require(label + "_selected_title_uses_native_highlight", color_property(title, "color") == highlight
                    or color_property(title, "face") == highlight)
            require(label + "_selected_text_uses_native_highlighted_text", color_property(text, "color") == foreground)
            counts = ink_colors(image, title)
            require(label + "_selected_title_highlight_rendered", counts.get(highlight, 0) > 30)
            require(label + "_selected_title_text_rendered", counts.get(foreground, 0) > 1)
            # Respect native scheme colors. Breeze's own selection text does
            # not promise a universal contrast ratio; do not invent new colors.
            require(label + "_selected_title_has_native_pixel_contrast", contrast(highlight, foreground) > 1)
            relief = item(button_name + "Relief")
            require(label + "_selection_keeps_sunken_relief", relief.property("sunken") and not button.property("pressed"))
            # The two physical relief bands persist after release; the separate
            # inset contrast rim is one physical pixel at this drawing scale.
            colors = panel.property("colorPalette")
            dark, shadow = colors.property("dark").name(), colors.property("shadow").name()
            require(label + "_sunken_first_pixel_band", color_at(image, button, button.width() / 2, 0) == dark)
            require(label + "_sunken_second_pixel_band", color_at(image, button, button.width() / 2, 2) == shadow)
            return {"text_contrast": round(contrast(highlight, foreground), 3),
                    "title_pixel_counts": {highlight: counts.get(highlight, 0), foreground: counts.get(foreground, 0)}}

        def unselected_appearance(button_name, title_name, text_name, image, regular_role, label):
            button, title, text = item(button_name), item(title_name), item(text_name)
            colors = panel.property("colorPalette")
            normal = colors.property(regular_role).name()
            foreground = colors.property("text").name()
            require(label + "_former_selection_raised", not button.property("selected")
                    and not item(button_name + "Relief").property("sunken"))
            require(label + "_former_title_color_restored", color_property(title, "color") == normal
                    or color_property(title, "face") == normal)
            require(label + "_former_text_color_restored", color_property(text, "color") == foreground)
            counts = ink_colors(image, title)
            require(label + "_former_title_pixels_restored", counts.get(normal, 0) > 30
                    and counts.get(foreground, 0) > 1)

        def pager_appearance(name, image, label, held=False):
            workspace = item("domainosDesk" + name)
            button = item("domainosWorkspace_" + name)
            title = item("domainosWorkspaceTitle_" + name)
            text = item("domainosWorkspaceTitleText_" + name)
            marker = item("domainosWorkspaceMarker_" + name)
            rim = item("domainosWorkspaceSelection_" + name)
            colors = panel.property("colorPalette")
            lamp = workspace.property("lampColor").name()
            background, foreground = colors.property("background").name(), colors.property("text").name()
            recessed = colors.property("recessed").name()
            normal_lamp, pressed_lamp = colors.property("pagerLight").name(), colors.property("pagerPressedLight").name()
            protected = bool(colors.property("pagerContrastProtected"))
            require(label + "_lamp_matches_semantic_palette_role", lamp == (pressed_lamp if held else normal_lamp))
            if protected:
                require(label + "_yellow_protection_keeps_lamp_visible_on_window", contrast(lamp, background) >= 3)
                require(label + "_yellow_protection_keeps_lamp_visible_on_base", contrast(lamp, recessed) >= 3)
            else:
                require(label + "_yellow_lamp_preserves_original_color", normal_lamp == "#dddd28")
                require(label + "_unprotected_pressed_lamp_preserves_original_glow",
                        pressed_lamp == QColor("#dddd28").lighter(125).name())
            require(label + "_marker_light_rendered", color_at(image, marker, marker.width() / 2, marker.height() / 2) == lamp)
            require(label + "_selected_outer_ring_visible", rim.isVisible() and workspace.property("lit"))
            require(label + "_outer_ring_has_original_extent", rim.x() == rim.y() == 0
                    and rim.width() == workspace.width() and rim.height() == workspace.height())
            for edge, x, y in [("top", rim.width() / 2, 0), ("left", 0, rim.height() / 2),
                               ("bottom", rim.width() / 2, rim.height() - 2), ("right", rim.width() - 2, rim.height() / 2)]:
                require(label + "_outer_ring_" + edge + "_is_yellow", color_at(image, rim, x, y) == lamp)
            require(label + "_title_keeps_normal_background", color_property(title, "color") == background)
            require(label + "_title_keeps_normal_text", color_property(text, "color") == foreground)
            counts = ink_colors(image, title)
            require(label + "_normal_title_pixels_rendered", counts.get(background, 0) > 30 and counts.get(foreground, 0) > 1)
            depressed = held and not workspace.property("selected")
            require(label + "_pager_relief_matches_transient_press", item("domainosWorkspace_" + name + "Relief").property("sunken") == depressed)
            require(label + "_pager_offset_matches_transient_press", button.property("pressOffset") == (2 if depressed else 0))
            return {"lamp": lamp, "lamp_background_contrast": round(contrast(lamp, background), 3),
                    "lamp_base_contrast": round(contrast(lamp, recessed), 3),
                    "pressed_lamp": pressed_lamp,
                    "pressed_background_contrast": round(contrast(pressed_lamp, background), 3),
                    "pressed_base_contrast": round(contrast(pressed_lamp, recessed), 3),
                    "contrast_protected": protected,
                    "normal_title_text_contrast": round(contrast(background, foreground), 3),
                    "body_sunken": bool(depressed), "body_offset": 2 if depressed else 0}

        def pager_coordinates():
            names = ("Work", "Procrastination")
            result = {}
            for name in names:
                root = item("domainosDesk" + name)
                for node in descendants(root):
                    if node.objectName():
                        pos = node.mapToScene(QPointF(0, 0))
                        result[node.objectName()] = [pos.x(), pos.y(), node.width(), node.height()]
            return result

        def same_except_pager_lights(before, after, names):
            # The original thin full outer ring covers two physical rows at
            # 50% scale. Only that perimeter and the tiny lamp may change.
            masks = []
            for name in names:
                workspace = item("domainosDesk" + name)
                left, top = image_point(workspace, 0, 0)
                right, bottom = image_point(workspace, workspace.width(), workspace.height())
                masks.extend([(left, top, right, top + 2), (left, bottom - 2, right, bottom),
                              (left, top, left + 2, bottom), (right - 2, top, right, bottom)])
                marker = item("domainosWorkspaceMarker_" + name)
                p1 = marker.mapToScene(QPointF(0, 0)) - panel.mapToScene(QPointF(0, 0))
                p2 = marker.mapToScene(QPointF(marker.width(), marker.height())) - panel.mapToScene(QPointF(0, 0))
                masks.append((math.floor(p1.x()), math.floor(p1.y()), math.ceil(p2.x()), math.ceil(p2.y())))
            for py in range(before.height()):
                for px in range(before.width()):
                    if before.pixel(px, py) != after.pixel(px, py) and not any(
                            left <= px < right and top <= py < bottom for left, top, right, bottom in masks):
                        return False
            return True

        def held_pager_body(name, before_image, held_image, before_coordinates, label):
            workspace = item("domainosDesk" + name)
            current = pager_coordinates()
            if workspace.property("selected"):
                require(label + "_selected_held_body_coordinates_fixed", current == before_coordinates)
                require(label + "_selected_held_changes_only_lamp_and_ring", same_except_pager_lights(
                                                        before_image, held_image, (name,)))
            else:
                # A fresh choice depresses by two canonical units (one physical
                # pixel here). Its title, text, lamp and map all move together.
                shift = panel.property("drawingScale") * 2
                for prefix in ("domainosWorkspaceTitle_", "domainosWorkspaceTitleText_",
                               "domainosWorkspaceMarker_", "domainosWorkspaceMap_"):
                    node_name = prefix + name
                    before, after = before_coordinates[node_name], current[node_name]
                    require(label + "_unselected_press_moves_" + prefix.rstrip("_"),
                            abs(after[0] - before[0] - shift) < 1e-6
                            and abs(after[1] - before[1] - shift) < 1e-6 and after[2:] == before[2:])
                require(label + "_unselected_press_changes_body_pixels", held_image != before_image
                        and not same_except_pager_lights(before_image, held_image, (name,)))

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

        def select(button_name, state_name, new_index, label):
            node = item(button_name)
            previous = panel.property(state_name)
            pager = button_name.startswith("domainosWorkspace_")
            if pager:
                previous_image = capture()
                previous_coordinates = pager_coordinates()
            QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point(node))
            require(label + "_feedback_immediate", node.property("pressed"))
            require(label + "_selection_waits_for_release", panel.property(state_name) == previous)
            if pager:
                depressed = not node.property("selected")
                require(label + "_relief_immediate_on_press", item(button_name + "Relief").property("sunken") == depressed)
                require(label + "_offset_immediate_on_press", node.property("pressOffset") == (2 if depressed else 0))
                held = capture(label + "-PRESSIONADO.png")
                pager_appearance(button_name.split("_", 1)[1], held, label + "_held", held=True)
                held_pager_body(button_name.split("_", 1)[1], previous_image, held, previous_coordinates, label)
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point(node))
            require(label + "_release_selects", panel.property(state_name) == new_index)
            require(label + "_release_clears_pressed", not node.property("pressed"))
            if pager:
                require(label + "_release_immediately_restores_raised_relief", not item(button_name + "Relief").property("sunken"))
                require(label + "_release_immediately_restores_zero_offset", node.property("pressOffset") == 0)
            released = capture()
            if pager:
                require(label + "_selected_body_coordinates_fixed", pager_coordinates() == previous_coordinates)
                require(label + "_selection_changes_only_lamp_and_ring", same_except_pager_lights(previous_image,
                                                                                            released, ("Work", "Procrastination")))
            return released

        def cancel(button_name, state_name, label):
            node = item(button_name)
            previous = panel.property(state_name)
            previous_image = capture()
            pager = button_name.startswith("domainosWorkspace_")
            if pager:
                previous_coordinates = pager_coordinates()
            QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point(node))
            require(label + "_feedback_immediate", node.property("pressed"))
            held = capture()
            require(label + "_pressed_changes_pixels", held != previous_image)
            require(label + "_held_preserves_selection", panel.property(state_name) == previous)
            if pager:
                pager_name = button_name.split("_", 1)[1]
                pager_appearance(pager_name, held, label + "_held", held=True)
                held_pager_body(pager_name, previous_image, held, previous_coordinates, label)
            QTest.mouseMove(window, QPoint(15, 15))
            require(label + "_outside_clears_pressed", not node.property("pressed"))
            if pager:
                require(label + "_outside_restores_raised_relief", not item(button_name + "Relief").property("sunken"))
                require(label + "_outside_restores_body_offset", node.property("pressOffset") == 0)
                require(label + "_outside_restores_body_coordinates", pager_coordinates() == previous_coordinates)
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(15, 15))
            require(label + "_cancel_preserves_selection", panel.property(state_name) == previous)
            require(label + "_cancel_restores_pixels", capture() == previous_image)

        try:
            settle()
            baseline_geometry = geometry()
            actual_lsi_image = None
            for name, file in profiles:
                require(name + "_scheme_available", file.is_file())
                palette = application_palette(file)
                app.setPalette(palette)
                settle()
                colors = panel.property("colorPalette")
                contrast_protected = bool(colors.property("pagerContrastProtected"))
                require(name + "_protection_active_only_for_yellow_collision", contrast_protected == (name in protected_profiles))
                if name not in protected_profiles:
                    require(name + "_approved_yellow_preserved", colors.property("pagerLight").name() == "#dddd28")
                fixed_sources = sources()
                select("domainosWorkspace_Work", "selectedWorkspaceIndex", 0, name + "_pager_work")
                require(name + "_work_exclusive", item("domainosDeskWork").property("selected")
                        and not item("domainosDeskProcrastination").property("selected"))
                work = capture(name + "-WORK.png")
                work_appearance = pager_appearance("Work", work, name + "_work")
                work_again = select("domainosWorkspace_Work", "selectedWorkspaceIndex", 0, name + "_pager_work_again")
                require(name + "_already_selected_work_release_preserves_pixels", work_again == work)
                select("domainosWorkspace_Procrastination", "selectedWorkspaceIndex", 1, name + "_pager_procrastination")
                require(name + "_procrastination_exclusive", item("domainosDeskProcrastination").property("selected")
                        and not item("domainosDeskWork").property("selected"))
                procrastination = capture(name + "-PROCRASTINATION.png")
                procrastination_appearance = pager_appearance("Procrastination", procrastination, name + "_procrastination")
                procrastination_again = select("domainosWorkspace_Procrastination", "selectedWorkspaceIndex", 1,
                                                name + "_pager_procrastination_again")
                require(name + "_already_selected_procrastination_release_preserves_pixels", procrastination_again == procrastination)
                unselected_appearance("domainosWorkspace_Work", "domainosWorkspaceTitle_Work",
                            "domainosWorkspaceTitleText_Work", procrastination, "background", name + "_work")
                selected_rim = item("domainosWorkspaceSelection_Procrastination")
                former_rim = item("domainosWorkspaceSelection_Work")
                require(name + "_workspace_rim_follows_selection", selected_rim.isVisible() and not former_rim.isVisible())
                require(name + "_former_workspace_marker_unlit", color_property(item("domainosWorkspaceMarker_Work"), "color")
                        == panel.property("colorPalette").property("recessed").name())
                if name == "ATUAL-LSI":
                    actual_lsi_image = procrastination
                require(name + "_pager_selection_changes_pixels", work != procrastination)
                cancel("domainosWorkspace_Work", "selectedWorkspaceIndex", name + "_pager_cancel")
                cancel("domainosWorkspace_Procrastination", "selectedWorkspaceIndex", name + "_pager_selected_cancel")
                # All seven task samples must be reachable, and exactly one selected.
                for index in range(7):
                    select("domainosTask_" + str(index), "selectedTaskIndex", index, name + "_task_" + str(index))
                    require(name + "_task_" + str(index) + "_exclusive",
                            [i for i in range(7) if item("domainosTask_" + str(i)).property("selected")] == [index])
                cancel("domainosTask_0", "selectedTaskIndex", name + "_iconbox_cancel")
                select("domainosTask_0", "selectedTaskIndex", 0, name + "_iconbox_desk")
                desk = capture(name + "-ICONBOX-DESK.png")
                desk_appearance = selected_appearance("domainosTask_0", "domainosTaskLabel_0",
                            "domainosTaskLabelText_0", desk, palette, name + "_desk")
                select("domainosTask_2", "selectedTaskIndex", 2, name + "_iconbox_winterm")
                winterm = capture(name + "-ICONBOX-WINTERM.png")
                winterm_appearance = selected_appearance("domainosTask_2", "domainosTaskLabel_2",
                            "domainosTaskLabelText_2", winterm, palette, name + "_winterm")
                unselected_appearance("domainosTask_0", "domainosTaskLabel_0", "domainosTaskLabelText_0",
                                      winterm, "label", name + "_desk")
                require(name + "_iconbox_selection_changes_pixels", desk != winterm)
                require(name + "_selection_preserves_geometry", geometry() == baseline_geometry)
                require(name + "_selection_does_not_rebuild_assets", sources() == fixed_sources)
                captures.extend([(name + " — Work", work), (name + " — Procrastination", procrastination),
                                 (name + " — Iconbox: Desk", desk), (name + " — Iconbox: winterm", winterm)])
                report["profiles"][name] = {"scheme": str(file), "highlight": palette.highlight().color().name(),
                                            "highlighted_text": palette.highlightedText().color().name(),
                                            "contrast_protected": contrast_protected,
                                            "appearance": {"work": work_appearance, "procrastination": procrastination_appearance,
                                                           "desk": desk_appearance, "winterm": winterm_appearance},
                                            "image_sources_sha256": fixed_sources}
            # Leave final test state equal to the fixture's default selection.
            select("domainosWorkspace_Procrastination", "selectedWorkspaceIndex", 1, "final_pager")
            select("domainosTask_0", "selectedTaskIndex", 0, "final_iconbox")
            # A yellow application palette cannot recolor reference mode. Back
            # in live mode, switching to lsi must restore the exact old yellow.
            app.setPalette(application_palette(synthetic_dir / "AMARELO-COLISAO.colors"))
            settle()
            panel.setProperty("followSystemColors", False)
            frozen_palette = capture("REFERENCIA-SOB-ESQUEMA-AMARELO.png")
            colors = panel.property("colorPalette")
            require("reference_mode_keeps_original_yellow", colors.property("pagerLight").name() == "#dddd28"
                    and not colors.property("pagerContrastProtected"))
            pager_appearance("Procrastination", frozen_palette, "reference_mode")
            panel.setProperty("followSystemColors", True)
            capture()
            require("yellow_palette_reactivates_contrast_protection", colors.property("pagerContrastProtected"))
            app.setPalette(application_palette(real_config / "kdeglobals"))
            restored = capture("RETORNO-AMARELO-PARA-LSI.png")
            require("return_from_yellow_restores_original_lamp", colors.property("pagerLight").name() == "#dddd28"
                    and not colors.property("pagerContrastProtected"))
            require("return_from_yellow_restores_lsi_pixels", restored == actual_lsi_image)
            # Only an explicitly enabled preview can change prototype indices.
            # The installed applet still waits for the user's functional design.
            before_disabled = capture()
            panel.setProperty("simulateSelection", False)
            select("domainosWorkspace_Work", "selectedWorkspaceIndex", 1, "simulation_disabled_pager")
            select("domainosTask_2", "selectedTaskIndex", 0, "simulation_disabled_iconbox")
            require("simulation_disabled_preserves_pixels", capture() == before_disabled)
            require("qml_diagnostics_zero", not warnings)
            require("production_source_unchanged", source_before == inventory(production))
            require("real_desktop_preferences_unchanged", config_before == {str(path): digest(path) for path in protected})
            def comparison(filename, rows):
                composite = QImage(1011, len(rows) * 145 + 20, QImage.Format.Format_RGB32)
                composite.fill(QColor("#303030"))
                painter = QPainter(composite)
                painter.setPen(QColor("white"))
                for index, (label, image) in enumerate(rows):
                    painter.drawText(20, 20 + index * 145, label)
                    painter.drawImage(20, 30 + index * 145, image)
                painter.end()
                require("comparison_saved_" + filename, composite.save(str(output / filename)))
            comparison("COMPARACAO-SELECOES.png", captures)
            comparison("COMPARACAO-PAGER.png", [(label, image) for label, image in captures if "Iconbox:" not in label])
            comparison("COMPARACAO-ICONBOX.png", [(label, image) for label, image in captures if "Iconbox:" in label])
            report.update(status="passed", qt=qVersion(), geometry=baseline_geometry,
                          production_source_sha256=source_before, protected_config_sha256=config_before,
                          comparison=str(output / "COMPARACAO-SELECOES.png"))
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
