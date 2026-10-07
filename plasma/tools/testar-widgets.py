#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Capture the five real applets in independent temporary Plasma hosts.

Requires plasmawindowed, C++, pkg-config (Qt6Widgets/Qt6Test), Xvfb,
dbus-run-session and Pillow. The test helper is compiled only into the output
directory. Three exported public Qt6Quick methods are resolved dynamically;
this is an optional test ABI adapter, not an installed runtime dependency.
The native host checks loading and click feedback, not a user's panel layout,
all window-manager actions or live network changes.
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
import tempfile

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
    args = parser.parse_args()
    for program in ("c++", "pkg-config", "xvfb-run", "Xvfb", "dbus-run-session", "plasmawindowed"):
        if not shutil.which(program):
            parser.error("Required optional test tool is missing: " + program)
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
    results = []
    for widget in args.widget or WIDGETS:
        try:
            results.append(run_widget(output, widget, helper))
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
            results.append({"widget": widget, "status": "failed", "failures": [str(exc)]})
        print(widget + ": " + results[-1]["status"], flush=True)
    unchanged = before == source_hashes()
    summary = {"format": 1, "status": "passed" if unchanged and all(
        result["status"] == "passed" for result in results) else "failed",
        "sources_unchanged": unchanged, "source_sha256": before,
        "helper_sha256": sha256(helper_source), "testing_only": True,
        "qt_compiled": subprocess.check_output(["pkg-config", "--modversion", "Qt6Widgets"], text=True).strip(),
        "limitations": ["Independent X11/Xvfb applet hosts; does not certify a user's live panel layout.",
                        "No real application launched; press is cancelled outside; fixture entries run /bin/false.",
                        "No live Wi-Fi/Bluetooth changes; native tray attachment and QML rendering are checked.",
                        "Optional test helper resolves three exported public Qt 6 Quick methods dynamically."],
        "widgets": results}
    (output / "RESULTADO.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("Report: " + str(output / "RESULTADO.json"), flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
