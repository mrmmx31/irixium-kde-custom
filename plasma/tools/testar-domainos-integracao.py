#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Smoke-test the shared functional composition in a private KDE backend.

The approved chassis loads native providers together without startup actions
or host changes. Gestures and provider actions have separate native tests.
"""
import argparse
import configparser
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


def worker(output):
    processes, logs = [], []
    try:
        for executable in ("kwin_x11", "kactivitymanagerd", "ksystemstats"):
            log = (output / (executable + ".log")).open("w"); logs.append(log)
            path=shutil.which(executable) or ("/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd" if executable=="kactivitymanagerd" else executable)
            processes.append(subprocess.Popen([path, *(["--remain"] if executable == "ksystemstats" else [])], stdout=log, stderr=subprocess.STDOUT))
        ready = False
        for _ in range(100):
            probe = subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"], capture_output=True, timeout=2)
            if probe.returncode == 0: ready = True; break
            time.sleep(.05)
        environment = dict(os.environ, LD_PRELOAD=str(output / "integration-host.so"),
            IRIX_DOMAINOS_INTEGRATION_CAPTURE=str(output / "functional-composition.png"),
            IRIX_DOMAINOS_INTEGRATION_REPORT=str(output / "state.json"))
        result = subprocess.run(["plasmawindowed", "org.irixclassic.domainos.panel"], env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=25)
        (output / "host.log").write_text(result.stdout)
        state = json.loads((output / "state.json").read_text()) if (output / "state.json").is_file() else {}
        errors = [message for message in result.stdout.splitlines() if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|module .+ is not installed|is not a type|Type .+ unavailable|Image: Cannot open", message)]
        checks = {
            "private_kwin_service_ready": ready,
            "native_plasma_host_exited_cleanly": result.returncode == 0,
            "functional_composition_loaded": state.get("functional_composition_loaded") is True,
            "live_phase_selected": state.get("phase") == "functional-integration",
            "real_time_connected_to_approved_date_face": state.get("timeAvailable") is True and state.get("date") not in ("—", "Feb 27\nThu"),
            "real_network_samples_connected_to_graph": state.get("sensors", {}).get("available") is True,
            "pager_reads_single_native_desktop_without_creating": state.get("workspaceCount") == 1,
            "no_startup_command_or_light": state.get("activity") == {"lit": False, "pending": 0} and state.get("commands") == {},
            "native_application_catalog_available": state.get("catalogCount", 0) > 0,
            "drawer_starts_independently_empty": state.get("pins") == [],
            "native_tasks_model_contains_host_window": state.get("taskProviderAvailable") is True and state.get("taskCount", 0) >= 1,
            "native_task_context_menu_compiles": state.get("nativeMenuReady") is True,
            "native_tray_containment_attached": state.get("tray", {}).get("available") is True,
            "native_tray_providers_preserved": "org.kde.plasma.volume" in state.get("tray", {}).get("visible", [])
                and state.get("tray", {}).get("notificationsAvailable") is True,
            "capture_saved": state.get("capture_saved") is True,
            "qml_runtime_errors_zero": not errors}
        popups=state.get("popup_windows", [])
        checks["help_failure_and_menus_escape_short_panel"] = len(popups)==4 and all(
            popup.get("opened") and popup.get("separate_window")
            and (popup.get("popup_height",0)<=109 or popup.get("extends_outside_host"))
            and popup.get("capture_saved") and popup.get("host_height")==109 for popup in popups)
        scheme = configparser.ConfigParser(interpolation=None)
        scheme.read(REPO / "colors/DomainOS-SR10.4.colors")
        expected = {role: "#" + "".join(f"{int(channel):02x}" for channel in scheme[section][key].split(",")[:3])
            for role, section, key in (("background", "Colors:Window", "BackgroundNormal"),
                ("recessed", "Colors:View", "BackgroundNormal"), ("text", "Colors:Window", "ForegroundNormal"),
                ("blue", "Colors:Selection", "BackgroundNormal"), ("white", "Colors:Selection", "ForegroundNormal"))}
        checks["shared_panel_follows_native_kde_palette"] = state.get("palette") == expected
        state["qml_errors"] = errors
        report = {"status": "passed" if all(checks.values()) else "failed", "checks": checks, "state": state,
            "scope": "Shared native Plasma composition; task/tray gestures, preferences and migration are validated separately"}
        (output / "NATIVO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        return 0 if all(checks.values()) else 1
    finally:
        for process in reversed(processes):
            process.terminate()
            try: process.wait(5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        for log in logs: log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(); output = args.saida.resolve()
    if args.worker: return worker(output)
    if not output.is_relative_to(Path("/tmp")) or output.exists(): parser.error("Use a new output directory under /tmp")
    output.mkdir(mode=0o700)
    env = os.environ.copy()
    config = Path(env.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    def hashes():
        return {name: hashlib.sha256((config / name).read_bytes()).hexdigest() if (config / name).is_file() else None
            for name in ("kdeglobals", "plasmarc", "kwinrc", "plasma-org.kde.plasma.desktop-appletsrc")}
    before = hashes()
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "LD_PRELOAD", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "XAUTHORITY", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XDG_SESSION_ID"):
        env.pop(key, None)
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        folder = output / name; folder.mkdir(mode=0o700); env[key] = str(folder)
    plasmoids = output / "data/plasma/plasmoids"
    plasmoids.mkdir(parents=True)
    for name in ("org.irixclassic.domainos.panel", "org.irixclassic.grosview"):
        shutil.copytree(REPO / "plasma/applets" / name, plasmoids / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("IrixClassic", "IrixClassicDomainOS"):
        shutil.copytree(REPO / "plasma" / name, output / "data/plasma/desktoptheme" / name)
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets"], text=True))
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(REPO / "plasma/tests/domainos-integration-host.cpp"),
        "-o", str(output / "integration-host.so"), *flags, "-ldl"], check=True)
    (output / "config/kwinrc").write_text("[Desktops]\nNumber=1\nName_1=Isolated test\n[Compositing]\nEnabled=false\n")
    (output / "config/kdeglobals").write_text((REPO / "colors/DomainOS-SR10.4.colors").read_text())
    (output / "config/plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
    env.update(XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg",
        QT_QPA_PLATFORM="xcb", QT_QPA_PLATFORMTHEME="kde", QT_QUICK_BACKEND="software", KWIN_COMPOSE="N", XDG_SESSION_TYPE="x11", XDG_CURRENT_DESKTOP="NONE", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(output / "no-system-bus"),
        PULSE_SERVER="unix:" + str(output / "no-audio-server"))
    bus = output / "bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    result = subprocess.run(["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1200x700x24", "dbus-run-session", "--config-file", str(bus), "--", sys.executable, str(Path(__file__).resolve()), "--saida", str(output), "--worker"], env=env, capture_output=True, text=True, timeout=40)
    (output / "native.log").write_text(result.stdout + result.stderr)
    report = json.loads((output / "NATIVO.json").read_text()) if (output / "NATIVO.json").is_file() else {"status": "failed", "failure": result.stderr}
    after = hashes()
    report["protected_configs"] = {"before": before, "after": after, "unchanged": before == after}
    report.setdefault("checks", {})["host_configs_unchanged"] = before == after
    report["status"] = "passed" if all(report["checks"].values()) and result.returncode == 0 else "failed"
    (output / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]), "result": str(output / "RESULTADO.json")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__": raise SystemExit(main())
