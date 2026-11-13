#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read explicitly selected launcher origins in this user's Plasma configuration.

Called only from the import controls. Returns desktop IDs for review; never edits
the source panel, synchronizes favorites, launches anything or writes settings.
"""
import configparser
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

PLUGINS = {"org.kde.plasma.taskmanager": ("Task Manager", "launcherList"),
    "org.kde.plasma.icontasks": ("Icons-only Task Manager", "launcherList"),
    "org.irixclassic.iconbox": ("Irix Classic Iconbox", "launchers"),
    "org.irixclassic.quicklaunch": ("Irix Classic launchers", "launcherUrls"),
    "org.kde.plasma.quicklaunch": ("Quicklaunch", "launcherUrls")}


def list_value(value):
    # KConfig StringList escapes literal commas and backslashes. Preserve the
    # delimiters instead of interpreting data as shell syntax or executable URLs.
    result, current, escaped = [], "", False
    for character in value:
        if escaped:
            current += character; escaped = False
        elif character == "\\": escaped = True
        elif character == ",": result.append(current); current = ""
        else: current += character
    if escaped: current += "\\"
    result.append(current)
    return result


def application_dirs():
    roots = [Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))]
    roots += [Path(value) for value in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if value]
    return [root/"applications" for root in roots]


def desktop_ids(value):
    result = []
    for entry in list_value(value):
        if entry.startswith("applications:"):
            identifier = unquote(entry[len("applications:"):])
        elif entry.startswith("file:"):
            url = urlparse(entry)
            if url.netloc not in ("", "localhost") or url.query or url.fragment: continue
            path = Path(unquote(url.path))
            if not path.is_absolute() or not path.is_file(): continue
            # Import only installed XDG application entries; arbitrary local
            # .desktop files or executable URLs are never translated to IDs.
            identifier = ""
            for directory in application_dirs():
                try:
                    identifier = path.resolve().relative_to(directory.resolve()).as_posix().replace("/", "-")
                    break
                except ValueError: pass
        else:
            identifier = entry
        if re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.desktop", identifier) and identifier not in result:
            result.append(identifier)
    return result


def origins(path):
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(path)
    found = []
    for section in config.sections():
        match = re.fullmatch(r"Containments\]\[(\d+)\]\[Applets\]\[(\d+)", section)
        if not match: continue
        plugin = config[section].get("plugin", "")
        if plugin not in PLUGINS: continue
        label, key = PLUGINS[plugin]
        settings = section + "][Configuration][General"
        value = config[settings].get(key, "") if config.has_section(settings) else ""
        ids = desktop_ids(value)
        found.append({"id": match[1] + "/" + match[2], "label": label + " · " + match[1] + "/" + match[2],
            "plugin": plugin, "count": len(ids), "desktopIds": ids})
    return found


def execute(request, path=None):
    if path is None:
        path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config")) / "plasma-org.kde.plasma.desktop-appletsrc"
    found = origins(path)
    if request.get("action") == "origins":
        return {"ok": True, "outcome": "observed", "origins": [{key:value for key,value in source.items() if key != "desktopIds"} for source in found]}
    if request.get("action") == "source":
        source = next((item for item in found if item["id"] == request.get("sourceId")), None)
        if source is None: raise ValueError("The selected launcher source no longer exists")
        return {"ok": True, "outcome": "observed", "sourceId": source["id"], "desktopIds": source["desktopIds"]}
    raise ValueError("Unknown launcher import operation")


def main():
    request = {}
    try:
        if len(sys.argv) != 2: raise ValueError("Expected one JSON request")
        request = json.loads(sys.argv[1])
        if not isinstance(request, dict): raise ValueError("Expected a JSON object")
        result = execute(request)
    except (ValueError, OSError, configparser.Error) as error:
        result = {"ok": False, "outcome": "failed", "detail": str(error)}
    result["token"] = request.get("token") if isinstance(request, dict) else None
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__": raise SystemExit(main())
