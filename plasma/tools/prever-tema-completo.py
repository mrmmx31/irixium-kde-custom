#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Open a whole, disposable Plasma/X11 theme session inside an owned Xephyr.

No startplasma, installer, systemd user import, personal bus or real HOME is used.
The parent owns Xephyr; bwrap exposes only its X socket and read-only theme
resources to a separate user/mount/network/PID namespace. Closing Xephyr ends
that namespace. Qt and GTK galleries use actual installed toolkit styles.
"""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import time
import traceback
import uuid
import zipfile

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[2] if len(SCRIPT.parents) > 2 else Path("/suite")
APPLET = "org.irixclassic.domainos.panel"
INNER_HOME = Path("/home/domainos-test")
GLOBAL_THEMES = ("org.kde.breeze.desktop", "org.magpie.irixclassic.desktop", "org.magpie.irixium.desktop")


def write_json(path, data):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def initial_color_scheme(requested, package_root, catalog):
    defaults = configparser.ConfigParser(interpolation=None)
    defaults.optionxform = str
    defaults.read(REPO / "look-and-feel/org.magpie.irixclassic.desktop/contents/defaults")
    name = requested or defaults.get("kdeglobals][General", "ColorScheme")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", name):
        raise RuntimeError("Nome inválido para o esquema inicial da prévia")
    for entry in catalog["components"]:
        if entry["root"] == "data" and entry["destination"] == "color-schemes/" + name + ".colors":
            source = package_root / entry["source"]
            if not source.is_file():
                source = REPO / entry["source"]
            if not source.is_file():
                raise RuntimeError("Esquema inicial ausente: " + name)
            return name, source
    system_scheme = Path("/usr/share/color-schemes") / (name + ".colors")
    if system_scheme.is_file():
        return name, system_scheme
    raise RuntimeError("Esquema inicial não encontrado: " + name)


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(4)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(4)


def wait_for(check, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(.1)
    raise TimeoutError("A sessão privada não ficou pronta dentro do prazo")


def run(argv, **kwargs):
    return subprocess.run(argv, capture_output=True, text=True, timeout=8, **kwargs)


def worker():
    # The marker alone is not the security boundary: mounts, identity, /proc,
    # absent host buses and explicit environment are checked before any GUI.
    import pwd
    home = Path.home()
    if (home != INNER_HOME or pwd.getpwuid(os.getuid()).pw_dir != str(home)
            or not Path("/etc/domainos-preview").is_file()
            or not Path("/home").is_dir()
            or set(Path("/home").iterdir()) != {INNER_HOME}
            or Path("/run/dbus/system_bus_socket").exists()):
        raise RuntimeError("A galeria exige o namespace privado do lançador")
    output = Path("/out")
    manifest = json.loads((output / "MANIFESTO.json").read_text())
    report = {"status": "starting", "checks": {}, "processes": {},
              "display": os.environ["DISPLAY"], "scope": "Whole Plasma in a disposable bwrap namespace; hardware/audio/network/authentication unavailable."}
    logs, children = [], []

    def save():
        write_json(output / "RESULTADO.json", report)

    def start(name, argv, environment=None):
        log = (output / (name + ".log")).open("w")
        logs.append(log)
        process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=environment)
        children.append(process)
        report["processes"][name] = {"pid": process.pid, "argv": argv}
        save()
        return process

    def dbus(service, path, method, *args):
        result = run(["qdbus6", service, path, method, *args])
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    def dbus_ready(service, path, method, *args):
        # Startup can own a bus name before its event loop answers. A bounded
        # readiness probe may time out; it is not a failure of a user action.
        try:
            return subprocess.run(["qdbus6", service, path, method, *args],
                                  capture_output=True, text=True, timeout=2).returncode == 0
        except subprocess.TimeoutExpired:
            return False

    try:
        report["namespace"] = {name: os.stat("/proc/self/ns/" + name).st_ino for name in ("mnt", "net", "pid", "user")}
        report["checks"]["namespaces_differ_from_parent"] = all(report["namespace"][key] != value for key, value in manifest["parent_namespaces"].items())
        report["checks"]["fake_identity_no_personal_home_or_bus"] = True
        resource_mounts = {resource["mount"] for resource in manifest["resources"]}
        report["checks"]["read_only_resources"] = all("ro" in line.split()[5].split(",") for line in Path("/proc/self/mountinfo").read_text().splitlines() if line.split()[4] == "/usr" or line.split()[4] in resource_mounts)
        report["checks"]["only_own_x_socket_exposed"] = list(Path("/tmp/.X11-unix").iterdir()) == [Path("/tmp/.X11-unix/X" + manifest["display"].lstrip(":"))]
        report["checks"]["no_personal_audio_hardware"] = not Path("/dev/snd").exists() and not Path("/dev/dri").exists()
        if not all(report["checks"].values()):
            raise RuntimeError("Uma barreira de isolamento não foi confirmada")
        start("dbus", ["dbus-daemon", "--nofork", "--config-file=/fixture/bus.conf"])
        wait_for(lambda: Path("/run/user/1000/bus").exists(), 3)
        start("xsettings", ["xsettingsd", "-c", str(home / ".config/xsettingsd/xsettingsd.conf")])
        start("kded", ["kded6"])
        wait_for(lambda: dbus_ready("org.kde.kded6", "/kded", "org.kde.kded6.loadedModules"), 10)
        dbus("org.kde.kded6", "/kded", "org.kde.kded6.loadModule", "gtkconfig")
        wait_for(lambda: dbus_ready("org.kde.kded6", "/modules/gtkconfig", "org.kde.GtkConfig.gtkTheme"), 10)
        if Path("/fixture/theme-companions/tools/theme_companion_bridge.py").is_file():
            install = run(["/usr/bin/python3", "-B", "/fixture/theme-companions/tools/theme_companion_bridge.py", "--instalar"])
            if install.returncode: raise RuntimeError(install.stderr.strip() or install.stdout.strip())
            companion = start("theme_companions", ["/usr/bin/python3", "-B",
                str(home/".local/share/irixium/theme-companions/tools/theme_companion_bridge.py"), "--observar"])
            def companion_ready():
                target = home/".local/state/irixium-gtk4-palette/IrixClassic-KDE/native-selection.json"
                if companion.poll() is not None:
                    raise RuntimeError("A integração GTK da prévia encerrou; consulte theme_companions.log")
                return target.is_file() and json.loads(target.read_text()).get("status") == "applied"
            wait_for(companion_ready, 15)
            report["checks"]["native_gtk_companions_ready"] = True
        kwin = start("kwin", ["kwin_x11", "--replace"])
        wait_for(lambda: dbus_ready("org.kde.KWin", "/KWin", "supportInformation"), 10)
        for name, path in (("activities", "/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd"), ("sensors", "/usr/bin/ksystemstats")):
            if Path(path).is_file():
                start(name, [path])
        plasma_env = os.environ.copy()
        if Path("/fixture/theme-probe.so").is_file():
            plasma_env["LD_PRELOAD"] = "/fixture/theme-probe.so"
        plasma = start("plasma", ["plasmashell", "--no-respawn"], plasma_env)
        wait_for(lambda: dbus_ready("org.kde.plasmashell", "/PlasmaShell", "evaluateScript", "print(desktops().length)"), 20)
        layout = """
            panels().forEach(p => p.remove());
            desktops().forEach(d => {
                d.wallpaperPlugin = "org.kde.image";
                d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
                d.writeConfig("Image", "file:///home/domainos-test/.local/share/wallpapers/IrixClassic/contents/images/1920x1080.jpg");
            });
            var p = new Panel;
            p.location = "bottom"; p.alignment = "center"; p.height = 109;
            p.lengthMode = "custom"; p.minimumLength = 971; p.maximumLength = 971;
            p.length = 971; p.hiding = "none"; p.floating = true;
            var w = p.addWidget("org.irixclassic.domainos.panel");
            w.currentConfigGroup = ["General"];
            w.writeConfig("keepActivityLight", true);
            w.writeConfig("activityLightMilliseconds", 300);
            w.writeConfig("terminalCommand", "/usr/bin/xterm");
            w.reloadConfig();
            print(JSON.stringify({panel:p.id,widget:w.id,type:w.type}));
        """
        reply = dbus("org.kde.plasmashell", "/PlasmaShell", "evaluateScript", layout)
        report["panel"] = json.loads(reply)
        report["checks"]["actual_plasmashell_production_panel"] = report["panel"].get("type") == APPLET
        start("qt6", ["/usr/bin/python3", "-B", "/fixture/gallery/qt6_demo.py"])
        start("gtk3", ["/usr/bin/python3", "-B", "/fixture/gallery/gtk3_demo.py"])
        start("gtk4", ["/usr/bin/python3", "-B", "/fixture/gallery/gtk4_demo.py"])
        # Wait for actual windows, then place them without repaint substitutes.
        def windows():
            found = {}
            for name in ("GTK3", "GTK4", "Qt6"):
                result = run(["xdotool", "search", "--onlyvisible", "--name", name])
                if result.returncode or not result.stdout.strip():
                    return None
                found[name] = result.stdout.strip().splitlines()[0]
            return found
        window_list = wait_for(windows, 20)
        report["windows"] = window_list
        # A complete applet is 971px wide. Plasma's native containment adds
        # gutters even with NoBackground; include measured gutters, as the
        # normal per-user activation does, instead of clipping the right edge.
        fit = """
            var p=panels().find(p=>p.widgets().length===1 && p.widgets()[0].type==="org.irixclassic.domainos.panel");
            if (!p) throw new Error("Private DomainOS panel missing");
            var g=p.widgets()[0].geometry;
            var before={length:p.maximumLength,height:p.height,x:g.x,width:g.width,y:g.y,widgetHeight:g.height};
            var extra=Math.max(0,971-g.width,g.x+g.width+g.x-p.maximumLength);
            if (extra>0) {var length=p.maximumLength+extra;p.minimumLength=length;p.maximumLength=length;}
            print(JSON.stringify({before:before,added:extra,afterLength:p.maximumLength}));
        """
        report["native_gutter_compensation"] = json.loads(dbus("org.kde.plasmashell", "/PlasmaShell", "evaluateScript", fit))
        placements = (("Qt6", 10, 45, 660, 590), ("GTK3", 705, 45, 870, 590), ("GTK4", 405, 145, 850, 620))
        for name, x, y, width, height in placements:
            moved = run(["xdotool", "windowmove", window_list[name], str(x), str(y)])
            sized = run(["xdotool", "windowsize", window_list[name], str(width), str(height)])
            report["checks"]["native_window_" + name] = moved.returncode == 0 and sized.returncode == 0
        # GTK4 is accessible on the second private desktop instead of obscuring
        # the initial Qt6/GTK3 side-by-side inspection.
        run(["xdotool", "set_desktop_for_window", window_list["GTK4"], "1"])
        run(["xdotool", "set_desktop", "0"])
        qt_report = wait_for(lambda: (home / "qtwidgets-proof/RESULTADO.json") if (home / "qtwidgets-proof/RESULTADO.json").is_file() else None, 5)
        report["qt6_gallery"] = json.loads(qt_report.read_text())
        report["initial_color_scheme"] = manifest["initial_color_scheme"]
        report["checks"]["private_initial_color_scheme"] = (
            report["qt6_gallery"]["selections"]["kdeglobals"]["General"]["ColorScheme"]
            == manifest["initial_color_scheme"])
        # The gallery reports installed plugin mappings rather than just a
        # requested config value. Both pieces of evidence are kept.
        mappings = Path("/proc/" + str(report["processes"]["qt6"]["pid"]) + "/maps").read_text()
        report["checks"]["kvantum_loaded_into_real_qt_widgets"] = "kvantum" in mappings.lower()
        report["checks"]["private_gtk_classic_requested"] = 'gtk-theme-name=IrixClassic-KDE' in (home / ".config/gtk-3.0/settings.ini").read_text()
        report["checks"]["all_native_apps_alive"] = all(process.poll() is None for process in children)
        report["checks"]["personal_dbus_services_not_owned"] = all(name not in dbus("org.freedesktop.DBus", "/org/freedesktop/DBus", "ListNames").splitlines() for name in ("org.freedesktop.systemd1", "org.freedesktop.portal.Desktop", "org.kde.kwalletd6"))
        capture = run(["/usr/bin/python3", "-B", "/fixture/prever-tema-completo.py", "--capture"])
        report["checks"]["private_screen_capture"] = capture.returncode == 0 and (output / "TEMA-COMPLETO.png").is_file()
        if not all(report["checks"].values()):
            raise RuntimeError("Uma verificação da sessão completa falhou")
        report["status"] = "open"
        save()
        write_json(output / "PRONTO.json", {"display": manifest["display"], "capture": "TEMA-COMPLETO.png"})
        while kwin.poll() is None and plasma.poll() is None:
            request = output / "REQUEST.json"
            if request.is_file():
                payload = json.loads(request.read_text())
                request.unlink()
                response = {"id": payload.get("id"), "ok": False}
                try:
                    if payload.get("action") == "colors":
                        scheme = payload.get("scheme", "")
                        if not re.fullmatch(r"[A-Za-z0-9_.-]+", scheme):
                            raise RuntimeError("Esquema inválido")
                        applied = run(["plasma-apply-colorscheme", scheme])
                        if applied.returncode:
                            raise RuntimeError(applied.stderr or applied.stdout)
                        response.update(ok=True, scheme=scheme, stdout=applied.stdout)
                    elif payload.get("action") == "theme":
                        theme = payload.get("theme", "")
                        if theme not in GLOBAL_THEMES:
                            raise RuntimeError("Tema global inválido")
                        # Exercise KDE's normal application path. Layout reset
                        # is deliberately not requested by this QA command.
                        applied = run(["plasma-apply-lookandfeel", "--apply", theme])
                        if applied.returncode:
                            raise RuntimeError(applied.stderr or applied.stdout)
                        response.update(ok=True, theme=theme, stdout=applied.stdout)
                    elif payload.get("action") == "capture":
                        result = run(["/usr/bin/python3", "-B", "/fixture/prever-tema-completo.py", "--capture"])
                        response.update(ok=result.returncode == 0, stderr=result.stderr)
                    elif payload.get("action") == "probe":
                        if not Path("/fixture/theme-probe.so").is_file():
                            raise RuntimeError("Esta prévia não carregou o observador")
                        probe = Path(os.environ["XDG_RUNTIME_DIR"]) / "irix-theme-probe"
                        temporary = probe.with_suffix(".tmp")
                        temporary.write_text(payload["id"])
                        temporary.chmod(0o600)
                        temporary.replace(probe)
                        response.update(ok=True, requested=payload["id"])
                    elif payload.get("action") == "settings":
                        start("settings-" + payload["id"], ["/usr/bin/systemsettings", "kcm_colors"])
                        response.update(ok=True)
                    else:
                        raise RuntimeError("Ação desconhecida")
                except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
                    response["error"] = str(error)
                write_json(output / "RESPONSE.json", response)
            time.sleep(1)
        raise RuntimeError("Um dos processos essenciais da prévia encerrou")
    except BaseException as error:
        report.update(status="failed", error=str(error), traceback=traceback.format_exc())
        save()
        write_json(output / "ERRO.json", {"error": str(error)})
        raise
    finally:
        for process in reversed(children):
            stop(process)
        for log in logs:
            log.close()


def capture():
    if Path.home() != INNER_HOME or not Path("/etc/domainos-preview").is_file():
        raise RuntimeError("A captura requer a sessão privada")
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    if not app.primaryScreen().grabWindow(0).save("/out/TEMA-COMPLETO.png"):
        raise RuntimeError("Não foi possível capturar a prévia")


def supervisor(output):
    def terminate(_number, _frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    manifest = json.loads((output / "MANIFESTO.json").read_text())
    if manifest["uid"] != os.getuid() or output.stat().st_uid != os.getuid():
        raise RuntimeError("A prévia pertence a outro usuário")
    xephyr, container = None, None
    try:
        with (output / "Xephyr.log").open("w") as log:
            # Only Xephyr, which embeds the new display, receives the host GUI
            # environment. No host environment is passed into bwrap.
            xephyr = subprocess.Popen(["Xephyr", manifest["display"], "-screen", "1600x1000", "-auth", str(output / "Xauthority"), "-nolisten", "tcp", "-extension", "MIT-SHM", "-noreset", "-br", "-title", "IRIX — GTK, Kvantum e cores; teste isolado"], stdout=log, stderr=subprocess.STDOUT)
        env = dict(os.environ, DISPLAY=manifest["display"], XAUTHORITY=str(output / "Xauthority"))
        wait_for(lambda: xephyr.poll() is None and run(["xdpyinfo"], env=env).returncode == 0, 10)
        cmd = ["unshare", "--user", "--map-root-user", "--net", "bwrap", "--unshare-user", "--unshare-ipc", "--unshare-pid", "--unshare-uts", "--uid", "1000", "--gid", "1000", "--clearenv", "--ro-bind", "/usr", "/usr", "--symlink", "usr/bin", "/bin", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64", "--ro-bind", str(output / "etc"), "/etc", "--proc", "/proc", "--dev", "/dev", "--bind", str(output / "run"), "/run", "--bind", str(output / "tmp"), "/tmp", "--bind", str(output / "home"), str(INNER_HOME), "--bind", str(output), "/out", "--ro-bind", str(output / "fixture"), "/fixture", "--ro-bind", "/tmp/.X11-unix/X" + manifest["display"].lstrip(":"), "/tmp/.X11-unix/X" + manifest["display"].lstrip(":"), "--ro-bind", str(output / "Xauthority"), str(INNER_HOME / ".Xauthority"), "--ro-bind", str(output / "applications"), "/usr/share/applications"]
        for resource in manifest["resources"]:
            cmd.extend(["--ro-bind", resource["source"], resource["mount"]])
        for key, value in manifest["environment"].items():
            cmd.extend(["--setenv", key, value])
        cmd.extend(["--die-with-parent", "--new-session", "--chdir", str(INNER_HOME), "/usr/bin/python3", "-B", "/fixture/prever-tema-completo.py", "--worker"])
        with (output / "namespace.log").open("w") as log:
            container = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"})
        while xephyr.poll() is None and container.poll() is None:
            time.sleep(.3)
        if xephyr.poll() is not None:
            write_json(output / "ENCERRADO.json", {"reason": "Outer Xephyr closed", "only_owned_namespace_stopped": True})
        elif not (output / "ERRO.json").exists():
            write_json(output / "ERRO.json", {"error": "Namespace encerrou antes da prévia; consulte namespace.log", "exit_code": container.returncode})
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        stop(container)
        stop(xephyr)
        before = manifest["protected_before"]
        write_json(output / "PERFIL-PRESERVADO.json", {"before": before, "after": {path: digest(Path(path)) for path in before}, "unchanged": all(digest(Path(path)) == value for path, value in before.items())})


def prepare(args):
    if os.getuid() == 0:
        raise RuntimeError("Execute como usuário da sessão gráfica, sem sudo")
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Execute a partir da sessão gráfica")
    for name in ("Xephyr", "unshare", "bwrap", "kwin_x11", "plasmashell", "dbus-daemon", "qdbus6", "xdotool", "xdpyinfo", "xauth", "xsettingsd"):
        if not shutil.which(name):
            raise RuntimeError("Dependência ausente: " + name)
    output = args.saida.resolve()
    ancestor = next(path for path in (output.parent, *output.parents) if path.exists())
    if output.exists() or ancestor.stat().st_uid != os.getuid() or any(
            parent.is_symlink() for parent in (args.saida.absolute(), *args.saida.absolute().parents)):
        raise RuntimeError("Use um diretório novo em uma pasta do próprio usuário, sem links simbólicos")
    if any(output == path or path in output.parents for path in map(Path, ("/usr", "/etc", "/opt", "/var"))):
        raise RuntimeError("A prévia não pode usar uma pasta compartilhada do sistema")
    number = next((n for n in range(60, 100) if not Path("/tmp/.X" + str(n) + "-lock").exists() and not Path("/tmp/.X11-unix/X" + str(n)).exists()), None)
    if number is None:
        raise RuntimeError("Nenhum display privado disponível")
    output.mkdir(mode=0o700)
    for name in ("home", "etc", "tmp", "run", "fixture", "applications", "package"):
        (output / name).mkdir(mode=0o700)
    for name in (".config", ".local/share", ".cache", ".local/state"):
        (output / "home" / name).mkdir(parents=True, mode=0o700)
    for name in (".X11-unix", ".ICE-unix"):
        (output / "tmp" / name).mkdir(mode=0o1777)
    runtime = output / "run/user/1000"
    runtime.mkdir(parents=True, mode=0o700)
    (output / "etc/passwd").write_text("domainos-test:x:1000:1000:DomainOS Theme Preview:/home/domainos-test:/usr/sbin/nologin\n")
    (output / "etc/group").write_text("domainos-test:x:1000:\n")
    (output / "etc/nsswitch.conf").write_text("passwd: files\ngroup: files\nhosts: files\n")
    (output / "etc/hosts").write_text("127.0.0.1 localhost\n")
    (output / "etc/machine-id").write_text(uuid.uuid4().hex + "\n")
    shutil.copyfile("/usr/share/zoneinfo/America/Manaus", output / "etc/localtime")
    (output / "etc/timezone").write_text("America/Manaus\n")
    (output / "etc/domainos-preview").write_text("Disposable theme preview; no host HOME/services/authentication\n")
    (output / "etc/fonts").mkdir()
    (output / "etc/fonts/fonts.conf").write_text('<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>/usr/share/fonts</dir><cachedir>/home/domainos-test/.cache/fontconfig</cachedir></fontconfig>')
    (output / "etc/xdg").mkdir()
    (output / "etc/pam.d").mkdir()
    for service in ("other", "kde", "kde-fingerprint", "kde-smartcard"):
        (output / "etc/pam.d" / service).write_text("auth required pam_deny.so\naccount required pam_deny.so\npassword required pam_deny.so\nsession required pam_deny.so\n")
    # Bundle extraction is never allowed to escape the new owned directory.
    with zipfile.ZipFile(args.pacote) as archive:
        for info in archive.infolist():
            member = Path(info.filename)
            if member.is_absolute() or ".." in member.parts or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise RuntimeError("Caminho inválido no pacote")
        archive.extractall(output / "package")
    package_roots = [path for path in (output / "package").iterdir() if path.is_dir() and (path / "PACOTE.json").is_file()]
    if len(package_roots) != 1:
        raise RuntimeError("O ZIP deve conter uma única raiz de pacote DomainOS")
    package_root = package_roots[0]
    for line in (package_root / "SHA256SUMS").read_text().splitlines():
        checksum, relative = line.split(maxsplit=1)
        relative = relative.lstrip(" *")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or digest(package_root / path) != checksum:
            raise RuntimeError("O checksum do pacote não confere: " + relative)
    native = package_root / "plasma/applets" / APPLET / "contents/native/menu/libdomainosmenuplugin.so"
    if not native.is_file():
        raise RuntimeError("O pacote deve incluir o módulo nativo da barra")
    catalog = json.loads((REPO / "components.json").read_text())
    resources = []
    config = output / "home/.config"
    data = output / "home/.local/share"
    # Native Global Theme application moves selected values into kdedefaults
    # and removes their user overrides. startplasma normally prepends this
    # directory to XDG_CONFIG_DIRS; our isolated session must do the same.
    (config / "kdedefaults").mkdir()
    (output / "home/.themes").mkdir()
    adaptive_names = {"IrixClassic-KDE", "IrixClassic-KDE-Reload", "Irixium-KDE", "Irixium-KDE-Reload"}
    for index, entry in enumerate(catalog["components"]):
        source = package_root / entry["source"]
        if not source.exists():
            source = REPO / entry["source"]
        if not source.exists():
            raise RuntimeError("Recurso ausente: " + entry["source"])
        target = (data if entry["root"] == "data" else config) / entry["destination"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry["destination"].startswith("themes/") and target.name in adaptive_names:
            # Runtime palettes modify only private copies. Public resources and
            # both actual profiles remain read-only outside this namespace.
            shutil.copytree(source, target)
            shutil.copytree(source, output/"home/.themes"/target.name)
            continue
        if entry["destination"].startswith("kwin/decorations/"):
            # Match the normal installer's discovery path/IDs, but only inside
            # the disposable HOME. The source package is never rewritten.
            normalized = output / "decorations" / target.name
            shutil.copytree(source, normalized)
            metadata = json.loads((normalized / "metadata.json").read_text())
            metadata["KPlugin"]["Id"] = target.name
            write_json(normalized / "metadata.json", metadata)
            legacy = data / "aurorae/themes" / target.name
            shutil.copytree(normalized, legacy)
            source = normalized
        # Direct mounts retain sibling imports used by production QML (notably
        # the grosview instruments); arbitrary symlink roots break that API.
        if source.is_dir():
            target.mkdir()
        else:
            target.touch()
        mount = str(INNER_HOME / target.relative_to(output / "home"))
        resources.append({"source": str(source.resolve()), "mount": mount, "component": entry["source"]})
        if entry["destination"].startswith("themes/"):
            compatibility = output/"home/.themes"/target.name
            compatibility.mkdir()
            resources.append({"source": str(source.resolve()), "mount": str(INNER_HOME/".themes"/target.name),
                "component": entry["source"]+":gtk2-compat"})
    (output / "home/.icons").symlink_to(".local/share/icons", target_is_directory=True)
    initial_scheme, initial_source = initial_color_scheme(args.esquema, package_root, catalog)
    scheme = configparser.ConfigParser(interpolation=None)
    scheme.optionxform = str
    scheme.read(initial_source)
    scheme["KDE"] = {"widgetStyle": "kvantum", "LookAndFeelPackage": "org.magpie.irixclassic.desktop", "SingleClick": "false"}
    scheme["Icons"] = {"Theme": "IrixClassic-SGI"}
    scheme["General"]["ColorScheme"] = initial_scheme
    scheme["General"]["font"] = "Nimbus Sans,10,-1,5,50,0,0,0,0,0"
    scheme["General"]["fixed"] = "Nimbus Mono PS,10,-1,5,50,0,0,0,0,0"
    with (config / "kdeglobals").open("w") as handle:
        scheme.write(handle)
    yellow = configparser.ConfigParser(interpolation=None)
    yellow.optionxform = str
    yellow.read(package_root / "colors/DomainOS-SR10.4.colors")
    yellow["General"]["Name"] = "Preview Yellow Contrast"
    yellow["General"]["ColorScheme"] = "PreviewYellowContrast"
    yellow["Colors:Window"]["BackgroundNormal"] = "238,221,90"
    yellow["Colors:View"]["BackgroundNormal"] = "255,242,156"
    yellow["Colors:Selection"]["BackgroundNormal"] = "245,208,0"
    with (data / "color-schemes/PreviewYellowContrast.colors").open("w") as handle:
        yellow.write(handle)
    (config / "plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
    (config / "Kvantum/kvantum.kvconfig").write_text("[General]\ntheme=IrixClassic\n")
    (config / "kcminputrc").write_text("[Mouse]\ncursorTheme=SGI-Classic\ncursorSize=24\n")
    (config / "kwinrc").write_text("[Desktops]\nNumber=2\nName_1=Work\nName_2=Procrastination\n[Compositing]\nEnabled=true\n[org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae\ntheme=" + args.decoracao + "\nButtonsOnLeft=M\nButtonsOnRight=IA\n")
    (config / "plasma-org.kde.plasma.desktop-appletsrc").write_text("[General]\nfirstRun=false\n")
    for version in ("3.0", "4.0"):
        directory = config / ("gtk-" + version)
        directory.mkdir()
        (directory / "settings.ini").write_text("[Settings]\ngtk-theme-name=IrixClassic-KDE\ngtk-icon-theme-name=IrixClassic-SGI\ngtk-font-name=Nimbus Sans 10\ngtk-cursor-theme-name=SGI-Classic\ngtk-cursor-theme-size=24\ngtk-application-prefer-dark-theme=false\n")
    (output / "home/.gtkrc-2.0").write_text('gtk-theme-name="IrixClassic-KDE"\ngtk-icon-theme-name="IrixClassic-SGI"\ngtk-font-name="Nimbus Sans 10"\ngtk-cursor-theme-name="SGI-Classic"\n')
    (config / "xsettingsd").mkdir()
    (config / "xsettingsd/xsettingsd.conf").write_text('Net/ThemeName "IrixClassic"\nNet/IconThemeName "IrixClassic-SGI"\nGtk/FontName "Nimbus Sans 10"\nGtk/CursorThemeName "SGI-Classic"\nGtk/CursorThemeSize 24\nXft/Antialias 1\nXft/DPI 98304\n')
    (config / "pulse").mkdir()
    (config / "pulse/client.conf").write_text("autospawn=no\nauto-connect-display=no\nauto-connect-localhost=no\n")
    gallery = output / "fixture/gallery"
    shutil.copytree(args.galeria_gtk, gallery)
    shutil.copyfile(args.galeria_qt, gallery / "qt6_demo.py")
    shutil.copyfile(Path(__file__), output / "fixture/prever-tema-completo.py")
    sys.path.insert(0, str(REPO/"tools"))
    from theme_companion_bridge import MODULES
    integration = output/"fixture/theme-companions"
    (integration/"tools").mkdir(parents=True)
    for module in MODULES:
        shutil.copyfile(REPO/"tools"/module, integration/"tools"/module)
    shutil.copyfile(REPO/"components.json", integration/"components.json")
    if args.observador:
        shutil.copyfile(args.observador, output / "fixture/theme-probe.so")
    # Allow only the native settings backend in this private bus. Loading all
    # desktop activation services would expose unrelated portals or agents.
    services = output/"fixture/dbus-services"
    services.mkdir()
    shutil.copyfile('/usr/share/dbus-1/services/ca.desrt.dconf.service', services/'ca.desrt.dconf.service')
    (output / "fixture/bus.conf").write_text('<busconfig><type>session</type><listen>unix:path=/run/user/1000/bus</listen><auth>EXTERNAL</auth><servicedir>/fixture/dbus-services</servicedir><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    launchers = {
        "qt6": ("Galeria Qt6 — Kvantum", "/usr/bin/python3 -B /fixture/gallery/qt6_demo.py", "applications-development"),
        "gtk2": ("Galeria GTK2 — Classic", "/usr/bin/python3 -B /fixture/gallery/gtk2_demo.py", "applications-development"),
        "gtk3": ("Galeria GTK3 — Classic", "/usr/bin/python3 -B /fixture/gallery/gtk3_demo.py", "applications-development"),
        "gtk4": ("Galeria GTK4 — Classic", "/usr/bin/python3 -B /fixture/gallery/gtk4_demo.py", "applications-development"),
        "settings": ("Configurações desta prévia", "/usr/bin/systemsettings", "preferences-system"),
        "kvantum": ("Kvantum desta prévia", "/usr/bin/kvantummanager", "preferences-desktop-theme"),
        "files": ("IrixClassic Files desta prévia", "/usr/bin/irixclassic-files", "system-file-manager"),
        "terminal": ("Terminal desta prévia", "/usr/bin/xterm", "utilities-terminal"),
    }
    desktop = output / "home/Desktop"
    desktop.mkdir()
    for key, (name, command, icon) in launchers.items():
        text = "[Desktop Entry]\nType=Application\nName=" + name + "\nExec=" + command + "\nIcon=" + icon + "\nCategories=Utility;\nDBusActivatable=false\nTerminal=false\n"
        (output / "applications" / ("irix-preview-" + key + ".desktop")).write_text(text)
    (output / "home/LEIA-ME.txt").write_text("PRÉVIA PRIVADA DO TEMA\n\nQt6 e GTK3 na área Work; GTK4 em Procrastination.\nUse Applications para abrir Configurações, Kvantum, Files e terminal.\nAs escolhas desta janela ficam apenas neste perfil temporário.\nRede, áudio, bloqueio e contas pessoais não estão conectados.\nFeche a janela externa Xephyr para encerrar somente a prévia.\n")
    authority = output / "Xauthority"
    result = run(["xauth", "-f", str(authority), "add", ":" + str(number), "MIT-MAGIC-COOKIE-1", os.urandom(16).hex()])
    if result.returncode:
        raise RuntimeError(result.stderr)
    config_host = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    before = {str(config_host / name): digest(config_host / name) for name in ("kdeglobals", "plasmarc", "kwinrc", "kcminputrc", "Kvantum/kvantum.kvconfig", "gtk-3.0/settings.ini", "gtk-4.0/settings.ini", "plasma-org.kde.plasma.desktop-appletsrc")}
    environment = {
        "PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": str(INNER_HOME), "USER": "domainos-test", "LOGNAME": "domainos-test",
        "XDG_CONFIG_HOME": str(INNER_HOME / ".config"), "XDG_DATA_HOME": str(INNER_HOME / ".local/share"), "XDG_CACHE_HOME": str(INNER_HOME / ".cache"), "XDG_STATE_HOME": str(INNER_HOME / ".local/state"),
        "XDG_RUNTIME_DIR": "/run/user/1000", "XDG_DATA_DIRS": "/usr/share",
        "XDG_CONFIG_DIRS": str(INNER_HOME / ".config/kdedefaults") + ":/etc/xdg",
        "XDG_CURRENT_DESKTOP": "KDE", "XDG_SESSION_TYPE": "x11",
        "KDE_SESSION_VERSION": "6", "KDE_FULL_SESSION": "true", "DISPLAY": ":" + str(number), "XAUTHORITY": str(INNER_HOME / ".Xauthority"), "ICEAUTHORITY": str(INNER_HOME / ".ICEauthority"),
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus", "DBUS_SYSTEM_BUS_ADDRESS": "unix:path=/run/no-system-bus",
        "QT_QPA_PLATFORM": "xcb", "QT_QPA_PLATFORMTHEME": "kde", "QT_QUICK_BACKEND": "software", "QSG_RENDER_LOOP": "basic", "QT_X11_NO_MITSHM": "1", "KWIN_COMPOSE": "O2", "LIBGL_ALWAYS_SOFTWARE": "1", "GDK_BACKEND": "x11", "GSK_RENDERER": "cairo", "FONTCONFIG_FILE": "/etc/fonts/fonts.conf", "TZ": "America/Manaus",
        "XCURSOR_THEME": "SGI-Classic", "XCURSOR_SIZE": "24", "XCURSOR_PATH": str(INNER_HOME / ".local/share/icons") + ":/usr/share/icons",
        "PULSE_CLIENTCONFIG": str(INNER_HOME / ".config/pulse/client.conf"), "PULSE_SERVER": "unix:/run/disabled-pulse", "PIPEWIRE_RUNTIME_DIR": "/run/user/1000", "PIPEWIRE_REMOTE": "disabled-pipewire",
        "IRIX_DOMAINOS_PRIVATE_XEPHYR": "1", "PRIVATE_XEPHYR": "1", "IRIX_DOMAINOS_PRIVATE_NAMESPACE": "bwrap", "IRIX_DOMAINOS_SESSION_ROOT": str(INNER_HOME),
    }
    manifest = {"uid": os.getuid(), "display": ":" + str(number), "resources": resources, "environment": environment, "protected_before": before,
                "launcher_sha256": digest(Path(__file__)),
                "initial_color_scheme": initial_scheme, "initial_color_source_sha256": digest(initial_source),
                "parent_namespaces": {name: os.stat("/proc/self/ns/" + name).st_ino for name in ("mnt", "net", "pid", "user")},
                "package": str(args.pacote.resolve()), "package_sha256": digest(args.pacote), "decoration": args.decoracao,
                "native_plugin_sha256": digest(native), "fonts": "Nimbus Sans 10; Nimbus Mono PS 10", "layout": "Qt6/GTK3 desktop 1; GTK4 desktop 2"}
    write_json(output / "MANIFESTO.json", manifest)
    with (output / "supervisor.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--supervisor", str(output)], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wait_for(lambda: (output / "PRONTO.json").exists() or (output / "ERRO.json").exists() or process.poll() is not None, 65)
        if not (output / "PRONTO.json").is_file():
            raise RuntimeError((output / "ERRO.json").read_text() if (output / "ERRO.json").exists() else "Supervisor encerrou; consulte os logs")
    except BaseException:
        if (output / "ERRO.json").exists():
            try:
                process.wait(10)
            except subprocess.TimeoutExpired:
                stop(process)
        else:
            stop(process)
        raise
    write_json(output / "PERFIL-PRESERVADO-AO-ABRIR.json", {"unchanged": all(digest(Path(path)) == value for path, value in before.items()), "protected_paths": list(before)})
    print(json.dumps({"status": "open", "display": manifest["display"], "supervisor_pid": process.pid, "report": str(output / "RESULTADO.json"), "capture": str(output / "TEMA-COMPLETO.png")}, ensure_ascii=False))


def control(args):
    output = args.sessao.resolve()
    if (output.stat().st_uid != os.getuid()
            or output.stat().st_mode & 0o077
            or (output / "ENCERRADO.json").exists() or (output / "ERRO.json").exists()
            or json.loads((output / "MANIFESTO.json").read_text())["uid"] != os.getuid()
            or json.loads((output / "RESULTADO.json").read_text())["status"] != "open"):
        raise RuntimeError("O comando exige uma prévia aberta pertencente ao usuário")
    request = output / "REQUEST.json"
    if request.exists():
        raise RuntimeError("Já existe uma solicitação pendente para esta prévia")
    token = uuid.uuid4().hex
    write_json(request, {"id": token, "action": args.comando, "scheme": args.esquema, "theme": args.tema})
    def reply():
        path = output / "RESPONSE.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text())
        return data if data.get("id") == token else None
    print(json.dumps(wait_for(reply, 15), ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pacote", type=Path, help="Released DomainOS ZIP with its native module")
    parser.add_argument("--galeria-gtk", type=Path, default=REPO / "plasma/tests/galerias-nativas")
    parser.add_argument("--galeria-qt", type=Path, default=REPO / "plasma/tests/galerias-nativas/qt6_demo.py")
    parser.add_argument("--observador", type=Path, help="Optional read-only Plasma diagnostic observer")
    parser.add_argument("--sessao", type=Path, help="Owned running preview to control")
    parser.add_argument("--comando", choices=("colors", "theme", "capture", "probe", "settings"))
    parser.add_argument("--esquema", help="Initial private color scheme, or scheme for the colors command; defaults to the Classic global theme")
    parser.add_argument("--tema", choices=GLOBAL_THEMES, help="Private preview global theme; keeps the panel layout")
    parser.add_argument("--saida", type=Path, default=Path("/tmp/irix-tema-completo-" + str(os.getuid()) + "-" + str(time.time_ns())))
    parser.add_argument("--decoracao", choices=("irixium_irix_classic_v4", "domainos_sr104"), default="irixium_irix_classic_v4")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--capture", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--supervisor", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker()
    elif args.capture:
        capture()
    elif args.supervisor:
        supervisor(args.supervisor.resolve())
    elif args.sessao and args.comando:
        control(args)
    elif not all((args.pacote, args.galeria_gtk, args.galeria_qt)):
        parser.error("Informe --pacote")
    else:
        prepare(args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, TimeoutError, subprocess.SubprocessError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
