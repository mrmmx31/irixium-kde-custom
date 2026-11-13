#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Click reset/Apply/Discard in a real private Plasma ConfigView.

Two native instances own separate edit buffers and KConfig groups. The fixture
uses the production schema and preference pages, never the user's applets.
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
import tarfile
import tempfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO / "plasma/applets/org.irixclassic.domainos.panel"
IDENTIFIER = "org.irixclassic.domainos.defaults.test"
CARRIER = "org.irixclassic.domainos.defaults.carrier.test"
CATEGORY_PAGES = ("ConfigInstruments.qml", "ConfigMonitor.qml", "ConfigCommands.qml", "ConfigIconbox.qml",
    "ConfigApplications.qml", "ConfigPager.qml", "ConfigTray.qml", "ConfigActivity.qml")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def fixture_qml(keys):
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
        objectName: "domainosDefaultsFixture"
        implicitWidth: 760; implicitHeight: 820
        Layout.minimumWidth: 760; Layout.minimumHeight: 820
        readonly property var nativeHost: host
        readonly property var schemaKeys: ''' + json.dumps(keys) + '''
        readonly property string snapshotJson: {
            const values = {}, defaults = {};
            for (const key of schemaKeys) {
                values[key] = Plasmoid.configuration[key];
                defaults[key] = Plasmoid.configuration[key + "Default"];
            }
            return JSON.stringify({instanceId: Plasmoid.id, values: values, defaults: defaults});
        }
        function seed() {
            const alternates = {tasksFilterMode:"minimized",applicationsMenuStyle:"kde",trayOverflowMode:"pagination",instrumentMetric:"cpu"};
            for (const key of schemaKeys) {
                const original = JSON.parse(JSON.stringify(Plasmoid.configuration[key + "Default"]));
                let value;
                if (key === "timeZones") value = ["UTC"];
                else if (key === "calendarPlugins") value = ["holidaysevents"];
                else if (Array.isArray(original)) value = [key === "pinnedApplications" ? "domainos-reset-qa.desktop" : "domainos-private-" + key];
                else if (typeof original === "boolean") value = !original;
                else if (typeof original === "number") value = original + 1;
                else value = alternates[key] || String(original) + "__private_reset_probe";
                Plasmoid.configuration[key] = value;
            }
            Plasmoid.configuration.writeConfig();
        }
        Rectangle { anchors.fill: parent; color: "#7894a7" }
    }
}
'''


def private_session(output):
    if os.environ.get("IRIX_DOMAINOS_DEFAULTS_PRIVATE") != "1":
        raise RuntimeError("Private session required")
    returns = []
    modes = ("baseline",) if os.environ.get("IRIX_DOMAINOS_DEFAULTS_BASELINE") == "1" else ("edit", "reload")
    for mode in modes:
        if mode == "reload":
            layout = Path(os.environ["XDG_CONFIG_HOME"]) / "plasmawindowed-appletsrc"
            if layout.is_file():
                shutil.copy2(layout, output / "two-native-instances-layout.ini")
        environment = dict(os.environ, LD_PRELOAD=str(output / "defaults-host.so"),
            IRIX_DOMAINOS_DEFAULTS_TEST="1", IRIX_DOMAINOS_DEFAULTS_MODE=mode,
            IRIX_DOMAINOS_DEFAULTS_DIR=str(output),
            IRIX_DOMAINOS_DEFAULTS_UI=str(Path(os.environ["XDG_DATA_HOME"]) / "plasma/plasmoids" / IDENTIFIER / "contents/ui"),
            IRIX_DOMAINOS_PREFERENCES_REPORT=str(output / (mode + ".json")))
        run = subprocess.run(["dbus-run-session", "--config-file=" + str(output / "private-bus.conf"), "--", "plasmawindowed", CARRIER],
            env=environment, capture_output=True, text=True, timeout=35)
        (output / (mode + ".log")).write_text(run.stdout + run.stderr)
        returns.append(run.returncode)
        if run.returncode:
            break
    return 0 if returns == [0] * len(modes) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--baseline-panel", type=Path,
        help="Readonly old package used to reproduce installed-framework diagnostics without reset pages")
    parser.add_argument("--categories", nargs="+", choices=CATEGORY_PAGES,
        default=["ConfigIconbox.qml", "ConfigTray.qml", "ConfigApplications.qml"],
        help="Production categories reset physically; the general reset and restart are also verified")
    parser.add_argument("--compact-artifacts", action="store_true",
        help="Keep build/profile/screenshots in a disposable repository directory; retain one compressed artifact and RESULTADO in /tmp")
    parser.add_argument("--internal-session", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(); output = args.saida.resolve()
    if args.internal_session:
        return private_session(output)
    if not output.is_relative_to(Path("/tmp")) or output == Path("/tmp") or output.exists():
        parser.error("Use a fresh directory under /tmp")
    output.mkdir(mode=0o700)
    applet = args.baseline_panel.resolve() if args.baseline_panel else APPLET
    schema = applet / "contents/config/main.xml"
    entries = ET.parse(schema).findall(".//{*}entry")
    keys = [entry.attrib["name"] for entry in entries]
    source_files = [schema, applet / "contents/config/config.qml", *sorted((applet / "contents/ui").glob("Config*"))]
    footer = applet / "contents/ui/DomainOSCategoryDefaults.qml"
    if footer.exists():
        source_files.append(footer)
    source_before = {str(path): digest(path) for path in source_files}
    protected = [Path.home() / ".config" / name for name in ("kdeglobals", "plasmarc", "kwinrc", "plasma-org.kde.plasma.desktop-appletsrc")]
    protected_before = {str(path): digest(path) for path in protected}
    private = tempfile.TemporaryDirectory(prefix=".domainos-defaults-qa-", dir=REPO)
    runtime = tempfile.TemporaryDirectory(prefix="dreset-", dir="/tmp")
    profile = Path(private.name)
    public_output = output
    if args.compact_artifacts:
        output = profile / "artifacts"
        output.mkdir(mode=0o700)
    paths = {key: profile / folder for key, folder in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"),
        ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime"))}
    paths["XDG_RUNTIME_DIR"] = Path(runtime.name)
    for path in paths.values():
        if path != paths["XDG_RUNTIME_DIR"]:
            path.mkdir(mode=0o700)
    scratch = profile / "tmp"
    scratch.mkdir(mode=0o700)
    fixture = paths["XDG_DATA_HOME"] / "plasma/plasmoids" / IDENTIFIER
    ui = fixture / "contents/ui"; ui.mkdir(parents=True)
    config = fixture / "contents/config"; config.mkdir()
    shutil.copy2(schema, config / "main.xml")
    shutil.copy2(applet / "contents/config/config.qml", config / "config.qml")
    for path in source_files:
        if path.parent == applet / "contents/ui":
            shutil.copy2(path, ui / path.name)
    (fixture / "metadata.json").write_text(json.dumps({"KPlugin":{"Id":IDENTIFIER,"Name":"DomainOS defaults private test","Version":"1.0","License":"GPL-3.0-or-later"},
        "KPackageStructure":"Plasma/Applet","X-Plasma-API-Minimum-Version":"6.0"}))
    (ui / "main.qml").write_text(fixture_qml(keys))
    carrier = paths["XDG_DATA_HOME"] / "plasma/plasmoids" / CARRIER
    carrier_ui = carrier / "contents/ui"; carrier_ui.mkdir(parents=True)
    (carrier / "metadata.json").write_text(json.dumps({"KPlugin":{"Id":CARRIER,"Name":"Own defaults carrier","Version":"1.0","License":"GPL-3.0-or-later"},
        "KPackageStructure":"Plasma/Applet","X-Plasma-API-Minimum-Version":"6.0"}))
    (carrier_ui / "main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        objectName:"domainosDefaultsCarrier"
        implicitWidth:760;implicitHeight:820
        Layout.minimumWidth:760;Layout.minimumHeight:820
        readonly property var nativeHost:host
    }
}
''')
    applications = paths["XDG_DATA_HOME"] / "applications"; applications.mkdir()
    (applications / "domainos-reset-qa.desktop").write_text("[Desktop Entry]\nType=Application\nName=Own reset fixture\nExec=/usr/bin/false\nIcon=utilities-terminal\nCategories=Utility;\n")
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Test"], text=True))
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(REPO / "plasma/tests/domainos-defaults-host.cpp"),
        "-o", str(output / "defaults-host.so"), *flags, "-ldl"], check=True, env=dict(os.environ, TMPDIR=str(scratch)))
    (output / "private-bus.conf").write_text('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">\n<busconfig><type>session</type><listen>unix:tmpdir=' + str(paths["XDG_RUNTIME_DIR"]) + '</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>\n')
    env = os.environ.copy()
    for name in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "XAUTHORITY", "LD_PRELOAD", "SESSION_MANAGER", "SSH_AUTH_SOCK", "XDG_SESSION_ID", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE"):
        env.pop(name, None)
    env.update({key:str(path) for key,path in paths.items()})
    env.update(XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", XDG_CURRENT_DESKTOP="NONE", XDG_SESSION_TYPE="x11",
        QT_QPA_PLATFORM="xcb", QT_QPA_PLATFORMTHEME="kde", QT_QUICK_BACKEND="software", QML_DISABLE_DISK_CACHE="1",
        DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(paths["XDG_RUNTIME_DIR"] / "no-system-bus"), PULSE_SERVER="unix:" + str(paths["XDG_RUNTIME_DIR"] / "no-audio"),
        IRIX_DOMAINOS_DEFAULTS_PRIVATE="1", IRIX_DOMAINOS_DEFAULTS_PAGES=",".join(dict.fromkeys(args.categories)),
        TMPDIR=str(scratch), LC_ALL="C.UTF-8", LANG="C.UTF-8")
    if args.baseline_panel:
        env["IRIX_DOMAINOS_DEFAULTS_BASELINE"] = "1"
    cache = subprocess.run(["kbuildsycoca6", "--noincremental"], env=dict(env,QT_QPA_PLATFORM="offscreen"), capture_output=True, text=True, timeout=20)
    (output / "sycoca.log").write_text(cache.stdout + cache.stderr)
    run = subprocess.run(["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1100x1000x24", sys.executable,
        str(Path(__file__).resolve()), "--saida", str(output), "--internal-session"], env=env, capture_output=True, text=True, timeout=75)
    (output / "session.log").write_text(run.stdout + run.stderr)
    with tarfile.open(public_output / "PRIVATE-PROFILE.tar.gz", "w:gz") as archive:
        for key in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
            archive.add(paths[key], arcname=paths[key].name)
        if args.compact_artifacts:
            archive.add(output, arcname="artifacts")
    if args.baseline_panel:
        result = report_baseline(output, run, source_before, protected_before, ui)
        if args.compact_artifacts:
            shutil.copy2(output / "RESULTADO.json", public_output / "RESULTADO.json")
        private.cleanup()
        runtime.cleanup()
        return result
    edit = json.loads((output / "edit.json").read_text()) if (output / "edit.json").exists() else {}
    reload = json.loads((output / "reload.json").read_text()) if (output / "reload.json").exists() else {}
    logs = "\n".join(path.read_text() for path in (output / "edit.log", output / "reload.log") if path.exists())
    diagnostics = [line for line in logs.splitlines() if any(marker in line for marker in ("ReferenceError:", "TypeError:", "SyntaxError:", "Cannot assign", "is not a type", "Error loading QML", "error when loading applet", "Binding loop detected"))]
    first = edit.get("seeded_first", {}); second = edit.get("seeded_second", {})
    defaults = first.get("defaults", {}); values = first.get("values", {})
    def state(stage, section="first"):
        return edit.get(stage, {}).get(section, {})
    general = edit.get("general_open_before_reset", {}); prepared = edit.get("general_prepared_before_apply", {})
    general_source = (ui / "ConfigDefaults.qml").read_text()
    cfg_keys = re.findall(r"property\s+var\s+cfg_(\w+)\s*:", general_source)
    checks = {
        "schema_and_general_buffer_keys_equal":set(cfg_keys)==set(keys) and len(cfg_keys)==len(keys),
        "native_host_exited":run.returncode==0 and not edit.get("failure") and not reload.get("failure"),
        "all_schema_defaults_come_from_native_map":set(defaults)==set(keys) and all(value is not None for value in defaults.values()),
        "all_schema_entries_started_customized":set(values)==set(keys) and all(values[key]!=defaults[key] for key in keys),
        "two_native_instance_ids_are_distinct":bool(first) and bool(second) and first.get("instanceId")!=second.get("instanceId"),
        "opening_general_is_not_dirty_or_a_write":general.get("page_loaded") is True and general.get("edits")==values and general.get("apply_enabled") is False and general.get("first")==first,
        "general_reset_uses_real_pointer":edit.get("general_reset_pointer") is True and edit.get("general_second_reset_pointer") is True,
        "general_reset_stages_all_native_defaults":prepared.get("edits")==defaults and prepared.get("first")==first and prepared.get("apply_enabled") is True,
        "general_reset_button_disables_once_defaults_prepared":prepared.get("reset_enabled") is False,
        "native_discard_uses_real_buttons":edit.get("native_cancel_pointer") is True and edit.get("native_discard_pointer") is True,
        "native_discard_preserves_all_saved_values":state("general_discarded")==first and edit.get("general_discarded",{}).get("config_visible") is False,
        "reopen_after_discard_recovers_saved_edits":edit.get("general_reopened_after_discard",{}).get("edits")==values and edit.get("general_reopened_after_discard",{}).get("apply_enabled") is False,
        "native_apply_uses_real_button":edit.get("native_general_apply_pointer") is True,
        "native_apply_saves_all_schema_defaults":state("general_applied").get("values")==defaults and edit.get("general_applied",{}).get("apply_enabled") is False,
        "general_reset_preserves_other_instance":all(state(stage,"second")==second for stage in ("general_open_before_reset","general_prepared_before_discard","general_discarded","general_prepared_before_apply","general_applied","final_general_applied")),
        "final_general_apply_finishes_at_defaults":edit.get("final_general_reset_pointer") is True and edit.get("final_general_apply_pointer") is True and state("final_general_applied").get("values")==defaults,
        "schema_defaults_persist_after_restart":reload.get("reloaded_first",{}).get("values")==defaults,
        "same_instance_ids_restored_after_restart":reload.get("reloaded_first",{}).get("instanceId")==first.get("instanceId") and reload.get("reloaded_second",{}).get("instanceId")==second.get("instanceId"),
        "other_instance_customization_persists_after_restart":reload.get("reloaded_second",{}).get("values")==second.get("values"),
        "already_default_general_has_no_pending_change":reload.get("reloaded_general",{}).get("page_loaded") is True and reload.get("reloaded_general",{}).get("edits")==defaults and reload.get("reloaded_general",{}).get("apply_enabled") is False and reload.get("reloaded_general",{}).get("reset_enabled") is False,
        "qml_errors_zero":not diagnostics,
        "sources_unchanged":source_before=={name:digest(Path(name)) for name in source_before},
        "real_profile_configs_unchanged":protected_before=={name:digest(Path(name)) for name in protected_before},
    }
    for page in dict.fromkeys(args.categories):
        before = edit.get(page + "_before", {}); pending = edit.get(page + "_prepared", {}); after = edit.get(page + "_applied", {})
        category_keys = set(pending.get("edits", {})); expected = dict(values)
        for key in category_keys:
            expected[key] = defaults[key]
        checks[page+"_physical_reset_and_apply"]=edit.get(page+"_reset_pointer") is True and edit.get(page+"_apply_pointer") is True
        checks[page+"_opening_is_not_dirty_or_a_write"]=before.get("page_loaded") is True and before.get("edits")=={key:values[key] for key in category_keys} and before.get("first",{}).get("values")==values and before.get("apply_enabled") is False
        checks[page+"_prepares_only_category_defaults"]=bool(category_keys) and pending.get("edits")=={key:defaults[key] for key in category_keys} and pending.get("first",{}).get("values")==values and pending.get("apply_enabled") is True and pending.get("reset_enabled") is False
        checks[page+"_apply_leaves_other_categories_and_instance_alone"]=after.get("first",{}).get("values")==expected and after.get("second")==second
    report = {"status":"passed" if all(checks.values()) else "failed","checks":checks,"edit":edit,"reload":reload,"qml_diagnostics":diagnostics,
        "scope":"Production preference pages and schema in two native applet instances in a private XDG/D-Bus/Xvfb profile. No user panel, desktop or other applet is reset.",
        "source_hashes":source_before,"protected_before":protected_before,"protected_after":{name:digest(Path(name)) for name in protected_before},
        "schema_entry_count":len(keys),"categories":list(dict.fromkeys(args.categories)),
        "test_source_hashes":{str(path):digest(path) for path in (Path(__file__), REPO / "plasma/tests/domainos-defaults-host.cpp")},
        "category_navigation":"Native ConfigView category API; Reset, Apply, Cancel and Discard use actual mouse events",
        "artifacts":str(public_output / "PRIVATE-PROFILE.tar.gz")}
    (public_output / "RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(checks),"failed":[key for key,value in checks.items() if not value],"report":str(public_output / "RESULTADO.json")},ensure_ascii=False))
    private.cleanup()
    runtime.cleanup()
    return 0 if report["status"]=="passed" else 1


def report_baseline(output, run, source_before, protected_before, ui):
    baseline = json.loads((output / "baseline.json").read_text()) if (output / "baseline.json").exists() else {}
    log = (output / "baseline.log").read_text() if (output / "baseline.log").exists() else ""
    diagnostics = [line for line in log.splitlines() if any(marker in line for marker in
        ("ReferenceError:","TypeError:","SyntaxError:","Cannot assign","is not a type","Error loading QML","error when loading applet","Binding loop detected"))]
    expected = ["qrc:/qt/qml/org/kde/kirigami/dialogs/PromptDialog.qml:135: TypeError: Cannot read property 'Success' of undefined",
        "qrc:/qt/qml/org/kde/kirigami/dialogs/PromptDialog.qml:97: TypeError: Cannot read property 'None' of undefined"]
    saved = baseline.get("seeded_first",{})
    checks = {
        "native_baseline_host_exited":run.returncode==0 and not baseline.get("failure"),
        "old_pages_have_no_reset_implementation":not (ui/"ConfigDefaults.qml").exists() and not (ui/"DomainOSCategoryDefaults.qml").exists()
            and "resetCategory" not in (ui/"ConfigUtils.js").read_text(),
        "three_stock_prompt_dialogs_reproduce_same_six_diagnostics":len(diagnostics)==6
            and all(diagnostics.count(line)==3 for line in expected),
        "old_sources_unchanged":source_before=={name:digest(Path(name)) for name in source_before},
        "real_profile_configs_unchanged":protected_before=={name:digest(Path(name)) for name in protected_before},
    }
    for cycle in range(3):
        prefix="baseline_"+str(cycle)
        opened=baseline.get(prefix+"_opened",{});pending=baseline.get(prefix+"_pending",{});discarded=baseline.get(prefix+"_discarded",{})
        checks[prefix+"_old_activity_page_without_reset"]=opened.get("page_loaded") is True and opened.get("reset_present") is False and opened.get("apply_enabled") is False
        checks[prefix+"_edit_is_pending_without_saving"]=baseline.get(prefix+"_edit_local") is True and pending.get("apply_enabled") is True and pending.get("first")==saved
        checks[prefix+"_native_cancel_and_discard"]=baseline.get(prefix+"_cancel_pointer") is True and baseline.get(prefix+"_discard_pointer") is True
        checks[prefix+"_discard_preserves_saved_values"]=discarded.get("first")==saved and discarded.get("config_visible") is False
    report={"status":"reproduced" if all(checks.values()) else "failed","checks":checks,"baseline":baseline,
        "qml_diagnostics":diagnostics,"source_hashes":source_before,"protected_before":protected_before,
        "protected_after":{name:digest(Path(name)) for name in protected_before},
        "scope":"Readonly pre-reset R7 preference pages and schema in an own native applet/XDG/D-Bus/Xvfb profile. Three ordinary unsaved edits and native Discard reproduce installed Kirigami diagnostics. No errors are suppressed and no installed SDK or user configuration is changed."}
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(checks),"failed":[key for key,value in checks.items() if not value],"report":str(output/"RESULTADO.json")},ensure_ascii=False))
    return 0 if report["status"]=="reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
