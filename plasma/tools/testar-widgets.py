#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Capture the five real applets in independent temporary Plasma hosts.

Requires plasmawindowed, C++, pkg-config (Qt6Widgets/Qt6Test), Xvfb,
dbus-run-session and Pillow. The test helper is compiled only into the output
directory. Three exported public Qt6Quick methods are resolved dynamically;
this is an optional test ABI adapter, not an installed runtime dependency.
The native host checks loading and click feedback, not a user's panel layout,
all window-manager actions or live network changes. Optional --window-tasks
adds genuine active/inactive/minimized window task checks with private kwin_x11
and three disposable Qt windows, without opening installed applications.
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
import tempfile
import time

from PIL import Image, ImageChops


REPO = Path(__file__).resolve().parents[2]
WIDGETS = ("applications", "quicklaunch", "iconbox", "systemtray", "analogclock")
FIXTURE_APPS = (("editor", "Editor", "org.kde.kate"),
                ("files", "Files", "folder"),
                ("terminal", "Terminal", "utilities-terminal"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    roots = (REPO / "plasma/applets", REPO / "plasma/IrixClassic")
    return {str(p.relative_to(REPO)): sha256(p) for root in roots
            for p in sorted(root.rglob("*")) if p.is_file()}


def set_fixture_default(path, entry_name, values):
    # Edit only the staged fixture, preserving all other package bytes.
    source = path.read_text()
    pattern = rf'(<entry name="{re.escape(entry_name)}"[^>]*>.*?<default>).*?(</default>)'
    updated, count = re.subn(pattern, lambda match: match[1] + ",".join(values) + match[2],
                            source, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"Fixture entry is missing or ambiguous: {entry_name}")
    path.write_text(updated)


def stage_fixture(root, widget):
    paths = {name: root / name for name in ("data", "config", "cache", "state", "runtime")}
    for path in paths.values():
        path.mkdir(parents=True)
    paths["runtime"].chmod(0o700)
    applets = paths["data"] / "plasma/plasmoids"
    applets.mkdir(parents=True)
    for source in sorted((REPO / "plasma/applets").iterdir()):
        if source.is_dir():
            shutil.copytree(source, applets / source.name)
    theme = paths["data"] / "plasma/desktoptheme/IrixClassic"
    shutil.copytree(REPO / "plasma/IrixClassic", theme)
    icons = paths["data"] / "icons"
    icons.mkdir()
    (icons / "IrixClassic-SGI").symlink_to(REPO / "icons/themes/IrixClassic-SGI", target_is_directory=True)
    (paths["config"] / "plasmarc").write_text("[Theme]\nname=IrixClassic\n")
    palette = (REPO / "colors/Irixium.colors").read_text()
    (paths["config"] / "kdeglobals").write_text(palette + "\n[Icons]\nTheme=IrixClassic-SGI\n")
    desktops = paths["data"] / "applications"
    desktops.mkdir()
    launchers = []
    for identifier, name, icon in FIXTURE_APPS:
        filename = f"org.irixclassic.fixture.{identifier}.desktop"
        (desktops / filename).write_text(
            f"[Desktop Entry]\nType=Application\nName={name}\nExec=/bin/false\n"
            f"Icon={icon}\nCategories=Utility;\n")
        launchers.append(f"applications:{filename}")
    overrides = []
    if widget in ("iconbox", "quicklaunch"):
        entry = "launchers" if widget == "iconbox" else "launcherUrls"
        path = applets / f"org.irixclassic.{widget}/contents/config/main.xml"
        set_fixture_default(path, entry, launchers)
        overrides.append({"file": str(path.relative_to(root)), "entry": entry, "values": launchers})
    if widget == "systemtray":
        path = applets / "org.irixclassic.systemtray/contents/ui/main.qml"
        source = path.read_text()
        if 'objectName: "classicTray"' not in source:
            source, count = re.subn(r"(\n\s*id: root\s*\n)",
                                   r'\1    objectName: "classicTray"\n', source, count=1)
            if count != 1:
                raise RuntimeError("Tray fixture cannot locate its root")
            path.write_text(source)
            overrides.append({"file": str(path.relative_to(root)), "objectName": "classicTray"})
    return paths, overrides


def environment(paths):
    env = os.environ.copy()
    for name in ("LD_PRELOAD", "DBUS_SESSION_BUS_ADDRESS", "QML_IMPORT_PATH", "QML2_IMPORT_PATH",
                 "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "WAYLAND_DISPLAY"):
        env.pop(name, None)
    env.update({"XDG_DATA_HOME": str(paths["data"]), "XDG_CONFIG_HOME": str(paths["config"]),
                "XDG_CACHE_HOME": str(paths["cache"]), "XDG_STATE_HOME": str(paths["state"]),
                "XDG_RUNTIME_DIR": str(paths["runtime"]), "XDG_CONFIG_DIRS": "/etc/xdg",
                "XDG_DATA_DIRS": "/usr/local/share:/usr/share", "QT_QPA_PLATFORM": "xcb",
                "QT_QPA_PLATFORMTHEME": "generic", "XDG_CURRENT_DESKTOP": "NONE",
                "QT_ACCESSIBILITY": "0", "QSG_RHI_BACKEND": "software",
                "QT_QUICK_BACKEND": "software", "LIBGL_ALWAYS_SOFTWARE": "1"})
    return env


def private_bus_config(path):
    # No service directories: the fixture cannot activate user/system daemons.
    path.write_text('''<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
"http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>
<policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy>
</busconfig>\n''')


def window_environment(paths):
    env = environment(paths)
    for name in ("DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER",
                 "XDG_SESSION_ID", "XDG_SESSION_PATH", "XDG_SEAT_PATH", "XDG_SEAT",
                 "DESKTOP_SESSION", "KDE_FULL_SESSION", "KDE_SESSION_VERSION"):
        env.pop(name, None)
    env.update({"DBUS_SYSTEM_BUS_ADDRESS": "unix:path=" + str(paths["runtime"] / "no-system-bus"),
                "XDG_SESSION_TYPE": "x11", "IRIX_PRIVATE_TASK_FIXTURE": "1", "KWIN_COMPOSE": "N"})
    return env


def window_session(job_path):
    """Internal child, already inside the fixture's Xvfb and non-activating bus."""
    job = json.loads(job_path.read_text())
    paths = {name: Path(value) for name, value in job["paths"].items()}
    if os.environ.get("IRIX_PRIVATE_TASK_FIXTURE") != "1" or not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        raise RuntimeError("Window task session must run under its private fixture launcher")
    for key, name in (("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"),
                      ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        if os.environ.get(key) != str(paths[name]):
            raise RuntimeError("Window task fixture has an unexpected XDG path")
    processes, streams = [], []
    output = Path(job["output"])
    try:
        kwin_log = (output / "kwin.log").open("w")
        streams.append(kwin_log)
        kwin = subprocess.Popen(["kwin_x11", "--replace"], stdout=kwin_log, stderr=subprocess.STDOUT)
        processes.append(kwin)
        deadline = time.monotonic() + 10
        while True:
            if kwin.poll() is not None:
                raise RuntimeError("Private kwin_x11 exited during initialization")
            state = subprocess.run(["xprop", "-root", "_NET_SUPPORTING_WM_CHECK"],
                                   capture_output=True, text=True)
            if state.returncode == 0 and re.search(r"0x[1-9a-fA-F][0-9a-fA-F]*", state.stdout):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("Private kwin_x11 did not claim its Xvfb display")
            time.sleep(.05)
        windows = []
        for identifier, name, _ in FIXTURE_APPS:
            desktop_id = "org.irixclassic.fixture." + identifier
            ready_file = output / (identifier + ".ready.json")
            log_file = output / (identifier + ".log")
            ready = ready_file.open("w")
            log = log_file.open("w")
            streams.extend((ready, log))
            process = subprocess.Popen([job["window_helper"], "--desktop-id", desktop_id,
                                        "--window-title", "IRIX disposable " + name], stdout=ready, stderr=log)
            processes.append(process)
            deadline = time.monotonic() + 8
            while not ready_file.stat().st_size:
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Disposable Qt window did not report readiness: " + identifier)
                time.sleep(.05)
            record = json.loads(ready_file.read_text())
            if not record.get("ready") or record.get("desktop_id") != desktop_id or record.get("pid") != process.pid:
                raise RuntimeError("Disposable window identity is inconsistent: " + identifier)
            windows.append(record)
        manifest = output / "windows.json"
        manifest.write_text(json.dumps(windows, indent=2) + "\n")
        subprocess.run(["xdotool", "mousemove", "1270", "790"], check=True)
        # Only the applet host receives the test preload. KWin and disposable
        # windows remain ordinary native Qt/X11 clients on the private bus.
        env = os.environ.copy()
        env.update({"LD_PRELOAD": job["capture_helper"], "IRIX_TEST_WINDOW_TASKS": "1",
                    "IRIX_TEST_WINDOWS": str(manifest), "IRIX_TEST_CAPTURE": job["capture"],
                    "IRIX_TEST_REPORT": job["report"], "IRIX_TEST_WIDGET": "iconbox"})
        result = subprocess.run(["plasmawindowed", "org.irixclassic.iconbox"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=35)
        (output / "host.log").write_text(result.stdout)
        print(result.stdout, end="")
        return result.returncode
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=3)
        for stream in streams:
            stream.close()


def run_window_tasks(output, capture_helper, window_helper):
    work = output / "fixture-window-tasks"
    work.mkdir()
    paths, overrides = stage_fixture(work, "iconbox")
    (paths["config"] / "kwinrc").write_text(
        "[Compositing]\nEnabled=false\n[Windows]\nFocusPolicy=ClickToFocus\nFocusStealingPreventionLevel=0\n")
    bus_config = work / "private-bus.conf"
    private_bus_config(bus_config)
    capture = work / "window-tasks.png"
    report_file = work / "window-tasks.json"
    job_file = work / "job.json"
    job_file.write_text(json.dumps({"paths": {key: str(value) for key, value in paths.items()},
        "output": str(work), "capture_helper": str(capture_helper), "window_helper": str(window_helper),
        "capture": str(capture), "report": str(report_file)}, indent=2) + "\n")
    command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x800x24",
               "dbus-run-session", "--config-file", str(bus_config), "--",
               sys.executable, str(Path(__file__).resolve()), "--internal-window-session", str(job_file)]
    result = subprocess.run(command, env=window_environment(paths), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=55)
    (work / "session.log").write_text(result.stdout)
    report = json.loads(report_file.read_text()) if report_file.is_file() else {}
    failures = native_errors(result.stdout)
    if result.returncode:
        failures.append("Private window task session exited: " + str(result.returncode))
    if report.get("failure"):
        failures.append(report["failure"])
    if not report.get("native_tasks_model") or not report.get("captured") or not capture.is_file():
        failures.append("Missing native TasksModel or host capture")
    cases = report.get("window_tasks", [])
    if [case.get("state") for case in cases] != ["active", "inactive", "minimized"]:
        failures.append("Genuine active/inactive/minimized delegates were not all exercised")
    for case in cases:
        required = ("state_ready", "identity_verified", "real_window_delegate", "immediate_held_feedback",
                    "held_roles_unchanged", "held_settled_roles_unchanged", "held_settled_feedback",
                    "normal_capture", "pressed_capture", "cancel_clears_feedback",
                    "cancel_roles_unchanged", "cancel_task_geometry_unchanged", "action_press_feedback", "action_waited_for_release",
                    "release_action_verified", "release_clears_feedback", "x11_action_verified")
        if not all(case.get(key) for key in required) or "-pressed" not in case.get("pressed_prefix", ""):
            failures.append("Native window task feedback/action failed for " + case.get("state", "unknown"))
        if not case.get("cancel_task_geometry_unchanged"):
            failures.append("Native task geometry moved after cancellation for " + case.get("state", "unknown"))
        normal = Path(case.get("normal_capture_file", "/nonexistent"))
        pressed = Path(case.get("pressed_capture_file", "/nonexistent"))
        if normal.is_file() and pressed.is_file():
            difference = compare_task_captures(normal, pressed, case.get("task_rect"))
            case["image_difference"] = difference
            if difference["changed_pixels"] == 0:
                failures.append("Pressed task region did not change for " + case["state"])
        else:
            failures.append("Missing before/held captures for " + case.get("state", "unknown"))
    return {"status": "failed" if failures else "passed", "report": report,
            "fixture_overrides": overrides, "failures": failures, "log": str(work / "session.log"),
            "bus_service_activation": False, "system_bus_available": False,
            "host_full_desktop_containment": False, "home_unchanged": True,
            "private_bus_config_sha256": sha256(bus_config)}


def compare_task_captures(normal_path, pressed_path, rect):
    normal = Image.open(normal_path).convert("RGBA")
    pressed = Image.open(pressed_path).convert("RGBA")
    if normal.size != pressed.size or not isinstance(rect, list) or len(rect) != 4:
        raise RuntimeError("Task capture dimensions/rectangle are invalid")
    x, y, width, height = rect
    box = (max(0, int(x)), max(0, int(y)),
           min(normal.width, int(x + width + .999)), min(normal.height, int(y + height + .999)))
    if box[2] <= box[0] or box[3] <= box[1]:
        raise RuntimeError("Task rectangle lies outside the native capture")
    difference = ImageChops.difference(normal.crop(box).convert("RGB"), pressed.crop(box).convert("RGB"))
    changed = sum(any(pixel) for pixel in difference.getdata())
    return {"region": list(box), "changed_pixels": changed}


def native_errors(log):
    # Missing KWin/hardware/session services are expected on the isolated bus.
    # QML loading/type/reference failures are not allowed to pass as captures.
    return [line for line in log.splitlines() if re.search(
        r"(?:ReferenceError:|TypeError:|SyntaxError:|module .+ is not installed|"
        r"Type .+ unavailable|is not a type|Cannot assign to non-existent property|"
        r"Error loading QML file)", line)]


def run_widget(output, widget, helper):
    work = output / ("fixture-" + widget)
    work.mkdir()
    paths, overrides = stage_fixture(work, widget)
    capture = output / (widget + ".png")
    report_file = output / (widget + ".json")
    # The preload is set AFTER starting the new session bus, exclusively for
    # plasmawindowed. D-Bus helpers and Xvfb never receive it.
    command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x800x24",
               "dbus-run-session", "--", "env", "LD_PRELOAD=" + str(helper),
               "IRIX_TEST_CAPTURE=" + str(capture), "IRIX_TEST_REPORT=" + str(report_file),
               "IRIX_TEST_WIDGET=" + widget, "plasmawindowed", "org.irixclassic." + widget]
    result = subprocess.run(command, env=environment(paths), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    (output / (widget + ".log")).write_text(result.stdout)
    report = json.loads(report_file.read_text()) if report_file.is_file() else {}
    failures = native_errors(result.stdout)
    if result.returncode != 0:
        failures.append(f"Native host exit: {result.returncode}")
    if report.get("failure"):
        failures.append(report["failure"])
    if not capture.is_file() or not report.get("captured") or not report.get("public_quick_symbols"):
        failures.append("Missing native capture/report/public Qt Quick symbols")
    if widget == "systemtray" and not report.get("internal_systray"):
        failures.append("Native tray containment did not attach")
    if widget == "iconbox":
        if not all(report.get(key) for key in ("real_task_delegate", "held_feedback", "cancel_clears_feedback")):
            failures.append("Native task press/cancel feedback failed")
        if "-pressed" not in report.get("pressed_prefix", ""):
            failures.append("Native task did not select its pressed SVG state")
        pressed = Path(str(capture) + ".pressed.png")
        if not pressed.is_file() or not report.get("pressed_capture"):
            failures.append("Missing pressed native capture")
        elif capture.is_file():
            difference = compare_task_captures(capture, pressed, report.get("task_rect"))
            report["image_difference"] = difference
            if difference["changed_pixels"] == 0:
                failures.append("Task region did not change while pressed")
    return {"widget": widget, "status": "failed" if failures else "passed", "report": report,
            "fixture_overrides": overrides, "failures": failures, "log": str(output / (widget + ".log")),
            "capture": str(capture)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, help="New or empty output directory (default: /tmp)")
    parser.add_argument("--widget", action="append", choices=WIDGETS,
                        help="Test selected widget; default: all five")
    parser.add_argument("--window-tasks", action="store_true",
                        help="Also exercise genuine window delegates under private kwin_x11")
    parser.add_argument("--internal-window-session", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.internal_window_session:
        return window_session(args.internal_window_session)
    for program in ("c++", "pkg-config", "xvfb-run", "Xvfb", "dbus-run-session", "plasmawindowed"):
        if not shutil.which(program):
            parser.error("Required optional test tool is missing: " + program)
    if args.window_tasks:
        for program in ("kwin_x11", "xdotool", "xprop"):
            if not shutil.which(program):
                parser.error("Required optional window task tool is missing: " + program)
    output = args.saida.resolve() if args.saida else Path(tempfile.mkdtemp(prefix="irixclassic-native-"))
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    before = source_hashes()
    helper_source = REPO / "plasma/tests/capture-host.cpp"
    helper = output / "capture-host.so"
    flags = shlex.split(subprocess.check_output(
        ["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Test"], text=True))
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(helper_source),
                    "-o", str(helper), *flags, "-ldl"], check=True)
    window_tasks = None
    if args.window_tasks:
        window_helper = output / "fixture-window"
        subprocess.run(["c++", "-std=c++17", str(REPO / "plasma/tests/fixture-window.cpp"),
                        "-o", str(window_helper), *flags], check=True)
    results = []
    for widget in args.widget or WIDGETS:
        try:
            results.append(run_widget(output, widget, helper))
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
            results.append({"widget": widget, "status": "failed", "failures": [str(exc)]})
        print(widget + ": " + results[-1]["status"], flush=True)
    if args.window_tasks:
        try:
            window_tasks = run_window_tasks(output, helper, window_helper)
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
            window_tasks = {"status": "failed", "failures": [str(exc)]}
        print("window-tasks: " + window_tasks["status"], flush=True)
    unchanged = before == source_hashes()
    summary = {"format": 1, "status": "passed" if unchanged and all(
        result["status"] == "passed" for result in results) and (
        window_tasks is None or window_tasks["status"] == "passed") else "failed",
        "sources_unchanged": unchanged, "source_sha256": before,
        "helper_sha256": sha256(helper_source), "testing_only": True,
        "window_helper_sha256": sha256(REPO / "plasma/tests/fixture-window.cpp") if args.window_tasks else None,
        "qt_compiled": subprocess.check_output(["pkg-config", "--modversion", "Qt6Widgets"], text=True).strip(),
        "limitations": ["Independent X11/Xvfb applet hosts; does not certify a user's live panel layout.",
                        "No installed application launched; disposable Qt windows are used only with --window-tasks.",
                        "Real window actions are proved only with --window-tasks; ordinary iconbox capture uses a pinned launcher.",
                        "No live Wi-Fi/Bluetooth changes; native tray attachment and QML rendering are checked.",
                        "Optional test helper resolves three exported public Qt 6 Quick methods dynamically."],
        "widgets": results, "window_tasks": window_tasks}
    (output / "RESULTADO.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("Report: " + str(output / "RESULTADO.json"), flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
