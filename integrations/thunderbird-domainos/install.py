#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Stage/install the optional aggregate bridge for the invoking user only.

This registers the native host and produces an XPI to install explicitly through
Thunderbird. It never edits an existing Thunderbird profile or account.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

BASE = Path(__file__).resolve().parent
HOST_NAME = "org.irixclassic.domainos.thunderbird"
EXTENSION_ID = "domainos-mail-count@irixclassic.local"


def install(home, data):
    home, data = Path(home).resolve(), Path(data).resolve()
    target = data / "irixclassic-domainos/thunderbird"
    target.mkdir(parents=True, mode=0o700, exist_ok=True)
    host = target / "native_host.py"
    shutil.copy2(BASE / "native_host.py", host); host.chmod(0o700)
    xpi = target / "domainos-thunderbird-unread-count.xpi"
    with zipfile.ZipFile(xpi, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((BASE / "extension").iterdir()):
            info = zipfile.ZipInfo(path.name, date_time=(2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, path.read_bytes())
    xpi.chmod(0o600)
    applications = data / "applications"
    applications.mkdir(parents=True, exist_ok=True)
    desktop = BASE / "org.irixclassic.domainos.thunderbird.counts.desktop"
    shutil.copy2(desktop, applications / desktop.name)
    # Mozilla's Linux per-user native-host directory; not a Thunderbird profile.
    manifests = home / ".mozilla/native-messaging-hosts"
    manifests.mkdir(parents=True, mode=0o700, exist_ok=True)
    manifest = manifests / (HOST_NAME + ".json")
    manifest.write_text(json.dumps({"name": HOST_NAME,
        "description": "DomainOS Thunderbird aggregate unread count only",
        "path": str(host), "type": "stdio", "allowed_extensions": [EXTENSION_ID]}, indent=2) + "\n")
    manifest.chmod(0o600)
    return {"native_host_manifest": str(manifest), "xpi": str(xpi), "desktop_id": desktop.name,
        "scope": "Invoking user's files only; Thunderbird profiles, accounts and settings are unchanged"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install-user", action="store_true", help="Register the host in this user's HOME/XDG_DATA_HOME")
    mode.add_argument("--stage", type=Path, help="Create a self-contained user tree in a new private directory")
    args = parser.parse_args()
    if args.install_user:
        if os.geteuid() == 0:
            parser.error("Run as your normal user; system installation is not supported")
        home = Path.home()
        data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
    else:
        stage = args.stage.resolve()
        if stage.exists(): parser.error("Use a new stage directory")
        stage.mkdir(parents=True, mode=0o700)
        home, data = stage / "home", stage / "data"
        home.mkdir(mode=0o700); data.mkdir(mode=0o700)
    print(json.dumps(install(home, data), indent=2))


if __name__ == "__main__":
    main()
