#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Launch panel commands with argument vectors, never a shell or elevated user.

The JSON result distinguishes a spawned process / accepted launcher request
from completion of the application. This helper does not own the app lifetime.
It reads session preferences; it never writes MIME defaults or KDE settings.
"""
import configparser
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True


def read_setting(file, group, key):
    reader = shutil.which("kreadconfig6")
    if not reader:
        return ""
    result = subprocess.run([reader, "--file", file, "--group", group, "--key", key],
                            capture_output=True, text=True, timeout=5)
    return result.stdout.strip() if result.returncode == 0 else ""


def desktop_id(value):
    """Accept desktop IDs, not commands, paths, URI parameters or options."""
    value = str(value)
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.desktop", value):
        raise ValueError("Expected an application desktop ID (*.desktop)")
    return value


def application_dirs():
    roots = [Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))]
    roots += [Path(p) for p in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if p]
    return [root / "applications" for root in roots]


def find_desktop_file(identifier):
    """Resolve XDG desktop IDs before invoking a potentially interactive launcher."""
    for directory in application_dirs():
        direct = directory / identifier
        if direct.is_file():
            return direct
        # XDG IDs replace subdirectory separators with hyphens. Most installed
        # entries are flat, so only search subdirectories for an applicable ID.
        if "-" in identifier and directory.is_dir():
            for candidate in directory.rglob("*.desktop"):
                if candidate.is_file() and candidate.relative_to(directory).as_posix().replace("/", "-") == identifier:
                    return candidate
    raise RuntimeError("Application is not installed: " + identifier)


class LauncherOutcomeUnknown(RuntimeError):
    """The launcher reply timed out after a request may have been submitted."""


def run_launcher(command):
    """Wait for launcher acceptance, never for the application's lifetime."""
    # Legacy KIO launches may leave stdout/stderr inherited by the application.
    # A pipe capture would wait for that application to exit after the launcher
    # itself has already returned. A temporary file preserves useful failure
    # details without owning or waiting for the application's lifetime.
    with tempfile.TemporaryFile() as errors:
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=errors, timeout=20)
        except subprocess.TimeoutExpired as error:
            raise LauncherOutcomeUnknown(
                "Launcher did not reply in time; the application may have started. "
                "Request state is unknown; do not automatically repeat the request") from error
        if result.returncode:
            errors.seek(0)
            detail = errors.read(8192).decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or "Application launcher rejected the request")


def launch_desktop(value):
    identifier = desktop_id(value)
    entry = find_desktop_file(identifier)
    launcher = shutil.which("kioclient6") or shutil.which("kioclient")
    if launcher:
        # applications: addresses folders in KIO, not an arbitrary Desktop ID.
        # Use the already resolved XDG entry as a literal launcher argument.
        command = [launcher, "--noninteractive", "exec", str(entry)]
    else:
        launcher = shutil.which("gtk-launch")
        if not launcher:
            raise RuntimeError("No KDE or GTK application launcher is installed")
        command = [launcher, identifier]
    run_launcher(command)
    return {"outcome": "request-accepted", "application": identifier,
            "detail": "Launcher accepted the request; application completion is not observed"}


def spawn(command):
    if not command or not shutil.which(command[0]):
        raise RuntimeError("Requested program is not installed")
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
    return {"outcome": "process-started", "pid": process.pid,
            "detail": "Process created; window availability and application completion are not observed"}


def desktop_value(value):
    """Encode a desktop-entry string value, including leading/trailing spaces."""
    return (value.replace("\\", "\\\\").replace(" ", "\\s")
            .replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r"))


def desktop_exec_argument(value):
    """Quote one literal Exec argument; no shell or field-code expansion.

    Exec quoting and desktop-file value escaping are two distinct layers.
    Quoting only with shlex would change literal percent codes and backslashes.
    """
    value = value.replace("%", "%%")
    for character in ("\\", '"', "$", "`"):
        value = value.replace(character, "\\" + character)
    return ('"' + value + '"').replace("\\", "\\\\").replace(
        "\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


def launch_argv(command):
    """Publish a KDE startup request while preserving a literal argv and cwd.

    KIO loads an owned executable temporary Desktop Entry with StartupNotify.
    Nothing is registered in XDG applications or retained after the request.
    Startup records belong to KDE; acceptance does not mean a window is ready.
    """
    if not command or any(not isinstance(arg, str) or "\0" in arg for arg in command):
        raise ValueError("Expected a nonempty program argument vector without NUL bytes")
    if not shutil.which(command[0]):
        raise RuntimeError("Requested program is not installed")
    launcher = shutil.which("kioclient6") or shutil.which("kioclient")
    if not launcher:
        return {**spawn(command), "startupNotificationRequested": False}
    with tempfile.TemporaryDirectory(prefix="irix-domainos-launch-") as temporary:
        entry = Path(temporary) / "command.desktop"
        entry.write_text("[Desktop Entry]\nType=Application\nStartupNotify=true\n"
            "Name=" + desktop_value(Path(command[0]).name) + "\n"
            "Path=" + desktop_value(os.getcwd()) + "\n"
            "Exec=" + " ".join(desktop_exec_argument(arg) for arg in command) + "\n",
            encoding="utf-8")
        # KDE authorizes this private launcher; its containing directory is0700.
        entry.chmod(0o700)
        run_launcher([launcher, "--noninteractive", "exec", str(entry)])
    return {"outcome": "request-accepted", "program": command[0],
            "startupNotificationRequested": True,
            "detail": "Launcher accepted the startup request; window availability and application completion are not observed"}


def default_mail_client():
    reader = shutil.which("xdg-mime")
    if reader:
        result = subprocess.run([reader, "query", "default", "x-scheme-handler/mailto"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return desktop_id(result.stdout.strip())
    # Preference used only when the user has no MIME default; no default write.
    for candidate in ("thunderbird.desktop", "org.mozilla.Thunderbird.desktop"):
        if any((p / candidate).is_file() for p in application_dirs()):
            return candidate
    raise RuntimeError("No mail client is configured; choose one in panel preferences")


def mail_clients():
    """Read desktop-entry metadata; never start a client or inspect mail data."""
    language = (os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "").split(".", 1)[0]
    localized = [language, language.split("_", 1)[0]] if language and language != "C" else []
    seen, clients = set(), []
    for directory in application_dirs():
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.desktop")):
            identifier = path.relative_to(directory).as_posix().replace("/", "-")
            if identifier in seen:
                continue
            # A hidden user entry masks the same installed system entry.
            seen.add(identifier)
            try:
                desktop_id(identifier)
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                parser.optionxform = str
                parser.read_string(path.read_text(encoding="utf-8"))
                entry = parser["Desktop Entry"]
                if entry.get("Type", "Application") != "Application" or any(
                        entry.get(key, "false").lower() == "true" for key in ("Hidden", "NoDisplay")):
                    continue
                mime_types = entry.get("MimeType", "").split(";")
                # Email categories also include exporters, attachment viewers
                # and theme editors. Require the actual mail-client handler.
                if "x-scheme-handler/mailto" not in mime_types:
                    continue
                executable = entry.get("TryExec", "")
                if executable and not shutil.which(executable):
                    continue
                name = next((entry["Name[" + locale + "]"] for locale in localized
                             if "Name[" + locale + "]" in entry), entry.get("Name", identifier))
                clients.append({"id": identifier, "name": name, "icon": entry.get("Icon", "mail-client")})
            except (OSError, UnicodeError, ValueError, KeyError, configparser.Error):
                # A malformed unrelated application must not prevent listing
                # the other installed clients. No file content is logged.
                continue
    clients.sort(key=lambda client: (client["name"].casefold(), client["id"]))
    try:
        preferred = default_mail_client()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError):
        preferred = ""
    return {"outcome": "metadata-read", "clients": clients, "defaultClient": preferred}


def xman_colors(palette):
    """X resource arguments follow the actual KDE palette supplied by the view."""
    colors = {}
    for key in ("background", "foreground", "selection", "selectionText"):
        value = str(palette.get(key, ""))
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Invalid xman palette color")
        colors[key] = value
    def luminance(color):
        rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
        return sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))
    def contrast(a, b):
        lo, hi = sorted((luminance(a), luminance(b)))
        return (hi + .05) / (lo + .05)
    for bg, fg in (("background", "foreground"), ("selection", "selectionText")):
        if contrast(colors[bg], colors[fg]) < 4.5:
            colors[fg] = max(("#000000", "#ffffff"), key=lambda c: contrast(colors[bg], c))
    return ["-bg", colors["background"], "-fg", colors["foreground"],
            "-xrm", "*menu.background: " + colors["background"],
            "-xrm", "*menu.foreground: " + colors["foreground"],
            "-xrm", "*Command.background: " + colors["selection"],
            "-xrm", "*Command.foreground: " + colors["selectionText"]]


def dbus_call(service, path, method, arguments=(), system=False):
    executable = shutil.which("qdbus6")
    if not executable:
        raise RuntimeError("Qt D-Bus client qdbus6 is not installed")
    command = [executable, *(["--system"] if system else []), service, path, method, *arguments]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Session service rejected the request")
    return result.stdout.strip()


def execute(request):
    action = request.get("action")
    if action == "terminal":
        configured = request.get("terminalCommand") or read_setting("kdeglobals", "General", "TerminalApplication")
        command = shlex.split(configured) if configured else ["konsole"]
        return launch_argv(command)
    if action == "application":
        return launch_desktop(request.get("desktopId", ""))
    if action == "mail":
        return launch_desktop(request.get("mailClient") or default_mail_client())
    if action == "mail-clients":
        return mail_clients()
    if action == "appearance":
        # The category's owner KCM opens Appearance & Style in System Settings.
        return launch_argv(["systemsettings", "kcm_lookandfeel"])
    if action == "xman":
        return launch_argv(["xman", *xman_colors(request.get("palette", {}))])
    if action == "kde-help":
        return launch_argv(["khelpcenter", "help:/plasma-desktop"])
    if action == "lock":
        dbus_call("org.freedesktop.ScreenSaver", "/ScreenSaver", "org.freedesktop.ScreenSaver.Lock")
        try:
            active = dbus_call("org.freedesktop.ScreenSaver", "/ScreenSaver", "org.freedesktop.ScreenSaver.GetActive")
        except RuntimeError as error:
            return {"action": "lock", "outcome": "request-accepted", "detail": "Lock accepted; state unavailable: " + str(error)}
        return {"action": "lock", "outcome": "confirmed" if active == "true" else "request-accepted",
                "detail": "Session service confirms the lock is active" if active == "true"
                else "Lock requested; the service has not confirmed it active yet"}
    if action in ("suspend", "hibernate"):
        dbus_call("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager."
                  + ("Suspend" if action == "suspend" else "Hibernate"), ["true"], system=True)
        return {"action": action, "outcome": "request-accepted", "detail": "Power service accepted the request"}
    if action == "logout-prompt":
        dbus_call("org.kde.LogoutPrompt", "/LogoutPrompt", "org.kde.LogoutPrompt.promptLogout")
        return {"action": action, "outcome": "request-accepted", "detail": "Logout confirmation requested"}
    raise ValueError("Unknown panel command")


def main(argv=None):
    request = {}
    try:
        args = sys.argv[1:] if argv is None else argv
        if len(args) != 1:
            raise ValueError("Expected one JSON request")
        request = json.loads(args[0])
        if not isinstance(request, dict):
            raise ValueError("Expected a JSON object")
        result = {"ok": True, **execute(request)}
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        result = {"ok": False, "outcome": "request-state-unknown"
                  if isinstance(error, LauncherOutcomeUnknown) else "failed", "detail": str(error)}
    result["token"] = request.get("token") if isinstance(request, dict) else None
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
