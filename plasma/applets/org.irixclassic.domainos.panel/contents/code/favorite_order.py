#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read one user's external KDE menu order without changing favorites or pins.

Kicker v6.3.6 reads activity ordering followed by global ordering from
kactivitymanagerd-statsrc. Existing Kickoff/Kicker applets take priority. With
none remaining, the greatest compatible legacy instance ID is used, matching
KDE's fallback convention; the caller displays that explicitly as a legacy
source. Conflicting existing menus are ambiguous, never silently selected.
Membership and launch actions remain owned by the live KAStats provider.
"""
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote

sys.dont_write_bytecode = True
from pin_import import list_value

MENU_CLIENTS = {
    "org.kde.plasma.kickoff": "org.kde.plasma.kickoff.favorites.instance-",
    "org.kde.plasma.kicker": "org.kde.plasma.kicker.favorites.instance-",
    "org.kde.plasma.kickerdash": "org.kde.plasma.kicker.favorites.instance-",
}


def key(value):
    value = unquote(str(value))
    return value[len("applications:"):] if value.startswith("applications:") else value


def read_config(path):
    result = configparser.ConfigParser(interpolation=None, strict=False)
    result.optionxform = str
    if path.exists():
        if not path.is_file() or path.stat().st_uid != os.getuid() or path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Favorite order must come from this user's regular configuration file")
        result.read_string(path.read_text(encoding="utf-8"))
    return result


def ordered(config, client, activity):
    result, seen = [], set()
    for scope in ([activity] if activity and activity != "global" else []) + ["global"]:
        section = "Favorites-" + client + "-" + scope
        if not config.has_section(section):
            continue
        for item in list_value(config[section].get("ordering", "")):
            item = key(item)
            if item and item not in seen:
                result.append(item)
                seen.add(item)
    return result


def observe(request, directory=None):
    directory = Path(directory or os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    applets = read_config(directory / "plasma-org.kde.plasma.desktop-appletsrc")
    stats = read_config(directory / "kactivitymanagerd-statsrc")
    activity = str(request.get("activity", ""))
    members = set(request.get("memberHashes", []))
    def matches(item):
        return not members or hashlib.md5(item.encode("utf-8"), usedforsecurity=False).hexdigest() in members
    existing = []
    for section in applets.sections():
        match = re.fullmatch(r"Containments\]\[(\d+)\]\[Applets\]\[(\d+)", section)
        plugin = applets[section].get("plugin", "")
        if match and plugin in MENU_CLIENTS:
            client = MENU_CLIENTS[plugin] + match[2]
            items = ordered(stats, client, activity)
            if items:
                existing.append({"client": client, "instance": int(match[2]),
                    "location": match[1] + "/" + match[2], "order": items, "kind": "existing"})
    if existing:
        # Ignore stale nonmembers when comparing the visual order of menus.
        visible_orders = {tuple(item for item in source["order"] if matches(item))
            for source in existing}
        if len(visible_orders) > 1:
            return {"ok": False, "outcome": "ambiguous", "detail": "Existing KDE menus have different favorite orders"}
        source = max(existing, key=lambda item: item["instance"])
    else:
        clients = set()
        for section in stats.sections():
            match = re.fullmatch(r"Favorites-(org\.kde\.plasma\.(?:kickoff|kicker)\.favorites\.instance-(\d+))-(.+)", section)
            if match and match[3] in ("global", activity):
                clients.add((match[1], int(match[2])))
        legacy = []
        for client, instance in clients:
            items = ordered(stats, client, activity)
            overlap = sum(matches(item) for item in items) if members else 0
            if items and (not members or overlap):
                legacy.append({"client": client, "instance": instance, "order": items,
                    "overlap": overlap, "kind": "legacy", "location": str(instance)})
        if not legacy:
            return {"ok": True, "outcome": "unavailable", "order": [], "kind": "provider", "location": ""}
        source = max(legacy, key=lambda item: (item["overlap"], item["instance"]))
    # Keep ranks for members which may arrive while the native Activity model
    # is rebuilding. Only the native provider determines what is displayed.
    return {"ok": True, "outcome": "observed", "order": source["order"],
        "kind": source["kind"], "location": source["location"], "client": source["client"]}


def main():
    request = {}
    try:
        if len(sys.argv) != 2:
            raise ValueError("Expected one JSON request")
        request = json.loads(sys.argv[1])
        if not isinstance(request, dict) or not isinstance(request.get("memberHashes", []), list) \
                or len(request.get("memberHashes", [])) > 512 \
                or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{32}", value) for value in request.get("memberHashes", [])):
            raise ValueError("Expected a JSON object and favorite identities")
        result = observe(request)
    except (ValueError, OSError, configparser.Error) as error:
        result = {"ok": False, "outcome": "failed", "detail": str(error)}
    result["token"] = request.get("token") if isinstance(request, dict) else None
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
