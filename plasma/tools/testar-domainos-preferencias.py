#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify instance-owned preferences in real Plasma with private XDG/bus/Xvfb.

Loads every configuration page; edits, discards, applies and restarts the native
host. A second real applet of the same plugin tests independence of KConfig groups.
Optional import reads an explicitly selected launcher list in a disposable profile.
Nothing is installed or applied in the user's real session.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO / "plasma/applets/org.irixclassic.domainos.panel"
IDENTIFIER = "org.irixclassic.domainos.preferences.test"
FIRST = "irix-domainos-qa-first.desktop"
SECOND = "irix-domainos-qa-second.desktop"
THIRD = "irix-domainos-qa-third.desktop"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def panel_categories_match(categories, configured_pages):
    expected = set(configured_pages)
    sources = [str(category.get("source", "")) for category in categories]
    names = [Path(source).name for source in sources]
    return len(expected) == 9 and len(configured_pages) == 9 and all(names.count(name) == 1 for name in expected) \
        and all(name in expected or (Path(source).is_absolute() and "plasmacalendarplugins" in Path(source).parts
            and Path(source).is_file()) for name, source in zip(names, sources))


def private_session(output):
    if os.environ.get("IRIX_DOMAINOS_PREFERENCES_PRIVATE_SESSION") != "1":
        raise RuntimeError("Private session required")
    outcomes = []
    for mode in ("edit", "reload"):
        if mode == "reload":
            # The second native applet is intentionally created for isolation.
            # plasmawindowed restores that containment and refuses a second
            # window for an already restored plugin. Keep the fixture layout
            # as evidence; retain the actual native preferences unchanged.
            layout = Path(os.environ["XDG_CONFIG_HOME"]) / "plasmawindowed-appletsrc"
            if layout.is_file():
                layout.rename(output / "two-instances-windowed-layout.ini")
        environment = dict(os.environ, LD_PRELOAD=str(output / "preferences-host.so"),
            IRIX_DOMAINOS_PREFERENCES_TEST="1", IRIX_DOMAINOS_PREFERENCES_MODE=mode,
            IRIX_DOMAINOS_PREFERENCES_REPORT=str(output / (mode + ".json")),
            IRIX_DOMAINOS_PREFERENCES_DIR=str(output))
        result = subprocess.run(["dbus-run-session", "--config-file=" + str(output / "private-bus.conf"), "--", "plasmawindowed", IDENTIFIER], env=environment, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, timeout=35)
        (output / (mode + ".log")).write_text(result.stdout)
        outcomes.append(result.returncode)
        if result.returncode:
            break
    return 0 if outcomes == [0, 0] else 1


def fixture_qml(page_keys):
    return '''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
PlasmoidItem {
    id: host
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    fullRepresentation: Item {
        id: fixture
        objectName: "domainosPreferencesTestFixture"
        implicitWidth: 760; implicitHeight: 800
        Layout.minimumWidth: 760; Layout.minimumHeight: 800
        property int scenario: 0
        readonly property var nativeHost: host
        property var outcomes: ({})
        property string activePage: "ConfigActivity.qml"
        readonly property var pageKeys: ''' + json.dumps(page_keys) + '''
        function saved() {
            const result = {};
            for (const key of Plasmoid.configuration.keys()) result[key] = Plasmoid.configuration[key];
            return result;
        }
        function pageValues() {
            const result = {};
            if (!pageLoader.item) return result;
            for (const key of (pageKeys[activePage] || [])) result[key] = pageLoader.item["cfg_" + key];
            if (activePage === "ConfigApplications.qml") {
                result.requestCount = pageLoader.item.requestCount;
                result.origins = pageLoader.item.importOrigins;
                result.importMessage = pageLoader.item.importMessage;
                result.title = (pageLoader.item.cfg_pinnedApplications || []).length ? pageLoader.item.pinTitle(0) : "";
            }
            if (activePage === "ConfigIconbox.qml") result.automaticAvailable = pageLoader.item.automaticAvailable;
            if (activePage === "ConfigInstruments.qml") result.availableCalendarProviders = pageLoader.item.availableCalendarProviders;
            if (activePage === "ConfigTray.qml") result.nativeSnapshotAvailable = pageLoader.item.nativeSnapshotAvailable;
            return result;
        }
        property string snapshotJson: {
            const unused = scenario;
            const trigger = pageLoader.item;
            return JSON.stringify({instanceId:Plasmoid.id, saved:saved(), page:activePage,
                pageStatus:pageLoader.status, edit:pageValues(), outcomes:outcomes});
        }
        function snapshotNow() { return JSON.stringify({instanceId:Plasmoid.id,saved:saved(),page:activePage,pageStatus:pageLoader.status,edit:pageValues(),outcomes:outcomes}); }
        function showPage(name) {
            activePage = name;
            const props = {};
            for (const key of pageKeys[name]) props["cfg_" + key] = Plasmoid.configuration[key];
            pageLoader.setSource("", {});
            pageLoader.setSource(name, props);
        }
        function applyPage() {
            // Same cfg_* mapping/writeConfig used by Plasma's applet dialog.
            for (const key of pageKeys[activePage]) Plasmoid.configuration[key] = pageLoader.item["cfg_" + key];
            Plasmoid.configuration.writeConfig();
        }
        function configureNative() {
            const action = Plasmoid.internalAction("configure");
            if (!action) return false;
            action.trigger();
            return true;
        }
        Rectangle { anchors.fill:parent; color:"#b4bdc3" }
        Loader { id:pageLoader; anchors.fill:parent; anchors.margins:12 }
        Component.onCompleted: showPage("ConfigActivity.qml")
        onScenarioChanged: {
            const page = pageLoader.item;
            if(scenario === 1) { page.cfg_keepActivityLight=true;page.cfg_activityLightMilliseconds=1750;page.cfg_barHintsEnabled=true; }
            else if(scenario === 2) showPage("ConfigActivity.qml");
            else if(scenario === 3) { page.cfg_keepActivityLight=true;page.cfg_activityLightMilliseconds=1750;page.cfg_barHintsEnabled=true;applyPage(); }
            else if(scenario === 4) showPage("ConfigIconbox.qml");
            else if(scenario === 5) {
                const accepted=page.selectFilter(2);
                outcomes=Object.assign({},outcomes,{automaticWithoutThreshold:page.cfg_tasksFilterMode,automaticWithoutThresholdAccepted:accepted});
            }
            else if(scenario === 6) { page.cfg_tasksAutomaticThreshold=3;page.cfg_tasksFilterMode="automatic";page.cfg_tasksGroupingMode=0;page.cfg_tasksOnlyCurrentDesktop=false;page.cfg_tasksOnlyCurrentScreen=true;page.cfg_tasksGroupingAppIdBlacklist=["org.kde.kate"];page.cfg_middleClickAction=3;page.cfg_wheelEnabled=false;page.cfg_wheelSkipMinimized=false;page.cfg_iconboxWindowThumbnails=true;page.cfg_iconboxHintsEnabled=false; }
            else if(scenario === 7) applyPage();
            else if(scenario === 8) showPage("ConfigApplications.qml");
            else if(scenario === 9) {
                page.cfg_applicationsMenuStyle="kde";
                const added = page.addList("applications:irix-domainos-qa-first.desktop\\nirix-domainos-qa-second.desktop\\nirix-domainos-qa-first.desktop");
                const invalid = page.addList("kate.desktop; invalid|shell");
                page.movePin(1,-1);page.removePin(1);
                outcomes=Object.assign({},outcomes,{validPinsAdded:added,invalidPinsAdded:invalid});
            }
            else if(scenario === 10) applyPage();
            else if(scenario === 13) applyPage();
            else if(scenario === 14) { showPage("ConfigMonitor.qml");pageLoader.item.cfg_instrumentMetric="cpu";pageLoader.item.cfg_instrumentSampleInterval=1500;pageLoader.item.cfg_instrumentHistoryLength=90;applyPage(); }
            else if(scenario === 15) { showPage("ConfigInstruments.qml");pageLoader.item.cfg_timeZones=["Local","UTC","Europe/London"];applyPage(); }
            else if(scenario === 16) { showPage("ConfigCommands.qml");pageLoader.item.cfg_mailClient="org.mozilla.thunderbird.desktop";pageLoader.item.cfg_terminalCommand="konsole --separate";applyPage(); }
            else if(scenario === 17) { showPage("ConfigPager.qml");pageLoader.item.cfg_pagerWheelActivates=true;applyPage(); }
            else if(scenario === 18) showPage("ConfigTray.qml");
            else if(scenario === 19) { page.setItemPolicy("org.kde.plasma.networkmanagement","visible");page.setItemPolicy("org.kde.plasma.volume","hidden");page.cfg_trayOrder=["org.kde.plasma.networkmanagement","org.kde.plasma.volume"];page.cfg_trayIncludeHiddenInOverflow=true;page.cfg_trayOverflowMode="pagination";const invalid=page.setIds("visible","org.kde.plasma.volume");outcomes=Object.assign({},outcomes,{invalidTrayOverlapAccepted:invalid}); }
            else if(scenario === 20) applyPage();
            else if(scenario === 22) outcomes=Object.assign({},outcomes,{nativeConfigureRequested:configureNative()});
        }
    }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True, help="New directory under /tmp")
    parser.add_argument("--internal-session", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(); output = args.saida.absolute()
    if args.internal_session:
        return private_session(output)
    if not output.is_relative_to(Path("/tmp")) or output.exists():
        parser.error("Use a new directory under /tmp")
    output.mkdir(mode=0o700)
    sources = [APPLET / "contents/config/main.xml", APPLET / "contents/config/config.qml",
               APPLET / "contents/ui/DomainOSCategoryDefaults.qml", *sorted((APPLET / "contents/ui").glob("Config*"))]
    sources_before = {str(path): digest(path) for path in sources}
    protected = [Path.home() / ".config" / name for name in ("kdeglobals", "plasmarc", "kwinrc", "plasma-org.kde.plasma.desktop-appletsrc")]
    config_before = {str(path): digest(path) for path in protected}
    namespace = {"k": "http://www.kde.org/standards/kcfg/1.0"}
    schema = ET.parse(APPLET / "contents/config/main.xml")
    schema_keys = {entry.attrib["name"] for entry in schema.findall(".//k:entry", namespace)}
    page_keys = {path.name: re.findall(r"property\s+(?:alias|var|string|bool)\s+cfg_(\w+)\s*:", path.read_text()) for path in sorted((APPLET / "contents/ui").glob("Config*.qml"))}
    configured_pages = re.findall(r'source:\s*"(Config[^"/]+\.qml)"', (APPLET / "contents/config/config.qml").read_text())
    paths = {key: output / name for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
        ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime"))}
    for path in paths.values():
        path.mkdir(mode=0o700)
    fixture = paths["XDG_DATA_HOME"] / "plasma/plasmoids" / IDENTIFIER
    shutil.copytree(APPLET, fixture, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (fixture / "metadata.json").write_text(json.dumps({"KPlugin": {"Id": IDENTIFIER, "Name": "DomainOS preferences private test", "Version": "1.0", "License": "GPL-3.0-or-later"}, "KPackageStructure": "Plasma/Applet", "X-Plasma-API-Minimum-Version": "6.0"}))
    (fixture / "contents/ui/main.qml").write_text(fixture_qml(page_keys))
    launcher_profile = paths["XDG_CONFIG_HOME"] / "plasma-org.kde.plasma.desktop-appletsrc"
    launcher_profile.write_text("[Containments][71][Applets][81]\nplugin=org.kde.plasma.icontasks\n\n[Containments][71][Applets][81][Configuration][General]\nlauncherList=applications:" + FIRST + ",applications:" + THIRD + "\n")
    import_source_before = digest(launcher_profile)
    applications = paths["XDG_DATA_HOME"] / "applications"; applications.mkdir()
    for desktop_id, title in ((FIRST, "DomainOS QA First"), (SECOND, "DomainOS QA Second"), (THIRD, "DomainOS QA Imported Third")):
        (applications / desktop_id).write_text("[Desktop Entry]\nType=Application\nName=" + title + "\nExec=/usr/bin/false\nIcon=utilities-terminal\nTerminal=false\nCategories=Utility;\n")
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Test"], text=True))
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(REPO / "plasma/tests/domainos-preferences-host.cpp"), "-o", str(output / "preferences-host.so"), *flags, "-ldl"], check=True)
    bus = output / "private-bus.conf"
    bus.write_text('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">\n<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>\n')
    environment = os.environ.copy()
    for name in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "LD_PRELOAD", "XDG_SESSION_ID", "KDE_FULL_SESSION", "KDE_SESSION_VERSION"):
        environment.pop(name, None)
    environment.update({key: str(path) for key, path in paths.items()})
    environment.update(XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", XDG_CURRENT_DESKTOP="NONE", XDG_SESSION_TYPE="x11", QT_QPA_PLATFORM="xcb", QT_QPA_PLATFORMTHEME="generic", QT_QUICK_BACKEND="software", LIBGL_ALWAYS_SOFTWARE="1", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(paths["XDG_RUNTIME_DIR"] / "no-system-bus"))
    cache = subprocess.run(["kbuildsycoca6", "--noincremental"], env=dict(environment, QT_QPA_PLATFORM="offscreen"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20)
    (output / "sycoca.log").write_text(cache.stdout)
    environment["IRIX_DOMAINOS_PREFERENCES_PRIVATE_SESSION"] = "1"
    # The fresh XDG_CACHE_HOME isolates caches. Disabling QML's disk cache
    # breaks enum initialization in the installed Kirigami PromptDialog.
    environment.pop("QML_DISABLE_DISK_CACHE", None)
    result = subprocess.run(["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1000x950x24", "dbus-run-session", "--config-file=" + str(bus), "--", sys.executable, str(Path(__file__).resolve()), "--saida", str(output), "--internal-session"], env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=55)
    (output / "session.log").write_text(result.stdout)
    edit = json.loads((output / "edit.json").read_text()) if (output / "edit.json").is_file() else {}
    reload = json.loads((output / "reload.json").read_text()) if (output / "reload.json").is_file() else {}
    logs = "\n".join(path.read_text() for path in (output / "edit.log", output / "reload.log") if path.is_file())
    diagnostics = [line for line in logs.splitlines() if any(marker in line for marker in ("ReferenceError:", "TypeError:", "SyntaxError:", "Cannot assign", "is not a type", "Error loading QML", "error when loading applet", "Binding loop detected"))]
    def state(stage, section="saved"):
        return edit.get(stage, {}).get(section, {})
    final = state("tray_applied")
    checks = {
        "xml_schema_and_pages_match": set(key for keys in page_keys.values() for key in keys) == (schema_keys if "ConfigDefaults.qml" in page_keys else schema_keys - {"configurationSchemaVersion", "showIconsRootLevel", "alignResultsToBottom"}),
        "private_native_host_exited": result.returncode == 0 and not edit.get("failure") and not reload.get("failure"),
        "all_editable_categories_load": {stage.get("page") for stage in edit.values() if isinstance(stage, dict) and stage.get("pageStatus") == 1} == set(configured_pages) - {"ConfigDefaults.qml"},
        "technical_defaults_preserve_unset_threshold": state("initial").get("tasksAutomaticThreshold") == -1 and state("initial").get("tasksFilterMode") == "normal" and state("initial").get("keepActivityLight") is False,
        "editing_does_not_write_native_config": state("edited_unsaved") == state("initial") and state("edited_unsaved", "edit").get("activityLightMilliseconds") == 1750,
        "discard_restores_saved_values": state("discarded", "edit").get("activityLightMilliseconds") == 1000 and state("discarded", "edit").get("keepActivityLight") is False,
        "apply_writes_native_config": state("activity_applied").get("activityLightMilliseconds") == 1750 and state("activity_applied").get("keepActivityLight") is True,
        "automatic_requires_explicit_threshold": state("automatic_without_threshold", "edit").get("tasksFilterMode") == "normal" and state("iconbox_edited_unsaved", "edit").get("automaticAvailable") is True,
        "iconbox_changes_wait_for_apply": state("iconbox_edited_unsaved").get("tasksAutomaticThreshold") == -1 and state("iconbox_applied").get("tasksAutomaticThreshold") == 3 and state("iconbox_applied").get("tasksGroupingMode") == 0,
        "inherited_mouse_defaults_match_previous_iconbox": state("initial").get("middleClickAction") == 2 and state("initial").get("wheelEnabled") is True and state("initial").get("wheelSkipMinimized") is True,
        "inherited_mouse_preferences_wait_for_apply": state("iconbox_edited_unsaved").get("middleClickAction") == 2 and state("iconbox_edited_unsaved").get("wheelEnabled") is True and state("iconbox_edited_unsaved").get("wheelSkipMinimized") is True and state("iconbox_edited_unsaved", "edit").get("middleClickAction") == 3 and state("iconbox_edited_unsaved", "edit").get("wheelEnabled") is False and state("iconbox_edited_unsaved", "edit").get("wheelSkipMinimized") is False,
        "inherited_mouse_preferences_apply_and_survive_restart": final.get("middleClickAction") == 3 and final.get("wheelEnabled") is False and final.get("wheelSkipMinimized") is False and reload.get("reloaded", {}).get("saved", {}).get("middleClickAction") == 3 and reload.get("reloaded", {}).get("saved", {}).get("wheelEnabled") is False and reload.get("reloaded", {}).get("saved", {}).get("wheelSkipMinimized") is False,
        "window_thumbnails_default_disabled": state("initial").get("iconboxWindowThumbnails") is False,
        "iconbox_titles_hint_default_enabled": state("initial").get("iconboxHintsEnabled") is True,
        "window_thumbnails_wait_for_apply": state("iconbox_edited_unsaved").get("iconboxWindowThumbnails") is False and state("iconbox_edited_unsaved", "edit").get("iconboxWindowThumbnails") is True,
        "window_thumbnails_apply_and_survive_restart": final.get("iconboxWindowThumbnails") is True and reload.get("reloaded", {}).get("saved", {}).get("iconboxWindowThumbnails") is True,
        "window_thumbnails_keep_other_instance_disabled": edit.get("second_instance", {}).get("saved", {}).get("iconboxWindowThumbnails") is False,
        "iconbox_hint_mode_applies_and_survives_restart": final.get("iconboxHintsEnabled") is False and reload.get("reloaded", {}).get("saved", {}).get("iconboxHintsEnabled") is False,
        "iconbox_hints_keep_other_instance_default": edit.get("second_instance", {}).get("saved", {}).get("iconboxHintsEnabled") is True,
        "bar_hints_default_disabled": state("initial").get("barHintsEnabled") is False,
        "bar_hint_edits_discard_without_write": state("edited_unsaved").get("barHintsEnabled") is False and state("edited_unsaved", "edit").get("barHintsEnabled") is True and state("discarded", "edit").get("barHintsEnabled") is False,
        "bar_hints_apply_and_survive_restart": final.get("barHintsEnabled") is True and reload.get("reloaded", {}).get("saved", {}).get("barHintsEnabled") is True,
        "bar_hints_keep_other_instance_disabled": edit.get("second_instance", {}).get("saved", {}).get("barHintsEnabled") is False,
        "applications_menu_defaults_to_domainos": state("initial").get("applicationsMenuStyle") == "domainos",
        "applications_menu_change_waits_for_apply": state("pins_edited_unsaved").get("applicationsMenuStyle") == "domainos" and state("pins_edited_unsaved", "edit").get("applicationsMenuStyle") == "kde",
        "applications_menu_style_applies_and_survives_restart": final.get("applicationsMenuStyle") == "kde" and reload.get("reloaded", {}).get("saved", {}).get("applicationsMenuStyle") == "kde",
        "applications_menu_keeps_other_instance_default": edit.get("second_instance", {}).get("saved", {}).get("applicationsMenuStyle") == "domainos",
        "kde_menu_compatibility_defaults_preserved": state("initial").get("showIconsRootLevel") is True and state("initial").get("alignResultsToBottom") is False and final.get("showIconsRootLevel") is True and final.get("alignResultsToBottom") is False,
        "pins_source_not_read_on_page_open": state("pins_initial", "edit").get("requestCount") == 0,
        "pin_ids_validated_deduplicated_reordered": state("pins_edited_unsaved", "edit").get("pinnedApplications") == [SECOND] and edit.get("pins_edited_unsaved", {}).get("outcomes", {}).get("invalidPinsAdded") is False,
        "pins_independent_and_saved_only_on_apply": state("pins_edited_unsaved").get("pinnedApplications") == [] and state("pins_applied").get("pinnedApplications") == [SECOND],
        "pins_titles_resolve_desktop_metadata": state("pins_edited_unsaved", "edit").get("title") == "DomainOS QA Second",
        "import_origin_selected_with_real_pointer": edit.get("real_origins_mouse_click") is True and len(state("import_origins", "edit").get("origins", [])) == 1 and state("import_origins", "edit").get("requestCount") == 1,
        "only_chosen_import_source_read": edit.get("real_source_mouse_click") is True and state("import_source_unsaved", "edit").get("pinnedApplications") == [SECOND, FIRST, THIRD] and state("import_source_unsaved").get("pinnedApplications") == [SECOND],
        "imported_source_profile_unchanged": digest(launcher_profile) == import_source_before,
        "monitor_preferences_persist": final.get("instrumentMetric") == "cpu" and final.get("instrumentSampleInterval") == 1500 and final.get("instrumentHistoryLength") == 90,
        "clock_zones_and_no_automatic_agenda": final.get("timeZones") == ["Local", "UTC", "Europe/London"] and final.get("calendarPlugins") == [],
        "mail_terminal_preferences_persist": final.get("mailClient") == "org.mozilla.thunderbird.desktop" and final.get("terminalCommand") == "konsole --separate",
        "pager_wheel_alternative_persists": final.get("pagerWheelActivates") is True,
        "tray_overlap_rejected": edit.get("tray_edited_unsaved", {}).get("outcomes", {}).get("invalidTrayOverlapAccepted") is False,
        "tray_preferences_wait_for_apply": state("tray_edited_unsaved").get("trayVisibleItems") == [] and final.get("trayVisibleItems") == ["org.kde.plasma.networkmanagement"] and final.get("trayHiddenItems") == ["org.kde.plasma.volume"] and final.get("trayOverflowMode") == "pagination",
        "second_real_applet_instance_keeps_defaults": edit.get("created_second_native_instance") is True and edit.get("second_instance", {}).get("instanceId") == 101 and edit.get("second_instance", {}).get("saved", {}).get("pinnedApplications") == [] and edit.get("second_instance", {}).get("saved", {}).get("tasksAutomaticThreshold") == -1 and edit.get("second_instance", {}).get("saved", {}).get("middleClickAction") == 2 and edit.get("second_instance", {}).get("saved", {}).get("wheelEnabled") is True and edit.get("second_instance", {}).get("saved", {}).get("wheelSkipMinimized") is True,
        "native_config_view_matches_configured_categories": edit.get("native_config_view_visible") is True and panel_categories_match(edit.get("native_config_categories", []), configured_pages) and edit.get("native_configuration_dialog", {}).get("outcomes", {}).get("nativeConfigureRequested") is True,
        "native_dialog_apply_by_real_pointer": edit.get("native_clock_page_edited") is True and edit.get("real_native_apply_mouse_click") is True and set(state("native_dialog_applied").get("timeZones", [])) == {"Local", "UTC", "Europe/London", "America/Manaus"},
        "native_config_survives_host_restart": reload.get("reloaded", {}).get("saved") == state("native_dialog_applied"),
        "qml_diagnostics_zero": not diagnostics,
        "production_preferences_sources_unchanged": sources_before == {str(path): digest(path) for path in sources},
        "real_desktop_preferences_unchanged": config_before == {str(path): digest(path) for path in protected},
    }
    native_warnings = [line for line in logs.splitlines() if "Setting initial properties failed:" in line or "Created graphical object was not placed" in line]
    report = {"format": 1, "status": "passed" if all(checks.values()) else "failed", "checks": checks, "qml_diagnostics": diagnostics, "native_dialog_property_scope_warnings": native_warnings, "native": edit, "reload": reload, "real_profiles_modified": False, "scope": "Private native Plasma KConfigPropertyMap, two applet IDs, edit/discard/apply/restart and explicit read-only pin import"}
    (output / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "failed": [name for name, ok in checks.items() if not ok], "report": str(output / "RESULTADO.json")}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
