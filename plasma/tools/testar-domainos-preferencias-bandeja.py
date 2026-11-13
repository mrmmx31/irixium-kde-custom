#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify routing and per-instance edits in the production Plasma ConfigView.

Starts the shipped DomainOS composition with its native tray in a disposable KDE
session. The default path checks tray policies; --painel-ui exercises the actual
pinned Preferences entry, Iconbox page, Apply, Cancel/Discard, another native
applet instance and persistence after restarting the private host. Physical paths
use X11 pointer clicks rather than configuration writes or emitted UI signals.
No live session, audio server, system D-Bus or other user's panel is configured.
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
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO / "plasma/applets/org.irixclassic.domainos.panel"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def panel_categories_match(categories, configured_pages):
    expected = set(configured_pages)
    sources = [str(category.get("source", "")) for category in categories]
    names = [Path(source).name for source in sources]
    return len(expected) == 9 and len(configured_pages) == 9 and all(names.count(name) == 1 for name in expected) \
        and all(name in expected or (Path(source).is_absolute() and "plasmacalendarplugins" in Path(source).parts
            and Path(source).is_file()) for name, source in zip(names, sources))


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_TRAY_CONFIG_PRIVATE_SESSION") != "1":
        raise RuntimeError("Private session required")
    processes, logs = [], []
    try:
        for executable in ("kwin_x11", "kactivitymanagerd", "ksystemstats"):
            path = shutil.which(executable) or "/usr/lib/x86_64-linux-gnu/libexec/" + executable
            log = (output / (executable + ".log")).open("w"); logs.append(log)
            processes.append(subprocess.Popen([path, *(["--remain"] if executable == "ksystemstats" else [])], stdout=log, stderr=subprocess.STDOUT))
        for _ in range(80):
            probe = subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"], capture_output=True, timeout=2)
            if probe.returncode == 0:
                break
            time.sleep(.05)
        ui = os.environ.get("IRIX_DOMAINOS_PANEL_UI_TEST") == "1"
        modes = ["panel-ui-edit", "panel-ui-reload"] if ui else [os.environ.get("IRIX_DOMAINOS_PREFERENCES_MODE", "tray-production")]
        outcomes = []
        for mode in modes:
            if mode == "panel-ui-reload":
                # The original windowed applet's settings remain in
                # plasmawindowedrc; only the separately added fixture instance
                # is restored from this containment layout. Retain it as proof
                # and avoid restoring a second window for the same plugin.
                layout = Path(os.environ["XDG_CONFIG_HOME"]) / "plasmawindowed-appletsrc"
                if layout.is_file():
                    # The private profile can be on the repository filesystem
                    # while retained reports are on tmpfs; rename gives EXDEV.
                    shutil.move(str(layout), output / "ui-two-instances-layout.ini")
                original = Path(os.environ["XDG_CONFIG_HOME"]) / "plasmawindowedrc"
                if original.is_file():
                    shutil.copyfile(original, output / "ui-original-windowed-settings.ini")
            environment = dict(os.environ, LD_PRELOAD=str(output / "preferences-host.so"),
                IRIX_DOMAINOS_PREFERENCES_TEST="1", IRIX_DOMAINOS_PREFERENCES_MODE=mode,
                IRIX_DOMAINOS_PREFERENCES_REPORT=str(output / (mode + ".json" if ui else "native.json")),
                IRIX_DOMAINOS_PREFERENCES_DIR=str(output),
                IRIX_DOMAINOS_PRODUCTION_TRAY_PAGE=str(Path(os.environ["XDG_DATA_HOME"]) / "plasma/plasmoids/org.irixclassic.domainos.panel/contents/ui/ConfigTray.qml"))
            result = subprocess.run(["plasmawindowed", "org.irixclassic.domainos.panel"], env=environment,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=35)
            (output / (mode + ".log" if ui else "host.log")).write_text(result.stdout)
            outcomes.append(result.returncode)
            if result.returncode:
                break
        return 0 if all(code == 0 for code in outcomes) and len(outcomes) == len(modes) else 1
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(3)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(3)
        for log in logs:
            log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True, help="New directory under /tmp")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--descartar",action="store_true",help="Testar Cancelar/Descartar nativos e reabrir, sem aplicar a edição")
    parser.add_argument("--somente-rota", action="store_true", help="Verificar signal configureRequested de main.qml, proprietário e 9 categorias, sem editar políticas")
    parser.add_argument("--clique-fisico", action="store_true", help="Com --somente-rota, testar também os cliques físicos da gaveta")
    parser.add_argument("--painel-ui", action="store_true", help="Testar gaveta/Preferências/Iconbox/Apply/Cancelar/Descartar físicos, outra instância, reabertura e persistência após reiniciar o host privado")
    parser.add_argument("--perfil-privado", type=Path, help="Novo diretório de perfil sob o repositório, para manter cache fora de /tmp")
    parser.add_argument("--runtime-privado", type=Path, help="Novo diretório curto sob /tmp para sockets privados, mantendo o cache no perfil")
    args = parser.parse_args(); output = args.saida.resolve()
    if args.worker:
        return worker(output)
    if args.somente_rota and args.descartar:
        parser.error("Escolha --somente-rota ou --descartar")
    if args.clique_fisico and not args.somente_rota:
        parser.error("--clique-fisico requer --somente-rota")
    if args.painel_ui and (args.somente_rota or args.descartar or args.clique_fisico):
        parser.error("--painel-ui tem seu próprio percurso físico; não combine com outros modos")
    if not output.is_relative_to(Path("/tmp")) or output.exists():
        parser.error("Use a new directory under /tmp")
    profile = args.perfil_privado.resolve() if args.perfil_privado else output
    if args.perfil_privado:
        if not profile.is_relative_to(REPO) or profile.exists():
            parser.error("--perfil-privado deve indicar um novo diretório sob o repositório")
        profile.mkdir(mode=0o700)
    output.mkdir(mode=0o700)
    protected = [Path.home() / ".config" / name for name in ("kdeglobals", "plasmarc", "kwinrc", "plasma-org.kde.plasma.desktop-appletsrc")]
    config_before = {str(path): digest(path) for path in protected}
    sources = [APPLET / "contents/config/main.xml", APPLET / "contents/config/config.qml", APPLET / "contents/ui/main.qml", *sorted((APPLET / "contents/ui").glob("Config*"))]
    before = {str(path): digest(path) for path in sources}
    configured_pages = re.findall(r'source:\s*"(Config[^"/]+\.qml)"', (APPLET / "contents/config/config.qml").read_text())
    environment = os.environ.copy()
    for name in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "LD_PRELOAD", "XDG_SESSION_ID", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XAUTHORITY"):
        environment.pop(name, None)
    paths = {key: profile / name for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
        ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime"))}
    if args.runtime_privado:
        runtime = args.runtime_privado.resolve()
        if not runtime.is_relative_to(Path("/tmp")) or runtime.exists() or len(os.fsencode(runtime)) > 64:
            parser.error("--runtime-privado deve indicar novo diretório curto sob /tmp (até 64 bytes)")
        paths["XDG_RUNTIME_DIR"] = runtime
    for key, path in paths.items():
        path.mkdir(mode=0o700); environment[key] = str(path)
    plasmoids = paths["XDG_DATA_HOME"] / "plasma/plasmoids"; plasmoids.mkdir(parents=True)
    for name in ("org.irixclassic.domainos.panel", "org.irixclassic.grosview"):
        shutil.copytree(REPO / "plasma/applets" / name, plasmoids / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("IrixClassic", "IrixClassicDomainOS"):
        shutil.copytree(REPO / "plasma" / name, paths["XDG_DATA_HOME"] / "plasma/desktoptheme" / name)
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Test"], text=True))
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(REPO / "plasma/tests/domainos-preferences-host.cpp"), "-o", str(output / "preferences-host.so"), *flags, "-ldl"], check=True)
    (paths["XDG_CONFIG_HOME"] / "kwinrc").write_text("[Desktops]\nNumber=1\nName_1=Private configuration test\n[Compositing]\nEnabled=false\n")
    (paths["XDG_CONFIG_HOME"] / "kdeglobals").write_text((REPO / "colors/DomainOS-SR10.4.colors").read_text())
    (paths["XDG_CONFIG_HOME"] / "plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
    environment.update(XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", XDG_CURRENT_DESKTOP="NONE", XDG_SESSION_TYPE="x11", QT_QPA_PLATFORM="xcb", QT_QPA_PLATFORMTHEME="kde", QT_QUICK_BACKEND="software", KWIN_COMPOSE="N", LIBGL_ALWAYS_SOFTWARE="1", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(paths["XDG_RUNTIME_DIR"] / "no-system-bus"), PULSE_SERVER="unix:" + str(paths["XDG_RUNTIME_DIR"] / "no-audio-server"), IRIX_DOMAINOS_TRAY_CONFIG_PRIVATE_SESSION="1")
    # Keep the normal QML cache policy inside this fresh private XDG cache;
    # disabling it breaks enum initialization in Kirigami PromptDialog.
    environment.pop("QML_DISABLE_DISK_CACHE", None)
    # KIO/QLocalServer socket names can exceed the Unix socket path limit when
    # a private profile is beneath a long repository path. The compiler keeps
    # the caller's TMPDIR; only these private GUI workers use the short runtime.
    if args.runtime_privado:
        environment["TMPDIR"] = str(paths["XDG_RUNTIME_DIR"])
    environment["IRIX_DOMAINOS_PREFERENCES_MODE"]=("tray-routing-physical" if args.clique_fisico else "tray-routing") if args.somente_rota else "tray-discard" if args.descartar else "tray-production"
    if args.painel_ui:
        environment["IRIX_DOMAINOS_PANEL_UI_TEST"] = "1"
    bus = output / "private-bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    result = subprocess.run(["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1300x950x24", "dbus-run-session", "--config-file=" + str(bus), "--", sys.executable, str(Path(__file__).resolve()), "--saida", str(output), "--worker"], env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=85 if args.painel_ui else 45)
    (output / "session.log").write_text(result.stdout)
    native = json.loads((output / "native.json").read_text()) if (output / "native.json").is_file() else {}
    log = (output / "host.log").read_text() if (output / "host.log").is_file() else result.stdout
    diagnostics = [line for line in log.splitlines() if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop detected|is not a type|error when loading applet", line)]
    native_items = native.get("native_provider_items", [])
    items_after = native.get("native_provider_items_after_apply", [])
    volume = next((item for item in items_after if item.get("id") == "org.kde.plasma.volume"), {})
    config_after = {str(path): digest(path) for path in protected}
    checks = {
        "production_host_exited": result.returncode == 0 and not native.get("failure"),
        "production_qaction_bridge_present": native.get("production_bridge_present") is True,
        "real_provider_ids_and_titles_available": len(native_items) >= 2 and all(item.get("id") and item.get("title") for item in native_items) and any(item["id"] == "org.kde.plasma.volume" for item in native_items),
        "configuration_requested_for_production_instance": native.get("production_configuration_requested") is True and native.get("production_config_view_visible") is True,
        "pinned_preferences_uses_distinct_panel_action": native.get("production_pinned_configuration_route_invoked") is True and native.get("production_configuration_action_distinct_from_tray") is True,
        "preferences_dialog_owner_is_panel": native.get("production_config_applet_id") == native.get("production_applet_id"),
        "panel_preferences_show_all_nine_categories": panel_categories_match(native.get("production_config_categories", []), configured_pages),
        "tray_category_and_page_load": native.get("production_tray_category_opened") is True and native.get("production_tray_page_loaded") is True,
        "cross_engine_snapshot_matches_native_providers": native.get("production_snapshot_available") is True and native.get("provider_titles_received") is True,
        "policy_edit_does_not_apply_early": native.get("configuration_map_available") is True and native.get("production_policy_edited") is True and native.get("saved_hidden_before_edit") == native.get("saved_hidden_before_apply") == [],
        "real_native_apply_persists_owned_policy": native.get("production_real_apply_mouse_click") is True and native.get("saved_hidden_after_apply") == ["org.kde.plasma.volume"],
        "native_tray_receives_owned_policy": volume.get("hidden") is True,
        "production_capture_saved": native.get("production_capture_saved") is True,
        "qml_runtime_errors_zero": not diagnostics,
        "production_preferences_sources_unchanged": before == {str(path): digest(path) for path in sources},
        "real_desktop_preferences_unchanged": config_before == config_after,
    }
    if args.descartar:
        items_after=native.get("native_provider_items_after_discard",[])
        volume=next((item for item in items_after if item.get("id")=="org.kde.plasma.volume"),{})
        checks.pop("real_native_apply_persists_owned_policy")
        checks.pop("native_tray_receives_owned_policy")
        checks.update({
            "native_cancel_button_clicked":native.get("production_real_cancel_mouse_click") is True,
            "native_discard_confirmation_clicked":native.get("production_real_discard_mouse_click") is True,
            "native_dialog_closed_after_discard":native.get("native_config_closed_after_discard") is True,
            "discard_does_not_write_owned_policy":native.get("saved_hidden_before_discard")==native.get("saved_hidden_after_discard")==native.get("saved_hidden_after_reopen")==[],
            "native_config_reopens_with_saved_policy":native.get("native_config_reopened") is True and native.get("reopened_page_uses_saved_policy") is True,
            "other_native_instance_preserves_policy":native.get("second_production_instance_created") is True and native.get("second_instance_id")==101 and native.get("production_applet_id")!=101 and native.get("second_hidden_before_discard")==native.get("second_hidden_after_discard")==native.get("second_hidden_after_reopen")==[],
            "discard_preserves_native_provider_visibility":volume.get("hidden") is False,
        })
    if args.somente_rota:
        checks = {name: checks[name] for name in (
            "production_host_exited", "production_qaction_bridge_present",
            "real_provider_ids_and_titles_available", "configuration_requested_for_production_instance",
            "pinned_preferences_uses_distinct_panel_action", "preferences_dialog_owner_is_panel",
            "panel_preferences_show_all_nine_categories", "production_preferences_sources_unchanged",
            "real_desktop_preferences_unchanged")}
        checks.update({
            "configuration_requested_through_main_qml_signal": native.get("production_pinned_configuration_route_invoked") is True,
            "opening_preferences_preserves_policy": native.get("saved_hidden_before_open") == native.get("saved_hidden_after_open") == [],
            "panel_preferences_capture_saved": native.get("production_initial_preferences_capture_saved") is True,
            "domainos_qml_runtime_errors_zero": not any("org.irixclassic.domainos.panel/" in line for line in diagnostics),
        })
        if args.clique_fisico:
            checks["pinned_preferences_entry_clicked_physically"] = native.get("production_pinned_drawer_open_requested") is True and native.get("production_pinned_preferences_physical_click") is True
    ui_reload = {}
    if args.painel_ui:
        native = json.loads((output / "panel-ui-edit.json").read_text()) if (output / "panel-ui-edit.json").is_file() else {}
        ui_reload = json.loads((output / "panel-ui-reload.json").read_text()) if (output / "panel-ui-reload.json").is_file() else {}
        log = "\n".join(path.read_text() for path in (output / "panel-ui-edit.log", output / "panel-ui-reload.log") if path.is_file())
        diagnostics = [line for line in log.splitlines() if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop detected|is not a type|error when loading applet", line)]
        initial = native.get("initial_configuration", {})
        expected = dict(initial, tasksOnlyCurrentScreen=True)
        applied = native.get("configuration_after_apply", {})
        other = native.get("second_configuration_before_edit", {})
        actual_filter = native.get("task_filter_after_apply", {})
        reloaded_filter = ui_reload.get("reloaded_task_filter", {})
        filter_fields = ("controllerAvailable", "viewAvailable", "scopeAvailable", "controllerOnlyCurrentScreen", "viewFilterByScreen", "scopeFilterByScreen")
        checks = {
            "private_hosts_exit_cleanly": result.returncode == 0 and bool(native) and bool(ui_reload) and not native.get("failure") and not ui_reload.get("failure"),
            "configuration_action_distinct_from_tray": native.get("configuration_action_distinct_from_tray") is True,
            "drawer_button_clicked_physically": native.get("drawer_button_physical_click") is True,
            "preferences_entry_clicked_physically": native.get("preferences_entry_physical_click") is True,
            "config_view_owner_is_panel": native.get("config_view_owner_id") == native.get("production_applet_id") and native.get("production_applet_id") is not None,
            "preferences_show_nine_panel_categories": panel_categories_match(native.get("config_categories", []), configured_pages),
            "iconbox_category_clicked_physically": native.get("iconbox_category_physical_click") is True and native.get("iconbox_page_loaded") is True and Path(str(native.get("iconbox_current_source", ""))).name == "ConfigIconbox.qml",
            "screen_checkbox_clicked_physically": native.get("screen_checkbox_physical_click") is True and initial.get("tasksOnlyCurrentScreen") is False and native.get("page_screen_preference_after_edit") is True,
            "editing_waits_for_apply": bool(initial) and native.get("configuration_before_apply") == initial,
            "apply_button_clicked_physically": native.get("apply_button_physical_click") is True,
            "apply_changes_only_chosen_preference": applied == expected,
            "apply_button_resets_after_save": native.get("apply_button_disabled_after_apply") is True,
            "native_task_providers_receive_preference": all(actual_filter.get(key) is True for key in filter_fields),
            "second_real_instance_has_distinct_id": native.get("second_instance_created") is True and native.get("second_instance_id") == 101 and native.get("second_instance_id") != native.get("production_applet_id"),
            "second_instance_keeps_entire_configuration": bool(other) and other.get("tasksOnlyCurrentScreen") is False and native.get("second_configuration_before_apply") == other and native.get("second_configuration_after_apply") == other,
            "unsaved_edit_waits_for_apply": native.get("unsaved_checkbox_physical_click") is True and native.get("page_screen_preference_unsaved") is False and native.get("configuration_before_discard") == applied,
            "cancel_and_discard_clicked_physically": native.get("cancel_button_physical_click") is True and native.get("discard_button_physical_click") is True and native.get("configuration_window_closed_after_discard") is True,
            "discard_preserves_entire_saved_configuration": bool(applied) and native.get("configuration_after_discard") == applied and native.get("second_configuration_after_discard") == other,
            "preferences_reopened_physically": native.get("reopen_drawer_physical_click") is True and native.get("reopen_preferences_physical_click") is True and native.get("reopened_config_view_owner_id") == native.get("production_applet_id"),
            "reopened_page_restores_saved_preference": native.get("reopened_iconbox_category_physical_click") is True and native.get("reopened_iconbox_page_loaded") is True and native.get("reopened_screen_preference") is True and native.get("reopened_configuration") == applied and native.get("reopened_apply_button_disabled") is True,
            "preferences_survive_private_host_restart": bool(applied) and ui_reload.get("reloaded_configuration") == applied,
            "native_task_providers_restore_preference": all(reloaded_filter.get(key) is True for key in filter_fields),
            "captures_saved": native.get("preferences_capture_saved") is True and native.get("applied_capture_saved") is True and native.get("reopened_capture_saved") is True,
            "domainos_qml_runtime_errors_zero": not any("org.irixclassic.domainos.panel/" in line for line in diagnostics),
            "qml_runtime_errors_zero": not diagnostics,
            "production_preferences_sources_unchanged": before == {str(path): digest(path) for path in sources},
            "real_desktop_preferences_unchanged": config_before == config_after,
        }
    report = {"format": 1, "status": "passed" if all(checks.values()) else "failed", "checks": checks,
        "native": native, "qml_diagnostics": diagnostics, "native_dialog_property_scope_warnings": [line for line in log.splitlines() if "Setting initial properties failed:" in line or "Created graphical object was not placed" in line], "real_profiles_modified": False,
        "real_profile_hashes": {"before": config_before, "after": config_after},
        "scope":"Native Plasma ConfigView owning production DomainOS. Real Cancel and Discard pointer clicks, re-opened saved policy and distinct native applet ID 101; no Apply" if args.descartar else "Native production tray ConfigView and real Apply pointer click"}
    if args.somente_rota:
        report["scope"] = ("Pinned drawer Preferences routing with physical pointer clicks" if args.clique_fisico else "Main.qml configureRequested signal routing; physical pinned entry click NOT verified") + ": owning panel ID, nine panel categories plus optional installed native calendar configuration UIs, unchanged configuration. No policy edit or Apply verified."
        report["status"] = ("routing-verified-with-framework-diagnostics" if diagnostics else "routing-verified") if all(checks.values()) else "failed"
        report["framework_qml_diagnostics"] = [line for line in diagnostics if "org.irixclassic.domainos.panel/" not in line]
    if args.painel_ui:
        report["reload"] = ui_reload
        report["scope"] = "Production main.qml: physical drawer button, pinned Preferences entry, Iconbox category, checkbox and native Apply, then another unsaved edit followed by physical Cancel/Discard and re-opening the same page. Checks only the chosen configuration key changes, actual TaskManager providers, independent real applet ID 101 and persisted settings after restarting the private host. No real profile modified."
        report["framework_qml_diagnostics"] = [line for line in diagnostics if "org.irixclassic.domainos.panel/" not in line]
        if checks.get("domainos_qml_runtime_errors_zero") and not checks["qml_runtime_errors_zero"] and all(ok for name, ok in checks.items() if name != "qml_runtime_errors_zero"):
            report["status"] = "functional-verified-with-framework-diagnostics"
    (output / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "failed": [name for name, ok in checks.items() if not ok], "report": str(output / "RESULTADO.json")}))
    if args.somente_rota and all(checks.values()) and diagnostics:
        return 2  # Route verified; native framework diagnostics remain unresolved.
    if args.painel_ui and report["status"] == "functional-verified-with-framework-diagnostics":
        return 2
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
