# SPDX-License-Identifier: GPL-3.0-or-later
"""Private test resources; never apply a decoration to a personal KWin session."""
import hashlib
import json
import os
from pathlib import Path
import shutil

REPO = Path(__file__).resolve().parents[3]
PACKAGE = REPO / "decorations/domainos/package"


def hashes(paths):
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            for path in paths}


def protected_paths(reference=None):
    home = Path.home()
    values = [home / ".config" / name for name in (
        "kwinrc", "kdeglobals", "plasmarc", "plasmashellrc", "plasma-org.kde.plasma.desktop-appletsrc",
        "Kvantum/kvantum.kvconfig", "gtk-3.0/settings.ini", "gtk-4.0/settings.ini")]
    values += list((REPO / "decorations/classic/package").rglob("*"))
    if reference is not None:
        values.append(reference)
    return [path for path in values if not path.is_dir()]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def prepare(output, graphical=False):
    output = output.absolute()
    if output.exists() or output.parent != Path("/tmp") or os.getuid() == 0:
        raise RuntimeError("Use a new /tmp output directory as an ordinary user")
    if not PACKAGE.is_dir():
        raise RuntimeError("DomainOS SR10.4 production package is not ready")
    output.mkdir(mode=0o700)
    for folder in ("home", "config", "data", "cache", "state", "runtime"):
        (output / folder).mkdir(mode=0o700)
    shutil.copytree(PACKAGE, output / "data/kwin/decorations/domainos_sr104")
    env = os.environ.copy()
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS",
                "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "LD_PRELOAD", "XAUTHORITY",
                "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE",
                "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XDG_SESSION_ID", "SSH_AUTH_SOCK"):
        env.pop(key, None)
    for key, folder in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                        ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        env[key] = str(output / folder)
    env.update(QT_QPA_PLATFORM="xcb" if graphical else "offscreen", QT_QPA_PLATFORMTHEME="generic",
               QT_QUICK_BACKEND="software", XDG_DATA_DIRS="/usr/local/share:/usr/share",
               XDG_CONFIG_DIRS="/etc/xdg", XDG_SESSION_TYPE="x11", XDG_CURRENT_DESKTOP="NONE",
               DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(output / "no-system-bus"),
               PULSE_SERVER="unix:" + str(output / "no-audio-server"),
               DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(output / "no-session-bus"))
    write_json(output / "SOURCE-HASHES.json", hashes([p for p in PACKAGE.rglob("*") if p.is_file()]))
    return env
