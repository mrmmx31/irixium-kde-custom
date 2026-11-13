#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native DomainOS decoration actions in an owned Xvfb → Xephyr → KWin session."""
import argparse
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
from common import hashes, prepare, protected_paths, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    args = parser.parse_args()
    protected = protected_paths(); before = hashes(protected)
    env = prepare(args.saida, graphical=True)
    output = args.saida.absolute()
    config = "[org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae\ntheme=domainos_sr104\n[Compositing]\nEnabled=false\n[Windows]\nTitlebarDoubleClickCommand=Maximize\n"
    (output / "config/kwinrc").write_text(config)
    (output / "config/kdeglobals").write_text("[General]\nwidgetStyle=Fusion\n")
    processes = []; logs = []; checks = []; app = None; windows = []
    def start(name, arguments, environment):
        stream = (output / (name + ".log")).open("w"); logs.append(stream)
        process = subprocess.Popen(arguments, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        processes.append(process)
        return process
    def command(*arguments):
        return subprocess.run(arguments, env=env, capture_output=True, text=True, check=True, timeout=4).stdout.strip()
    def check(name, passed, detail=None):
        record = {"check": name, "passed": bool(passed)}
        if detail is not None: record["detail"] = detail
        checks.append(record)
        if not passed: raise AssertionError(record)
    def wait(predicate, seconds=4):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if app: app.processEvents()
            if predicate(): return True
            time.sleep(.015)
        return False
    def free_display():
        for _ in range(200):
            number = random.SystemRandom().randint(610, 1890)
            if not Path(f"/tmp/.X{number}-lock").exists() and not Path(f"/tmp/.X11-unix/X{number}").exists():
                return ":" + str(number)
        raise RuntimeError("No unused private display found")
    try:
        parent_display = free_display()
        outer_env = dict(env, DISPLAY=parent_display)
        xvfb = start("xvfb", ["Xvfb", parent_display, "-screen", "0", "1440x1000x24", "-ac", "-nolisten", "tcp"], outer_env)
        check("owned Xvfb ready", wait(lambda: xvfb.poll() is None and subprocess.run(["xdpyinfo"], env=outer_env, capture_output=True).returncode == 0))
        private_display = free_display()
        xephyr = start("xephyr", ["Xephyr", private_display, "-screen", "1200x820", "-ac", "-nolisten", "tcp", "-noreset", "-br"], outer_env)
        env["DISPLAY"] = private_display
        check("owned nested Xephyr ready", wait(lambda: xephyr.poll() is None and subprocess.run(["xdpyinfo"], env=env, capture_output=True).returncode == 0))
        bus = subprocess.Popen(["dbus-daemon", "--session", "--nofork", "--print-address=1"], env=env,
                               stdout=subprocess.PIPE, stderr=(output / "dbus.log").open("w"), text=True)
        processes.append(bus)
        address = bus.stdout.readline().strip()
        check("owned private session bus", address.startswith("unix:"))
        env["DBUS_SESSION_BUS_ADDRESS"] = address
        os.environ.clear(); os.environ.update(env)
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
        app = QApplication([]); app.setQuitOnLastWindowClosed(False)
        kwin = start("kwin", ["kwin_x11"], env)
        check("owned KWin ready", wait(lambda: kwin.poll() is None and subprocess.run(["qdbus6", "org.kde.KWin", "/KWin"], env=env, capture_output=True).returncode == 0, 10))
        command("xsetroot", "-solid", "#475e78")
        class TestWindow(QWidget):
            def __init__(self, title):
                super().__init__(); self.closed = False; self.setWindowTitle(title)
                self.setStyleSheet("background:#78a0d5;color:white;font-family:monospace;font-size:15px")
                layout = QVBoxLayout(self); layout.addWidget(QLabel("Somente esta janela de teste pertence ao teste.\n\nDomínio: DomainOS SR10.4 / HP VUE\n\nMenu: clique simples abre; duplo fecha.\nMinimizar e maximizar: ação na soltura."))
                self.resize(580, 300)
            def closeEvent(self, event):
                self.closed = True; super().closeEvent(event)
        window = TestWindow("DomainOS SR10.4 — ações nativas A"); window.move(100, 130); window.show(); windows.append(window)
        companion = TestWindow("DomainOS SR10.4 — janela inativa B"); companion.move(540, 400); companion.resize(490, 220); companion.show(); windows.append(companion)
        def prop(widget, name):
            try: return command("xprop", "-id", str(int(widget.winId())), name)
            except subprocess.CalledProcessError: return ""
        check("both windows belong to this test process", all(str(os.getpid()) in prop(widget, "_NET_WM_PID") for widget in windows))
        check("native frame extents correspond to DomainOS", wait(lambda: "11, 11, 30, 11" in prop(window, "_NET_FRAME_EXTENTS")), prop(window, "_NET_FRAME_EXTENTS"))
        fixed=TestWindow("DomainOS — diálogo sem redimensionamento")
        fixed.setFixedSize(310,180); fixed.move(720,120); fixed.show(); windows.append(fixed)
        check("fixed-size native dialog has thin extents", wait(lambda: "6, 6, 25, 6" in prop(fixed,"_NET_FRAME_EXTENTS")), prop(fixed,"_NET_FRAME_EXTENTS"))
        restricted=TestWindow("DomainOS — redimensiona sem maximizar")
        restricted.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)
        restricted.move(650,580); restricted.show(); windows.append(restricted)
        # Qt can hide its maximize button without restricting the WM function.
        # Set the actual Motif hint on this owned test window: resize/move/
        # minimize/close allowed, maximize denied, as a separate capability.
        command("xprop","-id",str(int(restricted.winId())),"-f","_MOTIF_WM_HINTS","32c",
            "-set","_MOTIF_WM_HINTS","1, 46, 0, 0, 0")
        # KWin may retain maximize in its WM operations despite that client
        # hint. The real native proof here concerns resizing and frame extent;
        # Surface tests separately exercise the supplied maximizeable=false.
        check("native Motif hint does not disable resizing", wait(lambda:
            "_NET_WM_ACTION_RESIZE" in prop(restricted,"_NET_WM_ALLOWED_ACTIONS")),
            prop(restricted,"_MOTIF_WM_HINTS"))
        check("resizable native window with restricted Motif hint keeps thick extents", wait(lambda: "11, 11, 30, 11" in prop(restricted,"_NET_FRAME_EXTENTS")), prop(restricted,"_NET_FRAME_EXTENTS"))
        def activate(widget):
            command("xdotool", "windowactivate", "--sync", str(int(widget.winId())))
            app.processEvents(); time.sleep(.05)
        def frame(widget):
            geometry = command("xdotool", "getwindowgeometry", "--shell", str(int(widget.winId())))
            fields = dict(line.split("=", 1) for line in geometry.splitlines() if "=" in line)
            values = [int(v) for v in re.findall(r"\d+", prop(widget, "_NET_FRAME_EXTENTS").split("=", 1)[-1])]
            left, right, top, bottom = values
            return int(fields["X"])-left, int(fields["Y"])-top, int(fields["WIDTH"])+left+right, int(fields["HEIGHT"])+top+bottom
        def position(widget, kind):
            x, y, width, height = frame(widget)
            maximized = "_NET_WM_STATE_MAXIMIZED_HORZ" in prop(widget, "_NET_WM_STATE")
            top = 0 if maximized else 10
            horizontal = {"menu": 0 if maximized else 10, "minimize": width-(40 if maximized else 50), "maximize": width-(20 if maximized else 30)}[kind]
            return x+horizontal+10, y+top+10
        def pointer(widget, kind):
            # --sync waits for a motion event forever if the cursor already is
            # at the target (for example after closing the same window menu).
            x, y = position(widget, kind); command("xdotool", "mousemove", str(x), str(y))
            app.processEvents()
        def screenshot(name):
            app.processEvents(); time.sleep(.07)
            return app.primaryScreen().grabWindow(0).save(str(output / name))
        activate(window); check("native active/inactive screenshot", screenshot("native-active-inactive.png"))
        original = frame(window)
        title_rectangle = (original[0]+30, original[1]+10, original[2]-80, 19)
        title_normal = app.primaryScreen().grabWindow(0).toImage().copy(*title_rectangle)
        command("xdotool", "mousemove", str(original[0]+original[2]//2), str(original[1]+20), "mousedown", "1")
        check("native title held screenshot", screenshot("native-title-held.png"))
        title_held = app.primaryScreen().grabWindow(0).toImage().copy(*title_rectangle)
        check("native title press reverses painted relief", title_held != title_normal)
        command("xdotool", "mouseup", "1")
        check("native title release screenshot", screenshot("native-title-released.png"))
        check("native title release restores original relief", app.primaryScreen().grabWindow(0).toImage().copy(*title_rectangle) == title_normal)
        # The passive feedback must preserve KWin's configured double-click.
        command("xdotool", "click", "--repeat", "2", "--delay", "70", "1")
        check("native title double click still maximizes", wait(lambda: "_NET_WM_STATE_MAXIMIZED_HORZ" in prop(window, "_NET_WM_STATE")))
        pointer(window, "maximize"); command("xdotool", "click", "1")
        check("native title double-click maximization can restore", wait(lambda: "_NET_WM_STATE_MAXIMIZED_HORZ" not in prop(window, "_NET_WM_STATE")))
        pointer(window, "maximize"); command("xdotool", "mousedown", "1"); app.processEvents()
        check("native maximize not dispatched on press", "_NET_WM_STATE_MAXIMIZED_HORZ" not in prop(window, "_NET_WM_STATE"))
        check("native maximize held screenshot", screenshot("native-maximize-held.png"))
        command("xdotool", "mouseup", "1")
        check("native maximize dispatched on release", wait(lambda: "_NET_WM_STATE_MAXIMIZED_HORZ" in prop(window, "_NET_WM_STATE")))
        check("native maximized screenshot", screenshot("native-maximized.png"))
        pointer(window, "maximize"); command("xdotool", "click", "1")
        check("native restore dispatched", wait(lambda: "_NET_WM_STATE_MAXIMIZED_HORZ" not in prop(window, "_NET_WM_STATE")))
        pointer(window, "minimize"); command("xdotool", "mousedown", "1")
        check("native minimize not dispatched on press", "_NET_WM_STATE_HIDDEN" not in prop(window, "_NET_WM_STATE"))
        check("native minimize held screenshot", screenshot("native-minimize-held.png"))
        command("xdotool", "mouseup", "1")
        check("native minimize dispatched on release", wait(lambda: "_NET_WM_STATE_HIDDEN" in prop(window, "_NET_WM_STATE")))
        window.showNormal(); activate(window)
        check("native unminimize", wait(lambda: "_NET_WM_STATE_HIDDEN" not in prop(window, "_NET_WM_STATE")))
        pointer(window, "maximize"); command("xdotool", "mousedown", "1")
        command("xdotool", "mousemove", "--sync", "400", "600"); command("xdotool", "mouseup", "1")
        app.processEvents()
        check("native drag cancel does not maximize", "_NET_WM_STATE_MAXIMIZED_HORZ" not in prop(window, "_NET_WM_STATE"))
        x, y, width, height = frame(window)
        command("xdotool", "mousemove", "--sync", str(x+width-3), str(y+height-3), "mousedown", "1")
        command("xdotool", "mousemove", "--sync", str(x+width+63), str(y+height+42), "mouseup", "1")
        check("native border drag resize changes client dimensions", wait(lambda: frame(window)[2] != width or frame(window)[3] != height))
        check("native resized frame screenshot", screenshot("native-resized.png"))
        # Title input belongs to KWin. The decoration installs its title hit region.
        x, y, width, height = frame(window)
        command("xdotool", "mousemove", "--sync", str(x+width//2), str(y+20), "mousedown", "1")
        command("xdotool", "mousemove", "--sync", str(x+width//2+40), str(y+60), "mouseup", "1")
        check("native title moves window", wait(lambda: frame(window)[:2] != (x, y)))
        pointer(window, "menu"); command("xdotool", "click", "1")
        time.sleep(app.styleHints().mouseDoubleClickInterval()/1000 + .1); app.processEvents()
        visible_menus = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "kwin"], env=env, capture_output=True, text=True).stdout.strip()
        check("native single menu click opens KWin menu", bool(visible_menus))
        check("native menu screenshot", screenshot("native-menu.png"))
        command("xdotool", "key", "Escape"); app.processEvents()
        activate(companion)
        check("window A is inactive before double close", not window.isActiveWindow())
        pointer(window, "menu"); command("xdotool", "click", "--repeat", "2", "--delay", "70", "1")
        check("native double click closes originally inactive window", wait(lambda: window.closed))
        check("other native window remains open", not companion.closed and companion.isVisible())
        check("no pending KWin menu after double close", wait(lambda: not subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "kwin"], env=env, capture_output=True, text=True).stdout.strip()))
        activate(companion); pointer(companion, "menu"); command("xdotool", "click", "--repeat", "2", "--delay", "70", "1")
        check("native double click closes active window", wait(lambda: companion.closed))
        qml_errors = [line for line in (output / "kwin.log").read_text().splitlines()
                      if re.search(r"ReferenceError:|TypeError:|SyntaxError:|Binding loop|Cannot assign|is not a type|Type .+ unavailable", line)]
        check("no production QML errors in native KWin", not qml_errors, qml_errors)
    except Exception as error:
        checks.append({"check": "native test execution", "passed": False, "error": str(error)})
    finally:
        if app:
            for widget in windows: widget.close()
            app.processEvents()
        for child in reversed(processes):
            if child.poll() is None:
                child.terminate()
                try: child.wait(3)
                except subprocess.TimeoutExpired: child.kill(); child.wait()
        for log in logs: log.close()
        checks.append({"check": "only owned processes stopped", "passed": all(child.poll() is not None for child in processes)})
        checks.append({"check": "personal configuration and Classic package unchanged", "passed": hashes(protected) == before})
        report = {"scope": "Actual Aurorae decoration in own Xvfb/Xephyr/KWin/bus/HOME/XDG; only this process's QWidget clients targeted",
                  "checks": checks, "processes": [{"pid": child.pid, "exit": child.returncode} for child in processes],
                  "status": "passed" if all(c["passed"] for c in checks) else "failed"}
        write_json(output / "RESULTADO.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
