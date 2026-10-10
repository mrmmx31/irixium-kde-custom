#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Observe the native panel backdrop in an owned Xvfb/KWin/Plasma fixture.

Uses the activation harness's disposable profile and production CLI. Baseline
mode changes background hints only on its own newly created DomainOS panel to
validate the exposed KDE setter; fixed mode tests first creation and returning
from a saved panel made by a previous release. No style SVG is edited.
"""
import ast
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASELINE = "--baseline" in sys.argv
if BASELINE:
    sys.argv.remove("--baseline")
    os.environ["IRIX_DOMAINOS_BACKDROP_BASELINE"] = "1"
if "--interface-probe" in sys.argv:
    sys.argv.remove("--interface-probe")
    os.environ["IRIX_DOMAINOS_BACKDROP_INTERFACE"] = "1"
if "--qml-binding-probe" in sys.argv:
    sys.argv.remove("--qml-binding-probe")
    os.environ["IRIX_DOMAINOS_BACKDROP_QML_BINDING"] = "1"

PANEL_BACKGROUND_BINDING = '''
    readonly property bool soleDomainosPanel: Plasmoid.containment
        && Plasmoid.containment.pluginName === "org.kde.panel"
        && Plasmoid.containment.applets.length === 1
        && Plasmoid.containment.applets[0] === Plasmoid
    Binding {
        target: Plasmoid.containment
        property: "backgroundHints"
        value: PlasmaCore.Types.NoBackground
        when: host.soleDomainosPanel
        restoreMode: Binding.RestoreBindingOrValue
    }
'''


def maximize_owned_window(identifier, maximize):
    """Send the standard EWMH request on the fixture's private X11 display."""
    class Data(ctypes.Union):
        _fields_ = [("b", ctypes.c_char * 20), ("s", ctypes.c_short * 10), ("l", ctypes.c_long * 5)]

    class ClientMessage(ctypes.Structure):
        _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong), ("send_event", ctypes.c_int),
                    ("display", ctypes.c_void_p), ("window", ctypes.c_ulong), ("message_type", ctypes.c_ulong),
                    ("format", ctypes.c_int), ("data", Data)]

    class Event(ctypes.Union):
        _fields_ = [("message", ClientMessage), ("pad", ctypes.c_long * 24)]

    if os.environ.get("IRIX_DOMAINOS_ACTIVATION_PRIVATE") != "1":
        raise RuntimeError("Private X11 required")
    library = ctypes.CDLL("libX11.so.6")
    library.XOpenDisplay.argtypes = [ctypes.c_char_p]; library.XOpenDisplay.restype = ctypes.c_void_p
    library.XDefaultRootWindow.argtypes = [ctypes.c_void_p]; library.XDefaultRootWindow.restype = ctypes.c_ulong
    library.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]; library.XInternAtom.restype = ctypes.c_ulong
    library.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.POINTER(Event)]
    library.XFlush.argtypes = [ctypes.c_void_p]; library.XCloseDisplay.argtypes = [ctypes.c_void_p]
    display = library.XOpenDisplay(os.environ["DISPLAY"].encode())
    if not display:
        raise RuntimeError("Private display unavailable")
    try:
        event = Event(); event.message.type = 33; event.message.window = int(identifier)
        event.message.message_type = library.XInternAtom(display, b"_NET_WM_STATE", 0)
        event.message.format = 32
        event.message.data.l[:] = [1 if maximize else 0,
            library.XInternAtom(display, b"_NET_WM_STATE_MAXIMIZED_VERT", 0),
            library.XInternAtom(display, b"_NET_WM_STATE_MAXIMIZED_HORZ", 0), 1, 0]
        if not library.XSendEvent(display, library.XDefaultRootWindow(display), 0, (1 << 19) | (1 << 20), ctypes.byref(event)):
            raise RuntimeError("Window manager request refused")
        library.XFlush(display)
    finally:
        library.XCloseDisplay(display)


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_ACTIVATION_PRIVATE") != "1":
        raise RuntimeError("Private session required")
    sys.path.insert(0, str(ROOT / "tools"))
    import activate_domainos as activation
    baseline = os.environ.get("IRIX_DOMAINOS_BACKDROP_BASELINE") == "1"
    checks, observations, processes = {}, {}, []

    def wait_for(function, timeout=30):
        until, last = time.monotonic() + timeout, None
        while time.monotonic() < until:
            try:
                last = function()
                if last:
                    return last
            except Exception as error:
                last = repr(error)
            time.sleep(.1)
        raise RuntimeError("Private condition timed out: " + str(last))

    def evaluate(code):
        result = subprocess.run(["gdbus", "call", "--session", "--dest", "org.kde.plasmashell",
            "--object-path", "/PlasmaShell", "--method", "org.kde.PlasmaShell.evaluateScript", code],
            capture_output=True, text=True, timeout=30, check=True)
        return ast.literal_eval(result.stdout)[0]

    def panel(domainos):
        values = activation.call({"action": "inspect"})["state"]["panels"]
        return values[0] if len(values) == 1 and any(w["type"] == activation.PLUGIN for w in values[0]["widgets"]) == domainos else None

    def hints(identifier, value=None):
        code = "var p=panelById(" + str(identifier) + ");var initial=p.currentConfigGroup.slice();p.currentConfigGroup=[];"
        if value is not None:
            code += "p.writeConfig('UserBackgroundHints'," + json.dumps(value) + ");p.reloadConfig();"
        result = json.loads(evaluate(code + "var stored=p.readConfig('UserBackgroundHints',1);p.currentConfigGroup=initial;print(JSON.stringify({stored:stored,exposed:p.userBackgroundHints}));"))
        observations.setdefault("background_hint_reads", []).append({"id": identifier, "requested": value, **result})
        return "NoBackground" if str(result["stored"]) == "0" else "StandardBackground" if str(result["stored"]) == "1" else str(result["stored"])

    def cli(*args):
        run = subprocess.run([sys.executable, str(ROOT / "tools/activate_domainos.py"), *args],
            capture_output=True, text=True, timeout=60)
        observations.setdefault("cli", []).append({"args": args, "code": run.returncode,
            "stdout": run.stdout, "stderr": run.stderr})
        if run.returncode:
            raise RuntimeError(run.stdout + run.stderr)

    def ui():
        data = json.loads((output / "UI.json").read_text())
        roots = data.get("nativeRoots", [])
        return data if len(roots) == 1 else None

    def capture(stage, background, floating=None):
        def ready():
            data = ui()
            if not data or len(data.get("panels", [])) != 1:
                return None
            root = data["nativeRoots"][0]
            if (root["visibleBackgroundCount"] > 0) != background:
                return None
            if floating is not None and abs(root["floatingness"] - int(floating)) > .001:
                return None
            return data
        data = wait_for(ready)
        time.sleep(.5)
        data = ready()
        observations[stage] = data
        picture = output / (stage.upper() + ".png")
        shutil.copy2(output / "panel-live.png", picture)
        drawing = data["panels"][0]
        checks[stage + "_drawing_971_109"] = abs(drawing["width"] - 971) < .01 and abs(drawing["height"] - 109) < .01
        checks[stage + "_drawing_scale_half"] = abs(drawing["scale"] - .5) < .00001
        checks[stage + "_drawing_not_clipped"] = drawing["x"] >= 0 and drawing["y"] >= 0 and drawing["x"] + 971 <= drawing["windowWidth"] + .01 and drawing["y"] + 109 <= drawing["windowHeight"] + .01
        root = data["nativeRoots"][0]; mask = root["maskBounds"]
        checks[stage + "_native_mask_contains_drawing"] = root["maskEmpty"] or (mask["x"] <= drawing["x"] and mask["y"] <= drawing["y"] and mask["x"] + mask["width"] >= drawing["x"] + 971 and mask["y"] + mask["height"] >= drawing["y"] + 109)
        checks[stage + "_native_backdrop_correct"] = (data["nativeRoots"][0]["visibleBackgroundCount"] > 0) == background
        checks[stage + "_own_panel_capture"] = picture.is_file()
        return data

    try:
        # Private application colors deliberately differ from the blue style.
        config = Path(os.environ["XDG_CONFIG_HOME"])
        shutil.copy2(ROOT / "colors/Irixium.colors", config / "kdeglobals")
        (config / "plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
        qml_probe = os.environ.get("IRIX_DOMAINOS_BACKDROP_QML_BINDING") == "1"
        if qml_probe:
            private_main = Path(os.environ["XDG_DATA_HOME"]) / "plasma/plasmoids/org.irixclassic.domainos.panel/contents/ui/main.qml"
            text = private_main.read_text()
            private_main.write_text(text.replace('    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground\n',
                '    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground\n' + PANEL_BACKGROUND_BINDING, 1))
        for name, args in (("kwin", ["kwin_x11", "--replace"]), ("plasma", ["plasmashell", "--no-respawn"])):
            stream = (output / (name + ".log")).open("w")
            env = dict(os.environ)
            if name == "plasma":
                env["LD_PRELOAD"] = str(output / "activation-host.so")
            process = subprocess.Popen(args, env=env, stdout=stream, stderr=stream)
            processes.append((process, stream))
        before = wait_for(lambda: panel(False))
        time.sleep(3)
        before = panel(False)
        observations["original"] = before
        original_hint = hints(before["id"])
        if os.environ.get("IRIX_DOMAINOS_BACKDROP_INTERFACE") == "1":
            observations["native_interface"] = wait_for(ui)
            observations["scripting_properties"] = json.loads(evaluate("var p=panels()[0];print(JSON.stringify(Object.keys(p)));"))
            checks["native_interface_observed"] = bool(observations["native_interface"]["nativeRoots"][0]["exposed"])
            return 0
        cli()
        active = wait_for(lambda: panel(True))
        observations["first_hint"] = hints(active["id"])
        first = capture("before" if baseline else "first", baseline, True)
        checks["native_floating_padding_is_eight"] = first["nativeRoots"][0]["leftFloatingPadding"] == 8 and first["nativeRoots"][0]["bottomFloatingPadding"] == 8
        if baseline:
            checks["baseline_native_containment_background_reproduced"] = first["nativeRoots"][0]["backgroundHints"] != 0
            checks["native_setter_accepts_no_background"] = hints(active["id"], "NoBackground") == "NoBackground"
            fixed = capture("after", False, True)
            checks["native_hint_disables_background_frames"] = fixed["nativeRoots"][0]["backgroundHints"] == 0
        else:
            checks["first_creation_no_background"] = first["nativeRoots"][0]["backgroundHints"] == 0
            spacer = int(evaluate("var p=panelById(" + str(active["id"]) + ");var added=p.addWidget('org.kde.plasma.panelspacer');print(added.id);"))
            shared = wait_for(lambda: ui() if ui()["nativeRoots"][0]["backgroundHints"] == 1 else None)
            observations["another_widget_added"] = shared
            checks["binding_restores_prior_hint_when_another_widget_added"] = shared["nativeRoots"][0]["visibleBackgroundCount"] > 0
            evaluate("var w=panelById(" + str(active["id"]) + ").widgetById(" + str(spacer) + ");w.remove();print('removed');")
            capture("sole_again", False, True)
            checks["binding_reclaims_only_single_domainos_panel"] = wait_for(ui)["nativeRoots"][0]["backgroundHints"] == 0

        stream = (output / "owned-test-window.log").open("w")
        test_window = subprocess.Popen(["xterm", "-T", "DomainOSBackgroundProbe", "-geometry", "50x12+60+80"], stdout=stream, stderr=stream)
        processes.append((test_window, stream))
        def window_id():
            run = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "^DomainOSBackgroundProbe$"], capture_output=True, text=True)
            return run.stdout.strip().splitlines()[0] if run.returncode == 0 and run.stdout.strip() else None
        identifier = wait_for(window_id)
        maximize_owned_window(identifier, True)
        maximized = capture("maximized", False, False)
        checks["native_maximize_defloats_without_backdrop"] = maximized["nativeRoots"][0]["floatingness"] == 0
        maximize_owned_window(identifier, False)
        unmaximized = capture("unmaximized", False, True)
        checks["native_restore_recovers_floating_gap"] = unmaximized["nativeRoots"][0]["leftFloatingPadding"] == 8 and unmaximized["nativeRoots"][0]["bottomFloatingPadding"] == 8
        test_window.terminate(); test_window.wait(timeout=5)

        # Simulate the saved native containment from an older release. Only
        # this private panel is changed; its pins/preferences stay untouched.
        if not baseline:
            hints(active["id"], "StandardBackground")
        cli("--restaurar")
        restored = wait_for(lambda: panel(False))
        checks["original_background_choice_restored"] = hints(restored["id"]) == original_hint
        from_native = wait_for(ui)
        observations["original_restored_ui"] = from_native
        if not baseline:
            cli("--ponte")
            returned = wait_for(lambda: panel(True))
            capture("returned", False, True)
            checks["saved_old_domainos_reset_to_no_background"] = wait_for(ui)["nativeRoots"][0]["backgroundHints"] == 0
            cli("--ponte", "--restaurar")
            checks["second_original_background_restored"] = hints(wait_for(lambda: panel(False))["id"]) == original_hint
    except Exception as error:
        observations["error"] = repr(error)
    finally:
        for process, stream in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)
            stream.close()
        checks["own_processes_stopped"] = all(process.poll() is not None for process, _ in processes)
        (output / "WORKER.json").write_text(json.dumps({"checks": checks, "observations": observations}, indent=2))
    return 0 if checks and all(checks.values()) and "error" not in observations else 1


def main():
    spec = importlib.util.spec_from_file_location("domainos_background_activation", Path(__file__).with_name("testar-domainos-ativacao.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.worker = worker
    module.SESSION_ENTRY = Path(__file__).resolve()
    return module.main()


if __name__ == "__main__":
    sys.exit(main())
