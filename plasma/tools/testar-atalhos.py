#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the real launcher configuration page in an isolated Plasma host.

Uses native KOpenWithDialog selection/cancellation and the real cfg_* page.
The fixture models Plasma's Apply/Cancel transfer; it does not exercise the
complete Plasma KConfigDialog. HOME, XDG paths, D-Bus and X11 are private. No
application is launched. Optional test dependencies match testar-widgets.py.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "plasma/applets/org.irixclassic.quicklaunch"

FIXTURE_QML = r'''
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root
    objectName: "classicLauncherConfigurationFixture"
    preferredRepresentation: fullRepresentation
    width: 520
    height: 520
    Layout.minimumWidth: 520
    Layout.minimumHeight: 520
    Layout.preferredWidth: 520
    Layout.preferredHeight: 520
    property string phase: "loading"
    property var checks: []
    property int failed: 0
    property var original: []
    property var beforeSelector: []
    property var beforeRace: []
    property string testReportJson: JSON.stringify({checks: checks, failed: failed, phase: phase})

    ConfigLaunchers {
        id: editor
        anchors.fill: parent
    }

    function equal(actual, expected) { return JSON.stringify(actual) === JSON.stringify(expected); }
    function record(name, success) {
        checks = checks.concat([{name: name, passed: !!success}]);
        if (!success) failed += 1;
    }
    function button(item, name) {
        if (item.objectName === name) return item;
        for (let i = 0; i < item.children.length; ++i) {
            const found = button(item.children[i], name);
            if (found) return found;
        }
        return null;
    }
    function click(name) {
        const target = button(editor, name);
        if (!target || !target.enabled) throw new Error("Button missing/disabled: " + name);
        target.clicked();
    }
    function saved() { return Array.prototype.slice.call(plasmoid.configuration.launcherUrls); }
    function runListCases() {
        try {
            original = saved();
            editor.cfg_launcherUrls = original.slice();
            // The generic platform's Fusion theme chooses its own font. Set
            // 12pt only on fixture controls to test this required footprint;
            // production ConfigLaunchers contains no font override.
            const controls = ["classicLauncherAdd", "classicLauncherReplace", "classicLauncherRemove", "classicLauncherUp", "classicLauncherDown"];
            for (const name of controls) button(editor, name).font.pointSize = 12;
            editor.selectedIndex = -1;
            record("no selection disables replacement", !button(editor, "classicLauncherReplace").enabled);
            record("no selection cannot remove a row", !editor.removeSelected() && equal(editor.copiedUrls(), original));
            record("no selection cannot request replacement", editor.requestLauncher(true) === null);
            editor.selectedIndex = 1;
            click("classicLauncherUp");
            record("Up button moves selected token", equal(editor.copiedUrls(), [original[1], original[0], original[2]]));
            record("Up keeps selection on moved row", editor.selectedIndex === 0);
            record("first row disables Up", !button(editor, "classicLauncherUp").enabled);
            click("classicLauncherDown");
            record("Down button restores exact original tokens", equal(editor.copiedUrls(), original));
            record("edits have not written applet config", equal(saved(), original));
            click("classicLauncherRemove");
            record("Remove affects only selected row", equal(editor.copiedUrls(), [original[0], original[2]]));
            record("Remove keeps applet config intact", equal(saved(), original));
            // This is the cfg_* transfer used when a page is discarded/reopened.
            editor.cfg_launcherUrls = saved();
            record("Cancel reload restores exact saved tokens", equal(editor.copiedUrls(), original));
            editor.selectedIndex = editor.cfg_launcherUrls.length - 1;
            record("last row disables Down", !button(editor, "classicLauncherDown").enabled);
            record("out of bounds cannot reorder", !editor.moveSelected(1) && equal(editor.copiedUrls(), original));
            editor.selectedIndex = 1;
            beforeSelector = editor.copiedUrls();
            click("classicLauncherReplace");
            phase = "selector_cancel";
        } catch (error) { record(String(error), false); phase = "failed"; }
    }
    function afterSelectorCancel() {
        record("cancel native selector preserves list", equal(editor.copiedUrls(), beforeSelector));
        record("cancel native selector preserves applet config", equal(saved(), original));
        click("classicLauncherAdd");
        phase = "selector_add";
    }
    function afterSelectorAdd() {
        const urls = editor.copiedUrls();
        record("native Add appends selected application", urls.length === 4 && urls[3] === FIXTURE_EXTRA);
        record("native Add preserves every existing token", equal(urls.slice(0, 3), original));
        record("native Add remains unapplied", equal(saved(), original));
        editor.selectedIndex = 1;
        click("classicLauncherReplace");
        phase = "selector_replace";
    }
    function afterSelectorReplace() {
        const expected = [original[0], FIXTURE_FILES, original[2], FIXTURE_EXTRA];
        record("native Replace keeps exact row position", equal(editor.copiedUrls(), expected));
        record("native Replace remains unapplied", equal(saved(), original));
        // Same named cfg_* value assignment performed by the Plasma host on Apply.
        plasmoid.configuration.launcherUrls = editor.copiedUrls();
        record("Apply transfers exact current order", equal(saved(), expected));
        editor.selectedIndex = 0;
        click("classicLauncherRemove");
        editor.cfg_launcherUrls = saved();
        record("Cancel after Apply preserves previously applied list", equal(editor.copiedUrls(), expected));
        editor.selectedIndex = 0;
        click("classicLauncherReplace");
        editor.moveSelected(1);
        beforeRace = editor.copiedUrls();
        phase = "selector_race";
    }
    function afterSelectorRace() {
        record("nonmodal replacement refuses stale row", equal(editor.copiedUrls(), beforeRace));
        record("stale row is explained", editor.selectionMessage.length > 0);
        record("stale selector never changes saved config", equal(saved(), [original[0], FIXTURE_FILES, original[2], FIXTURE_EXTRA]));
        editor.cfg_launcherUrls = saved();
        editor.selectedIndex = 0;
        const controls = ["classicLauncherAdd", "classicLauncherReplace", "classicLauncherRemove", "classicLauncherUp", "classicLauncherDown"];
        record("five buttons fit 520px page", controls.every(function(name) {
            const control = button(editor, name);
            return control.width > 0 && control.x >= 0 && control.x + control.width <= control.parent.width + 0.5;
        }));
        record("native configuration page has requested width", root.width >= 520 && editor.width >= 520);
        record("configuration buttons use 12pt fixture font", controls.every(function(name) {
            return button(editor, name).font.pointSize === 12;
        }));
        phase = "done";
    }
    Component.onCompleted: Qt.callLater(runListCases)
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args()
    output = args.saida.resolve() if args.saida else Path(tempfile.mkdtemp(prefix="irixclassic-launcher-config-"))
    if output.exists() and any(output.iterdir()):
        parser.error("Output must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    for program in ("c++", "pkg-config", "xvfb-run", "dbus-run-session", "plasmawindowed", "kbuildsycoca6"):
        if not shutil.which(program): parser.error("Optional native test dependency missing: " + program)
    paths = {key: output / "fixture" / key for key in ("home", "data", "config", "cache", "state", "runtime")}
    for path in paths.values(): path.mkdir(parents=True)
    paths["runtime"].chmod(0o700)
    before = {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(SOURCE.rglob("*")) if path.is_file()}
    package = paths["data"] / "plasma/plasmoids/org.irixclassic.quicklaunch"
    shutil.copytree(SOURCE, package)
    desktop_root = paths["data"] / "applications"
    desktop_root.mkdir()
    entries = (("editor", "IRIX Fixture Editor"), ("dolphin", "IRIX Fixture Dolphin"), ("files", "IRIX Fixture Files"),
               ("terminal", "IRIX Fixture Terminal"), ("extra", "IRIX Fixture Extra"))
    desktop_files = {}
    for identifier, name in entries:
        filename = "org.irixclassic.fixture.Terminal % test.desktop" if identifier == "terminal" else "org.irixclassic.fixture." + identifier + ".desktop"
        desktop = desktop_root / filename
        desktop.write_text("[Desktop Entry]\nType=Application\nName=" + name + "\nExec=/bin/false\nIcon=folder\nCategories=Utility;\n")
        desktop_files[identifier] = desktop
    from urllib.parse import quote
    original = ["applications:org.irixclassic.fixture.editor.desktop",
                desktop_files["dolphin"].as_uri(), "applications:" + quote(desktop_files["terminal"].name, safe="")]
    qml = FIXTURE_QML.replace("FIXTURE_EXTRA", json.dumps(desktop_files["extra"].as_uri())).replace(
        "FIXTURE_FILES", json.dumps(desktop_files["files"].as_uri()))
    (package / "contents/ui/main.qml").write_text(qml)
    # Set only the disposable fixture default. Real source/user config is untouched.
    config = package / "contents/config/main.xml"
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location("irix_native_widget_fixture", REPO / "plasma/tools/testar-widgets.py")
    module = module_from_spec(spec); spec.loader.exec_module(module)
    module.set_fixture_default(config, "launcherUrls", original)
    (paths["config"] / "kdeglobals").write_text((REPO / "colors/Irixium.colors").read_text()
        .replace("[General]", "[General]\nfont=Nimbus Sans,12,-1,5,50,0,0,0,0,0"))
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Test"], text=True))
    helper = output / "capture-config.so"
    helper_source = REPO / "plasma/tests/capture-quicklaunch-config.cpp"
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(helper_source), "-o", str(helper), *flags, "-ldl"], check=True)
    env = module.environment(paths)
    env.update({"HOME": str(paths["home"]), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "QT_QUICK_CONTROLS_STYLE": "Fusion",
                "DBUS_SYSTEM_BUS_ADDRESS": "unix:path=" + str(paths["runtime"] / "no-system-bus")})
    bus_config = output / "private-bus.conf"
    module.private_bus_config(bus_config)
    launcher = output / "run.py"
    launcher.write_text("import os,subprocess\nsubprocess.run(['kbuildsycoca6','--noincremental'],check=True)\n"
        + "env=os.environ.copy()\nenv.update(" + repr({"LD_PRELOAD": str(helper),
        "IRIX_CONFIG_REPORT": str(output / "PAGE.json"), "IRIX_CONFIG_CAPTURE": str(output / "CONFIGURATION.png")})
        + ")\nraise SystemExit(subprocess.run(['plasmawindowed','org.irixclassic.quicklaunch'],env=env).returncode)\n")
    command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x800x24", "dbus-run-session",
               "--config-file", str(bus_config), "--", sys.executable, str(launcher)]
    result = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=40)
    (output / "host.log").write_text(result.stdout)
    report = json.loads((output / "PAGE.json").read_text()) if (output / "PAGE.json").exists() else {}
    errors = module.native_errors(result.stdout)
    unchanged = before == {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in sorted(SOURCE.rglob("*")) if path.is_file()}
    passed = unchanged and result.returncode == 0 and not errors and report.get("failed") == 0 and len(report.get("checks", [])) >= 24
    summary = {"status": "passed" if passed else "failed", "native_host_exit": result.returncode,
               "qml_errors": errors, "page": report,
               "sources": before, "sources_unchanged": unchanged,
               "limitations": ["Real page/controllers and native application selector; Apply/Cancel transfer is modeled by the fixture, not the complete Plasma configuration dialog.",
                               "Private generic platform uses Fusion controls; the user's native Qt style is inherited in the real Plasma configuration window.",
                               "No installed application launched, no real profile or session modified."]}
    (output / "RESULTADO.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print("Launcher configuration: " + summary["status"])
    print("Report: " + str(output / "RESULTADO.json"))
    return 0 if passed else 1


if __name__ == "__main__": raise SystemExit(main())
