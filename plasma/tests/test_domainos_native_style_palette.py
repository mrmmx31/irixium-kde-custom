#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render production SVGs through native KSvg and real Plasma popup headings.

Each color scheme runs in a private XDG profile and private D-Bus process,
with an external timeout. No desktop, PulseAudio, notifications or user profile
is contacted. The headings are the component actually used by Volume and
Notifications; the labels and control values are synthetic.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
STYLE = ROOT / "plasma/IrixClassicDomainOS"
FIXTURE = ROOT / "plasma/tests/DomainOSNativeStylePalettePreview.qml"
SCHEMES = {
    "current_roles": dict(Window="#c1c1c1", View="#9ebfbf", Button="#999999", Header="#c1c1c1",
        Tooltip="#c1c1c1", Selection="#78a0a0", Text="#000000", HighlightedText="#000000"),
    "dark": dict(Window="#26211b", View="#17130e", Button="#4e4233", Header="#342b23",
        Tooltip="#41352a", Selection="#ddb541", Text="#f2dfb3", HighlightedText="#23170e"),
    "yellow": dict(Window="#ddd377", View="#66540e", Button="#b39a33", Header="#e7c957",
        Tooltip="#f4dfab", Selection="#762853", Text="#1b1707", HighlightedText="#fff0df"),
    "strong_roles": dict(Window="#d6e0bd", View="#cfdac8", Button="#b9cfad", Header="#dbc59a",
        Tooltip="#e6d9bb", Selection="#a92662", Text="#173610", HighlightedText="#faeeee"),
}


def scheme_config(colors):
    lines = ["[General]", "ColorScheme=DomainOSPrivateTest", "[KDE]", "contrast=7"]
    def rgb(value):
        return ",".join(str(int(value[i:i+2], 16)) for i in (1, 3, 5))
    for section in ("Window", "View", "Button", "Header", "Tooltip", "Selection", "Complementary"):
        background = colors.get(section, "#1609da")
        foreground = colors["HighlightedText"] if section == "Selection" else colors["Text"]
        lines += ["[Colors:"+section+"]", "BackgroundNormal="+rgb(background),
            "BackgroundAlternate="+rgb(background), "ForegroundNormal="+rgb(foreground),
            "ForegroundInactive="+rgb(foreground), "DecorationFocus="+rgb(colors["Selection"]),
            "DecorationHover="+rgb(colors["Selection"]), "ForegroundPositive=40,130,60",
            "ForegroundNegative=200,20,60", "ForegroundNeutral=130,110,40"]
    lines += ["[ColorEffects:Inactive]", "Enable=false", "[ColorEffects:Disabled]", "Enable=false"]
    return "\n".join(lines)+"\n"


def worker(case):
    if os.environ.get("DOMAINOS_PRIVATE_STYLE_PALETTE") != "1":
        raise RuntimeError("Use the private native style launcher")
    from PyQt6.QtCore import QCoreApplication, QEvent, QPointF, QUrl, qInstallMessageHandler
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
    from PyQt6.QtQuick import QQuickItem
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtWidgets import QApplication
    app = QApplication([sys.argv[0]])
    colors = SCHEMES[case]
    def apply_palette(values):
        palette = app.palette()
        for role, key in {"Window":"Window", "Base":"View", "AlternateBase":"View", "Button":"Button",
                "WindowText":"Text", "Text":"Text", "ButtonText":"Text", "ToolTipBase":"Tooltip",
                "ToolTipText":"Text", "Highlight":"Selection", "HighlightedText":"HighlightedText"}.items():
            palette.setColor(getattr(QPalette.ColorRole, role), QColor(values[key]))
        app.setPalette(palette)
    apply_palette(colors)
    # A plain QQmlEngine has no C++ Applet context. Supply only the read-only
    # form factor used by installed BackgroundMetrics, without configuration,
    # actions or session access. Heading/KSvg/Controls themselves are native.
    context = Path(os.environ['TMPDIR'])/'PrivatePlasmoidContext.qml'
    context.write_text('pragma Singleton\nimport QtQuick\nimport org.kde.plasma.core as PC\nQtObject { readonly property int formFactor: PC.Types.Planar }\n')
    qmlRegisterSingletonType(QUrl.fromLocalFile(str(context)), 'org.kde.plasma.plasmoid', 1, 0, 'Plasmoid')
    messages = []
    qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(FIXTURE)))
    assert engine.rootObjects(), "Native style fixture did not load: "+str(messages)
    window = engine.rootObjects()[0]
    deadline = time.monotonic()+3
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    image = window.grabWindow()
    assert not image.isNull(), "Native render is empty"
    checks = {}
    samples = {}
    def find(name, item=None):
        item = item or window.contentItem()
        if item.objectName() == name:
            return item
        for child in item.childItems():
            found = find(name, child)
            if found is not None:
                return found
        return None
    def sample(item, point=None):
        p = item.mapToScene(point or QPointF(item.width()/2, item.height()/2))
        result = image.pixelColor(round(p.x()), round(p.y()))
        return result.name(), result.alpha()
    for name, role in (("button","Button"),("lineedit","View"),("sliderHighlight","Selection"),
                      ("switchActive","Selection"),("rawHeader","Header"),("rawFooter","Window"),
                      ("tooltip","Tooltip"),("viewSelected","Selection")):
        item = find("nativeFrame_"+name)
        assert item is not None, name
        actual, alpha = sample(item)
        samples[name] = actual
        checks[name+"_matches_selected_role"] = actual == colors[role]
        checks[name+"_surface_opaque"] = alpha == 255
    for name, role in (("nativeVolumeHeader","Header"),("nativeVolumeFooter","Window"),
                      ("nativeNotificationsHeader","Header"),("nativeNotificationsFooter","Window")):
        heading = find(name)
        assert heading is not None, name
        background = heading.property("background")
        actual, alpha = sample(background, QPointF(background.width()-20, background.height()/2))
        samples[name] = actual
        checks[name+"_matches_selected_role"] = actual == colors[role]
        checks[name+"_opaque_visible"] = alpha == 255 and background.isVisible()
    checks["native_header_text_role"] = window.property("headerThemeText").name() == colors["Text"]
    checks["native_footer_text_role"] = window.property("footerThemeText").name() == colors["Text"]
    checks["native_header_theme_role"] = window.property("headerThemeBackground").name() == colors["Header"]
    checks["native_footer_theme_role"] = window.property("footerThemeBackground").name() == colors["Window"]
    for name in ("nativeVolumeSlider", "nativeVolumeSwitch", "nativeVolumeButton"):
        checks[name+"_native_loaded"] = find(name) is not None
    checks["native_slider_value_unchanged"] = abs(find("nativeVolumeSlider").property("value")-.65) < .001
    # Native QSvg accepts every generated file. A previously installed style
    # is an optional *comparison*, never a dependency on a personal profile.
    # Absence is declared as skipped, not counted as preserved legacy bounds.
    old_style = Path(os.environ["DOMAINOS_INSTALLED_STYLE_REFERENCE"])
    reference_available = old_style.is_dir()
    reference = {"status":"checked" if reference_available else "skipped",
                 "reason":"installed style resource comparison" if reference_available else "no installed artwork reference available"}
    if reference_available:
        metadata_path = old_style/'metadata.json'
        reference['metadata_sha256'] = hashlib.sha256(metadata_path.read_bytes()).hexdigest() if metadata_path.is_file() else None
        reference['svg_sha256'] = {str(p.relative_to(old_style)):hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted(old_style.rglob('*.svg')) if p.is_file()}
    compared = 0
    for path in sorted(STYLE.rglob("*.svg")):
        renderer = QSvgRenderer(str(path))
        assert renderer.isValid(), str(path)
        for element in ET.parse(path).getroot().iter():
            identifier = element.get('id', '')
            if identifier and renderer.elementExists(identifier):
                bounds = renderer.boundsOnElement(identifier)
                assert all(math.isfinite(value) for value in (bounds.x(), bounds.y(), bounds.width(), bounds.height())), "Nonfinite native ID bounds: "+identifier
        old_file = old_style / path.relative_to(STYLE)
        if reference_available and old_file.exists():
            old = QSvgRenderer(str(old_file))
            for element in ET.parse(old_file).getroot().iter():
                identifier = element.get("id", "")
                if identifier and identifier != "current-color-scheme" and old.elementExists(identifier):
                    assert renderer.elementExists(identifier), "Lost native ID: "+identifier
                    assert renderer.boundsOnElement(identifier) == old.boundsOnElement(identifier), "Changed native bounds: "+identifier
                    compared += 1
    checks["all_generated_svgs_native_valid"] = True
    checks["all_current_native_id_bounds_finite"] = True
    if reference_available:
        checks["installed_artwork_native_ids_bounds_preserved"] = compared > 500
    reference['compared_native_bounds'] = compared
    output = Path(os.environ["DOMAINOS_PRIVATE_STYLE_OUTPUT"])
    image.save(str(output / (case+".png")))
    # Standard ApplicationPaletteChange causes KSvg to reparse its selected
    # KColorScheme and invalidate the native render cache. Exercise that exact
    # update in the private profile, retaining this window and QQmlEngine.
    next_case = {"current_roles":"strong_roles", "dark":"yellow", "yellow":"dark", "strong_roles":"current_roles"}[case]
    next_colors = SCHEMES[next_case]
    (Path(os.environ["XDG_CONFIG_HOME"])/"kdeglobals").write_text(scheme_config(next_colors))
    apply_palette(next_colors)
    QCoreApplication.sendEvent(app, QEvent(QEvent.Type.ApplicationPaletteChange))
    deadline = time.monotonic()+1.5
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    image = window.grabWindow()
    assert not image.isNull(), "Native live palette render is empty"
    for name, role in (("button","Button"),("lineedit","View"),("sliderHighlight","Selection"),
                      ("switchActive","Selection"),("rawHeader","Header"),("rawFooter","Window"),
                      ("tooltip","Tooltip"),("viewSelected","Selection")):
        actual, alpha = sample(find("nativeFrame_"+name))
        samples["live_"+name] = actual
        checks["live_"+name+"_changed_without_engine_reload"] = actual == next_colors[role] and alpha == 255
    for name, role in (("nativeVolumeHeader","Header"),("nativeVolumeFooter","Window"),
                      ("nativeNotificationsHeader","Header"),("nativeNotificationsFooter","Window")):
        background = find(name).property("background")
        actual, alpha = sample(background, QPointF(background.width()-20, background.height()/2))
        samples["live_"+name] = actual
        checks["live_"+name+"_changed_without_engine_reload"] = actual == next_colors[role] and alpha == 255
    checks["live_header_foreground_role"] = window.property("headerThemeText").name() == next_colors["Text"]
    checks["live_footer_foreground_role"] = window.property("footerThemeText").name() == next_colors["Text"]
    errors = [message for message in messages if any(part in message for part in
        ("TypeError", "ReferenceError", "Binding loop", "is not a type", "Cannot assign", "Error loading"))]
    checks["no_qml_errors_or_binding_loops"] = not errors
    image.save(str(output / (case+"-live-to-"+next_case+".png")))
    report = dict(pass_=all(checks.values()), case=case, checks=checks, samples=samples,
        compared_native_bounds=compared, geometry_reference=reference, errors=errors, private_scheme=colors, live_next_scheme=next_colors)
    (output / (case+".json")).write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report))
    window.close()
    return 0 if report["pass_"] else 1


class NativeStylePalette(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = Path(os.environ.get("DOMAINOS_NATIVE_STYLE_OUTPUT", "/tmp/irix-domainos-native-style-palette-20261009"))
        cls.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    def test_all_functional_paints_have_semantic_roles_or_partial_shades(self):
        count = 0
        for path in sorted(STYLE.rglob("*.svg")):
            tree = ET.parse(path).getroot()
            ids = [el.get("id") for el in tree.iter() if el.get("id")]
            self.assertEqual(len(ids), len(set(ids)), str(path))
            self.assertEqual(ids.count("current-color-scheme"), 1, str(path))
            self.assertFalse(any(re.search(r"#[0-9a-fA-F]{3,8}\b", el.text or "") for el in tree.iter() if el.tag.endswith("style")), str(path))
            for element in tree.iter():
                self.assertNotIn(element.tag.rsplit("}",1)[-1], ("linearGradient","radialGradient","filter","animate","animateTransform"))
                for paint in ("fill", "stroke"):
                    value = element.get(paint)
                    if value and value not in ("none", "currentColor"):
                        self.assertIn(value, ("#ffffff", "#000000"), (path, value))
                        self.assertIn(element.get("data-scheme-shade"), ("lighten", "darken"), (path, value))
                        self.assertGreater(float(element.get("opacity", "1")), 0)
                        self.assertLess(float(element.get("opacity", "1")), .55)
                if any(element.get(paint) == "currentColor" for paint in ("fill", "stroke")):
                    self.assertRegex(element.get("class", ""), r"^ColorScheme-[A-Z][a-zA-Z]+$")
                count += 1
        self.assertGreater(count, 10000)
        self.assertFalse((STYLE / "colors").exists(), "A style-local colors file overrides the user's KDE schema")
        expected = json.loads((STYLE / "CLASSIC-BASELINE.json").read_text())
        actual = {str(p.relative_to(STYLE.parent/"IrixClassic")):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (STYLE.parent/"IrixClassic").rglob("*") if p.is_file()}
        self.assertEqual(expected, actual)

    def run_scheme(self, case, missing_reference=False):
        with tempfile.TemporaryDirectory(prefix=".qa-native-style-palette-", dir=ROOT) as temporary:
            private = Path(temporary)
            env = dict(os.environ)
            for key in ("XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_STATE_HOME","XDG_RUNTIME_DIR","TMPDIR"):
                directory = private / key.lower()
                directory.mkdir(mode=0o700)
                env[key] = str(directory)
            for key in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS",
                        "DBUS_STARTER_BUS_TYPE","SESSION_MANAGER","LD_PRELOAD","QT_STYLE_OVERRIDE",
                        "QT_QPA_PLATFORMTHEME","QML_IMPORT_PATH","QML2_IMPORT_PATH","XAUTHORITY"):
                env.pop(key, None)
            env.update(QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software", QT_QUICK_CONTROLS_STYLE="org.kde.desktop",
                QT_SCALE_FACTOR="1", QML_DISABLE_DISK_CACHE="1", QT_QPA_PLATFORMTHEME="generic", XDG_CURRENT_DESKTOP="NONE",
                DOMAINOS_PRIVATE_STYLE_PALETTE="1", DOMAINOS_PRIVATE_STYLE_OUTPUT=str(self.output),
                DOMAINOS_INSTALLED_STYLE_REFERENCE=str(Path.home()/".local/share/plasma/desktoptheme/IrixClassicDomainOS"),
                DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(private/"disabled-system-bus"))
            if missing_reference:
                env['DOMAINOS_INSTALLED_STYLE_REFERENCE'] = str(private/'absent-reference')
                fresh_output = self.output/'missing-reference'
                fresh_output.mkdir(mode=0o700, exist_ok=True)
                env['DOMAINOS_PRIVATE_STYLE_OUTPUT'] = str(fresh_output)
            shutil.copytree(STYLE, Path(env["XDG_DATA_HOME"])/"plasma/desktoptheme/IrixClassicDomainOS")
            config = Path(env["XDG_CONFIG_HOME"])
            (config / "plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
            (config / "kdeglobals").write_text(scheme_config(SCHEMES[case]))
            bus = private / "private-bus.conf"
            bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>'
                '<policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
            process = subprocess.Popen(["dbus-run-session","--config-file",str(bus),"--",sys.executable,"-B",str(Path(__file__).resolve()),"--worker",case],
                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            try:
                stdout, stderr = process.communicate(timeout=18)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate(timeout=5)
                self.fail("Native style worker exceeded 18 seconds: "+case+"\n"+stdout+stderr)
            self.assertEqual(process.returncode, 0, case+" failed:\n"+stdout+stderr)
            report = json.loads(stdout.strip().splitlines()[-1])
            self.assertTrue(report["pass_"])
            if missing_reference:
                self.assertEqual(report['geometry_reference']['status'], 'skipped')
                self.assertEqual(report['compared_native_bounds'], 0)
                self.assertNotIn('installed_artwork_native_ids_bounds_preserved', report['checks'])
    def test_current_roles(self): self.run_scheme("current_roles")
    def test_dark(self): self.run_scheme("dark")
    def test_yellow(self): self.run_scheme("yellow")
    def test_strong_distinct_roles(self): self.run_scheme("strong_roles")
    def test_missing_reference_is_explicitly_skipped(self): self.run_scheme("current_roles", missing_reference=True)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        sys.exit(worker(sys.argv[2]))
    unittest.main()
